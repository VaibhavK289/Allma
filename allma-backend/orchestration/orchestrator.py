"""
Core Orchestrator Module

This is the central coordination point for all AI operations:
- Manages LLM interactions via Ollama
- Coordinates RAG pipeline execution
- Handles conversation context
- Routes requests to appropriate services

Architecture Pattern: Facade + Mediator
"""

import asyncio
import logging
from typing import AsyncGenerator, Dict, List, Optional, Any, Union
from dataclasses import dataclass
from datetime import datetime
from uuid import uuid4

import ollama
from ollama import AsyncClient

from .config import OrchestrationConfig
from .services.rag_service import RAGService
from .services.vector_store_service import VectorStoreService
from .services.document_service import DocumentService
from .services.conversation_service import ConversationService
from .models.schemas import (
    ChatMessage,
    ChatRequest,
    ChatResponse,
    ConversationContext,
    RAGContext,
    DocumentChunk,
)


logger = logging.getLogger(__name__)


@dataclass
class OrchestrationResult:
    """Result container for orchestration operations."""
    success: bool
    data: Any
    error: Optional[str] = None
    metadata: Optional[Dict[str, Any]] = None
    timestamp: datetime = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


class Orchestrator:
    """
    Central orchestrator for the RAG-enabled LLM application.
    
    Coordinates between:
    - Ollama LLM service
    - RAG pipeline
    - Vector store
    - Document processing
    - Conversation management
    
    Usage:
        config = OrchestrationConfig.from_env()
        orchestrator = Orchestrator(config)
        await orchestrator.initialize()
        
        response = await orchestrator.chat("What is machine learning?")
    """
    
    def __init__(self, config: Optional[OrchestrationConfig] = None):
        """Initialize the orchestrator with configuration."""
        self.config = config or OrchestrationConfig.from_env()
        self._initialized = False
        
        # Initialize services (lazy loading)
        self._ollama_client: Optional[AsyncClient] = None
        self._rag_service: Optional[RAGService] = None
        self._vector_store: Optional[VectorStoreService] = None
        self._document_service: Optional[DocumentService] = None
        self._conversation_service: Optional[ConversationService] = None
        
        # State tracking
        self._active_conversations: Dict[str, ConversationContext] = {}
        
        logger.info(f"Orchestrator created with model: {self.config.ollama.model}")
    
    async def initialize(self) -> OrchestrationResult:
        """
        Initialize all services and connections.
        Must be called before using the orchestrator.
        """
        try:
            logger.info("Initializing orchestration layer...")
            
            # Initialize Ollama client
            self._ollama_client = AsyncClient(host=self.config.ollama.host)
            
            # Verify Ollama connection
            models_response = await self._ollama_client.list()
            # Ollama returns Pydantic objects with .models attribute containing model objects
            models_list = models_response.models if hasattr(models_response, 'models') else []
            available_models = [
                m.model if hasattr(m, 'model') else str(m) 
                for m in models_list
            ]
            logger.info(f"Available Ollama models: {available_models}")
            
            # Initialize services
            self._vector_store = VectorStoreService(self.config.vector_store)
            await self._vector_store.initialize()
            
            self._rag_service = RAGService(
                config=self.config.rag,
                vector_store=self._vector_store,
                ollama_client=self._ollama_client,
                embedding_model=self.config.ollama.embedding_model
            )
            await self._rag_service.initialize()
            
            self._document_service = DocumentService(
                config=self.config.document,
                rag_config=self.config.rag
            )
            
            self._conversation_service = ConversationService()
            
            self._initialized = True
            logger.info("Orchestration layer initialized successfully")
            
            return OrchestrationResult(
                success=True,
                data={"status": "initialized", "models": available_models}
            )
            
        except Exception as e:
            logger.error(f"Failed to initialize orchestrator: {e}")
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def shutdown(self) -> None:
        """Gracefully shutdown all services."""
        logger.info("Shutting down orchestration layer...")
        
        if self._vector_store:
            await self._vector_store.close()
        
        self._initialized = False
        logger.info("Orchestration layer shutdown complete")
    
    def _ensure_initialized(self) -> None:
        """Verify orchestrator is initialized before operations."""
        if not self._initialized:
            raise RuntimeError("Orchestrator not initialized. Call initialize() first.")
    
    # ========== Chat Operations ==========
    
    async def chat(
        self,
        message: str,
        conversation_id: Optional[str] = None,
        use_rag: bool = True,
        stream: bool = False,
        **kwargs
    ) -> Union[ChatResponse, AsyncGenerator[str, None]]:
        """
        Process a chat message with optional RAG enhancement.
        
        Args:
            message: User's input message
            conversation_id: Optional ID to maintain conversation context
            use_rag: Whether to use RAG for context retrieval
            stream: Whether to stream the response
            **kwargs: Additional parameters for LLM
            
        Returns:
            ChatResponse or async generator for streaming
        """
        self._ensure_initialized()
        
        # Get or create conversation context
        if conversation_id and conversation_id in self._active_conversations:
            context = self._active_conversations[conversation_id]
        else:
            conversation_id = conversation_id or str(uuid4())
            context = ConversationContext(id=conversation_id)
            self._active_conversations[conversation_id] = context
        
        # Add user message to history
        user_message = ChatMessage(role="user", content=message)
        context.messages.append(user_message)
        
        try:
            # Retrieve RAG context if enabled
            rag_context: Optional[RAGContext] = None
            if use_rag:
                rag_context = await self._rag_service.retrieve_context(message)
                logger.debug(f"Retrieved {len(rag_context.chunks)} relevant chunks")
            
            # Build prompt with context
            full_prompt = self._build_prompt(message, rag_context)
            
            # Prepare messages for Ollama
            messages = self._prepare_messages(context, full_prompt, rag_context)
            
            if stream and self.config.enable_streaming:
                return self._stream_response(messages, context, rag_context)
            else:
                return await self._generate_response(messages, context, rag_context)
                
        except Exception as e:
            logger.error(f"Chat error: {e}")
            return ChatResponse(
                id=str(uuid4()),
                conversation_id=conversation_id,
                content=f"Error processing request: {str(e)}",
                error=str(e)
            )
    
    async def _generate_response(
        self,
        messages: List[Dict[str, str]],
        context: ConversationContext,
        rag_context: Optional[RAGContext]
    ) -> ChatResponse:
        """Generate a complete response from the LLM."""
        response = await self._ollama_client.chat(
            model=self.config.ollama.model,
            messages=messages,
            options={
                "temperature": self.config.ollama.temperature,
                "top_p": self.config.ollama.top_p,
                "top_k": self.config.ollama.top_k,
                "num_ctx": self.config.ollama.num_ctx,
                "num_predict": self.config.ollama.num_predict,
            }
        )
        
        assistant_content = response['message']['content']
        
        # Add assistant response to history
        assistant_message = ChatMessage(role="assistant", content=assistant_content)
        context.messages.append(assistant_message)
        
        return ChatResponse(
            id=str(uuid4()),
            conversation_id=context.id,
            content=assistant_content,
            model=self.config.ollama.model,
            sources=rag_context.sources if rag_context else [],
            usage={
                "prompt_tokens": response.get('prompt_eval_count', 0),
                "completion_tokens": response.get('eval_count', 0),
            }
        )
    
    async def _stream_response(
        self,
        messages: List[Dict[str, str]],
        context: ConversationContext,
        rag_context: Optional[RAGContext]
    ) -> AsyncGenerator[str, None]:
        """Stream response tokens from the LLM."""
        full_response = ""
        
        async for chunk in await self._ollama_client.chat(
            model=self.config.ollama.model,
            messages=messages,
            stream=True,
            options={
                "temperature": self.config.ollama.temperature,
                "num_ctx": self.config.ollama.num_ctx,
            }
        ):
            token = chunk['message']['content']
            full_response += token
            yield token
        
        # Add complete response to history
        assistant_message = ChatMessage(role="assistant", content=full_response)
        context.messages.append(assistant_message)
    
    def _build_prompt(
        self,
        message: str,
        rag_context: Optional[RAGContext]
    ) -> str:
        """Build the full prompt including RAG context if available."""
        if rag_context and rag_context.chunks:
            context_text = "\n\n---\n\n".join([
                f"[Source: {chunk.source}]\n{chunk.content}"
                for chunk in rag_context.chunks
            ])
            return self.config.rag.context_prompt_template.format(
                context=context_text,
                question=message
            )
        return message
    
    def _prepare_messages(
        self,
        context: ConversationContext,
        current_prompt: str,
        rag_context: Optional[RAGContext]
    ) -> List[Dict[str, str]]:
        """Prepare message list for Ollama API."""
        messages = [{"role": "system", "content": self.config.rag.system_prompt}]
        
        # Add conversation history (limited to last N messages)
        history_limit = 10
        for msg in context.messages[-history_limit:-1]:
            messages.append({"role": msg.role, "content": msg.content})
        
        # Add current message with RAG context
        messages.append({"role": "user", "content": current_prompt})
        
        return messages
    
    # ========== RAG Operations ==========
    
    async def ingest_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """
        Ingest a document into the RAG pipeline.
        
        Process: Document -> Chunks -> Embeddings -> Vector Store
        """
        self._ensure_initialized()
        
        try:
            # Process document into chunks
            chunks = await self._document_service.process_document(file_path, metadata)
            logger.info(f"Processed document into {len(chunks)} chunks")
            
            # Generate embeddings and store
            await self._rag_service.ingest_chunks(chunks)
            
            return OrchestrationResult(
                success=True,
                data={
                    "file": file_path,
                    "chunks_created": len(chunks),
                    "status": "ingested"
                }
            )
            
        except Exception as e:
            logger.error(f"Document ingestion failed: {e}")
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def ingest_text(
        self,
        text: str,
        source: str = "direct_input",
        metadata: Optional[Dict[str, Any]] = None
    ) -> OrchestrationResult:
        """Ingest raw text directly into the RAG pipeline."""
        self._ensure_initialized()
        
        try:
            chunks = await self._document_service.chunk_text(text, source, metadata)
            await self._rag_service.ingest_chunks(chunks)
            
            return OrchestrationResult(
                success=True,
                data={
                    "source": source,
                    "chunks_created": len(chunks),
                    "status": "ingested"
                }
            )
            
        except Exception as e:
            logger.error(f"Text ingestion failed: {e}")
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def search(
        self,
        query: str,
        top_k: Optional[int] = None
    ) -> OrchestrationResult:
        """
        Semantic search across the knowledge base.
        
        Returns relevant document chunks without LLM generation.
        """
        self._ensure_initialized()
        
        try:
            k = top_k or self.config.rag.top_k_results
            rag_context = await self._rag_service.retrieve_context(query, top_k=k)
            
            return OrchestrationResult(
                success=True,
                data={
                    "query": query,
                    "results": [
                        {
                            "content": chunk.content,
                            "source": chunk.source,
                            "score": chunk.score,
                            "metadata": chunk.metadata
                        }
                        for chunk in rag_context.chunks
                    ]
                }
            )
            
        except Exception as e:
            logger.error(f"Search failed: {e}")
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    # ========== Conversation Management ==========
    
    async def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[ConversationContext]:
        """Retrieve a conversation by ID."""
        return self._active_conversations.get(conversation_id)
    
    async def clear_conversation(self, conversation_id: str) -> bool:
        """Clear conversation history."""
        if conversation_id in self._active_conversations:
            del self._active_conversations[conversation_id]
            return True
        return False
    
    async def list_conversations(self) -> List[Dict[str, Any]]:
        """List all active conversations."""
        return [
            {
                "id": conv.id,
                "message_count": len(conv.messages),
                "created_at": conv.created_at.isoformat() if conv.created_at else None
            }
            for conv in self._active_conversations.values()
        ]
    
    # ========== Model Management ==========
    
    async def list_models(self) -> OrchestrationResult:
        """List available Ollama models."""
        self._ensure_initialized()
        
        try:
            response = await self._ollama_client.list()
            # Ollama returns Pydantic objects, access via attributes
            models = response.models if hasattr(response, 'models') else []
            
            return OrchestrationResult(
                success=True,
                data={
                    "models": [
                        {
                            "name": m.model if hasattr(m, 'model') else str(m),
                            "size": getattr(m, 'size', None),
                            "modified_at": str(getattr(m, 'modified_at', ''))
                        }
                        for m in models
                    ]
                }
            )
            
        except Exception as e:
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def pull_model(self, model_name: str) -> OrchestrationResult:
        """Pull/download a model from Ollama."""
        self._ensure_initialized()
        
        try:
            await self._ollama_client.pull(model_name)
            return OrchestrationResult(
                success=True,
                data={"model": model_name, "status": "pulled"}
            )
        except Exception as e:
            return OrchestrationResult(
                success=False,
                data=None,
                error=str(e)
            )
    
    async def set_model(self, model_name: str) -> None:
        """Change the active LLM model."""
        self.config.ollama.model = model_name
        logger.info(f"Switched to model: {model_name}")
    
    # ========== Health & Status ==========
    
    async def health_check(self) -> OrchestrationResult:
        """Check health of all services."""
        status = {
            "orchestrator": self._initialized,
            "ollama": False,
            "vector_store": False,
            "rag_service": False,
        }
        
        try:
            # Check Ollama
            if self._ollama_client:
                await self._ollama_client.list()
                status["ollama"] = True
            
            # Check Vector Store
            if self._vector_store:
                status["vector_store"] = await self._vector_store.health_check()
            
            # Check RAG Service
            if self._rag_service:
                status["rag_service"] = True
            
            all_healthy = all(status.values())
            
            return OrchestrationResult(
                success=all_healthy,
                data=status
            )
            
        except Exception as e:
            return OrchestrationResult(
                success=False,
                data=status,
                error=str(e)
            )
    
    def get_config(self) -> Dict[str, Any]:
        """Get current configuration."""
        return self.config.to_dict()
