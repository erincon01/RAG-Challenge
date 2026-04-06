# Data Layer Specification

**Domain:** data  
**Status:** Current system (brownfield baseline)  
**Last updated:** 2026-04-02  
**ADR references:**
- [ADR-001 Layered Architecture](../../../docs/adr/ADR-001-layered-architecture.md)
- [ADR-003 pgvector Migration](../../../docs/adr/ADR-003-pgvector-migration.md)

---

## Overview

The data layer follows a Repository Pattern with abstract base classes and
dual implementations (PostgreSQL + SQL Server). Domain entities are pure Python
dataclasses with zero framework imports.

---

## Domain Entities

### Enums

| Enum | Values | Purpose |
|------|--------|---------|
| `SearchAlgorithm` | COSINE, INNER_PRODUCT, L1_MANHATTAN, L2_EUCLIDEAN | Vector search algorithm selector |
| `EmbeddingModel` | ADA_002, T3_SMALL, T3_LARGE | Embedding model selector |

### Core Entities

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `Competition` | competition_id, country, name | Metadata only |
| `Season` | season_id, name | Metadata only |
| `Team` | team_id, name, gender, country, manager, manager_country | Full team data |
| `Stadium` | stadium_id, name, country | Venue metadata |
| `Referee` | referee_id, name, country | Official metadata |
| `Player` | player_id, player_name, jersey_number, country_id, country_name, position_id, position_name | Roster data |
| `Match` | match_id, match_date, competition, season, home_team, away_team, home_score, away_score, result, match_week, stadium, referee, json_data | Central entity; has `display_name` property |
| `EventDetail` | id, match_id, period, minute, quarter_minute, count, json_data, summary, summary_embedding_ada_002, summary_embedding_t3_small, summary_embedding_t3_large, summary_embedding_e5 | Aggregated at quarter-minute level; has `time_description` property |
| `SearchResult` | event (EventDetail), similarity_score (float), rank (int) | Wrapper for search hits |
| `SearchRequest` | match_id, query, language, search_algorithm, embedding_model, top_n, temperature, max_input_tokens, max_output_tokens, include_match_info, system_message | Validated in `__post_init__` |
| `ChatResponse` | question, normalized_question, answer, search_results, match_info, metadata | Complete RAG response |

### Domain Exceptions

| Exception | Base | Constructor | Usage |
|-----------|------|-------------|-------|
| `DomainException` | Exception | — | Base for all domain errors |
| `EntityNotFoundError` | DomainException | (entity_type, entity_id) | Lookup misses |
| `ValidationError` | DomainException | — | Domain validation failures |
| `DatabaseConnectionError` | DomainException | — | DB connectivity issues |
| `EmbeddingGenerationError` | DomainException | — | OpenAI API failures |

---

## Repository Pattern

### Abstract Interfaces (`base.py`)

```
BaseRepository (ABC)
├── get_connection() → Iterator[Connection]  (context manager)
├── test_connection() → bool
└── get_tables_info() → List[Dict[str, Any]]

MatchRepository(BaseRepository)
├── get_by_id(match_id) → Optional[Match]
├── get_all(competition_name, season_name, limit) → List[Match]
├── get_competitions() → List[Competition]
├── get_teams(match_id, limit) → List[Dict[str, Any]]
└── get_players(match_id, limit) → List[Dict[str, Any]]

EventRepository(BaseRepository)
├── get_events_by_match(match_id, limit) → List[EventDetail]
├── search_by_embedding(search_request, query_embedding) → List[SearchResult]
└── get_event_by_id(event_id) → Optional[EventDetail]

RepositoryFactory(ABC)
├── create_match_repository() → MatchRepository
└── create_event_repository() → EventRepository
```

### PostgreSQL Implementation (`postgres.py`)

- Uses `psycopg2` with `RealDictCursor`.
- Parameterized queries with `%s` placeholders (NEVER f-strings with user data).
- Vector search uses pgvector operators: `<=>` (cosine), `<#>` (inner product), `<->` (L2), custom for L1.
- Factory: `PostgresRepositoryFactory`.

### SQL Server Implementation (`sqlserver.py`)

- Uses `pyodbc`.
- Parameterized queries with `?` placeholders (NEVER f-strings with user data).
- Vector search uses SQL Server VECTOR type functions.
- Limited algorithms: no L1 Manhattan support.
- Factory: `SQLServerRepositoryFactory`.

### Dual-Repository Pattern

```
┌─────────────┐     source="postgres"     ┌───────────────────────┐
│  API Route  │─────────────────────────▶ │ PostgresRepositoryFactory │
│  (Depends)  │                           └──────────┬────────────┘
│             │     source="sqlserver"    ┌───────────▼──────────────┐
│             │─────────────────────────▶ │ SQLServerRepositoryFactory │
└─────────────┘                           └──────────────────────────┘
```

- Source selection via `source` query parameter (default: "postgres").
- `normalize_source()` maps aliases to canonical names.
- Capability validation before search: `validate_search_capabilities(source, model, algorithm)`.

---

## Database Schema

### PostgreSQL (pgvector)

**Table: `matches`**
- Primary key: `match_id` (int)
- Full match data with relation fields (competition, season, teams, stadium, referee)
- JSON column: `json_data` (original StatsBomb JSON)

**Table: `event_details`**
- Primary key: `id` (int)
- Foreign key: `match_id` → `matches`
- Aggregated at quarter-minute granularity
- Embedding columns (vector type):
  - `summary_embedding_ada_002` (vector(1536))
  - `summary_embedding_t3_small` (vector(1536))
  - `summary_embedding_t3_large` (vector(3072))
- Text column: `summary` (LLM-generated text summary of events)

### SQL Server

- Same logical schema as PostgreSQL.
- Uses SQL Server `VECTOR` type for embedding columns.
- Missing `text-embedding-3-large` support (only ada-002 and t3-small).
- Missing L1 Manhattan distance algorithm.

---

## Data Flow

### Ingestion Pipeline

```
StatsBomb GitHub API → Download JSON → Load to DB → Aggregate → Embed
```

1. **Download:** Fetch competitions/matches/events/lineups JSON from StatsBomb open-data GitHub repo.
2. **Load:** Parse JSON and insert into PostgreSQL or SQL Server.
3. **Aggregate:** Group raw events by quarter-minute, generate text summaries via LLM.
4. **Embed:** Call OpenAI API to generate vector embeddings for each summary.

### Services Involved

| Service | Purpose | Uses Repository? |
|---------|---------|-----------------|
| `StatsBombService` | Remote catalog discovery, JSON download | No (HTTP only) |
| `IngestionService` | Full pipeline orchestration | No (direct DB access) |
| `JobService` | Background job tracking (in-memory) | No (in-memory dict) |
| `DataExplorerService` | Read-only metadata queries | YES (injected MatchRepository) |
| `SearchService` | RAG pipeline (query → answer) | YES |

### Known Deviations

- `IngestionService` bypasses the Repository Pattern and connects directly to databases
  using `psycopg2`/`pyodbc`. This is intentional (different use case — bulk ingestion).
