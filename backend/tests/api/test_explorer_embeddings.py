"""
API tests for data explorer and embeddings status endpoints.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter


@pytest.fixture
def mock_explorer_svc():
    from app.services.data_explorer_service import DataExplorerService
    return MagicMock(spec=DataExplorerService)


@pytest.fixture
def mock_embeddings_svc():
    from app.services.ingestion_service import IngestionService
    return MagicMock(spec=IngestionService)


@pytest.fixture
def client(mock_explorer_svc, mock_embeddings_svc):
    from app.main import app
    from app.core.dependencies import (
        get_match_repository, get_event_repository,
        get_data_explorer_service, get_ingestion_service,
    )
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
    app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
    app.dependency_overrides[get_data_explorer_service] = lambda: mock_explorer_svc
    app.dependency_overrides[get_ingestion_service] = lambda: mock_embeddings_svc

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /explorer/teams
# ---------------------------------------------------------------------------

class TestListTeams:
    def test_get_teams_valid_request_returns_200(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
        ]
        response = client.get("/api/v1/teams")
        assert response.status_code == 200

    def test_get_teams_multiple_teams_returns_list(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
            {"team_id": 200, "name": "England", "gender": "male", "country": "England"},
        ]
        data = client.get("/api/v1/teams").json()
        assert len(data) == 2

    def test_get_teams_valid_response_contains_required_fields(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
        ]
        data = client.get("/api/v1/teams").json()
        assert "team_id" in data[0]
        assert "name" in data[0]

    def test_sqlserver_source_accepted(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.return_value = []
        response = client.get("/api/v1/teams?source=sqlserver")
        assert response.status_code == 200

    def test_match_id_filter_accepted(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.return_value = []
        response = client.get("/api/v1/teams?match_id=3943043")
        assert response.status_code == 200

    def test_returns_500_on_service_error(self, client, mock_explorer_svc):
        mock_explorer_svc.get_teams.side_effect = Exception("DB error")
        response = client.get("/api/v1/teams")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /explorer/players
# ---------------------------------------------------------------------------

class TestListPlayers:
    def test_get_players_valid_request_returns_200(self, client, mock_explorer_svc):
        mock_explorer_svc.get_players.return_value = [
            {
                "player_id": 1,
                "player_name": "Rodri",
                "jersey_number": 16,
                "country_name": "Spain",
                "position_name": "Defensive Midfield",
                "team_name": "Spain",
            },
        ]
        response = client.get("/api/v1/players")
        assert response.status_code == 200

    def test_get_players_valid_response_contains_required_fields(self, client, mock_explorer_svc):
        mock_explorer_svc.get_players.return_value = [
            {
                "player_id": 1,
                "player_name": "Rodri",
                "jersey_number": 16,
                "country_name": "Spain",
                "position_name": "Defensive Midfield",
                "team_name": "Spain",
            },
        ]
        data = client.get("/api/v1/players").json()
        player = data[0]
        assert "player_id" in player
        assert "player_name" in player

    def test_get_players_no_players_returns_empty_list(self, client, mock_explorer_svc):
        mock_explorer_svc.get_players.return_value = []
        data = client.get("/api/v1/players").json()
        assert data == []

    def test_returns_500_on_service_error(self, client, mock_explorer_svc):
        mock_explorer_svc.get_players.side_effect = Exception("DB down")
        response = client.get("/api/v1/players")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /explorer/tables-info
# ---------------------------------------------------------------------------

class TestListTablesInfo:
    def test_get_tables_info_valid_request_returns_200(self, client, mock_explorer_svc):
        mock_explorer_svc.get_tables_info.return_value = [
            {"table": "matches", "row_count": 42, "embedding_columns": []},
        ]
        response = client.get("/api/v1/tables-info")
        assert response.status_code == 200

    def test_table_info_fields_present(self, client, mock_explorer_svc):
        mock_explorer_svc.get_tables_info.return_value = [
            {"table": "matches", "row_count": 10, "embedding_columns": ["summary_embedding_ada_002"]},
        ]
        data = client.get("/api/v1/tables-info").json()
        assert "table" in data[0]
        assert "row_count" in data[0]
        assert "embedding_columns" in data[0]

    def test_returns_500_on_service_error(self, client, mock_explorer_svc):
        mock_explorer_svc.get_tables_info.side_effect = Exception("DB down")
        response = client.get("/api/v1/tables-info")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /embeddings/status
# ---------------------------------------------------------------------------

class TestGetEmbeddingsStatus:
    def test_get_embeddings_status_valid_request_returns_200(self, client, mock_embeddings_svc):
        mock_embeddings_svc.get_embeddings_status.return_value = {
            "total": 100,
            "covered": {"text-embedding-ada-002": 90},
            "status": {"done": 90, "pending": 10, "error": 0},
        }
        response = client.get("/api/v1/embeddings/status")
        assert response.status_code == 200

    def test_sqlserver_source_accepted(self, client, mock_embeddings_svc):
        mock_embeddings_svc.get_embeddings_status.return_value = {}
        response = client.get("/api/v1/embeddings/status?source=sqlserver")
        assert response.status_code == 200

    def test_returns_500_on_service_error(self, client, mock_embeddings_svc):
        mock_embeddings_svc.get_embeddings_status.side_effect = Exception("DB error")
        response = client.get("/api/v1/embeddings/status")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# TDD RED: DataExplorerService and IngestionService injected via dependency_overrides
# These tests FAIL until explorer.py and embeddings.py use Depends()
# ---------------------------------------------------------------------------

class TestExplorerDependencyInjection:
    @pytest.fixture
    def client_with_override(self):
        from unittest.mock import MagicMock
        from app.main import app
        from app.core.dependencies import (
            get_match_repository, get_event_repository,
            get_data_explorer_service,
        )
        from app.adapters.openai_client import get_openai_adapter
        from app.services.data_explorer_service import DataExplorerService

        mock_svc = MagicMock(spec=DataExplorerService)
        mock_svc.get_teams.return_value = [
            {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
        ]

        app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
        app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
        app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
        app.dependency_overrides[get_data_explorer_service] = lambda: mock_svc

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_svc

        app.dependency_overrides.clear()

    def test_teams_via_dependency_override_returns_200(self, client_with_override):
        client, _ = client_with_override
        response = client.get("/api/v1/teams")
        assert response.status_code == 200

    def test_teams_via_dependency_override_calls_service(self, client_with_override):
        client, mock_svc = client_with_override
        client.get("/api/v1/teams")
        mock_svc.get_teams.assert_called_once()


class TestEmbeddingsDependencyInjection:
    @pytest.fixture
    def client_with_override(self):
        from unittest.mock import MagicMock
        from app.main import app
        from app.core.dependencies import (
            get_match_repository, get_event_repository,
            get_ingestion_service,
        )
        from app.adapters.openai_client import get_openai_adapter
        from app.services.ingestion_service import IngestionService

        mock_svc = MagicMock(spec=IngestionService)
        mock_svc.get_embeddings_status.return_value = {"ada_002": 100}

        app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
        app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
        app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
        app.dependency_overrides[get_ingestion_service] = lambda: mock_svc

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_svc

        app.dependency_overrides.clear()

    def test_embeddings_status_via_dependency_override_returns_200(self, client_with_override):
        client, _ = client_with_override
        response = client.get("/api/v1/embeddings/status")
        assert response.status_code == 200

    def test_embeddings_status_via_dependency_override_calls_service(self, client_with_override):
        client, mock_svc = client_with_override
        client.get("/api/v1/embeddings/status")
        mock_svc.get_embeddings_status.assert_called_once()
