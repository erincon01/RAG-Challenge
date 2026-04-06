"""
API tests for match and competition endpoints.

GET /api/v1/competitions
GET /api/v1/matches
GET /api/v1/matches/{match_id}
"""

from unittest.mock import MagicMock
import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    make_match, make_competition,
    make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter,
)


@pytest.fixture
def mock_match_repo():
    return make_mock_match_repo()


@pytest.fixture
def client(mock_match_repo):
    from app.main import app
    from app.core.dependencies import get_match_repository, get_event_repository
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": mock_match_repo
    app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ===========================================================================
# GET /api/v1/competitions
# ===========================================================================

class TestListCompetitions:
    def test_list_competitions_default_returns_200(self, client):
        response = client.get("/api/v1/competitions")
        assert response.status_code == 200

    def test_list_competitions_default_returns_list(self, client):
        data = client.get("/api/v1/competitions").json()
        assert isinstance(data, list)

    def test_list_competitions_valid_data_contains_required_fields(self, client, mock_match_repo):
        mock_match_repo.get_competitions.return_value = [
            make_competition(1, "Europe", "UEFA Euro"),
            make_competition(11, "Spain", "La Liga"),
        ]
        data = client.get("/api/v1/competitions").json()
        assert len(data) == 2
        assert data[0]["competition_id"] == 1
        assert data[0]["name"] == "UEFA Euro"
        assert "country" in data[0]

    def test_empty_list_when_no_competitions(self, client, mock_match_repo):
        mock_match_repo.get_competitions.return_value = []
        data = client.get("/api/v1/competitions").json()
        assert data == []

    def test_db_error_returns_500(self, client, mock_match_repo):
        mock_match_repo.get_competitions.side_effect = Exception("DB timeout")
        response = client.get("/api/v1/competitions")
        assert response.status_code == 500


# ===========================================================================
# GET /api/v1/matches
# ===========================================================================

class TestListMatches:
    def test_list_matches_default_returns_200(self, client):
        response = client.get("/api/v1/matches")
        assert response.status_code == 200

    def test_returns_list_of_matches(self, client, mock_match_repo):
        mock_match_repo.get_all.return_value = [make_match(1), make_match(2)]
        data = client.get("/api/v1/matches").json()
        assert len(data) == 2

    def test_match_summary_fields(self, client):
        data = client.get("/api/v1/matches").json()
        assert len(data) > 0
        m = data[0]
        for field in ["match_id", "match_date", "home_team_name", "away_team_name",
                      "home_score", "away_score", "result", "display_name",
                      "competition_name", "season_name"]:
            assert field in m, f"Missing field: {field}"

    def test_display_name_format(self, client, mock_match_repo):
        mock_match_repo.get_all.return_value = [make_match(1, home_score=2, away_score=1)]
        data = client.get("/api/v1/matches").json()
        assert "Spain (2)" in data[0]["display_name"]
        assert "England (1)" in data[0]["display_name"]

    def test_filter_by_competition_name(self, client, mock_match_repo):
        client.get("/api/v1/matches?competition_name=UEFA+Euro")
        call_kwargs = mock_match_repo.get_all.call_args[1]
        assert call_kwargs["competition_name"] == "UEFA Euro"

    def test_filter_by_season_name(self, client, mock_match_repo):
        client.get("/api/v1/matches?season_name=2024")
        call_kwargs = mock_match_repo.get_all.call_args[1]
        assert call_kwargs["season_name"] == "2024"

    def test_limit_param_passed_to_repo(self, client, mock_match_repo):
        client.get("/api/v1/matches?limit=50")
        call_kwargs = mock_match_repo.get_all.call_args[1]
        assert call_kwargs["limit"] == 50

    def test_limit_too_high_rejected(self, client):
        response = client.get("/api/v1/matches?limit=9999")
        assert response.status_code == 422

    def test_limit_zero_rejected(self, client):
        response = client.get("/api/v1/matches?limit=0")
        assert response.status_code == 422

    def test_list_matches_no_matches_returns_empty_list(self, client, mock_match_repo):
        mock_match_repo.get_all.return_value = []
        data = client.get("/api/v1/matches").json()
        assert data == []

    def test_list_matches_db_error_returns_500(self, client, mock_match_repo):
        mock_match_repo.get_all.side_effect = Exception("Connection error")
        response = client.get("/api/v1/matches")
        assert response.status_code == 500

    def test_list_matches_sqlserver_source_accepted(self, client):
        response = client.get("/api/v1/matches?source=sqlserver")
        assert response.status_code == 200


# ===========================================================================
# GET /api/v1/matches/{match_id}
# ===========================================================================

class TestGetMatch:
    def test_returns_200_for_existing_match(self, client):
        response = client.get("/api/v1/matches/3943043")
        assert response.status_code == 200

    def test_returns_match_detail_fields(self, client):
        data = client.get("/api/v1/matches/3943043").json()
        for field in ["match_id", "match_date", "competition", "season_name",
                      "home_team", "away_team", "home_score", "away_score",
                      "result", "display_name"]:
            assert field in data, f"Missing field: {field}"

    def test_returns_nested_competition(self, client):
        data = client.get("/api/v1/matches/3943043").json()
        comp = data["competition"]
        assert "competition_id" in comp
        assert "name" in comp
        assert "country" in comp

    def test_returns_404_for_missing_match(self, client, mock_match_repo):
        mock_match_repo.get_by_id.return_value = None
        response = client.get("/api/v1/matches/99999")
        assert response.status_code == 404

    def test_returns_optional_stadium_name(self, client, mock_match_repo):
        mock_match_repo.get_by_id.return_value = make_match(include_stadium=True)
        data = client.get("/api/v1/matches/1").json()
        assert data["stadium_name"] == "Olympiastadion"

    def test_stadium_name_none_when_absent(self, client, mock_match_repo):
        mock_match_repo.get_by_id.return_value = make_match(include_stadium=False)
        data = client.get("/api/v1/matches/1").json()
        assert data["stadium_name"] is None

    def test_referee_name_present(self, client, mock_match_repo):
        mock_match_repo.get_by_id.return_value = make_match(include_referee=True)
        data = client.get("/api/v1/matches/1").json()
        assert data["referee_name"] == "Referee A"

    def test_db_error_returns_500(self, client, mock_match_repo):
        mock_match_repo.get_by_id.side_effect = Exception("DB failure")
        response = client.get("/api/v1/matches/1")
        assert response.status_code == 500
