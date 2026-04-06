"""
Base repository interfaces.

These define the contract that all repository implementations must follow.
This enables us to swap implementations (e.g., PostgreSQL vs SQL Server) without
changing business logic.
"""

from abc import ABC, abstractmethod
from contextlib import contextmanager
from typing import Any

from app.domain.entities import (
    Competition,
    EventDetail,
    Match,
    SearchRequest,
    SearchResult,
)


class BaseRepository(ABC):
    """Base repository with common database operations."""

    @abstractmethod
    @contextmanager
    def get_connection(self):
        """
        Get a database connection.

        Yields:
            Connection object (implementation-specific)
        """
        pass

    @abstractmethod
    def test_connection(self) -> bool:
        """
        Test if database connection is working.

        Returns:
            bool: True if connection is successful
        """
        pass

    @abstractmethod
    def get_tables_info(self) -> list[dict[str, Any]]:
        """
        Get table metadata (name, row_count, embedding_columns).

        Returns:
            List of dicts with table metadata
        """
        pass


class MatchRepository(BaseRepository):
    """Repository for Match entities."""

    @abstractmethod
    def get_by_id(self, match_id: int) -> Match | None:
        """
        Get a match by ID.

        Args:
            match_id: The match ID

        Returns:
            Match if found, None otherwise
        """
        pass

    @abstractmethod
    def get_all(
        self,
        competition_name: str | None = None,
        season_name: str | None = None,
        limit: int = 100,
    ) -> list[Match]:
        """
        Get all matches with optional filters.

        Args:
            competition_name: Filter by competition name
            season_name: Filter by season name
            limit: Maximum number of results

        Returns:
            List of matches
        """
        pass

    @abstractmethod
    def get_competitions(self) -> list[Competition]:
        """
        Get all unique competitions.

        Returns:
            List of competitions
        """
        pass

    @abstractmethod
    def get_teams(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """
        Get team metadata (team_id, name, gender, country).

        Args:
            match_id: Optional filter by match ID
            limit: Maximum number of results

        Returns:
            List of team dicts
        """
        pass

    @abstractmethod
    def get_players(
        self, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """
        Get player roster data (player_id, player_name, jersey_number, etc).

        Args:
            match_id: Optional filter by match ID
            limit: Maximum number of results

        Returns:
            List of player dicts
        """
        pass


class EventRepository(BaseRepository):
    """Repository for Event entities."""

    @abstractmethod
    def get_events_by_match(
        self, match_id: int, limit: int | None = None
    ) -> list[EventDetail]:
        """
        Get all events for a match.

        Args:
            match_id: The match ID
            limit: Maximum number of results

        Returns:
            List of event details
        """
        pass

    @abstractmethod
    def search_by_embedding(
        self, search_request: SearchRequest, query_embedding: list[float]
    ) -> list[SearchResult]:
        """
        Search events using vector similarity.

        Args:
            search_request: Search parameters
            query_embedding: The embedding vector for the search query

        Returns:
            List of search results ordered by similarity
        """
        pass

    @abstractmethod
    def get_event_by_id(self, event_id: int) -> EventDetail | None:
        """
        Get a single event by ID.

        Args:
            event_id: The event ID

        Returns:
            EventDetail if found, None otherwise
        """
        pass


class RepositoryFactory(ABC):
    """Factory for creating repository instances."""

    @abstractmethod
    def create_match_repository(self) -> MatchRepository:
        """Create a match repository instance."""
        pass

    @abstractmethod
    def create_event_repository(self) -> EventRepository:
        """Create an event repository instance."""
        pass
