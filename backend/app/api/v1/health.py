"""
Health check endpoints.

Provides endpoints for monitoring service health and readiness.
"""

from datetime import datetime
from typing import Dict, Any

from fastapi import APIRouter, Depends, status
from pydantic import BaseModel

from app.core.config import get_settings, Settings
from app.repositories.postgres import PostgresEventRepository
from app.repositories.sqlserver import SQLServerEventRepository

router = APIRouter()


class HealthResponse(BaseModel):
    """Health check response model."""

    status: str
    timestamp: datetime
    environment: str
    version: str
    checks: Dict[str, Any]


class ReadinessResponse(BaseModel):
    """Readiness check response model."""

    ready: bool
    checks: Dict[str, bool]


@router.get(
    "/health",
    response_model=HealthResponse,
    status_code=status.HTTP_200_OK,
    summary="Health check",
    description="Check if the service is running and healthy",
)
async def health_check(settings: Settings = Depends(get_settings)) -> HealthResponse:
    """
    Health check endpoint.

    Returns basic service status information.
    This endpoint always returns 200 OK if the service is running.

    Args:
        settings: Application settings (injected)

    Returns:
        HealthResponse: Service health information
    """
    return HealthResponse(
        status="healthy",
        timestamp=datetime.utcnow(),
        environment=settings.environment,
        version="0.1.0",
        checks={
            "api": "ok",
            "config": "ok",
        },
    )


@router.get(
    "/health/ready",
    response_model=ReadinessResponse,
    status_code=status.HTTP_200_OK,
    summary="Readiness check",
    description="Check if the service is ready to accept requests",
)
async def readiness_check(
    settings: Settings = Depends(get_settings),
) -> ReadinessResponse:
    """
    Readiness check endpoint.

    Checks if all dependencies (databases, external services) are available.
    Returns 200 OK only if the service is ready to handle requests.

    Args:
        settings: Application settings (injected)

    Returns:
        ReadinessResponse: Service readiness information
    """
    postgres_ok = PostgresEventRepository().test_connection()
    sqlserver_ok = SQLServerEventRepository().test_connection()

    checks = {
        "api": True,
        "config": True,
        "postgres": postgres_ok,
        "sqlserver": sqlserver_ok,
    }

    all_ready = all(checks.values())

    return ReadinessResponse(
        ready=all_ready,
        checks=checks,
    )


@router.get(
    "/health/live",
    status_code=status.HTTP_200_OK,
    summary="Liveness check",
    description="Check if the service is alive (for Kubernetes liveness probes)",
)
async def liveness_check() -> Dict[str, str]:
    """
    Liveness check endpoint.

    Minimal endpoint that only checks if the process is running.
    Used by Kubernetes/Docker for liveness probes.

    Returns:
        dict: Simple alive status
    """
    return {"status": "alive"}
