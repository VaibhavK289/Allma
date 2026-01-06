"""
Main Application Entry Point

FastAPI application that integrates the orchestration layer
with HTTP endpoints for the Ollama RAG system.

Usage:
    uvicorn main:app --reload --host 0.0.0.0 --port 8000
    
Or:
    python main.py
"""

import asyncio
import logging
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


# Global orchestrator instance
orchestrator: Orchestrator = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """
    Application lifespan manager.
    
    Handles startup and shutdown of the orchestration layer.
    """
    global orchestrator
    
    # Startup
    logging.info("Starting Ollama RAG Orchestration Server...")
    
    # Initialize configuration from environment
    config = OrchestrationConfig.from_env()
    
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
    
    logging.info("Orchestration layer initialized successfully")
    logging.info(f"Active model: {config.ollama.model}")
    logging.info(f"Embedding model: {config.ollama.embedding_model}")
    
    yield
    
    # Shutdown
    logging.info("Shutting down orchestration layer...")
    if orchestrator:
        await orchestrator.shutdown()
    logging.info("Shutdown complete")


# Setup logging
setup_logging(level="INFO")

# Create FastAPI application
app = FastAPI(
    title="Ollama RAG Orchestration API",
    description="""
    ## Ollama RAG Orchestration Layer
    
    A comprehensive API for interacting with Ollama LLMs enhanced with 
    Retrieval-Augmented Generation (RAG) capabilities.
    
    ### Features
    
    - **Chat**: Conversational AI with context awareness
    - **RAG**: Document ingestion and semantic search
    - **Models**: LLM model management
    - **Health**: System health monitoring
    
    ### Architecture
    
    This API implements the orchestration layer as shown in the architectural diagrams:
    
    1. **RAG Pipeline**: Document → Chunks → Embeddings → Vector Store → Retrieval
    2. **Chat Flow**: Query → RAG Context → LLM → Response
    3. **Multi-turn**: Conversation context management
    """,
    version="1.0.0",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Configure appropriately for production
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Include routers
app.include_router(chat_router)
app.include_router(rag_router)
app.include_router(models_router)
app.include_router(health_router)


@app.get("/")
async def root():
    """
    Root endpoint - API information.
    """
    return {
        "name": "Ollama RAG Orchestration API",
        "version": "1.0.0",
        "description": "RAG-enhanced LLM orchestration layer for Ollama",
        "docs": "/docs",
        "health": "/health",
        "endpoints": {
            "chat": "/chat",
            "rag": "/rag",
            "models": "/models",
            "health": "/health"
        }
    }


if __name__ == "__main__":
    import uvicorn
    
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=8000,
        reload=True,
        log_level="info"
    )
