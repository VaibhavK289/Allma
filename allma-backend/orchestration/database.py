"""
Database Models and Persistence Layer

SQLite-based persistence for:
- Conversations and messages
- Document metadata
- User settings
- Analytics and metrics

Uses SQLAlchemy for ORM with async support via aiosqlite.
"""

import os
import logging
from datetime import datetime
from typing import Optional, List, Dict, Any, AsyncGenerator
from contextlib import asynccontextmanager
import json

from sqlalchemy import (
    Column, String, Integer, Float, Text, DateTime, Boolean, 
    ForeignKey, Index, JSON, create_engine, event
)
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import relationship, sessionmaker
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy.pool import StaticPool


logger = logging.getLogger(__name__)

Base = declarative_base()


# ============================================================
# Database Models
# ============================================================

class Conversation(Base):
    """Conversation model for persisting chat history."""
    
    __tablename__ = "conversations"
    
    id = Column(String(64), primary_key=True)
    title = Column(String(255), nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    extra_data = Column(JSON, default=dict)  # renamed from 'metadata' (reserved in SQLAlchemy)
    is_active = Column(Boolean, default=True)
    
    # Relationships
    messages = relationship("Message", back_populates="conversation", cascade="all, delete-orphan", order_by="Message.created_at")
    
    # Indexes
    __table_args__ = (
        Index("idx_conversation_created", "created_at"),
        Index("idx_conversation_updated", "updated_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "title": self.title,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "updated_at": self.updated_at.isoformat() if self.updated_at else None,
            "message_count": len(self.messages) if self.messages else 0,
            "metadata": self.extra_data or {}
        }


class Message(Base):
    """Message model for individual chat messages."""
    
    __tablename__ = "messages"
    
    id = Column(String(64), primary_key=True)
    conversation_id = Column(String(64), ForeignKey("conversations.id", ondelete="CASCADE"), nullable=False)
    role = Column(String(16), nullable=False)  # user, assistant, system
    content = Column(Text, nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    tokens_used = Column(Integer, default=0)
    extra_data = Column(JSON, default=dict)  # renamed from 'metadata' (reserved in SQLAlchemy)
    
    # RAG context
    context_sources = Column(JSON, default=list)
    context_chunks = Column(Integer, default=0)
    
    # Relationships
    conversation = relationship("Conversation", back_populates="messages")
    
    # Indexes
    __table_args__ = (
        Index("idx_message_conversation", "conversation_id"),
        Index("idx_message_created", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "role": self.role,
            "content": self.content,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "tokens_used": self.tokens_used,
            "context_sources": self.context_sources or [],
            "metadata": self.extra_data or {}
        }


class Document(Base):
    """Document model for tracking ingested documents."""
    
    __tablename__ = "documents"
    
    id = Column(String(64), primary_key=True)
    filename = Column(String(255), nullable=False)
    file_path = Column(String(512), nullable=True)
    file_hash = Column(String(64), nullable=True)
    file_size = Column(Integer, default=0)
    mime_type = Column(String(128), nullable=True)
    
    # Processing info
    status = Column(String(32), default="pending")  # pending, processing, completed, failed
    chunks_count = Column(Integer, default=0)
    processed_at = Column(DateTime, nullable=True)
    error_message = Column(Text, nullable=True)
    
    # Timestamps
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Extra data
    extra_data = Column(JSON, default=dict)  # renamed from 'metadata' (reserved in SQLAlchemy)
    
    # Indexes
    __table_args__ = (
        Index("idx_document_hash", "file_hash"),
        Index("idx_document_status", "status"),
        Index("idx_document_created", "created_at"),
    )
    
    def to_dict(self) -> Dict[str, Any]:
        return {
            "id": self.id,
            "filename": self.filename,
            "file_size": self.file_size,
            "mime_type": self.mime_type,
            "status": self.status,
            "chunks_count": self.chunks_count,
            "created_at": self.created_at.isoformat() if self.created_at else None,
            "processed_at": self.processed_at.isoformat() if self.processed_at else None,
            "metadata": self.extra_data or {}
        }


class Setting(Base):
    """Application settings model."""
    
    __tablename__ = "settings"
    
    key = Column(String(128), primary_key=True)
    value = Column(Text, nullable=True)
    value_type = Column(String(32), default="string")  # string, int, float, bool, json
    description = Column(Text, nullable=True)
    updated_at = Column(DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def get_typed_value(self) -> Any:
        """Get value with correct type."""
        if self.value is None:
            return None
        
        if self.value_type == "int":
            return int(self.value)
        elif self.value_type == "float":
            return float(self.value)
        elif self.value_type == "bool":
            return self.value.lower() in ("true", "1", "yes")
        elif self.value_type == "json":
            return json.loads(self.value)
        else:
            return self.value


class Metrics(Base):
    """Metrics and analytics model."""
    
    __tablename__ = "metrics"
    
    id = Column(Integer, primary_key=True, autoincrement=True)
    metric_name = Column(String(128), nullable=False)
    metric_value = Column(Float, nullable=False)
    timestamp = Column(DateTime, default=datetime.utcnow, nullable=False)
    tags = Column(JSON, default=dict)
    
    # Indexes
    __table_args__ = (
        Index("idx_metrics_name", "metric_name"),
        Index("idx_metrics_timestamp", "timestamp"),
    )


# ============================================================
# Database Manager
# ============================================================

class DatabaseManager:
    """
    Manages database connections and sessions.
    
    Features:
    - Async SQLite support
    - Connection pooling
    - Automatic schema creation
    - Health checks
    """
    
    def __init__(self, database_url: Optional[str] = None):
        """
        Initialize database manager.
        
        Args:
            database_url: SQLAlchemy database URL. Defaults to SQLite.
        """
        self.database_url = database_url or self._get_default_url()
        self._engine = None
        self._session_factory = None
        self._initialized = False
    
    def _get_default_url(self) -> str:
        """Get default database URL."""
        data_dir = os.getenv("DATA_DIRECTORY", "./data")
        os.makedirs(data_dir, exist_ok=True)
        db_path = os.path.join(data_dir, "allma.db")
        return f"sqlite+aiosqlite:///{db_path}"
    
    async def initialize(self) -> None:
        """Initialize database connection and create tables."""
        if self._initialized:
            return
        
        logger.info(f"Initializing database: {self.database_url}")
        
        try:
            # Create async engine
            if "sqlite" in self.database_url:
                self._engine = create_async_engine(
                    self.database_url,
                    echo=False,
                    connect_args={"check_same_thread": False},
                    poolclass=StaticPool
                )
            else:
                self._engine = create_async_engine(
                    self.database_url,
                    echo=False,
                    pool_size=5,
                    max_overflow=10
                )
            
            # Create session factory
            self._session_factory = async_sessionmaker(
                bind=self._engine,
                class_=AsyncSession,
                expire_on_commit=False
            )
            
            # Create tables
            async with self._engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            
            self._initialized = True
            logger.info("Database initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize database: {e}")
            raise
    
    async def close(self) -> None:
        """Close database connections."""
        if self._engine:
            await self._engine.dispose()
            self._initialized = False
            logger.info("Database connections closed")
    
    @asynccontextmanager
    async def session(self) -> AsyncGenerator[AsyncSession, None]:
        """Get a database session."""
        if not self._initialized:
            await self.initialize()
        
        async with self._session_factory() as session:
            try:
                yield session
                await session.commit()
            except Exception:
                await session.rollback()
                raise
    
    async def health_check(self) -> bool:
        """Check database health."""
        try:
            async with self.session() as session:
                await session.execute("SELECT 1")
            return True
        except Exception as e:
            logger.error(f"Database health check failed: {e}")
            return False


# ============================================================
# Repository Pattern Implementations
# ============================================================

class ConversationRepository:
    """Repository for conversation operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Conversation:
        """Create a new conversation."""
        async with self.db.session() as session:
            conversation = Conversation(
                id=conversation_id,
                title=title or "New Conversation",
                metadata=metadata or {}
            )
            session.add(conversation)
            await session.flush()
            return conversation
    
    async def get(self, conversation_id: str) -> Optional[Conversation]:
        """Get conversation by ID."""
        async with self.db.session() as session:
            from sqlalchemy import select
            from sqlalchemy.orm import selectinload
            
            result = await session.execute(
                select(Conversation)
                .where(Conversation.id == conversation_id)
                .options(selectinload(Conversation.messages))
            )
            return result.scalar_one_or_none()
    
    async def list_all(
        self,
        limit: int = 50,
        offset: int = 0,
        active_only: bool = True
    ) -> List[Conversation]:
        """List all conversations."""
        async with self.db.session() as session:
            from sqlalchemy import select
            
            query = select(Conversation).order_by(Conversation.updated_at.desc())
            
            if active_only:
                query = query.where(Conversation.is_active == True)
            
            query = query.limit(limit).offset(offset)
            
            result = await session.execute(query)
            return list(result.scalars().all())
    
    async def update_title(self, conversation_id: str, title: str) -> bool:
        """Update conversation title."""
        async with self.db.session() as session:
            from sqlalchemy import update
            
            result = await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(title=title, updated_at=datetime.utcnow())
            )
            return result.rowcount > 0
    
    async def delete(self, conversation_id: str) -> bool:
        """Delete a conversation."""
        async with self.db.session() as session:
            from sqlalchemy import delete
            
            result = await session.execute(
                delete(Conversation).where(Conversation.id == conversation_id)
            )
            return result.rowcount > 0


class MessageRepository:
    """Repository for message operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create(
        self,
        message_id: str,
        conversation_id: str,
        role: str,
        content: str,
        tokens_used: int = 0,
        context_sources: Optional[List[str]] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Message:
        """Create a new message."""
        async with self.db.session() as session:
            message = Message(
                id=message_id,
                conversation_id=conversation_id,
                role=role,
                content=content,
                tokens_used=tokens_used,
                context_sources=context_sources or [],
                context_chunks=len(context_sources) if context_sources else 0,
                metadata=metadata or {}
            )
            session.add(message)
            await session.flush()
            
            # Update conversation timestamp
            from sqlalchemy import update
            await session.execute(
                update(Conversation)
                .where(Conversation.id == conversation_id)
                .values(updated_at=datetime.utcnow())
            )
            
            return message
    
    async def get_by_conversation(
        self,
        conversation_id: str,
        limit: int = 100
    ) -> List[Message]:
        """Get messages for a conversation."""
        async with self.db.session() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(Message)
                .where(Message.conversation_id == conversation_id)
                .order_by(Message.created_at.asc())
                .limit(limit)
            )
            return list(result.scalars().all())


class DocumentRepository:
    """Repository for document operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def create(
        self,
        document_id: str,
        filename: str,
        file_path: Optional[str] = None,
        file_hash: Optional[str] = None,
        file_size: int = 0,
        mime_type: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> Document:
        """Create a new document record."""
        async with self.db.session() as session:
            document = Document(
                id=document_id,
                filename=filename,
                file_path=file_path,
                file_hash=file_hash,
                file_size=file_size,
                mime_type=mime_type,
                status="pending",
                metadata=metadata or {}
            )
            session.add(document)
            await session.flush()
            return document
    
    async def update_status(
        self,
        document_id: str,
        status: str,
        chunks_count: int = 0,
        error_message: Optional[str] = None
    ) -> bool:
        """Update document processing status."""
        async with self.db.session() as session:
            from sqlalchemy import update
            
            values = {
                "status": status,
                "chunks_count": chunks_count,
                "updated_at": datetime.utcnow()
            }
            
            if status == "completed":
                values["processed_at"] = datetime.utcnow()
            
            if error_message:
                values["error_message"] = error_message
            
            result = await session.execute(
                update(Document)
                .where(Document.id == document_id)
                .values(**values)
            )
            return result.rowcount > 0
    
    async def get_by_hash(self, file_hash: str) -> Optional[Document]:
        """Get document by file hash (for deduplication)."""
        async with self.db.session() as session:
            from sqlalchemy import select
            
            result = await session.execute(
                select(Document).where(Document.file_hash == file_hash)
            )
            return result.scalar_one_or_none()
    
    async def list_all(
        self,
        status: Optional[str] = None,
        limit: int = 100
    ) -> List[Document]:
        """List all documents."""
        async with self.db.session() as session:
            from sqlalchemy import select
            
            query = select(Document).order_by(Document.created_at.desc())
            
            if status:
                query = query.where(Document.status == status)
            
            query = query.limit(limit)
            
            result = await session.execute(query)
            return list(result.scalars().all())


class MetricsRepository:
    """Repository for metrics operations."""
    
    def __init__(self, db: DatabaseManager):
        self.db = db
    
    async def record(
        self,
        metric_name: str,
        metric_value: float,
        tags: Optional[Dict[str, Any]] = None
    ) -> None:
        """Record a metric."""
        async with self.db.session() as session:
            metric = Metrics(
                metric_name=metric_name,
                metric_value=metric_value,
                tags=tags or {}
            )
            session.add(metric)
    
    async def get_stats(
        self,
        metric_name: str,
        hours: int = 24
    ) -> Dict[str, Any]:
        """Get metric statistics."""
        async with self.db.session() as session:
            from sqlalchemy import select, func
            from datetime import timedelta
            
            cutoff = datetime.utcnow() - timedelta(hours=hours)
            
            result = await session.execute(
                select(
                    func.count(Metrics.id).label("count"),
                    func.avg(Metrics.metric_value).label("avg"),
                    func.min(Metrics.metric_value).label("min"),
                    func.max(Metrics.metric_value).label("max")
                )
                .where(Metrics.metric_name == metric_name)
                .where(Metrics.timestamp >= cutoff)
            )
            
            row = result.one_or_none()
            if row:
                return {
                    "metric": metric_name,
                    "period_hours": hours,
                    "count": row.count or 0,
                    "avg": float(row.avg) if row.avg else 0.0,
                    "min": float(row.min) if row.min else 0.0,
                    "max": float(row.max) if row.max else 0.0
                }
            
            return {"metric": metric_name, "period_hours": hours, "count": 0}
