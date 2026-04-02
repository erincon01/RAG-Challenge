"""
API tests for chat/search endpoint.

POST /api/v1/chat/search
"""

import pytest
from fastapi.testclient import TestClient

from tests.conftest import (
    make_match, make_event, make_search_result, make_chat_response,
    make_mock_match_repo, make_mock_event_repo, make_mock_openai_adapter,
)

VALID_PAYLOAD = {
    "match_id": 3943043,
    "query": "Who scored the first goal?",
    "language": "english",
    "search_algorithm": "cosine",
    "embedding_model": "text-embedding-3-small",
    "top_n": 10,
    "temperature": 0.1,
    "include_match_info": True,
}


@pytest.fixture
def mock_match_repo():
    return make_mock_match_repo()


@pytest.fixture
def mock_event_repo():
    return make_mock_event_repo()


@pytest.fixture
def mock_openai_adapter():
    return make_mock_openai_adapter()


@pytest.fixture
def client(mock_match_repo, mock_event_repo, mock_openai_adapter):
    from app.main import app
    from app.core.dependencies import get_match_repository, get_event_repository
    from app.adapters.openai_client import get_openai_adapter

    app.dependency_overrides[get_match_repository] = lambda source="postgres": mock_match_repo
    app.dependency_overrides[get_event_repository] = lambda source="postgres": mock_event_repo
    app.dependency_overrides[get_openai_adapter] = lambda: mock_openai_adapter

    with TestClient(app, raise_server_exceptions=False) as c:
        yield c

    app.dependency_overrides.clear()


# ===========================================================================
# Happy path
# ===========================================================================

class TestChatSearchHappyPath:
    def test_returns_200(self, client):
        response = client.post("/api/v1/chat/search", json=VALID_PAYLOAD)
        assert response.status_code == 200

    def test_response_fields_present(self, client):
        data = client.post("/api/v1/chat/search", json=VALID_PAYLOAD).json()
        for field in ["question", "normalized_question", "answer",
                      "search_results", "metadata"]:
            assert field in data, f"Missing field: {field}"

    def test_question_preserved(self, client):
        data = client.post("/api/v1/chat/search", json=VALID_PAYLOAD).json()
        assert data["question"] == VALID_PAYLOAD["query"]

    def test_answer_from_mock(self, client, mock_openai_adapter):
        mock_openai_adapter.create_chat_completion.return_value = "Spain scored through Oyarzabal."
        data = client.post("/api/v1/chat/search", json=VALID_PAYLOAD).json()
        assert data["answer"] == "Spain scored through Oyarzabal."

    def test_search_results_structure(self, client, mock_event_repo):
        event = make_event(event_id=1, period=2, minute=86)
        mock_event_repo.search_by_embedding.return_value = [make_search_result(event, rank=1)]
        data = client.post("/api/v1/chat/search", json=VALID_PAYLOAD).json()
        assert len(data["search_results"]) == 1
        sr = data["search_results"][0]
        assert "event" in sr
        assert "similarity_score" in sr
        assert "rank" in sr
        assert sr["event"]["period"] == 2

    def test_match_info_included_when_requested(self, client):
        payload = {**VALID_PAYLOAD, "include_match_info": True}
        data = client.post("/api/v1/chat/search", json=payload).json()
        assert data["match_info"] is not None

    def test_match_info_absent_when_not_requested(self, client):
        payload = {**VALID_PAYLOAD, "include_match_info": False}
        data = client.post("/api/v1/chat/search", json=payload).json()
        assert data["match_info"] is None

    def test_metadata_contains_match_id(self, client):
        data = client.post("/api/v1/chat/search", json=VALID_PAYLOAD).json()
        assert data["metadata"]["match_id"] == VALID_PAYLOAD["match_id"]

    def test_source_sqlserver_accepted(self, client):
        response = client.post("/api/v1/chat/search?source=sqlserver", json=VALID_PAYLOAD)
        assert response.status_code == 200


# ===========================================================================
# Capability validation per source
# ===========================================================================

class TestCapabilityValidation:
    def test_postgres_supports_t3_large(self, client):
        payload = {**VALID_PAYLOAD, "embedding_model": "text-embedding-3-large",
                   "search_algorithm": "cosine"}
        response = client.post("/api/v1/chat/search?source=postgres", json=payload)
        assert response.status_code == 200

    def test_sqlserver_rejects_t3_large(self, client):
        payload = {**VALID_PAYLOAD, "embedding_model": "text-embedding-3-large"}
        response = client.post("/api/v1/chat/search?source=sqlserver", json=payload)
        assert response.status_code == 400

    def test_postgres_supports_l1_manhattan(self, client):
        payload = {**VALID_PAYLOAD, "search_algorithm": "l1_manhattan"}
        response = client.post("/api/v1/chat/search?source=postgres", json=payload)
        assert response.status_code == 200

    def test_sqlserver_rejects_l1_manhattan(self, client):
        payload = {**VALID_PAYLOAD, "search_algorithm": "l1_manhattan"}
        response = client.post("/api/v1/chat/search?source=sqlserver", json=payload)
        assert response.status_code == 400

    def test_all_postgres_algorithms_accepted(self, client):
        for algo in ["cosine", "inner_product", "l2_euclidean", "l1_manhattan"]:
            payload = {**VALID_PAYLOAD, "search_algorithm": algo}
            response = client.post("/api/v1/chat/search?source=postgres", json=payload)
            assert response.status_code == 200, f"Algorithm {algo} should be accepted"

    def test_all_sqlserver_algorithms_accepted(self, client):
        for algo in ["cosine", "inner_product", "l2_euclidean"]:
            payload = {**VALID_PAYLOAD, "search_algorithm": algo}
            response = client.post("/api/v1/chat/search?source=sqlserver", json=payload)
            assert response.status_code == 200, f"Algorithm {algo} should be accepted on sqlserver"


# ===========================================================================
# Request validation
# ===========================================================================

class TestRequestValidation:
    def test_missing_match_id_rejected(self, client):
        payload = {k: v for k, v in VALID_PAYLOAD.items() if k != "match_id"}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422

    def test_empty_query_rejected(self, client):
        payload = {**VALID_PAYLOAD, "query": ""}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422

    def test_invalid_algorithm_rejected(self, client):
        payload = {**VALID_PAYLOAD, "search_algorithm": "bm25"}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422

    def test_invalid_model_rejected(self, client):
        payload = {**VALID_PAYLOAD, "embedding_model": "gpt-4-embedding"}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422

    def test_top_n_too_high_rejected(self, client):
        payload = {**VALID_PAYLOAD, "top_n": 999}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422

    def test_top_n_zero_rejected(self, client):
        payload = {**VALID_PAYLOAD, "top_n": 0}
        response = client.post("/api/v1/chat/search", json=payload)
        assert response.status_code == 422


# ===========================================================================
# Error handling
# ===========================================================================

class TestErrorHandling:
    def test_search_service_error_returns_500(self, client, mock_event_repo):
        mock_event_repo.search_by_embedding.side_effect = Exception("DB crash")
        response = client.post("/api/v1/chat/search", json=VALID_PAYLOAD)
        assert response.status_code == 500

    def test_embedding_error_returns_500(self, client, mock_openai_adapter):
        from app.domain.exceptions import EmbeddingGenerationError
        mock_openai_adapter.create_embedding.side_effect = EmbeddingGenerationError("Rate limit")
        response = client.post("/api/v1/chat/search", json=VALID_PAYLOAD)
        assert response.status_code == 500
