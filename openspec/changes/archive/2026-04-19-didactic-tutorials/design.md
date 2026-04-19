## Context

The seed dataset has 2 matches (Euro 2024 Final, WC 2022 Final) with ~700 embedded rows. Both PostgreSQL and SQL Server have data. The RAG pipeline works end-to-end. The project has 25 existing questions in `data/questions.json` but they're raw evaluation data, not tutorial content.

## Goals / Non-Goals

**Goals:**
- Create self-contained tutorials that a developer can follow from start to finish
- Use real API calls and real results from the seed data
- Explain the RAG pipeline conceptually, not just "how to click buttons"
- Create a golden set for future automated evaluation

**Non-Goals:**
- Jupyter notebooks (deferred — tutorials as markdown first)
- Tutorial 4 (multi-backend) and Tutorial 5 (embedding models) — depend on #35/#36
- Frontend "tutorial mode" with annotations

## Decisions

### 1. Tutorials as markdown with curl examples
Developers can follow along with `curl` commands against the running stack. This is more portable than notebooks and doesn't require Jupyter setup.

### 2. Use both seed matches for variety
- Euro 2024 Final (Spain 2-1 England) — for Tutorial 1 (simpler, 90 min match)
- WC 2022 Final (Argentina 3-3 France, penalties) — for Tutorial 2 (complex, extra time + pens)

### 3. Golden set with match-specific questions
Each golden set entry references a specific match_id and includes expected answer keywords (not exact match — RAG answers vary by run).

## File change list

| File | Status | Description |
|------|--------|-------------|
| `docs/tutorials/01-first-semantic-search.md` | (new) | Tutorial 1: end-to-end RAG walkthrough |
| `docs/tutorials/02-comparing-search-algorithms.md` | (new) | Tutorial 2: cosine vs inner product vs L2 |
| `docs/tutorials/03-understanding-embeddings.md` | (new) | Tutorial 3: vectors, dimensions, similarity |
| `data/golden_set.json` | (new) | 10+ evaluation questions with expected answers |
| `docs/getting-started.md` | (modified) | Add tutorials section with links |
| `CHANGELOG.md` | (modified) | Update Unreleased |

## Rollback strategy

Delete new files, revert getting-started.md link additions. No code changes.
