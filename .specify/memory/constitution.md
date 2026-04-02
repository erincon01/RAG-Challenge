---
constitution_version: "2.0.0"
ratification_date: "2025-01-01"
last_amended_date: "2026-04-02"
amendment_procedure: "See Governance section below"
---

<!--
SYNC IMPACT REPORT
==================
Version change:     1.0.0 → 2.0.0

Bump type:          MAJOR — complete architectural replacement.
                    The Streamlit monolith (python_modules/module_*.py, sqlite-local, app.py shell)
                    has been fully superseded by a FastAPI layered backend + React TypeScript
                    frontend. All 8 v1 principles are retired; 10 new principles replace them.

Modified principles (old → new):
  I.   Multi-Source Data Portability  →  REPLACED BY I (Layered Architecture) + X (Docker Infrastructure)
  II.  Module Discipline              →  REPLACED BY I (Layered Architecture) + III (Dependency Injection)
  III. Test-First                     →  REPLACED BY VI (Test Strategy — new patterns and tools)
  IV.  RAG Pipeline Integrity         →  SUPERSEDED BY V (RAG Pipeline Integrity — 6-step, updated)
  V.   SQL Safety and Idempotency     →  RETAINED AS VII (SQL Safety — same rules, new driver context)
  VI.  Secrets-First Security         →  RETAINED AS VIII (Secrets-First — upgraded to Pydantic Settings)
  VII. Performance-Aware Design       →  REMOVED — folded into V and IX where applicable
  VIII.Deployment Discipline          →  REPLACED BY X (Docker Infrastructure)

Added principles (new):
  I.   Layered Architecture
  II.  Repository Pattern
  III. Dependency Injection via FastAPI Depends()
  IV.  Configuration Management via Pydantic Settings
  V.   RAG Pipeline Integrity (updated 6-step)
  VI.  Test Strategy
  VII. SQL Safety and Idempotency
  VIII.Secrets-First Security
  IX.  Frontend Contract
  X.   Docker-Based Infrastructure

Removed principles:
  - Multi-Source Data Portability (decode_source / sqlite-local / SQLAlchemy engines)
  - Module Discipline (Streamlit module_*.py boundary)
  - Performance-Aware Design (as stand-alone principle)
  - Deployment Discipline (replaced by Docker/devcontainer principle)

Templates reviewed:
  ✅ .specify/templates/plan-template.md   — Constitution Check gates updated to new 10 principles
  ✅ .specify/templates/spec-template.md   — FR/SC patterns compatible with new principle set
  ✅ .specify/templates/tasks-template.md  — Phase structure and task categories updated
  ✅ .specify/templates/constitution-template.md — source template; not modified

Follow-up TODOs:
  - TODO(CORS_PRODUCTION): main.py allow_origins=["*"] must be restricted before production deploy
  - TODO(SINGLETON_ADAPTER): OpenAIAdapter instantiated per-request; consider module-level singleton
  - TODO(CONNECTION_POOLING): PostgresMatchRepository and PostgresEventRepository open new connections
    per-call; add psycopg2.pool under high concurrency
-->

# RAG-Challenge Constitution

## Core Principles

### I. Layered Architecture

The backend MUST maintain strict one-way dependency flow across four layers.
No layer may import from a layer above it.

```
HTTP boundary
  └── api/v1/         ← request validation, HTTP status, response serialisation only
        └── services/ ← orchestration and business logic; no SQL, no HTTP concerns
              └── repositories/ ← data access only; returns domain entities
                    ├── domain/   ← pure Python dataclasses + exceptions; zero dependencies
                    ├── adapters/ ← thin wrappers for external services (OpenAI, etc.)
                    └── core/     ← config wiring and dependency providers
```

Rules:
- Route handlers (`api/v1/*.py`) MUST NOT contain SQL, business logic, or direct DB calls.
  Their only jobs are: validate HTTP input, call a service or repository via injected
  dependency, convert domain objects to API response models, and map exceptions to HTTP codes.
- Services (`services/*.py`) MUST NOT import `fastapi`, construct HTTP responses, or reference
  Pydantic API models from `api/v1/models.py`. They receive and return domain entities.
- Repositories (`repositories/*.py`) MUST NOT contain any business logic. They translate between
  DB rows and domain entities. All queries live in the repository; none in the service.
- Domain (`domain/`) MUST remain a pure Python layer: no database drivers, no HTTP framework,
  no external service SDKs. `entities.py` uses `@dataclass`; `exceptions.py` inherits from
  `DomainException`.
- Adapters (`adapters/`) wrap exactly one external service per file. They may only be called
  from services, never from route handlers or repositories.
- `core/config.py` re-exports `get_settings()`. `core/dependencies.py` re-exports typed
  `Depends()` shortcuts. `core/capabilities.py` owns the per-source capability matrix and
  `normalize_source()`.

Rationale: The Streamlit monolith mixed UI, data access, and business logic in the same
functions. The layered architecture makes each concern independently testable, swappable,
and reviewable.

### II. Repository Pattern

ALL database access MUST go through the `BaseRepository` ABC hierarchy defined in
`backend/app/repositories/base.py`.

Rules:
- `BaseRepository` provides `get_connection()` (context manager) and `test_connection()`.
  Every concrete implementation MUST implement both.
- `MatchRepository` and `EventRepository` extend `BaseRepository` with entity-specific
  abstract methods. Any new entity domain (e.g., players, lineups) MUST add its own
  abstract repository class to `base.py` before any concrete implementation is written.
- Concrete implementations live in `postgres.py` (psycopg2) and `sqlserver.py` (pyodbc).
  Switching data sources is a dependency injection concern — the service layer is unaware
  of which implementation it receives.
- Repository constructors MUST read all DB config from `get_settings()` at `__init__` time.
  They MUST NOT accept raw connection strings or credentials as constructor arguments.
- `get_connection()` MUST use `@contextmanager`, commit on success, rollback on exception,
  and always close in `finally`. No connection may be leaked.
- Row hydration helpers (`_row_to_match`, `_row_to_event`, etc.) MUST be private methods
  on the concrete class. Domain entities are NEVER constructed outside a repository.
- Repository factories (`PostgresRepositoryFactory`, `SQLServerRepositoryFactory`) are the
  sole objects allowed to instantiate concrete repository classes.

Source normalization:
- `core/capabilities.py::normalize_source()` collapses all aliases to `"postgres"` or
  `"sqlserver"`. These are the only two canonical sources; `sqlite-local` is retired.
- `SOURCE_CAPABILITIES` in `capabilities.py` is the single source of truth for which
  embedding models and distance algorithms each backend supports.

Rationale: The ABC contract guarantees that any service can be tested against a mock
repository and deployed against either backend without code changes.

### III. Dependency Injection via FastAPI Depends()

ALL external collaborators — repositories, services, adapters, and settings — MUST be
injected into route handlers and service constructors via FastAPI's `Depends()` mechanism.
Direct instantiation inside route handlers is forbidden.

Rules:
- Route handlers declare all collaborators as function parameters with `Depends()`:
  ```python
  async def list_matches(
      repo: MatchRepository = Depends(get_match_repository),
      openai: OpenAIAdapter = Depends(get_openai_adapter),
  ) -> ...:
  ```
- `core/dependencies.py` provides all `get_*` provider functions and typed `Annotated`
  shortcuts (`MatchRepo`, `EventRepo`).
- The `source` query parameter drives repository selection at request time via
  `get_repository_factory(source)` in `dependencies.py`. The factory pattern isolates
  source-to-implementation resolution.
- Tests MUST override dependencies using `app.dependency_overrides`:
  ```python
  app.dependency_overrides[get_match_repository] = lambda source="postgres": mock_repo
  ```
  Every test fixture that calls `TestClient(app)` MUST call `app.dependency_overrides.clear()`
  in teardown (use `yield` in fixtures to guarantee this).
- `get_settings()` MUST be wired via `Depends()` in any route that reads config at request
  time. Module-level `settings = get_settings()` is acceptable in repositories and adapters
  (called once at import time), but NEVER called inside route handler bodies.

Rationale: `Depends()` is the FastAPI-idiomatic way to achieve testability without mocking
at the OS/module level. It replaces `unittest.mock.patch(os.getenv)` patterns from v1.

### IV. Configuration Management via Pydantic Settings

ALL application configuration MUST be loaded through the `config/settings.py` module.
No route handler, service, repository, or adapter may call `os.getenv()` or `os.environ`
directly.

Rules:
- `config/settings.py` defines `DatabaseConfig`, `OpenAIConfig`, `RepositoryConfig`, and
  the top-level `Settings` class using `pydantic_settings.BaseSettings`.
- Sub-configs are composed as `Field(default_factory=<SubConfig>)` on the `Settings` class.
  All env-var aliases are declared in `Field(alias=...)` — never inferred by convention.
- A single module-level `settings` instance is created at `config/__init__.py` import time.
  `backend/app/core/config.py` re-exports it through `get_settings()` for FastAPI injection.
- `Settings.validate_required()` is called at startup when `environment != "test"`.
  Any missing or empty required field MUST raise `ValueError` with a descriptive message
  — fail fast before serving any requests.
- Adding a new configuration variable requires:
  1. Add typed `Field` in the appropriate `*Config` class.
  2. Add the variable with a description comment to `.env.example`.
  3. Add a dummy safe value to `conftest.py` if tests need it.
  4. Document in the PR description.
- `model_config = SettingsConfigDict(env_file=".env", case_sensitive=False, extra="ignore")`
  MUST be present on every `BaseSettings` subclass.
- The three allowed environments are `"local"`, `"azure"`, and `"test"`. No others.

Rationale: Centralised typed validation means misconfiguration is caught at startup,
not silently at the first request that needs the value.

### V. RAG Pipeline Integrity

The RAG query pipeline in `SearchService.search_and_chat()` MUST execute these steps
in order. No step may be skipped, reordered, or merged with another.

```
1. Translate    — if language != "english", translate query to English via OpenAI Chat
2. Embed        — generate query vector (default: text-embedding-3-small, 1536 dims)
3. Search       — vector similarity search via EventRepository.search_by_embedding()
4. Enrich       — prepend GAME_RESULT block when include_match_info is true
5. Budget       — count tokens; if tokens > max_input_tokens, return sentinel without LLM call
6. Generate     — chat completion via OpenAIAdapter.create_chat_completion()
```

Rules:
- Steps 1–6 are implemented in `SearchService`; repositories handle only step 3 (query
  execution). No RAG logic lives in route handlers or repositories.
- Step 5 (budget) is a hard guard: the sentinel `"TOKENS. The prompt is too long."` MUST be
  returned and logged without calling the LLM when the token budget is exceeded. This
  prevents runaway Azure OpenAI cost.
- The default similarity metric is **cosine** — `<=>` operator in PostgreSQL pgvector,
  `VECTOR_DISTANCE('cosine', ...)` in SQL Server. Other metrics are explicit opt-ins via
  the `SearchAlgorithm` enum.
- `SearchAlgorithm` and `EmbeddingModel` are defined as `str, Enum` in `domain/entities.py`
  and are the sole authoritative list. Any new model or metric requires:
  1. A new enum member in `domain/entities.py`.
  2. A corresponding entry in `SOURCE_CAPABILITIES` in `core/capabilities.py`.
  3. Updated DDL / index on the affected table(s).
- `validate_search_capabilities(source, embedding_model, search_algorithm)` MUST be called
  in the route handler before constructing the `SearchService`. Capability mismatches MUST
  be surfaced as HTTP 422 errors, not 500s.
- `OpenAIAdapter` uses exponential backoff for 429 and transient API errors (max 5 retries,
  initial backoff 1 s, cap 60 s). This logic lives exclusively in `_call_with_retry()`.
- Batch embedding calls use `BATCH_SIZE = 50` texts per request with a 100 ms inter-batch
  delay to respect Azure OpenAI rate limits.

Rationale: The pipeline is the core value delivery of the system. Breaking the order or
skipping steps produces incorrect answers or uncontrolled costs.

### VI. Test Strategy (NON-NEGOTIABLE)

No new public function, route, or service method may be merged without a corresponding test
written **before** the implementation (Red → Green → Refactor). Coverage MUST remain at or
above **80%** on `backend/app/` as measured by `pytest --cov=app`.

Test levels:

| Level | Location | Isolation | Run in CI? |
|---|---|---|---|
| Unit | `backend/tests/unit/` | All I/O mocked | ✅ Always |
| API | `backend/tests/api/` | `TestClient` + `dependency_overrides` | ✅ Always |
| Integration | `backend/tests/integration/` | Live DB required | ❌ `INTEGRATION_TESTS=1` |

API test rules (CI gate):
- Each API test module MUST define its own `client` fixture that applies `dependency_overrides`
  for ALL external collaborators (`get_match_repository`, `get_event_repository`,
  `get_openai_adapter`) and clears them in teardown via `yield` + `app.dependency_overrides.clear()`.
- `conftest.py` provides factory helpers (`make_match()`, `make_event()`,
  `make_mock_match_repo()`, etc.). All test data MUST be constructed via these factories;
  no inline dicts masquerading as domain objects in test assertions.
- `MagicMock(spec=MatchRepository)` MUST be used for repo mocks; `spec=` ensures the mock
  raises `AttributeError` on undefined method calls, catching interface drift early.
- Default match IDs in factories use the canonical match `3943043` (England vs Spain,
  Euro 2024 Final) and `3869685` (France vs Argentina, FIFA World Cup 2022 Final).

Unit test rules:
- All Azure OpenAI and DB calls MUST be mocked via `unittest.mock.patch` or injected mocks.
- No test may make a real network call; if a test requires network, it is an integration test.
- Test names follow `test_<method>_<scenario>_<expected_outcome>`.

Rationale: Azure cloud costs make live-service CI impractical. TestClient + dependency
overrides give fast, free, deterministic tests that still validate the full FastAPI
request/response cycle including middleware and exception handlers.

### VII. SQL Safety and Idempotency

ALL SQL executed from Python MUST use parameterised queries. String interpolation of
any externally-sourced value (including `match_id`, `top_n`, or user query text) into SQL
is forbidden.

```python
# CORRECT — psycopg2 (PostgreSQL)
cur.execute(
    "SELECT id, summary FROM events_details WHERE match_id = %s ORDER BY id LIMIT %s",
    (match_id, top_n),
)

# CORRECT — pyodbc (SQL Server)
cur.execute(
    "SELECT id, summary FROM events_details WHERE match_id = ? ORDER BY id"
    " OFFSET 0 ROWS FETCH NEXT ? ROWS ONLY",
    (match_id, top_n),
)

# FORBIDDEN — SQL injection risk
query = f"SELECT ... WHERE match_id = {match_id}"
```

Idempotency rules (DDL scripts):
- Every `CREATE TABLE` MUST use `IF NOT EXISTS`.
- Every `DROP TABLE` / `DROP INDEX` MUST use `IF EXISTS`.
- Scripts in `postgres/` and `sqlserver/` MUST be independently re-runnable without error.
- Scripts are numbered with zero-padded prefixes: `00_`, `01_`, `02_`, …

Syntax isolation:
- T-SQL constructs (`TOP`, `IDENTITY`, `OUTPUT INSERTED.*`, `NVARCHAR`, `?` placeholder,
  `VECTOR_DISTANCE()`) → `sqlserver/` files and `sqlserver.py` only.
- PostgreSQL constructs (`LIMIT`, `SERIAL`, `RETURNING`, `VECTOR(n)`, `<=>`,
  `%s` placeholder, pgvector operators) → `postgres/` files and `postgres.py` only.
- Mixing syntaxes across files is a merge-blocking defect.

Rationale: The system processes user-supplied natural language that feeds into SQL.
SQL injection is OWASP Top 10 #3; parameterised queries are the only safe mitigation.

### VIII. Secrets-First Security

ALL credentials, API keys, connection strings, and sensitive configuration MUST be loaded
exclusively via Pydantic Settings (`config/settings.py`). No secret may be hardcoded —
not in source, not in comments, not in example values that resemble real credentials.

Rules:
- Database passwords, OpenAI API keys, and Azure endpoints live in `.env` (gitignored).
- The production `.env` file is never committed. `.env.example` holds placeholder descriptions.
- `docker-compose.yml` reads credentials from environment variables (`${VAR:-default}`)
  using safe local-only defaults that are clearly non-production.
- For Azure Container / ACI deployments, secrets MUST be injected via
  `--secure-environment-variables`; non-sensitive config via `--environment-variables`.
- CORS: `allow_origins=["*"]` in `main.py` is a development-only setting. Before any
  public deployment, it MUST be replaced with an explicit origin allowlist
  (tracked as TODO(CORS_PRODUCTION)).
- The following MUST NEVER be committed:
  - `.env` (any variant with real credentials)
  - Database dump or data files (`*.db`, `*.bak`, `.sql` files containing INSERT data)
  - Generated embeddings or vector data files
  - `__pycache__/`, `*.pyc`, `*.pyo`

Rationale: The project uses sponsored Azure OpenAI API keys. Exposure of a key would
exhaust quota, incur charges, and compromise the sponsorship.

### IX. Frontend Contract

The React TypeScript frontend (`frontend/webapp/`) MUST communicate with the backend
exclusively through the versioned REST API at `backend/app/api/v1/`.

Rules:
- The frontend MUST NOT import Python modules, connect directly to PostgreSQL or SQL Server,
  or read the `.env` file. It is a pure HTTP client.
- All API request/response shapes MUST be defined in `backend/app/api/v1/models.py` (Pydantic
  models). The frontend TypeScript types MUST mirror these shapes. When the backend schema
  changes, the frontend types MUST be updated in the same PR.
- The base API URL MUST be read from a Vite environment variable (`VITE_API_URL`), never
  hardcoded. Example: `import.meta.env.VITE_API_URL`.
- HTTP errors from the backend (4xx, 5xx) MUST be surfaced to the user with a descriptive
  message. Silent failures are not acceptable.
- New backend endpoints MUST be added under `/api/v1/`; no endpoint lives outside the
  versioned prefix.
- When a breaking API change is required, bump the path to `/api/v2/` and maintain `/api/v1/`
  until frontend migration is complete in the same release.

Rationale: A clean API boundary means the frontend can be developed independently of the
backend, deployed separately, and enables future mobile or CLI clients to reuse the same
API without changes.

### X. Docker-Based Infrastructure

Local development and CI MUST use `docker-compose.yml` as the single source of truth for
infrastructure services. No external service (database, vector store) may be required to be
installed on the host machine.

Rules:
- The compose file defines exactly two database services: `rag-postgres` (PostgreSQL 17 +
  pgvector via `pgvector/pgvector:pg17`) and `rag-sqlserver` (SQL Server 2025 Express).
- Both services use named Docker volumes for data persistence and are on the `internal`
  network only. No service is exposed to the outside world beyond the declared port mappings.
- Both services MUST define `healthcheck` blocks. Dependent services MUST use
  `depends_on: condition: service_healthy`.
- `security_opt: no-new-privileges:true` MUST be present on all compose services.
- Resource limits (`deploy.resources.limits.memory`) MUST be set for SQL Server to prevent
  host memory exhaustion in local dev.
- Credentials in `docker-compose.yml` use `${VAR:-safe_local_default}` pattern. Local
  defaults are non-production-grade and documented as such in `.env.example`.
- DDL init scripts in `infra/docker/postgres/initdb/` are mounted read-only and run once at
  first container start. They MUST be idempotent (see Principle VII).
- New infrastructure dependencies (e.g., Redis, Elasticsearch) MUST be added to
  `docker-compose.yml` before any code that requires them is merged.

Rationale: Docker Compose eliminates "works on my machine" problems, makes onboarding
a one-command operation, and ensures CI uses an environment identical to development.

---

## Additional Constraints

### Brownfield Debt Register

The following known deviations from this constitution exist in the codebase and MUST NOT
be replicated. Each has a tracking TODO:

| TODO | Location | Violation | Resolution |
|---|---|---|---|
| `TODO(CORS_PRODUCTION)` | `backend/app/main.py` | `allow_origins=["*"]` | Restrict before public deploy |
| `TODO(SINGLETON_ADAPTER)` | `adapters/openai_client.py` | Adapter instantiated per-request | Consider module-level singleton |
| `TODO(CONNECTION_POOLING)` | `repositories/postgres.py` | New connection per call | Add `psycopg2.pool` under load |

These items MUST appear in the roadmap backlog and MUST be resolved before any load-testing
or production deployment milestone is declared complete.

### Embedding Model Registry

| Enum value | Azure deployment name | Dimensions | Default? |
|---|---|---|---|
| `text-embedding-3-small` | `text-embedding-3-small` | 1536 | ✅ Yes |
| `text-embedding-ada-002` | `ada-002` | 1536 | No |
| `text-embedding-3-large` | `text-embedding-3-large` | 3072 | No |

Upgrading to `text-embedding-3-large` requires explicit justification (quality improvement
demonstrated on the eval dataset). `text-embedding-3-small` is the mandatory default for all
new features.

### Key Development Match IDs

These match IDs MUST be used as defaults in all test factories and development scripts:
- `3943043` — UEFA Euro 2024 Final: England vs Spain
- `3869685` — FIFA World Cup 2022 Final: France vs Argentina

---

## Development Workflow

1. **Branch**: `feature/NNN-description`, `fix/NNN-description`, or `chore/description`.
2. **Constitution Check**: Before any implementation, verify the planned change complies with
   all 10 principles. Document the check result in the plan (`specs/.../plan.md`).
3. **Test first**: Write failing tests before writing the implementation (Principle VI).
4. **Lint and type check**: `ruff check backend/app/` and `mypy backend/app/` must pass clean.
5. **Coverage**: `pytest --cov=app --cov-report=term-missing` must report >= 80% on `backend/app/`.
6. **CHANGELOG**: Every PR that modifies code MUST add an entry under `## [Unreleased]`.
7. **conversation_log.md**: Append an entry to `docs/conversation_log.md` for every
   significant AI-assisted session.
8. **PR requirements**: No `.env`, no hardcoded credentials, no `*.pyc`, tests green,
   layer boundaries respected, Constitution Check section present in PR description.

### Constitution Check Gates (for plan-template.md)

Before implementing any feature, verify each applicable gate:

- [ ] **Layered arch**: Does the change respect the api → services → repositories → domain
      flow? No imports in the wrong direction?
- [ ] **Repository**: Is all new DB access behind an abstract repository method?
- [ ] **DI**: Are all collaborators injected via `Depends()`? No direct instantiation in handlers?
- [ ] **Config**: Are new env vars in `config/settings.py` → `.env.example` → `conftest.py`?
- [ ] **RAG pipeline**: If the feature involves Q&A, do all 6 steps execute in order?
- [ ] **Test-first**: Is there a failing test before the implementation exists?
- [ ] **SQL safety**: Are all new queries parameterised? No f-string SQL?
- [ ] **Secrets**: No hardcoded credentials? `.env` gitignored?
- [ ] **Frontend**: API response shapes updated in `api/v1/models.py` AND TypeScript types?
- [ ] **Docker**: New infrastructure services added to `docker-compose.yml`?

---

## Governance

This constitution supersedes version 1.0.0 and all prior guidance documents that reference
the Streamlit architecture (module_data.py, module_azure_openai.py, app.py shell).

**Amendment procedure**:
- PATCH: Any contributor may propose via PR; requires 1 reviewer approval.
- MINOR: Requires team discussion and documented rationale in PR description.
- MAJOR: Requires ADR (`docs/adr/ADR-NNN.md`) documenting the architectural decision,
  team consensus, and migration plan before the PR is opened.

**Compliance review**: Every PR description MUST include a Constitution Check section
confirming which principles apply and how they are satisfied. PRs without this section
are blocked from merge.

**Versioning policy**: Semantic versioning applies:
- MAJOR — principle removal, redefinition, or architectural replacement
- MINOR — new principle or materially expanded guidance
- PATCH — clarifications, wording, examples, typo fixes

**Version**: 2.0.0 | **Ratified**: 2025-01-01 | **Last Amended**: 2026-04-02
