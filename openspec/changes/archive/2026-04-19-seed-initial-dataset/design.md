## Context

The RAG-Challenge ingestion pipeline exists as 4 separate HTTP endpoints:
`download → load → aggregate → embeddings/rebuild`. Each is a background job.
Each was designed to be run manually. See `backend/app/services/ingestion_service.py:187-794`
for the four `run_*_job()` methods.

Three problems combine to make the out-of-the-box experience frustrating:

1. **The summary-generation step does not exist.**
   [ingestion_service.py:666-675](backend/app/services/ingestion_service.py#L666-L675) sets
   `summary=NULL` and `summary_script=NULL` during aggregate.
   [ingestion_service.py:458-489](backend/app/services/ingestion_service.py#L458-L489) filters
   `WHERE summary IS NOT NULL` in the embeddings rebuild step. The aggregate stage produces
   rows that the embedding stage will always skip. Nothing bridges the two. The
   `docs/data-model.md:137-139` description of "LLM-generated summary" was aspirational.

2. **The devcontainer seeds a dead row.**
   [.devcontainer/post-create.sh:86-149](.devcontainer/post-create.sh#L86-L149) inserts
   `match_id=900001` with `json_='{"seed": true}'` — no events, no aggregations, no
   embeddings. The match explorer sees one phantom row with no detail. The dashboard
   shows "Sources: 2" but has nothing to explore.

3. **The dashboard UX confuses "data source = database" with "data source = dataset".**
   [DashboardPage.tsx:15-21](frontend/webapp/src/pages/DashboardPage.tsx#L15-L21) calls
   `GET /api/v1/sources/status` which returns `[postgres, sqlserver]` connectivity.
   It always returns 2 items, so the empty state is never triggered. The user's
   original question "no me aparece ningún data source" is actually about **no matches
   visible in the explorer**, not about the sources list being empty.

This change fixes (1) and (2) directly, and addresses (3) by ensuring there are real
matches to explore after first run. The dashboard wording ("Data Sources") is out of scope
for this change — fixing that is a UX concern for a separate issue.

## Goals / Non-Goals

**Goals:**

- Make `Reopen in Container` (or `docker compose up` with post-create equivalent) produce
  a system where the dashboard shows 2 real matches with full RAG working, **without**
  requiring OPENAI_KEY.
- Close the missing summary-generation stage of the pipeline, as a proper, testable,
  first-class ingestion stage.
- Allow the maintainer to regenerate the seed dataset with a single command when the
  prompt template, the embedding model, or the match list changes.
- Allow a dev **with** an OpenAI key to run the full pipeline end-to-end on arbitrary
  match_ids via one HTTP call.
- Keep the repo lean: the ~20 MB seed artifact lives in a GitHub Release, not in git.

**Non-Goals:**

- Not changing the dashboard UI or the "Data Sources" label. That's a frontend UX fix
  tracked separately.
- Not adding more than 2 seed matches. Expanding the seed is cheap (edit the matches
  list in `seed_build.py`, re-run, re-upload); adding more here bloats the first PR.
- Not replacing the 4 existing ingestion endpoints. They stay as-is; the new
  `/full-pipeline` endpoint is a thin orchestrator on top.
- Not implementing a full CLI framework (click/typer). A plain `python -m` script is
  enough for seed_load / seed_build.
- Not committing raw StatsBomb JSON to the repo. They are downloaded on demand and
  referenced as public data (CC BY-NC-SA).
- Not implementing multi-model seed (only `text-embedding-3-small`). If the user wants
  `ada-002` or `3-large`, they run `full-pipeline` with their key.

## Decisions

### 1. The missing summary-generation stage is a new first-class pipeline step

**Decision:** Add `POST /api/v1/ingestion/summaries/generate` + `run_generate_summaries_job()`
as a fifth stage between `aggregate` and `embeddings/rebuild`. Do NOT fold it into either
of its neighbors.

**Rationale:**

- Keeps the pipeline composable: someone can run `aggregate`, iterate on the prompt
  template, re-run `summaries/generate` cheaply without re-aggregating.
- Keeps the cost model explicit: `summaries/generate` is the **expensive** LLM call
  (one chat completion per bucket), `embeddings/rebuild` is the **cheap** embed call
  (batched 50 at a time). Collapsing them would hide the cost asymmetry.
- Matches the existing file structure: one `run_*_job()` method per stage, one endpoint
  per stage, uniform job-status tracking.

**Alternative rejected:** "Generate summary + embedding in one loop." Rejected because
it couples prompt iteration to embedding cost and makes the job non-restartable mid-way.

### 2. Prompt template lives in a file, not hardcoded

**Decision:** Create `backend/app/services/prompts/event_summary.md` containing the
Jinja2-free plain-text template (with `{placeholder}` slots filled via `str.format()`).
Load it at service init time, not per-call.

**Rationale:**

- Editing a prompt shouldn't require touching Python code.
- Keeps the prompt version-controlled and reviewable in PRs.
- No new dependency: `str.format()` is enough. No Jinja2 required.

**Prompt inputs per call:**
- `match_info`: dict with team names, competition, date
- `period`, `minute`, `second_window` (e.g. "15-30s")
- `events_json`: the raw concatenated event JSON from the bucket
- `language`: "english" by default, configurable (existing settings honor language)

**Prompt output contract:** a 1-3 sentence narrative string, no markdown, no headers.
Enforced via a simple post-processing strip.

**Alternative rejected:** Using Pydantic structured output / function-calling. Rejected
because the text-only output is simpler, avoids schema drift, and the downstream
embedding step only needs the string.

### 3. Embedding model: only `text-embedding-3-small` for the seed

**Decision:** The seed Release tarball contains embeddings for `text-embedding-3-small`
only (1536 dims, stored in `summary_embedding_t3_small` column).

**Rationale:**

- Cheapest and most modern of the 3 supported models.
- Existing schema already has the column. No migration.
- Cuts Release tarball size roughly to 1/3 vs. seeding all 3 models.
- A dev who wants `ada-002` or `3-large` runs `POST /ingestion/embeddings/rebuild`
  with their key and the specific `embedding_models` payload.

**Alternative rejected:** Seed all 3 models. Rejected because it triples the Release
size and 95% of onboarding flows won't touch the other two models.

### 4. Seed artifacts: GitHub Release, not git

**Decision:** Package seed artifacts as a versioned tarball
(`seed-v1.tar.gz`) and publish it as a GitHub Release asset on a tag like `seed/v1`.
The Release asset URL is hardcoded in `seed_load.py` with a sha256 in a manifest.

**Rationale:**

- User explicitly asked not to commit raw JSONs to the repo.
- Embeddings for 2 matches × ~2500 buckets × 1536 floats ≈ 6 MB JSONL gzipped → fits
  any Release asset limit easily.
- Versioning via the `seed/vN` tag means updating the seed doesn't touch git history
  of code. The code references `v1`; to upgrade, a new PR bumps the version string.
- sha256 check in manifest catches tampering or partial downloads.

**Alternative rejected (1):** Git LFS. Rejected because it adds a required tool to the
onboarding path and the existing `.gitignore` + DevContainer flow already has enough
moving parts.

**Alternative rejected (2):** A public S3 bucket. Rejected because GitHub Releases are
already authenticated to the repo's identity, free, and traceable.

**Alternative rejected (3):** Commit seed to repo. User explicitly said no (and rightly
so — StatsBomb raw JSON is several MB per match even gzipped).

### 5. Seed loader runs in post-create, idempotently

**Decision:** Modify `.devcontainer/post-create.sh` to invoke `python -m
backend.scripts.seed_load` after the database bootstrap section. The loader checks
whether `SELECT COUNT(*) FROM matches WHERE match_id IN (3943043, 3869685)` returns 2
**and** a non-null `summary_embedding_t3_small` exists for those match_ids' aggregation
rows. If yes, it exits 0 immediately. If no, it downloads the Release tarball (if
needed) and loads everything.

**Rationale:**

- First `Reopen in Container` → populates automatically.
- Subsequent rebuilds → no-op, no network, no wait.
- Failed downloads → loader exits non-zero, post-create continues (downgrade gracefully
  instead of blocking the devcontainer from starting). A clear warning is printed.

**Alternative rejected:** A Makefile target `make seed`. Rejected as the *primary* path
because it requires the user to know it exists. Kept as an **opt-in secondary path**
for dev experimentation and CI. Both paths call the same `seed_load.py`.

### 6. The 900001 placeholder row is removed

**Decision:** Delete the current `match_id=900001` inserts from
`.devcontainer/post-create.sh:86-102` (Postgres) and `:131-149` (SQL Server). The real
seed replaces it.

**Rationale:**

- The placeholder row has no events, no embeddings, and no narrative. It only confuses
  the explorer.
- Nothing in the tests depends on `match_id=900001` (confirmed by
  `grep -r 900001 backend/tests/` — zero hits; all test fixtures use 3943043).

**Alternative rejected:** Keep 900001 as a smoke-test sentinel. Rejected — the seed
provides 2 real matches which serve the same smoke-test purpose much better.

### 7. Seed_load reuses ingestion service internals

**Decision:** `seed_load.py` imports `IngestionService` and calls its internal methods
(`_load_matches`, `_load_events`, `_build_aggregations`) with a database connection,
then issues two custom UPDATEs to set `summary` and `summary_embedding_t3_small` from
the JSONL files. It does **not** go through the HTTP endpoints.

**Rationale:**

- HTTP routing through localhost:8000 during post-create creates a chicken-and-egg
  issue (backend may not be ready yet).
- Direct service invocation is faster (no HTTP overhead for ~5000 rows × 2 DBs).
- Re-exercises the existing ingestion code paths — if those break, seed_load breaks
  too, which is a desirable tight coupling for CI detection.

**Trade-off accepted:** `_load_matches` / `_load_events` are currently private. The
change promotes them to "module-private but accessible from the same package", which
is fine in Python. No API leakage.

### 8. `full-pipeline` endpoint is an orchestrator, not a new code path

**Decision:** `POST /api/v1/ingestion/full-pipeline` sequentially invokes the 5 existing
`run_*_job()` methods (download → load → aggregate → generate_summaries → rebuild_embeddings)
in a single job, reporting combined progress. No new business logic.

**Rationale:**

- Single source of truth for each stage: if any stage changes, full-pipeline benefits
  automatically.
- The endpoint does one thing — orchestration — and does it in ~30 lines.

### 9. Where does the seed loader live: `backend/scripts/` vs `backend/app/cli/`?

**Decision:** `backend/scripts/seed_load.py` and `backend/scripts/seed_build.py`.

**Rationale:**

- `backend/app/` is the FastAPI app. Adding CLI entry points there blurs the boundary.
- `backend/scripts/` is a conventional location for maintenance scripts that import
  from the app but aren't part of it. Existing repo does not yet have `scripts/`, but
  this is a clean first entry.
- Both scripts can still import `from app.services.ingestion_service import IngestionService`
  as long as they're run from `backend/` (same cwd as pytest).

**Alternative rejected:** `backend/app/cli/seed.py`. Rejected because it suggests the
CLI is part of the shipped product, when it's a dev/maintainer tool.

### 10. Testing strategy for the new summary stage

**Decision:**

- **Unit tests** (`backend/tests/unit/test_summary_generation.py`):
  - Mock the OpenAI adapter (`MagicMock(spec=OpenAIAdapter)`).
  - Mock the DB connection.
  - Verify: prompt template is loaded, substituted correctly, the chat method is called
    with the right args, the SQL UPDATE is issued with the correct parameters.
  - Verify: empty events bucket is skipped with a warning (edge case).
  - Verify: rate-limit retry logic is exercised (reuse existing adapter retry test
    pattern).

- **Unit tests** (`backend/tests/unit/test_seed_loader.py`):
  - Mock filesystem (tmp_path fixture).
  - Mock repos and ingestion service internals.
  - Verify: idempotency check (both tables populated → exits 0).
  - Verify: download failure → exits non-zero with clear error.
  - Verify: sha256 mismatch → raises.

- **API test** (`backend/tests/api/test_ingestion_full_pipeline.py`):
  - FastAPI TestClient.
  - Mock all 5 `run_*_job` methods on the injected service.
  - POST `/ingestion/full-pipeline` with valid payload, assert all 5 are called in order.
  - Assert one of them raising propagates as a failed job status.

- **Integration test** (`backend/tests/integration/test_seed_load_live.py`,
  `@pytest.mark.integration`):
  - Requires docker-compose stack running.
  - Downloads the real Release tarball.
  - Runs seed_load against real Postgres + SQL Server containers.
  - Asserts matches, events_details, aggregations, summaries, embeddings are all populated.
  - Asserts running seed_load a second time is a no-op (idempotency).
  - **Skipped in CI** (no docker stack in GitHub Actions); runs manually via
    `pytest -m integration` on dev machines.

### 11. OPENAI_KEY: when is it required?

**Decision:** In decreasing order of necessity:

| Flow | Needs `OPENAI_KEY`? |
|---|---|
| First-run `post-create` seed load | **NO** (uses pre-computed Release tarball) |
| `make seed` / `python -m backend.scripts.seed_load` | **NO** (same path) |
| Dashboard chat / RAG runtime (existing behavior) | **YES** — unchanged |
| `POST /ingestion/full-pipeline` on a new match | **YES** (summary + embeddings call GPT) |
| `POST /ingestion/summaries/generate` standalone | **YES** |
| `POST /ingestion/embeddings/rebuild` standalone | **YES** (existing) |
| `backend/scripts/seed_build.py` (maintainer) | **YES** — only run when updating the Release |

This satisfies the user's requirement: a new dev can clone, `Reopen in Container`, and
have a working dashboard **without providing any key**. The chat UI itself, however,
still needs `OPENAI_KEY` in `.env.docker` to answer questions — that is unchanged from
today.

## File changes

| File | Action | Description |
|------|--------|-------------|
| `backend/app/services/prompts/__init__.py` | (new) | Package marker |
| `backend/app/services/prompts/event_summary.md` | (new) | Prompt template (plain text, `{placeholder}` slots) |
| `backend/app/services/ingestion_service.py` | (modified) | Add `run_generate_summaries_job()`, `_fetch_aggregation_rows_for_summary()`, `_update_summary_for_row()`, `run_full_pipeline_job()`, loader for the prompt file |
| `backend/app/api/v1/ingestion.py` | (modified) | Add `POST /ingestion/summaries/generate` and `POST /ingestion/full-pipeline` routes |
| `backend/app/adapters/openai_client.py` | (modified if needed) | Confirm existing `create_chat_completion()` supports the summary call; add helper only if not |
| `backend/scripts/__init__.py` | (new) | Package marker |
| `backend/scripts/seed_load.py` | (new) | Dev-path loader: download tarball, verify sha256, load DBs, update summaries + embeddings. No API calls. |
| `backend/scripts/seed_build.py` | (new) | Maintainer-path builder: downloads StatsBomb JSON for 2 matches, runs full pipeline against a throwaway DB or in-memory buffers, serializes to tarball, prints sha256 and upload instructions. Requires `OPENAI_KEY`. |
| `.devcontainer/post-create.sh` | (modified) | Remove 900001 inserts, add call to `python -m backend.scripts.seed_load` |
| `backend/tests/unit/test_summary_generation.py` | (new) | Unit tests for summary stage |
| `backend/tests/unit/test_seed_loader.py` | (new) | Unit tests for seed loader |
| `backend/tests/api/test_ingestion_full_pipeline.py` | (new) | API test for orchestrator |
| `backend/tests/integration/test_seed_load_live.py` | (new) | `@pytest.mark.integration` end-to-end |
| `docs/getting-started.md` | (modified) | Add "First run" section and troubleshooting |
| `data/seed/README.md` | (new) | Explains seed versioning, Release location, license |
| `CHANGELOG.md` | (modified) | `## [Unreleased]` entries |
| `docs/conversation_log.md` | (modified) | Session entry |

## Risks / Trade-offs

- **[Risk]** StatsBomb open-data URLs could change or go away. **Mitigation:** the seed
  tarball bundles `match.json`, `events.json`, `lineups.json` verbatim, so once a
  Release is published it is self-contained. `seed_build.py` is only needed for updates.

- **[Risk]** Prompt template drift: a maintainer edits `event_summary.md` but forgets
  to rebuild the Release, so production seed and current template diverge.
  **Mitigation:** `manifest.json` inside the tarball records the template's sha256 at
  build time. `seed_load.py` logs a warning if the current template's sha256 doesn't
  match. Not a hard error — the seed is still valid — but visible.

- **[Risk]** GitHub Release download during post-create adds a network dependency that
  could fail in restricted networks. **Mitigation:** graceful degrade (clear warning,
  devcontainer still starts). Also cache the tarball under
  `~/.cache/rag-challenge-seed/` so subsequent container rebuilds reuse it.

- **[Trade-off]** The seed tarball is hosted on GitHub Releases, so anyone cloning the
  repo can trigger the download but cannot modify the tarball without repo write access.
  Acceptable for an educational project.

- **[Risk]** `python -m backend.scripts.seed_load` assumes cwd is the repo root (like
  pytest does). **Mitigation:** the script uses absolute paths derived from
  `Path(__file__).resolve()` rather than cwd, so it works from anywhere.

- **[Trade-off]** The integration test `test_seed_load_live.py` downloads a real ~20 MB
  tarball the first time it runs, which slows local testing. **Mitigation:** marked
  `@pytest.mark.integration`, skipped by default. Also caches the tarball.

- **[Risk]** `seed_build.py` runs GPT calls which cost money. **Mitigation:** documented
  cost estimate (~$0.30 total for both matches, summaries + embeddings) and gated
  behind an explicit `--i-have-budget` flag.

## Rollback strategy

- **If the summary stage has a bug:** revert the PR. The pipeline returns to the pre-change
  behavior (summary always NULL, embeddings step is effectively a no-op). No data loss.

- **If the seed loader corrupts data:** `seed_load.py` operates only on the 2 seed
  match_ids. A `DELETE FROM matches WHERE match_id IN (3943043, 3869685)` followed by
  cascade-deletes from events and aggregations cleans up. Document this in
  `data/seed/README.md`.

- **If the Release tarball is bad:** publish a new `seed/v2` tag, bump the version
  string in `seed_load.py`, open a hotfix PR.

## Open questions to resolve during implementation

1. **Prompt wording for the narrative.** First pass is the implementer's choice; a
   follow-up PR can iterate with `seed_build.py` re-run and `seed/v2` tag. Track as a
   tuning exercise, not a blocker.

2. **Languages for summaries.** Default `"english"`. Settings already honor
   `Request.language`, so multi-language seed can be a future enhancement (would need
   separate tarballs per language or a `language_code` column).

3. **SQL Server aggregation table has fewer embedding columns** (2 vs Postgres's 3).
   The seed only uses `text-embedding-3-small` which both support, so this is not an
   issue for this change. Documented for future model additions.
