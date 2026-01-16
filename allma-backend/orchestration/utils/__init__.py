"""
Utilities package for the Orchestration Layer.

Contains helper functions and utilities for:
- Logging configuration
- Text processing
- Validation
- Error handling
- Caching
- Resilience patterns
"""

from .logger import setup_logging, get_logger
from .helpers import (
    truncate_text,
    estimate_tokens,
    sanitize_filename,
    ensure_directory,
)
from .validators import (
    ValidationResult,
    validate_message,
    validate_file_path,
    validate_uploaded_file,
    validate_metadata,
    validate_id,
    validate_search_query,
    validate_temperature,
    validate_top_k,
    validate_url,
    validate_conversation_title,
    sanitize_text,
    ALLOWED_EXTENSIONS,
    MAX_MESSAGE_LENGTH,
)
from .cache import (
    LRUCache,
    CacheEntry,
    EmbeddingCache,
    ResponseCache,
    cached,
    memoize,
    get_embedding_cache,
    get_response_cache,
    clear_all_caches,
    get_cache_stats,
)
from .resilience import (
    RetryConfig,
    retry,
    retry_async,
    CircuitState,
    CircuitBreaker,
    circuit_breaker,
    CircuitOpenError,
    with_fallback,
    with_timeout,
    timeout,
    resilient,
    ollama_circuit,
    chromadb_circuit,
    get_circuit_breaker_stats,
    reset_all_circuit_breakers,
)

__all__ = [
    # Logger
    "setup_logging",
    "get_logger",
    # Helpers
    "truncate_text",
    "estimate_tokens",
    "sanitize_filename",
    "ensure_directory",
    # Validators
    "ValidationResult",
    "validate_message",
    "validate_file_path",
    "validate_uploaded_file",
    "validate_metadata",
    "validate_id",
    "validate_search_query",
    "validate_temperature",
    "validate_top_k",
    "validate_url",
    "validate_conversation_title",
    "sanitize_text",
    "ALLOWED_EXTENSIONS",
    "MAX_MESSAGE_LENGTH",
    # Cache
    "LRUCache",
    "CacheEntry",
    "EmbeddingCache",
    "ResponseCache",
    "cached",
    "memoize",
    "get_embedding_cache",
    "get_response_cache",
    "clear_all_caches",
    "get_cache_stats",
    # Resilience
    "RetryConfig",
    "retry",
    "retry_async",
    "CircuitState",
    "CircuitBreaker",
    "circuit_breaker",
    "CircuitOpenError",
    "with_fallback",
    "with_timeout",
    "timeout",
    "resilient",
    "ollama_circuit",
    "chromadb_circuit",
    "get_circuit_breaker_stats",
    "reset_all_circuit_breakers",
]
