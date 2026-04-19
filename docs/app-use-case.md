
> **Note:** This document describes the current FastAPI + React architecture.
> See [architecture.md](architecture.md) for the full system design and
> [tech-stack.md](tech-stack.md) for versions and tooling.
> Azure is supported as an optional deployment target — see `OPENAI_PROVIDER` env var.
> Legacy Streamlit / Azure-first setup is archived in [docs/archive/legacy-azure-streamlit-setup.md](archive/legacy-azure-streamlit-setup.md).

---

## Use Cases

### UC-1: Ask a question about a match

**Actor:** Analyst / fan  
**Trigger:** User selects a match and types a natural-language question in the React UI.

**Happy path:**
1. Frontend sends `POST /api/v1/chat/search` with `{ match_id, query, language, embedding_model, search_algorithm, top_n }`.
2. `SearchService.search_and_chat()` runs the 6-step RAG pipeline:
   - Translate query to English (if needed)
   - Generate query embedding via OpenAI / Azure OpenAI
   - Vector-search `events_details__quarter_minute` (pgvector) or `events_details__15secs_agg` (SQL Server)
   - Build token-budgeted context from top-N results
   - Call GPT-4o for grounded answer
3. Response: `{ answer, sources, tokens_used, search_results }`.

**Variations:**
- `source=sqlserver` queries SQL Server instead of PostgreSQL.
- `language=es` triggers a translation step before embedding.

---

### UC-2: Browse available matches

**Actor:** Any user  
**Trigger:** User opens the match selector in the React UI.

**Happy path:**
1. Frontend sends `GET /api/v1/matches?source=postgres&competition_name=UEFA Euro&limit=50`.
2. `MatchRepository.get_all()` queries the `matches` table with optional filters.
3. Response: list of `{ match_id, home_team, away_team, date, competition, season }`.

---

### UC-3: Inspect raw events for a time window

**Actor:** Analyst  
**Trigger:** User wants to see raw events for a specific minute range.

**Happy path:**
1. Frontend sends `GET /api/v1/events?match_id=3788741&period=1&minute_from=30&minute_to=45`.
2. `EventRepository.get_by_match()` returns `EventDetail` objects for that time window.
3. Response includes `json_data` (Statsbomb raw JSON) and pre-computed `summary`.

---

### UC-4: Ingest a new match

**Actor:** Data engineer / admin  
**Trigger:** New Statsbomb match data is available.

**Happy path:**
1. Admin sends `POST /api/v1/ingestion/match/{match_id}`.
2. `IngestionService` downloads raw JSON from Statsbomb open-data GitHub.
3. Data is parsed and inserted into `matches`, `events_details__quarter_minute`.
4. Embeddings are generated for each event summary via OpenAI / Azure OpenAI.
5. Job status tracked via `JobService` and polled with `GET /api/v1/ingestion/jobs/{job_id}`.

---

### UC-5: Compare search algorithms

**Actor:** Researcher  
**Trigger:** Exploring which similarity metric gives better recall.

**Happy path:**
1. Send `POST /api/v1/chat/search` with `search_algorithm=cosine` → record results.
2. Repeat with `search_algorithm=inner_product`, `l2_euclidean`, `l1_manhattan`.
3. Compare `search_results[*].similarity_score` across responses.

Available algorithms (`SearchAlgorithm` enum): `cosine`, `inner_product`, `l2_euclidean`, `l1_manhattan`.

---

### UC-6: Health check

**Actor:** DevOps / monitoring  
**Trigger:** Uptime probe or deployment verification.

**Happy path:**
1. `GET /api/v1/health` → `{ status: "ok", db_postgres: true, db_sqlserver: true }`.
2. CI/CD pipeline uses this to verify successful deploy.

---

## API Reference (summary)

| Method | Path | Description |
|--------|------|-------------|
| `GET` | `/api/v1/health` | Liveness + DB checks |
| `GET` | `/api/v1/competitions` | List competitions |
| `GET` | `/api/v1/matches` | List matches (filterable) |
| `GET` | `/api/v1/matches/{match_id}` | Match detail |
| `GET` | `/api/v1/events` | Event details for a match |
| `POST` | `/api/v1/chat/search` | Full RAG pipeline |
| `POST` | `/api/v1/embeddings/generate` | Generate embeddings for a text |
| `POST` | `/api/v1/ingestion/match/{match_id}` | Ingest a match |
| `GET` | `/api/v1/ingestion/jobs/{job_id}` | Ingestion job status |
| `GET` | `/api/v1/capabilities` | Supported sources, models, algorithms |
| `GET` | `/docs` | Auto-generated OpenAPI docs (Swagger UI) |

