## Approach

Replace direct repository instantiation with FastAPI `Depends()` injection in the two
remaining handlers. The existing DI providers (`get_match_repository`, `get_event_repository`)
already support a `source` parameter — reuse them.

### Strategy

1. **`health.py` readiness check** — inject both Postgres and SQL Server event repositories
   via `Depends()`. The `readiness_check()` handler calls `.test_connection()` on each.
2. **`capabilities.py` source status** — same pattern: inject repositories, call `.test_connection()`.
3. **No new DI providers needed** — `get_event_repository(source)` already exists and returns
   the correct implementation based on source.

### Decision: How to inject both sources

The existing `get_event_repository(source="postgres")` returns one implementation at a time.
For health/capabilities we need both. Options:

**Option A:** Two separate `Depends()` calls with different source defaults.
**Option B:** A new `get_connectivity_checker()` provider that returns both.

**Choice: Option A** — simpler, no new abstractions for 2 call sites. Each handler declares
two parameters with `Depends(get_event_repository)` using different source values.

## File changes

| File | Change |
|------|--------|
| `backend/app/api/v1/health.py` | (modified) Replace direct `PostgresEventRepository()` / `SQLServerEventRepository()` with injected repos |
| `backend/app/api/v1/capabilities.py` | (modified) Same replacement pattern |
| `backend/tests/api/test_health.py` | (modified) Update mocks to use dependency overrides |
| `backend/tests/api/test_capabilities.py` | (modified) Update mocks to use dependency overrides |

## Rollback strategy

Revert the commit. No data migration, no env var changes, no API contract changes.

## Risks

- **[Risk]** Health check currently works without DI container being fully initialized →
  **Mitigation:** `test_connection()` is a simple method that doesn't require other dependencies.
  The repositories are lightweight to construct via `Depends()`.
