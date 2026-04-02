# RAG-Challenge

Football analytics RAG system built on StatsBomb open data. Users ask natural-language questions about matches; the system retrieves relevant event summaries via vector search and generates grounded answers with Azure OpenAI.

## Tech Stack

- **Backend**: Python 3.11 / FastAPI — layered architecture (`api → services → repositories → domain → adapters → core`)
- **Frontend**: React 19 / TypeScript 5.9 / Vite / TailwindCSS
- **Databases**: PostgreSQL 17 + pgvector, SQL Server 2025 Express
- **AI**: Azure OpenAI (GPT-4o chat, text-embedding-3-small vectors)
- **Infrastructure**: Docker Compose, devcontainer v2
- **Tests**: pytest (backend), vitest (frontend — planned)

## Constitution

The project constitution at `.specify/memory/constitution.md` (v2.0.0) defines 10 non-negotiable principles. Read it before making architectural decisions.

## Key Commands

```bash
# Tests
cd backend && pytest tests/ -v
cd backend && pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# Lint & format
ruff check backend/app
ruff format backend/app

# Type check
mypy backend/app

# Pre-commit hooks
pre-commit run --all-files

# Docker
docker compose up --build

# Spec-kit: create new feature
.specify/scripts/powershell/create-new-feature.ps1 'Feature description'
.specify/scripts/bash/create-new-feature.sh 'Feature description'
```

## Development Rules

- **TDD required**: write failing test first, then implement (Red → Green → Refactor)
- **Coverage >= 80%** on `backend/app/` — enforced by CI
- **Conventional commits**: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`
- **No direct push** to `main` or `develop` — all changes via PR
- **CHANGELOG.md** must be updated under `[Unreleased]` in every code PR
- **conversation_log.md** must be updated for every AI-assisted session
- **No secrets in code** — all config via Pydantic Settings (`config/settings.py`)
- **Parameterized SQL only** — no f-string SQL, no string interpolation in queries
- **Layer boundaries** — route handlers must not contain SQL or business logic

## Spec-Driven Development

New features follow the SDD workflow via spec-kit:

1. Feature specs live in `specs/NNN-feature-name/` (spec.md, plan.md, tasks.md)
2. Every plan.md must include a Constitution Check against all 10 principles
3. Commit spec artifacts before implementation code

See `specs/README.md` for the full workflow.

## Key References

- **Governance**: `.github/copilot-instructions.md` — detailed project norms
- **Architecture**: `docs/architecture.md` — backend layers, RAG pipeline
- **ADRs**: `docs/adr/` — 4 accepted architecture decision records
- **Git workflow**: `.github/instructions/git-workflow.instructions.md`
- **TDD patterns**: `.github/instructions/tdd.instructions.md`
- **CI pipeline**: `.github/workflows/ci.yml` — lint, typecheck, tests with coverage gate
