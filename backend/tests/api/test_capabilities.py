"""
API tests for capabilities and source status endpoints.

GET /api/v1/capabilities
GET /api/v1/sources/status
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


# ===========================================================================
# GET /api/v1/capabilities
# ===========================================================================

class TestCapabilitiesEndpoint:
    def test_capabilities_get_default_returns_200(self, client):
        assert client.get("/api/v1/capabilities").status_code == 200

    def test_response_has_capabilities_key(self, client):
        data = client.get("/api/v1/capabilities").json()
        assert "capabilities" in data

    def test_postgres_capabilities_present(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]
        assert "postgres" in caps

    def test_sqlserver_capabilities_present(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]
        assert "sqlserver" in caps

    def test_postgres_embedding_models_only_t3_small(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["postgres"]
        models = caps["embedding_models"]
        assert models == ["text-embedding-3-small"]

    def test_sqlserver_embedding_models_only_t3_small(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["sqlserver"]
        assert caps["embedding_models"] == ["text-embedding-3-small"]

    def test_postgres_all_four_algorithms(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["postgres"]
        algos = caps["search_algorithms"]
        for algo in ["cosine", "inner_product", "l2_euclidean", "l1_manhattan"]:
            assert algo in algos

    def test_sqlserver_missing_l1_manhattan(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["sqlserver"]
        assert "l1_manhattan" not in caps["search_algorithms"]

    def test_each_source_has_source_field(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]
        for src, data in caps.items():
            assert data["source"] == src


# ===========================================================================
# GET /api/v1/sources/status
# ===========================================================================

class TestSourcesStatusEndpoint:
    def test_sources_status_uses_injected_repos(self, client):
        """Verify sources/status endpoint uses DI-injected repos (not direct instantiation)."""
        response = client.get("/api/v1/sources/status")
        assert response.status_code == 200
        # The injected mocks should have been called
        client._mock_pg_repo.test_connection.assert_called_once()
        client._mock_sql_repo.test_connection.assert_called_once()

    def test_sources_status_both_up_returns_200(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = True
        assert client.get("/api/v1/sources/status").status_code == 200

    def test_returns_both_sources_by_default(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = True
        data = client.get("/api/v1/sources/status").json()

        sources = {s["source"] for s in data["sources"]}
        assert "postgres" in sources
        assert "sqlserver" in sources

    def test_connected_true_when_db_up(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = True
        data = client.get("/api/v1/sources/status").json()

        pg_status = next(s for s in data["sources"] if s["source"] == "postgres")
        assert pg_status["connected"] is True

    def test_connected_false_when_db_down(self, client):
        client._mock_pg_repo.test_connection.return_value = False
        client._mock_sql_repo.test_connection.return_value = False
        data = client.get("/api/v1/sources/status").json()

        for item in data["sources"]:
            assert item["connected"] is False

    def test_filter_by_postgres(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        data = client.get("/api/v1/sources/status?source=postgres").json()

        assert len(data["sources"]) == 1
        assert data["sources"][0]["source"] == "postgres"

    def test_filter_by_sqlserver(self, client):
        client._mock_sql_repo.test_connection.return_value = True
        data = client.get("/api/v1/sources/status?source=sqlserver").json()

        assert len(data["sources"]) == 1
        assert data["sources"][0]["source"] == "sqlserver"

    def test_invalid_source_raises_error(self, client):
        response = client.get("/api/v1/sources/status?source=mongodb")
        assert response.status_code in (400, 500)

    def test_response_has_timestamp(self, client):
        client._mock_pg_repo.test_connection.return_value = True
        client._mock_sql_repo.test_connection.return_value = True
        data = client.get("/api/v1/sources/status").json()

        assert "timestamp" in data


class TestNoDirectRepoImportsInCapabilities:
    def test_no_direct_repo_imports_in_capabilities_handler(self):
        """Verify capabilities.py does not import concrete repository classes."""
        import app.api.v1.capabilities as caps_module
        source = inspect.getsource(caps_module)
        tree = ast.parse(source)
        concrete_repos = {"PostgresEventRepository", "SQLServerEventRepository"}
        for node in ast.walk(tree):
            if isinstance(node, ast.ImportFrom):
                for alias in node.names:
                    assert alias.name not in concrete_repos, (
                        f"capabilities.py must not import {alias.name} directly"
                    )
