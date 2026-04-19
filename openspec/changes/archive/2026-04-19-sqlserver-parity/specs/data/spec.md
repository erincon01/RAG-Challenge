## MODIFIED Requirements

### Requirement: Seed data loads into both databases
The seed loader (`scripts/seed_load.py`) SHALL load pre-computed data into both PostgreSQL and SQL Server when invoked with `--source both`. After a successful seed load, both databases MUST have identical match counts, aggregation row counts, and embedding coverage.

#### Scenario: Seed loads into SQL Server successfully
- **GIVEN** Docker stack is running with both databases healthy
- **WHEN** `python -m scripts.seed_load --source sqlserver` is executed
- **THEN** SQL Server SHALL contain 2 matches, their events, aggregations, summaries, and embeddings

#### Scenario: API returns data from SQL Server after seed
- **GIVEN** seed data has been loaded into SQL Server
- **WHEN** `GET /api/v1/competitions?source=sqlserver` is requested
- **THEN** the response SHALL contain at least 2 competitions (UEFA Euro, FIFA World Cup)

#### Scenario: RAG search works on SQL Server
- **GIVEN** seed data with embeddings has been loaded into SQL Server
- **WHEN** `POST /api/v1/chat/search?source=sqlserver` is sent with a valid query
- **THEN** the response SHALL contain an answer with search results

### Requirement: SQL Server HNSW vector indexes
The SQL Server schema SHALL create HNSW vector indexes on the `embedding_3_small` column of `events_details__15secs_agg` for efficient vector similarity search.

#### Scenario: HNSW index exists after schema init
- **GIVEN** SQL Server container starts with init script
- **WHEN** schema initialization completes
- **THEN** an HNSW vector index SHALL exist on `events_details__15secs_agg.embedding_3_small`

#### Scenario: Vector search uses index
- **GIVEN** HNSW index exists and data is loaded
- **WHEN** a vector similarity search is executed
- **THEN** the query SHALL use the HNSW index (sub-linear search time)
