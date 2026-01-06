"""
Conversation Service

Manages conversation state and history for chat interactions.
Implements conversation patterns as implied by the architectural diagram:
- Multi-turn conversations
- Context management
- History persistence (optional)
"""

import logging
from typing import Dict, List, Optional, Any
from datetime import datetime, timedelta
from dataclasses import dataclass, field
from collections import OrderedDict

from ..models.schemas import ChatMessage, ConversationContext


logger = logging.getLogger(__name__)


@dataclass
class ConversationStats:
    """Statistics for a conversation."""
    message_count: int = 0
    user_messages: int = 0
    assistant_messages: int = 0
    total_tokens_estimate: int = 0
    started_at: Optional[datetime] = None
    last_activity: Optional[datetime] = None


class ConversationService:
    """
    Conversation Management Service
    
    Handles:
    - Conversation lifecycle (create, update, delete)
    - Message history management
    - Context window optimization
    - Memory/cache management
    
    Uses LRU cache to manage memory for active conversations.
    """
    
    def __init__(
        self,
        max_conversations: int = 100,
        max_messages_per_conversation: int = 100,
        conversation_ttl_hours: int = 24
    ):
        """
        Initialize conversation service.
        
        Args:
            max_conversations: Maximum number of active conversations
            max_messages_per_conversation: Max messages to retain per conversation
            conversation_ttl_hours: Time-to-live for inactive conversations
        """
        self.max_conversations = max_conversations
        self.max_messages = max_messages_per_conversation
        self.ttl_hours = conversation_ttl_hours
        
        # LRU cache for conversations
        self._conversations: OrderedDict[str, ConversationContext] = OrderedDict()
        self._stats: Dict[str, ConversationStats] = {}
    
    def create_conversation(
        self,
        conversation_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """
        Create a new conversation.
        
        Args:
            conversation_id: Unique identifier
            metadata: Optional metadata
            
        Returns:
            New ConversationContext
        """
        # Evict oldest if at capacity
        while len(self._conversations) >= self.max_conversations:
            oldest_id = next(iter(self._conversations))
            self._evict_conversation(oldest_id)
        
        context = ConversationContext(
            id=conversation_id,
            messages=[],
            metadata=metadata or {},
            created_at=datetime.utcnow()
        )
        
        self._conversations[conversation_id] = context
        self._stats[conversation_id] = ConversationStats(
            started_at=datetime.utcnow(),
            last_activity=datetime.utcnow()
        )
        
        logger.debug(f"Created conversation: {conversation_id}")
        return context
    
    def get_conversation(
        self,
        conversation_id: str
    ) -> Optional[ConversationContext]:
        """
        Retrieve a conversation by ID.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            ConversationContext or None
        """
        if conversation_id not in self._conversations:
            return None
        
        # Move to end (most recently used)
        self._conversations.move_to_end(conversation_id)
        
        # Update activity timestamp
        if conversation_id in self._stats:
            self._stats[conversation_id].last_activity = datetime.utcnow()
        
        return self._conversations[conversation_id]
    
    def get_or_create(
        self,
        conversation_id: str,
        metadata: Optional[Dict[str, Any]] = None
    ) -> ConversationContext:
        """Get existing conversation or create new one."""
        context = self.get_conversation(conversation_id)
        if context:
            return context
        return self.create_conversation(conversation_id, metadata)
    
    def add_message(
        self,
        conversation_id: str,
        message: ChatMessage
    ) -> bool:
        """
        Add a message to a conversation.
        
        Args:
            conversation_id: Conversation identifier
            message: Message to add
            
        Returns:
            True if successful
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return False
        
        # Trim if exceeding max messages
        if len(context.messages) >= self.max_messages:
            # Keep system messages and trim oldest non-system messages
            system_msgs = [m for m in context.messages if m.role == "system"]
            other_msgs = [m for m in context.messages if m.role != "system"]
            
            # Keep last N-1 messages to make room for new one
            keep_count = self.max_messages - len(system_msgs) - 1
            context.messages = system_msgs + other_msgs[-keep_count:]
        
        context.messages.append(message)
        
        # Update stats
        if conversation_id in self._stats:
            stats = self._stats[conversation_id]
            stats.message_count += 1
            stats.last_activity = datetime.utcnow()
            if message.role == "user":
                stats.user_messages += 1
            elif message.role == "assistant":
                stats.assistant_messages += 1
            # Rough token estimate
            stats.total_tokens_estimate += len(message.content.split()) * 1.3
        
        return True
    
    def get_messages(
        self,
        conversation_id: str,
        limit: Optional[int] = None,
        include_system: bool = True
    ) -> List[ChatMessage]:
        """
        Get messages from a conversation.
        
        Args:
            conversation_id: Conversation identifier
            limit: Maximum number of messages to return
            include_system: Whether to include system messages
            
        Returns:
            List of messages
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return []
        
        messages = context.messages
        
        if not include_system:
            messages = [m for m in messages if m.role != "system"]
        
        if limit:
            messages = messages[-limit:]
        
        return messages
    
    def set_system_message(
        self,
        conversation_id: str,
        content: str
    ) -> bool:
        """
        Set or update the system message for a conversation.
        
        Args:
            conversation_id: Conversation identifier
            content: System message content
            
        Returns:
            True if successful
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return False
        
        # Remove existing system messages
        context.messages = [m for m in context.messages if m.role != "system"]
        
        # Add new system message at the beginning
        system_msg = ChatMessage(role="system", content=content)
        context.messages.insert(0, system_msg)
        
        return True
    
    def clear_history(
        self,
        conversation_id: str,
        keep_system: bool = True
    ) -> bool:
        """
        Clear conversation history.
        
        Args:
            conversation_id: Conversation identifier
            keep_system: Whether to preserve system messages
            
        Returns:
            True if successful
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return False
        
        if keep_system:
            context.messages = [m for m in context.messages if m.role == "system"]
        else:
            context.messages = []
        
        return True
    
    def delete_conversation(self, conversation_id: str) -> bool:
        """
        Delete a conversation.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            True if deleted, False if not found
        """
        if conversation_id in self._conversations:
            del self._conversations[conversation_id]
            self._stats.pop(conversation_id, None)
            logger.debug(f"Deleted conversation: {conversation_id}")
            return True
        return False
    
    def list_conversations(
        self,
        limit: Optional[int] = None
    ) -> List[Dict[str, Any]]:
        """
        List all active conversations.
        
        Args:
            limit: Maximum number to return
            
        Returns:
            List of conversation summaries
        """
        summaries = []
        
        for conv_id, context in reversed(self._conversations.items()):
            stats = self._stats.get(conv_id, ConversationStats())
            
            summaries.append({
                "id": conv_id,
                "message_count": len(context.messages),
                "created_at": context.created_at.isoformat() if context.created_at else None,
                "last_activity": stats.last_activity.isoformat() if stats.last_activity else None,
                "metadata": context.metadata
            })
            
            if limit and len(summaries) >= limit:
                break
        
        return summaries
    
    def get_stats(self, conversation_id: str) -> Optional[ConversationStats]:
        """Get statistics for a conversation."""
        return self._stats.get(conversation_id)
    
    def cleanup_expired(self) -> int:
        """
        Remove expired conversations.
        
        Returns:
            Number of conversations removed
        """
        cutoff = datetime.utcnow() - timedelta(hours=self.ttl_hours)
        expired = []
        
        for conv_id, stats in self._stats.items():
            if stats.last_activity and stats.last_activity < cutoff:
                expired.append(conv_id)
        
        for conv_id in expired:
            self._evict_conversation(conv_id)
        
        if expired:
            logger.info(f"Cleaned up {len(expired)} expired conversations")
        
        return len(expired)
    
    def _evict_conversation(self, conversation_id: str) -> None:
        """Evict a conversation from cache."""
        self._conversations.pop(conversation_id, None)
        self._stats.pop(conversation_id, None)
        logger.debug(f"Evicted conversation: {conversation_id}")
    
    def get_context_for_llm(
        self,
        conversation_id: str,
        max_tokens: int = 4000
    ) -> List[Dict[str, str]]:
        """
        Get conversation context formatted for LLM.
        
        Optimizes context to fit within token limit.
        
        Args:
            conversation_id: Conversation identifier
            max_tokens: Maximum token budget
            
        Returns:
            List of message dicts for LLM API
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return []
        
        messages = []
        token_count = 0
        
        # Always include system message first
        for msg in context.messages:
            if msg.role == "system":
                messages.append({"role": msg.role, "content": msg.content})
                token_count += len(msg.content.split()) * 1.3
                break
        
        # Add messages from most recent, respecting token limit
        other_msgs = [m for m in context.messages if m.role != "system"]
        
        for msg in reversed(other_msgs):
            msg_tokens = len(msg.content.split()) * 1.3
            if token_count + msg_tokens > max_tokens:
                break
            messages.insert(1, {"role": msg.role, "content": msg.content})
            token_count += msg_tokens
        
        return messages
    
    def export_conversation(
        self,
        conversation_id: str
    ) -> Optional[Dict[str, Any]]:
        """
        Export a conversation for persistence.
        
        Args:
            conversation_id: Conversation identifier
            
        Returns:
            Serializable conversation data
        """
        context = self.get_conversation(conversation_id)
        if not context:
            return None
        
        stats = self._stats.get(conversation_id, ConversationStats())
        
        return {
            "id": context.id,
            "messages": [
                {"role": m.role, "content": m.content, "timestamp": m.timestamp.isoformat() if m.timestamp else None}
                for m in context.messages
            ],
            "metadata": context.metadata,
            "created_at": context.created_at.isoformat() if context.created_at else None,
            "stats": {
                "message_count": stats.message_count,
                "user_messages": stats.user_messages,
                "assistant_messages": stats.assistant_messages
            }
        }
    
    def import_conversation(
        self,
        data: Dict[str, Any]
    ) -> Optional[ConversationContext]:
        """
        Import a conversation from exported data.
        
        Args:
            data: Exported conversation data
            
        Returns:
            Imported ConversationContext
        """
        try:
            conversation_id = data["id"]
            
            context = self.create_conversation(
                conversation_id,
                metadata=data.get("metadata", {})
            )
            
            for msg_data in data.get("messages", []):
                msg = ChatMessage(
                    role=msg_data["role"],
                    content=msg_data["content"]
                )
                self.add_message(conversation_id, msg)
            
            return context
            
        except Exception as e:
            logger.error(f"Failed to import conversation: {e}")
            return None
