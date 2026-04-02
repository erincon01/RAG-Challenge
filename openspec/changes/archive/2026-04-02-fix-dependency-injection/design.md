## Context

Three API route modules instantiate their services at **module load time** using
module-level variables (`_service = XxxService()`). This pattern predates the
project's DI conventions and now violates them:

- `backend/app/api/v1/embeddings.py` — `_service = IngestionService()`
- `backend/app/api/v1/ingestion.py` — `_service = IngestionService()`
- `backend/app/api/v1/statsbomb.py` — `_service = StatsBombService()`
- `backend/app/api/v1/explorer.py` — `_service = DataExplorerService()`

Additionally, `IngestionService.__init__` creates `StatsBombService()` internally,
making it impossible to inject a test double for the StatsBomb HTTP client.

The established pattern (used by `matches.py`, `events.py`, `chat.py`) is:
1. Provider function in `app/core/dependencies.py`
2. `Annotated[XxxService, Depends(get_xxx_service)]` in route handler signature
3. `app.dependency_overrides[get_xxx_service] = lambda: mock` in tests

## Goals / Non-Goals

**Goals:**
- Move all four service instantiations from module level to `Depends()` providers.
- Add providers for `IngestionService`, `StatsBombService`, `DataExplorerService`
  to `app/core/dependencies.py`.
- Accept `StatsBombService` as a constructor parameter in `IngestionService`
  (instead of instantiating it internally) so both can be injected independently.
- Update tests to use `dependency_overrides` instead of patch.

**Non-Goals:**
- Changing any service business logic.
- Changing any API contracts (endpoints, request/response schemas, status codes).
- Migrating `IngestionService`'s direct psycopg2/pyodbc calls to repositories
  (separate concern, separate change).

## Decisions

### Decision 1 — Provider location: `core/dependencies.py`

All providers go into `app/core/dependencies.py`, which is the existing single
location for FastAPI DI wiring. No new files needed.

*Alternative considered:* co-locating providers with their service file.
Rejected: scatters wiring logic; the project already has a dedicated DI module.

### Decision 2 — `StatsBombService` as `IngestionService` constructor argument

`IngestionService.__init__` currently creates `StatsBombService()` directly.
We add an optional `statsbomb: StatsBombService | None = None` parameter,
defaulting to `StatsBombService()` when not provided. This keeps backward
compatibility (no callers break) while enabling injection in tests.

*Alternative considered:* passing `StatsBombService` via a separate setter.
Rejected: constructor injection is simpler and conventional in this codebase.

### Decision 3 — `IngestionService` and `DataExplorerService` are stateless

Both services only use `get_settings()` in `__init__`. Creating a new instance
per request is acceptable and consistent with how `SearchService` is handled.
No singleton optimization needed.

### Decision 4 — Type aliases for readability

Following the existing `MatchRepo` / `EventRepo` pattern, add:
```python
IngestionSvc = Annotated[IngestionService, Depends(get_ingestion_service)]
StatsBombSvc = Annotated[StatsBombService, Depends(get_statsbomb_service)]
ExplorerSvc  = Annotated[DataExplorerService, Depends(get_data_explorer_service)]
```

## File Change List

| File | Change |
|------|--------|
| `backend/app/core/dependencies.py` | (modified) — add 3 provider functions + 3 type aliases |
| `backend/app/services/ingestion_service.py` | (modified) — accept `StatsBombService` as constructor param |
| `backend/app/api/v1/ingestion.py` | (modified) — remove `_service`, inject via `Depends` |
| `backend/app/api/v1/embeddings.py` | (modified) — remove `_service`, inject via `Depends` |
| `backend/app/api/v1/statsbomb.py` | (modified) — remove `_service`, inject via `Depends` |
| `backend/app/api/v1/explorer.py` | (modified) — remove `_service`, inject via `Depends` |
| `backend/tests/api/test_statsbomb.py` | (modified) — use `dependency_overrides` |
| `backend/tests/api/test_events.py` | (modified) — verify no regression |

## Risks / Trade-offs

- **Per-request instantiation** — Creating `IngestionService` per request is slightly
  less efficient than a singleton. Acceptable since ingestion endpoints are low-frequency.
  → Mitigation: profile if needed; add singleton caching later if measured.

- **Test coverage gap** — Tests for ingestion and explorer routes may currently rely on
  the module-level `_service` being patchable. Switching to `dependency_overrides` is
  strictly superior but requires updating the mock strategy.
  → Mitigation: update tests as part of this change; CI enforces 80% coverage.

## Migration / Rollback

**Migration:** Pure refactor — no data migration, no config change, no schema change.
The change is safe to deploy without coordination.

**Rollback:** Revert the 6-8 modified files. No state to restore.
