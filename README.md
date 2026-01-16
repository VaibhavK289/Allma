# Allma Studio

<div align="center">

![Allma Studio Banner](https://img.shields.io/badge/Allma_Studio-AI_Powered-6366f1?style=for-the-badge&logo=openai&logoColor=white)

[![React](https://img.shields.io/badge/React-18.3.1-61dafb?style=flat-square&logo=react)](https://reactjs.org/)
[![FastAPI](https://img.shields.io/badge/FastAPI-0.115-009688?style=flat-square&logo=fastapi)](https://fastapi.tiangolo.com/)
[![Python](https://img.shields.io/badge/Python-3.11+-3776ab?style=flat-square&logo=python)](https://python.org/)
[![Tailwind CSS](https://img.shields.io/badge/Tailwind-3.4.3-38bdf8?style=flat-square&logo=tailwindcss)](https://tailwindcss.com/)
[![Vite](https://img.shields.io/badge/Vite-5.2-646cff?style=flat-square&logo=vite)](https://vitejs.dev/)
[![Ollama](https://img.shields.io/badge/Ollama-Local_LLM-000000?style=flat-square)](https://ollama.ai/)
[![Docker](https://img.shields.io/badge/Docker-Ready-2496ed?style=flat-square&logo=docker)](https://docker.com/)
[![License](https://img.shields.io/badge/License-MIT-green?style=flat-square)](LICENSE)

**A privacy-first, local AI chat application with RAG capabilities**

[Live Demo](https://allma-studio.vercel.app) • [Documentation](#-documentation) • [Getting Started](#-quick-start) • [API Reference](#-api-reference)

</div>

---

## Table of Contents

- [Overview](#overview)
- [Features](#features)
- [Architecture](#architecture)
- [Tech Stack](#tech-stack)
- [Quick Start](#quick-start)
- [Installation](#installation)
- [Configuration](#configuration)
- [API Reference](#api-reference)
- [Deployment](#deployment)
- [Project Structure](#project-structure)
- [Contributing](#contributing)
- [License](#license)

---

## Overview

**Allma Studio** is a full-stack AI chat application that runs entirely on your local machine, ensuring complete privacy and data control. It combines the power of local Large Language Models (LLMs) via Ollama with Retrieval-Augmented Generation (RAG) to provide intelligent, context-aware responses based on your own documents.

### Why Allma Studio?

| Traditional AI Chat | Allma Studio |
|---------------------|--------------|
| Data sent to cloud servers | 100% local processing |
| Pay-per-token pricing | Free after setup |
| Requires internet | Works offline |
| Privacy concerns | Your data stays yours |
| Generic responses | RAG-powered with your docs |

---

## Features

### AI Capabilities
- **Local LLM Integration** - Run powerful models like DeepSeek, Gemma, Qwen, and LLaMA locally via Ollama
- **RAG Pipeline** - Upload documents and get AI responses grounded in your own data
- **Smart Chunking** - Intelligent document splitting for optimal context retrieval
- **Semantic Search** - ChromaDB-powered vector similarity search
- **Conversation Memory** - Persistent chat history with context awareness

### User Interface
- **Modern React UI** - Clean, responsive design with TailwindCSS
- **Real-time Streaming** - Token-by-token response streaming for better UX
- **Dark/Light Mode** - Automatic theme detection with manual toggle
- **Markdown Rendering** - Rich text formatting with syntax highlighting
- **Mobile Responsive** - Works seamlessly on all device sizes

### Developer Experience
- **FastAPI Backend** - High-performance async Python API
- **Hot Reload** - Both frontend and backend with development hot-reload
- **Type Safety** - Pydantic models and TypeScript-ready API
- **Docker Ready** - One-command deployment with Docker Compose
- **Comprehensive Logging** - Structured logging with configurable levels

### Security & Privacy
- **No Data Collection** - Zero telemetry, your data never leaves your machine
- **CORS Protection** - Configurable cross-origin security
- **Rate Limiting** - Built-in API rate limiting
- **Non-root Containers** - Security-hardened Docker images

---

## Architecture

### System Architecture

<div align="center">

![System Architecture](diagrams/architecture-diagram.jpg)

</div>

The system follows a **layered architecture** with clear separation of concerns:

- **Frontend Layer**: React SPA with TailwindCSS, communicates via REST API
- **API Gateway**: FastAPI with async request handling
- **Orchestration Layer**: Central coordinator managing all services
- **Service Layer**: Domain-specific services (RAG, Document, Conversation, Vector Store)
- **Data Layer**: ChromaDB for vectors, SQLite for conversations, Ollama for LLM

### RAG Pipeline Architecture

<div align="center">

![RAG Implementation Architecture](diagrams/RAG_Implementation_Architecture_Diagram.jpg)

</div>

The RAG (Retrieval-Augmented Generation) pipeline implements:

1. **Query Processing**: User query embedding via Nomic Embed Text
2. **Vector Search**: Semantic similarity search in ChromaDB
3. **Context Ranking**: Relevance scoring and filtering
4. **Prompt Augmentation**: Context injection into LLM prompt
5. **Response Generation**: Streaming response from Ollama

### Document Ingestion Flow

<div align="center">

![RAG Ingestion Pipeline](diagrams/RAG_ingestion_Diagram.png)

</div>

Document ingestion follows these stages:
- **Loading**: Support for TXT, MD, PDF, DOCX, HTML, JSON, CSV
- **Extraction**: Text extraction with metadata preservation
- **Chunking**: Intelligent splitting with overlap for context continuity
- **Embedding**: Vector generation via Ollama embeddings API
- **Storage**: Persistent storage in ChromaDB

### Data Model

<div align="center">

![Entity Relationship Diagram](diagrams/Entity_Relationship_Diagram.png)

</div>

Key entities:
- **Documents** → split into **Chunks** → converted to **Embeddings**
- **Conversations** → contain **Messages** → reference **Sources**

---

## Tech Stack

### Frontend

| Technology | Version | Purpose |
|------------|---------|---------|
| React | 18.3.1 | UI Framework |
| Vite | 5.2.11 | Build Tool & Dev Server |
| TailwindCSS | 3.4.3 | Utility-first CSS |
| Axios | 1.7.2 | HTTP Client |
| React Markdown | 9.0.1 | Markdown Rendering |
| Lucide React | 0.378.0 | Icon System |

### Backend

| Technology | Version | Purpose |
|------------|---------|---------|
| Python | 3.11+ | Runtime |
| FastAPI | 0.115.0 | Web Framework |
| Uvicorn | 0.31.1 | ASGI Server |
| SQLAlchemy | 2.0.36 | Database ORM |
| ChromaDB | 0.5.17 | Vector Database |
| aiosqlite | 0.20.0 | Async SQLite |
| httpx | 0.28.1 | Async HTTP Client |
| python-multipart | 0.0.17 | File Upload Handling |

### AI/ML

| Technology | Purpose |
|------------|---------|
| Ollama | Local LLM Runtime |
| Nomic Embed Text | Embeddings Model |
| DeepSeek R1 | Reasoning LLM |
| Gemma 2 9B | General Purpose LLM |
| Qwen 2.5 Coder | Code-focused LLM |

### Infrastructure

| Technology | Purpose |
|------------|---------|
| Docker | Containerization |
| Docker Compose | Multi-container Orchestration |
| Nginx | Reverse Proxy |
| Kubernetes | Container Orchestration |
| Helm | K8s Package Manager |
| GitHub Actions | CI/CD |
| Vercel | Frontend Hosting |

---

## Quick Start

### Prerequisites

- **Docker Desktop** (recommended) OR:
  - Node.js 18+
  - Python 3.11+
  - Ollama installed and running

### One-Command Start (Docker)

```bash
# Clone the repository
git clone https://github.com/yourusername/allma-studio.git
cd allma-studio

# Copy environment file
cp .env.example .env

# Start all services
docker compose up -d

# Open in browser
open http://localhost:3000
```

### Manual Start (Development)

```bash
# Terminal 1: Start Ollama
ollama serve

# Terminal 2: Start Backend
cd allma-backend
pip install -r requirements.txt
uvicorn main:app --reload --port 8000

# Terminal 3: Start Frontend
cd allma-frontend
npm install
npm run dev
```

---

## Installation

### 1. Clone Repository

```bash
git clone https://github.com/yourusername/allma-studio.git
cd allma-studio
```

### 2. Install Ollama & Models

```bash
# Install Ollama (macOS)
brew install ollama

# Install Ollama (Linux)
curl -fsSL https://ollama.ai/install.sh | sh

# Install Ollama (Windows)
# Download from https://ollama.ai/download

# Pull required models
ollama pull nomic-embed-text    # Required for embeddings
ollama pull deepseek-r1:latest  # Recommended LLM
# OR choose another model:
ollama pull gemma2:9b
ollama pull qwen2.5-coder:7b
```

### 3. Backend Setup

```bash
cd allma-backend

# Create virtual environment
python -m venv venv

# Activate (Linux/macOS)
source venv/bin/activate
# Activate (Windows)
.\venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Start server
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

### 4. Frontend Setup

```bash
cd allma-frontend

# Install dependencies
npm install

# Start development server
npm run dev
```

### 5. Access Application

- **Frontend**: http://localhost:5173
- **Backend API**: http://localhost:8000
- **API Documentation**: http://localhost:8000/docs
- **Ollama**: http://localhost:11434

---

## Configuration

### Environment Variables

Create a `.env` file in the root directory:

```env
# Backend Configuration
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

# Frontend Configuration
VITE_API_URL=http://localhost:8000

# Optional: Cloud LLM (for production without local Ollama)
GROQ_API_KEY=your-groq-api-key
OPENAI_API_KEY=your-openai-api-key
```

### Model Configuration

| Model | Size | Best For | Command |
|-------|------|----------|---------|
| `deepseek-r1:latest` | 5.2GB | Reasoning, Analysis | `ollama pull deepseek-r1:latest` |
| `deepseek-r1:8b` | 5.2GB | Balanced Performance | `ollama pull deepseek-r1:8b` |
| `gemma2:9b` | 5.4GB | General Purpose | `ollama pull gemma2:9b` |
| `qwen2.5-coder:7b` | 4.7GB | Code Generation | `ollama pull qwen2.5-coder:7b` |
| `llama3.2` | 2.0GB | Fast Responses | `ollama pull llama3.2` |
| `nomic-embed-text` | 274MB | Embeddings (Required) | `ollama pull nomic-embed-text` |

---

## API Reference

### Base URL
```
http://localhost:8000/api
```

### Endpoints

#### Health Check
```http
GET /health
```
Returns system health status including Ollama connectivity.

**Response:**
```json
{
  "status": "healthy",
  "ollama_connected": true,
  "vector_store_ready": true,
  "timestamp": "2024-01-15T10:30:00Z"
}
```

#### Chat
```http
POST /chat/
```
Send a message and receive AI response.

**Request Body:**
```json
{
  "message": "Explain quantum computing",
  "use_rag": true,
  "conversation_id": "optional-uuid",
  "stream": true
}
```

**Response (Streaming):**
```text
data: {"content": "Quantum", "done": false}
data: {"content": " computing", "done": false}
data: {"content": " is...", "done": false}
data: {"content": "", "done": true, "sources": [...]}
```

#### Document Ingestion
```http
POST /rag/ingest
```
Upload and process documents for RAG.

**Request (multipart/form-data):**
- `file`: Document file (PDF, TXT, MD, DOCX)

**Response:**
```json
{
  "success": true,
  "document_id": "uuid",
  "chunks_created": 15,
  "message": "Document processed successfully"
}
```

#### List Models
```http
GET /models/
```
Get available Ollama models.

**Response:**
```json
{
  "models": [
    {
      "name": "deepseek-r1:latest",
      "size": "5.2GB",
      "modified": "2024-01-15T10:00:00Z"
    }
  ]
}
```

#### Switch Model
```http
POST /models/switch
```
Change the active LLM model.

**Request Body:**
```json
{
  "model_name": "gemma2:9b"
}
```

### Error Responses

```json
{
  "detail": {
    "error": "Error type",
    "message": "Human readable message",
    "code": "ERROR_CODE"
  }
}
```

| Code | Status | Description |
|------|--------|-------------|
| 400 | Bad Request | Invalid request format |
| 404 | Not Found | Resource not found |
| 500 | Server Error | Internal server error |
| 503 | Service Unavailable | Ollama not connected |

---

## 🚢 Deployment

### Docker Compose (Recommended)

```bash
# Development
docker compose up -d

# Production
docker compose -f docker-compose.prod.yml up -d
```

### Kubernetes

```bash
# Using Kustomize
kubectl apply -k k8s/overlays/production

# Using Helm
helm install allma-studio ./helm/allma-studio
```

### Vercel (Frontend Only)

The frontend can be deployed to Vercel with demo mode:

```bash
cd allma-frontend
npx vercel --prod
```

Demo mode provides a simulated AI experience without requiring a backend.

### Cloud Providers

| Provider | Frontend | Backend | Ollama |
|----------|----------|---------|--------|
| Vercel | Yes (Native) | No | No |
| Railway | Yes (Docker) | Yes (Docker) | No |
| Render | Yes (Static) | Yes (Docker) | No |
| AWS ECS | Yes (Docker) | Yes (Docker) | Yes (GPU instances) |
| GCP Cloud Run | Yes (Docker) | Yes (Docker) | Yes (GPU instances) |

For detailed deployment instructions, see [DEPLOYMENT.md](DEPLOYMENT.md).

---

## Project Structure

```
allma-studio/
├── 📂 allma-backend/           # FastAPI Backend
│   ├── main.py                 # Application entry point
│   ├── requirements.txt        # Python dependencies
│   ├── Dockerfile              # Backend container
│   ├── 📂 orchestration/       # Core business logic
│   │   ├── orchestrator.py     # Central coordinator
│   │   ├── config.py           # Configuration management
│   │   ├── database.py         # Database connections
│   │   ├── 📂 models/          # Pydantic schemas
│   │   ├── 📂 routes/          # API endpoints
│   │   │   ├── chat.py         # Chat endpoints
│   │   │   ├── rag.py          # RAG endpoints
│   │   │   ├── models.py       # Model management
│   │   │   └── health.py       # Health checks
│   │   ├── 📂 services/        # Business services
│   │   │   ├── rag_service.py
│   │   │   ├── document_service.py
│   │   │   ├── vector_store_service.py
│   │   │   └── conversation_service.py
│   │   └── 📂 utils/           # Utilities
│   └── 📂 data/                # Persistent data
│       └── vectorstore/        # ChromaDB data
│
├── 📂 allma-frontend/          # React Frontend
│   ├── package.json            # Node dependencies
│   ├── vite.config.js          # Vite configuration
│   ├── tailwind.config.js      # Tailwind configuration
│   ├── Dockerfile              # Frontend container
│   ├── vercel.json             # Vercel deployment
│   ├── 📂 src/
│   │   ├── main.jsx            # React entry point
│   │   ├── App.jsx             # Root component
│   │   ├── 📂 components/      # React components
│   │   ├── 📂 hooks/           # Custom React hooks
│   │   ├── 📂 services/        # API services
│   │   │   ├── api.js          # Backend API client
│   │   │   └── demoApi.js      # Demo mode fallback
│   │   └── 📂 assets/          # Static assets
│   └── 📂 nginx/               # Nginx configs
│
├── 📂 k8s/                     # Kubernetes manifests
│   ├── 📂 base/                # Base configurations
│   └── 📂 overlays/            # Environment overlays
│       ├── staging/
│       └── production/
│
├── 📂 helm/                    # Helm charts
│   └── allma-studio/
│
├── 📂 .github/                 # GitHub configurations
│   └── workflows/              # CI/CD pipelines
│
├── docker-compose.yml          # Development compose
├── docker-compose.prod.yml     # Production compose
├── .env.example                # Environment template
├── DEPLOYMENT.md               # Deployment guide
└── README.md                   # This file
```

---

## Contributing

We welcome contributions! Please follow these steps:

### 1. Fork & Clone

```bash
git clone https://github.com/yourusername/allma-studio.git
cd allma-studio
git checkout -b feature/your-feature
```

### 2. Development Setup

```bash
# Install pre-commit hooks
pip install pre-commit
pre-commit install

# Setup backend
cd allma-backend
pip install -r requirements.txt

# Setup frontend
cd allma-frontend
npm install
```

### 3. Code Standards

- **Python**: Follow PEP 8, use type hints
- **JavaScript**: ESLint + Prettier
- **Commits**: Conventional commits (`feat:`, `fix:`, `docs:`)

### 4. Submit PR

1. Write tests for new features
2. Update documentation
3. Create Pull Request with description

---

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## Acknowledgments

- [Ollama](https://ollama.ai/) - Local LLM runtime
- [FastAPI](https://fastapi.tiangolo.com/) - Modern Python web framework
- [React](https://react.dev/) - UI library
- [TailwindCSS](https://tailwindcss.com/) - CSS framework
- [ChromaDB](https://www.trychroma.com/) - Vector database

---

<div align="center">

**Built with passion for privacy-conscious AI enthusiasts**

[Back to Top](#allma-studio)

</div>
