---
description: "Use when writing, reviewing, or generating tests. Covers TDD workflow, pytest patterns, mocking Azure OpenAI and DB connections, and coverage requirements for RAG-Challenge backend."
applyTo: "backend/tests/**/*.py"
---

# TDD — Test-Driven Development

## Core Rule

**Write the test first, then the implementation.** No PR merges a new function or endpoint without a corresponding test.

## Three-Level Test Strategy

```
backend/tests/
  conftest.py              # Shared fixtures — TestClient + DI overrides + entity factories
  unit/                    # UNIT tests (fast, zero external deps)
    test_domain.py
    test_*_service.py
    test_openai_adapter.py
  api/                     # API tests (TestClient, mocked services via DI override)
    test_chat.py
    test_matches.py
    test_events.py
    ...
  integration/             # INTEGRATION tests (real DB, skipped by default)
    test_db_connections.py
```

| Level | Speed | Deps | Run in CI | Marker |
|-------|-------|------|-----------|--------|
| **Unit** | < 1s | None (all mocked) | ✅ Always | `@pytest.mark.unit` |
| **API** | < 1s | TestClient + mocked services | ✅ Always | `@pytest.mark.api` |
| **Integration** | seconds | Live DB | ❌ Optional | `@pytest.mark.integration` |

## Running Tests

```bash
# From backend/ directory
cd backend

# All tests (unit + api), verbose
pytest tests/ -v

# With coverage on backend/app
pytest tests/ --cov=app --cov-report=term-missing

# Unit only
pytest tests/ -v -m unit

# API only
pytest tests/ -v -m api

# Integration (needs .env with real DB)
pytest tests/ -v -m integration

# Fast: stop on first failure
pytest tests/ -x
```

Coverage target: **80% minimum** on `backend/app/`.

## TDD Cycle (Red → Green → Refactor)

1. **Red** — write a failing test that describes the expected behavior
2. **Green** — write the minimum code to make it pass
3. **Refactor** — clean up without breaking the test

## conftest.py — FastAPI TestClient with DI overrides

The root `backend/tests/conftest.py` provides a `TestClient` with all dependencies overridden via `app.dependency_overrides`.

```python
from fastapi.testclient import TestClient
from app.main import app
from app.core.dependencies import get_match_repository, get_search_service

@pytest.fixture
def mock_match_repo():
    repo = MagicMock(spec=MatchRepository)
    repo.get_all.return_value = [make_match()]
    return repo

@pytest.fixture
def client(mock_match_repo):
    app.dependency_overrides[get_match_repository] = lambda: mock_match_repo
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
```

## Mocking Rules

Always mock external dependencies. Never hit real Azure OpenAI or DB in unit/api tests.

### API tests — use dependency_overrides

```python
def test_list_matches_returns_200(client, mock_match_repo):
    mock_match_repo.get_all.return_value = [make_match(match_id=1)]
    response = client.get("/api/v1/matches")
    assert response.status_code == 200
    assert len(response.json()) == 1
```

### Unit tests — mock at call boundary

```python
def test_search_service_calls_repo(mock_match_repo):
    service = SearchService(repo=mock_match_repo)
    mock_match_repo.search_by_embedding.return_value = [make_search_result()]
    results = service.search(query="goal by Morata", match_id=3943043)
    mock_match_repo.search_by_embedding.assert_called_once()
    assert len(results) == 1
```

### Mock Azure OpenAI adapter

```python
@pytest.fixture
def mock_openai_adapter():
    adapter = MagicMock(spec=OpenAIAdapter)
    adapter.get_embedding.return_value = [0.1] * 1536
    adapter.get_chat_completion.return_value = "Spain won 2-1"
    return adapter
```

## Test Naming Conventions

```python
# Pattern: test_<unit>_<scenario>_<expected_outcome>
def test_list_matches_empty_db_returns_empty_list():
def test_search_service_over_token_budget_returns_sentinel():
def test_postgres_repo_connection_failure_raises_database_error():
def test_chat_endpoint_missing_question_returns_422():
```

## What to Test per Layer

| Layer | Key test scenarios |
|-------|-------------------|
| `api/v1/` | HTTP status codes, request validation (422), response schema |
| `services/` | business logic, edge cases, error propagation |
| `repositories/` | parameterized queries, error mapping (integration only) |
| `adapters/` | SDK call shape, response parsing, retry/error handling |
| `domain/` | entity validation, exception messages |

## Pytest Markers (defined in `backend/pytest.ini`)

- `@pytest.mark.unit` — pure unit; no external deps
- `@pytest.mark.api` — API endpoint tests with TestClient; mocked dependencies
- `@pytest.mark.integration` — requires live DB

### Mock Environment Variables

```python
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    monkeypatch.setenv("DB_SERVER_AZURE_POSTGRES", "localhost")
    monkeypatch.setenv("DB_NAME_AZURE_POSTGRES", "test_db")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key-000")
```

## Test Naming Conventions

```python
# Pattern: test_<function>_<scenario>_<expected_outcome>
def test_decode_source_postgres_returns_azure_postgres():
def test_decode_source_invalid_raises_value_error():
def test_get_connection_azure_sql_calls_pyodbc():
def test_search_embeddings_returns_top_k_results():
```

## What to Test per Module

| Module | Key test scenarios |
|--------|-------------------|
| `module_data.py` | `decode_source()` normalization, connection routing per source, SQL query execution |
| `module_azure_openai.py` | Embedding generation, chat completion parsing, token counting |
| `module_utils.py` | Batch processing logic, data transformation, file I/O |
| `module_github.py` | URL construction, JSON parsing, error handling on 404 |
| `module_streamlit_frontend.py` | Data formatting functions (avoid testing Streamlit UI calls directly) |

## Integration Tests

Integration tests that require real DB/API connections:
- Live in `tests/integration/`
- Skipped by default: `@pytest.mark.skipif(not os.getenv("INTEGRATION_TESTS"), reason="requires live DB")`
- Never run in CI unless explicitly enabled

## conftest.py Template

```python
import pytest
import os

@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Inject safe env vars for all unit tests."""
    monkeypatch.setenv("DB_SERVER_AZURE_POSTGRES", "localhost")
    monkeypatch.setenv("DB_NAME_AZURE_POSTGRES", "ragtest")
    monkeypatch.setenv("DB_USER_AZURE_POSTGRES", "testuser")
    monkeypatch.setenv("DB_PASSWORD_AZURE_POSTGRES", "testpass")
    monkeypatch.setenv("DB_SERVER_AZURE", "localhost")
    monkeypatch.setenv("DB_NAME_AZURE", "ragtest")
    monkeypatch.setenv("DB_USER_AZURE", "testuser")
    monkeypatch.setenv("DB_PASSWORD_AZURE", "testpass")
    monkeypatch.setenv("AZURE_OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("AZURE_OPENAI_KEY", "test-key-000")
    monkeypatch.setenv("AZURE_OPENAI_DEPLOYMENT", "gpt-4o")
    monkeypatch.setenv("AZURE_OPENAI_EMBEDDINGS_DEPLOYMENT", "text-embedding-3-small")
```
