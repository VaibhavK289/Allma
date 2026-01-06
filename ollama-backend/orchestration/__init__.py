"""
Orchestration Layer for Ollama RAG Application

This module provides the core orchestration capabilities for:
- LLM interactions via Ollama
- RAG (Retrieval-Augmented Generation) pipeline
- Document ingestion and processing
- Vector store management
- Conversation management

Architecture based on the diagrams:
- RAG Implementation Architecture
- Entity Relationship Diagram
- System Architecture Diagram
"""

from .orchestrator import Orchestrator
from .config import OrchestrationConfig

__version__ = "1.0.0"
__all__ = ["Orchestrator", "OrchestrationConfig"]
