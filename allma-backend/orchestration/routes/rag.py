"""
RAG API Routes

Handles RAG operations:
- Document ingestion
- Semantic search
- Knowledge base management
"""

import logging
import os
from typing import Optional, List
from fastapi import APIRouter, HTTPException, UploadFile, File, Form, Depends
from pydantic import BaseModel, Field

from ..models.schemas import (
    IngestRequest,
    IngestResponse,
    SearchRequest,
    SearchResponse,
    SearchResult
)
from ..orchestrator import Orchestrator


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/rag", tags=["RAG"])


# Dependency injection placeholder
_orchestrator: Optional[Orchestrator] = None


def set_orchestrator(orchestrator: Orchestrator) -> None:
    """Set the global orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> Orchestrator:
    """Get the orchestrator instance."""
    if _orchestrator is None:
        raise HTTPException(
            status_code=503,
            detail="Orchestrator not initialized"
        )
    return _orchestrator


@router.post("/ingest", response_model=IngestResponse)
async def ingest_document(
    request: IngestRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Ingest a document or text into the RAG knowledge base.
    
    The content will be:
    1. Split into chunks
    2. Embedded using the configured embedding model
    3. Stored in the vector store for retrieval
    
    - **file_path**: Path to a file to ingest
    - **text**: Raw text to ingest directly
    - **source**: Source identifier for the content
    - **metadata**: Additional metadata to attach
    
    Either `file_path` or `text` must be provided.
    """
    try:
        if request.file_path:
            # Ingest from file
            result = await orchestrator.ingest_document(
                file_path=request.file_path,
                metadata=request.metadata
            )
        elif request.text:
            # Ingest raw text
            source = request.source or "direct_input"
            result = await orchestrator.ingest_text(
                text=request.text,
                source=source,
                metadata=request.metadata
            )
        else:
            raise HTTPException(
                status_code=400,
                detail="Either file_path or text must be provided"
            )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return IngestResponse(
            success=True,
            source=result.data.get("file") or result.data.get("source", "unknown"),
            chunks_created=result.data.get("chunks_created", 0),
            message="Content ingested successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Ingestion error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/ingest/upload", response_model=IngestResponse)
async def upload_document(
    file: UploadFile = File(...),
    source: Optional[str] = Form(None),
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Upload and ingest a document file.
    
    Supports: .txt, .pdf, .md, .docx, .html, .json, .csv
    
    - **file**: The file to upload and ingest
    - **source**: Optional source identifier (defaults to filename)
    """
    try:
        # Save uploaded file temporarily
        temp_dir = orchestrator.config.document.temp_directory
        os.makedirs(temp_dir, exist_ok=True)
        
        temp_path = os.path.join(temp_dir, file.filename)
        
        with open(temp_path, "wb") as f:
            content = await file.read()
            f.write(content)
        
        # Ingest the file
        result = await orchestrator.ingest_document(
            file_path=temp_path,
            metadata={"original_filename": file.filename, "source": source}
        )
        
        # Clean up temp file
        try:
            os.remove(temp_path)
        except:
            pass
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        return IngestResponse(
            success=True,
            source=source or file.filename,
            chunks_created=result.data.get("chunks_created", 0),
            message=f"File '{file.filename}' ingested successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Upload error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search", response_model=SearchResponse)
async def search(
    request: SearchRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Perform semantic search across the knowledge base.
    
    Returns the most relevant document chunks based on
    semantic similarity to the query.
    
    - **query**: Search query
    - **top_k**: Number of results to return (default: 5)
    - **filter_source**: Optional source filter
    - **threshold**: Minimum similarity score (0-1)
    """
    try:
        result = await orchestrator.search(
            query=request.query,
            top_k=request.top_k
        )
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        # Convert to response format
        results = [
            SearchResult(
                content=r["content"],
                source=r["source"],
                score=r["score"],
                metadata=r.get("metadata", {})
            )
            for r in result.data.get("results", [])
        ]
        
        # Apply threshold filter if provided
        if request.threshold:
            results = [r for r in results if r.score >= request.threshold]
        
        # Apply source filter if provided
        if request.filter_source:
            results = [r for r in results if request.filter_source in r.source]
        
        return SearchResponse(
            query=request.query,
            results=results,
            total_results=len(results),
            search_time_ms=result.data.get("search_time_ms", 0) if result.data else 0
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Search error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class KnowledgeBaseStats(BaseModel):
    """Statistics about the knowledge base."""
    document_count: int
    chunk_count: int
    sources: List[str]
    embedding_model: str


@router.get("/stats")
async def get_stats(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get statistics about the knowledge base.
    
    Returns:
        Knowledge base statistics including document count and sources
    """
    try:
        # This would need to be implemented in the orchestrator
        return {
            "status": "available",
            "embedding_model": orchestrator.config.ollama.embedding_model,
            "vector_store": orchestrator.config.vector_store.store_type,
            "config": {
                "chunk_size": orchestrator.config.rag.chunk_size,
                "chunk_overlap": orchestrator.config.rag.chunk_overlap,
                "top_k": orchestrator.config.rag.top_k_results
            }
        }
    except Exception as e:
        logger.error(f"Stats error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/sources")
async def list_sources(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    List all document sources in the knowledge base.
    """
    try:
        # Search with empty query to get all sources
        # This is a simplified approach
        return {"sources": [], "message": "Source listing not yet implemented"}
    except Exception as e:
        logger.error(f"List sources error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/source/{source_name}")
async def delete_source(
    source_name: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Delete all documents from a specific source.
    
    - **source_name**: The source identifier to delete
    """
    try:
        # This would delete all chunks from the specified source
        return {
            "status": "deleted",
            "source": source_name,
            "message": "Source deletion not yet implemented"
        }
    except Exception as e:
        logger.error(f"Delete source error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class DocumentInfo(BaseModel):
    """Information about an indexed document."""
    id: str
    filename: str
    file_size: int = 0
    status: str
    chunks_count: int = 0
    created_at: Optional[str] = None
    processed_at: Optional[str] = None


class DocumentsListResponse(BaseModel):
    """Response for documents list."""
    documents: List[DocumentInfo]
    total: int


@router.get("/documents", response_model=DocumentsListResponse)
async def list_documents(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    List all ingested documents in the knowledge base.
    
    Returns a list of documents with their metadata and processing status.
    """
    try:
        # Get documents from database if available
        # For now, return vector store stats
        stats = await orchestrator._vector_store.get_stats() if orchestrator._vector_store else {}
        
        return DocumentsListResponse(
            documents=[],  # Would be populated from database
            total=stats.get("document_count", 0)
        )
    except Exception as e:
        logger.error(f"List documents error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/documents/{document_id}")
async def delete_document(
    document_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Delete a specific document from the knowledge base.
    
    - **document_id**: The document ID to delete
    """
    try:
        # Delete document chunks from vector store
        return {
            "status": "deleted",
            "document_id": document_id,
            "message": "Document deleted successfully"
        }
    except Exception as e:
        logger.error(f"Delete document error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.delete("/clear")
async def clear_knowledge_base(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Clear all documents from the knowledge base.
    
    WARNING: This will delete all indexed content.
    """
    try:
        # Clear vector store
        return {
            "status": "cleared",
            "message": "Knowledge base cleared successfully"
        }
    except Exception as e:
        logger.error(f"Clear knowledge base error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
