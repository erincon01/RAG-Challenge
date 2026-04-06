# ADR-004: Local Docker Infrastructure with SQL Server 2025 Express and PostgreSQL

## Status

**Accepted** - 2026-02-08

## Context

The current development workflow has significant friction:

### Current State

- **Azure PaaS Dependency**: All development requires connection to Azure PostgreSQL and Azure SQL
- **No Local Development**: Developers cannot work offline or without Azure credentials
- **Manual Setup**: Each developer must manually provision Azure resources
- **Cost**: Every development query incurs Azure charges
- **Slow Feedback Loop**: Network latency to Azure on every database operation
- **No Reproducibility**: Different developers may have different Azure configurations
- **Testing Challenges**: Integration tests require Azure infrastructure
- **No Devcontainer**: Current devcontainer setup is incomplete and doesn't work

### Problems

1. **Onboarding**: New developers need Azure subscription, credentials, and manual setup
2. **Development Cost**: Continuous Azure usage costs even during local development
3. **Offline Work**: Cannot work without internet connection to Azure
4. **CI/CD**: GitHub Actions require Azure credentials for integration tests
5. **Consistency**: No guarantee all developers have identical database schemas
6. **Iteration Speed**: Slow feedback loop for database changes

## Decision

Implement **local Docker-based infrastructure** with:

### Core Components

1. **PostgreSQL 17 with pgvector**
   - Image: `pgvector/pgvector:pg17` (or latest stable)
   - Extension: `vector` for similarity search
   - Port: `5432`
   - Volume: Persistent storage for development data

2. **SQL Server 2025 Express (Linux)**
   - Image: `mcr.microsoft.com/mssql/server:2025-latest`
   - Edition: Express (`MSSQL_PID=Express`)
   - Port: `1433`
   - Volume: Persistent storage for development data

3. **Backend (FastAPI)**
   - Custom Dockerfile
   - Port: `8000`
   - Depends on: PostgreSQL, SQL Server

4. **Frontend (Streamlit)**
   - Custom Dockerfile
   - Port: `8501`
   - Depends on: Backend

### Docker Compose Structure

```yaml
services:
  postgres:
    image: pgvector/pgvector:pg17
    environment:
      POSTGRES_DB: rag_challenge
      POSTGRES_USER: postgres
      POSTGRES_PASSWORD: postgres_local_password
    ports:
      - "5432:5432"
    volumes:
      - postgres_data:/var/lib/postgresql/data
      - ./infra/docker/postgres/initdb:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "pg_isready -U postgres"]
      interval: 10s
      timeout: 5s
      retries: 5

  sqlserver:
    image: mcr.microsoft.com/mssql/server:2025-latest
    environment:
      ACCEPT_EULA: "Y"
      MSSQL_SA_PASSWORD: "SqlServer_Local_Password123!"
      MSSQL_PID: "Express"
    ports:
      - "1433:1433"
    volumes:
      - sqlserver_data:/var/opt/mssql
      - ./infra/docker/sqlserver/initdb:/docker-entrypoint-initdb.d
    healthcheck:
      test: ["CMD-SHELL", "/opt/mssql-tools/bin/sqlcmd -S localhost -U sa -P SqlServer_Local_Password123! -Q 'SELECT 1'"]
      interval: 10s
      timeout: 5s
      retries: 5

  backend:
    build:
      context: ./backend
      dockerfile: Dockerfile
    ports:
      - "8000:8000"
    environment:
      ENVIRONMENT: local
      POSTGRES_HOST: postgres
      SQLSERVER_HOST: sqlserver
    depends_on:
      postgres:
        condition: service_healthy
      sqlserver:
        condition: service_healthy
    volumes:
      - ./backend:/app

  frontend:
    build:
      context: ./frontend
      dockerfile: Dockerfile
    ports:
      - "8501:8501"
    environment:
      BACKEND_URL: http://backend:8000
    depends_on:
      - backend
    volumes:
      - ./frontend:/app

volumes:
  postgres_data:
  sqlserver_data:
```

### Profiles for Different Scenarios

```yaml
# Local development (default)
docker compose up

# Local with Azure databases (for testing Azure integration)
docker compose --profile azure up

# CI/CD (GitHub Actions)
docker compose --profile ci up
```

### Database Initialization

**PostgreSQL Init Script** (`infra/docker/postgres/initdb/01-init.sql`):
```sql
-- Create vector extension
CREATE EXTENSION IF NOT EXISTS vector;

-- Create database schema
CREATE SCHEMA IF NOT EXISTS rag_challenge;

-- Run migrations
\i /migrations/postgres/V001__initial_schema.sql
```

**SQL Server Init Script** (`infra/docker/sqlserver/initdb/01-init.sql`):
```sql
-- Create database
IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'rag_challenge')
BEGIN
    CREATE DATABASE rag_challenge;
END;
GO

USE rag_challenge;
GO

-- Run migrations
-- ...
```

### Devcontainer 2.0

**Updated `.devcontainer/devcontainer.json`:**
```json
{
  "name": "RAG Challenge Dev",
  "dockerComposeFile": ["../infra/docker-compose.yml", "docker-compose.devcontainer.yml"],
  "service": "backend",
  "workspaceFolder": "/workspace",
  "forwardPorts": [8000, 8501, 5432, 1433],
  "postCreateCommand": "pip install -r requirements.txt && python -m pytest",
  "postStartCommand": "uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload",
  "customizations": {
    "vscode": {
      "extensions": [
        "ms-python.python",
        "ms-python.vscode-pylance",
        "ms-azuretools.vscode-docker",
        "ms-mssql.mssql",
        "ms-ossdata.vscode-postgresql"
      ]
    }
  }
}
```

## Consequences

### Positive

✅ **Full Local Development**: Everything runs locally, no Azure required
✅ **Offline Work**: Can develop without internet connection
✅ **Fast Feedback**: Instant database operations, no network latency
✅ **Zero Cloud Cost**: No Azure charges for local development
✅ **Reproducibility**: Exact same environment for all developers
✅ **Easy Onboarding**: `docker compose up` is the only command needed
✅ **CI/CD Integration**: GitHub Actions can spin up services easily
✅ **Isolated Testing**: Each developer has isolated database
✅ **Version Control**: Infrastructure as code in repository
✅ **Devcontainer Support**: Full VS Code devcontainer integration

### Negative

⚠️ **Initial Setup Time**: Docker images need to be pulled first time
⚠️ **Disk Space**: Docker images and volumes consume disk space (~5GB)
⚠️ **Resource Usage**: Multiple containers require more RAM (~4GB)
⚠️ **Learning Curve**: Developers need Docker/docker-compose knowledge
⚠️ **Windows Challenges**: SQL Server container better on Linux/WSL2
⚠️ **Parity Risk**: Local Docker may differ from Azure PaaS in some features

### Trade-offs

- **Azure Features vs Local Speed**: Lose some Azure-specific features, gain development speed
- **Resources vs Convenience**: Use more local resources, but easier development
- **Setup Time vs Runtime**: More upfront setup, faster everyday development

## Implementation Plan

### Phase 1: Docker Images (Week 3-4)

1. Create `infra/docker/postgres/Dockerfile` extending pgvector image
2. Create `infra/docker/sqlserver/Dockerfile` (or use base image directly)
3. Add init scripts for both databases
4. Test healthchecks

### Phase 2: Application Dockerfiles (Week 4)

1. Create `backend/Dockerfile` for FastAPI
2. Create `frontend/Dockerfile` for Streamlit
3. Optimize for development (hot reload, volume mounts)

### Phase 3: Docker Compose (Week 4)

1. Create main `infra/docker-compose.yml`
2. Add service dependencies and healthchecks
3. Configure networks and volumes
4. Test full stack locally

### Phase 4: Devcontainer (Week 6)

1. Update `.devcontainer/devcontainer.json`
2. Create `docker-compose.devcontainer.yml` override
3. Test "Reopen in Container" workflow
4. Document devcontainer setup

### Phase 5: CI/CD Integration (Week 7-8)

1. Add GitHub Actions workflow using docker compose
2. Run tests against local containers
3. Build and push images to GHCR

## Validation Criteria

### Must Have

- ✅ `docker compose up` starts all services successfully
- ✅ All healthchecks pass
- ✅ Backend can connect to both databases
- ✅ Frontend can communicate with backend
- ✅ Devcontainer opens successfully in VS Code
- ✅ Integration tests pass using local containers

### Performance Targets

- Startup time: < 2 minutes (first time), < 30 seconds (subsequent)
- Database query latency: < 10ms (vs ~50-100ms to Azure)
- Memory usage: < 4GB total
- Disk usage: < 5GB total

## Alternatives Considered

### Alternative 1: Keep Azure PaaS, Add VPN/Proxy
**Rejected** - Doesn't solve cost, offline, or reproducibility issues

### Alternative 2: Use Docker but PostgreSQL without pgvector
**Rejected** - Need pgvector for local embedding search

### Alternative 3: Use SQLite instead of SQL Server
**Rejected** - Want production parity, SQLite has different features/behavior

### Alternative 4: Kubernetes (k3d/minikube) instead of Docker Compose
**Rejected** - Too complex for local development, docker-compose is sufficient

## Docker Image Validation

### PostgreSQL with pgvector

Verify extension and functionality:
```sql
-- Check version
SELECT version();

-- Check pgvector extension
SELECT * FROM pg_available_extensions WHERE name = 'vector';

-- Test vector operations
CREATE TABLE test_vectors (id serial, vec vector(3));
INSERT INTO test_vectors (vec) VALUES ('[1,2,3]'), ('[4,5,6]');
SELECT vec <-> '[3,3,3]' AS distance FROM test_vectors;
```

### SQL Server 2025 Express

Verify edition and features:
```sql
-- Check version and edition
SELECT @@VERSION, SERVERPROPERTY('Edition');

-- Verify Express limitations are acceptable
SELECT SERVERPROPERTY('EngineEdition');  -- Should be 4 for Express
```

## References

- [SQL Server on Linux Docker Quickstart](https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker)
- [SQL Server Environment Variables](https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-configure-environment-variables)
- [pgvector Docker Image](https://github.com/pgvector/pgvector#docker)
- [Docker Compose Healthchecks](https://docs.docker.com/compose/compose-file/05-services/#healthcheck)
- [VS Code Devcontainers](https://code.visualstudio.com/docs/devcontainers/containers)

## Related ADRs

- [ADR-001: Adoption of Layered Architecture](ADR-001-layered-architecture.md) - Docker enables separate services
- [ADR-002: Centralized Configuration](ADR-002-centralized-configuration.md) - Settings support local environment
- [ADR-003: Migration to pgvector](ADR-003-pgvector-migration.md) - pgvector runs in local PostgreSQL
