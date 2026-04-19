## Context

The project has 3 embedding models defined in `EmbeddingModel` enum and `SOURCE_CAPABILITIES`. Only `text-embedding-3-small` has actual data (717 rows with embeddings in the seed). The ada-002 and t3-large columns exist in the DB schema but are always NULL. The frontend capabilities endpoint exposes all 3, and the chat developer mode lets users select them — but selecting ada-002 or t3-large returns zero results.

## Goals / Non-Goals

**Goals:**
- Remove deprecated models from the capabilities matrix so they stop appearing in UI
- Standardize IngestionService defaults to t3-small only
- Mark enum members as deprecated for code clarity
- Keep schema columns and enum values for backward compat (no migration)

**Non-Goals:**
- Dropping schema columns (separate migration, deferred)
- Adding new models (issue #36 — multi-provider LLM)
- Changing the embedding dimension (stays at 1536)

## Decisions

### 1. Soft deprecation via capabilities, not enum removal
Remove models from `SOURCE_CAPABILITIES` so the API/UI stops offering them. Keep `EmbeddingModel.ADA_002` and `T3_LARGE` in the enum with a `# deprecated` comment so existing code that references them (e.g., column mappings) doesn't break.

**Alternative rejected:** Remove enum members entirely — breaks column mapping dicts in repositories and ingestion service.

### 2. Single active model per source
Both postgres and sqlserver get `["text-embedding-3-small"]` only. This simplifies the UI (no model dropdown needed in user mode) and matches what the seed data actually provides.

## File change list

| File | Status | Description |
|------|--------|-------------|
| `backend/app/core/capabilities.py` | (modified) | Remove ada-002 and t3-large from embedding_models lists |
| `backend/app/domain/entities.py` | (modified) | Add deprecation comments to ADA_002 and T3_LARGE |
| `backend/app/services/ingestion_service.py` | (modified) | Update default models to t3-small only |
| `backend/tests/unit/test_capabilities.py` | (modified) | Update assertions for 1 model per source |
| `backend/tests/unit/test_search_service.py` | (modified) | Update if referencing deprecated models |

## Risks / Trade-offs

- **[Existing ada-002/t3-large data becomes inaccessible via UI]** → Acceptable — those columns are NULL in practice. If a user previously generated ada-002 embeddings, they can still query them via direct API with the model parameter (enum still exists).
- **[Schema columns waste storage]** → Deferred to a future migration change. ~0 cost since columns are NULL.

## Rollback strategy

Revert `capabilities.py` to add back the 3 models. No data changes to undo.
