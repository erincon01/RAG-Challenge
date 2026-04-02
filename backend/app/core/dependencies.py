"""Dependency injection for FastAPI."""

from typing import Annotated

from fastapi import Depends

from app.core.capabilities import normalize_source
from app.repositories.base import MatchRepository, EventRepository
from app.repositories.postgres import PostgresRepositoryFactory
from app.repositories.sqlserver import SQLServerRepositoryFactory
from app.services.statsbomb_service import StatsBombService
from app.services.ingestion_service import IngestionService
from app.services.data_explorer_service import DataExplorerService


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


def get_statsbomb_service() -> StatsBombService:
    """Dependency provider for StatsBombService."""
    return StatsBombService()


def get_ingestion_service(
    statsbomb: StatsBombService = Depends(get_statsbomb_service),
) -> IngestionService:
    """Dependency provider for IngestionService."""
    return IngestionService(statsbomb=statsbomb)


def get_data_explorer_service() -> DataExplorerService:
    """Dependency provider for DataExplorerService."""
    return DataExplorerService()


StatsBombSvc = Annotated[StatsBombService, Depends(get_statsbomb_service)]
IngestionSvc = Annotated[IngestionService, Depends(get_ingestion_service)]
ExplorerSvc = Annotated[DataExplorerService, Depends(get_data_explorer_service)]
