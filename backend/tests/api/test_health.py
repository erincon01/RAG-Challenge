"""
API tests for health endpoints.

/api/v1/health, /api/v1/health/live, /api/v1/health/ready
"""

import ast
import inspect
from unittest.mock import MagicMock

import pytest
from fastapi.testclient import TestClient

from app.repositories.base import EventRepository
from tests.conftest import make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter


@pytest.fixture
def client():
    from app.main import app
    from app.core.dependencies import (
        get_match_repository,
        get_event_repository,
        get_postgres_event_repository,
        get_sqlserver_event_repository,
    )
    from app.adapters.openai_client import get_openai_adapter

    mock_pg_repo = MagicMock(spec=EventRepository)
    mock_pg_repo.test_connection.return_value = True
    mock_sql_repo = MagicMock(spec=EventRepository)
    mock_sql_repo.test_connection.return_value = True

    app.dependency_overrides[get_match_repository] = lambda source="postgres": make_mock_match_repo()
    app.dependency_overrides[get_event_repository] = lambda source="postgres": make_mock_event_repo()
    app.dependency_overrides[get_postgres_event_repository] = lambda: mock_pg_repo
    app.dependency_overrides[get_sqlserver_event_repository] = lambda: mock_sql_repo
    app.dependency_overrides[get_openai_adapter] = lambda: make_mock_openai_adapter()

    with TestClient(app, raise_server_exceptions=False) as c:
        c._mock_pg_repo = mock_pg_repo  # type: ignore[attr-defined]
        c._mock_sql_repo = mock_sql_repo  # type: ignore[attr-defined]
        yield c

    app.dependency_overrides.clear()


class TestLivenessEndpoint:
    def test_returns_200(self, client):
        response = client.get("/api/v1/health/live")
        assert response.status_code == 200

    def test_returns_alive_status(self, client):
        response = client.get("/api/v1/health/live")
        assert response.json()["status"] == "alive"


class TestHealthEndpoint:
    def test_returns_200(self, client):
        response = client.get("/api/v1/health")
        assert response.status_code == 200

    def test_returns_healthy_status(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert data["status"] == "healthy"

    def test_contains_required_fields(self, client):
        response = client.get("/api/v1/health")
        data = response.json()
        assert "status" in data
        assert "timestamp" in data
        assert "environment" in data
        assert "version" in data
        assert "checks" in data

    def test_checks_api_and_config_ok(self, client):
        response = client.get("/api/v1/health")
        checks = response.json()["checks"]
        assert checks["api"] == "ok"
        assert checks["config"] == "ok"


class TestReadinessEndpoint:
    def test_readiness_check_uses_injected_repos(self, client):
        """Verify readiness endpoint uses DI-injected repos (not direct instantiation)."""
        response = client.get("/api/v1/health/ready")
        assert response.status_code == 200
        # The injected mocks should have been called
        client._mock_pg_repo.test_connection.assert_called_once()
        client._mock_sql_repo.test_connection.assert_called_once()

    def test_both_dbs_up_returns_ready(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = True

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is True
        assert data["checks"]["postgres"] is True
        assert data["checks"]["sqlserver"] is True

    def test_postgres_down_returns_not_ready(self, client):
        client._mock_pg_repo.test_connection.return_value = False
        client._mock_sql_repo.test_connection.return_value = True

        response = client.get("/api/v1/health/ready")

        assert response.status_code == 200
        data = response.json()
        assert data["ready"] is False
        assert data["checks"]["postgres"] is False

    def test_sqlserver_down_returns_not_ready(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = False

        response = client.get("/api/v1/health/ready")

        data = response.json()
        assert data["ready"] is False
        assert data["checks"]["sqlserver"] is False

    def test_both_dbs_down_returns_not_ready(self, client):
        client._mock_pg_repo.test_connection.return_value = False
        client._mock_sql_repo.test_connection.return_value = False

        response = client.get("/api/v1/health/ready")

        data = response.json()
        assert data["ready"] is False


class TestNoDirectRepoImportsInHealth:
    def test_no_direct_repo_imports_in_health_handler(self):
        """Verify health.py does not import concrete repository classes."""
        import app.api.v1.health as health_module
        source = inspect.getsource(health_module)
        tree = ast.parse(source)
        concrete_repos = {"PostgresEventRepository", "SQLServerEventRepository"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name not in concrete_repos, (
                        f"health.py must not import {alias.name} directly"
                    )


class TestRootEndpoint:
    def test_root_returns_200(self, client):
        response = client.get("/")
        assert response.status_code == 200

    def test_root_contains_name(self, client):
        data = client.get("/").json()
        assert "RAG Challenge" in data.get("name", "")

    def test_root_contains_docs_path(self, client):
        data = client.get("/").json()
        assert data.get("docs") == "/docs"
