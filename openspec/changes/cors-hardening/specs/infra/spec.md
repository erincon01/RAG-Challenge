## MODIFIED Requirements

### Requirement: CORS configuration

The system SHALL read allowed CORS origins from the `CORS_ORIGINS` environment variable.
The value MUST be a comma-separated list of origin URLs (e.g., `http://localhost:5173,http://localhost:8000`).
When `CORS_ORIGINS` is not set, the system SHALL default to `http://localhost:5173,http://localhost:8000`.
The system MUST NOT use `allow_origins=["*"]` in any environment.

#### Scenario: CORS origins loaded from environment variable
- **WHEN** `CORS_ORIGINS` is set to `https://app.example.com,https://admin.example.com`
- **THEN** the CORS middleware SHALL accept requests from `https://app.example.com` and `https://admin.example.com`
- **AND** reject requests from any other origin

#### Scenario: CORS origins default when env var is absent
- **WHEN** `CORS_ORIGINS` is not set in the environment
- **THEN** the CORS middleware SHALL accept requests from `http://localhost:5173` and `http://localhost:8000`
- **AND** reject requests from any other origin

#### Scenario: CORS origins parsing handles whitespace
- **WHEN** `CORS_ORIGINS` is set to `http://localhost:5173 , http://localhost:8000`
- **THEN** the system SHALL trim whitespace and accept both origins

#### Scenario: CORS rejects wildcard origin
- **WHEN** a request arrives from an origin not in the configured list
- **THEN** the response SHALL NOT include the `Access-Control-Allow-Origin` header
