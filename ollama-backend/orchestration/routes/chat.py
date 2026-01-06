"""
Chat API Routes

Handles chat interactions with the LLM through the orchestrator.
Supports both standard request-response and streaming.
"""

import logging
from typing import Optional
from fastapi import APIRouter, HTTPException, Depends
from fastapi.responses import StreamingResponse
from pydantic import BaseModel, Field

from ..models.schemas import ChatRequest, ChatResponse
from ..orchestrator import Orchestrator


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/chat", tags=["Chat"])


# Dependency injection placeholder for orchestrator
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


@router.post("/", response_model=ChatResponse)
async def chat(
    request: ChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Send a chat message and receive a response.
    
    The message will be processed through the RAG pipeline if `use_rag` is True,
    retrieving relevant context from the knowledge base before generating a response.
    
    - **message**: The user's input message
    - **conversation_id**: Optional ID for multi-turn conversations
    - **use_rag**: Whether to augment with retrieved context (default: True)
    - **stream**: Whether to stream the response (default: False)
    
    Returns:
        ChatResponse with the assistant's reply and metadata
    """
    try:
        # Apply model override if provided
        if request.model:
            await orchestrator.set_model(request.model)
        
        # Check if streaming is requested
        if request.stream:
            return StreamingResponse(
                orchestrator.chat(
                    message=request.message,
                    conversation_id=request.conversation_id,
                    use_rag=request.use_rag,
                    stream=True
                ),
                media_type="text/event-stream"
            )
        
        # Standard response
        response = await orchestrator.chat(
            message=request.message,
            conversation_id=request.conversation_id,
            use_rag=request.use_rag,
            stream=False
        )
        
        return response
        
    except Exception as e:
        logger.error(f"Chat error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/stream")
async def chat_stream(
    request: ChatRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Send a chat message and stream the response.
    
    Returns a stream of text tokens as they are generated.
    Useful for real-time UI updates.
    """
    try:
        async def generate():
            async for token in await orchestrator.chat(
                message=request.message,
                conversation_id=request.conversation_id,
                use_rag=request.use_rag,
                stream=True
            ):
                yield f"data: {token}\n\n"
            yield "data: [DONE]\n\n"
        
        return StreamingResponse(
            generate(),
            media_type="text/event-stream",
            headers={
                "Cache-Control": "no-cache",
                "Connection": "keep-alive",
            }
        )
        
    except Exception as e:
        logger.error(f"Stream error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ConversationResponse(BaseModel):
    """Response for conversation operations."""
    id: str
    message_count: int
    created_at: Optional[str] = None


@router.get("/conversation/{conversation_id}")
async def get_conversation(
    conversation_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get conversation details and history.
    
    - **conversation_id**: The conversation ID to retrieve
    
    Returns:
        Conversation details with message history
    """
    conversation = await orchestrator.get_conversation(conversation_id)
    
    if not conversation:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found: {conversation_id}"
        )
    
    return {
        "id": conversation.id,
        "messages": [
            {"role": m.role, "content": m.content}
            for m in conversation.messages
        ],
        "created_at": conversation.created_at.isoformat() if conversation.created_at else None
    }


@router.delete("/conversation/{conversation_id}")
async def delete_conversation(
    conversation_id: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Delete a conversation and its history.
    
    - **conversation_id**: The conversation ID to delete
    """
    success = await orchestrator.clear_conversation(conversation_id)
    
    if not success:
        raise HTTPException(
            status_code=404,
            detail=f"Conversation not found: {conversation_id}"
        )
    
    return {"status": "deleted", "conversation_id": conversation_id}


@router.get("/conversations")
async def list_conversations(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    List all active conversations.
    
    Returns:
        List of conversation summaries
    """
    conversations = await orchestrator.list_conversations()
    return {"conversations": conversations}
