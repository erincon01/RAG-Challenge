## MODIFIED Requirements

### Requirement: Supported embedding models
The system SHALL support only `text-embedding-3-small` (1536 dimensions) as the active embedding model. The models `text-embedding-ada-002` and `text-embedding-3-large` SHALL be deprecated and MUST NOT appear in the capabilities API response or the frontend UI.

#### Scenario: Capabilities endpoint returns only active model
- **GIVEN** a client requests `GET /api/v1/capabilities`
- **WHEN** the response is received
- **THEN** `embedding_models` for both postgres and sqlserver SHALL contain only `["text-embedding-3-small"]`

#### Scenario: Deprecated models are not selectable in chat developer mode
- **GIVEN** a user is on the Chat page in developer mode
- **WHEN** the embedding model dropdown is displayed
- **THEN** only `text-embedding-3-small` SHALL be available as an option

#### Scenario: Ingestion pipeline uses only active model
- **GIVEN** a developer runs the embedding generation step without specifying models
- **WHEN** the default models are resolved
- **THEN** only `text-embedding-3-small` SHALL be used for both postgres and sqlserver

#### Scenario: Deprecated enum members remain parseable
- **GIVEN** existing code references `EmbeddingModel.ADA_002` or `EmbeddingModel.T3_LARGE`
- **WHEN** the enum is evaluated
- **THEN** the values SHALL still resolve (backward compatibility) but MUST be annotated as deprecated
