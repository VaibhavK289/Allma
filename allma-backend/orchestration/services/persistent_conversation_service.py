"""
Persistent Conversation Service

Extends the base ConversationService with database persistence.
Provides automatic saving and loading of conversations from SQLite.
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime
from uuid import uuid4

from ..models.schemas import ChatMessage, ConversationContext
from ..database import DatabaseManager, ConversationRepository, MessageRepository
from .conversation_service import ConversationService, ConversationStats


logger = logging.getLogger(__name__)


class PersistentConversationService(ConversationService):
    """
    Conversation service with database persistence.
    
    Extends the in-memory ConversationService with:
    - Automatic persistence to SQLite
    - Loading conversations from database on access
    - Background sync of message history
    """
    
    def __init__(
        self,
        db: DatabaseManager,
        max_conversations: int = 100,
        max_messages_per_conversation: int = 100,
        conversation_ttl_hours: int = 24,
        auto_persist: bool = True
    ):
        """
        Initialize persistent conversation service.
        
        Args:
            db: Database manager instance
            max_conversations: Max in-memory conversations
            max_messages_per_conversation: Max messages to retain
            conversation_ttl_hours: TTL for inactive conversations
            auto_persist: Whether to auto-save to database
        """
        super().__init__(
            max_conversations=max_conversations,
            max_messages_per_conversation=max_messages_per_conversation,
            conversation_ttl_hours=conversation_ttl_hours
        )
        
        self.db = db
        self.auto_persist = auto_persist
        self._conversation_repo: Optional[ConversationRepository] = None
        self._message_repo: Optional[MessageRepository] = None
        self._loaded_from_db: set = set()
    
    async def initialize(self) -> None:
        """Initialize repositories after database is ready."""
        self._conversation_repo = ConversationRepository(self.db)
        self._message_repo = MessageRepository(self.db)
        logger.info("Persistent conversation service initialized")
    
    async def create_conversation_async(
        self,
        conversation_id: str,
        title: Optional[str] = None,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        Create a new conversation with database persistence.
        
        Args:
            conversation_id: Unique identifier
            title: Optional conversation title
            metadata: Optional metadata
            
        Returns:
            New ConversationContext
        """
        # Create in-memory
        context = self.create_conversation(conversation_id, metadata)
        
        # Persist to database
        if self.auto_persist and self._conversation_repo:
            try:
                await self._conversation_repo.create(
                    conversation_id=conversation_id,
                    title=title or self._generate_title(context),
                    metadata=metadata
                )
            except Exception as e:
                logger.error(f"Failed to persist conversation: {e}")
        
        return context
    
    async def get_conversation_async(
        self,
        conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Get conversation, loading from database if not in memory.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            ConversationContext or None
        """
        # Check in-memory cache first
        context = self.get_conversation(conversation_id)
        if context:
            return context
        
        # Try to load from database
        if conversation_id not in self._loaded_from_db and self._conversation_repo:
            try:
                db_conv = await self._conversation_repo.get(conversation_id)
                if db_conv:
                    # Reconstruct in-memory
                    context = self.create_conversation(
                        conversation_id,
                        metadata=db_conv.extra_data or {}
                    )
                    
                    # Load messages
                    if self._message_repo:
                        db_messages = await self._message_repo.get_by_conversation(
                            conversation_id
                        )
                        for msg in db_messages:
                            chat_msg = ChatMessage(
                                role=msg.role,
                                content=msg.content,
                                timestamp=msg.created_at,
                                metadata=msg.extra_data or {}
                            )
                            self.add_message(conversation_id, chat_msg)
                    
                    self._loaded_from_db.add(conversation_id)
                    logger.debug(f"Loaded conversation from DB: {conversation_id}")
                    return context
                    
            except Exception as e:
                logger.error(f"Failed to load conversation from DB: {e}")
        
        return None
    
    async def add_message_async(
        self,
        conversation_id: str,
        message: ChatMessage,
        context_sources: Optional[List[str]] = None
    ) -> bool:
        """
        Add a message with database persistence.
        
        Args:
            conversation_id: Conversation identifier
            message: Message to add
            context_sources: RAG sources used for response
            
        Returns:
            True if successful
        """
        # Add to in-memory
        success = self.add_message(conversation_id, message)
        
        if not success:
            return False
        
        # Persist to database
        if self.auto_persist and self._message_repo:
            try:
                await self._message_repo.create(
                    message_id=str(uuid4()),
                    conversation_id=conversation_id,
                    role=message.role,
                    content=message.content,
                    context_sources=context_sources
                )
            except Exception as e:
                logger.error(f"Failed to persist message: {e}")
        
        return True
    
    async def delete_conversation_async(self, conversation_id: str) -> bool:
        """
        Delete conversation from memory and database.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if deleted
        """
        # Delete from in-memory
        deleted = self.delete_conversation(conversation_id)
        self._loaded_from_db.discard(conversation_id)
        
        # Delete from database
        if self._conversation_repo:
            try:
                await self._conversation_repo.delete(conversation_id)
            except Exception as e:
                logger.error(f"Failed to delete conversation from DB: {e}")
        
        return deleted
    
    async def list_conversations_async(
        self,
        limit: int = 50,
        include_db: bool = True
    ) -> List[Dict[str, Any]]:
        """
        List all conversations including persisted ones.
        
        Args:
            limit: Maximum number to return
            include_db: Whether to include DB-only conversations
            
        Returns:
            List of conversation summaries
        """
        # Get in-memory conversations
        summaries = self.list_conversations(limit=limit)
        in_memory_ids = {s["id"] for s in summaries}
        
        # Add database-only conversations
        if include_db and self._conversation_repo:
            try:
                db_convs = await self._conversation_repo.list_all(limit=limit)
                for conv in db_convs:
                    if conv.id not in in_memory_ids:
                        summaries.append({
                            "id": conv.id,
                            "title": conv.title,
                            "message_count": len(conv.messages) if conv.messages else 0,
                            "created_at": conv.created_at.isoformat() if conv.created_at else None,
                            "last_activity": conv.updated_at.isoformat() if conv.updated_at else None,
                            "metadata": conv.extra_data or {},
                            "persisted": True
                        })
            except Exception as e:
                logger.error(f"Failed to list conversations from DB: {e}")
        
        # Sort by activity
        summaries.sort(
            key=lambda x: x.get("last_activity") or x.get("created_at") or "",
            reverse=True
        )
        
        return summaries[:limit]
    
    async def update_title_async(
        self,
        conversation_id: str,
        title: str
    ) -> bool:
        """
        Update conversation title in database.
        
        Args:
            conversation_id: Conversation identifier
            title: New title
            
        Returns:
            True if successful
        """
        if self._conversation_repo:
            try:
                return await self._conversation_repo.update_title(conversation_id, title)
            except Exception as e:
                logger.error(f"Failed to update conversation title: {e}")
        return False
    
    async def sync_to_database(self, conversation_id: str) -> bool:
        """
        Force sync a conversation to the database.
        
        Args:
            conversation_id: Conversation to sync
            
        Returns:
            True if successful
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return False
        
        try:
            # Ensure conversation exists in DB
            if self._conversation_repo:
                existing = await self._conversation_repo.get(conversation_id)
                if not existing:
                    await self._conversation_repo.create(
                        conversation_id=conversation_id,
                        title=self._generate_title(context),
                        metadata=context.metadata
                    )
            
            # Sync messages (simplified - in production, would compare timestamps)
            if self._message_repo:
                for msg in context.messages:
                    await self._message_repo.create(
                        message_id=str(uuid4()),
                        conversation_id=conversation_id,
                        role=msg.role,
                        content=msg.content
                    )
            
            logger.info(f"Synced conversation to database: {conversation_id}")
            return True
            
        except Exception as e:
            logger.error(f"Failed to sync conversation: {e}")
            return False
    
    def _generate_title(self, context: ConversationContext) -> str:
        """Generate a title from the first user message."""
        for msg in context.messages:
            if msg.role == "user":
                # Take first 50 characters
                title = msg.content[:50]
                if len(msg.content) > 50:
                    title += "..."
                return title
        return "New Conversation"
