"""
API tests for ingestion endpoints.

Tests all POST/GET/DELETE /api/v1/ingestion/* endpoints
with a mocked IngestionService.
"""

from unittest.mock import MagicMock, patch

import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    make_mock_match_repo,
    make_mock_event_repo,
    make_mock_openai_adapter,
)


@pytest.fixture
def mock_ingestion_svc():
    from app.services.ingestion_service import IngestionService

    svc = MagicMock(spec=IngestionService)
    svc.clear_downloaded_files.return_value = {
        "deleted_count": 0,
        "deleted_files": [],
        "deleted_dirs": [],
        "filters": {},
    }
    return svc


@pytest.fixture
def client(mock_ingestion_svc):
    from app.main import app
    from app.core.dependencies import (
        get_match_repository,
        get_event_repository,
        get_ingestion_service,
    )
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": (
        make_mock_match_repo()
    )
    app.dependency_overrides[get_event_repository] = lambda source="postgres": (
        make_mock_event_repo()
    )
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()
    app.dependency_overrides[get_ingestion_service] = lambda: mock_ingestion_svc

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ---------------------------------------------------------------------------
# POST /ingestion/download
# ---------------------------------------------------------------------------


class TestStartDownloadJob:
    def test_returns_202_with_match_ids(self, client):
        response = client.post(
            "/api/v1/ingestion/download",
            json={"match_ids": [3943043], "datasets": ["matches", "events"]},
        )
        assert response.status_code == 202

    def test_returns_202_with_competition_and_season(self, client):
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
    def test_returns_200_delete_all(self, client, mock_ingestion_svc):
        mock_ingestion_svc.clear_downloaded_files.return_value = {
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

    def test_returns_deleted_count(self, client, mock_ingestion_svc):
        mock_ingestion_svc.clear_downloaded_files.return_value = {
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

    def test_returns_500_on_service_error(self, client, mock_ingestion_svc):
        mock_ingestion_svc.clear_downloaded_files.side_effect = Exception("disk error")
        response = client.post(
            "/api/v1/ingestion/download/cleanup",
            json={"delete_all": True},
        )
        assert response.status_code == 500


# ---------------------------------------------------------------------------
# POST /ingestion/load
# ---------------------------------------------------------------------------


class TestStartLoadJob:
    def test_start_load_valid_request_returns_202(self, client):
        response = client.post(
            "/api/v1/ingestion/load",
            json={"source": "postgres", "datasets": ["matches", "events"]},
        )
        assert response.status_code == 202

    def test_sqlserver_source_accepted(self, client):
        response = client.post(
            "/api/v1/ingestion/load",
            json={"source": "sqlserver", "datasets": ["matches"]},
        )
        assert response.status_code == 202

    def test_response_type_is_load(self, client):
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
    def test_start_aggregate_valid_request_returns_202(self, client):
        response = client.post(
            "/api/v1/ingestion/aggregate",
            json={"source": "postgres"},
        )
        assert response.status_code == 202

    def test_response_type_is_aggregate(self, client):
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
    def test_start_rebuild_valid_request_returns_202(self, client):
        response = client.post(
            "/api/v1/ingestion/embeddings/rebuild",
            json={"source": "postgres"},
        )
        assert response.status_code == 202

    def test_response_type_is_embeddings_rebuild(self, client):
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
    def test_list_jobs_default_returns_200(self, client):
        response = client.get("/api/v1/ingestion/jobs")
        assert response.status_code == 200

    def test_list_jobs_default_response_has_items(self, client):
        data = client.get("/api/v1/ingestion/jobs").json()
        assert "items" in data

    def test_limit_param_accepted(self, client):
        response = client.get("/api/v1/ingestion/jobs?limit=10")
        assert response.status_code == 200


# ---------------------------------------------------------------------------
# DELETE /ingestion/jobs
# ---------------------------------------------------------------------------


class TestClearJobs:
    def test_clear_jobs_default_returns_200(self, client):
        response = client.delete("/api/v1/ingestion/jobs")
        assert response.status_code == 200

    def test_clear_jobs_response_has_removed_jobs(self, client):
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
        create_resp = client.post(
            "/api/v1/ingestion/load",
            json={"source": "postgres"},
        )
        job_id = create_resp.json()["job_id"]
        resp = client.get(f"/api/v1/ingestion/jobs/{job_id}")
        assert resp.status_code == 200
        assert resp.json()["id"] == job_id


# ---------------------------------------------------------------------------
# TDD RED: IngestionService injected via dependency_overrides (not _service patch)
# These tests FAIL until ingestion.py uses Depends(get_ingestion_service)
# ---------------------------------------------------------------------------


class TestIngestionDependencyInjection:
    @pytest.fixture
    def client_with_override(self):
        from app.main import app
        from app.core.dependencies import (
            get_match_repository,
            get_event_repository,
            get_ingestion_service,
        )
        from app.adapters.openai_client import get_openai_adapter
        from app.services.ingestion_service import IngestionService

        mock_svc = MagicMock(spec=IngestionService)
        mock_svc.run_download_job = MagicMock()

        app.dependency_overrides[get_match_repository] = lambda source="postgres": (
            make_mock_match_repo()
        )
        app.dependency_overrides[get_event_repository] = lambda source="postgres": (
            make_mock_event_repo()
        )
        app.dependency_overrides[get_openai_adapter] = lambda: (
            make_mock_openai_adapter()
        )
        app.dependency_overrides[get_ingestion_service] = lambda: mock_svc

        with TestClient(app, raise_server_exceptions=False) as c:
            yield c, mock_svc

        app.dependency_overrides.clear()

    def test_download_via_dependency_override_returns_202(self, client_with_override):
        client, _ = client_with_override
        response = client.post(
            "/api/v1/ingestion/download",
            json={"match_ids": [3943043], "datasets": ["matches"]},
        )
        assert response.status_code == 202

    def test_download_via_dependency_override_calls_service(self, client_with_override):
        client, mock_svc = client_with_override
        client.post(
            "/api/v1/ingestion/download",
            json={"match_ids": [3943043], "datasets": ["matches"]},
        )
        mock_svc.run_download_job.assert_called_once()


# ---------------------------------------------------------------------------
# POST /ingestion/summaries/generate
# ---------------------------------------------------------------------------


class TestStartGenerateSummariesJob:
    def test_returns_202_with_valid_payload(self, client):
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        assert response.status_code == 202

    def test_response_has_job_id_and_type(self, client):
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        data = response.json()
        assert "job_id" in data
        assert data["type"] == "summaries_generate"

    def test_accepts_unknown_source_passthrough(self, client):
        """``normalize_source`` passes unknown values through unchanged
        (see app/core/capabilities.py). Source validation happens later in
        the service layer when it tries to open a connection. This matches
        the behavior of /ingestion/load, /aggregate, /embeddings/rebuild."""
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "mongo", "match_ids": [3943043]},
        )
        assert response.status_code == 202

    def test_accepts_sqlserver_source(self, client):
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "sqlserver", "match_ids": [3943043]},
        )
        assert response.status_code == 202

    def test_accepts_language_override(self, client):
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={
                "source": "postgres",
                "match_ids": [3943043],
                "language": "spanish",
            },
        )
        assert response.status_code == 202

    def test_empty_match_ids_allowed_as_bulk_mode(self, client):
        """Empty match_ids means 'all matches with NULL summary'."""
        response = client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "postgres", "match_ids": []},
        )
        assert response.status_code == 202

    def test_calls_service_run_generate_summaries_job(self, mock_ingestion_svc, client):
        mock_ingestion_svc.run_generate_summaries_job = MagicMock()
        client.post(
            "/api/v1/ingestion/summaries/generate",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        mock_ingestion_svc.run_generate_summaries_job.assert_called_once()


# ---------------------------------------------------------------------------
# POST /ingestion/full-pipeline
# ---------------------------------------------------------------------------


class TestStartFullPipelineJob:
    def test_returns_202_with_match_ids(self, client):
        response = client.post(
            "/api/v1/ingestion/full-pipeline",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        assert response.status_code == 202

    def test_returns_202_with_competition_and_season(self, client):
        response = client.post(
            "/api/v1/ingestion/full-pipeline",
            json={
                "source": "postgres",
                "competition_id": 55,
                "season_id": 282,
            },
        )
        assert response.status_code == 202

    def test_returns_400_when_no_ids_or_competition(self, client):
        response = client.post(
            "/api/v1/ingestion/full-pipeline",
            json={"source": "postgres"},
        )
        assert response.status_code == 400

    def test_response_has_job_id_and_type(self, client):
        response = client.post(
            "/api/v1/ingestion/full-pipeline",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        data = response.json()
        assert "job_id" in data
        assert data["type"] == "full_pipeline"

    def test_calls_service_run_full_pipeline_job(self, mock_ingestion_svc, client):
        mock_ingestion_svc.run_full_pipeline_job = MagicMock()
        client.post(
            "/api/v1/ingestion/full-pipeline",
            json={"source": "postgres", "match_ids": [3943043]},
        )
        mock_ingestion_svc.run_full_pipeline_job.assert_called_once()

    def test_accepts_embedding_models_override(self, client):
        response = client.post(
            "/api/v1/ingestion/full-pipeline",
            json={
                "source": "postgres",
                "match_ids": [3943043],
                "embedding_models": ["text-embedding-3-small"],
            },
        )
        assert response.status_code == 202
