# Backend Services Documentation

This guide explains the backend architecture and service layer of Allma Studio.

## Overview

The backend is organized as a **microservices-inspired monolith** with clear separation of concerns:

- Presentation Layer (FastAPI Routes)
- Orchestration Layer (Central Coordinator)
- Service Layer (Domain-specific services)
- Data Access Layer (Databases and external APIs)

## Services

### RAGService
Handles Retrieval-Augmented Generation:
- Embedding generation via Ollama
- Vector similarity search in ChromaDB
- Result reranking for relevance
- Context assembly for LLM

### DocumentService
Processes and ingests documents:
- Multi-format file parsing (PDF, DOCX, MD, TXT, etc.)
- Intelligent text chunking with overlap
- Metadata extraction and preservation

### VectorStoreService
Manages vector embeddings storage:
- ChromaDB backend (with FAISS/Qdrant support)
- Similarity search operations
- Collection management

### ConversationService
Manages chat history and context:
- Conversation lifecycle management
- Message history tracking
- Memory and cache optimization

## Configuration

Backend configuration is managed in `orchestration/config.py`:

```python
from orchestration.config import OrchestrationConfig

config = OrchestrationConfig.from_env()
```

### Environment Variables

```env
# Ollama Configuration
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest

# Vector Store
VECTOR_STORE_PATH=./data/vectorstore
CHROMA_PERSIST_DIRECTORY=./data/vectorstore

# API Settings
API_HOST=0.0.0.0
API_PORT=8000
LOG_LEVEL=INFO
```

## API Endpoints

See [API Reference](../API.md) for complete endpoint documentation.

### Main Endpoints
- POST `/chat/` - Send chat message
- POST `/rag/ingest` - Ingest documents
- POST `/rag/search` - Search documents
- GET `/models/` - List available models
- GET `/health` - System health check

## Database

SQLite for conversation storage with async SQLAlchemy:
- Conversations table
- Messages table
- Message sources (RAG references)

ChromaDB for vector storage:
- Document embeddings
- Metadata indexing
- Similarity search

## Running the Backend

```bash
cd allma-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000
```

## Development

See [Contributing Guidelines](../../CONTRIBUTING.md) for development setup.

### Testing

```bash
pytest --cov=orchestration
```

### Type Checking

```bash
mypy orchestration/
```

## Troubleshooting

**"Cannot connect to Ollama"**
- Ensure Ollama is running: `ollama serve`
- Check OLLAMA_HOST env var matches your setup

**"Embedding model not found"**
- Pull the model: `ollama pull nomic-embed-text`
- Verify in Ollama: `ollama list`

**"ChromaDB error"**
- Check write permissions in `VECTOR_STORE_PATH`
- Ensure sufficient disk space

## Next Steps

- [API Documentation](../API.md)
- [System Architecture](../ARCHITECTURE.md)
- [Full README](../../README.md)
