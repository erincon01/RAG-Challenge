## MODIFIED Requirements

### Requirement: SQL Server setup documentation
The project SHALL include a dedicated `docs/sql-server-setup.md` document that covers Docker setup, schema structure, naming differences from PostgreSQL, seed loading, and troubleshooting.

#### Scenario: Developer follows SQL Server setup guide
- **GIVEN** a developer reads `docs/sql-server-setup.md`
- **WHEN** they follow the step-by-step instructions
- **THEN** they SHALL have SQL Server running in Docker with seed data loaded and RAG search functional

#### Scenario: Schema differences are documented
- **GIVEN** a developer reads `docs/data-model.md`
- **WHEN** they look for SQL Server specifics
- **THEN** they SHALL find a mapping table showing PostgreSQL vs SQL Server table/column names

### Requirement: Getting started covers both databases
The `docs/getting-started.md` guide SHALL include SQL Server-specific notes alongside PostgreSQL setup, including startup time differences and troubleshooting.

#### Scenario: Getting started mentions SQL Server
- **GIVEN** a developer reads `docs/getting-started.md`
- **WHEN** they look for SQL Server information
- **THEN** they SHALL find notes about SQL Server Docker setup, slower startup, and how to verify data loaded
