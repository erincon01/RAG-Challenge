# Plan de Migracion de Frontend Web (sin Streamlit)

Fecha: 2026-02-08
Estado: Propuesto

## 1) Objetivo
Sustituir Streamlit por un frontend web moderno compatible con el backend FastAPI actual, y ampliar el backend para cubrir el flujo completo de ingestion/carga/consulta de datos de StatsBomb en PostgreSQL y SQL Server, incluyendo estado real de embeddings por motor.

## 2) Resumen ejecutivo
- El backend actual ya soporta consulta de competiciones, partidos, eventos y chat semantico.
- El frontend Streamlit refactorizado cubre solo el caso de chat sobre partidos; no cubre ingestion ni operacion completa.
- Existe un frontend legacy (`app.py`) con muchos menus utiles, pero acoplado a DB y modulos legacy.
- Hay inconsistencias tecnicas que deben resolverse antes de migrar UI (especialmente SQL Server).
- Recomendacion de stack: `React + TypeScript + Tailwind` (Vite).

## 3) Estado actual (AS-IS)

### 3.1 Frontend
- Frontend actual refactorizado: una sola pantalla de analisis/chat sobre partidos.
  - Referencias: `frontend/streamlit_app/app_refactored.py:30`, `frontend/streamlit_app/app_refactored.py:95`
- Frontend legacy con muchos menus/pantallas (Project, Competitions, Matches, Teams, Players, Events, Chat Logs, etc.).
  - Referencias: `app.py:305`, `python_modules/module_streamlit_frontend.py:318`, `python_modules/module_streamlit_frontend.py:427`, `python_modules/module_streamlit_frontend.py:687`
- No existe proyecto TypeScript/Tailwind en el repo.

### 3.2 Backend API disponible
Endpoints implementados:
- `GET /api/v1/health`, `/health/ready`, `/health/live`
- `GET /api/v1/competitions`
- `GET /api/v1/matches`, `GET /api/v1/matches/{match_id}`
- `GET /api/v1/events`, `GET /api/v1/events/{event_id}`
- `POST /api/v1/chat/search`
- Referencias: `backend/app/api/v1/health.py:35`, `backend/app/api/v1/matches.py:23`, `backend/app/api/v1/events.py:18`, `backend/app/api/v1/chat.py:23`

Brecha funcional para el objetivo solicitado:
- No hay endpoints para:
  - descubrir competiciones/matches desde StatsBomb remoto,
  - lanzar descargas,
  - cargar a DB por motor,
  - ver progreso de jobs,
  - exponer estado de embeddings por tabla/motor,
  - consultar visores tipo teams/players/tables-info del frontend legacy.

### 3.3 Ingestion y scripts
- Existen funciones utiles en modulos legacy (`module_github.py`, `module_data.py`), pero no integradas al backend nuevo.
  - Referencias: `python_modules/module_github.py:215`, `python_modules/module_data.py:530`
- Scripts SQL/Python de carga parcialmente rotos o desactualizados:
  - imports a modulos no existentes (`module_sql_azure`),
  - llamadas a funciones no existentes (`load_events_data_into_sql_paas`, `load_lineups_data_into_sql_paas`).
  - Referencias: `sqlserver/01_download_to_local.py:14`, `sqlserver/02_load_data_into_database_from_local.py:17`

### 3.4 Estado de DB y embeddings

#### PostgreSQL
- Schema local docker incluye `events_details__quarter_minute` con columnas vector para 4 modelos e indices HNSW.
  - Referencias: `infra/docker/postgres/initdb/02-schema.sql:72`, `infra/docker/postgres/initdb/02-schema.sql:84`
- Repositorio backend Postgres soporta modelos `ada-002`, `t3-small`, `t3-large`, `e5` y algoritmos cosine/inner/l2.
  - Referencias: `backend/app/repositories/postgres.py:349`, `backend/app/repositories/postgres.py:356`
- Falta endpoint de estado de cobertura de embeddings (porcentaje `IS NOT NULL`) y pipeline de regeneracion desde API.

#### SQL Server
- Schema local docker usa tabla `events_details__15secs_agg` y columna `_15secs`.
  - Referencias: `infra/docker/sqlserver/initdb/01-schema.sql:167`, `infra/docker/sqlserver/initdb/01-schema.sql:172`
- Repositorio backend SQL Server consulta `event_details_15secs_agg` y `quarter_sec` (nombres distintos), por lo que hay alto riesgo de fallo operativo.
  - Referencias: `backend/app/repositories/sqlserver.py:311`, `backend/app/repositories/sqlserver.py:313`, `backend/app/repositories/sqlserver.py:439`
- Repositorio mapea `embedding_3_large`, pero schema actual no la define en `events_details__15secs_agg` local.
  - Referencias: `backend/app/repositories/sqlserver.py:373`, `infra/docker/sqlserver/initdb/01-schema.sql:167`

#### Validaciones cruzadas faltantes
- API acepta `l1_manhattan`, pero repositorios no implementan ese algoritmo.
  - Referencias: `backend/app/api/v1/models.py:141`, `backend/app/repositories/postgres.py:356`, `backend/app/repositories/sqlserver.py:377`
- Health readiness no valida conexion real a DB.
  - Referencia: `backend/app/api/v1/health.py:92`

### 3.5 Documentacion
- Hay drift entre docs y estado real (scripts y rutas inexistentes).
  - Referencias: `docs/azure-postgres.md:58`, `docs/azure-postgres.md:275`, `docs/app-use-case.md:8`
- `backend/README.md` marca como "Coming soon" endpoints/partes ya implementadas.
  - Referencias: `backend/README.md:98`, `backend/README.md:204`

## 4) Decision de frontend

### Recomendado
- `React + TypeScript + Vite + TailwindCSS`
- Estado/cache: `TanStack Query`
- Routing: `React Router`
- Validacion de formularios: `zod` + `react-hook-form`

## 5) Arquitectura objetivo (TO-BE)

### 5.1 Frontend
- SPA TypeScript en `frontend/webapp/`
- UI desacoplada totalmente de DB
- Todo via REST al backend

### 5.2 Backend
- Mantener FastAPI por capas y agregar modulo de orquestacion:
  - `app/services/ingestion_service.py`
  - `app/api/v1/ingestion.py`
  - `app/services/capabilities_service.py`
  - `app/api/v1/capabilities.py`
- Añadir ejecucion de jobs con seguimiento de estado.

### 5.3 Contrato minimo nuevo de API
- `GET /api/v1/capabilities`
- `GET /api/v1/sources/status`
- `GET /api/v1/statsbomb/competitions`
- `GET /api/v1/statsbomb/matches?competition_id=&season_id=`
- `POST /api/v1/ingestion/download`
- `POST /api/v1/ingestion/load`
- `POST /api/v1/ingestion/aggregate`
- `POST /api/v1/ingestion/embeddings/rebuild`
- `GET /api/v1/ingestion/jobs`
- `GET /api/v1/ingestion/jobs/{job_id}`
- `GET /api/v1/embeddings/status?source=&table=&match_id=`
- `GET /api/v1/teams`, `GET /api/v1/players`, `GET /api/v1/tables-info` (para recuperar pantallas legacy)

## 6) Menus/pantallas propuestas
1. Dashboard
- Estado backend + DBs + jobs recientes + cobertura embeddings.

2. Data Sources
- Selector de motor (`postgres` / `sqlserver`), test de conectividad y capacidades por motor.

3. Catalogo StatsBomb
- Buscar y seleccionar competiciones/temporadas.
- Vista de partidos disponibles por competicion.

4. Descarga
- Lanzar descarga de `matches`, `lineups`, `events` por seleccion.
- Ver progreso, errores, reintentos.

5. Carga a Base de Datos
- Elegir destino (Postgres o SQL Server).
- Ejecutar carga y ver resumen de filas afectadas.

6. Agregaciones y Resumenes
- Construccion de tablas agregadas (`quarter_minute`/`15secs_agg`, `minute_agg`).
- Generacion de `summary`.

7. Embeddings
- Estado de embeddings por motor/modelo/tabla.
- Rebuild de embeddings por `match_id` o lote.

8. Explorador de Datos
- Competitions, Matches, Teams, Players, Events, Tables Info.

9. Chat RAG
- Modo Usuario y Modo Developer.
- Filtros por motor, algoritmo y modelo compatibles.

10. Historial y Logs
- Historial de preguntas/respuestas y logs operativos de ingestion.

## 7) Plan por fases

### Fase 0 - Correcciones bloqueantes (backend y contrato)
Objetivo: dejar base estable para construir frontend web.

Tareas:
- Corregir repositorio SQL Server a nombres reales de tabla/columnas.
- Validacion por motor para algoritmos/modelos (evitar combinaciones invalidas).
- Implementar checks reales de DB en `/health/ready`.
- Exponer endpoint `capabilities`.
- Alinear README backend y docs tecnicas.

DoD:
- `matches/events/chat` funcionando en ambos motores (con datasets de prueba).
- OpenAPI refleja capacidades reales por motor.

### Fase 1 - API de ingestion y jobs
Objetivo: soportar flujo completo de descarga y carga desde backend.

Tareas:
- Crear servicio de jobs con estados (`pending/running/success/error/canceled`).
- Endpoints para descubrir StatsBomb (competiciones y partidos).
- Endpoints para descargar y cargar por destino.
- Endpoint de progreso y logs por job.

DoD:
- Se puede lanzar un job de descarga+carga desde API y monitorear fin a fin.

### Fase 2 - Bootstrap frontend TypeScript
Objetivo: iniciar SPA y sistema visual.

Tareas:
- Crear `frontend/webapp` (Vite + TS + Tailwind).
- Configurar cliente API tipado y manejo global de errores.
- Layout principal, navegacion y guardado de estado UI.

DoD:
- App web levanta en Docker y consume backend.

### Fase 3 - Pantallas operativas core
Objetivo: cubrir flujo de negocio principal solicitado.

Tareas:
- Implementar pantallas: Dashboard, Sources, Catalogo StatsBomb, Descarga, Carga.
- Polling o SSE para estado de jobs.

DoD:
- Usuario puede seleccionar competiciones de StatsBomb y cargar en motor elegido desde UI.

### Fase 4 - Visores funcionales y parity con legacy
Objetivo: recuperar pantallas de analitica y exploracion.

Tareas:
- Implementar vistas: Competitions, Matches, Teams, Players, Events, Tables Info.
- Match viewer por motor con filtros.

DoD:
- Paridad funcional minima con menus clave del `app.py` legacy.

### Fase 5 - Embeddings y Chat avanzado
Objetivo: visibilidad y control de vectorizacion por motor.

Tareas:
- Pantalla de estado embeddings por tabla/modelo.
- Rebuild/manual trigger por match.
- Chat con restricciones dinamicas segun capacidades por motor.

DoD:
- UI informa claramente que motor/modelo/algoritmo esta soportado y en que estado.

### Fase 6 - Hardening, testing y cutover
Objetivo: producir migracion sin regresiones.

Tareas:
- Tests backend (unit + integration) y frontend (component + e2e smoke).
- Observabilidad basica (logs estructurados por job/request).
- Actualizar docker-compose para nuevo frontend web.
- Marcar Streamlit como deprecated.

DoD:
- Nuevo frontend web en produccion local/docker y Streamlit fuera de ruta principal.

## 8) Backlog inicial priorizado
1. Arreglar mismatch SQL Server repo vs schema.
2. Implementar `GET /api/v1/capabilities`.
3. Implementar checks DB en `/health/ready`.
4. Crear modelo de jobs de ingestion.
5. Exponer `statsbomb/competitions` y `statsbomb/matches`.
6. Exponer `ingestion/download` y `ingestion/load`.
7. Crear frontend TS base + autenticidad visual.
8. Implementar pantalla Catalogo StatsBomb.
9. Implementar pantalla Descarga/Carga con progreso.
10. Implementar pantalla Embeddings Status.
11. Implementar visores Teams/Players/Events/Tables Info.
12. Migrar Chat RAG y modo Developer.

## 9) Riesgos y mitigaciones
- Riesgo: deuda legacy de scripts/documentacion.
- Mitigacion: centralizar operacion en API nueva y marcar scripts legacy como "historicos".

- Riesgo: diferencias reales de capacidades entre motores.
- Mitigacion: endpoint `capabilities` y validacion server-side por combinacion.

- Riesgo: jobs largos bloqueando API.
- Mitigacion: ejecutar jobs en background con persistencia de estado y retries.

## 10) Criterios de aceptacion global
- Frontend Streamlit deja de ser la UI principal.
- Frontend web permite:
  - seleccionar competiciones StatsBomb,
  - descargar y cargar por motor,
  - visualizar partidos por motor,
  - ver estado de embeddings por motor.
- Backend ofrece contrato estable y documentado para todo el flujo operativo.
- Documentacion del repo consistente con codigo y scripts reales.
