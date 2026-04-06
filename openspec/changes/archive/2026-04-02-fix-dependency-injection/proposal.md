## Why

Several route modules instantiate services at module level (`_service = XxxService()`),
bypassing FastAPI's `Depends()` mechanism. This breaks testability (impossible to swap
dependencies in tests), violates the project's DI contract, and creates hidden coupling
between modules and their transitive dependencies.

## What Changes

- Remove all module-level service instantiations from API route files.
- Register `IngestionService`, `StatsBombService`, and `DataExplorerService` as providers
  in `app/core/dependencies.py` following the existing pattern.
- Inject services via `Annotated[XxxService, Depends(get_xxx_service)]` in route handlers.
- Update all affected tests to use `app.dependency_overrides` instead of patching internals.
- No behavioral changes — purely a structural refactor for correctness and testability.

## Capabilities

### New Capabilities

*(none — no new user-facing capabilities)*

### Modified Capabilities

- `api`: DI contract for all route handlers now uniformly enforced via `Depends()`.
  No request/response contract changes; only internal wiring changes.
- `infra`: `core/dependencies.py` gains three new providers
  (`get_ingestion_service`, `get_statsbomb_service`, `get_data_explorer_service`).

## Impact

**Affected files:**
- `backend/app/api/v1/ingestion.py` — remove `_ingestion_service = IngestionService()`
- `backend/app/api/v1/statsbomb.py` — remove `_statsbomb_service = StatsBombService()`
- `backend/app/api/v1/explorer.py` — remove `_explorer_service = DataExplorerService()`
- `backend/app/core/dependencies.py` — add 3 new provider functions
- `backend/tests/api/test_*.py` — update mocking strategy for affected routes

**Backward compatibility:** Full. No API contract changes (endpoints, request/response
schemas, or behavior are unchanged).

**Layers affected:** API, Core (DI wiring). Service and Domain layers untouched.

**Test impact:** Tests for ingestion, statsbomb, and explorer routes must switch from
patching module-level instances to using `app.dependency_overrides`.
