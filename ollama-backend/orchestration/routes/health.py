"""
Health Check API Routes

Provides health and status endpoints for:
- Overall system health
- Individual service health
- Configuration information
"""

import logging
from typing import Optional
from datetime import datetime
from fastapi import APIRouter, Depends
from pydantic import BaseModel

from ..models.schemas import HealthResponse, ServiceStatus
from ..orchestrator import Orchestrator
from .. import __version__


logger = logging.getLogger(__name__)

router = APIRouter(prefix="/health", tags=["Health"])


# Dependency injection placeholder
_orchestrator: Optional[Orchestrator] = None


def set_orchestrator(orchestrator: Orchestrator) -> None:
    """Set the global orchestrator instance."""
    global _orchestrator
    _orchestrator = orchestrator


def get_orchestrator() -> Orchestrator:
    """Get the orchestrator instance."""
    return _orchestrator


@router.get("/", response_model=HealthResponse)
async def health_check(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Check the health of all services.
    
    Returns the overall system health status along with
    individual service statuses.
    
    Statuses:
    - **healthy**: All services operational
    - **degraded**: Some services have issues
    - **unhealthy**: Critical services unavailable
    """
    services = []
    
    if orchestrator is None:
        return HealthResponse(
            status="unhealthy",
            version=__version__,
            services=[
                ServiceStatus(
                    name="orchestrator",
                    status="unhealthy",
                    details={"error": "Not initialized"}
                )
            ],
            timestamp=datetime.utcnow()
        )
    
    try:
        # Check orchestrator health
        result = await orchestrator.health_check()
        
        for service_name, is_healthy in result.data.items():
            services.append(
                ServiceStatus(
                    name=service_name,
                    status="healthy" if is_healthy else "unhealthy"
                )
            )
        
        # Determine overall status
        all_healthy = all(s.status == "healthy" for s in services)
        any_healthy = any(s.status == "healthy" for s in services)
        
        if all_healthy:
            overall_status = "healthy"
        elif any_healthy:
            overall_status = "degraded"
        else:
            overall_status = "unhealthy"
        
        return HealthResponse(
            status=overall_status,
            version=__version__,
            services=services,
            timestamp=datetime.utcnow()
        )
        
    except Exception as e:
        logger.error(f"Health check error: {e}")
        return HealthResponse(
            status="unhealthy",
            version=__version__,
            services=[
                ServiceStatus(
                    name="system",
                    status="unhealthy",
                    details={"error": str(e)}
                )
            ],
            timestamp=datetime.utcnow()
        )


@router.get("/live")
async def liveness():
    """
    Kubernetes-style liveness probe.
    
    Returns 200 if the service is alive.
    """
    return {"status": "alive", "timestamp": datetime.utcnow().isoformat()}


@router.get("/ready")
async def readiness(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Kubernetes-style readiness probe.
    
    Returns 200 if the service is ready to accept traffic.
    """
    if orchestrator is None or not orchestrator._initialized:
        return {
            "status": "not_ready",
            "reason": "Orchestrator not initialized"
        }
    
    return {
        "status": "ready",
        "timestamp": datetime.utcnow().isoformat()
    }


class ConfigResponse(BaseModel):
    """Current configuration response."""
    ollama_host: str
    model: str
    embedding_model: str
    vector_store: str
    rag_enabled: bool
    streaming_enabled: bool


@router.get("/config")
async def get_config(
    orchestrator: Orchestrator = Depends(get_orchestrator)
):
    """
    Get current configuration.
    
    Returns the active configuration settings.
    """
    if orchestrator is None:
        return {"error": "Orchestrator not initialized"}
    
    return orchestrator.get_config()


@router.get("/version")
async def get_version():
    """
    Get API version information.
    """
    return {
        "version": __version__,
        "api": "Ollama RAG Orchestration Layer",
        "timestamp": datetime.utcnow().isoformat()
    }
