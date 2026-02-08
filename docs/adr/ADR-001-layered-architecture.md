# ADR-001: Adoption of Layered Architecture

## Status

**Accepted** - 2026-02-08

## Context

The RAG Challenge application was initially built as a monolithic Streamlit application where:

- UI, business logic, and data access code are tightly coupled in the same modules
- Streamlit pages directly access the database (both PostgreSQL and SQL Server)
- No clear separation of concerns between layers
- Difficult to test individual components in isolation
- High coupling between modules leads to code duplication
- Database connection logic is repeated across multiple modules
- Makes it challenging to evolve the application or add new features
- Prevents horizontal scaling or independent deployment of components

**Key Problems Identified:**
- `app.py` contains UI, orchestration, and implicit data access
- `python_modules/` have mixed responsibilities (data access, LLM calls, business logic)
- No HTTP API layer - everything runs in a single process
- Cannot easily replace frontend or add multiple clients
- Testing requires running the entire Streamlit application

## Decision

We will refactor the application into a **layered architecture** with clear separation between:

### 1. Frontend Layer
- Keep Streamlit as the initial UI (minimize migration cost)
- Transform it into a **thin client** that only handles presentation and user interaction
- Communicate with backend exclusively via HTTP REST API
- No direct database access from frontend
- Located in `frontend/` directory

### 2. Backend Layer (FastAPI)
- New FastAPI application with clear internal layers:
  - **API layer** (`api/`): HTTP routers, request/response DTOs, validation
  - **Service layer** (`services/`): Business logic, use cases, LLM orchestration
  - **Repository layer** (`repositories/`): Database queries, query builders per engine
  - **Domain layer** (`domain/`): Entities, value objects, domain rules
  - **Adapters layer** (`adapters/`): External integrations (OpenAI, Azure OpenAI)
- Located in `backend/` directory
- Provides versioned REST API (starting with `/api/v1/`)
- Handles all business logic and data access

### 3. Data Layer
- PostgreSQL with pgvector for embeddings
- SQL Server 2025 Express for relational data
- Accessed only through repository layer
- Migrations managed per database engine

**Target Structure:**
```
/
  backend/
    app/
      api/         # HTTP routes and DTOs
      services/    # Business logic
      repositories/ # Data access per DB engine
      domain/      # Entities and rules
      adapters/    # External integrations
      config/      # Backend-specific config
    tests/
    main.py
  frontend/
    streamlit_app/
      app.py
      pages/
      services/    # HTTP client to backend
      components/
  config/          # Shared configuration
```

## Consequences

### Positive

✅ **Separation of Concerns**: Each layer has a single, well-defined responsibility
✅ **Testability**: Can test each layer independently with mocks
✅ **Flexibility**: Can replace frontend (e.g., React, Vue) without touching backend
✅ **Scalability**: Backend and frontend can be scaled independently
✅ **Multiple Clients**: Can add mobile app, CLI, or other clients using same API
✅ **Team Collaboration**: Different teams can work on different layers with clear contracts
✅ **Code Reuse**: Business logic in services can be reused across different APIs
✅ **Security**: Backend can implement proper authentication, authorization, and rate limiting
✅ **Monitoring**: Easier to add logging, metrics, and tracing per layer
✅ **Documentation**: OpenAPI/Swagger auto-generated from FastAPI

### Negative

⚠️ **Migration Effort**: Significant upfront work to refactor existing code
⚠️ **Added Complexity**: More moving parts (HTTP calls, serialization, error handling)
⚠️ **Performance Overhead**: Network calls between frontend and backend (mitigated by local deployment)
⚠️ **Learning Curve**: Team needs to understand layered architecture principles
⚠️ **Operational Overhead**: Two applications to deploy and monitor instead of one

### Trade-offs

- **Short-term**: More initial development time
- **Long-term**: Much faster feature development and maintenance
- **Deployment**: More complex initially, but enables better scaling later

## Implementation Plan

1. **Phase 0**: Stabilization (fix bugs, centralize config)
2. **Phase 1**: Create backend with minimal endpoints, migrate logic from modules
3. **Phase 2**: Dockerize both backend and frontend
4. **Phase 3**: Complete feature parity with current monolith
5. **Phase 4**: Deprecate direct database access from frontend

## Alternatives Considered

### Alternative 1: Keep Monolithic Streamlit
**Rejected** - While simpler short-term, this doesn't address fundamental scalability and maintainability issues.

### Alternative 2: Microservices Architecture
**Rejected** - Too complex for current team size and requirements. Layered architecture provides enough separation without microservices overhead.

### Alternative 3: Gradual Refactoring with Adapters
**Rejected** - Attempting to gradually refactor without a clean break leads to hybrid code that's difficult to maintain.

## References

- Clean Architecture by Robert C. Martin
- [FastAPI Best Practices](https://github.com/zhanymkanov/fastapi-best-practices)
- [Layered Architecture Pattern](https://www.oreilly.com/library/view/software-architecture-patterns/9781491971437/ch01.html)

## Related ADRs

- [ADR-002: Centralized Configuration with Pydantic Settings](ADR-002-centralized-configuration.md)
- [ADR-003: Migration from Azure AI Extensions to pgvector](ADR-003-pgvector-migration.md)
- [ADR-004: Local Docker Infrastructure](ADR-004-local-docker-infrastructure.md)
