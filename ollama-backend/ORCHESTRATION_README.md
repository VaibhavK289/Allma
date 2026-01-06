# Ollama RAG Orchestration Layer

A comprehensive orchestration layer for building RAG (Retrieval-Augmented Generation) applications with Ollama.

## Architecture Overview

This orchestration layer implements the architecture shown in the project diagrams:

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                           ORCHESTRATION LAYER                                │
├─────────────────────────────────────────────────────────────────────────────┤
│                                                                              │
│  ┌──────────────┐     ┌──────────────┐     ┌──────────────────────────────┐ │
│  │   Frontend   │────▶│  FastAPI     │────▶│       Orchestrator           │ │
│  │   (React)    │◀────│  API Routes  │◀────│  (Central Coordinator)       │ │
│  └──────────────┘     └──────────────┘     └──────────────────────────────┘ │
│                                                      │                       │
│                       ┌──────────────────────────────┼───────────────────┐  │
│                       │                              │                   │  │
│                       ▼                              ▼                   ▼  │
│              ┌──────────────┐            ┌──────────────┐      ┌──────────┐ │
│              │ RAG Service  │            │ Vector Store │      │  Ollama  │ │
│              │              │───────────▶│   Service    │      │  Client  │ │
│              │ - Retrieval  │            │              │      │          │ │
│              │ - Embedding  │            │ - ChromaDB   │      │ - LLM    │ │
│              │ - Reranking  │            │ - Search     │      │ - Embed  │ │
│              └──────────────┘            └──────────────┘      └──────────┘ │
│                       │                                                      │
│                       ▼                                                      │
│              ┌──────────────┐                                               │
│              │  Document    │                                               │
│              │  Service     │                                               │
│              │              │                                               │
│              │ - Loading    │                                               │
│              │ - Chunking   │                                               │
│              │ - Processing │                                               │
│              └──────────────┘                                               │
│                                                                              │
└─────────────────────────────────────────────────────────────────────────────┘
```

## Project Structure

```
ollama-backend/
├── main.py                      # FastAPI application entry point
├── requirements.txt             # Python dependencies
├── .env.example                 # Environment configuration template
├── orchestration/               # Core orchestration layer
│   ├── __init__.py
│   ├── config.py               # Configuration management
│   ├── orchestrator.py         # Central orchestrator
│   ├── models/                 # Data models & schemas
│   │   ├── __init__.py
│   │   └── schemas.py          # Pydantic models
│   ├── services/               # Business logic services
│   │   ├── __init__.py
│   │   ├── rag_service.py      # RAG pipeline
│   │   ├── vector_store_service.py
│   │   ├── document_service.py
│   │   └── conversation_service.py
│   ├── routes/                 # API endpoints
│   │   ├── __init__.py
│   │   ├── chat.py
│   │   ├── rag.py
│   │   ├── models.py
│   │   └── health.py
│   └── utils/                  # Utilities
│       ├── __init__.py
│       ├── logger.py
│       └── helpers.py
└── data/                       # Runtime data (created automatically)
    ├── vectorstore/
    ├── temp/
    └── processed/
```

## Quick Start

### Prerequisites

- Python 3.10+
- Ollama installed and running
- Required Ollama models:
  - LLM: `llama3.2` (or your preferred model)
  - Embeddings: `nomic-embed-text`

### Installation

1. **Install dependencies:**
   ```bash
   cd ollama-backend
   pip install -r requirements.txt
   ```

2. **Configure environment:**
   ```bash
   cp .env.example .env
   # Edit .env with your settings
   ```

3. **Pull required Ollama models:**
   ```bash
   ollama pull llama3.2
   ollama pull nomic-embed-text
   ```

4. **Start the server:**
   ```bash
   uvicorn main:app --reload --host 0.0.0.0 --port 8000
   ```

5. **Access the API:**
   - API Documentation: http://localhost:8000/docs
   - ReDoc: http://localhost:8000/redoc
   - Health Check: http://localhost:8000/health

## API Endpoints

### Chat
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/chat/` | Send a chat message |
| POST | `/chat/stream` | Stream chat response |
| GET | `/chat/conversation/{id}` | Get conversation |
| DELETE | `/chat/conversation/{id}` | Delete conversation |
| GET | `/chat/conversations` | List all conversations |

### RAG
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | `/rag/ingest` | Ingest text/file path |
| POST | `/rag/ingest/upload` | Upload and ingest file |
| POST | `/rag/search` | Semantic search |
| GET | `/rag/stats` | Get RAG statistics |

### Models
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/models/` | List available models |
| POST | `/models/switch` | Switch active model |
| POST | `/models/pull` | Pull new model |

### Health
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/health/` | Full health check |
| GET | `/health/live` | Liveness probe |
| GET | `/health/ready` | Readiness probe |

## Usage Examples

### Chat with RAG

```python
import requests

# Send a message with RAG enabled
response = requests.post("http://localhost:8000/chat/", json={
    "message": "What is machine learning?",
    "use_rag": True,
    "conversation_id": "my-conversation"
})

print(response.json()["content"])
```

### Ingest Documents

```python
# Ingest text directly
requests.post("http://localhost:8000/rag/ingest", json={
    "text": "Machine learning is a subset of AI...",
    "source": "ml_intro",
    "metadata": {"category": "AI"}
})

# Upload a file
with open("document.pdf", "rb") as f:
    requests.post(
        "http://localhost:8000/rag/ingest/upload",
        files={"file": f}
    )
```

### Semantic Search

```python
response = requests.post("http://localhost:8000/rag/search", json={
    "query": "neural networks",
    "top_k": 5
})

for result in response.json()["results"]:
    print(f"[{result['score']:.2f}] {result['content'][:100]}...")
```

## Configuration

All configuration can be set via environment variables:

| Variable | Default | Description |
|----------|---------|-------------|
| `OLLAMA_HOST` | `http://localhost:11434` | Ollama server URL |
| `OLLAMA_MODEL` | `llama3.2` | Default LLM model |
| `OLLAMA_EMBEDDING_MODEL` | `nomic-embed-text` | Embedding model |
| `OLLAMA_TEMPERATURE` | `0.7` | Generation temperature |
| `VECTOR_STORE_TYPE` | `chromadb` | Vector store backend |
| `RAG_CHUNK_SIZE` | `1000` | Document chunk size |
| `RAG_CHUNK_OVERLAP` | `200` | Chunk overlap |
| `RAG_TOP_K` | `5` | Results per search |

## Key Components

### Orchestrator

The central coordinator that manages all services and handles request routing.

```python
from orchestration import Orchestrator, OrchestrationConfig

config = OrchestrationConfig.from_env()
orchestrator = Orchestrator(config)
await orchestrator.initialize()

# Chat with RAG
response = await orchestrator.chat(
    message="Explain quantum computing",
    use_rag=True
)
```

### RAG Service

Handles the retrieval-augmented generation pipeline:
1. Query embedding generation
2. Vector similarity search
3. Result reranking
4. Context assembly

### Document Service

Processes documents through the ingestion pipeline:
1. Multi-format loading (PDF, DOCX, MD, etc.)
2. Text extraction and cleaning
3. Intelligent chunking with overlap
4. Metadata extraction

### Vector Store Service

Manages vector embeddings with pluggable backends:
- ChromaDB (default)
- FAISS (optional)
- Qdrant (optional)

## Development

### Running Tests

```bash
pytest tests/ -v
```

### Code Style

```bash
# Format code
black orchestration/

# Check linting
ruff check orchestration/
```

## License

MIT License
