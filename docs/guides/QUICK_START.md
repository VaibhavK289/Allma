# Quick Start Guide

Get Allma Studio up and running in minutes.

## Prerequisites

Choose one option:

### Option 1: Docker (Recommended)
- Docker Desktop installed

### Option 2: Local Setup
- Node.js 18+
- Python 3.11+
- Ollama installed

## One-Minute Start (Docker)

```bash
# Clone repository
git clone https://github.com/VaibhavK289/Allma.git
cd allma-studio

# Copy environment file
cp .env.example .env

# Start everything
docker compose up -d

# Open browser to http://localhost:3000
```

Done! The application is running locally with:
- Frontend at http://localhost:3000
- Backend API at http://localhost:8000
- Ollama at http://localhost:11434

## Manual Setup (5 minutes)

### Step 1: Install Ollama

Download and install from [ollama.ai](https://ollama.ai)

Then pull models:
```bash
ollama pull nomic-embed-text    # Required for RAG
ollama pull deepseek-r1:latest  # Or your preferred LLM
```

### Step 2: Start Backend

```bash
cd allma-backend
python -m venv venv

# Activate venv
# macOS/Linux:
source venv/bin/activate
# Windows:
.\venv\Scripts\activate

pip install -r requirements.txt
uvicorn main:app --reload
```

Backend API available at http://localhost:8000

### Step 3: Start Frontend

Open a new terminal:

```bash
cd allma-frontend
npm install
npm run dev
```

Frontend available at http://localhost:5173

### Step 4: Verify Installation

Check http://localhost:8000/docs for API documentation

## Configuration

Create `.env` file in project root:

```env
OLLAMA_HOST=http://localhost:11434
OLLAMA_MODEL=deepseek-r1:latest
OLLAMA_EMBEDDING_MODEL=nomic-embed-text:latest
VITE_API_URL=http://localhost:8000
```

## Using the Application

1. **Chat**: Type messages in the input box and press Enter or click Send
2. **Document Upload**: 
   - Click the upload button to select files
   - Or drag and drop into the chat area
   - Supported formats: PDF, DOCX, MD, TXT, HTML, JSON, CSV
3. **Enable RAG**: Toggle RAG button to ground responses in uploaded documents
4. **Switch Models**: Use the model dropdown to change LLM
5. **Dark Mode**: Toggle theme with sun/moon icon

## Troubleshooting

### "Cannot connect to Ollama"
```bash
# Check if Ollama is running
ollama serve

# Verify models are installed
ollama list

# Pull default models if missing
ollama pull nomic-embed-text
ollama pull deepseek-r1:latest
```

### Frontend blank page
- Clear browser cache (Ctrl+Shift+Delete)
- Check browser console for errors (F12)
- Verify backend is running on correct port

### Slow responses
- Check Ollama logs for errors
- Ensure your model is downloaded fully
- Try smaller model: `ollama pull llama3.2`

### Out of memory
- Reduce model size
- Close other applications
- Check available RAM

## Available Models

| Model | Size | Speed | Quality |
|-------|------|-------|---------|
| llama3.2 | 2GB | Very Fast | Good |
| gemma2:9b | 5.4GB | Medium | Excellent |
| qwen2.5-coder:7b | 4.7GB | Medium | Excellent |
| deepseek-r1:latest | 5.2GB | Slow | Excellent |

## Next Steps

1. Upload documents to try RAG
2. Explore different models
3. Customize settings
4. Read [Full Documentation](../../README.md)
5. Check [API Reference](../API.md)

## Support

- Review [README](../../README.md) for detailed information
- Check [API Documentation](../API.md)
- See [Contributing Guidelines](../../CONTRIBUTING.md)
- Report issues on GitHub

---

Happy chatting!
