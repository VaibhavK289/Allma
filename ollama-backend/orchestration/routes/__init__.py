"""
API Routes for the Orchestration Layer

Provides FastAPI routers for:
- Chat endpoints
- RAG/Search endpoints
- Document ingestion
- Model management
- Health checks
"""

from .chat import router as chat_router
from .rag import router as rag_router
from .models import router as models_router
from .health import router as health_router

__all__ = [
    "chat_router",
    "rag_router",
    "models_router",
    "health_router",
]
