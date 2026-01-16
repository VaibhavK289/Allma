"""
Custom Exceptions for the Orchestration Layer

Production-grade exception hierarchy for consistent error handling
across all services and API endpoints.
"""

from typing import Optional, Dict, Any
from enum import Enum


class ErrorCode(str, Enum):
    """Standardized error codes for API responses."""
    
    # General errors (1xxx)
    INTERNAL_ERROR = "ERR_1000"
    VALIDATION_ERROR = "ERR_1001"
    CONFIGURATION_ERROR = "ERR_1002"
    NOT_INITIALIZED = "ERR_1003"
    TIMEOUT_ERROR = "ERR_1004"
    
    # Ollama errors (2xxx)
    OLLAMA_CONNECTION_ERROR = "ERR_2000"
    OLLAMA_MODEL_NOT_FOUND = "ERR_2001"
    OLLAMA_GENERATION_ERROR = "ERR_2002"
    OLLAMA_EMBEDDING_ERROR = "ERR_2003"
    OLLAMA_TIMEOUT = "ERR_2004"
    
    # RAG errors (3xxx)
    RAG_INGESTION_ERROR = "ERR_3000"
    RAG_RETRIEVAL_ERROR = "ERR_3001"
    RAG_EMBEDDING_ERROR = "ERR_3002"
    RAG_CONTEXT_ERROR = "ERR_3003"
    
    # Vector Store errors (4xxx)
    VECTOR_STORE_ERROR = "ERR_4000"
    VECTOR_STORE_CONNECTION = "ERR_4001"
    VECTOR_STORE_NOT_FOUND = "ERR_4002"
    VECTOR_STORE_WRITE_ERROR = "ERR_4003"
    
    # Document errors (5xxx)
    DOCUMENT_NOT_FOUND = "ERR_5000"
    DOCUMENT_PARSE_ERROR = "ERR_5001"
    DOCUMENT_FORMAT_ERROR = "ERR_5002"
    DOCUMENT_TOO_LARGE = "ERR_5003"
    DOCUMENT_EMPTY = "ERR_5004"
    
    # Conversation errors (6xxx)
    CONVERSATION_NOT_FOUND = "ERR_6000"
    CONVERSATION_LIMIT_EXCEEDED = "ERR_6001"
    MESSAGE_TOO_LONG = "ERR_6002"
    
    # Rate limiting (7xxx)
    RATE_LIMIT_EXCEEDED = "ERR_7000"
    QUOTA_EXCEEDED = "ERR_7001"


class OrchestrationException(Exception):
    """
    Base exception class for all orchestration layer errors.
    
    Provides structured error information for consistent
    error handling and API responses.
    """
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.INTERNAL_ERROR,
        status_code: int = 500,
        details: Optional[Dict[str, Any]] = None,
        cause: Optional[Exception] = None
    ):
        """
        Initialize the exception.
        
        Args:
            message: Human-readable error message
            error_code: Standardized error code
            status_code: HTTP status code for API responses
            details: Additional error details
            cause: The underlying exception that caused this error
        """
        super().__init__(message)
        self.message = message
        self.error_code = error_code
        self.status_code = status_code
        self.details = details or {}
        self.cause = cause
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert exception to dictionary for JSON serialization."""
        return {
            "error": True,
            "code": self.error_code.value,
            "message": self.message,
            "details": self.details
        }
    
    def __str__(self) -> str:
        return f"[{self.error_code.value}] {self.message}"


# ============================================================
# Service-specific Exceptions
# ============================================================

class OllamaException(OrchestrationException):
    """Exception for Ollama-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.OLLAMA_CONNECTION_ERROR,
        **kwargs
    ):
        super().__init__(message, error_code, status_code=502, **kwargs)


class OllamaConnectionError(OllamaException):
    """Failed to connect to Ollama service."""
    
    def __init__(self, host: str, cause: Optional[Exception] = None):
        super().__init__(
            message=f"Failed to connect to Ollama at {host}",
            error_code=ErrorCode.OLLAMA_CONNECTION_ERROR,
            details={"host": host},
            cause=cause
        )


class OllamaModelNotFoundError(OllamaException):
    """Requested model not available in Ollama."""
    
    def __init__(self, model: str, available_models: Optional[list] = None):
        super().__init__(
            message=f"Model '{model}' not found in Ollama",
            error_code=ErrorCode.OLLAMA_MODEL_NOT_FOUND,
            details={"model": model, "available": available_models or []}
        )
        self.status_code = 404


class OllamaTimeoutError(OllamaException):
    """Ollama request timed out."""
    
    def __init__(self, operation: str, timeout: int):
        super().__init__(
            message=f"Ollama {operation} timed out after {timeout}s",
            error_code=ErrorCode.OLLAMA_TIMEOUT,
            details={"operation": operation, "timeout_seconds": timeout}
        )
        self.status_code = 504


# ============================================================
# RAG Exceptions
# ============================================================

class RAGException(OrchestrationException):
    """Exception for RAG pipeline errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.RAG_INGESTION_ERROR,
        **kwargs
    ):
        super().__init__(message, error_code, **kwargs)


class RAGIngestionError(RAGException):
    """Failed to ingest document into RAG pipeline."""
    
    def __init__(self, source: str, reason: str, cause: Optional[Exception] = None):
        super().__init__(
            message=f"Failed to ingest '{source}': {reason}",
            error_code=ErrorCode.RAG_INGESTION_ERROR,
            details={"source": source, "reason": reason},
            cause=cause
        )


class RAGRetrievalError(RAGException):
    """Failed to retrieve context from RAG pipeline."""
    
    def __init__(self, query: str, reason: str):
        super().__init__(
            message=f"Retrieval failed for query: {reason}",
            error_code=ErrorCode.RAG_RETRIEVAL_ERROR,
            details={"query": query[:100], "reason": reason}
        )


# ============================================================
# Vector Store Exceptions
# ============================================================

class VectorStoreException(OrchestrationException):
    """Exception for vector store errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.VECTOR_STORE_ERROR,
        **kwargs
    ):
        super().__init__(message, error_code, **kwargs)


class VectorStoreConnectionError(VectorStoreException):
    """Failed to connect to vector store."""
    
    def __init__(self, backend: str, cause: Optional[Exception] = None):
        super().__init__(
            message=f"Failed to connect to {backend} vector store",
            error_code=ErrorCode.VECTOR_STORE_CONNECTION,
            details={"backend": backend},
            cause=cause
        )


# ============================================================
# Document Exceptions
# ============================================================

class DocumentException(OrchestrationException):
    """Exception for document processing errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.DOCUMENT_PARSE_ERROR,
        **kwargs
    ):
        super().__init__(message, error_code, status_code=400, **kwargs)


class DocumentNotFoundError(DocumentException):
    """Document file not found."""
    
    def __init__(self, file_path: str):
        super().__init__(
            message=f"Document not found: {file_path}",
            error_code=ErrorCode.DOCUMENT_NOT_FOUND,
            details={"file_path": file_path}
        )
        self.status_code = 404


class DocumentParseError(DocumentException):
    """Failed to parse document."""
    
    def __init__(self, file_path: str, format: str, reason: str):
        super().__init__(
            message=f"Failed to parse {format} document: {reason}",
            error_code=ErrorCode.DOCUMENT_PARSE_ERROR,
            details={"file_path": file_path, "format": format, "reason": reason}
        )


class DocumentTooLargeError(DocumentException):
    """Document exceeds maximum size limit."""
    
    def __init__(self, file_path: str, size_mb: float, max_size_mb: int):
        super().__init__(
            message=f"Document too large: {size_mb:.1f}MB (max: {max_size_mb}MB)",
            error_code=ErrorCode.DOCUMENT_TOO_LARGE,
            details={"file_path": file_path, "size_mb": size_mb, "max_mb": max_size_mb}
        )
        self.status_code = 413


class UnsupportedFormatError(DocumentException):
    """Document format not supported."""
    
    def __init__(self, extension: str, supported: list):
        super().__init__(
            message=f"Unsupported file format: {extension}",
            error_code=ErrorCode.DOCUMENT_FORMAT_ERROR,
            details={"extension": extension, "supported": supported}
        )
        self.status_code = 415


# ============================================================
# Conversation Exceptions
# ============================================================

class ConversationException(OrchestrationException):
    """Exception for conversation-related errors."""
    
    def __init__(
        self,
        message: str,
        error_code: ErrorCode = ErrorCode.CONVERSATION_NOT_FOUND,
        **kwargs
    ):
        super().__init__(message, error_code, **kwargs)


class ConversationNotFoundError(ConversationException):
    """Conversation not found."""
    
    def __init__(self, conversation_id: str):
        super().__init__(
            message=f"Conversation not found: {conversation_id}",
            error_code=ErrorCode.CONVERSATION_NOT_FOUND,
            details={"conversation_id": conversation_id}
        )
        self.status_code = 404


class MessageTooLongError(ConversationException):
    """Message exceeds maximum length."""
    
    def __init__(self, length: int, max_length: int):
        super().__init__(
            message=f"Message too long: {length} chars (max: {max_length})",
            error_code=ErrorCode.MESSAGE_TOO_LONG,
            details={"length": length, "max_length": max_length}
        )
        self.status_code = 400


# ============================================================
# Rate Limiting Exceptions
# ============================================================

class RateLimitException(OrchestrationException):
    """Exception for rate limiting."""
    
    def __init__(
        self,
        message: str,
        retry_after: int = 60,
        **kwargs
    ):
        super().__init__(
            message,
            error_code=ErrorCode.RATE_LIMIT_EXCEEDED,
            status_code=429,
            **kwargs
        )
        self.retry_after = retry_after
        self.details["retry_after"] = retry_after


# ============================================================
# Initialization Exceptions
# ============================================================

class InitializationError(OrchestrationException):
    """Failed to initialize a service or component."""
    
    def __init__(self, component: str, reason: str, cause: Optional[Exception] = None):
        super().__init__(
            message=f"Failed to initialize {component}: {reason}",
            error_code=ErrorCode.NOT_INITIALIZED,
            details={"component": component, "reason": reason},
            cause=cause
        )


class NotInitializedError(OrchestrationException):
    """Service accessed before initialization."""
    
    def __init__(self, service: str):
        super().__init__(
            message=f"{service} not initialized. Call initialize() first.",
            error_code=ErrorCode.NOT_INITIALIZED,
            status_code=503,
            details={"service": service}
        )
