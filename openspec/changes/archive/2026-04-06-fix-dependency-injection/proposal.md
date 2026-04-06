## Why

Two API handlers (`health.py` and `capabilities.py`) instantiate repository implementations
directly (`PostgresEventRepository()`, `SQLServerEventRepository()`) instead of using
FastAPI `Depends()`. This violates the DI architecture rule, makes those handlers untestable
without a live database, and creates tight coupling to concrete implementations.

All other handlers already use `Depends()` correctly — these two are the last holdouts.

## What Changes

- Replace direct `PostgresEventRepository()` / `SQLServerEventRepository()` instantiation
  in `health.py` readiness check with injected repositories
- Replace direct instantiation in `capabilities.py` source status check with injected repositories
- Add a DI provider for health/connectivity checks if needed
- Update tests to use dependency overrides instead of mocking constructors

## Capabilities

### New Capabilities

(none — this is a refactoring of existing behavior)

### Modified Capabilities

- `api`: Health and capabilities endpoints use injected repositories instead of direct instantiation

## Impact

- **Affected layers:** API (`health.py`, `capabilities.py`), DI (`dependencies.py`)
- **Affected files:** 2 handler files, 1 DI file, 2 test files
- **API contract:** No change — response shapes and status codes remain identical
- **Test impact:** Health/capabilities tests can use dependency overrides (no live DB needed)
- **Backwards compatibility:** Fully compatible
- **Breaking:** None
