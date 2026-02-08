# Plan Completo de Rearquitectura - RAG Challenge

## ✅ Estado de Implementación (Actualizado: 2026-02-08)

### Fase 0 - Estabilización Técnica ✅ COMPLETADA
- ✅ Bugs críticos corregidos (module_github, module_azure_openai, app)
- ✅ Configuración centralizada con Pydantic Settings implementada
- ✅ ADRs documentados (4 ADRs completos)
- **Branch:** `feature/rearquitectura-completa`
- **Commits:** d536e87, e40f393, 8c04a65

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

### Fase 2 - Docker Local ⏳ PENDIENTE
- ⏳ Dockerfiles (backend, frontend)
- ⏳ PostgreSQL 17 + pgvector en Docker
- ⏳ SQL Server 2025 Express en Docker
- ⏳ docker-compose.yml con healthchecks
- ⏳ Devcontainer 2.0

### Fase 2A - Migración pgvector ⏳ PENDIENTE
- ⏳ Diseño de columnas vector físicas
- ⏳ Pipeline de embeddings gestionado por aplicación
- ⏳ Migración de Azure AI extensions a pgvector puro

### Fases 3-6 ⏳ PENDIENTES
- Fase 3: Devcontainer 2.0
- Fase 4: Automatización de tareas
- Fase 5: GitHub Actions CI/CD
- Fase 6: Usabilidad y experiencia

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

## Fase 2 - Docker local con imagenes propias (Semanas 3-4)

Objetivo: entorno local reproducible y sin dependencia PaaS para desarrollo base.

- Crear Dockerfiles locales:
  - `backend/Dockerfile`
  - `frontend/Dockerfile`
  - `infra/docker/postgres/Dockerfile` (base `pgvector/pgvector:pg17` o equivalente)
  - `infra/docker/sqlserver/Dockerfile` (base `mcr.microsoft.com/mssql/server:2025-latest`, `MSSQL_PID=Express`)
- Crear `infra/docker-compose.yml` con servicios:
  - `frontend`
  - `backend`
  - `postgres`
  - `sqlserver`
- Agregar `volumes` persistentes y `healthchecks`.
- Incluir init scripts SQL idempotentes por motor.
- Mantener perfiles:
  - `docker compose --profile local up`
  - `docker compose --profile azure up` (si aplica proxy hacia PaaS).

Entregables:
- `docker compose up` levanta app completa local.
- Postgres `pgvector` y SQL Server 2025 Express quedan operativos con healthchecks.
- Seeds/minimos de datos para demo funcional.

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
