"""
Document Service

Handles document processing and ingestion as shown in the RAG Ingestion Pipeline:
1. Document Loading (various formats)
2. Text Extraction
3. Chunking/Splitting
4. Metadata Extraction

Supports formats:
- Text (.txt)
- Markdown (.md)
- PDF (.pdf)
- Word Documents (.docx)
- HTML (.html)
- JSON (.json)
- CSV (.csv)
"""

import logging
import os
from typing import List, Optional, Dict, Any
from pathlib import Path
from dataclasses import dataclass
import hashlib
import re
from datetime import datetime

from ..config import DocumentConfig, RAGConfig
from ..models.schemas import DocumentChunk, DocumentMetadata


logger = logging.getLogger(__name__)


@dataclass
class ProcessingResult:
    """Result of document processing."""
    success: bool
    chunks: List[DocumentChunk]
    metadata: DocumentMetadata
    error: Optional[str] = None


class TextSplitter:
    """
    Intelligent text splitting for RAG optimization.
    
    Strategies:
    - Recursive character splitting
    - Sentence-aware splitting
    - Paragraph-aware splitting
    - Token-based splitting
    """
    
    def __init__(
        self,
        chunk_size: int = 1000,
        chunk_overlap: int = 200,
        separators: Optional[List[str]] = None
    ):
        """
        Initialize text splitter.
        
        Args:
            chunk_size: Target chunk size in characters
            chunk_overlap: Overlap between chunks
            separators: List of separators in order of preference
        """
        self.chunk_size = chunk_size
        self.chunk_overlap = chunk_overlap
        self.separators = separators or [
            "\n\n",   # Paragraphs
            "\n",     # Lines
            ". ",     # Sentences
            "! ",     # Exclamations
            "? ",     # Questions
            "; ",     # Semicolons
            ", ",     # Commas
            " ",      # Words
            ""        # Characters
        ]
    
    def split_text(self, text: str) -> List[str]:
        """
        Split text into chunks with overlap.
        
        Args:
            text: Input text to split
            
        Returns:
            List of text chunks
        """
        return self._recursive_split(text, self.separators)
    
    def _recursive_split(
        self,
        text: str,
        separators: List[str]
    ) -> List[str]:
        """Recursively split text using separators."""
        if not text:
            return []
        
        if len(text) <= self.chunk_size:
            return [text.strip()] if text.strip() else []
        
        # Try each separator
        for sep in separators:
            if sep and sep in text:
                chunks = self._split_with_separator(text, sep, separators[1:])
                if chunks:
                    return chunks
        
        # Fallback: split by chunk_size
        return self._split_by_size(text)
    
    def _split_with_separator(
        self,
        text: str,
        separator: str,
        remaining_separators: List[str]
    ) -> List[str]:
        """Split text using a specific separator."""
        splits = text.split(separator)
        chunks = []
        current_chunk = ""
        
        for split in splits:
            if not split.strip():
                continue
            
            # Check if adding this split exceeds chunk size
            potential = current_chunk + separator + split if current_chunk else split
            
            if len(potential) <= self.chunk_size:
                current_chunk = potential
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(current_chunk.strip())
                
                # If split itself is too large, recursively split
                if len(split) > self.chunk_size:
                    sub_chunks = self._recursive_split(split, remaining_separators)
                    chunks.extend(sub_chunks)
                    current_chunk = ""
                else:
                    current_chunk = split
        
        # Don't forget the last chunk
        if current_chunk.strip():
            chunks.append(current_chunk.strip())
        
        # Apply overlap
        return self._apply_overlap(chunks)
    
    def _split_by_size(self, text: str) -> List[str]:
        """Split text by character size."""
        chunks = []
        start = 0
        
        while start < len(text):
            end = start + self.chunk_size
            chunk = text[start:end]
            
            # Try to end at word boundary
            if end < len(text):
                last_space = chunk.rfind(' ')
                if last_space > self.chunk_size // 2:
                    chunk = chunk[:last_space]
                    end = start + last_space
            
            chunks.append(chunk.strip())
            start = end - self.chunk_overlap
        
        return chunks
    
    def _apply_overlap(self, chunks: List[str]) -> List[str]:
        """Apply overlap between chunks."""
        if not chunks or self.chunk_overlap == 0:
            return chunks
        
        overlapped = [chunks[0]]
        
        for i in range(1, len(chunks)):
            prev_chunk = chunks[i - 1]
            curr_chunk = chunks[i]
            
            # Get overlap from previous chunk
            overlap_text = prev_chunk[-self.chunk_overlap:] if len(prev_chunk) > self.chunk_overlap else prev_chunk
            
            # Find a good starting point (word boundary)
            space_idx = overlap_text.find(' ')
            if space_idx > 0:
                overlap_text = overlap_text[space_idx + 1:]
            
            # Combine overlap with current chunk
            overlapped.append(overlap_text + " " + curr_chunk)
        
        return overlapped


class DocumentLoader:
    """
    Multi-format document loader.
    
    Supports loading and extracting text from various document formats.
    """
    
    @staticmethod
    async def load(file_path: str) -> str:
        """
        Load and extract text from a document.
        
        Args:
            file_path: Path to the document
            
        Returns:
            Extracted text content
        """
        path = Path(file_path)
        extension = path.suffix.lower()
        
        if extension == '.txt':
            return await DocumentLoader._load_text(file_path)
        elif extension == '.md':
            return await DocumentLoader._load_markdown(file_path)
        elif extension == '.pdf':
            return await DocumentLoader._load_pdf(file_path)
        elif extension == '.docx':
            return await DocumentLoader._load_docx(file_path)
        elif extension == '.html':
            return await DocumentLoader._load_html(file_path)
        elif extension == '.json':
            return await DocumentLoader._load_json(file_path)
        elif extension == '.csv':
            return await DocumentLoader._load_csv(file_path)
        else:
            # Try as plain text
            return await DocumentLoader._load_text(file_path)
    
    @staticmethod
    async def _load_text(file_path: str) -> str:
        """Load plain text file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            return f.read()
    
    @staticmethod
    async def _load_markdown(file_path: str) -> str:
        """Load and clean markdown file."""
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Basic markdown to text conversion
        # Remove code blocks but keep content
        content = re.sub(r'```[\s\S]*?```', '', content)
        # Remove inline code
        content = re.sub(r'`[^`]+`', '', content)
        # Remove images
        content = re.sub(r'!\[.*?\]\(.*?\)', '', content)
        # Convert links to text
        content = re.sub(r'\[([^\]]+)\]\([^\)]+\)', r'\1', content)
        # Remove headers markers
        content = re.sub(r'^#+\s*', '', content, flags=re.MULTILINE)
        # Remove emphasis markers
        content = re.sub(r'\*\*([^*]+)\*\*', r'\1', content)
        content = re.sub(r'\*([^*]+)\*', r'\1', content)
        
        return content
    
    @staticmethod
    async def _load_pdf(file_path: str) -> str:
        """Load PDF file using PyPDF2 or pdfplumber."""
        try:
            import pypdf
            
            text_content = []
            with open(file_path, 'rb') as f:
                reader = pypdf.PdfReader(f)
                for page in reader.pages:
                    text_content.append(page.extract_text() or "")
            
            return "\n\n".join(text_content)
            
        except ImportError:
            logger.warning("PyPDF not installed. Install with: pip install pypdf")
            raise ValueError("PDF support requires pypdf: pip install pypdf")
    
    @staticmethod
    async def _load_docx(file_path: str) -> str:
        """Load Word document."""
        try:
            from docx import Document
            
            doc = Document(file_path)
            paragraphs = [p.text for p in doc.paragraphs if p.text.strip()]
            
            return "\n\n".join(paragraphs)
            
        except ImportError:
            logger.warning("python-docx not installed. Install with: pip install python-docx")
            raise ValueError("DOCX support requires python-docx: pip install python-docx")
    
    @staticmethod
    async def _load_html(file_path: str) -> str:
        """Load and extract text from HTML."""
        try:
            from bs4 import BeautifulSoup
            
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                soup = BeautifulSoup(f.read(), 'html.parser')
            
            # Remove script and style elements
            for element in soup(['script', 'style', 'nav', 'footer', 'header']):
                element.decompose()
            
            return soup.get_text(separator='\n', strip=True)
            
        except ImportError:
            # Fallback: basic tag removal
            with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                content = f.read()
            return re.sub(r'<[^>]+>', '', content)
    
    @staticmethod
    async def _load_json(file_path: str) -> str:
        """Load JSON file and convert to text."""
        import json
        
        with open(file_path, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        def flatten_json(obj, prefix=""):
            """Flatten JSON to readable text."""
            lines = []
            if isinstance(obj, dict):
                for key, value in obj.items():
                    new_prefix = f"{prefix}.{key}" if prefix else key
                    lines.extend(flatten_json(value, new_prefix))
            elif isinstance(obj, list):
                for i, item in enumerate(obj):
                    lines.extend(flatten_json(item, f"{prefix}[{i}]"))
            else:
                lines.append(f"{prefix}: {obj}")
            return lines
        
        return "\n".join(flatten_json(data))
    
    @staticmethod
    async def _load_csv(file_path: str) -> str:
        """Load CSV file and convert to text."""
        import csv
        
        rows = []
        with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
            reader = csv.reader(f)
            headers = next(reader, [])
            
            for row in reader:
                row_text = ", ".join(
                    f"{h}: {v}" for h, v in zip(headers, row) if v.strip()
                )
                if row_text:
                    rows.append(row_text)
        
        return "\n".join(rows)


class DocumentService:
    """
    Document Processing Service
    
    Orchestrates the document ingestion pipeline:
    1. Load document from file
    2. Extract and clean text
    3. Generate metadata
    4. Split into chunks
    5. Prepare for embedding
    
    Implements the RAG Ingestion Diagram workflow.
    """
    
    def __init__(
        self,
        config: DocumentConfig,
        rag_config: RAGConfig
    ):
        """
        Initialize document service.
        
        Args:
            config: Document processing configuration
            rag_config: RAG pipeline configuration
        """
        self.config = config
        self.rag_config = rag_config
        
        # Initialize text splitter
        self.splitter = TextSplitter(
            chunk_size=rag_config.chunk_size,
            chunk_overlap=rag_config.chunk_overlap
        )
        
        # Ensure directories exist
        os.makedirs(config.temp_directory, exist_ok=True)
        os.makedirs(config.processed_directory, exist_ok=True)
    
    async def process_document(
        self,
        file_path: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Process a document through the ingestion pipeline.
        
        Args:
            file_path: Path to the document
            metadata: Additional metadata to attach
            
        Returns:
            List of document chunks ready for embedding
        """
        path = Path(file_path)
        
        # Validate file
        if not path.exists():
            raise FileNotFoundError(f"Document not found: {file_path}")
        
        if path.suffix.lower() not in self.config.supported_extensions:
            raise ValueError(f"Unsupported file type: {path.suffix}")
        
        file_size_mb = path.stat().st_size / (1024 * 1024)
        if file_size_mb > self.config.max_file_size_mb:
            raise ValueError(f"File too large: {file_size_mb:.2f}MB > {self.config.max_file_size_mb}MB")
        
        logger.info(f"Processing document: {path.name} ({file_size_mb:.2f}MB)")
        
        # Load document
        text = await DocumentLoader.load(file_path)
        
        if not text.strip():
            raise ValueError("Document is empty or could not be parsed")
        
        # Generate document metadata
        doc_metadata = self._generate_metadata(path, text, metadata)
        
        # Chunk the text
        chunks = await self.chunk_text(
            text=text,
            source=path.name,
            metadata={**doc_metadata.to_dict(), **(metadata or {})}
        )
        
        logger.info(f"Document processed: {len(chunks)} chunks created")
        
        return chunks
    
    async def chunk_text(
        self,
        text: str,
        source: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[DocumentChunk]:
        """
        Split text into chunks for embedding.
        
        Args:
            text: Raw text content
            source: Source identifier
            metadata: Optional metadata to attach
            
        Returns:
            List of DocumentChunk objects
        """
        # Clean the text
        cleaned_text = self._clean_text(text)
        
        # Split into chunks
        text_chunks = self.splitter.split_text(cleaned_text)
        
        # Create DocumentChunk objects
        chunks = []
        for i, chunk_text in enumerate(text_chunks):
            if not chunk_text.strip():
                continue
            
            chunk_id = self._generate_chunk_id(source, i, chunk_text)
            
            chunk = DocumentChunk(
                id=chunk_id,
                content=chunk_text,
                source=source,
                chunk_index=i,
                metadata={
                    "chunk_number": i + 1,
                    "total_chunks": len(text_chunks),
                    "char_count": len(chunk_text),
                    **(metadata or {})
                }
            )
            chunks.append(chunk)
        
        return chunks
    
    def _clean_text(self, text: str) -> str:
        """Clean and normalize text."""
        # Normalize whitespace
        text = re.sub(r'\s+', ' ', text)
        # Remove null bytes
        text = text.replace('\x00', '')
        # Normalize line breaks
        text = text.replace('\r\n', '\n').replace('\r', '\n')
        # Remove excessive newlines
        text = re.sub(r'\n{3,}', '\n\n', text)
        
        return text.strip()
    
    def _generate_metadata(
        self,
        path: Path,
        text: str,
        extra_metadata: Optional[Dict[str, Any]] = None
    ) -> DocumentMetadata:
        """Generate metadata for a document."""
        stats = path.stat()
        
        return DocumentMetadata(
            filename=path.name,
            file_path=str(path.absolute()),
            file_type=path.suffix.lower(),
            file_size=stats.st_size,
            created_at=datetime.fromtimestamp(stats.st_ctime),
            modified_at=datetime.fromtimestamp(stats.st_mtime),
            char_count=len(text),
            word_count=len(text.split()),
            checksum=hashlib.md5(text.encode()).hexdigest()
        )
    
    def _generate_chunk_id(
        self,
        source: str,
        index: int,
        content: str
    ) -> str:
        """Generate unique ID for a chunk."""
        content_hash = hashlib.sha256(content.encode()).hexdigest()[:8]
        return f"{source}_{index}_{content_hash}"
    
    async def process_batch(
        self,
        file_paths: List[str],
        metadata: Optional[Dict[str, Any]] = None
    ) -> List[ProcessingResult]:
        """
        Process multiple documents.
        
        Args:
            file_paths: List of document paths
            metadata: Shared metadata for all documents
            
        Returns:
            List of processing results
        """
        results = []
        
        for file_path in file_paths:
            try:
                chunks = await self.process_document(file_path, metadata)
                doc_metadata = self._generate_metadata(
                    Path(file_path),
                    "",  # We don't need text for metadata generation
                    metadata
                )
                results.append(ProcessingResult(
                    success=True,
                    chunks=chunks,
                    metadata=doc_metadata
                ))
            except Exception as e:
                logger.error(f"Failed to process {file_path}: {e}")
                results.append(ProcessingResult(
                    success=False,
                    chunks=[],
                    metadata=None,
                    error=str(e)
                ))
        
        return results
    
    def get_supported_extensions(self) -> List[str]:
        """Get list of supported file extensions."""
        return self.config.supported_extensions.copy()
