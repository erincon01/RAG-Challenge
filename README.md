# Football Analytics Copilot — RAG Challenge

AI-powered football match analysis using Retrieval-Augmented Generation (RAG) with OpenAI and vector embeddings over [StatsBomb open data](https://github.com/statsbomb/open-data).

## What it does

Ask natural-language questions about a football match. The system retrieves the most relevant events via vector similarity search, builds a token-budgeted context, and sends it to an LLM for a grounded answer.

**Example:** "Who scored the winning goal in the Euro 2024 final?" — the system finds the relevant events from the match, assembles context, and generates a detailed answer with sources.

## Quick start

### Option A: Docker (recommended)

```bash
git clone https://github.com/erincon01/RAG-Challenge.git
cd RAG-Challenge
git checkout develop
cp .env.docker.example .env.docker
# Edit .env.docker — set OPENAI_KEY and OPENAI_ENDPOINT
docker compose up --build
```

- Frontend: http://localhost:5173
- Backend API: http://localhost:8000
- API Docs: http://localhost:8000/docs
- PostgreSQL: `localhost:5432`
- SQL Server: `localhost:1433`

### Option B: DevContainer (VS Code)

Open the repo in VS Code — it will offer to reopen in the DevContainer. All services start automatically.

### Option C: Manual

```bash
# Backend
cd backend
pip install -r requirements.txt
cp ../.env.example ../.env  # edit with your credentials
python -m app.main
# http://localhost:8000/docs

# Frontend
cd frontend/webapp
npm install
cp .env.example .env
npm run dev
# http://localhost:5173
```

## Architecture

```
Frontend (React + TypeScript)          Backend (FastAPI)
┌────────────────────────┐     REST   ┌─────────────────────────────┐
│ Vite + Tailwind        │◄──────────►│ API Layer (v1)              │
│ TanStack Query         │            │   ↓                        │
│ 7 pages                │            │ Services Layer              │
└────────────────────────┘            │   ↓                        │
                                      │ Repositories (dual-repo)   │
                                      │   ↓              ↓         │
                                      │ PostgreSQL    SQL Server    │
                                      │ (pgvector)    (VECTOR)      │
                                      │   ↓                        │
                                      │ OpenAI Adapter             │
                                      └─────────────────────────────┘
```

**Layers:** API → Services → Repositories → Domain → Adapters. One-way dependency rule — no layer imports from above. All external dependencies injected via FastAPI `Depends()`.

See [docs/architecture.md](docs/architecture.md) for the full system design.

## Tech stack

| Layer | Technology |
|-------|-----------|
| Backend | Python 3.11+, FastAPI, Pydantic v2, Uvicorn |
| Frontend | React 18, TypeScript, Vite, Tailwind, TanStack Query |
| Databases | PostgreSQL 17 + pgvector, SQL Server 2025 |
| AI | OpenAI / Azure OpenAI (embeddings + chat completions) |
| Infrastructure | Docker Compose, DevContainers, GitHub Actions CI |
| Governance | [OpenSpec](https://github.com/Fission-AI/OpenSpec) spec-driven development |
| Testing | pytest (470+ tests, 82% coverage), ruff, mypy |

See [docs/tech-stack.md](docs/tech-stack.md) for detailed versions and configuration.

## Key features

- **Semantic search** with multiple embedding models (ada-002, text-embedding-3-small/large)
- **Multiple search algorithms** (cosine, inner product, L2)
- **Token budget guard** — counts tokens before LLM call, truncates context if needed
- **Multi-language** — auto-translates queries to English
- **Dual database** — PostgreSQL and SQL Server, switchable at query time
- **StatsBomb integration** — browse and import competitions/matches from open data
- **Job management** — track downloads, imports, embeddings with real-time status
- **7-page web UI** — Dashboard, Catalog, Operations, Explorer, Embeddings, Chat, Data Sources

## Application pages

1. **Dashboard** — System health, database status, recent jobs
2. **Data Sources** — Database connectivity and capability matrix
3. **StatsBomb Catalog** — Browse and select competitions/matches
4. **Operations** — Download, load, and process data with job tracking
5. **Data Explorer** — Browse competitions, matches, teams, players, events
6. **Embeddings** — Coverage status, rebuild embeddings per match/model
7. **Chat** — AI-powered semantic search with natural language

## API endpoints

Full interactive documentation at http://localhost:8000/docs (Swagger) and http://localhost:8000/redoc.

| Group | Endpoints |
|-------|-----------|
| Health | `GET /health`, `/health/ready`, `/health/live` |
| Capabilities | `GET /capabilities`, `/sources/status` |
| StatsBomb | `GET /statsbomb/competitions`, `/statsbomb/matches` |
| Data | `GET /competitions`, `/matches`, `/matches/{id}`, `/events`, `/events/{id}` |
| Explorer | `GET /explorer/teams`, `/explorer/players`, `/explorer/tables` |
| Ingestion | `POST /ingestion/download`, `/load`, `/aggregate` + job management |
| Embeddings | `GET /embeddings/status`, `POST /embeddings/rebuild` |
| Chat | `POST /chat/search` |

All endpoints prefixed with `/api/v1`.

## Testing

```bash
cd backend
pytest tests/ -v                                              # run all tests
pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80  # with coverage
ruff check app/                                                # lint
ruff format --check app/                                       # format check
mypy app/                                                      # type check
```

CI runs all checks on every PR (GitHub Actions).

## Project structure

```
RAG-Challenge/
├── backend/                    # FastAPI backend
│   ├── app/
│   │   ├── api/v1/            # HTTP endpoints
│   │   ├── services/          # Business logic (SearchService, IngestionService, ...)
│   │   ├── repositories/      # Data access (PostgreSQL, SQL Server)
│   │   ├── domain/            # Entities, exceptions
│   │   ├── adapters/          # External integrations (OpenAI)
│   │   └── core/              # Config, DI providers
│   ├── tests/                 # 470+ tests (unit + API)
│   └── requirements.txt
├── frontend/webapp/           # React + TypeScript frontend
│   ├── src/pages/             # 7 application pages
│   ├── src/lib/api/           # Type-safe API client
│   └── package.json
├── config/                    # Centralized Pydantic settings
├── infra/docker/              # Docker init scripts (postgres, sqlserver)
├── openspec/                  # Spec-driven governance
│   ├── specs/                 # System specs (api, rag, data, infra)
│   └── changes/archive/       # Completed change artifacts
├── docs/                      # Documentation
│   ├── architecture.md        # System architecture
│   ├── tech-stack.md          # Technology details
│   ├── semantic-search.md     # Vector search explained
│   ├── data-model.md          # Database schema
│   ├── app-use-case.md        # Use cases and demo questions
│   ├── statsbomb-intro.md     # StatsBomb data explained
│   ├── conversation_log.md    # AI session audit trail
│   ├── PLAN_OPENSPEC_ADOPTION.md  # Governance roadmap
│   └── adr/                   # Architecture Decision Records
├── .devcontainer/             # VS Code DevContainer
├── .github/workflows/ci.yml  # CI pipeline
├── docker-compose.yml         # Full stack orchestration
├── .env.example               # Environment template
├── .env.docker.example        # Docker environment template
├── .pre-commit-config.yaml    # Ruff lint + format hooks
├── CLAUDE.md                  # AI assistant entry point
├── AGENTS.md                  # Project rules and conventions
├── CHANGELOG.md               # Version history
└── README.md
```

## Documentation

| Document | Purpose |
|----------|---------|
| [docs/getting-started.md](docs/getting-started.md) | New contributor guide — setup, OpenSpec workflow, where to find things |
| [AGENTS.md](AGENTS.md) | All project rules (architecture, DI, testing, git, security) |
| [CLAUDE.md](CLAUDE.md) | AI assistant entry point — references all key files |
| [CHANGELOG.md](CHANGELOG.md) | Version history |
| [docs/architecture.md](docs/architecture.md) | System design and layer diagram |
| [docs/tech-stack.md](docs/tech-stack.md) | Technology versions and configuration |
| [docs/semantic-search.md](docs/semantic-search.md) | Vector search algorithms and models |
| [docs/data-model.md](docs/data-model.md) | Database schema and entity model |
| [docs/app-use-case.md](docs/app-use-case.md) | Use cases and demo questions |
| [docs/statsbomb-intro.md](docs/statsbomb-intro.md) | StatsBomb data structure |
| [docs/PLAN_OPENSPEC_ADOPTION.md](docs/PLAN_OPENSPEC_ADOPTION.md) | Governance roadmap with sources |
| [docs/conversation_log.md](docs/conversation_log.md) | AI session audit trail |
| [docs/adr/](docs/adr/) | Architecture Decision Records (4 ADRs) |
| [openspec/specs/](openspec/specs/) | System specs (api, rag, data, infra) |

## For AI assistants

Start with [CLAUDE.md](CLAUDE.md). It points to [AGENTS.md](AGENTS.md) which has all project rules. Key commands, architecture constraints, testing requirements, and the OpenSpec governance workflow are all documented there.

## Troubleshooting

**Frontend not loading?** Check `docker compose ps` — all services should be `healthy`. If SQL Server shows `starting`, wait 30-60 seconds.

**Database connection refused?** Inside the DevContainer, use service names (`postgres`, `sqlserver`) instead of `localhost`.

**Tests failing?** Unit/API tests don't need a running database — they mock all external calls. Run `cd backend && pytest tests/ -v`.

## Team

[Sabados Tech](https://www.youtube.com/channel/UCw89YeTGdK74ZZ97_xcI2FA) — a group of friends from Argentina and Spain who share football and technology.

- [Eugenio Serrano](https://www.linkedin.com/in/eugenio-serrano/)
- [José Mariano Álvarez](https://www.linkedin.com/in/josemarianoalvarez/)
- [Eladio Rincón](https://www.linkedin.com/in/erincon/)

Built for the [Microsoft RAG Hack Challenge](https://github.com/microsoft/RAG_Hack).

## License

MIT
