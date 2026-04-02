"""
API tests for capabilities and source status endpoints.

GET /api/v1/capabilities
GET /api/v1/sources/status
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


# ===========================================================================
# GET /api/v1/capabilities
# ===========================================================================

class TestCapabilitiesEndpoint:
    def test_returns_200(self, client):
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

    def test_postgres_embedding_models(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["postgres"]
        models = caps["embedding_models"]
        assert "text-embedding-ada-002" in models
        assert "text-embedding-3-small" in models
        assert "text-embedding-3-large" in models

    def test_sqlserver_missing_t3_large(self, client):
        caps = client.get("/api/v1/capabilities").json()["capabilities"]["sqlserver"]
        assert "text-embedding-3-large" not in caps["embedding_models"]

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
    def test_returns_200(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg, \
             patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            pg.return_value.test_connection.return_value = True
            sql.return_value.test_connection.return_value = True
            assert client.get("/api/v1/sources/status").status_code == 200

    def test_returns_both_sources_by_default(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg, \
             patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            pg.return_value.test_connection.return_value = True
            sql.return_value.test_connection.return_value = True
            data = client.get("/api/v1/sources/status").json()

        sources = {s["source"] for s in data["sources"]}
        assert "postgres" in sources
        assert "sqlserver" in sources

    def test_connected_true_when_db_up(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg, \
             patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            pg.return_value.test_connection.return_value = True
            sql.return_value.test_connection.return_value = True
            data = client.get("/api/v1/sources/status").json()

        pg_status = next(s for s in data["sources"] if s["source"] == "postgres")
        assert pg_status["connected"] is True

    def test_connected_false_when_db_down(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg, \
             patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            pg.return_value.test_connection.return_value = False
            sql.return_value.test_connection.return_value = False
            data = client.get("/api/v1/sources/status").json()

        for item in data["sources"]:
            assert item["connected"] is False

    def test_filter_by_postgres(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg:
            pg.return_value.test_connection.return_value = True
            data = client.get("/api/v1/sources/status?source=postgres").json()

        assert len(data["sources"]) == 1
        assert data["sources"][0]["source"] == "postgres"

    def test_filter_by_sqlserver(self, client):
        with patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            sql.return_value.test_connection.return_value = True
            data = client.get("/api/v1/sources/status?source=sqlserver").json()

        assert len(data["sources"]) == 1
        assert data["sources"][0]["source"] == "sqlserver"

    def test_invalid_source_raises_error(self, client):
        response = client.get("/api/v1/sources/status?source=mongodb")
        assert response.status_code in (400, 500)

    def test_response_has_timestamp(self, client):
        with patch("app.api.v1.capabilities.PostgresEventRepository") as pg, \
             patch("app.api.v1.capabilities.SQLServerEventRepository") as sql:
            pg.return_value.test_connection.return_value = True
            sql.return_value.test_connection.return_value = True
            data = client.get("/api/v1/sources/status").json()

        assert "timestamp" in data
