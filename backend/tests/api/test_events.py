"""
API tests for event endpoints.

GET /api/v1/events
GET /api/v1/events/{event_id}
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    make_event,
    make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter,
)


@pytest.fixture
def mock_event_repo():
    return make_mock_event_repo()


@pytest.fixture
def client(mock_event_repo):
    from app.main import app
    from app.core.dependencies import get_match_repository, get_event_repository
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
    app.dependency_overrides[get_event_repository] = lambda source="postgres": mock_event_repo
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ===========================================================================
# GET /api/v1/events
# ===========================================================================

class TestListEvents:
    def test_returns_200(self, client):
        response = client.get("/api/v1/events?match_id=3943043")
        assert response.status_code == 200

    def test_match_id_required(self, client):
        response = client.get("/api/v1/events")
        assert response.status_code == 422

    def test_returns_list_of_events(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.return_value = [
            make_event(1), make_event(2), make_event(3)
        ]
        data = client.get("/api/v1/events?match_id=3943043").json()
        assert len(data) == 3

    def test_event_fields_present(self, client):
        data = client.get("/api/v1/events?match_id=3943043").json()
        assert len(data) > 0
        e = data[0]
        for field in ["id", "match_id", "period", "minute", "quarter_minute",
                      "count", "time_description"]:
            assert field in e, f"Missing field: {field}"

    def test_time_description_format(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.return_value = [
            make_event(1, period=2, minute=60, quarter_minute=3)
        ]
        data = client.get("/api/v1/events?match_id=1").json()
        desc = data[0]["time_description"]
        assert "Period 2" in desc
        assert "Minute 60" in desc

    def test_match_id_passed_to_repo(self, client, mock_event_repo):
        client.get("/api/v1/events?match_id=9999")
        call_kwargs = mock_event_repo.get_events_by_match.call_args[1]
        assert call_kwargs["match_id"] == 9999

    def test_limit_passed_to_repo(self, client, mock_event_repo):
        client.get("/api/v1/events?match_id=1&limit=25")
        call_kwargs = mock_event_repo.get_events_by_match.call_args[1]
        assert call_kwargs["limit"] == 25

    def test_limit_too_high_rejected(self, client):
        response = client.get("/api/v1/events?match_id=1&limit=9999")
        assert response.status_code == 422

    def test_optional_summary_included(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.return_value = [
            make_event(summary="Spain attacks on the left wing")
        ]
        data = client.get("/api/v1/events?match_id=1").json()
        assert data[0]["summary"] == "Spain attacks on the left wing"

    def test_null_summary_when_absent(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.return_value = [make_event(summary=None)]
        data = client.get("/api/v1/events?match_id=1").json()
        assert data[0]["summary"] is None

    def test_empty_result(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.return_value = []
        data = client.get("/api/v1/events?match_id=1").json()
        assert data == []

    def test_db_error_returns_500(self, client, mock_event_repo):
        mock_event_repo.get_events_by_match.side_effect = Exception("DB error")
        response = client.get("/api/v1/events?match_id=1")
        assert response.status_code == 500


# ===========================================================================
# GET /api/v1/events/{event_id}
# ===========================================================================

class TestGetEvent:
    def test_returns_200_for_existing_event(self, client):
        response = client.get("/api/v1/events/1")
        assert response.status_code == 200

    def test_returns_event_fields(self, client, mock_event_repo):
        mock_event_repo.get_event_by_id.return_value = make_event(
            event_id=42, match_id=3943043, period=1, minute=30
        )
        data = client.get("/api/v1/events/42").json()
        assert data["id"] == 42
        assert data["match_id"] == 3943043
        assert data["period"] == 1
        assert data["minute"] == 30

    def test_returns_404_for_missing_event(self, client, mock_event_repo):
        mock_event_repo.get_event_by_id.return_value = None
        response = client.get("/api/v1/events/99999")
        assert response.status_code == 404

    def test_db_error_returns_500(self, client, mock_event_repo):
        mock_event_repo.get_event_by_id.side_effect = Exception("DB error")
        response = client.get("/api/v1/events/1")
        assert response.status_code == 500
