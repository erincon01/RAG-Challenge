# Tech Stack

## Backend

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | Python | 3.11+ | Type hints required on all public functions |
| Web framework | FastAPI | ≥ 0.109.0 | Async-capable, OpenAPI docs at `/docs` |
| ASGI server | Uvicorn | ≥ 0.27.0 | `[standard]` extras for WebSockets/performance |
| Data validation | Pydantic v2 | ≥ 2.0.0 | Request/response schemas in `api/v1/models.py` |
| Config management | pydantic-settings | ≥ 2.0.0 | `config/settings.py` → `get_settings()` via `Depends()` |
| PostgreSQL driver | psycopg2-binary | ≥ 2.9.9 | Used by `PostgresMatchRepository` |
| SQL Server driver | pyodbc | ≥ 5.0.1 | Used by `SQLServerMatchRepository` |
| ORM / query builder | SQLAlchemy | ≥ 2.0.25 | Optional; raw SQL preferred for vector queries |
| OpenAI client | openai | ≥ 1.10.0 | Supports both Azure OpenAI and direct OpenAI |
| HTTP client | requests | ≥ 2.31.0 | Used by `StatsbombService` for open-data fetching |
| Data frames | pandas | ≥ 2.0.0 | Ingestion pipeline only — not in service layer |
| Env file loading | python-dotenv | ≥ 1.0.0 | Dev convenience (Pydantic Settings reads `.env` directly) |

## Frontend

| Component | Technology | Version | Notes |
|-----------|-----------|---------|-------|
| Language | TypeScript | ~5.9 | Strict mode |
| UI framework | React | ^19.2 | Functional components + hooks only |
| Build tool | Vite | ^7.2 | `npm run dev` for hot module reload |
| Styling | Tailwind CSS | ^3.4 | Utility-first, no custom CSS files |
| Routing | React Router DOM | ^7.13 | SPA routing |
| Server state | TanStack Query (React Query) | ^5.90 | All API calls go through Query/Mutation |
| Form handling | React Hook Form + Zod | ^7.71 / ^4.3 | Schema-validated forms |

## Databases

| Database | Technology | Version | Vector extension | Vector search syntax |
|----------|-----------|---------|-----------------|---------------------|
| PostgreSQL | pgvector | pg16 + pgvector latest | `vector(1536)` type | `<=>` cosine, `<#>` inner product, `<->` L2 |
| Azure SQL Server | VECTOR type (native) | SQL Server 2022 / Azure SQL | `VECTOR(1536)` type | `VECTOR_DISTANCE('cosine', col, @vec)` |

### Embedding columns per table

| Model | Column | Dimensions |
|-------|--------|-----------|
| `text-embedding-ada-002` | `summary_embedding_ada_002` | 1536 |
| `text-embedding-3-small` | `summary_embedding_t3_small` | 1536 |
| `text-embedding-3-large` | `summary_embedding_t3_large` | 3072 |

Default model for new features: **`text-embedding-3-small`** (best cost/quality ratio).

## AI Services

| Service | Provider | Usage |
|---------|---------|-------|
| Chat completions | Azure OpenAI (GPT-4o / GPT-4) | RAG answer generation |
| Embeddings | Azure OpenAI | Generate vectors for event summaries and queries |
| Provider | Configurable via `OPENAI_PROVIDER` | `"azure"` (default) or `"openai"` (direct) |
| API version | `2024-06-01` | Azure OpenAI REST API version |

## Development Tooling

| Tool | Version | Purpose |
|------|---------|---------|
| ruff | ≥ 0.4.0 | Linter + formatter (replaces flake8, isort, black) |
| mypy | ≥ 1.8.0 | Static type checking (`strict = false`, tighten progressively) |
| pytest | ≥ 7.4.3 | Test runner |
| pytest-asyncio | ≥ 0.21.1 | Async test support (`asyncio_mode = auto`) |
| pytest-cov | ≥ 4.1.0 | Coverage reporting (`--cov=app --cov-fail-under=80`) |
| httpx | ≥ 0.26.0 | FastAPI `TestClient` transport |
| pre-commit | ≥ 3.7.0 | Git hooks (ruff, mypy, hygiene, no-commit-to-main/develop) |

## Infrastructure

| Component | Technology | Notes |
|-----------|-----------|-------|
| Container runtime | Docker + Docker Compose | `docker compose up --build` starts all services |
| Dev containers | VS Code devcontainer | `.devcontainer/` — post-create installs all deps |
| CI | GitHub Actions (`ci.yml`) | lint → typecheck → unit+api tests (coverage ≥ 80%) |
| CD | GitHub Actions (`cd.yml`) | push to `develop` → staging; push to `main` → production |
| Cloud | Azure | Azure App Service (backend), Azure Static Web App (frontend) |

## Environment Variables

All secrets and config come from `.env` (local) or Azure App Settings (cloud).
See `.env.example` for required variables.

| Variable | Description | Used by |
|----------|-------------|---------|
| `POSTGRES_HOST` | PostgreSQL host | `DatabaseConfig` |
| `POSTGRES_DB` | PostgreSQL database name | `DatabaseConfig` |
| `POSTGRES_USER` | PostgreSQL user | `DatabaseConfig` |
| `POSTGRES_PASSWORD` | PostgreSQL password | `DatabaseConfig` |
| `SQLSERVER_HOST` | SQL Server host | `DatabaseConfig` |
| `SQLSERVER_DB` | SQL Server database name | `DatabaseConfig` |
| `SQLSERVER_USER` | SQL Server user | `DatabaseConfig` |
| `SQLSERVER_PASSWORD` | SQL Server password | `DatabaseConfig` |
| `OPENAI_PROVIDER` | `"azure"` or `"openai"` | `OpenAIConfig` |
| `OPENAI_ENDPOINT` | Azure OpenAI endpoint URL | `OpenAIConfig` |
| `OPENAI_KEY` | Azure OpenAI API key | `OpenAIConfig` |
| `OPENAI_MODEL` | Chat model deployment name | `OpenAIConfig` |
| `OPENAI_MODEL2` | Secondary chat model | `OpenAIConfig` |
| `REPO_OWNER` | Statsbomb GitHub org (`statsbomb`) | `RepositoryConfig` |
| `REPO_NAME` | Statsbomb repo (`open-data`) | `RepositoryConfig` |
| `LOCAL_FOLDER` | Local data download path | `RepositoryConfig` |
| `ENVIRONMENT` | `local` \| `azure` \| `test` | `Settings` |
