"""Dependency injection for FastAPI."""

from typing import Annotated

from fastapi import Depends

from app.core.capabilities import normalize_source
from app.repositories.base import MatchRepository, EventRepository
from app.repositories.postgres import PostgresRepositoryFactory
from app.repositories.sqlserver import SQLServerRepositoryFactory


def get_repository_factory(source: str = "postgres"):
    """Get repository factory based on request source."""
    normalized_source = normalize_source(source)
    if normalized_source == "postgres":
        return PostgresRepositoryFactory()
    if normalized_source == "sqlserver":
        return SQLServerRepositoryFactory()
    raise ValueError(f"Unsupported database source: {source}")


def get_match_repository(
    source: str = "postgres",
) -> MatchRepository:
    """Dependency provider for MatchRepository."""
    factory = get_repository_factory(source)
    return factory.create_match_repository()


def get_event_repository(
    source: str = "postgres",
) -> EventRepository:
    """Dependency provider for EventRepository."""
    factory = get_repository_factory(source)
    return factory.create_event_repository()


MatchRepo = Annotated[MatchRepository, Depends(get_match_repository)]
EventRepo = Annotated[EventRepository, Depends(get_event_repository)]
