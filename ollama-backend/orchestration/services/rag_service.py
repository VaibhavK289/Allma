"""
RAG (Retrieval-Augmented Generation) Service

Implements the RAG pipeline as shown in the RAG_Implementation_Architecture_Diagram:
1. Query Processing
2. Embedding Generation
3. Vector Similarity Search
4. Context Ranking & Selection
5. Prompt Augmentation

This service coordinates between:
- Ollama for embeddings
- Vector Store for retrieval
- Reranking for relevance
"""

import logging
from typing import List, Optional, Dict, Any
from dataclasses import dataclass
import asyncio

from ollama import AsyncClient

from ..config import RAGConfig
from ..models.schemas import DocumentChunk, RAGContext
from .vector_store_service import VectorStoreService


logger = logging.getLogger(__name__)


@dataclass
class RetrievalMetrics:
    """Metrics for retrieval operations."""
    query_embedding_time_ms: float
    search_time_ms: float
    rerank_time_ms: float
    total_time_ms: float
    chunks_retrieved: int
    chunks_after_filter: int


class RAGService:
    """
    RAG Pipeline Service
    
    Handles the complete retrieval-augmented generation workflow:
    
    1. Embedding Generation: Convert queries to vectors using Ollama
    2. Similarity Search: Find relevant chunks in vector store
    3. Reranking: Score and filter results for relevance
    4. Context Assembly: Build context for LLM consumption
    
    Architecture follows the RAG Implementation Architecture Diagram:
    [Query] -> [Embedder] -> [Vector Search] -> [Reranker] -> [Context]
    """
    
    def __init__(
        self,
        config: RAGConfig,
        vector_store: VectorStoreService,
        ollama_client: AsyncClient,
        embedding_model: str
    ):
        """
        Initialize RAG service.
        
        Args:
            config: RAG configuration settings
            vector_store: Vector store service instance
            ollama_client: Ollama async client for embeddings
            embedding_model: Name of the embedding model
        """
        self.config = config
        self.vector_store = vector_store
        self.ollama_client = ollama_client
        self.embedding_model = embedding_model
        self._initialized = False
        
        # Cache for embeddings
        self._embedding_cache: Dict[str, List[float]] = {}
        self._cache_max_size = 1000
    
    async def initialize(self) -> None:
        """Initialize the RAG service."""
        logger.info(f"Initializing RAG service with model: {self.embedding_model}")
        
        # Verify embedding model is available
        try:
            # Generate a test embedding
            test_embedding = await self._generate_embedding("test")
            logger.info(f"Embedding dimension: {len(test_embedding)}")
            self._initialized = True
            
        except Exception as e:
            logger.error(f"Failed to initialize RAG service: {e}")
            raise
    
    async def _generate_embedding(self, text: str) -> List[float]:
        """
        Generate embedding vector for text using Ollama.
        
        Args:
            text: Input text to embed
            
        Returns:
            Embedding vector as list of floats
        """
        # Check cache first
        cache_key = hash(text)
        if cache_key in self._embedding_cache:
            return self._embedding_cache[cache_key]
        
        # Generate embedding via Ollama
        response = await self.ollama_client.embeddings(
            model=self.embedding_model,
            prompt=text
        )
        
        embedding = response['embedding']
        
        # Cache the result
        if len(self._embedding_cache) < self._cache_max_size:
            self._embedding_cache[cache_key] = embedding
        
        return embedding
    
    async def _generate_embeddings_batch(
        self,
        texts: List[str],
        batch_size: int = 10
    ) -> List[List[float]]:
        """
        Generate embeddings for multiple texts in batches.
        
        Args:
            texts: List of texts to embed
            batch_size: Number of concurrent embedding requests
            
        Returns:
            List of embedding vectors
        """
        embeddings = []
        
        for i in range(0, len(texts), batch_size):
            batch = texts[i:i + batch_size]
            batch_embeddings = await asyncio.gather(*[
                self._generate_embedding(text)
                for text in batch
            ])
            embeddings.extend(batch_embeddings)
            
            logger.debug(f"Generated embeddings for batch {i // batch_size + 1}")
        
        return embeddings
    
    async def retrieve_context(
        self,
        query: str,
        top_k: Optional[int] = None,
        filter_metadata: Optional[Dict[str, Any]] = None
    ) -> RAGContext:
        """
        Retrieve relevant context for a query.
        
        This implements the core RAG retrieval pipeline:
        1. Generate query embedding
        2. Perform similarity search
        3. Apply reranking if enabled
        4. Filter by similarity threshold
        5. Return assembled context
        
        Args:
            query: The search query
            top_k: Number of results to return
            filter_metadata: Optional metadata filters
            
        Returns:
            RAGContext containing relevant chunks and sources
        """
        import time
        start_time = time.time()
        
        k = top_k or self.config.top_k_results
        
        # Step 1: Generate query embedding
        embed_start = time.time()
        query_embedding = await self._generate_embedding(query)
        embed_time = (time.time() - embed_start) * 1000
        
        # Step 2: Similarity search in vector store
        search_start = time.time()
        results = await self.vector_store.search(
            query_embedding=query_embedding,
            top_k=k * 2,  # Retrieve more for reranking
            filter_metadata=filter_metadata
        )
        search_time = (time.time() - search_start) * 1000
        
        # Step 3: Reranking (if enabled)
        rerank_start = time.time()
        if self.config.rerank_enabled and results:
            results = await self._rerank_results(query, results)
        rerank_time = (time.time() - rerank_start) * 1000
        
        # Step 4: Filter by similarity threshold
        filtered_results = [
            r for r in results
            if r.score >= self.config.similarity_threshold
        ][:k]
        
        # Step 5: Assemble context
        total_time = (time.time() - start_time) * 1000
        
        # Extract unique sources
        sources = list(set(chunk.source for chunk in filtered_results))
        
        logger.info(
            f"RAG retrieval: {len(filtered_results)} chunks in {total_time:.2f}ms "
            f"(embed: {embed_time:.2f}ms, search: {search_time:.2f}ms, rerank: {rerank_time:.2f}ms)"
        )
        
        return RAGContext(
            query=query,
            chunks=filtered_results,
            sources=sources,
            metrics={
                "embedding_time_ms": embed_time,
                "search_time_ms": search_time,
                "rerank_time_ms": rerank_time,
                "total_time_ms": total_time,
                "chunks_retrieved": len(results),
                "chunks_returned": len(filtered_results)
            }
        )
    
    async def _rerank_results(
        self,
        query: str,
        results: List[DocumentChunk]
    ) -> List[DocumentChunk]:
        """
        Rerank search results for better relevance.
        
        Uses a combination of:
        - Semantic similarity scores
        - Keyword matching
        - Position/recency weighting
        
        Args:
            query: Original query
            results: Initial search results
            
        Returns:
            Reranked list of chunks
        """
        query_terms = set(query.lower().split())
        
        for chunk in results:
            # Base score from vector similarity
            base_score = chunk.score
            
            # Keyword overlap bonus
            chunk_terms = set(chunk.content.lower().split())
            overlap = len(query_terms & chunk_terms)
            keyword_bonus = min(overlap * 0.05, 0.2)  # Max 0.2 bonus
            
            # Update score
            chunk.score = min(base_score + keyword_bonus, 1.0)
        
        # Sort by updated scores
        results.sort(key=lambda x: x.score, reverse=True)
        
        return results
    
    async def ingest_chunks(
        self,
        chunks: List[DocumentChunk]
    ) -> Dict[str, Any]:
        """
        Ingest document chunks into the RAG pipeline.
        
        Process:
        1. Generate embeddings for all chunks
        2. Store chunks with embeddings in vector store
        3. Return ingestion statistics
        
        Args:
            chunks: List of document chunks to ingest
            
        Returns:
            Ingestion statistics
        """
        if not chunks:
            return {"chunks_ingested": 0, "status": "empty"}
        
        logger.info(f"Ingesting {len(chunks)} chunks into RAG pipeline")
        
        # Generate embeddings for all chunks
        texts = [chunk.content for chunk in chunks]
        embeddings = await self._generate_embeddings_batch(texts)
        
        # Attach embeddings to chunks
        for chunk, embedding in zip(chunks, embeddings):
            chunk.embedding = embedding
        
        # Store in vector store
        await self.vector_store.add_chunks(chunks)
        
        return {
            "chunks_ingested": len(chunks),
            "embedding_dimension": len(embeddings[0]) if embeddings else 0,
            "status": "success"
        }
    
    async def delete_by_source(self, source: str) -> int:
        """
        Delete all chunks from a specific source.
        
        Args:
            source: Source identifier to delete
            
        Returns:
            Number of chunks deleted
        """
        return await self.vector_store.delete_by_metadata({"source": source})
    
    async def get_stats(self) -> Dict[str, Any]:
        """Get RAG service statistics."""
        vector_stats = await self.vector_store.get_stats()
        
        return {
            "embedding_model": self.embedding_model,
            "embedding_cache_size": len(self._embedding_cache),
            "config": {
                "chunk_size": self.config.chunk_size,
                "chunk_overlap": self.config.chunk_overlap,
                "top_k": self.config.top_k_results,
                "similarity_threshold": self.config.similarity_threshold,
                "rerank_enabled": self.config.rerank_enabled
            },
            "vector_store": vector_stats
        }
    
    def clear_cache(self) -> None:
        """Clear the embedding cache."""
        self._embedding_cache.clear()
        logger.info("Embedding cache cleared")
