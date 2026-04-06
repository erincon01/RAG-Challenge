## Approach

Refactor `DataExplorerService` to delegate database access to injected repositories,
following the existing Repository Pattern. The service keeps its orchestration role
but loses all raw driver code.

### Strategy

1. **Extend repository interfaces** — add `get_teams()`, `get_players()`, `get_tables_info()` to `MatchRepository` (teams/players relate to matches) or introduce a lightweight `ExplorerRepository` if methods don't fit the existing abstractions.
2. **Implement in both backends** — `PostgresMatchRepository` and `SQLServerMatchRepository` get the new methods with their respective SQL dialects.
3. **Refactor service** — inject repositories, remove `_get_connection()`, `_table_exists()`, and all `psycopg2`/`pyodbc` imports.
4. **Update DI provider** — `get_data_explorer_service()` passes repositories from existing DI.
5. **Simplify tests** — mock at repository interface level instead of driver level.

### Decision: Where to put the new methods

**Option A:** Add to `MatchRepository` — teams/players are match-related data.
**Option B:** New `ExplorerRepository` — these are metadata/exploration queries, different from domain queries.

**Choice: Option A** — the queries are about match-related entities (teams, players). Adding a new repository for 3 methods would be over-abstraction. `get_tables_info()` is a DB metadata query that fits in `BaseRepository`.

## File changes

| File | Change |
|------|--------|
| `backend/app/repositories/base.py` | (modified) Add `get_teams()`, `get_players()` to `MatchRepository`; add `get_tables_info()` to `BaseRepository` |
| `backend/app/repositories/postgres.py` | (modified) Implement new methods in `PostgresMatchRepository` |
| `backend/app/repositories/sqlserver.py` | (modified) Implement new methods in `SQLServerMatchRepository` |
| `backend/app/services/data_explorer_service.py` | (modified) Remove raw connections, delegate to injected repos |
| `backend/app/core/dependencies.py` | (modified) Update `get_data_explorer_service()` to pass repos |
| `backend/tests/unit/test_dependencies_and_explorer_service.py` | (modified) Simplify mocks to repository level |

## Rollback strategy

All changes are internal refactoring — the API contract is unchanged.
Rollback: revert the commit. No data migration, no env var changes, no breaking API changes.

## Risks

- **[Risk]** Existing tests mock at driver level → **Mitigation:** rewrite tests to mock repository interfaces, which is simpler and catches more real bugs
- **[Risk]** SQL queries may behave differently when moved to repository → **Mitigation:** preserve exact SQL, just move it; API tests verify end-to-end behavior
