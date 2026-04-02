# API Layer Specification

**Domain:** api  
**Status:** Current system (brownfield baseline)  
**Last updated:** 2026-04-02  
**ADR references:** [ADR-001 Layered Architecture](../../../docs/adr/ADR-001-layered-architecture.md)

---

## Overview

The API layer exposes a RESTful interface via FastAPI under the `/api/v1/` prefix.
All route handlers MUST delegate to the service layer; they SHALL NOT contain business logic,
direct database access, or adapter imports.

---

## Endpoints

### Health

| Method | Path | Response | Purpose |
|--------|------|----------|---------|
| GET | `/api/v1/health` | `HealthResponse` | Service status, timestamp, environment, version, checks |
| GET | `/api/v1/health/ready` | `ReadinessResponse` | Database connectivity check (ready: bool) |

**Behavior:**
- Given the backend is running, When `GET /health` is called, Then it MUST return HTTP 200 with `status`, `timestamp`, `environment`, `version`, and `checks` fields.
- Given the database is unreachable, When `GET /health/ready` is called, Then it MUST return `ready: false` with individual check results.

### Competitions and Matches

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/competitions` | `source` | `List[CompetitionResponse]` |
| GET | `/api/v1/matches` | `source`, `competition_name`, `season_name`, `limit` | `List[MatchSummaryResponse]` |
| GET | `/api/v1/matches/{match_id}` | `source` | `MatchDetailResponse` |

**Behavior:**
- Given valid `source` ("postgres" or "sqlserver"), When competitions are requested, Then return all distinct competitions from the selected source.
- Given a valid `match_id`, When a match detail is requested, Then return full match data including teams, stadium, referee, and scores.
- Given an invalid `match_id`, When a match detail is requested, Then return HTTP 404.

### Events

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/events` | `match_id`, `source`, `limit` | `List[EventDetailResponse]` |
| GET | `/api/v1/events/{event_id}` | `source` | `EventDetailResponse` |

**Behavior:**
- Given a valid `match_id`, When events are requested, Then return all aggregated events for that match.
- Given `limit` parameter, When events are requested, Then return at most `limit` results.

### Chat / Search (RAG)

| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | `/api/v1/chat/search` | `SearchRequest` | `SearchResponse` |

**SearchRequest fields:**
- `match_id` (int, required)
- `query` (str, required)
- `language` (str, default "english")
- `search_algorithm` (SearchAlgorithm enum)
- `embedding_model` (EmbeddingModel enum)
- `top_n` (int, 1-100, default 10)
- `temperature` (float, 0-2, default 0.1)
- `max_input_tokens` (int, default 10000)
- `max_output_tokens` (int, default 5000)
- `include_match_info` (bool, default true)
- `system_message` (Optional[str])

**Behavior:**
- Given a valid search request, When submitted, Then the system MUST normalize the query, generate embeddings, perform vector search, build context, and return an LLM-generated answer.
- Given `language != "english"`, When submitted, Then the system MUST translate the query to English before embedding.
- Given an unsupported `search_algorithm` for the selected source, Then return HTTP 400.

### Capabilities

| Method | Path | Response |
|--------|------|----------|
| GET | `/api/v1/capabilities` | `CapabilitiesResponse` |
| GET | `/api/v1/sources/status` | `SourceStatusResponse` |

**Behavior:**
- When capabilities are requested, Then return the supported embedding models and search algorithms for each data source.

### StatsBomb Remote Catalog

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/statsbomb/competitions` | — | `List[StatsBombCompetitionResponse]` |
| GET | `/api/v1/statsbomb/matches` | `competition_id`, `season_id` | `List[StatsBombMatchResponse]` |

### Data Explorer

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/teams` | `source`, `match_id`, `limit` | `List[TeamExplorerResponse]` |
| GET | `/api/v1/players` | `source`, `match_id`, `limit` | `List[PlayerExplorerResponse]` |
| GET | `/api/v1/tables-info` | `source` | `List[TableInfoResponse]` |

### Ingestion (Background Jobs)

| Method | Path | Request Body | Response |
|--------|------|-------------|----------|
| POST | `/api/v1/download` | `DownloadRequest` | `JobCreateResponse` |
| POST | `/api/v1/download-cleanup` | `DownloadCleanupRequest` | `DownloadCleanupResponse` |
| POST | `/api/v1/load` | `LoadRequest` | `JobCreateResponse` |
| POST | `/api/v1/aggregate` | `AggregateRequest` | `JobCreateResponse` |
| POST | `/api/v1/embeddings/rebuild` | `EmbeddingsRebuildRequest` | `JobCreateResponse` |
| GET | `/api/v1/jobs` | — | `JobListResponse` |
| GET | `/api/v1/jobs/{job_id}` | — | `Dict` |
| POST | `/api/v1/jobs/clear` | — | `ClearJobsResponse` |

### Embeddings Status

| Method | Path | Params | Response |
|--------|------|--------|----------|
| GET | `/api/v1/embeddings/status` | `source` | `Dict[str, Any]` |

---

## Cross-Cutting Concerns

### Source Selection
- All data endpoints accept `source` query parameter (default: "postgres").
- Valid sources: "postgres", "sqlserver".
- Source is normalized via `normalize_source()` before use.

### CORS
- **Current state:** `allow_origins=["*"]` (permissive for development).
- **Required for production:** Restrict origins to frontend domain.

### Dependency Injection
- Route handlers MUST receive dependencies via `Depends()`.
- Type aliases: `MatchRepo = Annotated[MatchRepository, Depends(get_match_repository)]`.

### Known Deviations
- `IngestionService()` and `StatsBombService()` are instantiated at module level in some routers (SHOULD use DI).
- `DataExplorerService` bypasses the repository pattern (direct DB access).
