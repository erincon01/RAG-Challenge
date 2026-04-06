"""Embeddings status endpoints."""

from typing import Any

from fastapi import APIRouter, HTTPException, Query, status

from app.core.capabilities import normalize_source
from app.core.dependencies import IngestionSvc

router = APIRouter()


@router.get(
    "/embeddings/status",
    response_model=dict[str, Any],
    status_code=status.HTTP_200_OK,
    summary="Get embeddings coverage status",
)
async def get_embeddings_status(
    service: IngestionSvc,
    source: str = Query(
        default="postgres", description="Database source: postgres or sqlserver"
    ),
) -> dict[str, Any]:
    try:
        return service.get_embeddings_status(normalize_source(source))
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to fetch embeddings status: {e}",
        )
