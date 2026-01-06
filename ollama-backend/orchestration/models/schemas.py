"""
Pydantic Schemas for the Orchestration Layer

Based on the Entity Relationship Diagram:
- Users -> Conversations -> Messages
- Documents -> Chunks -> Embeddings
- Queries -> Retrievals -> Responses
"""

from datetime import datetime
from typing import Optional, List, Dict, Any
from dataclasses import dataclass, field
from pydantic import BaseModel, Field
from enum import Enum


# ============================================================
# Chat & Conversation Models
# ============================================================

class MessageRole(str, Enum):
    """Valid message roles."""
    SYSTEM = "system"
    USER = "user"
    ASSISTANT = "assistant"


@dataclass
class ChatMessage:
    """
    A single message in a conversation.
    
    Attributes:
        role: The role of the message sender (system, user, assistant)
        content: The message content
        timestamp: When the message was created
        metadata: Optional additional data
    """
    role: str
    content: str
    timestamp: Optional[datetime] = None
    metadata: Optional[Dict[str, Any]] = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.utcnow()


@dataclass
class ConversationContext:
    """
    Context for an ongoing conversation.
    
    Maintains conversation state including:
    - Message history
    - Conversation metadata
    - Timestamps
    """
    id: str
    messages: List[ChatMessage] = field(default_factory=list)
    metadata: Dict[str, Any] = field(default_factory=dict)
    created_at: Optional[datetime] = None
    
    def __post_init__(self):
        if self.created_at is None:
            self.created_at = datetime.utcnow()


class ChatRequest(BaseModel):
    """API request model for chat endpoints."""
    message: str = Field(..., description="User's input message")
    conversation_id: Optional[str] = Field(None, description="Conversation ID for multi-turn chats")
    use_rag: bool = Field(True, description="Whether to use RAG for context")
    stream: bool = Field(False, description="Whether to stream the response")
    model: Optional[str] = Field(None, description="Override default model")
    temperature: Optional[float] = Field(None, ge=0, le=2, description="Sampling temperature")
    max_tokens: Optional[int] = Field(None, description="Maximum tokens to generate")
    
    class Config:
        json_schema_extra = {
            "example": {
                "message": "What is machine learning?",
                "conversation_id": "conv_123",
                "use_rag": True,
                "stream": False
            }
        }


class ChatResponse(BaseModel):
    """API response model for chat endpoints."""
    id: str = Field(..., description="Response ID")
    conversation_id: str = Field(..., description="Conversation ID")
    content: str = Field(..., description="Assistant's response")
    model: Optional[str] = Field(None, description="Model used")
    sources: List[str] = Field(default_factory=list, description="Sources used for RAG")
    usage: Optional[Dict[str, int]] = Field(None, description="Token usage")
    error: Optional[str] = Field(None, description="Error message if any")
    created_at: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "id": "resp_456",
                "conversation_id": "conv_123",
                "content": "Machine learning is a subset of artificial intelligence...",
                "model": "llama3.2",
                "sources": ["ml_textbook.pdf", "ai_guide.md"],
                "usage": {"prompt_tokens": 150, "completion_tokens": 200}
            }
        }


# ============================================================
# Document & Chunk Models
# ============================================================

@dataclass
class DocumentChunk:
    """
    A chunk of text from a document.
    
    Represents a segment of a document after text splitting,
    ready for embedding and storage in the vector store.
    
    Attributes:
        id: Unique identifier for the chunk
        content: The text content
        source: Source document identifier
        chunk_index: Index of this chunk within the document
        embedding: Vector embedding (populated after embedding)
        score: Similarity score (populated during retrieval)
        metadata: Additional metadata
    """
    content: str
    source: str
    chunk_index: int = 0
    id: Optional[str] = None
    embedding: Optional[List[float]] = None
    score: float = 0.0
    metadata: Optional[Dict[str, Any]] = None


@dataclass
class DocumentMetadata:
    """
    Metadata for a processed document.
    
    Captures information about the source document
    for tracking and reference.
    """
    filename: str
    file_path: str
    file_type: str
    file_size: int  # bytes
    created_at: Optional[datetime] = None
    modified_at: Optional[datetime] = None
    char_count: int = 0
    word_count: int = 0
    checksum: Optional[str] = None
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary."""
        return {
            "filename": self.filename,
            "file_path": self.file_path,
            "file_type": self.file_type,
            "file_size": self.file_size,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "modified_at": self.modified_at.isoformat() if self.modified_at else None,
            "char_count": self.char_count,
            "word_count": self.word_count,
            "checksum": self.checksum
        }


# ============================================================
# RAG Models
# ============================================================

@dataclass
class RAGContext:
    """
    Context retrieved through the RAG pipeline.
    
    Contains the results of semantic search along with
    metadata about the retrieval process.
    """
    query: str
    chunks: List[DocumentChunk] = field(default_factory=list)
    sources: List[str] = field(default_factory=list)
    metrics: Optional[Dict[str, Any]] = None
    
    @property
    def has_context(self) -> bool:
        """Check if any context was retrieved."""
        return len(self.chunks) > 0
    
    def get_combined_text(self, separator: str = "\n\n") -> str:
        """Get combined text from all chunks."""
        return separator.join(chunk.content for chunk in self.chunks)


class SearchResult(BaseModel):
    """Single search result from semantic search."""
    content: str = Field(..., description="Matched content")
    source: str = Field(..., description="Source document")
    score: float = Field(..., description="Similarity score (0-1)")
    metadata: Dict[str, Any] = Field(default_factory=dict)
    
    class Config:
        json_schema_extra = {
            "example": {
                "content": "Machine learning is a type of artificial intelligence...",
                "source": "ml_textbook.pdf",
                "score": 0.92,
                "metadata": {"page": 15, "chapter": "Introduction"}
            }
        }


class SearchRequest(BaseModel):
    """API request for semantic search."""
    query: str = Field(..., description="Search query")
    top_k: int = Field(5, ge=1, le=50, description="Number of results")
    filter_source: Optional[str] = Field(None, description="Filter by source")
    threshold: Optional[float] = Field(None, ge=0, le=1, description="Minimum similarity score")


class SearchResponse(BaseModel):
    """API response for semantic search."""
    query: str
    results: List[SearchResult]
    total_results: int
    search_time_ms: float


# ============================================================
# Ingestion Models
# ============================================================

class IngestRequest(BaseModel):
    """API request for document ingestion."""
    file_path: Optional[str] = Field(None, description="Path to file (for file upload)")
    text: Optional[str] = Field(None, description="Raw text to ingest")
    source: Optional[str] = Field(None, description="Source identifier")
    metadata: Optional[Dict[str, Any]] = Field(None, description="Additional metadata")
    
    class Config:
        json_schema_extra = {
            "example": {
                "text": "This is the content to be ingested into the knowledge base.",
                "source": "manual_input",
                "metadata": {"category": "documentation"}
            }
        }


class IngestResponse(BaseModel):
    """API response for document ingestion."""
    success: bool
    source: str
    chunks_created: int
    message: str
    
    class Config:
        json_schema_extra = {
            "example": {
                "success": True,
                "source": "document.pdf",
                "chunks_created": 15,
                "message": "Document ingested successfully"
            }
        }


# ============================================================
# API Health & Status Models
# ============================================================

class ServiceStatus(BaseModel):
    """Status of an individual service."""
    name: str
    status: str  # "healthy", "degraded", "unhealthy"
    latency_ms: Optional[float] = None
    details: Optional[Dict[str, Any]] = None


class HealthResponse(BaseModel):
    """API response for health check endpoint."""
    status: str = Field(..., description="Overall status: healthy, degraded, unhealthy")
    version: str = Field(..., description="API version")
    services: List[ServiceStatus] = Field(default_factory=list)
    timestamp: datetime = Field(default_factory=datetime.utcnow)
    
    class Config:
        json_schema_extra = {
            "example": {
                "status": "healthy",
                "version": "1.0.0",
                "services": [
                    {"name": "ollama", "status": "healthy", "latency_ms": 50},
                    {"name": "vector_store", "status": "healthy", "latency_ms": 10}
                ],
                "timestamp": "2026-01-06T12:00:00Z"
            }
        }


class ModelInfo(BaseModel):
    """Information about an available model."""
    name: str
    size: Optional[int] = None
    modified_at: Optional[str] = None
    digest: Optional[str] = None


class ModelsResponse(BaseModel):
    """API response for models list."""
    models: List[ModelInfo]
    current_model: str


# ============================================================
# Configuration Models
# ============================================================

class ConfigUpdate(BaseModel):
    """Request to update configuration."""
    model: Optional[str] = Field(None, description="Change active model")
    temperature: Optional[float] = Field(None, ge=0, le=2)
    top_k: Optional[int] = Field(None, ge=1, le=50)
    use_rag: Optional[bool] = None
    
    class Config:
        json_schema_extra = {
            "example": {
                "model": "llama3.2",
                "temperature": 0.8,
                "top_k": 5
            }
        }
