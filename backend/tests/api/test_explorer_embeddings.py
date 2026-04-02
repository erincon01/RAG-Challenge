"""
API tests for data explorer and embeddings status endpoints.
"""

from unittest.mock import patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter


@pytest.fixture
def client():
    from app.main import app
    from app.core.dependencies import get_match_repository, get_event_repository
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
    app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# GET /explorer/teams
# ---------------------------------------------------------------------------

class TestListTeams:
    def test_returns_200(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.return_value = [
                {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
            ]
            response = client.get("/api/v1/teams")
        assert response.status_code == 200

    def test_returns_list(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.return_value = [
                {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
                {"team_id": 200, "name": "England", "gender": "male", "country": "England"},
            ]
            data = client.get("/api/v1/teams").json()
        assert len(data) == 2

    def test_team_fields_present(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.return_value = [
                {"team_id": 100, "name": "Spain", "gender": "male", "country": "Spain"},
            ]
            data = client.get("/api/v1/teams").json()
        assert "team_id" in data[0]
        assert "name" in data[0]

    def test_sqlserver_source_accepted(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.return_value = []
            response = client.get("/api/v1/teams?source=sqlserver")
        assert response.status_code == 200

    def test_match_id_filter_accepted(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.return_value = []
            response = client.get("/api/v1/teams?match_id=3943043")
        assert response.status_code == 200

    def test_returns_500_on_service_error(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_teams.side_effect = Exception("DB error")
            response = client.get("/api/v1/teams")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /explorer/players
# ---------------------------------------------------------------------------

class TestListPlayers:
    def test_returns_200(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_players.return_value = [
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

    def test_player_fields_present(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_players.return_value = [
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

    def test_returns_empty_list(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_players.return_value = []
            data = client.get("/api/v1/players").json()
        assert data == []

    def test_returns_500_on_service_error(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_players.side_effect = Exception("DB down")
            response = client.get("/api/v1/players")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /explorer/tables-info
# ---------------------------------------------------------------------------

class TestListTablesInfo:
    def test_returns_200(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_tables_info.return_value = [
                {"table": "matches", "row_count": 42, "embedding_columns": []},
            ]
            response = client.get("/api/v1/tables-info")
        assert response.status_code == 200

    def test_table_info_fields_present(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_tables_info.return_value = [
                {"table": "matches", "row_count": 10, "embedding_columns": ["summary_embedding_ada_002"]},
            ]
            data = client.get("/api/v1/tables-info").json()
        assert "table" in data[0]
        assert "row_count" in data[0]
        assert "embedding_columns" in data[0]

    def test_returns_500_on_service_error(self, client):
        with patch("app.api.v1.explorer._service") as mock_svc:
            mock_svc.get_tables_info.side_effect = Exception("DB down")
            response = client.get("/api/v1/tables-info")
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# GET /embeddings/status
# ---------------------------------------------------------------------------

class TestGetEmbeddingsStatus:
    def test_returns_200(self, client):
        with patch("app.api.v1.embeddings._service") as mock_svc:
            mock_svc.get_embeddings_status.return_value = {
                "total": 100,
                "covered": {"text-embedding-ada-002": 90},
                "status": {"done": 90, "pending": 10, "error": 0},
            }
            response = client.get("/api/v1/embeddings/status")
        assert response.status_code == 200

    def test_sqlserver_source_accepted(self, client):
        with patch("app.api.v1.embeddings._service") as mock_svc:
            mock_svc.get_embeddings_status.return_value = {}
            response = client.get("/api/v1/embeddings/status?source=sqlserver")
        assert response.status_code == 200

    def test_returns_500_on_service_error(self, client):
        with patch("app.api.v1.embeddings._service") as mock_svc:
            mock_svc.get_embeddings_status.side_effect = Exception("DB error")
            response = client.get("/api/v1/embeddings/status")
        assert response.status_code == 500
