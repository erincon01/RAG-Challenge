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

### Coming Soon

- `GET /api/v1/competitions` - List competitions
- `GET /api/v1/matches` - List matches
- `GET /api/v1/events` - Query match events
- `POST /api/v1/chat/search` - Semantic search with LLM

## Testing

```bash
# Run all tests
pytest

# Run with coverage
pytest --cov=app --cov-report=html

# Run specific test file
pytest tests/test_health.py

# Run with verbose output
pytest -v
```

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
- [ ] Repository layer (PostgreSQL)
- [ ] Repository layer (SQL Server)
- [ ] Service layer (embeddings, search)
- [ ] OpenAI adapter
- [ ] Competition endpoints
- [ ] Match endpoints
- [ ] Event endpoints
- [ ] Chat/search endpoint
- [ ] Authentication
- [ ] Rate limiting
- [ ] Comprehensive tests

## License

MIT
