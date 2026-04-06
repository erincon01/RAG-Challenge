# Infrastructure Specification

**Domain:** infra  
**Status:** Current system (brownfield baseline)  
**Last updated:** 2026-04-02  
**ADR references:** [ADR-004 Local Docker Infrastructure](../../../docs/adr/ADR-004-local-docker-infrastructure.md)

---

## Overview

The project uses Docker Compose for local development with 4 services.
CI/CD is handled via GitHub Actions. Configuration follows Pydantic BaseSettings.

---

## Docker Compose Services

```
┌─────────────────────────────────────────────────────────────┐
│                      Host Machine                           │
│   ┌───────────────────┐    ┌──────────────────────────┐    │
│   │  frontend :5173   │───▶│    backend :8000          │    │
│   │  (React/Vite)     │    │    (FastAPI/uvicorn)      │    │
│   └───────────────────┘    └────────┬─────────┬───────┘    │
│            external network         │         │             │
│  ──────────────────────────────────┼─────────┼──────────── │
│            internal network         │         │             │
│                              ┌──────▼──┐  ┌──▼──────────┐  │
│                              │postgres │  │ sqlserver    │  │
│                              │  :5432  │  │   :1433     │  │
│                              └─────────┘  └─────────────┘  │
└─────────────────────────────────────────────────────────────┘
```

### Service Details

| Service | Image | Port | Memory Limit |
|---------|-------|------|-------------|
| **postgres** | `pgvector/pgvector:pg17` | 5432 | — |
| **sqlserver** | Custom (SQL Server Express 2025) | 1433 | — |
| **backend** | Custom (Python 3.11+ / FastAPI) | 8000 | 2 GB |
| **frontend** | Custom (Node.js / Vite) | 5173 | 256 MB |

### Networks

| Network | Purpose | Services |
|---------|---------|----------|
| `internal` | DB access (no external exposure) | backend, postgres, sqlserver |
| `external` | Frontend-backend communication | frontend, backend |

### Volumes

| Volume | Purpose |
|--------|---------|
| `postgres_data` | PostgreSQL data persistence |
| `sqlserver_data` | SQL Server data persistence |
| `frontend_node_modules` | Node modules cache |

### Health Checks

| Service | Method | Interval | Timeout |
|---------|--------|----------|---------|
| backend | HTTP GET `/api/v1/health/live` | 5s | 3s |
| postgres | pg_isready | (Docker default) | — |
| sqlserver | (custom script) | (Docker default) | — |

### Security

- `security_opt: no-new-privileges:true` on all services.
- Sensitive values from `.env` file (not committed).
- `.env` is in `.gitignore`.

---

## Configuration (`config/settings.py`)

### Structure

```
Settings (BaseSettings)
├── database: DatabaseConfig
│   ├── postgres_host, postgres_db, postgres_user, postgres_password
│   └── sqlserver_host, sqlserver_db, sqlserver_user, sqlserver_password
├── openai: OpenAIConfig
│   ├── openai_provider ("azure" | "openai", default "azure")
│   ├── openai_endpoint, openai_key
│   └── openai_model, openai_model2 (default "gpt-4")
├── repository: RepositoryConfig
│   ├── repo_owner (default "statsbomb")
│   ├── repo_name (default "open-data")
│   └── local_folder (default "./data")
├── cors_origins_str (str, alias CORS_ORIGINS, default "http://localhost:5173,http://localhost:8000")
│   └── cors_origins (property) → List[str] split on commas with whitespace trim
├── environment ("local" | "azure" | "test", default "local")
├── debug (bool, default False)
└── log_level (str, default "INFO")
```

### Rules

- All configuration MUST use Pydantic `BaseSettings` with environment variables.
- `os.getenv()` is PROHIBITED outside `settings.py`.
- Production startup MUST call `settings.validate_required()` to fail-fast on missing variables.
- Singleton access via `get_settings()` function.

---

## Dependency Injection (`core/dependencies.py`)

### Providers

| Provider | Returns | Used By |
|----------|---------|---------|
| `get_repository_factory(source)` | `PostgresRepositoryFactory` or `SQLServerRepositoryFactory` | Internal |
| `get_match_repository(source)` | `MatchRepository` implementation | Route handlers |
| `get_event_repository(source)` | `EventRepository` implementation | Route handlers |

### Type Aliases

```python
MatchRepo = Annotated[MatchRepository, Depends(get_match_repository)]
EventRepo = Annotated[EventRepository, Depends(get_event_repository)]
```

### Rules

- ALL dependencies MUST be injected via `FastAPI Depends()`.
- Providers live ONLY in `app/core/dependencies.py`.
- NEVER instantiate services or repos at module level.
- In tests, use `app.dependency_overrides[provider] = lambda: mock`.
- Always call `app.dependency_overrides.clear()` in teardown.

---

## CI/CD Workflows

### CI (`ci.yml`)

- **Trigger:** Push to `develop`, `main`, or any PR.
- **Jobs:**
  1. **Lint:** `ruff check .`
  2. **Type check:** `mypy`
  3. **Tests:** `pytest --cov --cov-fail-under=80`

### CD (`cd.yml`)

- **Trigger:** Push to `main` (after merge from develop).
- **Jobs:** Deployment workflow (details TBD).

---

## Testing Infrastructure

### Framework

- `pytest` + `pytest-cov` for coverage.
- Minimum coverage threshold: 80%.
- Test discovery: `backend/tests/`.

### Structure

```
backend/tests/
├── conftest.py          # Shared fixtures and factories
├── api/                 # API route integration tests
│   ├── test_capabilities.py
│   ├── test_chat.py
│   ├── test_events.py
│   ├── test_health.py
│   ├── test_matches.py
│   └── test_statsbomb.py
├── unit/                # Unit tests (services, repos, domain)
└── integration/         # Integration tests (DB, external APIs)
```

### Rules

- Test naming: `test_<method>_<scenario>_<expected>`.
- Use `MagicMock(spec=TargetClass)` — never bare `MagicMock()`.
- Use factories from `conftest.py` — never inline dicts.
- Always call `app.dependency_overrides.clear()` in teardown.
- Current test count: 416 tests, ~80% coverage.

---

## CORS Configuration

The system SHALL read allowed CORS origins from the `CORS_ORIGINS` environment variable.
The value MUST be a comma-separated list of origin URLs (e.g., `http://localhost:5173,http://localhost:8000`).
When `CORS_ORIGINS` is not set, the system SHALL default to `http://localhost:5173,http://localhost:8000`.
The system MUST NOT use `allow_origins=["*"]` in any environment.

---

## Known Deviations

- No `.env.example` file for frontend.
