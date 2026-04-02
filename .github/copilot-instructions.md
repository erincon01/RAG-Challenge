# RAG-Challenge — Project Guidelines

## Project Overview

Football/soccer event data RAG (Retrieval-Augmented Generation) system using StatsBomb open data.
Queries are answered via semantic similarity search over embeddings stored in PostgreSQL (pgvector) or Azure SQL Server.

Tech stack: **Python 3.11+**, **FastAPI**, **React TypeScript + Tailwind**, **PostgreSQL + pgvector**, **Azure SQL Server**, **Azure OpenAI**, **Docker Compose** (local dev).

## Code Architecture

- `backend/` — FastAPI backend (Python 3.11+)
  - `backend/app/api/v1/` — HTTP endpoints, one file per domain (chat, matches, events, embeddings, ingestion…)
  - `backend/app/services/` — business logic; stateless; injected via FastAPI `Depends()`
  - `backend/app/repositories/` — data access; `BaseRepository` ABC + PostgreSQL/SQL Server implementations
  - `backend/app/domain/` — entities, exceptions, value objects (pure Python, no frameworks)
  - `backend/app/adapters/` — external service adapters (Azure OpenAI client)
  - `backend/app/core/` — config (`get_settings()`), dependency wiring, startup
- `frontend/` — React TypeScript + Tailwind frontend
- `config/` — shared Pydantic Settings (loaded by backend and scripts)
- `postgres/` — PostgreSQL DDL, embedding setup, queries
- `sqlserver/` — Azure SQL DDL and T-SQL scripts
- `backend/tests/` — pytest test suite (`unit/`, `api/`, `integration/`)

See [docs/spec-kit-migration-plan.md](docs/spec-kit-migration-plan.md) for the full SDD workflow with spec-kit.

## TDD — Test-Driven Development (required)

**Write the test before the implementation.** No new function or module is merged without a corresponding test.

- Test runner: `pytest` (with `pytest-asyncio` for async endpoints)
- Test location: `backend/tests/` — `unit/`, `api/`, `integration/`
- Run tests: `cd backend && pytest tests/ -v`
- Run with coverage: `cd backend && pytest tests/ --cov=app --cov-report=term-missing`
- Minimum coverage target: **80%** on `backend/app/`
- Mock via FastAPI dependency override (`app.dependency_overrides`) + `unittest.mock.patch` for adapters

See [.github/instructions/tdd.instructions.md](.github/instructions/tdd.instructions.md) for detailed TDD patterns.

## Git Workflow

- **Branch naming**: `feature/NNN-short-description`, `fix/NNN-description`, `chore/description`
- **Commits**: Conventional Commits — `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`
- **PRs**: All changes via Pull Request; no direct push to `main`
- **PR requirements**: tests pass, no `.env`, no hardcoded credentials, no `*.pyc`

See [.github/instructions/git-workflow.instructions.md](.github/instructions/git-workflow.instructions.md) for full norms.

## CHANGELOG.md (mandatory)

`CHANGELOG.md` lives at the project root and **must be updated in every PR**. It is the authoritative record of what changed and why.

- Format: [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) — sections `Added`, `Changed`, `Fixed`, `Removed`
- Each PR adds an entry under `## [Unreleased]`
- On merge to `main`, `[Unreleased]` is promoted to a dated version entry
- Never merge a PR that modifies code without a CHANGELOG entry
- Docs-only or chore PRs may skip CHANGELOG but must justify it in the PR description

## conversation_log.md (mandatory)

`docs/conversation_log.md` is the human-readable log of this project's AI-assisted journey. It exists to document the evolution of the project as a brownfield adoption case study.

**Rules — non-negotiable:**

- Every significant user request and the resulting AI decision must be logged
- Each entry follows this structure:
  ```
  ### [YYYY-MM-DD] Session N — <short title>
  **User asked:** <1–3 sentence summary of the request>
  **Decision:** <what was decided and why>
  **Artifacts created/modified:** <list of files>
  ```
- The log is append-only — never edit or delete past entries
- Add new entries at the bottom of the file
- Log AI decisions that involved trade-offs or alternatives considered

## Security

- **Never** hardcode credentials, API keys, or connection strings in source code
- All secrets via Pydantic Settings (`config/` module) loaded from `.env` (excluded from git)
- Route handlers MUST use `get_settings()` via `Depends()` — never call `os.getenv()` directly in endpoints
- `.env.example` is the reference for required variables — keep it updated
- Never commit `.env`, DB files (`*.db`), or generated embeddings

## CI/CD

- GitHub Actions workflows live in `.github/workflows/`
- Every PR triggers: lint (`ruff`), type check (`mypy`), tests (`pytest`)
- Deployment to Azure only from `main` branch after all checks pass

## Python Standards

- Formatter: `ruff format` (applied to `backend/app/`)
- Linter: `ruff check`
- Type hints required on all new public functions and methods
- Repository pattern: all DB access through `BaseRepository` ABC implementations; inject via `Depends()`
- Business logic in `services/`; never in `api/` route handlers or `repositories/`
- Config: use `Depends(get_settings)` in endpoints — never import settings or call `os.getenv()` directly

See [.github/instructions/python-modules.instructions.md](.github/instructions/python-modules.instructions.md) for module conventions.
