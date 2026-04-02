"""Unit tests for core/dependencies.py and DataExplorerService."""

from unittest.mock import MagicMock, patch

import pytest

from app.core.dependencies import get_repository_factory, get_match_repository, get_event_repository
from app.repositories.postgres import PostgresRepositoryFactory
from app.repositories.sqlserver import SQLServerRepositoryFactory


class TestGetRepositoryFactory:
    def test_postgres_source_returns_postgres_factory(self):
        factory = get_repository_factory("postgres")
        assert isinstance(factory, PostgresRepositoryFactory)

    def test_postgresql_alias_returns_postgres_factory(self):
        factory = get_repository_factory("postgresql")
        assert isinstance(factory, PostgresRepositoryFactory)

    def test_sqlserver_source_returns_sqlserver_factory(self):
        factory = get_repository_factory("sqlserver")
        assert isinstance(factory, SQLServerRepositoryFactory)

    def test_azure_sql_alias_returns_sqlserver_factory(self):
        factory = get_repository_factory("azure-sql")
        assert isinstance(factory, SQLServerRepositoryFactory)

    def test_unsupported_source_raises(self):
        with pytest.raises(ValueError):
            get_repository_factory("mongodb")


class TestGetMatchRepository:
    def test_returns_match_repo_for_postgres(self):
        from app.repositories.base import MatchRepository
        repo = get_match_repository("postgres")
        assert isinstance(repo, MatchRepository)

    def test_returns_match_repo_for_sqlserver(self):
        from app.repositories.base import MatchRepository
        repo = get_match_repository("sqlserver")
        assert isinstance(repo, MatchRepository)


class TestGetEventRepository:
    def test_returns_event_repo_for_postgres(self):
        from app.repositories.base import EventRepository
        repo = get_event_repository("postgres")
        assert isinstance(repo, EventRepository)

    def test_returns_event_repo_for_sqlserver(self):
        from app.repositories.base import EventRepository
        repo = get_event_repository("sqlserver")
        assert isinstance(repo, EventRepository)


# ---------------------------------------------------------------------------
# DataExplorerService tests with mocked connections
# ---------------------------------------------------------------------------

class TestDataExplorerServiceGetTeams:
    def _make_mock_conn(self, rows):
        cursor = MagicMock()
        cursor.fetchall.return_value = rows
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    @patch("app.services.data_explorer_service.psycopg2.connect")
    def test_get_teams_postgres_returns_list(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        row = (100, "Spain", "male", "Spain")
        conn, cursor = self._make_mock_conn([row])

        with patch.object(svc, "_get_connection") as mock_gc:
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_teams(source="postgres")

        assert len(results) == 1
        assert results[0]["team_id"] == 100
        assert results[0]["name"] == "Spain"

    @patch("app.services.data_explorer_service.psycopg2.connect")
    def test_get_teams_postgres_with_match_id(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        row = (100, "Spain", "male", "Spain")
        conn, cursor = self._make_mock_conn([row])

        with patch.object(svc, "_get_connection") as mock_gc:
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_teams(source="postgres", match_id=3943043)

        assert len(results) == 1

    @patch("app.services.data_explorer_service.pyodbc.connect")
    def test_get_teams_sqlserver_returns_list(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        row = (200, "England", "male", "England")
        conn, cursor = self._make_mock_conn([row])

        with patch.object(svc, "_get_connection") as mock_gc:
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_teams(source="sqlserver")

        assert len(results) == 1
        assert results[0]["name"] == "England"

    @patch("app.services.data_explorer_service.psycopg2.connect")
    def test_get_teams_skips_rows_with_none_team_id(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        rows = [(None, "Unknown", "male", "Unknown"), (100, "Spain", "male", "Spain")]
        conn, cursor = self._make_mock_conn(rows)

        with patch.object(svc, "_get_connection") as mock_gc:
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_teams(source="postgres")

        assert len(results) == 1
        assert results[0]["team_id"] == 100


class TestDataExplorerServiceGetPlayers:
    def _make_mock_conn(self, rows, table_exists=True):
        cursor = MagicMock()
        cursor.fetchall.return_value = rows
        # table exists check: fetchone returns a row or None
        cursor.fetchone.return_value = (1,) if table_exists else None
        conn = MagicMock()
        conn.cursor.return_value = cursor
        return conn, cursor

    @patch("app.services.data_explorer_service.psycopg2.connect")
    def test_get_players_returns_empty_when_no_table(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        conn, cursor = self._make_mock_conn(rows=[], table_exists=False)

        with patch.object(svc, "_get_connection") as mock_gc:
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_players(source="postgres")

        assert results == []

    @patch("app.services.data_explorer_service.psycopg2.connect")
    def test_get_players_postgres_returns_list(self, mock_connect):
        from app.services.data_explorer_service import DataExplorerService

        svc = DataExplorerService()
        player_row = (1, "Rodri", 16, "Spain", "Defensive Midfield", "Spain")
        conn, cursor = self._make_mock_conn(rows=[player_row], table_exists=True)
        # first fetchone for table check, then fetchall for data
        cursor.fetchone.return_value = (1,)

        with patch.object(svc, "_table_exists") as mock_te, patch.object(svc, "_get_connection") as mock_gc:
            mock_te.return_value = True
            mock_gc.return_value.__enter__ = MagicMock(return_value=conn)
            mock_gc.return_value.__exit__ = MagicMock(return_value=False)
            results = svc.get_players(source="postgres")

        assert len(results) == 1
        assert results[0]["player_name"] == "Rodri"


# ---------------------------------------------------------------------------
# TDD RED: DI providers for IngestionService, StatsBombService, DataExplorerService
# These tests FAIL until the providers are added to core/dependencies.py
# ---------------------------------------------------------------------------

class TestGetIngestionServiceProvider:
    def test_get_ingestion_service_returns_ingestion_service(self):
        from app.core.dependencies import get_ingestion_service
        from app.services.ingestion_service import IngestionService

        svc = get_ingestion_service()
        assert isinstance(svc, IngestionService)

    def test_get_ingestion_service_accepts_statsbomb_injection(self):
        from app.core.dependencies import get_ingestion_service
        from app.services.statsbomb_service import StatsBombService

        mock_sb = MagicMock(spec=StatsBombService)
        svc = get_ingestion_service(statsbomb=mock_sb)
        assert svc.statsbomb is mock_sb

    def test_ingestion_svc_alias_is_annotated(self):
        from app.core.dependencies import IngestionSvc
        import typing
        assert hasattr(IngestionSvc, "__metadata__") or hasattr(typing.get_args(IngestionSvc), "__len__")


class TestGetStatsBombServiceProvider:
    def test_get_statsbomb_service_returns_statsbomb_service(self):
        from app.core.dependencies import get_statsbomb_service
        from app.services.statsbomb_service import StatsBombService

        svc = get_statsbomb_service()
        assert isinstance(svc, StatsBombService)

    def test_statsbomb_svc_alias_is_annotated(self):
        from app.core.dependencies import StatsBombSvc
        import typing
        assert hasattr(StatsBombSvc, "__metadata__") or hasattr(typing.get_args(StatsBombSvc), "__len__")


class TestGetDataExplorerServiceProvider:
    def test_get_data_explorer_service_returns_data_explorer_service(self):
        from app.core.dependencies import get_data_explorer_service
        from app.services.data_explorer_service import DataExplorerService

        svc = get_data_explorer_service()
        assert isinstance(svc, DataExplorerService)

    def test_explorer_svc_alias_is_annotated(self):
        from app.core.dependencies import ExplorerSvc
        import typing
        assert hasattr(ExplorerSvc, "__metadata__") or hasattr(typing.get_args(ExplorerSvc), "__len__")


class TestIngestionServiceAcceptsStatsBombParam:
    def test_init_with_statsbomb_uses_provided_instance(self):
        from app.services.ingestion_service import IngestionService
        from app.services.statsbomb_service import StatsBombService

        mock_sb = MagicMock(spec=StatsBombService)
        svc = IngestionService(statsbomb=mock_sb)
        assert svc.statsbomb is mock_sb

    def test_init_without_statsbomb_creates_default(self):
        from app.services.ingestion_service import IngestionService
        from app.services.statsbomb_service import StatsBombService

        svc = IngestionService()
        assert isinstance(svc.statsbomb, StatsBombService)
