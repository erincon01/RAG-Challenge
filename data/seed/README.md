# Seed Dataset

Pre-computed data for two canonical football finals, used to populate the
dashboard on first run without requiring an OpenAI API key.

## What's in the seed

| Match | Competition | `match_id` | Date | Result |
|-------|-------------|------------|------|--------|
| **Spain 2-1 England** | UEFA Euro 2024 Final | `3943043` | 2024-07-14 | AET |
| **Argentina 3-3 France** (pens. 4-2) | FIFA World Cup 2022 Final | `3869685` | 2022-12-18 | Penalties |

Both matches have:

- Raw StatsBomb match metadata
- Raw events (~4,000 events per match across 120+ minutes)
- 15-second bucket aggregations (~2,500 rows per match)
- LLM-generated narrative summaries for each bucket
- Pre-computed `text-embedding-3-small` vectors (1536 dims) for each summary

Approximately **5,000 embedded rows total** — enough to demo the full
RAG pipeline end-to-end.

## Data source & licensing

Raw data comes from **StatsBomb Open Data** (
<https://github.com/statsbomb/open-data>
), licensed under **CC BY-NC-SA 4.0**. See their repo for the full license
and terms. This project references StatsBomb data for non-commercial
educational use, downloading it on demand from their public GitHub.

Summaries and embeddings are **generated** by this project using
OpenAI's `gpt-4o-mini` (summaries) and `text-embedding-3-small`
(embeddings), and distributed under the same CC BY-NC-SA 4.0 license.

**StatsBomb raw JSON is NOT committed to this repository.** The seed
tarball hosted on GitHub Releases is a derivative work containing
pre-processed aggregations and generated narratives — no raw event data
from StatsBomb is stored in git.

## Where the seed lives

The actual seed tarball is published as a **GitHub Release asset** at:

<https://github.com/erincon01/RAG-Challenge/releases/download/seed/v1/seed-v1.tar.gz>

It is **not** in this directory and **not** in git history. This
README is the only thing shipped in the repo; the tarball is downloaded
on demand by `backend/scripts/seed_load.py` into `~/.cache/rag-challenge-seed/`.

## How the seed is loaded

On first `Reopen in Container`, `.devcontainer/post-create.sh` calls
`python -m scripts.seed_load --source both`, which:

1. Checks idempotency: if both match_ids are already in the `matches`
   table AND have non-null embeddings in the aggregation table, exits 0
   without touching anything.
2. Downloads the tarball from the GitHub Release (if not already cached
   locally).
3. Verifies sha256 of every file against `manifest.json`.
4. Stages the match + events JSON files into the layout expected by
   `IngestionService._load_matches` / `_load_events`.
5. Runs the load + aggregate steps against both PostgreSQL and SQL Server.
6. UPDATEs `summary` and `summary_embedding_t3_small` columns from the
   pre-computed JSONL files inside the tarball.

**No OpenAI calls. No API key required.**

## How to re-seed manually

If the automatic post-create seed load fails (network issues, seed not
yet published, etc.) or you want to reset:

```bash
make seed                           # both databases
make seed-force                     # re-seed even if already present
cd backend && python -m scripts.seed_load --source postgres
cd backend && python -m scripts.seed_load --source sqlserver
```

To clear the local cache and force a fresh download:

```bash
rm -rf ~/.cache/rag-challenge-seed
make seed
```

To remove seed data from the database:

```sql
-- PostgreSQL
DELETE FROM events_details__quarter_minute WHERE match_id IN (3943043, 3869685);
DELETE FROM events_details WHERE match_id IN (3943043, 3869685);
DELETE FROM events WHERE match_id IN (3943043, 3869685);
DELETE FROM matches WHERE match_id IN (3943043, 3869685);

-- SQL Server (same statements, uses `events_details__15secs_agg` for the agg table)
```

## How to regenerate the seed tarball (maintainer only)

The seed is built once per `vN` bump by a maintainer with an OpenAI key.
The process is **paid** (~$0.30 with `gpt-4o-mini` + `text-embedding-3-small`
for both matches).

```bash
# 1. Set OPENAI_KEY in backend/.env or .env.docker
# 2. Start the full stack
docker compose up -d

# 3. Build the seed — runs the full pipeline then exports from Postgres
cd backend
python -m scripts.seed_build --i-have-budget --output ../seed-v1.tar.gz

# 4. Review the output
tar tzf ../seed-v1.tar.gz | head -20

# 5. Publish
gh release create seed/v1 ../seed-v1.tar.gz \
  --title "Seed dataset v1" \
  --notes "Pre-computed summaries and embeddings for Euro 2024 + WC 2022 finals."
```

To add more matches to a future version, edit `SEED_MATCH_IDS` in
`backend/scripts/seed_build.py` and `backend/scripts/seed_load.py`, bump
`SEED_VERSION` to `v2`, rebuild, and publish a new Release at `seed/v2`.

## Tarball layout

```
seed/
  v1/
    manifest.json              # version, embedding model, sha256 per file
    3943043/
      match.json               # raw StatsBomb match metadata
      events.json              # raw StatsBomb events list
      summaries.jsonl          # one {row_id, match_id, period, minute, quarter_minute, summary} per line
      embeddings_t3_small.jsonl  # one {row_id, vector} per line (1536-dim)
    3869685/
      match.json
      events.json
      summaries.jsonl
      embeddings_t3_small.jsonl
```

`manifest.json` schema:

```json
{
  "version": "v1",
  "embedding_model": "text-embedding-3-small",
  "matches": [
    {"match_id": 3943043, "label": "Euro 2024 Final (Spain 2-1 England)", "competition_id": 55, "season_id": 282},
    {"match_id": 3869685, "label": "World Cup 2022 Final (Argentina 3-3 France, pens 4-2)", "competition_id": 43, "season_id": 106}
  ],
  "files": {
    "3943043/match.json": "abc123...",
    "3943043/events.json": "def456...",
    "...": "..."
  }
}
```
