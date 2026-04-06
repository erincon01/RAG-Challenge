## MODIFIED Requirements

### Requirement: Health and capabilities handlers use DI

The `readiness_check()` handler in `health.py` MUST receive repository instances via
FastAPI `Depends()` injection. It MUST NOT instantiate `PostgresEventRepository` or
`SQLServerEventRepository` directly.

The `get_sources_status()` handler in `capabilities.py` MUST follow the same pattern.

#### Scenario: Readiness check uses injected repositories
- **GIVEN** a FastAPI app with DI overrides for repositories
- **WHEN** `GET /api/v1/health/ready` is called
- **THEN** the handler SHALL use the injected repository's `test_connection()` method
- **AND** SHALL NOT import or instantiate concrete repository classes

#### Scenario: Capabilities source status uses injected repositories
- **GIVEN** a FastAPI app with DI overrides for repositories
- **WHEN** `GET /api/v1/capabilities/sources` is called
- **THEN** the handler SHALL use the injected repository's `test_connection()` method

### REMOVED Deviation

Any known deviation about direct repository instantiation in health/capabilities handlers
SHALL be removed after this change.
