"""
Main Application Entry Point

Production-ready FastAPI application with:
- Comprehensive error handling
- Request logging and tracing
- Rate limiting
- Security headers
- Database persistence
- Health checks

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    
Or:
    python main.py
"""

import asyncio
import logging
import os
from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from orchestration import Orchestrator, OrchestrationConfig
from orchestration.routes import chat_router, rag_router, models_router, health_router
from orchestration.routes.chat import set_orchestrator as set_chat_orchestrator
from orchestration.routes.rag import set_orchestrator as set_rag_orchestrator
from orchestration.routes.models import set_orchestrator as set_models_orchestrator
from orchestration.routes.health import set_orchestrator as set_health_orchestrator
from orchestration.utils import setup_logging
from orchestration.middleware import (
    RequestIDMiddleware,
    LoggingMiddleware,
    ErrorHandlerMiddleware,
    RateLimitMiddleware,
    SecurityHeadersMiddleware,
    TimeoutMiddleware,
    get_cors_config
)
from orchestration.database import DatabaseManager


# Global instances
orchestrator: Orchestrator = None
database: DatabaseManager = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown of all services:
    - Database connection
    - Orchestration layer
    - Vector store
    - Service health checks
    """
    global orchestrator, database
    
    # ===== STARTUP =====
    logging.info("=" * 60)
    logging.info("Starting Allma AI Backend Server...")
    logging.info("=" * 60)
    
    try:
        # Initialize database
        logging.info("Initializing database...")
        database = DatabaseManager()
        await database.initialize()
        
        # Initialize configuration from environment
        config = OrchestrationConfig.from_env()
        logging.info(f"Configuration loaded:")
        logging.info(f"  → Ollama Host: {config.ollama.host}")
        logging.info(f"  → LLM Model: {config.ollama.model}")
        logging.info(f"  → Embedding Model: {config.ollama.embedding_model}")
        logging.info(f"  → Vector Store: {config.vector_store.store_type}")
        
        # Create and initialize orchestrator
        orchestrator = Orchestrator(config)
        result = await orchestrator.initialize()
        
        if not result.success:
            logging.error(f"Failed to initialize orchestrator: {result.error}")
            raise RuntimeError(f"Initialization failed: {result.error}")
        
        # Set orchestrator for all routes
        set_chat_orchestrator(orchestrator)
        set_rag_orchestrator(orchestrator)
        set_models_orchestrator(orchestrator)
        set_health_orchestrator(orchestrator)
        
        logging.info("=" * 60)
        logging.info("✓ All services initialized successfully")
        logging.info("✓ API ready at http://localhost:8000")
        logging.info("✓ Docs available at http://localhost:8000/docs")
        logging.info("=" * 60)
        
    except Exception as e:
        logging.error(f"Startup failed: {e}")
        raise
    
    yield
    
    # ===== SHUTDOWN =====
    logging.info("=" * 60)
    logging.info("Shutting down services...")
    
    if orchestrator:
        await orchestrator.shutdown()
    
    if database:
        await database.close()
    
    logging.info("Shutdown complete")
    logging.info("=" * 60)


# Setup logging
setup_logging(level=os.getenv("LOG_LEVEL", "INFO"))

# Create FastAPI application
app = FastAPI(
    title="Allma AI Backend API",
    description="""
## Allma AI - RAG-Powered Local LLM Platform

A production-ready API for interacting with local Ollama LLMs enhanced 
with Retrieval-Augmented Generation (RAG) capabilities.

### Features

- **🤖 Chat**: Natural language conversations with AI
- **📚 RAG**: Document ingestion and intelligent retrieval
- **⚡ Streaming**: Real-time token streaming
- **🔒 Privacy**: All data stays local
- **📊 Analytics**: Usage metrics and insights

### Architecture

```
Frontend → FastAPI → Orchestrator → Services → Ollama/ChromaDB
                          ↓
                   RAG Pipeline:
                   Query → Embed → Search → Rerank → Context → LLM
```

### Quick Start

1. Ensure Ollama is running with required models
2. POST to `/chat/` with your message
3. Use `/rag/ingest` to add documents to knowledge base
4. Enable RAG in chat requests for context-aware responses
    """,
    version="2.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
    openapi_tags=[
        {"name": "Chat", "description": "Chat and conversation endpoints"},
        {"name": "RAG", "description": "Document ingestion and retrieval"},
        {"name": "Models", "description": "LLM model management"},
        {"name": "Health", "description": "System health and status"},
    ]
)

# ============================================================
# Middleware Stack (order matters - executed bottom to top)
# ============================================================

# 1. Security headers (outermost)
app.add_middleware(SecurityHeadersMiddleware)

# 2. Request timeout
app.add_middleware(TimeoutMiddleware, timeout_seconds=120)

# 3. Error handling
app.add_middleware(ErrorHandlerMiddleware)

# 4. Request logging
app.add_middleware(LoggingMiddleware)

# 5. Rate limiting
if os.getenv("ENABLE_RATE_LIMIT", "true").lower() == "true":
    app.add_middleware(
        RateLimitMiddleware,
        requests_per_minute=int(os.getenv("RATE_LIMIT_RPM", "60")),
        burst_size=int(os.getenv("RATE_LIMIT_BURST", "10"))
    )

# 6. Request ID tracking
app.add_middleware(RequestIDMiddleware)

# 7. CORS (innermost)
cors_config = get_cors_config()
app.add_middleware(
    CORSMiddleware,
    **cors_config
)

# ============================================================
# Include API Routers
# ============================================================

app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(models_router)
app.include_router(health_router)


# ============================================================
# Root Endpoints
# ============================================================

@app.get("/", tags=["Root"])
async def root():
    """
    API Information and Navigation.
    
    Returns basic API information and available endpoints.
    """
    return {
        "name": "Allma AI Backend API",
        "version": "2.0.0",
        "description": "RAG-enhanced LLM orchestration with local Ollama models",
        "status": "operational",
        "documentation": {
            "swagger": "/docs",
            "redoc": "/redoc",
            "openapi": "/openapi.json"
        },
        "endpoints": {
            "chat": "/chat/",
            "rag": "/rag/",
            "models": "/models/",
            "health": "/health/"
        },
        "links": {
            "github": "https://github.com/allma-studio",
            "ollama": "https://ollama.ai"
        }
    }


@app.get("/api/v1", tags=["Root"])
async def api_v1():
    """API v1 version info."""
    return {
        "api_version": "v1",
        "status": "active",
        "deprecation_date": None
    }


# ============================================================
# Main Entry Point
# ============================================================

if __name__ == "__main__":
    import uvicorn
    
    # Production settings
    host = os.getenv("HOST", "0.0.0.0")
    port = int(os.getenv("PORT", "8000"))
    workers = int(os.getenv("WORKERS", "1"))
    reload = os.getenv("RELOAD", "true").lower() == "true"
    
    print(f"""
╔═══════════════════════════════════════════════════════════════╗
║                    ALLMA AI BACKEND                           ║
║═══════════════════════════════════════════════════════════════║
║  Host:     {host}                                          ║
║  Port:     {port}                                              ║
║  Workers:  {workers}                                               ║
║  Reload:   {reload}                                            ║
║───────────────────────────────────────────────────────────────║
║  Docs:     http://{host}:{port}/docs                            ║
║  Health:   http://{host}:{port}/health                          ║
╚═══════════════════════════════════════════════════════════════╝
    """)
    
    uvicorn.run(
        "main:app",
        host=host,
        port=port,
        workers=workers if not reload else 1,
        reload=reload,
        log_level="info",
        access_log=True
    )
