"""
Configuration module for the Orchestration Layer.

Centralizes all configuration settings for:
- Ollama LLM settings
- Vector store configuration
- RAG pipeline parameters
- Document processing settings
"""

from dataclasses import dataclass, field
from typing import Optional, List, Dict, Any
from enum import Enum
import os


class EmbeddingModel(str, Enum):
    """Supported embedding models."""
    NOMIC_EMBED = "nomic-embed-text"
    MXBAI_EMBED = "mxbai-embed-large"
    ALL_MINILM = "all-minilm"


class LLMModel(str, Enum):
    """Supported LLM models."""
    LLAMA3 = "llama3"
    LLAMA3_2 = "llama3.2"
    MISTRAL = "mistral"
    CODELLAMA = "codellama"
    PHI3 = "phi3"
    GEMMA = "gemma"


class VectorStoreType(str, Enum):
    """Supported vector store backends."""
    CHROMADB = "chromadb"
    FAISS = "faiss"
    QDRANT = "qdrant"


@dataclass
class OllamaConfig:
    """Configuration for Ollama LLM connection."""
    host: str = "http://localhost:11434"
    model: str = LLMModel.LLAMA3_2.value
    embedding_model: str = EmbeddingModel.NOMIC_EMBED.value
    temperature: float = 0.7
    top_p: float = 0.9
    top_k: int = 40
    num_ctx: int = 4096
    num_predict: int = 1024
    timeout: int = 120
    
    @classmethod
    def from_env(cls) -> "OllamaConfig":
        """Create config from environment variables."""
        return cls(
            host=os.getenv("OLLAMA_HOST", "http://localhost:11434"),
            model=os.getenv("OLLAMA_MODEL", LLMModel.LLAMA3_2.value),
            embedding_model=os.getenv("OLLAMA_EMBEDDING_MODEL", EmbeddingModel.NOMIC_EMBED.value),
            temperature=float(os.getenv("OLLAMA_TEMPERATURE", "0.7")),
            num_ctx=int(os.getenv("OLLAMA_NUM_CTX", "4096")),
        )


@dataclass
class VectorStoreConfig:
    """Configuration for vector store."""
    store_type: str = VectorStoreType.CHROMADB.value
    persist_directory: str = "./data/vectorstore"
    collection_name: str = "documents"
    embedding_dimension: int = 768
    distance_metric: str = "cosine"
    
    @classmethod
    def from_env(cls) -> "VectorStoreConfig":
        """Create config from environment variables."""
        return cls(
            store_type=os.getenv("VECTOR_STORE_TYPE", VectorStoreType.CHROMADB.value),
            persist_directory=os.getenv("VECTOR_STORE_PATH", "./data/vectorstore"),
            collection_name=os.getenv("VECTOR_STORE_COLLECTION", "documents"),
        )


@dataclass
class RAGConfig:
    """Configuration for RAG pipeline."""
    chunk_size: int = 1000
    chunk_overlap: int = 200
    top_k_results: int = 5
    similarity_threshold: float = 0.7
    rerank_enabled: bool = True
    max_context_length: int = 8000
    
    # Prompt templates
    system_prompt: str = """You are a helpful AI assistant with access to a knowledge base. 
Use the provided context to answer questions accurately. 
If the context doesn't contain relevant information, say so honestly."""
    
    context_prompt_template: str = """Based on the following context, please answer the question.

Context:
{context}

Question: {question}

Answer:"""

    @classmethod
    def from_env(cls) -> "RAGConfig":
        """Create config from environment variables."""
        return cls(
            chunk_size=int(os.getenv("RAG_CHUNK_SIZE", "1000")),
            chunk_overlap=int(os.getenv("RAG_CHUNK_OVERLAP", "200")),
            top_k_results=int(os.getenv("RAG_TOP_K", "5")),
        )


@dataclass
class DocumentConfig:
    """Configuration for document processing."""
    supported_extensions: List[str] = field(default_factory=lambda: [
        ".txt", ".pdf", ".md", ".docx", ".html", ".json", ".csv"
    ])
    max_file_size_mb: int = 50
    temp_directory: str = "./data/temp"
    processed_directory: str = "./data/processed"
    
    @classmethod
    def from_env(cls) -> "DocumentConfig":
        """Create config from environment variables."""
        return cls(
            max_file_size_mb=int(os.getenv("MAX_FILE_SIZE_MB", "50")),
            temp_directory=os.getenv("TEMP_DIRECTORY", "./data/temp"),
            processed_directory=os.getenv("PROCESSED_DIRECTORY", "./data/processed"),
        )


@dataclass
class OrchestrationConfig:
    """Master configuration for the entire orchestration layer."""
    ollama: OllamaConfig = field(default_factory=OllamaConfig)
    vector_store: VectorStoreConfig = field(default_factory=VectorStoreConfig)
    rag: RAGConfig = field(default_factory=RAGConfig)
    document: DocumentConfig = field(default_factory=DocumentConfig)
    
    # General settings
    debug: bool = False
    log_level: str = "INFO"
    enable_streaming: bool = True
    max_concurrent_requests: int = 10
    
    @classmethod
    def from_env(cls) -> "OrchestrationConfig":
        """Create complete config from environment variables."""
        return cls(
            ollama=OllamaConfig.from_env(),
            vector_store=VectorStoreConfig.from_env(),
            rag=RAGConfig.from_env(),
            document=DocumentConfig.from_env(),
            debug=os.getenv("DEBUG", "false").lower() == "true",
            log_level=os.getenv("LOG_LEVEL", "INFO"),
            enable_streaming=os.getenv("ENABLE_STREAMING", "true").lower() == "true",
        )
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert config to dictionary."""
        return {
            "ollama": {
                "host": self.ollama.host,
                "model": self.ollama.model,
                "embedding_model": self.ollama.embedding_model,
                "temperature": self.ollama.temperature,
            },
            "vector_store": {
                "store_type": self.vector_store.store_type,
                "persist_directory": self.vector_store.persist_directory,
                "collection_name": self.vector_store.collection_name,
            },
            "rag": {
                "chunk_size": self.rag.chunk_size,
                "chunk_overlap": self.rag.chunk_overlap,
                "top_k_results": self.rag.top_k_results,
            },
            "debug": self.debug,
            "log_level": self.log_level,
        }
