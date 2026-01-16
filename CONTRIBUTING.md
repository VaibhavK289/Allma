# Contributing to Allma Studio

Thank you for your interest in contributing to Allma Studio! This document provides guidelines and instructions for contributing.

## Table of Contents

- [Code of Conduct](#code-of-conduct)
- [Getting Started](#getting-started)
- [Development Setup](#development-setup)
- [Making Changes](#making-changes)
- [Pull Request Process](#pull-request-process)
- [Coding Standards](#coding-standards)
- [Testing](#testing)
- [Documentation](#documentation)

---

## Code of Conduct

### Our Pledge

We are committed to providing a welcoming and inclusive environment. We pledge to:

- Be respectful and constructive in all interactions
- Welcome diverse perspectives and experiences
- Accept constructive criticism gracefully
- Focus on what is best for the community
- Show empathy towards other community members

### Unacceptable Behavior

- Harassment or discrimination of any kind
- Trolling, insulting, or derogatory comments
- Public or private harassment
- Publishing others' private information without permission

---

## Getting Started

### Finding Issues

1. **Good First Issues** - Look for issues labeled `good-first-issue`
2. **Help Wanted** - Issues labeled `help-wanted` need contributors
3. **Bug Reports** - Help fix reported bugs
4. **Feature Requests** - Implement requested features

### Before You Start

1. Check if the issue is already being worked on
2. Comment on the issue to claim it
3. Wait for maintainer confirmation if it's a large change
4. Fork the repository

---

## Development Setup

### Prerequisites

- **Python 3.11+** with pip
- **Node.js 18+** with npm
- **Ollama** installed and running
- **Git** for version control
- **Docker** (optional, for containerized development)

### Step-by-Step Setup

```bash
# 1. Fork and clone the repository
git clone https://github.com/YOUR_USERNAME/allma-studio.git
cd allma-studio

# 2. Add upstream remote
git remote add upstream https://github.com/ORIGINAL_OWNER/allma-studio.git

# 3. Create a feature branch
git checkout -b feature/your-feature-name

# 4. Set up backend
cd allma-backend
python -m venv venv
source venv/bin/activate  # Windows: .\venv\Scripts\activate
pip install -r requirements.txt
pip install -r requirements-dev.txt  # Development dependencies

# 5. Set up frontend
cd ../allma-frontend
npm install

# 6. Set up pre-commit hooks
pip install pre-commit
pre-commit install

# 7. Pull required Ollama models
ollama pull nomic-embed-text
ollama pull deepseek-r1:latest  # Or your preferred model
```

### Development Dependencies

Create `requirements-dev.txt` if it doesn't exist:

```txt
pytest>=7.0.0
pytest-asyncio>=0.21.0
pytest-cov>=4.0.0
black>=23.0.0
isort>=5.12.0
flake8>=6.0.0
mypy>=1.0.0
httpx>=0.24.0
```

---

## Making Changes

### Branch Naming Convention

Use descriptive branch names:

```
feature/add-pdf-support
fix/chat-streaming-error
docs/update-api-reference
refactor/optimize-embedding-cache
test/add-rag-service-tests
```

### Commit Messages

Follow [Conventional Commits](https://www.conventionalcommits.org/):

```
<type>(<scope>): <description>

[optional body]

[optional footer]
```

**Types:**
| Type | Description |
|------|-------------|
| `feat` | New feature |
| `fix` | Bug fix |
| `docs` | Documentation only |
| `style` | Formatting, no code change |
| `refactor` | Code refactoring |
| `test` | Adding or updating tests |
| `chore` | Maintenance tasks |
| `perf` | Performance improvements |

**Examples:**
```bash
feat(rag): add support for DOCX file parsing
fix(chat): resolve streaming timeout on slow connections
docs(api): update endpoint documentation for v2
refactor(services): extract embedding logic to separate module
test(vector-store): add integration tests for ChromaDB
```

### Making Atomic Commits

Keep commits focused and atomic:

```bash
# Good - separate concerns
git commit -m "feat(rag): add PDF text extraction"
git commit -m "test(rag): add tests for PDF extraction"
git commit -m "docs(rag): document PDF support"

# Bad - mixed concerns
git commit -m "add PDF support, tests, and docs"
```

---

## Pull Request Process

### Before Submitting

1. **Sync with upstream:**
   ```bash
   git fetch upstream
   git rebase upstream/main
   ```

2. **Run all tests:**
   ```bash
   # Backend
   cd allma-backend
   pytest --cov=orchestration

   # Frontend
   cd allma-frontend
   npm test
   ```

3. **Run linters:**
   ```bash
   # Backend
   black .
   isort .
   flake8 .
   mypy .

   # Frontend
   npm run lint
   ```

4. **Update documentation** if needed

### PR Template

When creating a PR, include:

```markdown
## Description
Brief description of changes.

## Type of Change
- [ ] Bug fix (non-breaking change fixing an issue)
- [ ] New feature (non-breaking change adding functionality)
- [ ] Breaking change (fix or feature causing existing functionality to change)
- [ ] Documentation update

## Related Issues
Fixes #123
Relates to #456

## Changes Made
- Added X
- Modified Y
- Removed Z

## Testing
- [ ] Unit tests added/updated
- [ ] Integration tests added/updated
- [ ] Manual testing completed

## Screenshots (if applicable)

## Checklist
- [ ] Code follows project style guidelines
- [ ] Self-review completed
- [ ] Comments added for complex code
- [ ] Documentation updated
- [ ] No new warnings generated
- [ ] Tests pass locally
```

### Review Process

1. **Automated Checks** - CI must pass
2. **Code Review** - At least one maintainer approval
3. **Testing** - Manual verification if needed
4. **Merge** - Squash and merge preferred

---

## Coding Standards

### Python (Backend)

**Style Guide:** PEP 8 with Black formatting

```python
# Good
from typing import List, Optional

from fastapi import APIRouter, Depends

from orchestration.models import ChatRequest, ChatResponse
from orchestration.services import RAGService


class ChatHandler:
    """Handles chat message processing."""

    def __init__(self, rag_service: RAGService) -> None:
        self.rag_service = rag_service

    async def process_message(
        self,
        message: str,
        use_rag: bool = False,
        conversation_id: Optional[str] = None,
    ) -> ChatResponse:
        """
        Process a chat message and return response.

        Args:
            message: User's input message
            use_rag: Whether to use RAG retrieval
            conversation_id: Optional conversation identifier

        Returns:
            ChatResponse with AI-generated content
        """
        if use_rag:
            context = await self.rag_service.retrieve(message)
            return await self._generate_with_context(message, context)
        return await self._generate(message)
```

**Key Rules:**
- Use type hints everywhere
- Write docstrings for public methods
- Keep functions focused and small
- Use async/await for I/O operations
- Prefer composition over inheritance

### JavaScript/React (Frontend)

**Style Guide:** ESLint + Prettier

```javascript
// Good
import { useState, useCallback } from 'react';
import PropTypes from 'prop-types';

/**
 * ChatInput component for user message input.
 * @param {Object} props - Component props
 * @param {Function} props.onSend - Callback when message is sent
 * @param {boolean} props.disabled - Whether input is disabled
 */
export function ChatInput({ onSend, disabled = false }) {
  const [message, setMessage] = useState('');

  const handleSubmit = useCallback(
    (e) => {
      e.preventDefault();
      if (message.trim() && !disabled) {
        onSend(message);
        setMessage('');
      }
    },
    [message, disabled, onSend]
  );

  return (
    <form onSubmit={handleSubmit} className="flex gap-2">
      <input
        type="text"
        value={message}
        onChange={(e) => setMessage(e.target.value)}
        disabled={disabled}
        placeholder="Type your message..."
        className="flex-1 px-4 py-2 rounded-lg border"
      />
      <button
        type="submit"
        disabled={disabled || !message.trim()}
        className="px-6 py-2 bg-blue-500 text-white rounded-lg"
      >
        Send
      </button>
    </form>
  );
}

ChatInput.propTypes = {
  onSend: PropTypes.func.isRequired,
  disabled: PropTypes.bool,
};
```

**Key Rules:**
- Use functional components with hooks
- Prefer named exports
- Use PropTypes or TypeScript
- Keep components focused
- Use descriptive variable names

---

## Testing

### Backend Testing

```python
# tests/test_rag_service.py
import pytest
from unittest.mock import AsyncMock, MagicMock

from orchestration.services import RAGService


@pytest.fixture
def mock_ollama_client():
    client = AsyncMock()
    client.post.return_value = {"embedding": [0.1] * 768}
    return client


@pytest.fixture
def rag_service(mock_ollama_client):
    service = RAGService()
    service.ollama_client = mock_ollama_client
    return service


@pytest.mark.asyncio
async def test_embed_text_returns_vector(rag_service):
    """Test that embed_text returns a valid embedding vector."""
    embedding = await rag_service.embed_text("Hello, world!")
    
    assert isinstance(embedding, list)
    assert len(embedding) == 768
    assert all(isinstance(x, float) for x in embedding)


@pytest.mark.asyncio
async def test_retrieve_returns_documents(rag_service):
    """Test that retrieve returns relevant documents."""
    # Arrange
    rag_service.vector_store.search = AsyncMock(return_value=[
        {"content": "Test document", "score": 0.9}
    ])
    
    # Act
    results = await rag_service.retrieve("test query", k=5)
    
    # Assert
    assert len(results) == 1
    assert results[0]["content"] == "Test document"
```

**Running Tests:**
```bash
cd allma-backend

# Run all tests
pytest

# Run with coverage
pytest --cov=orchestration --cov-report=html

# Run specific test file
pytest tests/test_rag_service.py

# Run tests matching pattern
pytest -k "test_embed"
```

### Frontend Testing

```javascript
// src/components/__tests__/ChatInput.test.jsx
import { render, screen, fireEvent } from '@testing-library/react';
import { ChatInput } from '../ChatInput';

describe('ChatInput', () => {
  it('renders input and button', () => {
    render(<ChatInput onSend={() => {}} />);
    
    expect(screen.getByPlaceholderText(/type your message/i)).toBeInTheDocument();
    expect(screen.getByRole('button', { name: /send/i })).toBeInTheDocument();
  });

  it('calls onSend with message when form is submitted', () => {
    const onSend = jest.fn();
    render(<ChatInput onSend={onSend} />);
    
    const input = screen.getByPlaceholderText(/type your message/i);
    fireEvent.change(input, { target: { value: 'Hello!' } });
    fireEvent.submit(input);
    
    expect(onSend).toHaveBeenCalledWith('Hello!');
  });

  it('disables button when disabled prop is true', () => {
    render(<ChatInput onSend={() => {}} disabled />);
    
    expect(screen.getByRole('button')).toBeDisabled();
  });
});
```

**Running Tests:**
```bash
cd allma-frontend

# Run all tests
npm test

# Run with coverage
npm test -- --coverage

# Run in watch mode
npm test -- --watch
```

---

## Documentation

### Code Documentation

**Python:**
```python
def chunk_text(
    text: str,
    chunk_size: int = 500,
    overlap: int = 50,
) -> List[Chunk]:
    """
    Split text into overlapping chunks for embedding.

    This function divides input text into smaller chunks suitable for
    embedding generation. Chunks overlap to maintain context across
    chunk boundaries.

    Args:
        text: The input text to chunk.
        chunk_size: Maximum characters per chunk. Defaults to 500.
        overlap: Number of overlapping characters between chunks.
            Defaults to 50.

    Returns:
        List of Chunk objects containing the text and metadata.

    Raises:
        ValueError: If chunk_size is less than overlap.

    Example:
        >>> chunks = chunk_text("Long document text...", chunk_size=100)
        >>> print(len(chunks))
        5
    """
```

**JavaScript:**
```javascript
/**
 * Send a chat message and receive streaming response.
 *
 * @param {string} message - The user's message to send
 * @param {Object} options - Additional options
 * @param {boolean} options.useRag - Enable RAG retrieval
 * @param {string} options.conversationId - Conversation identifier
 * @param {Function} options.onToken - Callback for each token
 * @returns {Promise<ChatResponse>} The complete response
 *
 * @example
 * const response = await sendMessage("Hello!", {
 *   useRag: true,
 *   onToken: (token) => console.log(token)
 * });
 */
export async function sendMessage(message, options = {}) {
  // Implementation
}
```

### README Updates

When adding features, update:

1. **Features section** in README.md
2. **API documentation** in docs/API.md
3. **Configuration** if new env vars added
4. **Installation** if new dependencies added

---

## Questions?

- **Discord:** [Join our community](#)
- **GitHub Issues:** Open an issue for bugs or features
- **Email:** maintainers@example.com

Thank you for contributing to Allma Studio!
