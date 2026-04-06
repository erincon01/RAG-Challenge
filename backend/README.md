# RAG Challenge Backend

FastAPI backend service for RAG Challenge - UEFA Euro match analysis with embeddings.

## Architecture

This backend follows a **layered architecture** pattern:

```
app/
├── api/            # HTTP routes, request/response models
│   └── v1/         # API version 1
│       └── health.py
├── services/       # Business logic and use cases
├── repositories/   # Data access layer (per database engine)
├── domain/         # Domain entities and rules
├── adapters/       # External integrations (OpenAI, etc)
├── core/           # Core utilities (config, logging, exceptions)
└── main.py         # Application entry point
```

### Layer Responsibilities

- **API Layer** (`api/`): HTTP endpoints, request/response DTOs, validation
- **Service Layer** (`services/`): Business logic, use cases, orchestration
- **Repository Layer** (`repositories/`): Database queries, SQL builders per engine
- **Domain Layer** (`domain/`): Entities, value objects, domain rules
- **Adapters Layer** (`adapters/`): External service integrations
- **Core** (`core/`): Cross-cutting concerns (config, logging, middleware)

## Requirements

- Python 3.10+
- PostgreSQL 17 with pgvector extension (for local development)
- SQL Server 2025 Express (for local development)

## Setup

### 1. Install Dependencies

```bash
cd backend
pip install -r requirements.txt
```

### 2. Configure Environment

Create a `.env` file in the project root (one level up from backend/):

```bash
# Copy from example
cp ../.env.example ../.env

# Edit with your values
nano ../.env
```

Required variables:
- `ENVIRONMENT=local`
- Database connection strings (PostgreSQL and SQL Server)
- OpenAI API credentials

### 3. Run the Server

#### Development Mode (with auto-reload)

```bash
# From backend/ directory
python -m app.main

# Or using uvicorn directly
uvicorn app.main:app --reload --host 0.0.0.0 --port 8000
```

#### Production Mode

```bash
uvicorn app.main:app --host 0.0.0.0 --port 8000 --workers 4
```

## API Documentation

Once running, visit:

- **Interactive API docs (Swagger UI)**: http://localhost:8000/docs
- **Alternative docs (ReDoc)**: http://localhost:8000/redoc
- **OpenAPI JSON**: http://localhost:8000/openapi.json

## Endpoints

### Health Checks

- `GET /` - Root endpoint with API information
- `GET /api/v1/health` - Detailed health check with environment info
- `GET /api/v1/health/ready` - Readiness probe (checks dependencies)
- `GET /api/v1/health/live` - Liveness probe (minimal check)

### Data Retrieval

- `GET /api/v1/competitions` - List competitions
- `GET /api/v1/matches` - List matches
- `GET /api/v1/matches/{match_id}` - Get match detail
- `GET /api/v1/events` - Query match events by match
- `GET /api/v1/events/{event_id}` - Get event detail

### StatsBomb & Operations

- `GET /api/v1/statsbomb/competitions` - Browse StatsBomb competitions
- `GET /api/v1/statsbomb/matches` - Browse StatsBomb matches by competition/season
- `POST /api/v1/ingestion/download` - Download StatsBomb data
- `POST /api/v1/ingestion/load` - Load data into a selected database
- `POST /api/v1/ingestion/aggregate` - Create aggregate tables
- `GET /api/v1/ingestion/jobs` - List jobs
- `GET /api/v1/ingestion/jobs/{job_id}` - Get job detail
- `POST /api/v1/ingestion/jobs/{job_id}/cancel` - Cancel a running job
- `DELETE /api/v1/ingestion/jobs` - Clear completed jobs

### Search & Embeddings

- `GET /api/v1/capabilities` - Capability matrix by source
- `GET /api/v1/sources/status` - Connectivity status by source
- `GET /api/v1/explorer/teams` - Team explorer data
- `GET /api/v1/explorer/players` - Player explorer data
- `GET /api/v1/explorer/tables` - Database table metadata
- `GET /api/v1/embeddings/status` - Embedding coverage by match
- `POST /api/v1/embeddings/rebuild` - Rebuild embeddings for selected matches
- `POST /api/v1/chat/search` - Semantic search with RAG-generated answer

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/api/test_health.py

# Run with verbose output
pytest -v
```

Local validation on 2026-04-02: `259 passed` on Python 3.12.

## Development

### Adding a New Endpoint

1. **Create domain entities** in `domain/` (if needed)
2. **Create repository methods** in `repositories/` for data access
3. **Create service methods** in `services/` for business logic
4. **Create DTOs** (Pydantic models) for request/response
5. **Create router** in `api/v1/` and register in `main.py`
6. **Write tests** in `tests/`

### Code Style

- Follow PEP 8
- Use type hints for all functions
- Document functions with docstrings
- Keep functions small and focused (< 40 lines)
- Use dependency injection for testability

### Adding Dependencies

1. Add to `requirements.txt`
2. Update Docker images if needed
3. Document in this README if it's a major dependency

## Configuration

Configuration is managed through the centralized `config` module in the project root.

See `../config/README.md` for details on:
- Environment variables
- Settings structure
- Environment-specific configuration

## Docker

### Build Image

```bash
docker build -t rag-challenge-backend:latest .
```

### Run Container

```bash
docker run -p 8000:8000 \
  --env-file ../.env \
  rag-challenge-backend:latest
```

## Troubleshooting

### Import Errors

Make sure the project root is in PYTHONPATH:

```bash
export PYTHONPATH="${PYTHONPATH}:$(pwd)/.."
```

### Database Connection Errors

Check that:
1. Databases are running (PostgreSQL and SQL Server)
2. Connection strings in `.env` are correct
3. Database users have necessary permissions

### Port Already in Use

Change the port in the run command:

```bash
uvicorn app.main:app --port 8001
```

## Project Status

Current implementation status:

- [x] Layered architecture structure
- [x] FastAPI application setup
- [x] Health check endpoints
- [x] Configuration integration
- [x] Repository layer (PostgreSQL)
- [x] Repository layer (SQL Server)
- [x] Service layer (ingestion, explorer, embeddings, search)
- [x] OpenAI adapter
- [x] Competition endpoints
- [x] Match endpoints
- [x] Event endpoints
- [x] Chat/search endpoint
- [x] Backend pytest suite (local branch state)
- [ ] Authentication
- [ ] Rate limiting
- [ ] CI-backed coverage enforcement

## License

MIT
