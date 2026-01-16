"""
Orchestration Layer for Allma AI Backend

This module provides the core orchestration capabilities for:
- LLM interactions via Ollama
- RAG (Retrieval-Augmented Generation) pipeline
- Document ingestion and processing
- Vector store management
- Conversation management
- Database persistence
- Error handling and exceptions

Architecture based on the diagrams:
- RAG Implementation Architecture
- Entity Relationship Diagram
- System Architecture Diagram
"""

from .orchestrator import Orchestrator
from .config import OrchestrationConfig
from .exceptions import (
    OrchestrationException,
    OllamaException,
    OllamaConnectionError,
    OllamaModelNotFoundError,
    RAGException,
    RAGIngestionError,
    RAGRetrievalError,
    VectorStoreException,
    DocumentException,
    DocumentNotFoundError,
    DocumentParseError,
    ConversationException,
    ConversationNotFoundError,
    RateLimitException,
    InitializationError,
    NotInitializedError,
    ErrorCode
)
from .database import (
    DatabaseManager,
    Conversation,
    Message,
    Document,
    ConversationRepository,
    MessageRepository,
    DocumentRepository
)

__version__ = "2.0.0"
__all__ = [
    # Core
    "Orchestrator",
    "OrchestrationConfig",
    
    # Database
    "DatabaseManager",
    "Conversation",
    "Message", 
    "Document",
    "ConversationRepository",
    "MessageRepository",
    "DocumentRepository",
    
    # Exceptions
    "OrchestrationException",
    "OllamaException",
    "OllamaConnectionError",
    "OllamaModelNotFoundError",
    "RAGException",
    "RAGIngestionError",
    "RAGRetrievalError",
    "VectorStoreException",
    "DocumentException",
    "DocumentNotFoundError",
    "DocumentParseError",
    "ConversationException",
    "ConversationNotFoundError",
    "RateLimitException",
    "InitializationError",
    "NotInitializedError",
    "ErrorCode"
]
