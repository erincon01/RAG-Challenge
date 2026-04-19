## Context

The project uses a dual-database architecture: PostgreSQL (pgvector) and SQL Server 2025 (native VECTOR). Both are in `docker-compose.yml`, both have init scripts, and the API supports `?source=sqlserver` on all endpoints. However, after seed loading, SQL Server has no data — the seed_load script's SQL Server path either fails silently or never runs the aggregation/summary/embedding update steps correctly.

Key schema differences:
- PostgreSQL aggregation table: `events_details__quarter_minute`, column `quarter_minute`, embedding `summary_embedding_t3_small`
- SQL Server aggregation table: `events_details__15secs_agg`, column `_15secs`, embedding `embedding_3_small`
- SQL Server has extra tables: `lineups`, `players` (unused by seed)
- SQL Server has no HNSW vector indexes

## Goals / Non-Goals

**Goals:**
- Fix seed_load.py so `make seed` populates both databases with identical data
- Add HNSW indexes to SQL Server schema for vector search performance
- Create `docs/sql-server-setup.md` as a standalone developer guide
- Validate with E2E tests that Explorer/Chat work with `source=sqlserver`
- Document schema naming differences

**Non-Goals:**
- Renaming SQL Server tables/columns to match PostgreSQL (too risky, breaks existing deployments)
- Adding `lineups`/`players` tables to PostgreSQL (separate future work)
- Performance benchmarking (HNSW vs full scan) — document as future work
- Changing the Repository Pattern or DI layer (code already handles both sources)

## Decisions

### 1. Keep different table/column names, document why
The schema was designed independently for each database before the project adopted conventions. Renaming `events_details__15secs_agg` to `events_details__quarter_minute` on SQL Server would require:
- Schema migration on any existing SQL Server databases
- Updating every SQL query in the SQL Server repository
- Risk of breaking the `seed_load.py` position-matching logic

**Decision:** Keep names as-is. Document the mapping in `docs/data-model.md` and `docs/sql-server-setup.md`.

### 2. HNSW index syntax for SQL Server 2025
SQL Server 2025 supports `CREATE VECTOR INDEX ... USING HNSW`. Parameters:
- `METRIC = 'cosine'` — matches our primary search algorithm
- `M = 16` — graph connectivity (default, good for ~1K vectors)
- `EF_CONSTRUCTION = 64` — build-time quality (default)

Only one index needed: on `embedding_3_small` (the only active model).

### 3. Debug seed_load SQL Server path, not rewrite
The seed_load.py already has SQL Server support. The issue is likely:
- The `IngestionService._load_matches` / `_load_events` / `_build_aggregations` methods may not work correctly with the SQL Server connection inside Docker
- Or the `_apply_summaries_and_embeddings` step may fail on the SQL Server column mapping

**Decision:** Debug the existing code path, fix the specific failure, don't rewrite.

## File change list

| File | Status | Description |
|------|--------|-------------|
| `infra/docker/sqlserver/initdb/01-schema.sql` | (modified) | Add HNSW vector index on `embedding_3_small` |
| `backend/scripts/seed_load.py` | (modified) | Fix SQL Server loading path |
| `docs/sql-server-setup.md` | (new) | Dedicated SQL Server setup guide |
| `docs/getting-started.md` | (modified) | Add SQL Server notes and troubleshooting |
| `docs/data-model.md` | (modified) | Document schema differences between PG and SQL Server |
| `frontend/webapp/tests/e2e/cross-cutting.spec.ts` | (modified) | Verify sqlserver source has data after seed |
| `CHANGELOG.md` | (modified) | Update Unreleased section |

## Risks / Trade-offs

- **[SQL Server 2025 HNSW syntax may differ]** → Verified against MS documentation. The syntax is `CREATE VECTOR INDEX ... USING HNSW WITH (METRIC = 'cosine', M = 16, EF_CONSTRUCTION = 64)`.
- **[seed_load fix may reveal deeper IngestionService bugs]** → If the fix is complex, we document it and create a follow-up issue rather than scope-creeping.
- **[Schema naming confusion persists]** → Mitigated by clear documentation with a mapping table.

## Rollback strategy

- Revert SQL Server schema changes (drop index if created)
- Revert seed_load.py changes
- Remove new docs files
- No database data changes to undo (seed can be re-run)
