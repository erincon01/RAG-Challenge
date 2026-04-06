"""
API tests for StatsBomb catalog endpoints.

GET /api/v1/statsbomb/competitions
GET /api/v1/statsbomb/matches
"""

from unittest.mock import patch, MagicMock
import pytest
from fastapi.testclient import TestClient

from tests.conftest import make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter

COMPETITIONS_RAW = [
    {"competition_id": 55, "season_id": 282, "competition_name": "UEFA Euro", "season_name": "2024", "country_name": "Europe"},
    {"competition_id": 11, "season_id": 90, "competition_name": "La Liga", "season_name": "2023/24", "country_name": "Spain"},
    {"competition_id": 2, "season_id": 44, "competition_name": "Champions League", "season_name": "2023/24", "country_name": "Europe"},
]

MATCHES_RAW = [
    {"match_id": 3943043, "match_date": "2024-07-14", "home_score": 2, "away_score": 1,
     "home_team": {"home_team_name": "Spain"}, "away_team": {"away_team_name": "England"}},
    {"match_id": 3943044, "match_date": "2024-07-10", "home_score": 1, "away_score": 2,
     "home_team": {"home_team_name": "France"}, "away_team": {"away_team_name": "Spain"}},
]


@pytest.fixture
def mock_statsbomb_svc():
    from app.services.statsbomb_service import StatsBombService
    return MagicMock(spec=StatsBombService)


@pytest.fixture
def client(mock_statsbomb_svc):
    from app.main import app
    from app.core.dependencies import (
        get_match_repository, get_event_repository, get_statsbomb_service,
    )
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
    app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
    app.dependency_overrides[get_statsbomb_service] = lambda: mock_statsbomb_svc

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ===========================================================================
# GET /api/v1/statsbomb/competitions
# ===========================================================================

class TestStatsBombCompetitions:
    def test_returns_200(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.return_value = COMPETITIONS_RAW
        response = client.get("/api/v1/statsbomb/competitions")
        assert response.status_code == 200

    def test_returns_list(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.return_value = COMPETITIONS_RAW
        data = client.get("/api/v1/statsbomb/competitions").json()
        assert isinstance(data, list)
        assert len(data) == 3

    def test_response_fields(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.return_value = COMPETITIONS_RAW[:1]
        data = client.get("/api/v1/statsbomb/competitions").json()
        item = data[0]
        assert "competition_id" in item
        assert "competition_name" in item
        assert "season_id" in item
        assert "season_name" in item

    def test_skips_rows_with_missing_ids(self, client, mock_statsbomb_svc):
        raw = [
            {"competition_id": None, "season_id": 1, "competition_name": "Bad"},
            {"competition_id": 55, "season_id": None, "competition_name": "Also bad"},
            {"competition_id": 55, "season_id": 282, "competition_name": "UEFA Euro", "season_name": "2024"},
        ]
        mock_statsbomb_svc.list_competitions.return_value = raw
        data = client.get("/api/v1/statsbomb/competitions").json()
        assert len(data) == 1
        assert data[0]["competition_id"] == 55

    def test_sorted_by_competition_then_season(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.return_value = COMPETITIONS_RAW
        data = client.get("/api/v1/statsbomb/competitions").json()
        names = [d["competition_name"] for d in data]
        assert names == sorted(names, key=str.lower)

    def test_empty_list_when_no_competitions(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.return_value = []
        data = client.get("/api/v1/statsbomb/competitions").json()
        assert data == []

    def test_service_error_returns_500(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_competitions.side_effect = Exception("Network error")
        response = client.get("/api/v1/statsbomb/competitions")
        assert response.status_code == 500


# ===========================================================================
# GET /api/v1/statsbomb/matches
# ===========================================================================

class TestStatsBombMatches:
    def test_returns_200(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.return_value = MATCHES_RAW
        response = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282")
        assert response.status_code == 200

    def test_competition_id_required(self, client):
        response = client.get("/api/v1/statsbomb/matches?season_id=282")
        assert response.status_code == 422

    def test_season_id_required(self, client):
        response = client.get("/api/v1/statsbomb/matches?competition_id=55")
        assert response.status_code == 422

    def test_returns_match_list(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.return_value = MATCHES_RAW
        data = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282").json()
        assert len(data) == 2

    def test_match_id_in_response(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.return_value = MATCHES_RAW
        data = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282").json()
        ids = {m["match_id"] for m in data}
        assert 3943043 in ids
        assert 3943044 in ids

    def test_skips_rows_without_match_id(self, client, mock_statsbomb_svc):
        raw = [{"match_id": None}, {"match_id": 3943043, "match_date": "2024-07-14"}]
        mock_statsbomb_svc.list_matches.return_value = raw
        data = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282").json()
        assert len(data) == 1
        assert data[0]["match_id"] == 3943043

    def test_passes_params_to_service(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.return_value = []
        client.get("/api/v1/statsbomb/matches?competition_id=11&season_id=90")
        mock_statsbomb_svc.list_matches.assert_called_once_with(competition_id=11, season_id=90)

    def test_empty_result_for_unknown_competition(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.return_value = []
        data = client.get("/api/v1/statsbomb/matches?competition_id=999&season_id=999").json()
        assert data == []

    def test_service_error_returns_500(self, client, mock_statsbomb_svc):
        mock_statsbomb_svc.list_matches.side_effect = Exception("Network failure")
        response = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282")
        assert response.status_code == 500


# ===========================================================================
# TDD RED: StatsBombService injected via dependency_overrides (not _service patch)
# These tests FAIL until statsbomb.py uses Depends(get_statsbomb_service)
# ===========================================================================

class TestStatsBombDependencyInjection:
    @pytest.fixture
    def client_with_override(self):
        from app.main import app
        from app.core.dependencies import (
            get_match_repository, get_event_repository,
            get_statsbomb_service,
        )
        from app.adapters.openai_client import get_openai_adapter

        mock_svc = MagicMock()
        mock_svc.list_competitions.return_value = COMPETITIONS_RAW
        mock_svc.list_matches.return_value = MATCHES_RAW

        app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
        app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
        app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
        app.dependency_overrides[get_statsbomb_service] = lambda: mock_svc

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_svc

        app.dependency_overrides.clear()

    def test_competitions_via_dependency_override_returns_200(self, client_with_override):
        client, _ = client_with_override
        response = client.get("/api/v1/statsbomb/competitions")
        assert response.status_code == 200

    def test_competitions_via_dependency_override_calls_service(self, client_with_override):
        client, mock_svc = client_with_override
        client.get("/api/v1/statsbomb/competitions")
        mock_svc.list_competitions.assert_called_once()

    def test_matches_via_dependency_override_returns_200(self, client_with_override):
        client, _ = client_with_override
        response = client.get("/api/v1/statsbomb/matches?competition_id=55&season_id=282")
        assert response.status_code == 200
