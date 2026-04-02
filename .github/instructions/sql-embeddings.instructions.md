---
description: "Use when writing, reviewing, or generating SQL scripts for PostgreSQL/pgvector or Azure SQL Server. Covers embedding pipeline patterns, vector search operators, parameterized queries, and naming conventions."
applyTo: "{postgres,sqlserver}/**/*.sql"
---

# SQL and Embedding Pipeline Conventions

## Database Targets

This project uses **two SQL backends** — always be explicit about which target a script is for:

| Directory | Target | Notes |
|-----------|--------|-------|
| `postgres/` | Azure PostgreSQL + pgvector | Vector similarity search |
| `sqlserver/` | Azure SQL Server | T-SQL, no native vector ops |

Never mix T-SQL syntax (`TOP`, `NOCOUNT`) with PostgreSQL syntax (`LIMIT`, `RETURNING`) in the same script.

## Parameterized Queries (mandatory)

Never concatenate user input or variables directly into SQL strings.

```python
# CORRECT
cursor.execute(
    "SELECT * FROM events WHERE match_id = %s AND minute = %s",
    (match_id, minute)
)

# WRONG — SQL injection risk
cursor.execute(f"SELECT * FROM events WHERE match_id = {match_id}")
```

Use `%s` placeholders for psycopg2, `?` for pyodbc/sqlite3.

## pgvector Operators

```sql
-- Cosine similarity (most common for embeddings)
ORDER BY embedding <=> query_embedding

-- L2 distance
ORDER BY embedding <-> query_embedding

-- Inner product
ORDER BY embedding <#> query_embedding
```

Use `<=>` (cosine) by default unless there is a specific reason to use another metric.

## Embedding Column Naming

- Embedding columns: `embedding` (singular)
- Embedding model column: `embedding_model`
- Summary/text used for embedding: `summary`

## Standard Embedding Search Template (PostgreSQL)

```sql
SELECT
    match_id,
    minute,
    summary,
    1 - (embedding <=> %(query_embedding)s::vector) AS similarity_score
FROM event_details_embeddings
WHERE match_id = %(match_id)s
ORDER BY embedding <=> %(query_embedding)s::vector
LIMIT %(top_k)s;
```

## Index Requirements

All tables with an `embedding` column must have a vector index:

```sql
-- IVFFlat for large datasets (tune lists to sqrt(row_count))
CREATE INDEX ON event_details_embeddings
USING ivfflat (embedding vector_cosine_ops)
WITH (lists = 100);

-- HNSW for smaller/medium datasets (faster queries, more memory)
CREATE INDEX ON event_details_embeddings
USING hnsw (embedding vector_cosine_ops);
```

## DDL Conventions

- All DDL scripts: idempotent (`CREATE TABLE IF NOT EXISTS`, `DROP INDEX IF EXISTS`)
- Tables use `snake_case`
- Scripts numbered with zero-padded prefix: `00_tables_setup.sql`, `01_load_data.sql`
- Always include a rollback/cleanup comment block at the top of destructive scripts

## Azure SQL Specifics

- Use `NVARCHAR` for text (not `VARCHAR`) to support Unicode
- No `RETURNING` clause — use `OUTPUT INSERTED.*` instead
- Stored procedures for embedding generation use `sp_` prefix

## Testing SQL Scripts

- Test against a local SQLite DB before running against Azure
- Keep test data sets small (1–2 matches) during development
- Document the `match_id` values used in development comments:
  ```sql
  -- France vs Argentina: match_id = 3869685
  -- England vs Spain:    match_id = 3943043
  ```
