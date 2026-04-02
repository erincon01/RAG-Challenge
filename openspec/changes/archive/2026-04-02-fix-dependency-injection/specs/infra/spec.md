## MODIFIED Requirements

### Requirement: All service dependencies injected via Depends()
The system SHALL inject ALL service dependencies via FastAPI `Depends()` providers
registered in `app/core/dependencies.py`. Module-level service instantiation
(`_service = XxxService()`) is PROHIBITED in route modules.

#### Scenario: IngestionService injected in ingestion routes
- **WHEN** a request arrives at any `/api/v1/` ingestion endpoint
- **THEN** `IngestionService` SHALL be resolved via `Depends(get_ingestion_service)`
  and MUST NOT be a module-level singleton

#### Scenario: StatsBombService injected in statsbomb routes
- **WHEN** a request arrives at `/api/v1/statsbomb/*`
- **THEN** `StatsBombService` SHALL be resolved via `Depends(get_statsbomb_service)`
  and MUST NOT be a module-level singleton

#### Scenario: DataExplorerService injected in explorer routes
- **WHEN** a request arrives at `/api/v1/teams`, `/api/v1/players`, or `/api/v1/tables-info`
- **THEN** `DataExplorerService` SHALL be resolved via `Depends(get_data_explorer_service)`
  and MUST NOT be a module-level singleton

#### Scenario: IngestionService accepts StatsBombService as constructor parameter
- **WHEN** `IngestionService` is instantiated
- **THEN** it SHALL accept an optional `statsbomb: StatsBombService | None` parameter
- **AND** when `None` is passed, it SHALL default to `StatsBombService()`
- **AND** this MUST NOT change any existing behavior

#### Scenario: Tests can replace services via dependency_overrides
- **WHEN** a test overrides `get_ingestion_service`, `get_statsbomb_service`,
  or `get_data_explorer_service` via `app.dependency_overrides`
- **THEN** the route handler SHALL use the test-provided mock
- **AND** the test teardown MUST call `app.dependency_overrides.clear()`

## ADDED Requirements

### Requirement: Typed DI aliases for all services
`app/core/dependencies.py` SHALL expose `Annotated` type aliases for all
injectable services, following the existing `MatchRepo` / `EventRepo` pattern:
- `IngestionSvc = Annotated[IngestionService, Depends(get_ingestion_service)]`
- `StatsBombSvc = Annotated[StatsBombService, Depends(get_statsbomb_service)]`
- `ExplorerSvc  = Annotated[DataExplorerService, Depends(get_data_explorer_service)]`

#### Scenario: Route handlers use type aliases
- **WHEN** a route handler declares a service parameter
- **THEN** it SHALL use the typed alias (e.g. `service: IngestionSvc`)
  rather than the verbose `Annotated[..., Depends(...)]` form
