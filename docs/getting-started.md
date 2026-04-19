# Getting Started — RAG-Challenge

Guide for new contributors (human or AI) to start producing in 10 minutes.

## 1. Setup

### DevContainer (recommended)

Open the repo in VS Code — accept the "Reopen in Container" prompt. Everything starts automatically (backend, frontend, PostgreSQL, SQL Server).

### Docker Compose (without DevContainer)

```bash
git clone https://github.com/erincon01/RAG-Challenge.git
cd RAG-Challenge && git checkout develop
cp .env.docker.example .env.docker   # edit: set OPENAI_KEY and OPENAI_ENDPOINT
docker compose up --build
```

### Verify it works

- Frontend: http://localhost:5173
- Backend docs: http://localhost:8000/docs
- Tests: `cd backend && pytest tests/ -v` (530+ tests, no DB needed)

### First run — seed dataset

On first container open, `.devcontainer/post-create.sh` automatically
loads the **seed dataset**: two iconic finals with pre-computed summaries
and embeddings that are **included in the repository** under `data/seed/`.

| Match | Competition | match_id |
|---|---|---|
| **Spain 2-1 England** | UEFA Euro 2024 Final | 3943043 |
| **Argentina 3-3 France** (pens. 4-2) | FIFA World Cup 2022 Final | 3869685 |

The seed is **pre-computed**: summaries (generated with `gpt-4o-mini`)
and 1536-dim embeddings (generated with `text-embedding-3-small`) are
already in the repo, so **no OpenAI key is required** to populate the
dashboard on first run. No network download is needed either.

Raw match and event data comes from
[StatsBomb Open Data](https://github.com/statsbomb/open-data)
(CC BY-NC-SA 4.0).

If the seed load failed, the devcontainer still starts. You can retry with:

```bash
make seed                            # both databases
make seed-postgres                   # postgres only
make seed-sqlserver                  # sqlserver only
cd backend && python -m scripts.seed_load --source both --force  # re-seed
```

The seed loads into **both PostgreSQL and SQL Server**. You can switch
between them at any time using the **Source** dropdown in the header.

> **Note:** SQL Server starts slower (~30s vs ~5s for PostgreSQL). If the
> seed load fails for SQL Server, wait a moment and retry with `make seed-sqlserver`.
> See [docs/sql-server-setup.md](sql-server-setup.md) for troubleshooting.

After a successful seed load, the dashboard at http://localhost:5173/dashboard
should show 2 matches in the explorer, and the chat page can answer
questions about them (**the chat runtime still needs `OPENAI_KEY` set
in `.env.docker`** — only the seed loading is offline).

### Adding more matches (requires OpenAI key)

To ingest a new match with the full pipeline (download → load → aggregate
→ summaries → embeddings):

```bash
curl -X POST http://localhost:8000/api/v1/ingestion/full-pipeline \
  -H "Content-Type: application/json" \
  -d '{
    "source": "postgres",
    "match_ids": [3943077],
    "competition_id": 55,
    "season_id": 282
  }'
```

This requires `OPENAI_KEY` to be set and will consume OpenAI tokens
(approximately $0.15-0.30 per match with GPT-4o-mini + text-embedding-3-small).

## 2. Understand the project

| Read this | To understand |
|-----------|--------------|
| [README.md](../README.md) | What the project does, architecture, tech stack |
| [AGENTS.md](../AGENTS.md) | All project rules — architecture, DI, testing, git, security |
| [docs/architecture.md](architecture.md) | System design and layer diagram |
| [docs/tech-stack.md](tech-stack.md) | Technology versions and configuration |
| [openspec/specs/](../openspec/specs/) | Current system specs (api, rag, data, infra) |

## 3. How to make changes (OpenSpec workflow)

This project uses **spec-driven development** with [OpenSpec](https://github.com/Fission-AI/OpenSpec). Every change follows a 3-step process: **propose → apply → archive**.

### Step 1: Propose

Before writing code, create a change proposal:

```
/opsx:propose <change-name>
```

Example: `/opsx:propose add-rate-limiting`

This generates 4 artifacts in `openspec/changes/<name>/`:
- `proposal.md` — Why this change? What's affected?
- `design.md` — How? File changes, approach, rollback strategy
- `specs/<capability>/spec.md` — Delta spec (what behavior changes)
- `tasks.md` — Implementation checklist grouped by layer

### Step 2: Apply

Implement the tasks from the proposal:

```
/opsx:apply <change-name>
```

The agent reads the tasks and implements them one by one, following TDD:
1. Write the test (Red)
2. Write the minimum code to pass (Green)
3. Run `pytest` on the file before marking the task `[x]`
4. Run the full suite before finishing

### Step 3: Archive

After the PR is merged:

```
/opsx:archive <change-name>
```

This moves the change to `openspec/changes/archive/` and syncs delta specs into the main specs at `openspec/specs/`.

### Example: full cycle

```
# 1. Propose
/opsx:propose fix-rate-limiting

# 2. Review the artifacts in openspec/changes/fix-rate-limiting/
#    Adjust if needed, then apply

# 3. Apply (creates branch, implements tasks, runs tests)
/opsx:apply fix-rate-limiting

# 4. Create PR, get it reviewed and merged

# 5. Archive
/opsx:archive fix-rate-limiting
```

### Parallel changes

If you have 2-3 independent changes (different files/layers), you can apply them in parallel using worktrees:

1. Propose all changes on `develop` (sequential)
2. Launch agents with `isolation: "worktree"` (one per change)
3. Each produces a PR against `develop`
4. Merge PRs sequentially

See `AGENTS.md` § "Parallel development with worktrees" for rules.

## 4. Key rules (summary)

- **Architecture:** API → Services → Repositories → Domain → Adapters (one-way dependency)
- **DI:** All dependencies via FastAPI `Depends()` — no module-level singletons
- **Testing:** TDD, 80% coverage minimum, naming: `test_<method>_<scenario>_<expected>`
- **Git:** Branch from `develop`, conventional commits, update CHANGELOG
- **Security:** No `allow_origins=["*"]`, no hardcoded secrets, parameterized SQL only
- **No AI attribution** in commits, PRs, or code

## 5. Key commands

```bash
# Tests
cd backend && pytest tests/ -v
cd backend && pytest tests/ --cov=app --cov-fail-under=80

# Lint & format
ruff check backend/app
ruff format backend/app

# Type check
mypy backend/app

# Docker
docker compose up --build
```

## 6. Tutorials

Learn how the RAG pipeline works with step-by-step guides using the seed data:

| Tutorial | What you'll learn |
|----------|------------------|
| [01 — Your first semantic search](tutorials/01-first-semantic-search.md) | End-to-end RAG query: question → embedding → vector search → LLM answer |
| [02 — Comparing search algorithms](tutorials/02-comparing-search-algorithms.md) | Cosine vs inner product vs L2 Euclidean with real results |
| [03 — Understanding embeddings](tutorials/03-understanding-embeddings.md) | What vectors are, 1536 dimensions, the embedding pipeline |

A golden set of evaluation questions is available at `data/golden_set.json`.

## 7. Where to find things

| What | Where |
|------|-------|
| API endpoints | `backend/app/api/v1/` |
| Business logic | `backend/app/services/` |
| Database access | `backend/app/repositories/` (postgres.py, sqlserver.py) |
| Domain entities | `backend/app/domain/entities.py` |
| OpenAI integration | `backend/app/adapters/openai_client.py` |
| DI providers | `backend/app/core/dependencies.py` |
| Configuration | `config/settings.py` (Pydantic BaseSettings) |
| Frontend pages | `frontend/webapp/src/pages/` |
| API client | `frontend/webapp/src/lib/api/client.ts` |
| System specs | `openspec/specs/{api,rag,data,infra}/spec.md` |
| Archived changes | `openspec/changes/archive/` |
| Test fixtures | `backend/tests/conftest.py` |
