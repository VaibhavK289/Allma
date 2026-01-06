"""
Models API Routes

Handles LLM model management:
- List available models
- Switch active model
- Pull new models
"""

import logging
from typing import Optional, List
from fastapi import APIRouter, HTTPException, Depends
from pydantic import BaseModel

from ..models.schemas import ModelInfo, ModelsResponse
from ..orchestrator import Orchestrator


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/models", tags=["Models"])


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


@router.get("/", response_model=ModelsResponse)
async def list_models(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    List all available Ollama models.
    
    Returns the models currently available on the Ollama server,
    along with the currently active model.
    """
    try:
        result = await orchestrator.list_models()
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        models = [
            ModelInfo(
                name=m["name"],
                size=m.get("size"),
                modified_at=m.get("modified_at")
            )
            for m in result.data.get("models", [])
        ]
        
        return ModelsResponse(
            models=models,
            current_model=orchestrator.config.ollama.model
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"List models error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ModelSwitchRequest(BaseModel):
    """Request to switch the active model."""
    model: str


class ModelSwitchResponse(BaseModel):
    """Response for model switch."""
    previous_model: str
    current_model: str
    message: str


@router.post("/switch", response_model=ModelSwitchResponse)
async def switch_model(
    request: ModelSwitchRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Switch to a different LLM model.
    
    The model must be available on the Ollama server.
    Use the pull endpoint to download new models first.
    
    - **model**: Name of the model to switch to
    """
    try:
        previous = orchestrator.config.ollama.model
        
        # Verify model exists
        result = await orchestrator.list_models()
        if result.success:
            available = [m["name"] for m in result.data.get("models", [])]
            if request.model not in available and not any(request.model in m for m in available):
                raise HTTPException(
                    status_code=404,
                    detail=f"Model '{request.model}' not found. Available: {available}"
                )
        
        await orchestrator.set_model(request.model)
        
        return ModelSwitchResponse(
            previous_model=previous,
            current_model=request.model,
            message=f"Switched from {previous} to {request.model}"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Switch model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


class ModelPullRequest(BaseModel):
    """Request to pull a new model."""
    model: str


class ModelPullResponse(BaseModel):
    """Response for model pull."""
    model: str
    status: str
    message: str


@router.post("/pull", response_model=ModelPullResponse)
async def pull_model(
    request: ModelPullRequest,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Pull/download a new model from Ollama.
    
    This will download the model from the Ollama model library.
    May take some time for large models.
    
    - **model**: Name of the model to pull (e.g., "llama3.2", "mistral")
    """
    try:
        result = await orchestrator.pull_model(request.model)
        
        if not result.success:
            raise HTTPException(
                status_code=500,
                detail=f"Failed to pull model: {result.error}"
            )
        
        return ModelPullResponse(
            model=request.model,
            status="success",
            message=f"Model '{request.model}' pulled successfully"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Pull model error: {e}")
        raise HTTPException(status_code=500, detail=str(e))


@router.get("/{model_name}")
async def get_model_info(
    model_name: str,
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get detailed information about a specific model.
    
    - **model_name**: Name of the model to get info for
    """
    try:
        result = await orchestrator.list_models()
        
        if not result.success:
            raise HTTPException(status_code=500, detail=result.error)
        
        # Find the model
        for model in result.data.get("models", []):
            if model["name"] == model_name or model_name in model["name"]:
                return {
                    "name": model["name"],
                    "size": model.get("size"),
                    "modified_at": model.get("modified_at"),
                    "digest": model.get("digest"),
                    "is_current": model["name"] == orchestrator.config.ollama.model
                }
        
        raise HTTPException(
            status_code=404,
            detail=f"Model '{model_name}' not found"
        )
        
    except HTTPException:
        raise
    except Exception as e:
        logger.error(f"Get model info error: {e}")
        raise HTTPException(status_code=500, detail=str(e))
