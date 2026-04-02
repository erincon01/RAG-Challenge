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
    adapter.create_embedding.return_value = [0.1] * 1536
    adapter.create_chat_completion.return_value = "Spain won 2-1"
    return adapter
```

## TDD Workflow per Feature (step-by-step)

```
1. Understand the acceptance criteria for the feature
2. Write a failing API test (test_<feature>.py in api/)
3. Write a failing unit test for the service logic (test_<feature>_service.py in unit/)
4. Implement the domain entity / exception if new types are needed
5. Implement the service method
6. Implement the route handler in api/v1/
7. All tests green → check coverage (pytest --cov=app)
8. Refactor if needed, tests must stay green
9. Open PR — CI enforces coverage ≥ 80%
```

**Never skip step 2 and 3.** Implementation first = tech debt.

## Test Naming Conventions

```python
# Pattern: test_<unit>_<scenario>_<expected_outcome>
def test_list_matches_empty_db_returns_empty_list():
def test_search_service_over_token_budget_truncates_context():
def test_postgres_repo_connection_failure_raises_database_error():
def test_chat_endpoint_missing_question_returns_422():
def test_search_service_calls_openai_adapter_once_per_request():
```

## What to Test per Layer

| Layer | Key test scenarios |
|-------|-------------------|
| `api/v1/` | HTTP status codes, request validation (422), response schema shape |
| `services/` | Business logic, edge cases, exception propagation, token budget logic |
| `repositories/` | Parameterized queries, entity mapping, error conversion (integration only) |
| `adapters/` | SDK call shape, response parsing, retry/backoff on 429/500 |
| `domain/` | Entity validation (`__post_init__`), exception messages, enum values |

## Pytest Markers (defined in `backend/pytest.ini`)

- `@pytest.mark.unit` — pure unit; no external deps
- `@pytest.mark.api` — API endpoint tests with TestClient; mocked dependencies
- `@pytest.mark.integration` — requires live DB; NOT run in CI by default

## Mock Environment (if settings are loaded outside DI)

Settings are injected via `Depends(get_settings)` in most routes — override via `dependency_overrides`.
For code that loads settings at module level (e.g. adapters), use `monkeypatch`:

```python
@pytest.fixture(autouse=True)
def mock_env(monkeypatch):
    """Inject safe env vars — used when settings are loaded at import time."""
    monkeypatch.setenv("POSTGRES_HOST", "localhost")
    monkeypatch.setenv("POSTGRES_DB", "ragtest")
    monkeypatch.setenv("POSTGRES_USER", "testuser")
    monkeypatch.setenv("POSTGRES_PASSWORD", "testpass")
    monkeypatch.setenv("OPENAI_ENDPOINT", "https://test.openai.azure.com/")
    monkeypatch.setenv("OPENAI_KEY", "test-key-000")
    monkeypatch.setenv("OPENAI_MODEL", "gpt-4o")
```
