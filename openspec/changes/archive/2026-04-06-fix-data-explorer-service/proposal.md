## Why

`DataExplorerService` bypasses the Repository Pattern by managing raw `psycopg2`/`pyodbc`
connections directly (`_get_connection()` at line 22). This violates the architecture rule
that services must delegate all database access to injected repositories. It duplicates
SQL dialect branching already solved in the repository layer, makes unit tests harder
(must mock drivers instead of interfaces), and couples the service to specific driver versions.
The data spec explicitly flags this as a deviation to be reviewed.

## What Changes

- Remove `_get_connection()` and all raw `psycopg2`/`pyodbc` usage from `DataExplorerService`
- Add repository methods for the three queries DataExplorerService currently handles:
  `get_teams()`, `get_players()`, `get_tables_info()`
- Refactor `DataExplorerService` to accept injected repositories and delegate queries
- Simplify unit tests from driver-level mocking to repository interface mocking
- Fully backwards-compatible: API contract (routes, request/response) unchanged

## Capabilities

### New Capabilities

(none — this is a refactoring of existing behavior)

### Modified Capabilities

- `data`: Repository interfaces (`MatchRepository`, `EventRepository`) gain new query methods for teams, players, and table metadata

## Impact

- **Affected layers:** Service (`data_explorer_service.py`), Repository (`base.py`, `postgres.py`, `sqlserver.py`), DI (`dependencies.py`)
- **Affected files:** 6 production files, 2 test files
- **API contract:** No change — routes, request params, and response shapes remain identical
- **Test impact:** Unit tests simplified (mock repos instead of drivers); API tests unchanged
- **Backwards compatibility:** Fully compatible — external behavior identical
- **Breaking:** None
