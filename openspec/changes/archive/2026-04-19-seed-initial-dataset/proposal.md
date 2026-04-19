## Why

A new developer who clones RAG-Challenge and runs `docker compose up` (or "Reopen in Container")
lands on `http://localhost:5173/dashboard` and sees **nothing interesting**. The dashboard shows
2 connected data sources (postgres, sqlserver) but zero matches, zero events, zero embeddings.
The semantic search is unusable because:

1. The only seeded row is a placeholder (`match_id=900001`, `{"seed": true}`) in
   `.devcontainer/post-create.sh:86-149` — no events, no aggregations, no embeddings.
2. To get real data, the dev must run **4 sequential HTTP calls** against `/api/v1/ingestion/*`
   (download → load → aggregate → embeddings/rebuild), each as a background job, each requiring
   an OpenAI key for the embeddings step.
3. **Critical gap discovered during investigation**: the `aggregate` stage populates
   `events_details__quarter_minute.summary = NULL` and `.embeddings/rebuild` filters
   `WHERE summary IS NOT NULL`, so embeddings are **never created** out of the box. A summary
   generation step (LLM-based narrative per 15-second bucket) is described in
   `docs/data-model.md:137-139` but **does not exist in code**. This is a silent dead-end in
   the pipeline.

Result: the project is impossible to evaluate without either (a) understanding the pipeline
internals and filling the gap manually, or (b) following a long manual setup that consumes
OpenAI tokens on every fresh clone.

This change fixes all three problems in one coordinated effort. References **issue #40
(Area 8: Automatic setup and seed data)** as the umbrella, and adds the two canonical finals
already used across the test suite and proposed in that issue.

## What Changes

### A. Close the summary-generation gap (new pipeline stage)

- Add `POST /api/v1/ingestion/summaries/generate` endpoint that, for a given `source` +
  `match_ids`, reads rows from `events_details__quarter_minute` (Postgres) or
  `events_details__15secs_agg` (SQL Server), calls a chat model (GPT-4o-mini by default)
  with a prompt template converting raw event JSON into football commentary, and UPDATEs the
  `summary` column row-by-row.
- Add `IngestionService.run_generate_summaries_job(payload)` as the job handler.
- Add a prompt template under `backend/app/services/prompts/event_summary.md` (or equivalent
  — see design.md) that the service loads.
- Add a `POST /api/v1/ingestion/full-pipeline` endpoint that chains:
  `download → load → aggregate → generate_summaries → embeddings/rebuild` for a given match list,
  reporting progress via the existing job-status mechanism.

### B. Seed dataset (2 canonical finals, pre-computed)

- Pre-compute summaries and embeddings **once**, outside the repo, for:
  1. **Euro 2024 Final** — `competition_id=55`, `season_id=282`, `match_id=3943043`
     (Spain 2-1 England, 2024-07-14)
  2. **World Cup 2022 Final** — `competition_id=43`, `season_id=106`, `match_id=3869685`
     (Argentina 3-3 France, pens. 4-2, 2022-12-18)
- Publish the pre-computed artifacts as a **GitHub Release asset** (`seed-v1.tar.gz` or similar),
  NOT committed to the repo. The raw StatsBomb JSON is referenced as public data and downloaded
  on demand if needed — it is not committed either.
- Seed file structure (inside the Release tarball):
  ```
  seed/
    v1/
      manifest.json              # version, matches, embedding model, sha256 per file
      3943043/
        match.json               # raw StatsBomb match row (from matches/55/282.json)
        events.json              # raw StatsBomb events/3943043.json
        lineups.json              # raw StatsBomb lineups/3943043.json
        summaries.jsonl          # one row per 15-sec bucket with generated summary
        embeddings_t3_small.jsonl # one row per bucket with 1536-dim vector
      3869685/
        match.json
        events.json
        lineups.json
        summaries.jsonl
        embeddings_t3_small.jsonl
  ```

### C. Seed loader (no API calls)

- Add `backend/scripts/seed_load.py` (or `backend/app/cli/seed.py` — see design.md for location)
  that:
  1. Downloads the Release tarball if not already present under `backend/data/seed/v1/`.
  2. Verifies sha256 against `manifest.json`.
  3. Loads `matches`, `events`, `events_details` using the existing ingestion service's
     `_load_matches()` / `_load_events()` paths (refactored to accept local JSON, not just
     `./data/` convention).
  4. Runs `_build_aggregations()` for the seed match_ids.
  5. UPDATEs `summary` column from `summaries.jsonl`.
  6. UPDATEs `summary_embedding_t3_small` column from `embeddings_t3_small.jsonl`.
  7. **Zero OpenAI calls. Works without OPENAI_KEY.**

### D. Wire seed into first-run experience

- Update `.devcontainer/post-create.sh` to call the seed loader idempotently: if
  `SELECT COUNT(*) FROM matches WHERE match_id IN (3943043, 3869685)` returns 2 rows with
  non-null `summary_embedding_t3_small` in their aggregation rows, skip. Otherwise, run the
  seed loader for both Postgres and SQL Server.
- Replace the current `match_id=900001` placeholder seed with real data. Keep the 900001 row
  out of the final seed (dead code, no events, confuses the explorer).

### E. Fallback path for devs who want to regenerate

- Document in `docs/getting-started.md` how to:
  1. Run the seed loader offline (default path, no key).
  2. Run the full pipeline against any match_id with a key (`POST /ingestion/full-pipeline`).
- Add a `backend/scripts/seed_build.py` (maintainer-only, **not** run during dev onboarding)
  that regenerates the Release tarball from scratch using OPENAI_KEY. This is the script the
  maintainer runs once, uploads the tarball to a GitHub Release, and bumps the version tag.

### F. Documentation

- `docs/getting-started.md`: "First run" section that describes what the dashboard will show
  after `Reopen in Container` (2 matches with full RAG).
- `data/seed/README.md`: explains the seed version scheme, how to regenerate, where the
  Release is hosted, licensing (StatsBomb open-data CC BY-NC-SA).
- `CHANGELOG.md` under `## [Unreleased]`.

## Capabilities

### New Capabilities

- **`rag`**: Summary generation pipeline stage that converts aggregated 15-second event
  buckets into natural-language football commentary using an LLM. Previously missing entirely.
- **`data`**: Offline seed dataset mechanism — pre-computed summaries + embeddings distributed
  as a GitHub Release, loaded idempotently on first run without OpenAI API calls.

### Modified Capabilities

- **`api`**: Adds two new ingestion endpoints (`/ingestion/summaries/generate` and
  `/ingestion/full-pipeline`). No breaking changes to existing endpoints.
- **`infra`**: `.devcontainer/post-create.sh` replaces the synthetic `match_id=900001` seed
  with a real idempotent seed loader.

## Impact

- **Affected layers:**
  - API: new routes in `backend/app/api/v1/ingestion.py`
  - Service: new methods in `backend/app/services/ingestion_service.py`; new
    `backend/app/services/prompts/` directory
  - Adapters: `OpenAIAdapter` gets a new `create_chat_completion_for_summary()` helper
    (or reuse existing chat method if it already covers this case)
  - Scripts: `backend/scripts/seed_load.py` (dev-path, no key) and `backend/scripts/seed_build.py`
    (maintainer-path, needs key)
  - Infra: `.devcontainer/post-create.sh` rewritten
  - Docs: `docs/getting-started.md`, `data/seed/README.md`

- **Affected files (estimated):**
  - Modified: 6 — `backend/app/api/v1/ingestion.py`, `backend/app/services/ingestion_service.py`,
    `.devcontainer/post-create.sh`, `docs/getting-started.md`, `CHANGELOG.md`, `docs/conversation_log.md`
  - New: 8 — `backend/app/services/prompts/event_summary.md`,
    `backend/scripts/seed_load.py`, `backend/scripts/seed_build.py`,
    `backend/tests/unit/test_summary_generation.py`,
    `backend/tests/unit/test_seed_loader.py`,
    `backend/tests/api/test_ingestion_full_pipeline.py`,
    `data/seed/README.md`,
    `openspec/changes/seed-initial-dataset/*` (this change)

- **Test impact:**
  - New unit tests for summary generation (mock OpenAI adapter, verify prompt + SQL update)
  - New unit tests for seed loader (mock filesystem + mock repos)
  - New API test for `/ingestion/full-pipeline` orchestration
  - Integration test (marked `@pytest.mark.integration`) that runs the full seed load
    against real Docker Postgres + SQL Server — **skipped in CI by default**, runs locally
    on demand

- **Backwards compatibility:**
  - **Existing ingestion endpoints unchanged** — no breaking changes.
  - The `match_id=900001` synthetic seed is removed. Anyone who relied on it would have been
    relying on empty rows; risk is effectively zero.
  - `events_details__quarter_minute.summary` becomes populated for seed matches; was NULL
    before. No schema change.

- **Breaking changes:** None for existing users. The first-run experience of the devcontainer
  changes (more data appears), but that is the goal of the change.

## References

- GitHub issue: **erincon01/RAG-Challenge#40** (Area 8: Automatic setup and seed data)
- `docs/PLAN_V5_IMPROVEMENTS.md` — Area 8
- Existing pre-generated summary previews at `data/scripts_summary/preview/` (only 10 files,
  manually crafted, for match 3943043 only — will be replaced by the automated pipeline output)
- StatsBomb open-data license: CC BY-NC-SA 4.0 (non-commercial, attribution required)
