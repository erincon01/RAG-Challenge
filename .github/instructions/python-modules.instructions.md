---
description: "Use when creating, editing, or reviewing Python modules in backend/app/. Covers FastAPI layer structure, repository pattern, service/domain conventions, dependency injection, and type hints."
applyTo: "backend/**/*.py"
---

# Python Module Conventions (FastAPI Architecture)

## Layer Structure

All backend code lives in `backend/app/` with strict layer separation. Each layer has one responsibility.

| Layer | Path | Responsibility |
|-------|------|----------------|
| **API** | `backend/app/api/v1/` | HTTP route handlers only; delegate all logic to services |
| **Services** | `backend/app/services/` | Business logic; stateless; no direct DB or HTTP calls |
| **Repositories** | `backend/app/repositories/` | DB access only; implements `BaseRepository` ABC |
| **Domain** | `backend/app/domain/` | Entities, exceptions, value objects (pure Python, no frameworks) |
| **Adapters** | `backend/app/adapters/` | External services (Azure OpenAI); wrap the SDK |
| **Core** | `backend/app/core/` | Config (`get_settings()`), dependency wiring, startup |

Rule: dependencies only flow **downward** — API → Service → Repository/Adapter. Never skip layers.

## Dependency Injection (mandatory)

All dependencies are injected via FastAPI `Depends()`. Never instantiate services or repositories inside route handlers.

```python
# CORRECT — inject via Depends
@router.get("/matches")
async def list_matches(
    service: MatchService = Depends(get_match_service),
    settings: Settings = Depends(get_settings),
) -> list[Match]:
    return await service.get_all()

# WRONG — never instantiate directly in handler
async def list_matches():
    repo = PostgresMatchRepository()  # ❌
```

## Repository Pattern (mandatory for DB access)

All DB access goes through a repository that implements `BaseRepository` from `backend/app/repositories/base.py`.

```python
# Define the interface in base.py
class MatchRepository(BaseRepository):
    @abstractmethod
    def get_by_id(self, match_id: int) -> Optional[Match]: ...

# Implement per DB engine
class PostgresMatchRepository(MatchRepository):
    @contextmanager
    def get_connection(self):
        conn = psycopg2.connect(...)
        try:
            yield conn
        finally:
            conn.close()

    def get_by_id(self, match_id: int) -> Optional[Match]:
        with self.get_connection() as conn:
            # parameterized query — always
            cursor.execute("SELECT ... WHERE match_id = %s", (match_id,))
```

Never write raw SQL in API handlers or services.

## Config and Secrets (mandatory)

All configuration is loaded via Pydantic Settings from `config/` module. Route handlers receive settings via `Depends(get_settings)`.

```python
# CORRECT — inject settings via Depends
@router.get("/search")
async def search(
    settings: Settings = Depends(get_settings),
):
    endpoint = settings.openai_endpoint  # always from Settings

# WRONG — never call os.getenv() directly in routes or services
endpoint = os.getenv("OPENAI_ENDPOINT")  # ❌
```

When adding new env vars: update `.env.example` AND `config/` Settings class.

## Domain Entities

- Define all data models as Pydantic `BaseModel` in `backend/app/domain/entities.py`
- Define custom exceptions in `backend/app/domain/exceptions.py`
- Domain objects are pure Python — no FastAPI, no DB drivers in this layer

```python
class Match(BaseModel):
    match_id: int
    competition: Competition
    home_team: Team
    away_team: Team
```

## Azure OpenAI Adapter

- The `AzureOpenAI` client is a module-level singleton in `backend/app/adapters/openai_client.py`
- Never instantiate `AzureOpenAI` inside a service method or per-request
- Services receive the adapter via dependency injection

## Error Handling

- Raise domain exceptions from `backend/app/domain/exceptions.py` (e.g., `DatabaseConnectionError`, `EntityNotFoundError`)
- API layer catches domain exceptions and maps to HTTP status codes
- Never catch broad `Exception` silently; always log with `logging.exception()`

```python
# Service raises domain exception
def get_by_id(self, match_id: int) -> Match:
    result = self.repo.get_by_id(match_id)
    if result is None:
        raise EntityNotFoundError(f"Match {match_id} not found")
    return result

# API handler maps to HTTP
@router.get("/matches/{match_id}")
async def get_match(match_id: int, service: MatchService = Depends(...)):
    try:
        return service.get_by_id(match_id)
    except EntityNotFoundError:
        raise HTTPException(status_code=404)
```

## Type Hints (required on all public functions)

```python
def search_by_embedding(
    self,
    search_request: SearchRequest,
    query_embedding: list[float],
) -> list[SearchResult]:
    ...
```

## Imports

- Standard library first, then third-party, then local (`app.*`)
- Avoid wildcard imports (`from module import *`)
- Import only what is used
