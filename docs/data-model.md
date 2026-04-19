# Data Model

## Source Data — StatsBomb Open Data

The project ingests data from the [StatsBomb open-data](https://github.com/statsbomb/open-data)
GitHub repository. See [statsbomb-intro.md](statsbomb-intro.md) for the raw data structure.

The ingestion pipeline transforms the raw JSON into a relational model optimised for
vector search.

---

## Internal Domain Entities

```
Competition ◄──── Match ────► Season
                   │
          ┌────────┼────────┐
          ▼        ▼        ▼
      home_team  away_team  Stadium
       (Team)    (Team)     Referee
                   │
                   ▼
             EventDetail ──► SearchResult
              (quarter-      (similarity_score,
               minute agg)    rank)
```

### Entity Summary

| Entity | Key Fields | Notes |
|--------|-----------|-------|
| `Competition` | competition_id, country, name | Read-only metadata |
| `Season` | season_id, name | Linked to matches |
| `Team` | team_id, name, gender, country, manager | Home/away reference |
| `Stadium` | stadium_id, name, country | Match venue |
| `Referee` | referee_id, name, country | Match official |
| `Player` | player_id, player_name, jersey_number, position_id, position_name, country_id, country_name | Roster data from lineups |
| `Match` | match_id, match_date, competition, season, home_team, away_team, home_score, away_score, result, match_week, stadium, referee, json_data | Central entity — has `display_name` property |
| `EventDetail` | id, match_id, period, minute, quarter_minute, count, json_data, summary, embeddings (×3) | Aggregated events at 15-second intervals |
| `SearchResult` | event (EventDetail), similarity_score (float), rank (int) | Wrapper returned by vector search |

### Enums

| Enum | Values | Purpose |
|------|--------|---------|
| `SearchAlgorithm` | COSINE, INNER_PRODUCT, L1_MANHATTAN, L2_EUCLIDEAN | Distance function selector |
| `EmbeddingModel` | ADA_002, T3_SMALL, T3_LARGE | OpenAI embedding model selector |

### Request/Response Entities

| Entity | Purpose |
|--------|---------|
| `SearchRequest` | RAG query input — validated in `__post_init__` (top_n: 1-100, temperature: 0-2) |
| `ChatResponse` | RAG answer output — question, normalized_question, answer, search_results, match_info, metadata |

All entities are **pure Python dataclasses** in `backend/app/domain/entities.py`
with zero framework imports.

---

## Database Schema

Two backends maintain logically equivalent schemas.

### PostgreSQL (pgvector)

#### Table: `matches`

| Column | Type | Notes |
|--------|------|-------|
| match_id | INT (PK) | StatsBomb match ID |
| match_date | DATE | |
| competition_id | INT | |
| competition_name | VARCHAR | |
| season_id | INT | |
| season_name | VARCHAR | |
| home_team_id | INT | |
| home_team_name | VARCHAR | |
| away_team_id | INT | |
| away_team_name | VARCHAR | |
| home_score | INT | |
| away_score | INT | |
| stadium_id | INT | Nullable |
| stadium_name | VARCHAR | Nullable |
| referee_id | INT | Nullable |
| referee_name | VARCHAR | Nullable |
| json_data | TEXT | Full StatsBomb JSON |

#### Table: `events_details__quarter_minute`

| Column | Type | Notes |
|--------|------|-------|
| id | SERIAL (PK) | Auto-increment |
| match_id | INT (FK) | → matches.match_id |
| period | INT | 1 = first half, 2 = second half |
| minute | INT | Match clock minute |
| quarter_minute | INT | 1-4 (15-second segments within the minute) |
| count | INT | Number of raw events aggregated |
| json_data | TEXT | Aggregated raw event JSON |
| summary | TEXT | LLM-generated text summary |
| summary_embedding_ada_002 | vector(1536) | text-embedding-ada-002 |
| summary_embedding_t3_small | vector(1536) | text-embedding-3-small |
| summary_embedding_t3_large | vector(3072) | text-embedding-3-large |

**Indexes:** HNSW indexes on each embedding column for sub-linear search.

**Vector operators:**

| Algorithm | Operator | Distance |
|-----------|----------|----------|
| Cosine | `<=>` | 1 − cosine_similarity |
| Inner product | `<#>` | Negative inner product |
| L2 Euclidean | `<->` | Euclidean distance |
| L1 Manhattan | Custom SQL | Sum of absolute differences |

### SQL Server (VECTOR type)

Same logical schema with different naming conventions. The code handles both via the Repository Pattern.

| Aspect | PostgreSQL | SQL Server |
|--------|-----------|------------|
| Vector type | `vector(N)` (pgvector extension) | `VECTOR(N)` (native, SQL Server 2025) |
| Search function | Operators (`<=>`, `<#>`, `<->`) | `VECTOR_DISTANCE('cosine', col, @vec)` |
| Vector indexes | HNSW (pgvector) | Not available (Express edition) |
| Active embedding model | text-embedding-3-small | text-embedding-3-small |
| L1 Manhattan | Supported | Not supported |

**Schema naming differences:**

| Concept | PostgreSQL | SQL Server |
|---------|-----------|------------|
| Aggregation table | `events_details__quarter_minute` | `events_details__15secs_agg` |
| Time bucket column | `quarter_minute` | `_15secs` |
| Embedding column | `summary_embedding_t3_small` | `embedding_3_small` |
| Primary key | Auto-increment `id` | Composite `(match_id, period, minute, _15secs)` |
| Extra tables | — | `lineups`, `players` (unused) |

See [docs/sql-server-setup.md](sql-server-setup.md) for the full SQL Server guide.

---

## Data Aggregation

Raw StatsBomb events (individual actions like passes, shots, tackles) are aggregated
at the **quarter-minute** level (15-second intervals). Each aggregated record contains:

1. **count** — Number of raw events in this interval.
2. **json_data** — Combined raw event JSON.
3. **summary** — Natural language summary generated by an LLM describing what happened
   in that 15-second window.
4. **embeddings** — Vector representations of the summary, one per supported model.

This aggregation reduces the search space from thousands of individual events per match
to a manageable set of ~360 quarter-minute buckets (90 minutes × 4 segments).

---

## Data Distribution

See [data-distribution.md](data-distribution.md) for statistics on competitions
and matches by region.
