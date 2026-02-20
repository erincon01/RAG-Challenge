# Plan Completo de Rearquitectura - RAG Challenge

## ✅ Estado de Implementación (Actualizado: 2026-02-20)

> **Resumen Ejecutivo:** ~85% del plan total completado. Todas las fases del plan original (0-2) y del plan de migración frontend (0-6) están implementadas. Pendiente: migración pgvector, devcontainer, automatización y CI/CD.

---

## Plan Original: Backend/Frontend Separation

### Fase 0 - Estabilización Técnica ✅ COMPLETADA
- ✅ Bugs críticos corregidos (module_github, module_azure_openai, app)
- ✅ Configuración centralizada con Pydantic Settings implementada
- ✅ ADRs documentados (4 ADRs completos)
- **Branch:** `feature/rearquitectura-completa`
- **Commits:** d536e87, e40f393, 8c04a65
- **Fecha completada:** 2026-02-08

### Fase 1 - Separación en Capas Backend/Frontend ✅ COMPLETADA
- ✅ Backend FastAPI con arquitectura por capas completa
  - ✅ API layer (health, matches, events, chat endpoints)
  - ✅ Service layer (SearchService con orquestación completa)
  - ✅ Repository layer (PostgreSQL y SQL Server desacoplados)
  - ✅ Domain layer (entidades, value objects, excepciones)
  - ✅ Adapters layer (OpenAI/Azure OpenAI)
- ✅ Frontend Streamlit refactorizado como cliente HTTP
  - ✅ API client completo (todas las operaciones via HTTP)
  - ✅ Sin acceso directo a base de datos
  - ✅ Modo usuario y desarrollador
- ✅ Documentación completa de todas las capas (READMEs)
- **Branch:** `feature/rearquitectura-completa`
- **Commits:** ba7e9a3, 23f4a1d, ee8d491, f378b3b
- **Fecha completada:** 2026-02-08

### Fase 2 - Docker Local ✅ COMPLETADA

- ✅ Dockerfiles (backend con ODBC+psycopg2, frontend React TypeScript con Vite)
- ✅ PostgreSQL 17 + pgvector en Docker (init scripts idempotentes, schema portable)
- ✅ SQL Server 2025 Express en Docker (custom entrypoint, init scripts idempotentes)
- ✅ docker-compose.yml con healthchecks, volumes persistentes y depends_on
- ✅ .env.docker para configuración local
- ✅ .dockerignore optimizados
- **Branch:** `feature/rearquitectura-completa`
- **Commits:** 9a956b0, 75284be
- **Fecha completada:** 2026-02-08

---

## Plan Frontend Web Migration: React TypeScript

### Fase 0 - Correcciones Bloqueantes Backend ✅ COMPLETADA
- ✅ Endpoint `/api/v1/capabilities` implementado
- ✅ Endpoint `/api/v1/sources/status` con test real de conectividad
- ✅ Validación de DB en `/health/ready`
- ✅ Capacidades por motor documentadas
- **Commits:** 8e6b4cb
- **Fecha completada:** 2026-02-08

### Fase 1 - API de Ingestion y Jobs ✅ COMPLETADA
- ✅ `IngestionService` completo (612 líneas de código)
- ✅ `JobService` con estados (pending/running/success/error/canceled)
- ✅ `StatsBombService` para catálogo remoto
- ✅ Endpoints: `/api/v1/statsbomb/*`, `/api/v1/ingestion/*`
- ✅ Sistema de jobs con tracking y logs
- **Commits:** a16b791
- **Archivos:** `backend/app/services/ingestion_service.py`, `backend/app/services/job_service.py`, `backend/app/services/statsbomb_service.py`
- **Fecha completada:** 2026-02-08

### Fase 2 - Bootstrap Frontend TypeScript ✅ COMPLETADA
- ✅ React 19 + TypeScript + Vite
- ✅ TailwindCSS para estilos
- ✅ TanStack Query para estado y caché
- ✅ React Router para navegación
- ✅ Cliente API tipado completo (151 líneas)
- ✅ Types completos (208 tipos TypeScript)
- ✅ AppShell con navegación
- ✅ UI Settings management
- **Commits:** 5f8ee88
- **Archivos:** `frontend/webapp/` (proyecto completo, 3867 líneas añadidas)
- **Fecha completada:** 2026-02-08

### Fase 3 - Pantallas Operativas Core ✅ COMPLETADA
- ✅ DashboardPage: estado backend, DBs, jobs recientes
- ✅ SourcesPage: selector de motor, test conectividad
- ✅ CatalogPage: catálogo StatsBomb con selección (182 líneas)
- ✅ OperationsPage: descarga/carga con tracking (480 líneas)
- ✅ Local storage para selección de catálogo
- ✅ Polling de estado de jobs
- **Commits:** 3e4b0e4
- **Archivos:** `frontend/webapp/src/pages/*.tsx`, `frontend/webapp/src/lib/storage/catalogSelection.ts`
- **Fecha completada:** 2026-02-08

### Fase 4 - Visores Funcionales y Paridad ✅ COMPLETADA
- ✅ `DataExplorerService` implementado (276 líneas)
- ✅ Endpoint `/api/v1/explorer/*`
- ✅ ExplorerPage con vistas: Competitions, Matches, Teams, Players, Events, Tables Info (272 líneas)
- ✅ Paridad funcional con menus del `app.py` legacy
- **Commits:** 38db8d5
- **Archivos:** `backend/app/services/data_explorer_service.py`, `backend/app/api/v1/explorer.py`, `frontend/webapp/src/pages/ExplorerPage.tsx`
- **Fecha completada:** 2026-02-08

### Fase 5 - Embeddings y Chat Avanzado ✅ COMPLETADA
- ✅ EmbeddingsPage: estado de cobertura, rebuild por match (193 líneas)
- ✅ ChatPage: RAG con restricciones dinámicas según capacidades (242 líneas)
- ✅ Endpoint `/api/v1/embeddings/*`
- ✅ UI capability-aware (adapta según motor seleccionado)
- **Commits:** e25b511
- **Archivos:** `frontend/webapp/src/pages/EmbeddingsPage.tsx`, `frontend/webapp/src/pages/ChatPage.tsx`
- **Fecha completada:** 2026-02-08

### Fase 6 - Hardening, Testing y Cutover ✅ PARCIALMENTE COMPLETADA
- ✅ Filtros de limpieza en descargas
- ✅ Limpieza de jobs completados
- ✅ Terminal de ejecución
- ✅ Frontend web en docker-compose
- ⏳ Tests backend (pendiente)
- ⏳ Tests frontend (pendiente)
- ⏳ Logging estructurado (pendiente)
- ✅ Streamlit marcado como deprecated en docs
- **Commits:** db0cb73, b1be41a, 4849d53, 1204ca1
- **Fecha:** 2026-02-08 a 2026-02-20

---

## Fases Pendientes

### Fase 2A - Migración pgvector ⏳ CRÍTICA - NO INICIADA
**Objetivo:** Eliminar dependencias Azure PaaS para PostgreSQL

**Estado:** ADR-003 en "Proposed", checklist sin completar

**Tareas pendientes:**
- ⏳ Actualizar schema con columnas metadata (embedding_status, embedding_updated_at, embedding_error)
- ⏳ Implementar embedding generation service en backend
- ⏳ Crear batch processing worker
- ⏳ Backfill de embeddings existentes
- ⏳ Validar paridad funcional y de performance
- ⏳ Actualizar queries del repositorio
- ⏳ Eliminar dependencias `azure_ai` y `azure_local_ai`

**Impacto:** Bloqueante para independencia total de Azure PaaS

**Estimación:** 3-4 semanas

### Fase 3 - Devcontainer 2.0 ⏳ EN PROGRESO
**Objetivo:** Devcontainer funcional y reproducible

**Estado:** Iniciado (commit 75284be), no finalizado

**Tareas pendientes:**
- ⏳ Corregir `devcontainer.json` para usar docker-compose
- ⏳ Implementar `postCreateCommand` (deps, migraciones, seed)
- ⏳ Implementar `postStartCommand` (health checks)
- ⏳ Configurar port forwarding completo
- ⏳ Validar "Reopen in Container" funciona en entorno limpio

**Estimación:** 1 semana

### Fase 4 - Automatización de Tareas ⏳ NO INICIADA
**Objetivo:** CLI de tareas para operaciones comunes

**Tareas pendientes:**
- ⏳ Crear task runner (`task.ps1` / `task.sh` / `Taskfile.yml` / `justfile`)
- ⏳ Comandos: `bootstrap`, `db-up`, `db-migrate`, `db-seed`, `test`, `lint`, `run-local`
- ⏳ Estandarizar migraciones Postgres (Alembic/Flyway)
- ⏳ Estandarizar migraciones SQL Server
- ⏳ Idempotencia total

**Estimación:** 1-2 semanas

### Fase 5 - GitHub Actions CI/CD ⏳ NO INICIADA
**Objetivo:** Pipeline de calidad automatizada

**Tareas pendientes:**
- ⏳ Workflow `ci.yml` (lint, tests, integration tests)
- ⏳ Workflow `docker.yml` (build, vulnerability scan, push GHCR)
- ⏳ Workflow `release.yml` (semver, changelog)
- ⏳ Branch protection + required checks
- ⏳ Codeowners (opcional)

**Estimación:** 1-2 semanas

### Fase 6 - Usabilidad Final ⏳ PARCIALMENTE COMPLETADA
**Objetivo:** Polish UX y observabilidad

**Completado:**
- ✅ Modo usuario vs desarrollador
- ✅ Validaciones en UI

**Pendiente:**
- ⏳ Logging estructurado con `request_id`, `match_id`
- ⏳ Métricas: latencia, errores, tokens, coste
- ⏳ Caching de consultas frecuentes
- ⏳ Paginación optimizada en tablas grandes
- ⏳ Timeout/retry configurables en LLM/DB

**Estimación:** 2-3 semanas

---

## 1) Objetivo

Rearquitecturar la aplicacion para pasar de un enfoque monolitico/manual y centrado en PaaS, a una solucion por capas (backend + frontend), ejecutable de forma local con Dockerfiles e imagenes locales, orquestada con docker-compose, con devcontainer funcional y pipeline de calidad en GitHub Actions.

---

## 2) Diagnostico actual (analisis del estado real)

### 2.1 Arquitectura y codigo

- App monolitica Streamlit con logica de UI + negocio + acceso a datos en el mismo flujo:
  - `app.py:16`
  - `app.py:47`
- No existe capa backend HTTP/API dedicada (no FastAPI/Flask ni contratos API).
- No existe separacion clara frontend/backend.
- Alto acoplamiento entre modulos y duplicacion de conexion DB:
  - `python_modules/module_data.py:10`
  - `python_modules/module_azure_openai.py:16`
  - `python_modules/module_github.py:10`
- Query SQL dinamica generada por LLM y ejecutada sin whitelist estricta:
  - `python_modules/module_azure_openai.py:551`
  - `python_modules/module_data.py:1029`

### 2.2 Docker y entorno local

- No existe `docker-compose.yml` en raiz.
- No hay Dockerfile de aplicacion en raiz, pero scripts lo referencian:
  - `deploy/docker-commands.ps1:6` usa `-f dockerfile` (archivo inexistente en raiz).
- Existe Dockerfile en `.devcontainer`, pero `devcontainer.json` apunta a un Dockerfile no existente:
  - `.devcontainer/devcontainer.json:9` -> `"dockerfile": "dockerfile"` (inconsistente con estructura actual).

### 2.3 Devcontainer

- Hay base de devcontainer, pero con configuracion incompleta/inconsistente para reproducibilidad full-stack.
- `postStartCommand` ejecuta Streamlit directo, sin levantar dependencias (DBs locales) ni preparar esquema/migraciones:
  - `.devcontainer/devcontainer.json:36`

### 2.4 Automatizacion y scripts

- Flujo fuertemente manual con scripts `.ps1` y SQL sueltos:
  - `deploy/azure_commands.ps1`
  - `deploy/docker-commands.ps1`
  - `postgres/setup_postgres.ps1`
- Falta un runner unificado de tareas (Make/Taskfile/CLI) para operaciones repetibles.

### 2.5 Calidad, CI/CD, testing y observabilidad

- No hay carpeta `.github/workflows` (sin CI automatizada).
- No se observan tests unitarios/integracion.
- No hay gates de lint, seguridad, coverage, ni build/push de imagenes.

### 2.6 Documentacion y deuda de consistencia

- Documentacion y scripts referencian rutas/archivos que no existen (drift documental):
  - `python/01-download_to_local.py` (no existe)
  - `python/02-load_data_into_postgres_from_local.py` (no existe)
  - `python/03-load_tables_from_local_to_postgres_azure.py` (no existe)
  - `postgres/tables_setup_onprem.sql` (no existe)

### 2.7 Hallazgos puntuales de estabilidad

- Bug potencial por variable no definida:
  - `python_modules/module_github.py:67` usa `password` no definida en ese scope.
  - `python_modules/module_github.py:242` usa `dataset` antes de asignarla.
- Bug funcional:
  - `python_modules/module_azure_openai.py:415` pisa `top_n = 10`, ignorando parametro recibido.
  - `app.py:246` compara lista `language` con string, condicion siempre verdadera.
  - `app.py:256` usa `dataset` no definido al mostrar logs.

### 2.8 Brecha DB especifica para el cambio solicitado

- Postgres actual está acoplado a PaaS Azure:
  - uso de extensiones `azure_ai` y `azure_local_ai` en `postgres/server_setup_to_use_embeddings.sql`.
  - columnas generadas con `azure_local_ai.create_embeddings(...)` y `azure_openai.create_embeddings(...)` en `postgres/tables_setup_azure_open_ai-create-quarter_sec.sql`.
  - consultas runtime que invocan `create_embeddings(...)` en `python_modules/module_azure_openai.py`.
- Implicación: pasar a `pgvector` local requiere rediseñar la generación de embeddings (de DB-managed a app-managed/worker).
- SQL Server actual asume capacidades de Azure SQL PaaS (por ejemplo, `sp_invoke_external_rest_endpoint` en stored procedures), por lo que la migración a SQL Server 2025 Express en Linux debe validar compatibilidad feature por feature antes de cerrar el diseño final.

---

## 3) Arquitectura objetivo (to-be)

## 3.1 Capas

- Frontend:
  - Streamlit mantenido como UI inicial (menor coste de migracion).
  - Consume backend via REST (el frontend deja de consultar DB directo).
- Backend:
  - FastAPI con capas:
    - `api` (routers, DTOs, validacion)
    - `service` (casos de uso)
    - `repository` (acceso DB y query builders)
    - `domain` (entidades y reglas)
    - `adapters` (OpenAI/Azure OpenAI, proveedores vectoriales)
- Data layer:
  - Postgres local en Docker con imagen `pgvector/pgvector:pg17` (o tag estable equivalente) y extension `vector` habilitada.
  - SQL Server 2025 Express en Linux Docker con imagen `mcr.microsoft.com/mssql/server:2025-latest` y `MSSQL_PID=Express`.
  - Migraciones versionadas por motor (Postgres y SQL Server) y seeds idempotentes por entorno.

## 3.2 Estructura propuesta de repositorio

```text
/
  backend/
    app/
      api/
      services/
      repositories/
      domain/
      adapters/
      config/
    tests/
    Dockerfile
  frontend/
    streamlit_app/
      app.py
      pages/
      services/        # cliente HTTP al backend
      components/
    Dockerfile
  infra/
    docker/
      postgres/
        Dockerfile
        initdb/
      sqlserver/
        Dockerfile
        initdb/
    docker-compose.yml
  migrations/
    postgres/
    sqlserver/
  scripts/
    task.ps1
    task.sh
  .devcontainer/
    devcontainer.json
    docker-compose.devcontainer.yml
  .github/
    workflows/
      ci.yml
      docker.yml
      release.yml
```

## 3.3 Contrato de imagenes DB en Docker

- Postgres:
  - Imagen base: `pgvector/pgvector:pg17`.
  - Extension requerida: `CREATE EXTENSION IF NOT EXISTS vector;`.
  - Puerto: `5432`.
  - Volumen persistente dedicado.
- SQL Server:
  - Imagen base: `mcr.microsoft.com/mssql/server:2025-latest`.
  - Edition target: `Express` via `MSSQL_PID=Express`.
  - OS: Linux container.
  - Puertos: `1433`.
  - Variables minimas: `ACCEPT_EULA=Y`, `MSSQL_SA_PASSWORD`, `MSSQL_PID=Express`.
- Compose:
  - Healthchecks obligatorios antes de arrancar backend/frontend.
  - Init scripts idempotentes por motor.
  - Perfil `local` como camino por defecto para desarrollo.

---

## 4) Plan de ejecucion por fases

## Fase 0 - Stabilizacion tecnica ✅ COMPLETADA

**Objetivo:** bajar riesgo antes de mover arquitectura.

**Tareas completadas:**
- ✅ Corregir bugs minimos bloqueantes:
  - ✅ `module_github.py` variables no definidas (password, dataset)
  - ✅ `module_azure_openai.py` respetar `top_n` (eliminado hardcoded value)
  - ✅ `app.py` condiciones y logs (language comparison, dataset logs)
- ✅ Unificar configuracion en `settings` central (Pydantic BaseSettings)
  - ✅ `config/settings.py` con DatabaseConfig, OpenAIConfig, RepositoryConfig
  - ✅ Validación fail-fast al arranque
  - ✅ Support para entornos: `local`, `azure`, `test`
- ✅ Definir convencion de entornos y actualizar `.env.example`

**Entregables:**
- ✅ Commits de hardening (d536e87)
- ✅ 4 ADRs completos documentados:
  - ADR-001: Layered Architecture
  - ADR-002: Centralized Configuration
  - ADR-003: pgvector Migration Strategy
  - ADR-004: Local Docker Infrastructure

## Fase 1 - Separacion en capas backend/frontend ✅ COMPLETADA

**Objetivo:** desacoplar UI del acceso directo a DB.

**Tareas completadas:**

### 1.1 Backend FastAPI ✅
- ✅ Estructura completa con capas (api, services, repositories, domain, adapters, core)
- ✅ Endpoints implementados:
  - ✅ `GET /` - Root with API info
  - ✅ `GET /api/v1/health` - Health check detallado
  - ✅ `GET /api/v1/health/ready` - Readiness probe
  - ✅ `GET /api/v1/health/live` - Liveness probe
  - ✅ `GET /api/v1/competitions` - List competitions
  - ✅ `GET /api/v1/matches` - List matches con filtros
  - ✅ `GET /api/v1/matches/{id}` - Match details
  - ✅ `GET /api/v1/events` - List events por match
  - ✅ `GET /api/v1/events/{id}` - Event details
  - ✅ `POST /api/v1/chat/search` - Búsqueda semántica + AI chat

### 1.2 Repositorios Desacoplados ✅
- ✅ `repositories/base.py` - Interfaces abstractas (contratos)
- ✅ `repositories/postgres.py` - Implementación PostgreSQL completa
  - PostgresMatchRepository, PostgresEventRepository
  - Soporte pgvector operators (<=> <#> <->)
  - Query parametrizadas, context managers
- ✅ `repositories/sqlserver.py` - Implementación SQL Server completa
  - SQLServerMatchRepository, SQLServerEventRepository
  - VECTOR_DISTANCE function support
  - Compatible con SQL Server 2025 Express

### 1.3 Service Layer ✅
- ✅ `services/search_service.py` - Orquestación completa de búsqueda
  - Traducción multi-idioma
  - Generación de embeddings
  - Búsqueda vectorial
  - Generación de respuestas con LLM
  - Context building con match info

### 1.4 Domain Layer ✅
- ✅ `domain/entities.py` - Entidades completas
  - Match, EventDetail, Competition, Team, Stadium, Referee
  - SearchRequest, SearchResult, ChatResponse
  - Enums: SearchAlgorithm, EmbeddingModel
- ✅ `domain/exceptions.py` - Excepciones de dominio

### 1.5 Adapters Layer ✅
- ✅ `adapters/openai_client.py` - Cliente OpenAI/Azure OpenAI
  - create_embedding()
  - create_chat_completion()
  - translate_to_english()

### 1.6 Frontend Refactorizado ✅
- ✅ `frontend/streamlit_app/services/api_client.py` - Cliente HTTP completo
  - Todos los métodos para endpoints del backend
  - Error handling, timeouts
  - Configuración via BACKEND_URL
- ✅ `frontend/streamlit_app/app_refactored.py` - App Streamlit limpia
  - Sin acceso directo a BD
  - Solo comunicación HTTP con backend
  - Modo usuario vs desarrollador
  - Multi-idioma, personalidades (Andrés Montes, Chiquito)

### 1.7 Documentación ✅
- ✅ READMEs completos para cada capa:
  - `backend/app/api/README.md` - API Layer patterns
  - `backend/app/services/README.md` - Service Layer patterns
  - `backend/app/repositories/README.md` - Repository patterns
  - `backend/app/domain/README.md` - Domain-Driven Design
  - `backend/app/adapters/README.md` - Adapter patterns
  - `frontend/README.md` - Frontend architecture
  - `backend/README.md` - Backend overview
  - `config/README.md` - Configuration guide

**Entregables:**
- ✅ Backend y frontend completamente desacoplados en carpetas separadas
- ✅ Contrato OpenAPI versionado (auto-generado en /docs)
- ✅ Documentación exhaustiva de arquitectura y patrones

## Fase 2 - Docker local con imagenes propias ✅ COMPLETADA

Objetivo: entorno local reproducible y sin dependencia PaaS para desarrollo base.

**Tareas completadas:**

### 2.1 Dockerfiles ✅

- ✅ `backend/Dockerfile` - Python 3.11-slim + ODBC Driver 18 + psycopg2 + config module
  - Build context desde raíz del proyecto para incluir `config/`
  - Sistema de dependencias: gnupg2, curl, libpq-dev, gcc, msodbcsql18, unixodbc-dev
- ✅ `frontend/Dockerfile` - Python 3.11-slim + Streamlit
  - Entrypoint: `streamlit run streamlit_app/app_refactored.py --server.headless=true`
- ✅ `infra/docker/sqlserver/Dockerfile` - Extiende `mcr.microsoft.com/mssql/server:2025-latest`
  - Custom entrypoint (`setup.sh`) que espera SQL Server ready y ejecuta init scripts
  - `MSSQL_PID=Express`

### 2.2 Init Scripts Idempotentes ✅

- ✅ PostgreSQL (`infra/docker/postgres/initdb/`):
  - `01-extensions.sql` - Habilita extensión `vector`
  - `02-schema.sql` - Schema completo portable (matches, events, events_details, events_details__quarter_minute con columnas VECTOR físicas + índices HNSW)
- ✅ SQL Server (`infra/docker/sqlserver/initdb/`):
  - `01-schema.sql` - Crea DB `rag_challenge` + todas las tablas (matches, lineups, players, events, events_details, events_details__15secs_agg) con `IF NOT EXISTS`

### 2.3 Docker Compose ✅

- ✅ `docker-compose.yml` en raíz con 4 servicios:
  - `postgres` (pgvector/pgvector:pg17) - healthcheck con `pg_isready`
  - `sqlserver` (custom build) - healthcheck con `sqlcmd`
  - `backend` (FastAPI) - healthcheck con `/api/v1/health/live`, depends_on DB healthy
  - `frontend` (Streamlit) - depends_on backend healthy
- ✅ Volúmenes persistentes: `postgres_data`, `sqlserver_data`
- ✅ Volume mounts para desarrollo con hot-reload
- ✅ Variables de entorno con defaults sensatos

### 2.4 Configuración ✅

- ✅ `.env.docker` - Configuración local para Docker
- ✅ `.dockerignore` - Optimizado para contexto de build
- ✅ `backend/.dockerignore`, `frontend/.dockerignore`

**Entregables:**

- ✅ `docker compose up` levanta app completa local
- ✅ Postgres pgvector y SQL Server 2025 Express con healthchecks
- ✅ Schemas inicializados automáticamente al primer arranque

## Fase 2A - Migracion profunda Postgres PaaS -> Postgres + pgvector (Semanas 4-6)

Objetivo: reemplazar dependencias Azure-specific (`azure_ai`, `azure_local_ai`) por una arquitectura portable basada en `pgvector` y embeddings gestionados por la aplicacion.

Alcance (impacto alto detectado):
- Scripts SQL actuales dependen de funciones PaaS (`azure_local_ai.create_embeddings`, `azure_openai.create_embeddings`) en columnas generadas.
- Setup de servidor actual exige extensiones no disponibles en Postgres local estandar.
- Codigo Python actual construye queries de similitud invocando `create_embeddings(...)` en tiempo de consulta.

Trabajo tecnico exhaustivo:
- Diseñar nuevo modelo de embedding en Postgres:
  - columnas `vector` fisicas (no generadas por extension Azure).
  - estrategia por modelo (`ada_002`, `t3_small`, `t3_large`, `e5`) con control de dimensiones.
- Reescribir pipeline de enriquecimiento:
  - resumen -> embedding (backend worker) -> persistencia.
  - procesamiento batch incremental por `match_id` y por estado (`pending`, `done`, `error`).
- Reescribir consultas vectoriales para `pgvector` puro:
  - cosine (`<=>`), inner product (`<#>`), l2 (`<->`).
  - query parametrizada, sin interpolacion de texto.
- Definir indexacion ANN por caso:
  - HNSW para `vector_cosine_ops`, `vector_ip_ops`, `vector_l2_ops`.
  - tuning de `m`, `ef_construction`, `ef_search`.
- Diseñar migraciones y estrategia de backfill:
  - migraciones separadas por tabla.
  - batch sizes y checkpoints para recuperacion.
- Validar paridad funcional y de performance contra baseline actual:
  - precision top-k de recuperacion.
  - latencia p50/p95 por algoritmo.
  - coste de regeneracion de embeddings.

Entregables:
- ADR especifica de migracion PaaS -> pgvector.
- Scripts SQL y migraciones 100% portables en local Docker.
- Worker de embeddings estable con reintentos y trazabilidad.
- Informe de paridad (calidad + rendimiento) frente al flujo actual.

## Fase 3 - Devcontainer 2.0 (Semana 6)

Objetivo: retomarlo de forma estable.

- Corregir `.devcontainer/devcontainer.json` para usar compose y servicios.
- Definir contenedor de desarrollo principal (backend o tooling) con acceso a DBs.
- `postCreateCommand`:
  - instalar dependencias
  - ejecutar migraciones
  - cargar dataset minimo
- `postStartCommand`:
  - validar salud de backend/frontend
- Forward de puertos:
  - frontend (8501)
  - backend (8000)
  - postgres (5432)
  - sqlserver (1433)

Entregables:
- `Reopen in Container` funcional en entorno limpio.

## Fase 4 - Automatizacion de tareas (Semana 7)

Objetivo: eliminar operaciones manuales repetitivas.

- Crear CLI de tareas (`task.ps1`, `task.sh` o `justfile`/`Taskfile.yml`) para:
  - `bootstrap`
  - `db-up`
  - `db-migrate`
  - `db-seed`
  - `test`
  - `lint`
  - `run-local`
- Estandarizar migraciones:
  - Postgres: Alembic/Flyway/Liquibase (uno solo, no mezclar).
  - SQL Server: migraciones versionadas equivalentes.
- Idempotencia total de scripts.

Entregables:
- Setup desde cero en <= 20 minutos con un solo comando.

## Fase 5 - GitHub Actions (Semanas 7-8)

Objetivo: calidad continua y entregables automatizados.

- Workflow `ci.yml` (PR + push):
  - lint (`ruff`, `black --check`)
  - type-check (`mypy` opcional incremental)
  - unit tests (`pytest`)
  - integration tests con servicios (`postgres`, `sqlserver`) via `services`.
- Workflow `docker.yml`:
  - build de imagenes (`backend`, `frontend`)
  - scan de vulnerabilidades (Trivy/Grype)
  - push a GHCR en `main` y tags.
- Workflow `release.yml`:
  - versionado semantico
  - changelog
  - artefactos
- Protecciones:
  - branch protection + required checks
  - codeowners (si aplica)

Entregables:
- Pipeline verde en PR.
- Imagenes versionadas en registro.

## Fase 6 - Usabilidad y experiencia (Semanas 8-10)

Objetivo: mejorar UX y operacion diaria.

- Simplificar UI:
  - modo usuario (simple)
  - modo avanzado (developer)
- Validaciones y mensajes de error accionables.
- Trazabilidad:
  - logging estructurado (request_id, match_id, source)
  - metricas basicas (latencia, errores, tokens, coste estimado)
- Performance:
  - caching de consultas frecuentes
  - paginacion en tablas grandes
  - timeout/retry en llamadas LLM/DB.

Entregables:
- Mejora medible de tiempo de respuesta y claridad de uso.

---

## 5) Definicion de listo (DoD) por bloque

- Arquitectura:
  - Sin acceso directo DB desde frontend.
  - >= 80% de endpoints clave cubiertos con tests de contrato.
- Infra local:
  - `docker compose up` levanta todo sin pasos manuales externos.
  - DBs inicializadas automaticamente.
- Devcontainer:
  - Onboarding reproducible en entorno limpio.
- CI/CD:
  - Todo PR ejecuta lint + tests + build.
  - Falla bloquea merge.

---

## 6) Riesgos y mitigaciones

- Riesgo: diferencias funcionales entre Azure PaaS y local (especialmente en Postgres por uso actual de `azure_ai/azure_local_ai`).
  - Mitigacion: fase dedicada de migracion a `pgvector`, adapter por proveedor y tests de paridad por motor.
- Riesgo: diferencias de capacidades SQL entre Azure SQL y SQL Server 2025 Express en contenedor Linux.
  - Mitigacion: matriz de compatibilidad por feature (`VECTOR`, endpoints REST, seguridad) y fallback en backend cuando una feature no exista.
- Riesgo: costo de migrar todo de una vez.
  - Mitigacion: enfoque incremental por endpoints y feature flags.
- Riesgo: drift documental.
  - Mitigacion: docs generadas desde comandos reales + checks en CI.
- Riesgo: seguridad en SQL generado por LLM.
  - Mitigacion: parser/whitelist de SQL permitida + solo SELECT + limites estrictos.

---

## 7) Backlog priorizado (primeras 13 tareas)

1. Corregir bugs conocidos en `app.py`, `module_github.py`, `module_azure_openai.py`.
2. Crear `backend/` con FastAPI y endpoint `health`.
3. Extraer modulo de configuracion central (`settings`).
4. Implementar repositorio Postgres y SQL Server desacoplados.
5. Crear cliente frontend->backend.
6. Crear Dockerfile backend.
7. Crear Dockerfile frontend.
8. Crear imagen local Postgres basada en `pgvector/pgvector` con init scripts y migraciones.
9. Crear imagen local SQL Server 2025 Express (Linux) con `MSSQL_PID=Express`.
10. Crear `infra/docker-compose.yml` con healthchecks y perfiles.
11. Ejecutar migracion profunda de embeddings en Postgres (de funciones Azure a pipeline propio).
12. Arreglar devcontainer para compose y bootstrap automatico.
13. Crear GH Actions CI (lint + tests + build + integration tests con Postgres/SQL Server).

---

## 8) Resultado esperado al finalizar

- Proyecto modular por capas.
- Entorno local completo con Dockerfiles + docker-compose (Postgres y SQL Server incluidos).
- Devcontainer utilizable para desarrollo diario.
- Menos trabajo manual, mas comandos estandar.
- Calidad controlada por GitHub Actions.
- Base lista para evolucionar la aplicacion sin deuda estructural.

---

## 9) Buenas practicas de codificacion (obligatorias en la re-arquitectura)

### 9.1 Gestion de variables y parametros

- Evitar variables globales y estado implicito.
- Pasar dependencias explicitas por constructor o parametros (inyeccion de dependencias).
- Reducir firmas con muchos parametros: usar objetos de configuracion tipados (`Settings`, `SearchRequest`, etc.).
- Limitar parametros por funcion (objetivo: <= 5). Si se supera, crear DTO o value object.

### 9.2 Variables de entorno y configuracion

- Centralizar todo en una unica capa de configuracion (`settings.py`) con validacion al arranque.
- Fail-fast: si falta una variable critica, la aplicacion no arranca.
- Separar configuracion por entorno (`local`, `test`, `azure`) sin `if` dispersos en el codigo.
- No leer `os.getenv()` dentro de funciones de dominio o repositorios; leer una vez en `config`.
- Mantener `.env.example` completo, consistente y versionado con cada cambio.

### 9.3 Tamano y complejidad de funciones

- Evitar funciones largas (objetivo: <= 40 lineas de logica real).
- Una funcion debe tener una sola responsabilidad clara.
- Extraer bloques repetidos a funciones pequenas reutilizables.
- Reducir anidacion (objetivo: maximo 2-3 niveles) usando retornos tempranos.

### 9.4 Simplificacion y abstraccion

- Separar por capas: `api` -> `service` -> `repository` -> `adapter`.
- La UI no debe contener logica de negocio ni acceso DB directo.
- Encapsular SQL por motor en repositorios; evitar SQL embebido en multiples lugares.
- Definir interfaces o puertos para proveedores externos (LLM, DB, archivos) y facilitar pruebas.

### 9.5 Seguridad y robustez del codigo

- Prohibido ejecutar SQL con interpolacion directa de strings para entrada de usuario.
- Usar consultas parametrizadas y whitelist de operaciones permitidas.
- Estandarizar manejo de errores con excepciones de dominio y mensajes accionables.
- No exponer secretos ni datos sensibles en logs.

### 9.6 Estandares de calidad automatizados

- Lint y formato obligatorios en CI (`ruff`, `black --check`).
- Tipado progresivo (`mypy`) en modulos criticos.
- Cobertura minima para logica de negocio (objetivo inicial: >= 70%).
- Tests unitarios para servicios y tests de integracion para repositorios.

### 9.7 Criterios DoD de codigo (por PR)

- No introduce nuevas funciones monoliticas.
- No agrega nuevas lecturas directas de `os.getenv()` fuera de `config`.
- Incluye tests para logica nueva o modificada.
- Pasa lint, tests y build en GitHub Actions.
- Actualiza documentacion si cambia contrato, config o flujo operativo.

### 9.8 Aplicacion inmediata al estado actual del repo

- Dividir `call_gpt` en casos de uso pequenos y servicios reutilizables.
- Eliminar duplicacion de `decode_source/get_connection` entre modulos.
- Consolidar configuracion de DB y LLM en un unico modulo tipado.
- Sustituir scripts manuales sueltos por comandos de tarea estandarizados.





---

## 10) Referencias tecnicas verificadas (para decisiones DB)

- SQL Server en Linux Docker (quickstart oficial, tag 2025):
  - https://learn.microsoft.com/en-us/sql/linux/quickstart-install-connect-docker?view=sql-server-ver17
- Variables de entorno SQL Server en contenedor (`MSSQL_PID=Express` soportado):
  - https://learn.microsoft.com/en-us/sql/linux/sql-server-linux-configure-environment-variables?view=sql-server-ver17
- Imagen Docker para Postgres con pgvector (README oficial):
  - https://github.com/pgvector/pgvector
