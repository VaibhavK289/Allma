"""
Middleware components for the FastAPI application.

Production-grade middleware for:
- Request/Response logging
- Error handling
- Rate limiting
- Security headers
- Request ID tracking
- Performance monitoring
"""

import time
import uuid
import logging
from typing import Callable, Optional, Dict, Any
from datetime import datetime
from collections import defaultdict
import asyncio

from fastapi import Request, Response, HTTPException
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from .exceptions import OrchestrationException, RateLimitException, ErrorCode


logger = logging.getLogger(__name__)


# ============================================================
# Request Context
# ============================================================

class RequestContext:
    """Thread-local storage for request context."""
    
    _context: Dict[str, Any] = {}
    
    @classmethod
    def set(cls, key: str, value: Any) -> None:
        cls._context[key] = value
    
    @classmethod
    def get(cls, key: str, default: Any = None) -> Any:
        return cls._context.get(key, default)
    
    @classmethod
    def get_request_id(cls) -> Optional[str]:
        return cls.get("request_id")
    
    @classmethod
    def clear(cls) -> None:
        cls._context.clear()


# ============================================================
# Request ID Middleware
# ============================================================

class RequestIDMiddleware(BaseHTTPMiddleware):
    """
    Adds unique request ID to each request for tracing.
    
    The request ID is:
    - Added to request state
    - Added to response headers
    - Used in all log messages
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Generate or extract request ID
        request_id = request.headers.get("X-Request-ID") or str(uuid.uuid4())[:8]
        
        # Store in request state
        request.state.request_id = request_id
        RequestContext.set("request_id", request_id)
        
        # Process request
        response = await call_next(request)
        
        # Add to response headers
        response.headers["X-Request-ID"] = request_id
        
        return response


# ============================================================
# Logging Middleware
# ============================================================

class LoggingMiddleware(BaseHTTPMiddleware):
    """
    Comprehensive request/response logging.
    
    Logs:
    - Request method, path, client IP
    - Response status and timing
    - Error details when applicable
    """
    
    def __init__(self, app, exclude_paths: Optional[list] = None):
        super().__init__(app)
        self.exclude_paths = exclude_paths or ["/health/live", "/health/ready", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip logging for excluded paths
        if request.url.path in self.exclude_paths:
            return await call_next(request)
        
        request_id = getattr(request.state, "request_id", "unknown")
        start_time = time.time()
        
        # Log request
        client_ip = request.client.host if request.client else "unknown"
        logger.info(
            f"[{request_id}] → {request.method} {request.url.path} "
            f"(client: {client_ip})"
        )
        
        # Process request
        try:
            response = await call_next(request)
            
            # Calculate timing
            duration_ms = (time.time() - start_time) * 1000
            
            # Log response
            logger.info(
                f"[{request_id}] ← {response.status_code} "
                f"({duration_ms:.1f}ms)"
            )
            
            # Add timing header
            response.headers["X-Response-Time"] = f"{duration_ms:.1f}ms"
            
            return response
            
        except Exception as e:
            duration_ms = (time.time() - start_time) * 1000
            logger.error(
                f"[{request_id}] ✗ Error after {duration_ms:.1f}ms: {str(e)}"
            )
            raise


# ============================================================
# Error Handling Middleware
# ============================================================

class ErrorHandlerMiddleware(BaseHTTPMiddleware):
    """
    Centralized error handling for all exceptions.
    
    Converts exceptions to structured JSON responses with:
    - Consistent error format
    - Appropriate status codes
    - Error codes for client handling
    - Sanitized error messages
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await call_next(request)
            
        except OrchestrationException as e:
            # Handle our custom exceptions
            logger.error(f"Orchestration error: {e}")
            return JSONResponse(
                status_code=e.status_code,
                content=e.to_dict()
            )
        
        except HTTPException as e:
            # Handle FastAPI HTTP exceptions
            return JSONResponse(
                status_code=e.status_code,
                content={
                    "error": True,
                    "code": f"HTTP_{e.status_code}",
                    "message": e.detail,
                    "details": {}
                }
            )
        
        except asyncio.TimeoutError:
            logger.error("Request timeout")
            return JSONResponse(
                status_code=504,
                content={
                    "error": True,
                    "code": ErrorCode.TIMEOUT_ERROR.value,
                    "message": "Request timed out",
                    "details": {}
                }
            )
        
        except Exception as e:
            # Handle unexpected exceptions
            request_id = getattr(request.state, "request_id", "unknown")
            logger.exception(f"[{request_id}] Unhandled exception: {e}")
            
            # Don't expose internal errors in production
            return JSONResponse(
                status_code=500,
                content={
                    "error": True,
                    "code": ErrorCode.INTERNAL_ERROR.value,
                    "message": "An unexpected error occurred",
                    "details": {"request_id": request_id}
                }
            )


# ============================================================
# Rate Limiting Middleware
# ============================================================

class RateLimiter:
    """
    Token bucket rate limiter.
    
    Allows bursts up to bucket size while maintaining
    average rate over time.
    """
    
    def __init__(
        self,
        requests_per_minute: int = 60,
        burst_size: int = 10
    ):
        self.rate = requests_per_minute / 60.0  # requests per second
        self.burst_size = burst_size
        self.tokens: Dict[str, float] = defaultdict(lambda: burst_size)
        self.last_update: Dict[str, float] = defaultdict(time.time)
        self._lock = asyncio.Lock()
    
    async def is_allowed(self, key: str) -> bool:
        """Check if request is allowed under rate limit."""
        async with self._lock:
            now = time.time()
            
            # Replenish tokens based on time passed
            time_passed = now - self.last_update[key]
            self.tokens[key] = min(
                self.burst_size,
                self.tokens[key] + time_passed * self.rate
            )
            self.last_update[key] = now
            
            # Check if we have a token available
            if self.tokens[key] >= 1.0:
                self.tokens[key] -= 1.0
                return True
            
            return False
    
    def get_retry_after(self, key: str) -> int:
        """Get seconds until next token available."""
        tokens_needed = 1.0 - self.tokens[key]
        return max(1, int(tokens_needed / self.rate))


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Rate limiting middleware.
    
    Limits requests per client IP or API key.
    """
    
    def __init__(
        self,
        app,
        requests_per_minute: int = 60,
        burst_size: int = 10,
        exclude_paths: Optional[list] = None
    ):
        super().__init__(app)
        self.limiter = RateLimiter(requests_per_minute, burst_size)
        self.exclude_paths = exclude_paths or ["/health", "/docs", "/openapi.json"]
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        # Skip rate limiting for excluded paths
        if any(request.url.path.startswith(p) for p in self.exclude_paths):
            return await call_next(request)
        
        # Get client identifier (IP or API key)
        client_id = self._get_client_id(request)
        
        # Check rate limit
        if not await self.limiter.is_allowed(client_id):
            retry_after = self.limiter.get_retry_after(client_id)
            logger.warning(f"Rate limit exceeded for {client_id}")
            
            return JSONResponse(
                status_code=429,
                content={
                    "error": True,
                    "code": ErrorCode.RATE_LIMIT_EXCEEDED.value,
                    "message": "Rate limit exceeded",
                    "details": {"retry_after": retry_after}
                },
                headers={"Retry-After": str(retry_after)}
            )
        
        return await call_next(request)
    
    def _get_client_id(self, request: Request) -> str:
        """Extract client identifier from request."""
        # Check for API key first
        api_key = request.headers.get("X-API-Key")
        if api_key:
            return f"key:{api_key[:8]}"
        
        # Fall back to client IP
        forwarded_for = request.headers.get("X-Forwarded-For")
        if forwarded_for:
            return f"ip:{forwarded_for.split(',')[0].strip()}"
        
        return f"ip:{request.client.host if request.client else 'unknown'}"


# ============================================================
# Security Headers Middleware
# ============================================================

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """
    Adds security headers to all responses.
    
    Includes:
    - Content-Security-Policy
    - X-Content-Type-Options
    - X-Frame-Options
    - X-XSS-Protection
    - Referrer-Policy
    """
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        response = await call_next(request)
        
        # Add security headers
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Referrer-Policy"] = "strict-origin-when-cross-origin"
        response.headers["Permissions-Policy"] = "geolocation=(), microphone=(), camera=()"
        
        # Add CSP for API responses
        if request.url.path.startswith("/api") or request.url.path.startswith("/v1"):
            response.headers["Content-Security-Policy"] = "default-src 'none'"
        
        return response


# ============================================================
# Timeout Middleware
# ============================================================

class TimeoutMiddleware(BaseHTTPMiddleware):
    """
    Request timeout middleware.
    
    Cancels requests that exceed the timeout limit.
    """
    
    def __init__(self, app, timeout_seconds: int = 120):
        super().__init__(app)
        self.timeout = timeout_seconds
    
    async def dispatch(self, request: Request, call_next: Callable) -> Response:
        try:
            return await asyncio.wait_for(
                call_next(request),
                timeout=self.timeout
            )
        except asyncio.TimeoutError:
            request_id = getattr(request.state, "request_id", "unknown")
            logger.error(f"[{request_id}] Request timeout after {self.timeout}s")
            
            return JSONResponse(
                status_code=504,
                content={
                    "error": True,
                    "code": ErrorCode.TIMEOUT_ERROR.value,
                    "message": f"Request timed out after {self.timeout} seconds",
                    "details": {"timeout_seconds": self.timeout}
                }
            )


# ============================================================
# CORS Configuration
# ============================================================

def get_cors_config() -> dict:
    """
    Get CORS configuration for production.
    
    Returns conservative defaults that should be
    customized based on deployment environment.
    """
    import os
    
    # Get allowed origins from environment
    allowed_origins_str = os.getenv("CORS_ORIGINS", "*")
    
    if allowed_origins_str == "*":
        allowed_origins = ["*"]
    else:
        allowed_origins = [o.strip() for o in allowed_origins_str.split(",")]
    
    return {
        "allow_origins": allowed_origins,
        "allow_credentials": True,
        "allow_methods": ["GET", "POST", "PUT", "DELETE", "OPTIONS", "PATCH"],
        "allow_headers": [
            "Authorization",
            "Content-Type",
            "X-Request-ID",
            "X-API-Key",
            "Accept",
            "Origin",
        ],
        "expose_headers": [
            "X-Request-ID",
            "X-Response-Time",
            "X-RateLimit-Remaining",
        ],
        "max_age": 600,  # 10 minutes
    }
