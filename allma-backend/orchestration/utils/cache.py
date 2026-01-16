"""
Caching Utilities for Performance Optimization

Implements:
- LRU cache for embeddings
- TTL cache for API responses
- Thread-safe caching mechanisms
"""

import asyncio
import hashlib
import time
from typing import Optional, Any, Dict, Callable, TypeVar, Generic
from dataclasses import dataclass, field
from collections import OrderedDict
from functools import wraps
import logging

logger = logging.getLogger(__name__)


# ============================================================
# Cache Entry
# ============================================================

@dataclass
class CacheEntry:
    """A single cache entry with TTL support."""
    value: Any
    created_at: float = field(default_factory=time.time)
    expires_at: Optional[float] = None
    hits: int = 0
    
    @property
    def is_expired(self) -> bool:
        """Check if entry has expired."""
        if self.expires_at is None:
            return False
        return time.time() > self.expires_at
    
    def touch(self) -> None:
        """Record a cache hit."""
        self.hits += 1


# ============================================================
# LRU Cache
# ============================================================

class LRUCache:
    """
    Thread-safe LRU cache with optional TTL.
    
    Features:
    - Least Recently Used eviction
    - Optional TTL per entry
    - Hit/miss statistics
    """
    
    def __init__(self, max_size: int = 1000, default_ttl: Optional[int] = None):
        """
        Initialize LRU cache.
        
        Args:
            max_size: Maximum number of entries
            default_ttl: Default TTL in seconds (None = no expiration)
        """
        self.max_size = max_size
        self.default_ttl = default_ttl
        self._cache: OrderedDict[str, CacheEntry] = OrderedDict()
        self._lock = asyncio.Lock()
        self._hits = 0
        self._misses = 0
    
    async def get(self, key: str) -> Optional[Any]:
        """
        Get value from cache.
        
        Args:
            key: Cache key
            
        Returns:
            Cached value or None
        """
        async with self._lock:
            entry = self._cache.get(key)
            
            if entry is None:
                self._misses += 1
                return None
            
            if entry.is_expired:
                del self._cache[key]
                self._misses += 1
                return None
            
            # Move to end (most recently used)
            self._cache.move_to_end(key)
            entry.touch()
            self._hits += 1
            return entry.value
    
    async def set(
        self,
        key: str,
        value: Any,
        ttl: Optional[int] = None
    ) -> None:
        """
        Set value in cache.
        
        Args:
            key: Cache key
            value: Value to cache
            ttl: Optional TTL override
        """
        async with self._lock:
            # Calculate expiration
            effective_ttl = ttl if ttl is not None else self.default_ttl
            expires_at = None
            if effective_ttl:
                expires_at = time.time() + effective_ttl
            
            # Create entry
            entry = CacheEntry(value=value, expires_at=expires_at)
            
            # Remove old entry if exists
            if key in self._cache:
                del self._cache[key]
            
            # Add new entry
            self._cache[key] = entry
            
            # Evict if needed
            while len(self._cache) > self.max_size:
                self._cache.popitem(last=False)
    
    async def delete(self, key: str) -> bool:
        """
        Delete key from cache.
        
        Args:
            key: Cache key
            
        Returns:
            True if deleted, False if not found
        """
        async with self._lock:
            if key in self._cache:
                del self._cache[key]
                return True
            return False
    
    async def clear(self) -> int:
        """
        Clear all entries.
        
        Returns:
            Number of entries cleared
        """
        async with self._lock:
            count = len(self._cache)
            self._cache.clear()
            self._hits = 0
            self._misses = 0
            return count
    
    async def cleanup_expired(self) -> int:
        """
        Remove expired entries.
        
        Returns:
            Number of entries removed
        """
        async with self._lock:
            expired_keys = [
                k for k, v in self._cache.items()
                if v.is_expired
            ]
            for key in expired_keys:
                del self._cache[key]
            return len(expired_keys)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        total = self._hits + self._misses
        hit_rate = self._hits / total if total > 0 else 0
        
        return {
            "size": len(self._cache),
            "max_size": self.max_size,
            "hits": self._hits,
            "misses": self._misses,
            "hit_rate": hit_rate,
            "default_ttl": self.default_ttl
        }


# ============================================================
# Embedding Cache
# ============================================================

class EmbeddingCache:
    """
    Specialized cache for document embeddings.
    
    Uses content hash as key to avoid re-embedding
    identical content.
    """
    
    def __init__(
        self,
        max_size: int = 10000,
        ttl: int = 3600  # 1 hour default
    ):
        self._cache = LRUCache(max_size=max_size, default_ttl=ttl)
        self._embedding_dim: Optional[int] = None
    
    @staticmethod
    def _hash_content(content: str) -> str:
        """Generate hash for content."""
        return hashlib.sha256(content.encode()).hexdigest()[:32]
    
    async def get_embedding(self, content: str) -> Optional[list]:
        """
        Get cached embedding for content.
        
        Args:
            content: Text content
            
        Returns:
            Cached embedding or None
        """
        key = self._hash_content(content)
        return await self._cache.get(key)
    
    async def set_embedding(
        self,
        content: str,
        embedding: list,
        ttl: Optional[int] = None
    ) -> None:
        """
        Cache an embedding.
        
        Args:
            content: Text content
            embedding: Embedding vector
            ttl: Optional TTL override
        """
        if self._embedding_dim is None:
            self._embedding_dim = len(embedding)
        
        key = self._hash_content(content)
        await self._cache.set(key, embedding, ttl)
    
    async def get_or_compute(
        self,
        content: str,
        compute_fn: Callable[[str], Any]
    ) -> list:
        """
        Get cached embedding or compute and cache.
        
        Args:
            content: Text content
            compute_fn: Async function to compute embedding
            
        Returns:
            Embedding vector
        """
        # Try cache first
        embedding = await self.get_embedding(content)
        if embedding is not None:
            return embedding
        
        # Compute
        embedding = await compute_fn(content)
        
        # Cache
        await self.set_embedding(content, embedding)
        
        return embedding
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        stats = self._cache.stats
        stats["embedding_dim"] = self._embedding_dim
        return stats


# ============================================================
# Response Cache
# ============================================================

class ResponseCache:
    """
    Cache for API responses and query results.
    
    Useful for caching:
    - Frequently asked questions
    - Document search results
    - Model responses
    """
    
    def __init__(
        self,
        max_size: int = 500,
        ttl: int = 300  # 5 minutes default
    ):
        self._cache = LRUCache(max_size=max_size, default_ttl=ttl)
    
    @staticmethod
    def _generate_key(*args, **kwargs) -> str:
        """Generate cache key from arguments."""
        key_data = str(args) + str(sorted(kwargs.items()))
        return hashlib.md5(key_data.encode()).hexdigest()
    
    async def get(
        self,
        *args,
        **kwargs
    ) -> Optional[Any]:
        """Get cached response."""
        key = self._generate_key(*args, **kwargs)
        return await self._cache.get(key)
    
    async def set(
        self,
        value: Any,
        *args,
        ttl: Optional[int] = None,
        **kwargs
    ) -> None:
        """Cache a response."""
        key = self._generate_key(*args, **kwargs)
        await self._cache.set(key, value, ttl)
    
    async def invalidate(self, *args, **kwargs) -> bool:
        """Invalidate a cached response."""
        key = self._generate_key(*args, **kwargs)
        return await self._cache.delete(key)
    
    @property
    def stats(self) -> Dict[str, Any]:
        """Get cache statistics."""
        return self._cache.stats


# ============================================================
# Decorators
# ============================================================

T = TypeVar('T')


def cached(
    cache: LRUCache,
    key_fn: Optional[Callable[..., str]] = None,
    ttl: Optional[int] = None
):
    """
    Decorator for caching async function results.
    
    Args:
        cache: LRUCache instance
        key_fn: Function to generate cache key
        ttl: Optional TTL for entries
        
    Example:
        @cached(my_cache, key_fn=lambda x: f"user:{x}")
        async def get_user(user_id: str):
            ...
    """
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            # Generate key
            if key_fn:
                key = key_fn(*args, **kwargs)
            else:
                key = hashlib.md5(
                    (func.__name__ + str(args) + str(kwargs)).encode()
                ).hexdigest()
            
            # Try cache
            result = await cache.get(key)
            if result is not None:
                return result
            
            # Execute function
            result = await func(*args, **kwargs)
            
            # Cache result
            await cache.set(key, result, ttl)
            
            return result
        
        # Attach cache reference for testing
        wrapper.cache = cache
        return wrapper
    
    return decorator


def memoize(maxsize: int = 128, ttl: Optional[int] = None):
    """
    Simple memoization decorator.
    
    Args:
        maxsize: Maximum cache size
        ttl: Optional TTL in seconds
        
    Example:
        @memoize(maxsize=100, ttl=60)
        async def expensive_operation(param):
            ...
    """
    cache = LRUCache(max_size=maxsize, default_ttl=ttl)
    
    def decorator(func):
        @wraps(func)
        async def wrapper(*args, **kwargs):
            key = hashlib.md5(
                (func.__name__ + str(args) + str(kwargs)).encode()
            ).hexdigest()
            
            result = await cache.get(key)
            if result is not None:
                return result
            
            result = await func(*args, **kwargs)
            await cache.set(key, result)
            
            return result
        
        wrapper.cache = cache
        wrapper.cache_stats = lambda: cache.stats
        wrapper.cache_clear = lambda: asyncio.create_task(cache.clear())
        
        return wrapper
    
    return decorator


# ============================================================
# Global Cache Instances
# ============================================================

# Singleton instances for application-wide caching
_embedding_cache: Optional[EmbeddingCache] = None
_response_cache: Optional[ResponseCache] = None


def get_embedding_cache(
    max_size: int = 10000,
    ttl: int = 3600
) -> EmbeddingCache:
    """Get or create embedding cache singleton."""
    global _embedding_cache
    if _embedding_cache is None:
        _embedding_cache = EmbeddingCache(max_size=max_size, ttl=ttl)
        logger.info(f"Initialized embedding cache (max_size={max_size}, ttl={ttl})")
    return _embedding_cache


def get_response_cache(
    max_size: int = 500,
    ttl: int = 300
) -> ResponseCache:
    """Get or create response cache singleton."""
    global _response_cache
    if _response_cache is None:
        _response_cache = ResponseCache(max_size=max_size, ttl=ttl)
        logger.info(f"Initialized response cache (max_size={max_size}, ttl={ttl})")
    return _response_cache


async def clear_all_caches() -> Dict[str, int]:
    """Clear all global caches."""
    cleared = {}
    
    if _embedding_cache:
        cleared["embedding"] = await _embedding_cache._cache.clear()
    
    if _response_cache:
        cleared["response"] = await _response_cache._cache.clear()
    
    logger.info(f"Cleared all caches: {cleared}")
    return cleared


def get_cache_stats() -> Dict[str, Any]:
    """Get statistics for all caches."""
    stats = {}
    
    if _embedding_cache:
        stats["embedding"] = _embedding_cache.stats
    
    if _response_cache:
        stats["response"] = _response_cache.stats
    
    return stats
