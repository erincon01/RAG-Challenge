# Architecture

## Overview

RAG Challenge is a football match analysis system built on the
**Retrieval-Augmented Generation (RAG)** pattern. Users ask natural-language questions
about a match; the system retrieves the most semantically relevant match events,
builds a token-budgeted context, and sends it to an LLM to produce a grounded answer.

```
React Frontend  ──HTTP──►  FastAPI Backend  ──SQL──►  PostgreSQL / SQL Server
                                │                        (event_details + embeddings)
                                └──REST──►  OpenAI / Azure OpenAI
                                           (embeddings + chat completions)
```

---

## Backend Layer Architecture

The backend enforces a strict **one-way dependency** rule:
`api` → `services` → `repositories` → `domain`.
No layer may import from a layer above it.

```
backend/app/
├── api/v1/          ← HTTP layer: routing, request/response validation (Pydantic models)
├── services/        ← Business logic: orchestration, RAG pipeline, no I/O
├── repositories/    ← Data access: SQL queries, driver calls, no business logic
├── domain/          ← Pure Python: entities, exceptions, value objects
├── adapters/        ← External service clients (OpenAI / Azure OpenAI)
└── core/            ← Config (Pydantic Settings), dependency wiring (FastAPI Depends)
```

### `api/v1/` — HTTP Layer

Thin route handlers. Responsibility: parse HTTP request → call service → return HTTP response.
No business logic. No direct DB calls.

| Router | Prefix | Responsibility |
|--------|--------|----------------|
| `health.py` | `/api/v1/health` | Liveness + DB connectivity check |
| `matches.py` | `/api/v1/matches` | List and retrieve matches |
| `events.py` | `/api/v1/events` | Query event details for a match |
| `chat.py` | `/api/v1/chat` | Full RAG pipeline: search + LLM answer |
| `embeddings.py` | `/api/v1/embeddings` | Generate / inspect embeddings |
| `ingestion.py` | `/api/v1/ingestion` | Trigger data ingestion jobs |
| `statsbomb.py` | `/api/v1/statsbomb` | Statsbomb open-data proxy endpoints |
| `explorer.py` | `/api/v1/explorer` | Data explorer (ad-hoc queries) |
| `capabilities.py` | `/api/v1/capabilities` | Advertise supported sources/models |
| `models.py` | — | Shared Pydantic request/response schemas |

### `services/` — Business Logic Layer

Stateless classes injected via `Depends()`. All external calls go through injected
repositories or adapters — never direct driver calls.

| Service | Responsibility |
|---------|---------------|
| `SearchService` | Core RAG pipeline (translate → embed → search → context → LLM) |
| `IngestionService` | Download Statsbomb data and load into DB |
| `JobService` | Background job tracking for long-running ingestion |
| `DataExplorerService` | Ad-hoc data exploration queries |
| `StatsbombService` | Statsbomb open-data fetching and parsing |

### `repositories/` — Data Access Layer

All DB access goes through `BaseRepository` ABC. The factory pattern selects the
correct implementation at request time based on the `source` parameter.

```
BaseRepository (ABC)
├── MatchRepository (ABC)   ← get_by_id, get_all, search_events
└── EventRepository (ABC)   ← get_by_match, vector_search

PostgresRepositoryFactory   → PostgresMatchRepository, PostgresEventRepository
SQLServerRepositoryFactory  → SQLServerMatchRepository, SQLServerEventRepository
```

**Key rule:** repositories never return raw dicts or DB rows — they always return
domain entities from `domain/entities.py`.

### `domain/` — Pure Python Domain Model

No framework dependencies. Contains:

- **Entities** (`entities.py`): `Match`, `Competition`, `Season`, `Team`, `Stadium`,
  `Referee`, `Player`, `EventDetail`, `SearchResult`, `SearchRequest`, `ChatResponse`,
  `SearchAlgorithm` (enum), `EmbeddingModel` (enum)
- **Exceptions** (`exceptions.py`): `EntityNotFoundError`, `ValidationError`,
  `DatabaseConnectionError`, `EmbeddingGenerationError`

### `adapters/` — External Service Clients

`OpenAIAdapter` wraps OpenAI / Azure OpenAI. Instantiated per-request
(see TODO in constitution: evaluate module-level singleton).
Provides:
- `create_embedding(text, model)` → `List[float]`
- `create_chat_completion(messages, ...)` → `str`
- Retry logic with exponential backoff (up to 5 retries, max 60 s)

### `core/` — Configuration and DI Wiring

- `config.py`: re-exports `get_settings()` → `Settings` (Pydantic Settings singleton)
- `dependencies.py`: FastAPI `Depends()` providers for repositories
- `capabilities.py`: `normalize_source()` — maps raw source strings to canonical `"postgres"` / `"sqlserver"`

---

## RAG Pipeline (6 steps)

```
User question
     │
     ▼
① translate_to_english(question)          ← LLM call if language ≠ "english"
     │
     ▼
② create_embedding(normalized_question)   ← OpenAI / Azure OpenAI embeddings API
     │
     ▼
③ vector_search(embedding, top_n)         ← pgvector <=> / VECTOR_DISTANCE()
     │
     ▼
④ build_context(results, max_tokens)      ← token-budget enforcement
     │
     ▼
⑤ create_chat_completion(context, q)      ← OpenAI / Azure OpenAI chat completions
     │
     ▼
ChatResponse(answer, sources, tokens_used)
```

**Token budget rule:** step ④ iterates search results in rank order, adding each
event summary to the context until `max_input_tokens` would be exceeded.
Remaining results are discarded — never truncated mid-sentence.

---

## Database Model

Two supported backends. Tables are logically equivalent; SQL dialects differ.

### PostgreSQL (`pgvector`)

```sql
events_details__quarter_minute
  id                          SERIAL PRIMARY KEY
  match_id                    INT
  period                      INT
  minute                      INT
  quarter_minute              INT        -- 1-4 (15-second segments)
  count                       INT
  json_data                   TEXT
  summary                     TEXT
  summary_embedding_ada_002   vector(1536)
  summary_embedding_t3_small  vector(1536)
  summary_embedding_t3_large  vector(3072)
```

Vector search operators: `<=>` (cosine), `<#>` (inner product), `<->` (L2/Euclidean)

HNSW indexes on each embedding column for sub-linear search at scale.

### SQL Server (`VECTOR` type)

```sql
events_details__15secs_agg
  -- same logical columns
  summary_embedding_t3_small  VECTOR(1536)
```

Vector search: `VECTOR_DISTANCE('cosine', col, @query_vector)`

---

## Configuration

All configuration is loaded at startup via `config/settings.py` (Pydantic Settings).
The `.env` file is the single source of truth for local development.

```
config/
└── settings.py   ← Settings, DatabaseConfig, OpenAIConfig, RepositoryConfig

Loaded by: backend/app/core/config.py → get_settings() → used via Depends()
```

**Rule:** Route handlers MUST use `Depends(get_settings)`.
Never call `os.getenv()` directly in `api/` or `services/`.

---

## Frontend

React TypeScript + Tailwind CSS (`frontend/webapp/`).
Communicates **exclusively** via REST calls to `backend/app/api/v1/`.
No direct DB or OpenAI access from the frontend.

---

## Infrastructure (Local Dev)

`docker-compose.yml` at project root is the single source of truth for local services:

```yaml
services:
  postgres:    image: pgvector/pgvector:pg16  port: 5432
  sqlserver:   image: mcr.microsoft.com/mssql/server:2022  port: 1433
  backend:     build: ./backend   port: 8000
  frontend:    build: ./frontend  port: 3000
```

Start everything:
```bash
docker compose up --build
```

Backend only (with hot-reload):
```bash
cd backend && uvicorn app.main:app --reload --port 8000
```
