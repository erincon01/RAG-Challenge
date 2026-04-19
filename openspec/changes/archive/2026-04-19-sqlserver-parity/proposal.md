## Why

SQL Server is supposed to be a first-class alternative to PostgreSQL, but a developer who switches to `source=sqlserver` gets empty pages. The seed data loads into PostgreSQL but fails silently for SQL Server. There are no HNSW vector indexes, schema naming differs from PostgreSQL (different table and column names), and no setup documentation exists. This prevents the project from demonstrating its multi-database RAG architecture — a key didactic feature. Addresses issues #33 and #52.

## What Changes

- **Fix seed loading into SQL Server** — debug and resolve why `seed_load.py --source sqlserver` produces empty tables
- **Add HNSW vector indexes** to `events_details__15secs_agg` for `embedding_3_small` (SQL Server 2025 native)
- **Create setup documentation** — `docs/sql-server-setup.md` with Docker setup, schema differences, and troubleshooting
- **Update existing docs** — `docs/getting-started.md`, `docs/data-model.md` with SQL Server specifics
- **Add E2E validation** — verify Explorer and Chat work with `source=sqlserver` after seed
- **Document schema differences** — explain why table/column names differ between PostgreSQL and SQL Server (no rename — too risky for a brownfield project)

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities
- `data`: seed loading must work for both postgres and sqlserver; HNSW indexes added to SQL Server schema
- `infra`: SQL Server init script updated with vector indexes; documentation added

## Impact

- **Infra** (`infra/docker/sqlserver/initdb/01-schema.sql`): add HNSW index creation
- **Scripts** (`backend/scripts/seed_load.py`): debug and fix SQL Server loading path
- **Docs** (`docs/sql-server-setup.md`, `docs/getting-started.md`, `docs/data-model.md`): new and updated docs
- **Tests** (`frontend/webapp/tests/e2e/cross-cutting.spec.ts`): verify sqlserver source with data
- **Backward compatibility**: fully backward-compatible — adds indexes and docs, no schema column changes
- **Affected layers**: Infra (schema), Scripts (seed), Docs, E2E Tests
- **Test impact**: existing 530 backend tests unaffected; E2E cross-cutting test updated
