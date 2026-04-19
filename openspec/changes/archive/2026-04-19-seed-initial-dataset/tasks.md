## Phase 0 — Prep

- [ ] 0.1 Create branch `feature/040-seed-initial-dataset` from `develop`
- [ ] 0.2 Read `proposal.md` and `design.md` end-to-end; confirm scope with user if any decision feels wrong
- [ ] 0.3 Confirm OpenAI key is set in `backend/.env` (or `.env.docker`) for the maintainer-path scripts; verify `OPENAI_PROVIDER`, `OPENAI_ENDPOINT`, `OPENAI_KEY`, `OPENAI_MODEL` are loaded correctly
- [ ] 0.4 Verify StatsBomb open-data URLs are reachable:
  `curl -I https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/3943043.json`
  `curl -I https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/3869685.json`

## Phase 1 — Summary generation stage (closes the pipeline gap)

### 1.1 Prompt template

- [ ] 1.1.1 Create `backend/app/services/prompts/__init__.py` (empty)
- [ ] 1.1.2 Create `backend/app/services/prompts/event_summary.md` with a first-pass prompt:
  slots `{match_info}`, `{period}`, `{minute}`, `{second_window}`, `{events_json}`, `{language}`
  — output contract: 1-3 sentence plain-text narrative, no markdown headers
- [ ] 1.1.3 Write unit test `test_event_summary_prompt_loads_from_file` that opens the file,
  runs `str.format()` with fake slots, asserts no `KeyError` and output length > 0

### 1.2 Ingestion service changes

- [ ] 1.2.1 Add private method `_load_prompt_template()` to `IngestionService` that reads
  `backend/app/services/prompts/event_summary.md` at init time and caches the content
- [ ] 1.2.2 Add private method `_fetch_aggregation_rows_for_summary(conn, source, match_ids)`
  returning rows with `id`, `period`, `minute`, `quarter_minute`, `json_` (the raw events
  JSON from the `GROUP BY` string_agg) from the aggregation table where `summary IS NULL`
  for the given match_ids
- [ ] 1.2.3 Add private method `_update_summary_for_row(conn, source, row_id, summary)`
  that issues the UPDATE with parameterized query (`%s` / `?`)
- [ ] 1.2.4 Add public method `run_generate_summaries_job(payload, job)` that:
  (a) opens a connection for the given source,
  (b) loads match metadata (home/away team, competition, date) once per match_id for prompt context,
  (c) iterates rows from `_fetch_aggregation_rows_for_summary`,
  (d) for each row, builds the prompt via `str.format()`, calls `OpenAIAdapter.create_chat_completion()`,
  (e) strips the response, calls `_update_summary_for_row`,
  (f) updates `job.progress` every N rows,
  (g) handles rate-limit errors via the existing retry logic in the adapter,
  (h) commits the transaction at the end
- [ ] 1.2.5 Write unit test `test_generate_summaries_job_happy_path` — mock adapter, mock connection,
  verify prompt is built, chat is called once per row, UPDATE is issued with the response
- [ ] 1.2.6 Write unit test `test_generate_summaries_job_skips_empty_buckets` — row with empty
  `json_` should be skipped and logged, no chat call
- [ ] 1.2.7 Write unit test `test_generate_summaries_job_continues_on_partial_failure` — one
  row raises, next row still processes
- [ ] 1.2.8 Run pytest on the new test file; confirm all pass and imports resolve from `backend/`

### 1.3 API endpoint

- [ ] 1.3.1 Add `POST /api/v1/ingestion/summaries/generate` route in `backend/app/api/v1/ingestion.py`
  accepting `{source: "postgres"|"sqlserver", match_ids: list[int]}`, returning job_id
- [ ] 1.3.2 Wire the route to a background task that calls `run_generate_summaries_job`
- [ ] 1.3.3 Write API test `test_post_summaries_generate_returns_job_id` — mock service,
  POST with valid payload, assert 202 and job_id in response
- [ ] 1.3.4 Write API test `test_post_summaries_generate_rejects_invalid_source` — POST with
  `source="mongo"`, assert 422 or 400
- [ ] 1.3.5 Write API test `test_post_summaries_generate_empty_match_ids_rejected` — POST with
  `match_ids=[]`, assert validation error
- [ ] 1.3.6 Run pytest on the API test file; confirm all pass

## Phase 2 — Full-pipeline orchestrator endpoint

- [ ] 2.1 Add public method `run_full_pipeline_job(payload, job)` to `IngestionService` that
  sequentially invokes `run_download_job`, `run_load_job`, `run_aggregate_job`,
  `run_generate_summaries_job`, `run_rebuild_embeddings_job` with shared job progress tracking
- [ ] 2.2 Add `POST /api/v1/ingestion/full-pipeline` route accepting the union of all stage
  payloads (source, match_ids, competition_id, season_id, embedding_models optional)
- [ ] 2.3 Write unit test `test_run_full_pipeline_calls_stages_in_order` — mock each stage,
  assert call order and that a failure in stage N aborts stages N+1..5
- [ ] 2.4 Write API test `test_post_full_pipeline_happy_path` — mock service, POST, assert
  202 + job_id
- [ ] 2.5 Run pytest; confirm all pass

## Phase 3 — Maintainer script (seed_build.py)

- [ ] 3.1 Create `backend/scripts/__init__.py` (empty)
- [ ] 3.2 Create `backend/scripts/seed_build.py` with argparse flags `--i-have-budget`,
  `--output <path>`, `--matches 3943043,3869685`
- [ ] 3.3 Implement download step: call `StatsBombService.download_match_file()` for
  `matches`, `events`, `lineups` datasets for each match_id, into a temp directory
- [ ] 3.4 Implement DB step: spin up a throwaway Postgres (or reuse the local one with a
  temp schema), run `_load_matches`, `_load_events`, `_build_aggregations` for the seed
  match_ids — OR — skip the DB and go straight to in-memory processing (decision during
  implementation; whichever is simpler)
- [ ] 3.5 Implement summary generation step: iterate buckets, call the summary prompt +
  GPT-4o-mini, write to `summaries.jsonl` (one `{bucket_id, summary}` per line)
- [ ] 3.6 Implement embedding step: iterate `summaries.jsonl`, call
  `OpenAIAdapter.create_embedding()` batched 50, write to
  `embeddings_t3_small.jsonl` (one `{bucket_id, vector}` per line)
- [ ] 3.7 Assemble tarball `seed-v1.tar.gz` with the structure in proposal.md §B
- [ ] 3.8 Compute sha256 for each file, write `manifest.json`
- [ ] 3.9 Print upload instructions: `gh release create seed/v1 ./seed-v1.tar.gz --notes "..."`
- [ ] 3.10 **MANUAL:** maintainer runs `python -m backend.scripts.seed_build --i-have-budget`
  once, reviews output, runs the `gh release create` command, confirms the asset is
  downloadable at `https://github.com/erincon01/RAG-Challenge/releases/download/seed/v1/seed-v1.tar.gz`
- [ ] 3.11 Write unit test `test_seed_build_refuses_without_budget_flag` — argparse test,
  no OpenAI calls
- [ ] 3.12 Run ruff + pytest on scripts changes

## Phase 4 — Dev-path script (seed_load.py)

- [ ] 4.1 Create `backend/scripts/seed_load.py` with hardcoded constants:
  - `SEED_VERSION = "v1"`
  - `SEED_URL = "https://github.com/erincon01/RAG-Challenge/releases/download/seed/v1/seed-v1.tar.gz"`
  - `SEED_MATCH_IDS = (3943043, 3869685)`
  - `CACHE_DIR = Path.home() / ".cache" / "rag-challenge-seed"`
- [ ] 4.2 Implement `check_idempotency(source)` that returns True if both match_ids exist
  AND have non-null `summary_embedding_t3_small` in their aggregation rows
- [ ] 4.3 Implement `download_and_verify(url, cache_dir)` that downloads the tarball if not
  cached, extracts to a temp dir, verifies sha256s against manifest.json, returns the
  extracted path
- [ ] 4.4 Implement `load_into(source, seed_path)`:
  - Read `match.json` files → `_load_matches` (internal API)
  - Read `events.json` files → `_load_events`
  - Call `_build_aggregations` for seed match_ids
  - Read `summaries.jsonl` → UPDATE `summary` by bucket_id
  - Read `embeddings_t3_small.jsonl` → UPDATE `summary_embedding_t3_small` by bucket_id
- [ ] 4.5 Add main entry point supporting `--source postgres` / `--source sqlserver` /
  `--source both` (default: `both`)
- [ ] 4.6 On any failure, print clear error to stderr, exit non-zero; do NOT raise unhandled
  exceptions (post-create must continue even on failure)
- [ ] 4.7 Write unit test `test_seed_load_idempotent_when_data_present` — mock repos,
  check_idempotency returns True → script exits 0 without touching files
- [ ] 4.8 Write unit test `test_seed_load_downloads_and_loads_when_data_missing` — mock repos,
  check_idempotency returns False → script calls download + load in order
- [ ] 4.9 Write unit test `test_seed_load_sha256_mismatch_aborts` — mock manifest with wrong
  hash → script raises and exits non-zero
- [ ] 4.10 Write unit test `test_seed_load_download_failure_graceful` — mock network error →
  script logs warning and exits non-zero, no partial state in DB
- [ ] 4.11 Run pytest and confirm all unit tests pass

## Phase 5 — Wire into post-create

- [ ] 5.1 Modify `.devcontainer/post-create.sh`:
  - Remove the `INSERT INTO matches ... 900001 ...` blocks for both Postgres and SQL Server
  - After the `wait_for_db` section, add a call:
    ```bash
    echo "[post-create] Loading seed dataset..."
    python -m backend.scripts.seed_load --source both || {
      echo "  [warn] Seed load failed — dashboard will be empty, you can retry with 'make seed' or 'python -m backend.scripts.seed_load'"
    }
    ```
- [ ] 5.2 Verify post-create.sh still parses with `bash -n .devcontainer/post-create.sh`
- [ ] 5.3 Add a `Makefile` (or append to existing one — check repo root first) with a target:
  ```makefile
  seed:
  	@cd backend && python -m scripts.seed_load --source both
  ```
- [ ] 5.4 **DEFERRED: requires docker on user host** — Rebuild the devcontainer and verify:
  - `docker compose exec backend python -c "from app.repositories... ; print(count)"`
    shows 2 matches, ~5000 aggregation rows, ~5000 non-null summaries, ~5000 non-null
    `summary_embedding_t3_small` values
  - Dashboard at `http://localhost:5173/dashboard` shows both matches in the explorer
  - Chat page can ask "¿Quién marcó el primer gol de la final?" and get a relevant answer

## Phase 6 — Documentation

- [ ] 6.1 Create `data/seed/README.md` explaining:
  - What the seed contains (2 matches)
  - License (StatsBomb CC BY-NC-SA 4.0, attribution text)
  - Where the tarball lives (GitHub Release URL)
  - How to regenerate (`python -m backend.scripts.seed_build --i-have-budget`)
  - How to clean local seed cache (`rm -rf ~/.cache/rag-challenge-seed`)
  - How to remove seed data from DB
- [ ] 6.2 Update `docs/getting-started.md`:
  - Add "First run" section describing what the dashboard shows after `Reopen in Container`
  - Add troubleshooting section: what to do if seed load failed
  - Mention that the chat UI requires `OPENAI_KEY` in `.env.docker` (unchanged)
- [ ] 6.3 Update `CHANGELOG.md` under `## [Unreleased]`:
  - **Added**: automatic seed dataset (2 finals), new ingestion stages (summaries, full-pipeline)
  - **Changed**: devcontainer first-run loads real data instead of placeholder
  - **Removed**: synthetic `match_id=900001` placeholder
- [ ] 6.4 Append session entry to `docs/conversation_log.md`

## Phase 7 — Integration test

- [ ] 7.1 Create `backend/tests/integration/test_seed_load_live.py` with
  `@pytest.mark.integration` decorator
- [ ] 7.2 Test `test_seed_load_populates_postgres_and_sqlserver` — requires running
  docker-compose stack; cleans the 2 match_ids, runs `seed_load.py`, asserts counts and
  non-null summaries/embeddings
- [ ] 7.3 Test `test_seed_load_second_run_is_noop` — runs `seed_load.py` twice, asserts
  second run exits 0 in < 2 seconds and makes no DB writes
- [ ] 7.4 Document in the test file how to run: `pytest -m integration backend/tests/integration/`
- [ ] 7.5 Confirm integration tests are excluded from default CI by checking `pytest.ini`

## Phase 8 — Final verification

- [ ] 8.1 Run `pytest backend/tests/ -v` (excluding integration) — all 470+ tests + new tests must pass
- [ ] 8.2 Run `pytest -m integration backend/tests/integration/` on local docker stack — must pass
- [ ] 8.3 Run `ruff check backend/` and `ruff format --check backend/`
- [ ] 8.4 Run `mypy backend/app` — no new errors introduced
- [ ] 8.5 From a clean devcontainer rebuild, verify the dashboard shows both matches and the
  chat UI can answer questions about them (requires `OPENAI_KEY`)

## Phase 9 — Commit & PR

- [ ] 9.1 Stage all new and modified files
- [ ] 9.2 Commit in logical chunks (one commit per phase if clean, or a single squashable PR):
  - `feat(ingestion): add summary generation stage`
  - `feat(ingestion): add full-pipeline orchestrator endpoint`
  - `feat(seed): add seed_load and seed_build scripts`
  - `chore(devcontainer): replace placeholder seed with automatic seed load`
  - `docs: document seed dataset and first-run experience`
- [ ] 9.3 Push branch, open PR against `develop`, link issue #40 in the body
- [ ] 9.4 Request review, iterate, merge
- [ ] 9.5 After merge, run `/opsx:archive seed-initial-dataset`
- [ ] 9.6 After merge, close issue #40 (or leave open if this is only phase 1 of 40's broader scope)

---

### Verification rules

- **Never mark a task `[x]` without running the verification it implies.** Especially:
  - Phase 1 tasks require pytest to pass on the new tests before being marked.
  - Phase 5.4 requires docker and is DEFERRED to the user or a host with docker access.
  - Phase 7 requires docker and is DEFERRED.
  - Phase 3.10 involves publishing to GitHub Releases and requires maintainer approval.

- **Summaries are expensive.** The first successful run of `seed_build.py` generates
  ~5000 chat completions. Estimate ~$0.30 with GPT-4o-mini. Do not iterate on the prompt
  in a loop without reviewing costs.

- **Test runner cwd.** All pytest commands must run from `backend/` so that
  `from app.services...` imports resolve correctly.

- **TDD rule.** Write the failing test first, then the implementation, then verify green.
  Do not skip the failing-test step.
