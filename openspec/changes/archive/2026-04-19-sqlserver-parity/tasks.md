## 1. Debug and fix seed loading into SQL Server

- [x] 1.1 Run `docker compose exec backend python -m scripts.seed_load --source sqlserver --force` and capture the error output
- [x] 1.2 Identify the failure point in the SQL Server loading path (matches, events, aggregations, summaries, or embeddings)
- [x] 1.3 Fix the seed_load.py SQL Server path so data loads successfully
- [x] 1.4 Verify: `curl /api/v1/matches?source=sqlserver` returns 2 seed matches
- [x] 1.5 Verify: `curl /api/v1/competitions?source=sqlserver` returns competitions

## 2. Add HNSW vector indexes to SQL Server schema

- [x] 2.1 Attempted `CREATE VECTOR INDEX` — SQL Server 2025 Express does not support vector indexes. Documented limitation in schema and docs.
- [x] 2.2 Added comment to `infra/docker/sqlserver/initdb/01-schema.sql` documenting the Express edition limitation
- [x] 2.3 Vector search works via `VECTOR_DISTANCE()` with sequential scan (acceptable for seed dataset size)
- [x] 2.4 Fixed `SQLServerEventRepository.search_by_embedding` — same pyodbc ntext-to-vector cast issue as seed_load

## 3. Documentation

- [x] 3.1 Create `docs/sql-server-setup.md` with: Docker setup, schema overview, naming differences from PostgreSQL, seed loading, troubleshooting (slow startup, ODBC driver)
- [x] 3.2 Update `docs/getting-started.md` with SQL Server-specific notes (startup time, verification commands)
- [x] 3.3 Update `docs/data-model.md` with a mapping table: PostgreSQL table/column names vs SQL Server equivalents

## 4. E2E validation

- [x] 4.1 Update `frontend/webapp/tests/e2e/cross-cutting.spec.ts` US-23 to verify SQL Server has data (not just empty page)
- [x] 4.2 Run E2E tests: `cd frontend/webapp && npx playwright test cross-cutting.spec.ts` (2 passed)
- [x] 4.3 Test RAG search on SQL Server: `POST /api/v1/chat/search?source=sqlserver` returns an answer

## 5. Final validation

- [x] 5.1 Run backend tests: `cd backend && pytest tests/ -v` (530 passed)
- [x] 5.2 Run full E2E suite: `cd frontend/webapp && npx playwright test` (23 passed, 1 skipped)
- [x] 5.3 Update CHANGELOG.md under `## [Unreleased]`
