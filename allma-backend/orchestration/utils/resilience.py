"""
Retry and Circuit Breaker Utilities

Production-grade resilience patterns for:
- Exponential backoff retry
- Circuit breaker pattern
- Fallback mechanisms
"""

import asyncio
import time
import random
import logging
from typing import (
    TypeVar, Callable, Optional, Any, 
    List, Type, Awaitable
)
from dataclasses import dataclass, field
from functools import wraps
from enum import Enum

logger = logging.getLogger(__name__)

T = TypeVar('T')


# ============================================================
# Retry Configuration
# ============================================================

@dataclass
class RetryConfig:
    """Configuration for retry behavior."""
    max_attempts: int = 3
    initial_delay: float = 1.0  # seconds
    max_delay: float = 30.0  # seconds
    exponential_base: float = 2.0
    jitter: bool = True  # Add randomness to prevent thundering herd
    retryable_exceptions: tuple = (Exception,)
    
    def get_delay(self, attempt: int) -> float:
        """Calculate delay for given attempt number."""
        delay = min(
            self.initial_delay * (self.exponential_base ** attempt),
            self.max_delay
        )
        
        if self.jitter:
            delay = delay * (0.5 + random.random())
        
        return delay


# ============================================================
# Retry Decorator
# ============================================================

def retry(
    max_attempts: int = 3,
    initial_delay: float = 1.0,
    max_delay: float = 30.0,
    retryable_exceptions: tuple = (Exception,),
    on_retry: Optional[Callable[[Exception, int], None]] = None
):
    """
    Retry decorator with exponential backoff.
    
    Args:
        max_attempts: Maximum number of attempts
        initial_delay: Initial delay in seconds
        max_delay: Maximum delay in seconds
        retryable_exceptions: Exception types to retry
        on_retry: Callback called on each retry
        
    Example:
        @retry(max_attempts=3, retryable_exceptions=(ConnectionError,))
        async def fetch_data():
            ...
    """
    config = RetryConfig(
        max_attempts=max_attempts,
        initial_delay=initial_delay,
        max_delay=max_delay,
        retryable_exceptions=retryable_exceptions
    )
    
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            last_exception = None
            
            for attempt in range(config.max_attempts):
                try:
                    return await func(*args, **kwargs)
                
                except config.retryable_exceptions as e:
                    last_exception = e
                    
                    if attempt < config.max_attempts - 1:
                        delay = config.get_delay(attempt)
                        
                        logger.warning(
                            f"Retry {attempt + 1}/{config.max_attempts} "
                            f"for {func.__name__}: {e}. "
                            f"Waiting {delay:.2f}s..."
                        )
                        
                        if on_retry:
                            on_retry(e, attempt + 1)
                        
                        await asyncio.sleep(delay)
                    else:
                        logger.error(
                            f"All {config.max_attempts} attempts failed "
                            f"for {func.__name__}: {e}"
                        )
            
            raise last_exception
        
        return wrapper
    return decorator


async def retry_async(
    func: Callable[..., Awaitable[T]],
    *args,
    config: Optional[RetryConfig] = None,
    **kwargs
) -> T:
    """
    Execute async function with retry logic.
    
    Args:
        func: Async function to execute
        config: Retry configuration
        *args, **kwargs: Function arguments
        
    Returns:
        Function result
    """
    if config is None:
        config = RetryConfig()
    
    last_exception = None
    
    for attempt in range(config.max_attempts):
        try:
            return await func(*args, **kwargs)
        
        except config.retryable_exceptions as e:
            last_exception = e
            
            if attempt < config.max_attempts - 1:
                delay = config.get_delay(attempt)
                logger.warning(
                    f"Retry {attempt + 1}/{config.max_attempts}: {e}. "
                    f"Waiting {delay:.2f}s..."
                )
                await asyncio.sleep(delay)
    
    raise last_exception


# ============================================================
# Circuit Breaker
# ============================================================

class CircuitState(Enum):
    """Circuit breaker states."""
    CLOSED = "closed"       # Normal operation
    OPEN = "open"           # Failing, reject requests
    HALF_OPEN = "half_open" # Testing if recovered


@dataclass
class CircuitBreaker:
    """
    Circuit breaker pattern implementation.
    
    Prevents cascade failures by temporarily stopping
    calls to a failing service.
    """
    failure_threshold: int = 5
    recovery_timeout: float = 30.0  # seconds
    half_open_max_calls: int = 3
    
    # Internal state
    _state: CircuitState = field(default=CircuitState.CLOSED, init=False)
    _failure_count: int = field(default=0, init=False)
    _success_count: int = field(default=0, init=False)
    _last_failure_time: Optional[float] = field(default=None, init=False)
    _half_open_calls: int = field(default=0, init=False)
    
    @property
    def state(self) -> CircuitState:
        """Get current state, auto-transitioning if needed."""
        if self._state == CircuitState.OPEN:
            if self._should_attempt_reset():
                self._state = CircuitState.HALF_OPEN
                self._half_open_calls = 0
                logger.info("Circuit breaker transitioning to HALF_OPEN")
        
        return self._state
    
    def _should_attempt_reset(self) -> bool:
        """Check if enough time has passed to attempt reset."""
        if self._last_failure_time is None:
            return False
        return time.time() - self._last_failure_time >= self.recovery_timeout
    
    def record_success(self) -> None:
        """Record a successful call."""
        if self._state == CircuitState.HALF_OPEN:
            self._success_count += 1
            self._half_open_calls += 1
            
            if self._success_count >= self.half_open_max_calls:
                self._close()
        else:
            self._failure_count = 0
    
    def record_failure(self) -> None:
        """Record a failed call."""
        self._failure_count += 1
        self._last_failure_time = time.time()
        
        if self._state == CircuitState.HALF_OPEN:
            self._open()
        elif self._failure_count >= self.failure_threshold:
            self._open()
    
    def _open(self) -> None:
        """Open the circuit."""
        self._state = CircuitState.OPEN
        logger.warning(
            f"Circuit breaker OPENED after {self._failure_count} failures"
        )
    
    def _close(self) -> None:
        """Close the circuit."""
        self._state = CircuitState.CLOSED
        self._failure_count = 0
        self._success_count = 0
        self._half_open_calls = 0
        logger.info("Circuit breaker CLOSED - service recovered")
    
    def is_available(self) -> bool:
        """Check if calls are allowed."""
        state = self.state  # Triggers auto-transition
        
        if state == CircuitState.CLOSED:
            return True
        
        if state == CircuitState.HALF_OPEN:
            return self._half_open_calls < self.half_open_max_calls
        
        return False
    
    def reset(self) -> None:
        """Manually reset the circuit."""
        self._close()
        self._last_failure_time = None
        logger.info("Circuit breaker manually reset")
    
    @property
    def stats(self) -> dict:
        """Get circuit breaker statistics."""
        return {
            "state": self._state.value,
            "failure_count": self._failure_count,
            "success_count": self._success_count,
            "last_failure_time": self._last_failure_time,
            "failure_threshold": self.failure_threshold,
            "recovery_timeout": self.recovery_timeout
        }


def circuit_breaker(breaker: CircuitBreaker):
    """
    Circuit breaker decorator.
    
    Args:
        breaker: CircuitBreaker instance
        
    Example:
        ollama_breaker = CircuitBreaker(failure_threshold=3)
        
        @circuit_breaker(ollama_breaker)
        async def call_ollama():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            if not breaker.is_available():
                raise CircuitOpenError(
                    f"Circuit breaker open for {func.__name__}"
                )
            
            try:
                result = await func(*args, **kwargs)
                breaker.record_success()
                return result
            
            except Exception as e:
                breaker.record_failure()
                raise
        
        wrapper.breaker = breaker
        return wrapper
    
    return decorator


class CircuitOpenError(Exception):
    """Raised when circuit breaker is open."""
    pass


# ============================================================
# Fallback Pattern
# ============================================================

def with_fallback(
    fallback_fn: Callable[..., Awaitable[T]],
    exceptions: tuple = (Exception,)
):
    """
    Decorator that provides fallback on failure.
    
    Args:
        fallback_fn: Async function to call on failure
        exceptions: Exception types to trigger fallback
        
    Example:
        async def default_response():
            return "Service unavailable"
        
        @with_fallback(default_response)
        async def get_response():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            try:
                return await func(*args, **kwargs)
            except exceptions as e:
                logger.warning(
                    f"Falling back for {func.__name__} due to: {e}"
                )
                return await fallback_fn(*args, **kwargs)
        
        return wrapper
    return decorator


# ============================================================
# Timeout Utility
# ============================================================

async def with_timeout(
    coro: Awaitable[T],
    timeout: float,
    error_message: Optional[str] = None
) -> T:
    """
    Execute coroutine with timeout.
    
    Args:
        coro: Coroutine to execute
        timeout: Timeout in seconds
        error_message: Custom error message
        
    Returns:
        Coroutine result
        
    Raises:
        asyncio.TimeoutError: If timeout exceeded
    """
    try:
        return await asyncio.wait_for(coro, timeout=timeout)
    except asyncio.TimeoutError:
        msg = error_message or f"Operation timed out after {timeout}s"
        logger.error(msg)
        raise asyncio.TimeoutError(msg)


def timeout(seconds: float, message: Optional[str] = None):
    """
    Timeout decorator.
    
    Args:
        seconds: Timeout in seconds
        message: Custom error message
        
    Example:
        @timeout(30, "LLM response timeout")
        async def generate_response():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            return await with_timeout(
                func(*args, **kwargs),
                seconds,
                message or f"{func.__name__} timed out after {seconds}s"
            )
        return wrapper
    return decorator


# ============================================================
# Combined Patterns
# ============================================================

def resilient(
    max_retries: int = 3,
    retry_delay: float = 1.0,
    timeout_seconds: Optional[float] = None,
    breaker: Optional[CircuitBreaker] = None,
    fallback_fn: Optional[Callable[..., Awaitable[T]]] = None
):
    """
    Combined resilience decorator.
    
    Applies multiple patterns:
    1. Timeout (if specified)
    2. Circuit breaker (if specified)
    3. Retry with backoff
    4. Fallback (if specified)
    
    Example:
        @resilient(
            max_retries=3,
            timeout_seconds=30,
            breaker=service_breaker,
            fallback_fn=get_cached_response
        )
        async def call_external_service():
            ...
    """
    def decorator(func: Callable[..., Awaitable[T]]) -> Callable[..., Awaitable[T]]:
        @wraps(func)
        async def wrapper(*args, **kwargs) -> T:
            async def execute():
                # Apply timeout if specified
                if timeout_seconds:
                    return await with_timeout(
                        func(*args, **kwargs),
                        timeout_seconds
                    )
                return await func(*args, **kwargs)
            
            try:
                # Check circuit breaker
                if breaker and not breaker.is_available():
                    raise CircuitOpenError(f"Circuit open for {func.__name__}")
                
                # Execute with retry
                result = await retry_async(
                    execute,
                    config=RetryConfig(
                        max_attempts=max_retries,
                        initial_delay=retry_delay
                    )
                )
                
                # Record success
                if breaker:
                    breaker.record_success()
                
                return result
                
            except Exception as e:
                # Record failure
                if breaker:
                    breaker.record_failure()
                
                # Try fallback
                if fallback_fn:
                    logger.warning(f"Using fallback for {func.__name__}: {e}")
                    return await fallback_fn(*args, **kwargs)
                
                raise
        
        return wrapper
    return decorator


# ============================================================
# Service-specific Circuit Breakers
# ============================================================

# Pre-configured circuit breakers for common services
ollama_circuit = CircuitBreaker(
    failure_threshold=3,
    recovery_timeout=30.0,
    half_open_max_calls=1
)

chromadb_circuit = CircuitBreaker(
    failure_threshold=5,
    recovery_timeout=15.0,
    half_open_max_calls=2
)


def get_circuit_breaker_stats() -> dict:
    """Get stats for all circuit breakers."""
    return {
        "ollama": ollama_circuit.stats,
        "chromadb": chromadb_circuit.stats
    }


def reset_all_circuit_breakers() -> None:
    """Reset all circuit breakers."""
    ollama_circuit.reset()
    chromadb_circuit.reset()
    logger.info("All circuit breakers reset")
