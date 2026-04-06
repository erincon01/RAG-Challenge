"""Data explorer service for teams, players and table metadata."""

from __future__ import annotations

from typing import Any

from app.repositories.base import MatchRepository


class DataExplorerService:
    """Read-only service for operational data exploration endpoints.

    Delegates all database access to injected repository instances.
    """

    def __init__(self, match_repo: MatchRepository | None = None):
        self._match_repo = match_repo

    def get_teams(
        self, source: str, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get team metadata, delegating to the match repository."""
        if self._match_repo is None:
            raise RuntimeError("MatchRepository not injected")
        return self._match_repo.get_teams(match_id=match_id, limit=limit)

    def get_players(
        self, source: str, match_id: int | None = None, limit: int = 500
    ) -> list[dict[str, Any]]:
        """Get player roster data, delegating to the match repository."""
        if self._match_repo is None:
            raise RuntimeError("MatchRepository not injected")
        return self._match_repo.get_players(match_id=match_id, limit=limit)

    def get_tables_info(self, source: str) -> list[dict[str, Any]]:
        """Get table metadata, delegating to the match repository."""
        if self._match_repo is None:
            raise RuntimeError("MatchRepository not injected")
        return self._match_repo.get_tables_info()
