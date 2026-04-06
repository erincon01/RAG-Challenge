# Changelog

All notable changes to this project will be documented in this file.

Format based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/).

---

## [Unreleased]

### Changed
- Rename ~50 test functions across 15 test files to follow `test_<method>_<scenario>_<expected>` naming convention

### Added
- `docs/getting-started.md` — new contributor guide (setup, OpenSpec workflow, where to find things)
- `frontend/webapp/.env.example` with `VITE_API_BASE_URL` and `VITE_BACKEND_ORIGIN`
- `.pre-commit-config.yaml` with ruff lint + format hooks for backend
- Token budget guard in RAG pipeline: counts tokens before LLM call using `tiktoken` and truncates lowest-ranked search results if context exceeds `max_input_tokens`
- Token usage metadata in response: `input_tokens`, `max_input_tokens`, `results_truncated`
- `tiktoken` dependency added to `backend/requirements.txt`

### Fixed
- Replace direct `PostgresEventRepository()` / `SQLServerEventRepository()` instantiation in `health.py` and `capabilities.py` with FastAPI `Depends()` injection
- Add `get_postgres_event_repository` and `get_sqlserver_event_repository` DI providers in `dependencies.py`
- Refactor `DataExplorerService` to use injected `MatchRepository` instead of raw `psycopg2`/`pyodbc` connections, following the Repository Pattern

### Security
- Replace `allow_origins=["*"]` with configurable `CORS_ORIGINS` env var in CORS middleware
- Add `cors_origins` setting to `config/settings.py` with safe localhost defaults

### Governance
- `AGENTS.md` — single source of truth for all project conventions and agent rules
- `CLAUDE.md` — Claude Code entry point with project overview, commands, and governance chain
- `openspec/` — OpenSpec v1.2.0 governance: config, 4 system specs (api, rag, data, infra), 1 archived change
- `.claude/commands/opsx/` + `.claude/skills/` — Claude Code OpenSpec integration (propose, apply, archive, explore)
- `.github/prompts/opsx-*` + `.github/skills/openspec-*` — GitHub Copilot OpenSpec integration
- `.github/pull_request_template.md` — PR checklist with architecture check (OpenSpec-aware)
- `mypy.ini` — targeted mypy config (pyodbc and config/ stubs ignored; no blanket ignore)
- `types-psycopg2` added to `backend/requirements.txt`
- `docs/PLAN_OPENSPEC_ADOPTION.md` — full adoption plan (phases 0-3 completed)
- `docs/architecture.md`, `docs/data-model.md`, `docs/semantic-search.md`, `docs/tech-stack.md`
- `docs/conversation_log.md` — AI session audit trail (17 sessions documented)
- `docs/archive/` — completed migration plans moved here
- Backend pytest suite: 433+ tests, 80%+ coverage (unit + API)
- `backend/pytest.ini` with `unit`, `api`, `integration` markers
- `.github/workflows/ci.yml` — lint + typecheck + tests with 80% coverage gate
- `.github/workflows/cd.yml` — deployment skeleton (placeholder)

### Changed
- **OpenSpec replaces spec-kit** as the spec-driven governance framework (PR #11)
- DI refactor: replaced `_service = XxxService()` module-level singletons with `Depends()` in all route files
- `core/dependencies.py` — 3 new providers (`get_statsbomb_service`, `get_ingestion_service`, `get_data_explorer_service`) + type aliases
- All API tests migrated from `patch("..._service")` to `dependency_overrides`
- `ruff format` applied to all backend files (ruff 0.15.8+ compatible)
- `PROJECT_STATUS.md` — rewritten to reflect current state (2026-04-06)
- `README.md` — added branch governance table, updated test count and status
- `PLAN_REARQUITECTURA_COMPLETO.md` → moved to `docs/archive/`
- `PLAN_MIGRACION_FRONTEND_WEB.md` → moved to `docs/archive/`

### Removed
- spec-kit artifacts: `.specify/`, `.flake8`, `pyproject.toml`, `specs/README.md`
- spec-kit agents (`.github/agents/speckit.*.agent.md`)
- spec-kit prompts (`.github/prompts/speckit.*.prompt.md`)
- spec-kit docs (`docs/spec-kit-adoption-plan.md`, `docs/articles/brownfield-to-speckit-adoption.md`, `docs/audit/`)
- Obsolete instruction files (`.github/instructions/python-modules.instructions.md`, `sql-embeddings.instructions.md`)
- `.pre-commit-config.yaml` (to be reintroduced when pre-commit hooks are validated)
- `dotnetMalaga/` directory (presentations already in `docs/presentations/`)

---

## [3.2.0] - 2026-02-20 — Devcontainer v2 + pgvector portable

### Added
- **devcontainer**: `docker-compose.override.yml` — activates postgres profile and runs `sleep infinity` so VS Code manages the lifecycle
- **devcontainer**: `post-create.sh` — installs Python deps, bootstraps PostgreSQL + SQL Server schemas (idempotent), seeds a smoke-test row in each DB
- **devcontainer**: `post-start.sh` — starts uvicorn in background, runs liveness + readiness + optional frontend health checks
- **devcontainer**: `.env.docker.example` — template without hardcoded credentials
- **devcontainer**: SQLTools VS Code extensions for in-container DB access (postgres + sqlserver)
- **devcontainer**: port forwarding configured for 5173, 8000, 5432, 1433
- **pgvector**: fully portable embeddings pipeline — embeddings generated by OpenAI API in the application layer, not by Azure DB extensions
- **pgvector**: `embedding_status`, `embedding_updated_at`, `embedding_error` tracking columns in schema
- **pgvector**: HNSW indexes for cosine (`<=>`) and inner product (`<#>`) similarity
- **pgvector**: batch processing worker with exponential backoff retry
- **pgvector**: `OPENAI_PROVIDER` setting (`azure|openai`) for portable adapter
- **frontend**: React TypeScript replaces Streamlit as the primary frontend (Streamlit marked deprecated)

### Removed
- All `azure_ai` and `azure_local_ai` extension dependencies from PostgreSQL schema and queries
- `DB_*_AZURE_*` environment variable naming (replaced with neutral names)
- Streamlit legacy frontend from active development

### Fixed
- Devcontainer build failures due to missing compose override
- CRLF issues in shell scripts and config files

**Commits:** `7a311db`, `27d40ae`, `5b14ae2`, `9943bff`, `891f991`
**PRs merged:** #7 (devcontainer-v2), #6 (rearquitectura-completa), #5 (pgvector-cleanup)

---

## [3.1.0] - 2026-02-08 — Operations & Embeddings hardening

### Added
- **OperationsPage**: download cleanup filters to remove stale/partial downloads
- **OperationsPage**: "Clear completed jobs" action
- **OperationsPage**: embedded execution terminal for real-time job output
- **EmbeddingsPage**: embeddings coverage status per match
- **EmbeddingsPage**: rebuild embeddings per match via UI
- **ChatPage**: capability-aware RAG — chat adapts dynamically to available DB capabilities
- SQL Server schema adjustments for Docker Express edition compatibility

### Changed
- Vector model configuration updated and unified across backend
- Environment variable `.env.docker` removed from git tracking (added to `.gitignore`)

### Fixed
- Typos and spelling corrections across documentation
- SQL Server schema `setup.sh` line endings (CRLF → LF)

**Commits:** `b1be41a`, `4849d53`, `1204ca1`, `db0cb73`, `e25b511`, `1222e8f`

---

## [3.0.0] - 2026-02-08 — Full React TypeScript frontend (Phases 0–5)

Major milestone: complete migration from Streamlit to React TypeScript frontend, with full backend API coverage for ingestion, exploration, embeddings, and RAG chat.

### Added

#### Backend — Phase 0: Source capabilities & readiness
- `GET /api/v1/capabilities` endpoint with DB capabilities matrix per engine
- `GET /api/v1/sources/status` with real connectivity test
- DB validation in `/health/ready` readiness probe
- `feat(phase-0)` — commit `8e6b4cb`

#### Backend — Phase 1: Ingestion API & Job system
- `IngestionService` (612 lines) with full StatsBomb → PostgreSQL/SQL Server pipeline
- `JobService` with state machine: `pending → running → success/error/canceled`
- `StatsBombService` for remote catalog browsing
- New endpoints: `GET/POST /api/v1/statsbomb/*`, `GET/POST /api/v1/ingestion/*`
- Job tracking with logs, progress, and cancellation
- `feat(phase-1)` — commit `a16b791`

#### Frontend — Phase 2: React TypeScript bootstrap
- React 19 + TypeScript + Vite project scaffolded at `frontend/webapp/`
- TailwindCSS for styling
- TanStack Query for server state and caching
- React Router v6 for navigation
- Type-safe API client (`client.ts`, 151 lines)
- Full TypeScript domain types (`types.ts`, 208 types)
- `AppShell` layout with sidebar navigation
- UI settings management with local storage
- `feat(phase-2)` — commit `5f8ee88`

#### Frontend — Phase 3: Core operational screens
- `DashboardPage` — system health, DB status, recent jobs at a glance
- `SourcesPage` (formerly CatalogPage structure) — engine selector, connectivity test
- `CatalogPage` — StatsBomb competitions/matches browser with selection (182 lines)
- `OperationsPage` — download/load pipeline with real-time job tracking and polling (480 lines)
- Catalog selection persisted to local storage
- `feat(phase-3)` — commit `3e4b0e4`

#### Backend + Frontend — Phase 4: Data explorer & parity
- `DataExplorerService` (276 lines) with queries for competitions, matches, teams, players, events
- `GET /api/v1/explorer/*` endpoints
- `ExplorerPage` with tabbed views: Competitions, Matches, Teams, Players, Events, Tables Info (272 lines)
- Full functional parity with legacy `app.py` menus
- `feat(phase-4)` — commit `38db8d5`

#### Frontend — Phase 5: Embeddings & advanced chat
- `EmbeddingsPage` — embedding coverage per match, rebuild trigger (193 lines)
- `ChatPage` — RAG semantic search with dynamic restrictions based on engine capabilities (242 lines)
- `GET/POST /api/v1/embeddings/*` endpoints
- `feat(phase-5)` — commit `e25b511`

#### Infrastructure
- `docker-compose.yml` with 4 services: postgres, sqlserver, backend, frontend
- Persistent volumes: `postgres_data`, `sqlserver_data`
- Healthchecks with `depends_on: condition: service_healthy`
- Idempotent init scripts for PostgreSQL and SQL Server
- Frontend `Dockerfile` (Node 20 + Vite build)
- `docs/adr/ADR-001` through `ADR-004` accepted

### Changed
- Frontend Streamlit refactored as pure HTTP client (no direct DB access)
- OpenAI adapter unified for Azure OpenAI + direct OpenAI

**Commits (all 2026-02-08):** `8e6b4cb`, `777b5ae`, `a16b791`, `5f8ee88`, `3e4b0e4`, `38db8d5`, `e25b511`

---

## [2.0.0] - 2026-02-08 — Backend rearchitecture + Docker infrastructure

Full backend layered architecture and local Docker infrastructure.

### Added

#### Phase 0: Technical stabilization
- Centralized configuration with Pydantic `BaseSettings` (`config/settings.py`)
  - `DatabaseConfig`, `OpenAIConfig`, `RepositoryConfig`
  - Fail-fast validation at startup
  - Environments: `local`, `azure`, `test`
- Fixed bugs in `module_github.py` (undefined variables `password`, `dataset`)
- Fixed `module_azure_openai.py` hardcoded `top_n = 10` (now respects parameter)
- Fixed `app.py` language comparison and dataset log bugs
- 4 Architecture Decision Records: ADR-001 (Layered Architecture), ADR-002 (Centralized Config), ADR-003 (pgvector Migration), ADR-004 (Local Docker Infrastructure)
- **Commits:** `d536e87`, `e40f393`, `8c04a65`

#### Phase 1: Backend/Frontend separation
- FastAPI backend with full layer separation at `backend/`
  - `api/` — routers, DTOs, validation (health, matches, events, chat, competitions)
  - `services/` — use cases (`SearchService` with multi-language support, embedding generation, vector search, LLM response)
  - `repositories/` — `PostgresMatchRepository`, `PostgresEventRepository`, `SQLServerMatchRepository`, `SQLServerEventRepository` (all decoupled from each other)
  - `domain/` — entities: Match, EventDetail, Competition, Team, SearchRequest, SearchResult, ChatResponse; Enums: SearchAlgorithm, EmbeddingModel
  - `adapters/` — unified OpenAI/Azure OpenAI client (`create_embedding`, `create_chat_completion`, `translate_to_english`)
- READMEs for every layer documenting patterns and contracts
- Frontend Streamlit refactored as pure HTTP client (`app_refactored.py`)
- **Commits:** `ba7e9a3`, `23f4a1d`, `ee8d491`, `f378b3b`

#### Phase 2: Docker local infrastructure
- `backend/Dockerfile` — Python 3.11-slim + ODBC Driver 18 + psycopg2
- `infra/docker/sqlserver/Dockerfile` — SQL Server 2025 Express with custom `setup.sh` entrypoint
- PostgreSQL init scripts: `01-extensions.sql` (vector extension), `02-schema.sql` (full portable schema with HNSW indexes)
- SQL Server init scripts: `01-schema.sql` (rag_challenge DB + all tables, idempotent)
- **Commits:** `9a956b0`, `75284be`

---

## [1.0.0] - 2025-07-06 — Initial cleanup

### Changed
- Removed unused media files and outdated presentation assets
- Updated `data.txt` with relevant project resource links

**Commit:** `283ba89`

---

## Legend

- **[Unreleased]** — Changes staged/pending for next commit
- **[x.y.z]** — Released versions following [SemVer](https://semver.org/)
- Types: `Added`, `Changed`, `Deprecated`, `Removed`, `Fixed`, `Security`
