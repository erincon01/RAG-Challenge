# Seed Dataset

Pre-computed data for two canonical football finals, used to populate the
dashboard on first run without requiring an OpenAI API key.

## What's in the seed

| Match | Competition | `match_id` | Date | Result |
|-------|-------------|------------|------|--------|
| **Spain 2-1 England** | UEFA Euro 2024 Final | `3943043` | 2024-07-14 | AET |
| **Argentina 3-3 France** (pens. 4-2) | FIFA World Cup 2022 Final | `3869685` | 2022-12-18 | Penalties |

Each match directory contains:

| File | Description | Source |
|------|-------------|--------|
| `match.json` | Match metadata (teams, score, competition) | StatsBomb Open Data |
| `events.json` | All match events (~4,000 per match) | StatsBomb Open Data |
| `summaries.jsonl` | Narrative summary per 15-second bucket | Generated with `gpt-4o-mini` |
| `embeddings_t3_small.jsonl` | 1536-dim vector per summary | Generated with `text-embedding-3-small` |

Approximately **~700 embedded rows total** — enough to demo the full
RAG pipeline end-to-end.

## Directory layout

```
data/seed/
  README.md                            # this file
  manifest.json                        # version, embedding model, sha256 per file
  3943043/                             # Euro 2024 Final (Spain 2-1 England)
    match.json
    events.json
    summaries.jsonl
    embeddings_t3_small.jsonl
  3869685/                             # WC 2022 Final (Argentina 3-3 France)
    match.json
    events.json
    summaries.jsonl
    embeddings_t3_small.jsonl
```

## Data source & licensing

Raw match and event data comes from **StatsBomb Open Data**:
<https://github.com/statsbomb/open-data>

Licensed under **CC BY-NC-SA 4.0**. See their repository for the full
license terms. This project uses StatsBomb data for non-commercial
educational purposes.

The original data can also be accessed directly from StatsBomb's GitHub:
- Matches: `https://raw.githubusercontent.com/statsbomb/open-data/master/data/matches/{competition_id}/{season_id}.json`
- Events: `https://raw.githubusercontent.com/statsbomb/open-data/master/data/events/{match_id}.json`

Summaries and embeddings are **generated** by this project using
OpenAI's `gpt-4o-mini` (summaries) and `text-embedding-3-small`
(embeddings), and distributed under the same CC BY-NC-SA 4.0 license.

## How the seed is loaded

On first `Reopen in Container`, `.devcontainer/post-create.sh` calls
`python -m scripts.seed_load --source both`, which:

1. Checks idempotency: if both match_ids are already in the `matches`
   table AND have non-null embeddings in the aggregation table, exits 0
   without touching anything.
2. Reads the seed files from `data/seed/` in the repo.
3. Verifies sha256 of every file against `manifest.json`.
4. Stages the match + events JSON files into the layout expected by
   `IngestionService._load_matches` / `_load_events`.
5. Runs the load + aggregate steps against both PostgreSQL and SQL Server.
6. UPDATEs `summary` and `summary_embedding_t3_small` columns from the
   pre-computed JSONL files.

**No OpenAI calls. No API key required.**

## How to seed manually

```bash
make seed                           # both databases
make seed-force                     # re-seed even if already present
cd backend && python -m scripts.seed_load --source postgres
cd backend && python -m scripts.seed_load --source sqlserver
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

## How to regenerate the seed (maintainer only)

The seed is built once per `vN` bump by a maintainer with an OpenAI key.
The process is **paid** (~$0.30 with `gpt-4o-mini` + `text-embedding-3-small`
for both matches).

```bash
# 1. Set OPENAI_KEY in .env.docker
# 2. Start the full stack
docker compose up -d

# 3. Build the seed — runs the full pipeline then exports from Postgres
cd backend
python -m scripts.seed_build --i-have-budget --output /tmp/seed-v1.tar.gz

# 4. Extract into data/seed/ (overwrite existing)
tar xzf /tmp/seed-v1.tar.gz -C ../data/seed/ --strip-components=2

# 5. Commit the updated seed files
```

To add more matches to a future version, edit `SEED_MATCH_IDS` in
`backend/scripts/seed_build.py` and `backend/scripts/seed_load.py`.
