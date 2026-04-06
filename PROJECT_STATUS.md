# Project Status — RAG-Challenge

**Last Updated:** 2026-04-06
**Branch:** `develop`
**Governance:** [OpenSpec](https://github.com/Fission-AI/OpenSpec) (spec-driven development)

---

## Summary

| Area | Status |
|------|--------|
| Backend (FastAPI) | Complete — layered architecture, DI via Depends(), 470+ tests, 82% coverage |
| Frontend (React TS) | Complete — 7 pages, type-safe API client |
| Databases | PostgreSQL 17 + pgvector, SQL Server 2025 Express |
| CI pipeline | Complete — ruff + mypy + pytest 80% coverage gate |
| OpenSpec governance | Complete — 4 system specs, 5 archived changes, full workflow |
| Pre-commit hooks | Configured — ruff lint + format |
| DevContainer | Working — auto-starts all services |

## Resolved in latest session (2026-04-06)

- CORS hardened — `allow_origins=["*"]` replaced with configurable `CORS_ORIGINS` env var
- DataExplorerService refactored to use Repository Pattern (no more raw psycopg2/pyodbc)
- Health/capabilities handlers migrated to Depends() injection
- Token budget guard added to RAG pipeline (tiktoken-based, truncates context if over budget)
- Test naming convention enforced across all 470+ tests
- Pre-commit config, frontend .env.example added
- OpenSpec verification rules and worktree parallel workflow documented

## Pending

### Medium priority

| Item | Description |
|------|-------------|
| CD pipeline | `cd.yml` is placeholder (echo stubs) |
| Integration tests | `backend/tests/integration/` is empty — needs live DB |
| Frontend tests | No vitest or playwright configured |
| IngestionService refactor | Direct DB access, should use Repository Pattern |

### Low priority

| Item | Description |
|------|-------------|
| Structured logging | request_id, match_id, latency, token usage |
| Query caching | Cache for frequently asked questions |
| Task runner | `Taskfile.yml` or `justfile` for common commands |
| Release to main | Merge develop → main with tag v0.2.0 |
