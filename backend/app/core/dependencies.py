"""
Dependency injection for FastAPI.

This module provides functions for injecting dependencies into route handlers.
"""

from typing import Annotated
from fastapi import Depends, HTTPException, Header

from app.core.config import get_settings, Settings
from app.repositories.base import MatchRepository, EventRepository
from app.repositories.postgres import (
    PostgresMatchRepository,
    PostgresEventRepository,
    PostgresRepositoryFactory,
)
from app.repositories.sqlserver import (
    SQLServerMatchRepository,
    SQLServerEventRepository,
    SQLServerRepositoryFactory,
)


def get_repository_factory(source: str = "postgres"):
    """
    Get the appropriate repository factory based on the source.

    Args:
        source: Database source ("postgres" or "sqlserver")

    Returns:
        Repository factory instance

    Raises:
        ValueError: If source is not supported
    """
    if source.lower() in ["postgres", "postgresql", "azure-postgres"]:
        return PostgresRepositoryFactory()
    elif source.lower() in ["sqlserver", "sql-server", "azure-sql"]:
        return SQLServerRepositoryFactory()
    else:
        raise ValueError(f"Unsupported database source: {source}")


def get_match_repository(
    source: str = "postgres",
) -> MatchRepository:
    """
    Dependency for injecting MatchRepository.

    Args:
        source: Database source ("postgres" or "sqlserver")

    Returns:
        MatchRepository instance

    Example:
        @app.get("/matches/{match_id}")
        async def get_match(
            match_id: int,
            repo: MatchRepository = Depends(get_match_repository)
        ):
            return repo.get_by_id(match_id)
    """
    factory = get_repository_factory(source)
    return factory.create_match_repository()


def get_event_repository(
    source: str = "postgres",
) -> EventRepository:
    """
    Dependency for injecting EventRepository.

    Args:
        source: Database source ("postgres" or "sqlserver")

    Returns:
        EventRepository instance

    Example:
        @app.get("/events")
        async def get_events(
            match_id: int,
            repo: EventRepository = Depends(get_event_repository)
        ):
            return repo.get_events_by_match(match_id)
    """
    factory = get_repository_factory(source)
    return factory.create_event_repository()


# Type aliases for cleaner route signatures
MatchRepo = Annotated[MatchRepository, Depends(get_match_repository)]
EventRepo = Annotated[EventRepository, Depends(get_event_repository)]
