# Copilot Instructions for Ollama RAG Application

## Architecture Overview

This is a **full-stack RAG (Retrieval-Augmented Generation) application** with:
- **Backend**: FastAPI orchestration layer (`ollama-backend/`) connecting to local Ollama LLMs
- **Frontend**: React + Vite SPA (`ollama-frontend/`) with Tailwind CSS

### Core Data Flow
```
Frontend → FastAPI Routes → Orchestrator → Services → Ollama/ChromaDB
```

The **Orchestrator** ([orchestration/orchestrator.py](ollama-backend/orchestration/orchestrator.py)) is the central facade coordinating:
- `RAGService` - embeddings, retrieval, reranking
- `VectorStoreService` - ChromaDB persistence
- `DocumentService` - file parsing, chunking
- `ConversationService` - chat history

## Backend Patterns

### Service Initialization
All services use async `initialize()` pattern. The app lifecycle in [main.py](ollama-backend/main.py) wires orchestrator to routes via `set_orchestrator()` functions:
```python
# Routes receive orchestrator via dependency injection
orchestrator: Orchestrator = Depends(get_orchestrator)
```

### Adding New API Endpoints
1. Create route file in `orchestration/routes/`
2. Define router with prefix: `router = APIRouter(prefix="/new", tags=["New"])`
3. Add `set_orchestrator()` and `get_orchestrator()` functions
4. Register in [main.py](ollama-backend/main.py) and include router

### Pydantic Models
Request/response models live in [orchestration/models/schemas.py](ollama-backend/orchestration/models/schemas.py). Use `@dataclass` for internal data (e.g., `ChatMessage`), `BaseModel` for API contracts.

### Configuration
All config uses dataclasses with `from_env()` factory methods in [config.py](ollama-backend/orchestration/config.py):
```python
config = OrchestrationConfig.from_env()  # Reads from environment
```

Key env vars: `OLLAMA_HOST`, `OLLAMA_MODEL`, `OLLAMA_EMBEDDING_MODEL`, `VECTOR_STORE_PATH`

## Required Ollama Models

Available locally:
- **LLM**: `deepseek-r1:latest` (5.2GB), `gemma2:9b` (5.4GB), `qwen2.5-coder:7b` (4.7GB), `deepseek-r1:8b` (5.2GB)
- **Embeddings**: `nomic-embed-text:latest` (274MB) - **required for RAG**

**Note**: Default config in [config.py](ollama-backend/orchestration/config.py) is `llama3.2`, which is not installed locally. Set via environment:
```bash
export OLLAMA_MODEL=deepseek-r1:latest  # or your preferred model
```

## Development Workflows

### Backend
```bash
cd ollama-backend
pip install -r requirements.txt
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```
API docs at `http://localhost:8000/docs`

### Frontend  
```bash
cd ollama-frontend
npm install
npm run dev
```

### Testing RAG Pipeline
1. Start backend with Ollama running
2. POST to `/rag/ingest` with file_path or text
3. Query via `/chat/` with `use_rag: true`

## Key Conventions

- **Async everywhere**: All service methods are `async`. Use `asyncio.gather()` for parallel operations.
- **Result wrapper**: Operations return `OrchestrationResult(success, data, error)` - always check `.success`
- **Logging**: Use `from orchestration.utils import setup_logging` - each module has its own logger
- **Vector store abstraction**: `VectorStoreBackend` ABC allows swapping ChromaDB for FAISS/Qdrant

## File Structure Quick Reference

| Path | Purpose |
|------|---------|
| `orchestration/orchestrator.py` | Central coordinator - start here for flow understanding |
| `orchestration/services/rag_service.py` | Embedding generation, retrieval, reranking logic |
| `orchestration/services/vector_store_service.py` | ChromaDB wrapper with fallback |
| `orchestration/routes/*.py` | FastAPI endpoints by domain |
| `orchestration/config.py` | All configuration dataclasses |
