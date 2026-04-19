# SQL Server Setup Guide

This guide covers how SQL Server 2025 Express works in the RAG-Challenge project alongside PostgreSQL.

## Quick start

SQL Server starts automatically with `docker compose up`. The seed data loads into both databases:

```bash
docker compose up -d          # starts all 4 services
make seed                     # loads seed into both PostgreSQL AND SQL Server
```

Verify SQL Server has data:

```bash
curl -s "http://localhost:8000/api/v1/matches?source=sqlserver"
# Should return 2 matches (Euro 2024 Final, WC 2022 Final)

curl -s "http://localhost:8000/api/v1/competitions?source=sqlserver"
# Should return 2 competitions (UEFA Euro, FIFA World Cup)
```

## Architecture

```
┌──────────────────────────────────────────────────────────────┐
│  Frontend (React)  ──  Source: [PostgreSQL ▼] / SQL Server   │
│                            │                                  │
│  Backend (FastAPI)         │ ?source=sqlserver                │
│    ├── PostgresRepository ─┘                                  │
│    └── SQLServerRepository ──► SQL Server 2025 Express        │
│                                  ├── VECTOR(1536) columns     │
│                                  ├── VECTOR_DISTANCE()        │
│                                  └── No HNSW indexes (Express)│
└──────────────────────────────────────────────────────────────┘
```

The `source` parameter in the URL controls which database is queried. All API endpoints support both `postgres` and `sqlserver`.

## Docker configuration

**Image:** Custom build from `mcr.microsoft.com/mssql/server:2025-latest`

**Startup time:** ~30 seconds (vs ~5 seconds for PostgreSQL). The `setup.sh` entrypoint waits for SQL Server to be ready before running init scripts.

**Credentials (local dev only):**
| Variable | Default |
|----------|---------|
| `SQLSERVER_HOST` | `sqlserver` (Docker service name) |
| `SQLSERVER_DB` | `rag_challenge` |
| `SQLSERVER_USER` | `sa` |
| `SQLSERVER_PASSWORD` | `SqlServer_Local_Pwd123!` |

## Schema differences from PostgreSQL

The SQL Server schema was designed independently and uses different naming:

| Concept | PostgreSQL | SQL Server |
|---------|-----------|------------|
| Aggregation table | `events_details__quarter_minute` | `events_details__15secs_agg` |
| Time bucket column | `quarter_minute` | `_15secs` |
| Embedding column | `summary_embedding_t3_small` | `embedding_3_small` |
| Ada-002 column | `summary_embedding_ada_002` | `embedding_ada_002` |
| Primary key | Auto-increment `id` | Composite `(match_id, period, minute, _15secs)` |
| Extra tables | — | `lineups`, `players` (currently unused) |

The code handles both naming conventions transparently via the Repository Pattern — `PostgresEventRepository` and `SQLServerEventRepository` each know their own table/column names.

## Vector search

SQL Server 2025 supports native `VECTOR(1536)` columns and `VECTOR_DISTANCE()` for similarity search:

```sql
SELECT TOP 5
    id, match_id, summary,
    VECTOR_DISTANCE('cosine', embedding_3_small, CAST(@query_vec AS VECTOR(1536))) AS score
FROM events_details__15secs_agg
WHERE match_id = @match_id AND embedding_3_small IS NOT NULL
ORDER BY score ASC
```

### HNSW indexes — Express limitation

SQL Server 2025 **Express edition** does not support `CREATE VECTOR INDEX`. Vector searches use sequential scans via `VECTOR_DISTANCE()`. This is acceptable for the seed dataset (~700 rows per match) but would be slow for large datasets.

For production workloads or large datasets, use **SQL Server 2025 Developer or Enterprise edition** which supports:

```sql
-- Only works on Developer/Enterprise edition
CREATE VECTOR INDEX idx_embedding_hnsw
ON events_details__15secs_agg (embedding_3_small)
USING HNSW
WITH (METRIC = 'cosine', M = 16, EF_CONSTRUCTION = 64);
```

### Search algorithm support

| Algorithm | PostgreSQL | SQL Server |
|-----------|-----------|------------|
| Cosine | `<=>` operator + HNSW index | `VECTOR_DISTANCE('cosine', ...)` — sequential scan |
| Inner product | `<#>` operator + HNSW index | `VECTOR_DISTANCE('dot', ...)` — sequential scan |
| L2 Euclidean | `<->` operator | `VECTOR_DISTANCE('euclidean', ...)` — sequential scan |
| L1 Manhattan | Custom SQL | Not supported |

## Troubleshooting

### SQL Server container won't start
```bash
docker compose logs sqlserver    # check for errors
docker compose restart sqlserver # retry
```
Common cause: insufficient memory. SQL Server Express needs ~512 MB minimum.

### Seed load fails with "ntext to vector" error
This was a known issue (fixed in PR #52). If you see this error, update to the latest `develop` branch.

### Empty data after seed load
Check that both databases are healthy before seeding:
```bash
docker compose ps     # all 4 services should be healthy/running
make seed-force       # force re-seed both databases
```

### Switching source in the UI
Use the **Source** dropdown in the header bar. All pages (Explorer, Chat, Embeddings) will reload with data from the selected source.

## Files reference

| File | Description |
|------|-------------|
| `infra/docker/sqlserver/Dockerfile` | Custom SQL Server image build |
| `infra/docker/sqlserver/initdb/01-schema.sql` | Schema init script |
| `infra/docker/sqlserver/setup.sh` | Startup entrypoint |
| `backend/app/repositories/sqlserver.py` | SQL Server repository (all queries) |
| `backend/app/core/capabilities.py` | Capability matrix per source |
