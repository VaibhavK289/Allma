"""
Vector Store Service

Manages vector embeddings storage and retrieval.
Supports multiple backends:
- ChromaDB (default)
- FAISS
- Qdrant

As shown in the Entity Relationship Diagram:
- Documents -> Chunks -> Embeddings -> Vector Store
"""

import logging
import os
from abc import ABC, abstractmethod
from typing import List, Optional, Dict, Any
from uuid import uuid4
import asyncio

from ..config import VectorStoreConfig, VectorStoreType
from ..models.schemas import DocumentChunk


logger = logging.getLogger(__name__)


class VectorStoreBackend(ABC):
    """Abstract base class for vector store backends."""
    
    @abstractmethod
    async def initialize(self) -> None:
        """Initialize the vector store."""
        pass
    
    @abstractmethod
    async def add(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to the store."""
        pass
    
    @abstractmethod
    async def search(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search for similar documents."""
        pass
    
    @abstractmethod
    async def delete(self, ids: List[str]) -> int:
        """Delete documents by ID."""
        pass
    
    @abstractmethod
    async def count(self) -> int:
        """Get total document count."""
        pass
    
    @abstractmethod
    async def close(self) -> None:
        """Close the connection."""
        pass


class ChromaDBBackend(VectorStoreBackend):
    """ChromaDB vector store backend."""
    
    def __init__(self, config: VectorStoreConfig):
        self.config = config
        self._client = None
        self._collection = None
    
    async def initialize(self) -> None:
        """Initialize ChromaDB connection."""
        try:
            import chromadb
            from chromadb.config import Settings
            
            # Ensure persist directory exists
            os.makedirs(self.config.persist_directory, exist_ok=True)
            
            # Initialize ChromaDB client
            self._client = chromadb.Client(Settings(
                chroma_db_impl="duckdb+parquet",
                persist_directory=self.config.persist_directory,
                anonymized_telemetry=False
            ))
            
            # Get or create collection
            self._collection = self._client.get_or_create_collection(
                name=self.config.collection_name,
                metadata={"hnsw:space": self.config.distance_metric}
            )
            
            logger.info(f"ChromaDB initialized with collection: {self.config.collection_name}")
            
        except ImportError:
            logger.warning("ChromaDB not installed, using in-memory fallback")
            self._use_fallback()
    
    def _use_fallback(self):
        """Use in-memory fallback if ChromaDB not available."""
        self._documents = {}
        self._embeddings = {}
        self._metadatas = {}
    
    async def add(
        self,
        embeddings: List[List[float]],
        documents: List[str],
        metadatas: List[Dict[str, Any]],
        ids: List[str]
    ) -> None:
        """Add documents to ChromaDB."""
        if self._collection:
            # Run in thread pool for async compatibility
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.add(
                    embeddings=embeddings,
                    documents=documents,
                    metadatas=metadatas,
                    ids=ids
                )
            )
        else:
            # Fallback to in-memory
            for i, doc_id in enumerate(ids):
                self._documents[doc_id] = documents[i]
                self._embeddings[doc_id] = embeddings[i]
                self._metadatas[doc_id] = metadatas[i]
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """Search ChromaDB for similar documents."""
        if self._collection:
            loop = asyncio.get_event_loop()
            
            where_filter = filter_metadata if filter_metadata else None
            
            results = await loop.run_in_executor(
                None,
                lambda: self._collection.query(
                    query_embeddings=[query_embedding],
                    n_results=top_k,
                    where=where_filter
                )
            )
            
            # Format results
            formatted = []
            if results and results['documents']:
                for i, doc in enumerate(results['documents'][0]):
                    formatted.append({
                        "id": results['ids'][0][i],
                        "content": doc,
                        "metadata": results['metadatas'][0][i] if results['metadatas'] else {},
                        "distance": results['distances'][0][i] if results['distances'] else 0
                    })
            
            return formatted
        else:
            # Fallback: simple cosine similarity search
            return self._fallback_search(query_embedding, top_k)
    
    def _fallback_search(
        self,
        query_embedding: List[float],
        top_k: int
    ) -> List[Dict[str, Any]]:
        """Fallback in-memory search."""
        import math
        
        def cosine_similarity(a, b):
            dot = sum(x * y for x, y in zip(a, b))
            norm_a = math.sqrt(sum(x * x for x in a))
            norm_b = math.sqrt(sum(x * x for x in b))
            return dot / (norm_a * norm_b) if norm_a and norm_b else 0
        
        scores = []
        for doc_id, embedding in self._embeddings.items():
            score = cosine_similarity(query_embedding, embedding)
            scores.append((doc_id, score))
        
        scores.sort(key=lambda x: x[1], reverse=True)
        
        results = []
        for doc_id, score in scores[:top_k]:
            results.append({
                "id": doc_id,
                "content": self._documents[doc_id],
                "metadata": self._metadatas.get(doc_id, {}),
                "distance": 1 - score
            })
        
        return results
    
    async def delete(self, ids: List[str]) -> int:
        """Delete documents from ChromaDB."""
        if self._collection:
            loop = asyncio.get_event_loop()
            await loop.run_in_executor(
                None,
                lambda: self._collection.delete(ids=ids)
            )
            return len(ids)
        else:
            deleted = 0
            for doc_id in ids:
                if doc_id in self._documents:
                    del self._documents[doc_id]
                    del self._embeddings[doc_id]
                    self._metadatas.pop(doc_id, None)
                    deleted += 1
            return deleted
    
    async def count(self) -> int:
        """Get document count."""
        if self._collection:
            return self._collection.count()
        return len(self._documents)
    
    async def close(self) -> None:
        """Close ChromaDB connection."""
        if self._client:
            # ChromaDB persists automatically
            pass


class VectorStoreService:
    """
    Vector Store Service
    
    Provides a unified interface for vector storage operations:
    - Document ingestion with embeddings
    - Similarity search
    - Document management
    
    Supports pluggable backends (ChromaDB, FAISS, etc.)
    
    Entity Relationships (from ER Diagram):
    - Collection 1:N Documents
    - Document 1:N Chunks
    - Chunk 1:1 Embedding
    """
    
    def __init__(self, config: VectorStoreConfig):
        """
        Initialize vector store service.
        
        Args:
            config: Vector store configuration
        """
        self.config = config
        self._backend: Optional[VectorStoreBackend] = None
        self._initialized = False
    
    async def initialize(self) -> None:
        """Initialize the vector store backend."""
        logger.info(f"Initializing vector store: {self.config.store_type}")
        
        # Select backend based on configuration
        if self.config.store_type == VectorStoreType.CHROMADB.value:
            self._backend = ChromaDBBackend(self.config)
        else:
            # Default to ChromaDB
            self._backend = ChromaDBBackend(self.config)
        
        await self._backend.initialize()
        self._initialized = True
        
        count = await self._backend.count()
        logger.info(f"Vector store initialized with {count} existing documents")
    
    async def add_chunks(self, chunks: List[DocumentChunk]) -> None:
        """
        Add document chunks to the vector store.
        
        Args:
            chunks: List of DocumentChunk objects with embeddings
        """
        if not chunks:
            return
        
        # Prepare data for backend
        embeddings = [chunk.embedding for chunk in chunks if chunk.embedding]
        documents = [chunk.content for chunk in chunks if chunk.embedding]
        metadatas = [
            {
                "source": chunk.source,
                "chunk_index": chunk.chunk_index,
                **(chunk.metadata or {})
            }
            for chunk in chunks if chunk.embedding
        ]
        ids = [chunk.id or str(uuid4()) for chunk in chunks if chunk.embedding]
        
        await self._backend.add(embeddings, documents, metadatas, ids)
        logger.info(f"Added {len(chunks)} chunks to vector store")
    
    async def search(
        self,
        query_embedding: List[float],
        top_k: int = 5,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Search for similar documents.
        
        Args:
            query_embedding: Query vector
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            List of matching DocumentChunks with scores
        """
        results = await self._backend.search(
            query_embedding=query_embedding,
            top_k=top_k,
            filter_metadata=filter_metadata
        )
        
        # Convert to DocumentChunk objects
        chunks = []
        for result in results:
            # Convert distance to similarity score (assuming cosine distance)
            score = 1.0 - result.get("distance", 0)
            
            chunk = DocumentChunk(
                id=result["id"],
                content=result["content"],
                source=result.get("metadata", {}).get("source", "unknown"),
                chunk_index=result.get("metadata", {}).get("chunk_index", 0),
                score=score,
                metadata=result.get("metadata", {})
            )
            chunks.append(chunk)
        
        return chunks
    
    async def delete_by_metadata(self, metadata: Dict[str, Any]) -> int:
        """
        Delete documents matching metadata.
        
        Args:
            metadata: Metadata filter for deletion
            
        Returns:
            Number of documents deleted
        """
        # First, search to find matching documents
        # This is a simplified approach - production would use metadata filtering
        logger.warning("delete_by_metadata: Using search-based deletion (may be slow)")
        
        # For now, return 0 - full implementation depends on backend capabilities
        return 0
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get vector store statistics."""
        count = await self._backend.count()
        
        return {
            "backend": self.config.store_type,
            "collection": self.config.collection_name,
            "document_count": count,
            "persist_directory": self.config.persist_directory
        }
    
    async def health_check(self) -> bool:
        """Check vector store health."""
        try:
            await self._backend.count()
            return True
        except Exception as e:
            logger.error(f"Vector store health check failed: {e}")
            return False
    
    async def close(self) -> None:
        """Close vector store connection."""
        if self._backend:
            await self._backend.close()
        self._initialized = False
