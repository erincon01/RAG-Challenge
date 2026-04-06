## 1. Repository layer

- [x] 1.1 Add abstract methods `get_teams(match_id, limit)` and `get_players(match_id, limit)` to `MatchRepository` in `base.py`
- [x] 1.2 Add abstract method `get_tables_info()` to `BaseRepository` in `base.py`
- [x] 1.3 Implement `get_teams()` and `get_players()` in `PostgresMatchRepository` (move SQL from service)
- [x] 1.4 Implement `get_teams()` and `get_players()` in `SQLServerMatchRepository` (move SQL from service)
- [x] 1.5 Implement `get_tables_info()` in both Postgres and SQL Server base repositories

## 2. Service layer

- [x] 2.1 Refactor `DataExplorerService.__init__()` to accept `MatchRepository` instead of `Settings`
- [x] 2.2 Refactor `get_teams()`, `get_players()`, `get_tables_info()` to delegate to repository
- [x] 2.3 Remove `_get_connection()`, `_table_exists()`, and all `psycopg2`/`pyodbc` imports

## 3. DI layer

- [x] 3.1 Update `get_data_explorer_service()` in `dependencies.py` to pass `MatchRepository`

## 4. Tests (TDD — write before implementation)

- [x] 4.1 Write unit test: `test_get_teams_delegates_to_repository` — verify service calls `match_repo.get_teams()`
- [x] 4.2 Write unit test: `test_get_players_delegates_to_repository` — verify service calls `match_repo.get_players()`
- [x] 4.3 Write unit test: `test_get_tables_info_delegates_to_repository` — verify service calls `repo.get_tables_info()`
- [x] 4.4 Write unit test: `test_service_has_no_psycopg2_import` — verify no raw driver imports
- [x] 4.5 Update existing API tests if any mock patching paths changed
- [x] 4.6 Run full test suite and verify 80%+ coverage maintained
