"""Capabilities and source status endpoints."""

from datetime import datetime

from fastapi import APIRouter, Depends, Query, status
from pydantic import BaseModel

from app.core.capabilities import (
    SOURCE_CAPABILITIES,
    get_source_capabilities,
    normalize_source,
)
from app.core.dependencies import get_postgres_event_repository, get_sqlserver_event_repository
from app.repositories.base import EventRepository

router = APIRouter()


class SourceCapabilitiesResponse(BaseModel):
    """Capabilities for a source."""

    source: str
    embedding_models: list[str]
    search_algorithms: list[str]


class CapabilitiesResponse(BaseModel):
    """Capabilities matrix for all configured sources."""

    capabilities: dict[str, SourceCapabilitiesResponse]


class SourceStatusItem(BaseModel):
    """Connection status for a source."""

    source: str
    connected: bool


class SourceStatusResponse(BaseModel):
    """Current source connectivity status."""

    timestamp: datetime
    sources: list[SourceStatusItem]


@router.get(
    "/capabilities",
    response_model=CapabilitiesResponse,
    status_code=status.HTTP_200_OK,
    summary="Capabilities by source",
    description="Get supported embedding models and search algorithms for each source.",
)
async def get_capabilities() -> CapabilitiesResponse:
    """Return capability matrix for all sources."""
    data: dict[str, SourceCapabilitiesResponse] = {}
    for source, caps in SOURCE_CAPABILITIES.items():
        data[source] = SourceCapabilitiesResponse(
            source=source,
            embedding_models=caps["embedding_models"],
            search_algorithms=caps["search_algorithms"],
        )
    return CapabilitiesResponse(capabilities=data)


@router.get(
    "/sources/status",
    response_model=SourceStatusResponse,
    status_code=status.HTTP_200_OK,
    summary="Source connectivity status",
    description="Check connectivity for postgres and sqlserver repositories.",
)
async def get_sources_status(
    postgres_repo: EventRepository = Depends(get_postgres_event_repository),
    sqlserver_repo: EventRepository = Depends(get_sqlserver_event_repository),
    source: str | None = Query(
        default=None,
        description="Optional source filter: postgres or sqlserver",
    ),
) -> SourceStatusResponse:
    """Check repository-level connectivity per source."""
    repos = {
        "postgres": postgres_repo,
        "sqlserver": sqlserver_repo,
    }

    requested_sources: list[str]
    if source:
        requested_sources = [normalize_source(source)]
        # Validate source exists
        get_source_capabilities(requested_sources[0])
    else:
        requested_sources = ["postgres", "sqlserver"]

    items: list[SourceStatusItem] = []
    for src in requested_sources:
        connected = repos[src].test_connection()
        items.append(SourceStatusItem(source=src, connected=connected))

    return SourceStatusResponse(timestamp=datetime.utcnow(), sources=items)
