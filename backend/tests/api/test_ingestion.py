"""
API tests for ingestion endpoints.

Tests all POST/GET/DELETE /api/v1/ingestion/* endpoints
with a mocked IngestionService.
"""

from unittest.mock import MagicMock, patch

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
# POST /ingestion/download
# ---------------------------------------------------------------------------

class TestStartDownloadJob:
    def test_returns_202_with_match_ids(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_download_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/download",
                json={"match_ids": [3943043], "datasets": ["matches", "events"]},
            )
        assert response.status_code == 202

    def test_returns_202_with_competition_and_season(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_download_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/download",
                json={"competition_id": 55, "season_id": 282, "datasets": ["events"]},
            )
        assert response.status_code == 202

    def test_returns_400_when_no_ids_or_competition(self, client):
        response = client.post(
            "/api/v1/ingestion/download",
            json={"datasets": ["matches"]},
        )
        assert response.status_code == 400

    def test_response_has_job_id(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_download_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/download",
                json={"match_ids": [1], "datasets": ["matches"]},
            )
        data = response.json()
        assert "job_id" in data
        assert "status" in data
        assert "type" in data

    def test_invalid_dataset_rejected(self, client):
        response = client.post(
            "/api/v1/ingestion/download",
            json={"match_ids": [1], "datasets": ["invalid_dataset"]},
        )
        assert response.status_code == 422


# ---------------------------------------------------------------------------
# POST /ingestion/download/cleanup
# ---------------------------------------------------------------------------

class TestCleanupDownloadedFiles:
    def test_returns_200_delete_all(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.clear_downloaded_files.return_value = {
                "deleted_count": 5,
                "deleted_files": ["f1", "f2"],
                "deleted_dirs": ["d1"],
                "filters": {},
            }
            response = client.post(
                "/api/v1/ingestion/download/cleanup",
                json={"delete_all": True},
            )
        assert response.status_code == 200

    def test_returns_deleted_count(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.clear_downloaded_files.return_value = {
                "deleted_count": 3,
                "deleted_files": ["a", "b", "c"],
                "deleted_dirs": [],
                "filters": {"match_ids": [1]},
            }
            response = client.post(
                "/api/v1/ingestion/download/cleanup",
                json={"match_ids": [1]},
            )
        data = response.json()
        assert data["deleted_count"] == 3

    def test_returns_500_on_service_error(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.clear_downloaded_files.side_effect = Exception("disk error")
            response = client.post(
                "/api/v1/ingestion/download/cleanup",
                json={"delete_all": True},
            )
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /ingestion/load
# ---------------------------------------------------------------------------

class TestStartLoadJob:
    def test_returns_202(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_load_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/load",
                json={"source": "postgres", "datasets": ["matches", "events"]},
            )
        assert response.status_code == 202

    def test_sqlserver_source_accepted(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_load_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/load",
                json={"source": "sqlserver", "datasets": ["matches"]},
            )
        assert response.status_code == 202

    def test_response_type_is_load(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_load_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/load",
                json={"source": "postgres"},
            )
        data = response.json()
        assert data["type"] == "load"


# ---------------------------------------------------------------------------
# POST /ingestion/aggregate
# ---------------------------------------------------------------------------

class TestStartAggregateJob:
    def test_returns_202(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_aggregate_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/aggregate",
                json={"source": "postgres"},
            )
        assert response.status_code == 202

    def test_response_type_is_aggregate(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_aggregate_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/aggregate",
                json={"source": "postgres"},
            )
        data = response.json()
        assert data["type"] == "aggregate"


# ---------------------------------------------------------------------------
# POST /ingestion/embeddings/rebuild
# ---------------------------------------------------------------------------

class TestStartRebuildEmbeddingsJob:
    def test_returns_202(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_rebuild_embeddings_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/embeddings/rebuild",
                json={"source": "postgres"},
            )
        assert response.status_code == 202

    def test_response_type_is_embeddings_rebuild(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_rebuild_embeddings_job = MagicMock()
            response = client.post(
                "/api/v1/ingestion/embeddings/rebuild",
                json={"source": "postgres"},
            )
        data = response.json()
        assert data["type"] == "embeddings_rebuild"


# ---------------------------------------------------------------------------
# GET /ingestion/jobs
# ---------------------------------------------------------------------------

class TestListJobs:
    def test_returns_200(self, client):
        response = client.get("/api/v1/ingestion/jobs")
        assert response.status_code == 200

    def test_response_has_items(self, client):
        data = client.get("/api/v1/ingestion/jobs").json()
        assert "items" in data

    def test_limit_param_accepted(self, client):
        response = client.get("/api/v1/ingestion/jobs?limit=10")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /ingestion/jobs
# ---------------------------------------------------------------------------

class TestClearJobs:
    def test_returns_200(self, client):
        response = client.delete("/api/v1/ingestion/jobs")
        assert response.status_code == 200

    def test_response_has_removed_jobs(self, client):
        data = client.delete("/api/v1/ingestion/jobs").json()
        assert "removed_jobs" in data


# ---------------------------------------------------------------------------
# GET /ingestion/jobs/{job_id}
# ---------------------------------------------------------------------------

class TestGetJob:
    def test_returns_404_for_unknown_job(self, client):
        response = client.get("/api/v1/ingestion/jobs/nonexistent-job-id")
        assert response.status_code == 404

    def test_returns_job_after_creation(self, client):
        with patch("app.api.v1.ingestion._service") as mock_svc:
            mock_svc.run_load_job = MagicMock()
            create_resp = client.post(
                "/api/v1/ingestion/load",
                json={"source": "postgres"},
            )
        job_id = create_resp.json()["job_id"]
        resp = client.get(f"/api/v1/ingestion/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id
