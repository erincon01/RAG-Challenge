"""Unit tests for core/dependencies.py and DataExplorerService."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from app.core.dependencies import get_repository_factory, get_match_repository, get_event_repository
from app.repositories.base import MatchRepository, EventRepository
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
        repo = get_match_repository("postgres")
        assert isinstance(repo, MatchRepository)

    def test_returns_match_repo_for_sqlserver(self):
        repo = get_match_repository("sqlserver")
        assert isinstance(repo, MatchRepository)


class TestGetEventRepository:
    def test_returns_event_repo_for_postgres(self):
        repo = get_event_repository("postgres")
        assert isinstance(repo, EventRepository)

    def test_returns_event_repo_for_sqlserver(self):
        repo = get_event_repository("sqlserver")
        assert isinstance(repo, EventRepository)


# ---------------------------------------------------------------------------
# DataExplorerService — repository-based tests
# ---------------------------------------------------------------------------

class TestDataExplorerServiceGetTeams:
    """Tests for get_teams delegating to MatchRepository."""

    def test_get_teams_delegates_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
        ]

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_teams(source="postgres")

        mock_repo.get_teams.assert_called_once_with(match_id=None, limit=500)
        assert len(results) == 1
        assert results[0]["team_id"] == 100
        assert results[0]["name"] == "Spain"

    def test_get_teams_passes_match_id_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
        ]

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_teams(source="postgres", match_id=3943043)

        mock_repo.get_teams.assert_called_once_with(match_id=3943043, limit=500)
        assert len(results) == 1

    def test_get_teams_passes_limit_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_teams.return_value = []

        svc = DataExplorerService(match_repo=mock_repo)
        svc.get_teams(source="postgres", limit=10)

        mock_repo.get_teams.assert_called_once_with(match_id=None, limit=10)

    def test_get_teams_returns_empty_list_from_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_teams.return_value = []

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_teams(source="postgres")

        assert results == []


class TestDataExplorerServiceGetPlayers:
    """Tests for get_players delegating to MatchRepository."""

    def test_get_players_delegates_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_players.return_value = [
            {
                "player_id": 1,
                "player_name": "Rodri",
                "jersey_number": 16,
                "country_name": "Spain",
                "position_name": "Defensive Midfield",
                "team_name": "Spain",
            },
        ]

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_players(source="postgres")

        mock_repo.get_players.assert_called_once_with(match_id=None, limit=500)
        assert len(results) == 1
        assert results[0]["player_name"] == "Rodri"

    def test_get_players_passes_match_id_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_players.return_value = []

        svc = DataExplorerService(match_repo=mock_repo)
        svc.get_players(source="postgres", match_id=3943043)

        mock_repo.get_players.assert_called_once_with(match_id=3943043, limit=500)

    def test_get_players_returns_empty_list_from_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_players.return_value = []

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_players(source="postgres")

        assert results == []


class TestDataExplorerServiceGetTablesInfo:
    """Tests for get_tables_info delegating to MatchRepository."""

    def test_get_tables_info_delegates_to_repository(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_tables_info.return_value = [
            {"table": "matches", "row_count": 42, "embedding_columns": []},
        ]

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_tables_info(source="postgres")

        mock_repo.get_tables_info.assert_called_once()
        assert len(results) == 1
        assert results[0]["table"] == "matches"
        assert results[0]["row_count"] == 42

    def test_get_tables_info_returns_multiple_tables(self):
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        mock_repo.get_tables_info.return_value = [
            {"table": "matches", "row_count": 42, "embedding_columns": []},
            {"table": "events_details__quarter_minute", "row_count": 1000, "embedding_columns": ["summary_embedding_ada_002"]},
        ]

        svc = DataExplorerService(match_repo=mock_repo)
        results = svc.get_tables_info(source="postgres")

        assert len(results) == 2


class TestDataExplorerServiceNoPsycopg2Import:
    """Verify the service has no raw driver imports."""

    def test_service_has_no_psycopg2_import(self):
        import app.services.data_explorer_service as module

        source = inspect.getsource(module)
        assert "psycopg2" not in source, "DataExplorerService must not import psycopg2"

    def test_service_has_no_pyodbc_import(self):
        import app.services.data_explorer_service as module

        source = inspect.getsource(module)
        assert "pyodbc" not in source, "DataExplorerService must not import pyodbc"


# ---------------------------------------------------------------------------
# DI providers for IngestionService, StatsBombService, DataExplorerService
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

    def test_get_data_explorer_service_accepts_match_repo_injection(self):
        from app.core.dependencies import get_data_explorer_service
        from app.services.data_explorer_service import DataExplorerService

        mock_repo = MagicMock(spec=MatchRepository)
        svc = get_data_explorer_service(match_repo=mock_repo)
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
