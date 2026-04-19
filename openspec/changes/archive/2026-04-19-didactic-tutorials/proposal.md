## Why

The project has strong educational potential — it demonstrates a complete RAG pipeline with real football data, dual databases, and semantic search. But there are no step-by-step tutorials for learning. A developer who clones the repo can run it, but doesn't understand HOW it works or WHY design decisions were made. Tutorials 1-3 from issue #39 have no dependencies and can be created now using the existing seed data.

## What Changes

- Create `docs/tutorials/` directory with 3 step-by-step tutorials
- **Tutorial 1**: "Your first semantic search" — from question to answer, explaining each RAG pipeline step
- **Tutorial 2**: "Comparing search algorithms" — cosine vs inner product vs L2, with real results
- **Tutorial 3**: "Understanding embeddings" — what vectors are, how similarity works, 1536 dimensions explained
- Create `data/golden_set.json` — 10+ questions with expected answers for evaluation
- Link tutorials from README and getting-started

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
_(none — documentation only)_

## Impact

- **Docs**: `docs/tutorials/` (new directory, 3 markdown files)
- **Data**: `data/golden_set.json` (new)
- **Docs**: `docs/getting-started.md`, `README.md` (modified — add tutorial links)
- **Backward compatibility**: fully backward-compatible — docs and data only
- **Affected layers**: none
- **Test impact**: none
