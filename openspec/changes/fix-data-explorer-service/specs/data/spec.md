## MODIFIED Requirements

### Requirement: Repository interfaces for exploration queries

`MatchRepository` SHALL provide the following additional methods:

- `get_teams(match_id: Optional[int], limit: int) -> List[Dict[str, Any]]`
  Returns team metadata (team_id, name, gender, country, manager).
- `get_players(match_id: Optional[int], limit: int) -> List[Dict[str, Any]]`
  Returns player roster data (player_id, name, jersey_number, country, position, team_name).

`BaseRepository` SHALL provide:

- `get_tables_info() -> List[Dict[str, Any]]`
  Returns table metadata (name, row_count, columns, has_embedding).

`DataExplorerService` MUST NOT import or use `psycopg2` or `pyodbc` directly.
All database access MUST go through injected repository instances.

### Requirement: Backwards compatibility

The API contract for `/api/v1/teams`, `/api/v1/players`, and `/api/v1/tables-info`
MUST remain unchanged. Response shapes, status codes, and query parameters SHALL
be identical before and after the refactoring.

#### Scenario: Teams query via repository
- **GIVEN** a `DataExplorerService` with an injected `MatchRepository`
- **WHEN** `get_teams(source="postgres")` is called
- **THEN** the service SHALL delegate to `match_repo.get_teams()` without creating any raw connection

#### Scenario: No raw driver imports in service
- **GIVEN** the refactored `DataExplorerService`
- **WHEN** inspecting its imports
- **THEN** neither `psycopg2` nor `pyodbc` SHALL appear

### REMOVED Deviation

The known deviation "DataExplorerService bypasses the Repository Pattern" SHALL be removed
from `openspec/specs/data/spec.md` after this change is implemented.
