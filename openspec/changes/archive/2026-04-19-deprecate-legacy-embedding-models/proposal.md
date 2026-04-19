## Why

The project advertises 3 embedding models (ada-002, t3-small, t3-large) in the capabilities matrix, but only `text-embedding-3-small` is actually used — the seed dataset has t3-small embeddings only, the schema columns for ada-002 and t3-large are always NULL, and generating embeddings for deprecated models wastes API budget. The dashboard and chat developer mode show all 3 as selectable, misleading users into thinking they work. This addresses issue #34.

## What Changes

- Mark `text-embedding-ada-002` and `text-embedding-3-large` as **deprecated** in the `EmbeddingModel` enum
- Remove ada-002 and t3-large from the capabilities matrix (`SOURCE_CAPABILITIES`) so they no longer appear in the UI
- Keep the enum values and schema columns for backward compatibility (no data migration yet)
- Update default embedding models in `IngestionService` to only use t3-small
- Standardize on `text-embedding-3-small` (1536 dims) as the sole active model
- Update tests that reference deprecated models

## Capabilities

### New Capabilities

_(none)_

### Modified Capabilities
- `rag`: the embedding model selection is narrowed to t3-small only; ada-002 and t3-large are deprecated

## Impact

- **Domain** (`app/domain/entities.py`): deprecation annotation on enum members
- **Core** (`app/core/capabilities.py`): remove deprecated models from capabilities lists
- **Services** (`app/services/ingestion_service.py`): update default models to t3-small only
- **Tests**: update any tests that assert on 3 models or reference deprecated models
- **Backward compatibility**: fully backward-compatible — schema columns remain, existing data untouched, deprecated models still parseable by enum but not offered in UI
- **Affected layers**: Domain, Core, Services, Tests (no API endpoint changes, no Repository changes)
- **Test impact**: update capability-related tests, embedding status tests; all existing backend tests must pass
