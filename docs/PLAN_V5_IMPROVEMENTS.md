# Plan de Mejoras v5 — RAG-Challenge

**Fecha:** 2026-04-06
**Estado:** Propuesta
**Rama base:** `develop`

---

## Contexto

Este proyecto nació hace ~2 años como un prototipo RAG sobre datos de fútbol de StatsBomb.
En su origen usaba Azure PostgreSQL con extensiones `azure_ai`/`azure_local_ai` para generar
embeddings en la propia base de datos, y Azure SQL Server con stored procedures para búsquedas
vectoriales. Desde entonces:

- Se migró a pgvector con embeddings generados en la aplicación (ADR-003).
- Se añadió SQL Server 2025 con tipo `VECTOR` nativo.
- Se experimentó con 3 modelos de embedding (ada-002, t3-small, t3-large) y 4 algoritmos de búsqueda.
- Se modernizó la arquitectura a capas (FastAPI + React + DI + Repository Pattern).

Sin embargo, quedan áreas donde la tecnología ha avanzado y el proyecto puede beneficiarse.
Este plan propone mejoras agrupadas en 8 áreas.

---

## Área 1: SQL Server — Índices vectoriales nativos (HNSW)

### Situación actual

- SQL Server 2025 soporta `VECTOR(1536)` y `VECTOR_DISTANCE()` pero el proyecto
  **no crea ningún índice vectorial** — todas las búsquedas son scans secuenciales.
- SQL Server 2025 ya soporta **índices HNSW nativos** (`CREATE VECTOR INDEX ... USING HNSW`),
  pero no se están usando.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Crear índices HNSW en `events_details__15secs_agg` para `embedding_3_small` y `embedding_ada_002` | Alta | Baja |
| Evaluar parámetros `m` y `ef_construction` óptimos para el dataset (~360 vectores/partido) | Media | Media |
| Añadir benchmark comparativo scan vs HNSW en SQL Server | Media | Media |
| Documentar la configuración en `docs/semantic-search.md` | Baja | Baja |

### Ejemplo de implementación

```sql
-- SQL Server 2025 — HNSW nativo
CREATE VECTOR INDEX idx_15secs_t3small_hnsw
ON events_details__15secs_agg (embedding_3_small)
USING HNSW
WITH (METRIC = 'cosine', M = 16, EF_CONSTRUCTION = 64);
```

### Impacto

Con el dataset actual (~360 vectores por partido × N partidos), el beneficio de HNSW será
marginal para búsquedas filtradas por `match_id`, pero **relevante si se busca globalmente**
(cross-match search, buscar jugadas similares en toda la competición).

---

## Área 2: Simplificación de modelos de embedding

### Situación actual

- Se mantienen 3 modelos: `ada-002` (legacy), `t3-small` (default), `t3-large` (solo PostgreSQL).
- `ada-002` es el modelo antiguo de OpenAI, ya reemplazado por la familia `text-embedding-3-*`.
- `t3-large` (3072 dims) solo funciona en PostgreSQL y no aporta mejora significativa en este dominio.
- El esquema tiene columnas separadas por modelo, lo que multiplica almacenamiento e índices.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Deprecar `text-embedding-ada-002` — marcar como legacy, dejar de generar embeddings nuevos | Alta | Baja |
| Evaluar si `t3-large` (3072) aporta valor vs `t3-small` (1536) en este dataset | Media | Media |
| Simplificar esquema: una sola columna de embedding por tabla + columna `embedding_model` | Media | Alta |
| Unificar la dimensión a 1536 como estándar del proyecto | Alta | Baja |
| Eliminar columnas `embedding_ada_002` en migraciones futuras | Baja | Baja |

### Diseño propuesto (esquema simplificado)

```sql
-- En vez de N columnas por modelo, una sola columna + metadatos
ALTER TABLE events_details__quarter_minute
    ADD COLUMN embedding VECTOR(1536),
    ADD COLUMN embedding_model VARCHAR(50) DEFAULT 'text-embedding-3-small';

-- Índice HNSW sobre la columna unificada
CREATE INDEX idx_edqm_embedding_hnsw
ON events_details__quarter_minute USING hnsw (embedding vector_cosine_ops);
```

### Nota

Si en el futuro se quiere soportar modelos con diferentes dimensiones (ej. Cohere 1024,
Mistral 1024), considerar usar `halfvec` de pgvector o normalizar a dimensión fija con
`dimensions` parameter de la API de OpenAI.

---

## Área 3: Qdrant como base de datos vectorial

### Situación actual

- El proyecto usa pgvector (PostgreSQL) y VECTOR nativo (SQL Server) como almacenamiento vectorial.
- En ADR-003 se rechazó Qdrant por "complejidad operativa", pero el contexto ha cambiado:
  - Qdrant tiene Docker image oficial ligera.
  - Ofrece filtrado, payloads, multi-tenancy, y snapshots nativos.
  - Permite desacoplar el almacenamiento vectorial del relacional.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Añadir Qdrant como **tercer backend vectorial** (además de PostgreSQL y SQL Server) | Media | Alta |
| Crear `QdrantEventRepository` implementando la interfaz existente `EventRepository` | Media | Alta |
| Añadir servicio Qdrant al `docker-compose.yml` | Media | Baja |
| Implementar pipeline de sincronización: datos relacionales en PostgreSQL, vectores en Qdrant | Media | Alta |
| Comparar rendimiento: pgvector vs Qdrant vs SQL Server HNSW | Media | Media |
| Documentar trade-offs en un ADR | Baja | Baja |

### Arquitectura propuesta

```
                    ┌──────────────┐
                    │   Frontend   │
                    └──────┬───────┘
                           │
                    ┌──────▼───────┐
                    │   FastAPI    │
                    └──────┬───────┘
                           │
              ┌────────────┼────────────┐
              │            │            │
     ┌────────▼──┐  ┌──────▼───┐  ┌────▼─────┐
     │ PostgreSQL │  │SQL Server│  │  Qdrant  │
     │ (pgvector) │  │ (VECTOR) │  │          │
     └───────────┘  └──────────┘  └──────────┘

     source=postgres  source=sqlserver  source=qdrant
```

### Docker Compose

```yaml
rag-qdrant:
  image: qdrant/qdrant:latest
  ports:
    - "6333:6333"    # REST API
    - "6334:6334"    # gRPC
  volumes:
    - qdrant_data:/qdrant/storage
  mem_limit: 512m
```

### Valor didáctico

Qdrant permite demostrar la diferencia entre **vector DB dedicada** vs **extensión vectorial
en DB relacional**, que es un tema frecuente en arquitecturas RAG actuales.

---

## Área 4: Multi-proveedor de LLM y embeddings

### Situación actual

- `OpenAIAdapter` soporta Azure OpenAI y OpenAI directo (via `OPENAI_PROVIDER`).
- No hay soporte para otros proveedores (OpenRouter, Ollama, Together AI, Mistral, etc.).
- El SDK de OpenAI se usa directamente — no hay abstracción de proveedor.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Crear interfaz `LLMProvider` con métodos `create_embedding()` y `create_chat_completion()` | Alta | Media |
| Implementar `OpenAIProvider` (cubre Azure OpenAI + OpenAI directo) | Alta | Baja |
| Implementar `OpenRouterProvider` (compatible con API OpenAI, cubre 200+ modelos) | Alta | Media |
| Implementar `OllamaProvider` (modelos locales, sin coste API) | Media | Media |
| Configuración multi-proveedor via env vars | Alta | Media |
| Frontend: selector de proveedor en la página de Chat | Media | Media |
| Documentar proveedores soportados y modelos | Baja | Baja |

### Diseño propuesto

```python
# app/adapters/base.py
from abc import ABC, abstractmethod

class LLMProvider(ABC):
    @abstractmethod
    def create_embedding(self, text: str, model: str) -> list[float]: ...

    @abstractmethod
    def create_chat_completion(
        self, messages: list[dict], model: str, temperature: float, max_tokens: int
    ) -> str: ...

# app/adapters/openai_provider.py
class OpenAIProvider(LLMProvider):
    """Azure OpenAI + OpenAI directo."""
    ...

# app/adapters/openrouter_provider.py
class OpenRouterProvider(LLMProvider):
    """OpenRouter — acceso a 200+ modelos via API compatible OpenAI."""
    # Base URL: https://openrouter.ai/api/v1
    ...

# app/adapters/ollama_provider.py
class OllamaProvider(LLMProvider):
    """Ollama — modelos locales (llama3, mistral, nomic-embed-text, etc.)."""
    # Base URL: http://localhost:11434/v1
    ...
```

### Configuración

```env
# Proveedor principal para chat
LLM_PROVIDER=openai          # openai | openrouter | ollama
LLM_API_KEY=sk-...
LLM_BASE_URL=                # opcional, para OpenRouter/Ollama
LLM_MODEL=gpt-4o-mini

# Proveedor de embeddings (puede ser distinto al de chat)
EMBEDDING_PROVIDER=openai    # openai | openrouter | ollama
EMBEDDING_API_KEY=sk-...
EMBEDDING_BASE_URL=
EMBEDDING_MODEL=text-embedding-3-small
```

### Nota sobre OpenRouter

OpenRouter es especialmente interesante porque:
- Compatible con la API de OpenAI (mismo SDK, solo cambia `base_url`).
- Acceso a modelos de Anthropic, Google, Meta, Mistral, etc.
- Pay-per-use sin suscripciones.
- Fallback automático entre proveedores.

### Nota sobre Ollama

Ollama permite ejecutar modelos localmente sin coste de API:
- Embeddings: `nomic-embed-text` (768 dims), `mxbai-embed-large` (1024 dims).
- Chat: `llama3`, `mistral`, `qwen2`, etc.
- API compatible OpenAI (`/v1/chat/completions`, `/v1/embeddings`).
- Requiere ajustar la dimensión de embedding si el modelo no produce 1536.

---

## Área 5: PostgreSQL nativo (sin dependencias Azure)

### Situación actual

- La migración de Azure se completó en ADR-003 — el código ya es portable.
- Docker usa `pgvector/pgvector:pg17` (PostgreSQL nativo).
- **Sin embargo**, la documentación todavía contiene referencias a "Azure PostgreSQL":
  - `docs/app-use-case.md` menciona "Azure SQL", "Azure OpenAI", "Azure PostgreSQL".
  - Variables de entorno son neutras (`POSTGRES_HOST`, etc.) — esto está bien.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Limpiar documentación: eliminar referencias a "Azure PostgreSQL" donde ya no aplica | Alta | Baja |
| Actualizar `docs/app-use-case.md` — eliminar sección legacy de Streamlit/Azure o mover a `docs/archive/` | Media | Baja |
| Verificar que `docker-compose.yml` no tenga dependencias Azure residuales | Baja | Baja |
| Documentar conexión a Azure Database for PostgreSQL como **opción**, no como requisito | Baja | Baja |
| Añadir ejemplo `.env` para conexión a Azure Database for PostgreSQL flexible server | Baja | Baja |

### Estado

Esta área está **mayoritariamente resuelta** — el trabajo principal es limpieza de documentación
y clarificar que Azure es una opción de despliegue, no un requisito.

---

## Área 6: Mejoras en el pipeline de carga/ingestion

### Situación actual

- `IngestionService` tiene acceso directo a la base de datos (no usa Repository Pattern).
- El pipeline es secuencial: download → load → aggregate → embeddings.
- No hay validación de datos ni detección de duplicados.
- Los summaries se generan fuera del pipeline actual (hueco en la cadena).
- El `JobService` es in-memory — se pierden los jobs al reiniciar.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Refactorizar `IngestionService` para usar Repository Pattern (pendiente en PROJECT_STATUS) | Alta | Alta |
| Añadir generación de summaries al pipeline (actualmente es un paso manual/externo) | Alta | Media |
| Implementar detección de duplicados en la carga | Media | Media |
| Añadir validación de datos StatsBomb (schema validation con Pydantic) | Media | Media |
| Persistir estado de jobs en base de datos (no solo in-memory) | Media | Alta |
| Pipeline completo en un solo paso: `POST /ingestion/full-pipeline` | Baja | Media |
| Soporte para ingestion incremental (solo partidos nuevos) | Baja | Media |
| Progress tracking con WebSocket o SSE | Baja | Alta |

### Diseño: generación de summaries

```python
# Paso intermedio entre aggregate y embeddings
async def run_summarize_job(self, match_ids: list[int], source: str):
    """Genera summaries de texto para cada bucket de 15 segundos."""
    rows = self.repo.get_rows_without_summary(match_ids)
    for row in rows:
        summary = self.openai.create_chat_completion(
            messages=[
                {"role": "system", "content": SUMMARIZE_PROMPT},
                {"role": "user", "content": row.json_data},
            ],
            temperature=0.1,
            max_tokens=500,
        )
        self.repo.update_summary(row.id, summary)
```

---

## Área 7: Casos de uso didácticos

### Situación actual

- El proyecto tiene 6 use cases documentados pero orientados a un usuario técnico.
- La documentación mezcla contenido legacy (Streamlit, Azure) con la arquitectura actual.
- No hay guías paso a paso para aprender sobre RAG, embeddings o búsqueda vectorial.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Crear `docs/tutorials/` con guías paso a paso | Alta | Media |
| Tutorial 1: "Tu primera búsqueda semántica" — de pregunta a respuesta | Alta | Media |
| Tutorial 2: "Comparando algoritmos de búsqueda" — cosine vs IP vs L2 | Media | Media |
| Tutorial 3: "Entendiendo embeddings" — visualización de vectores, dimensiones, similitud | Media | Alta |
| Tutorial 4: "Multi-backend" — misma consulta en PostgreSQL, SQL Server y Qdrant | Media | Media |
| Tutorial 5: "Modelos de embedding" — comparativa t3-small vs nomic-embed vs Cohere | Baja | Media |
| Añadir Jupyter notebooks con ejemplos interactivos | Media | Media |
| Crear dataset de preguntas con respuestas esperadas (golden set) para evaluación | Alta | Media |
| Frontend: modo "tutorial" con anotaciones en la UI | Baja | Alta |

### Estructura propuesta

```
docs/tutorials/
├── 01-first-semantic-search.md
├── 02-comparing-search-algorithms.md
├── 03-understanding-embeddings.md
├── 04-multi-backend-comparison.md
├── 05-embedding-models.md
└── notebooks/
    ├── embeddings-visualization.ipynb
    └── search-algorithm-comparison.ipynb
```

### Golden set de evaluación

Crear un archivo `data/golden_set.json` con preguntas, respuestas esperadas y métricas:

```json
[
  {
    "match_id": 3788741,
    "question": "Who scored the first goal?",
    "expected_answer_contains": ["Morata", "goal", "first half"],
    "expected_top_result_period": 1,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine"
  }
]
```

---

## Área 8: Setup automático y seed data

### Situación actual

- El pipeline de ingestion requiere 4 pasos manuales secuenciales: download → load → aggregate → embeddings.
- La generación de summaries y embeddings consume tokens de API (coste real por cada setup).
- No existe un comando "one-click" para levantar el sistema con datos funcionales.
- Los datos de StatsBomb se descargan cada vez desde GitHub (no hay datos pre-empaquetados).
- Un nuevo desarrollador no puede probar el RAG sin ejecutar todo el pipeline y tener una API key.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Crear dataset seed pre-generado con summaries y embeddings incluidos | Alta | Media |
| Seleccionar partidos representativos como seed data | Alta | Baja |
| Script `make seed-load` que carga el seed en PostgreSQL y/o SQL Server | Alta | Media |
| Endpoint `POST /ingestion/full-pipeline` que ejecuta download → load → aggregate → summarize → embeddings en un solo paso | Media | Alta |
| Documentar el proceso completo de setup en `docs/getting-started.md` | Media | Baja |
| Añadir seed data como fixtures del repositorio (versionado en git) | Media | Media |
| Soporte para selección de DB destino en el setup automático | Media | Media |

### Partidos propuestos como seed data

| Partido | Competición | match_id | Motivo |
|---------|-------------|----------|--------|
| España 2-1 Inglaterra | UEFA Euro 2024 Final | `3943043` | Ya tiene summaries generados en `data/scripts_summary/` |
| Argentina 3-3 Francia (pen. 4-2) | FIFA World Cup 2022 Final | Por confirmar en StatsBomb | Partido icónico, máxima complejidad (prórroga + penaltis) |

### Estructura del seed data

```
data/seed/
├── README.md                          # Qué contiene, cómo se generó
├── matches/
│   ├── 3943043.json                   # España-Inglaterra (raw StatsBomb)
│   └── XXXXXXX.json                   # Argentina-Francia (raw StatsBomb)
├── events/
│   ├── 3943043.json
│   └── XXXXXXX.json
├── lineups/
│   ├── 3943043.json
│   └── XXXXXXX.json
├── summaries/                         # Summaries pre-generados (evita coste LLM)
│   ├── 3943043_quarter_minute.json
│   └── XXXXXXX_quarter_minute.json
└── embeddings/                        # Embeddings pre-generados (evita coste API)
    ├── 3943043_t3_small_1536.json     # text-embedding-3-small (1536 dims)
    └── XXXXXXX_t3_small_1536.json
```

### Pipeline de setup automático

```
┌─────────────────────────────────────────────────────────────┐
│  make seed-load  (o POST /ingestion/seed)                   │
│                                                             │
│  1. Lee data/seed/matches/*.json → INSERT matches           │
│  2. Lee data/seed/events/*.json  → INSERT events            │
│  3. Lee data/seed/lineups/*.json → INSERT lineups           │
│  4. Agrega en buckets 15s → INSERT aggregation table        │
│  5. Lee data/seed/summaries/*.json → UPDATE summary         │
│  6. Lee data/seed/embeddings/*.json → UPDATE embeddings     │
│                                                             │
│  ✅ Sin llamadas a API — todo pre-generado                  │
│  ✅ Funciona sin OPENAI_KEY                                 │
│  ✅ < 30 segundos en Docker local                           │
└─────────────────────────────────────────────────────────────┘
```

### Pipeline completo (con API)

Para usuarios que quieran regenerar datos o ingerir nuevos partidos:

```
POST /ingestion/full-pipeline
{
  "competition_id": 55,
  "season_id": 282,
  "match_ids": [3943043],
  "source": "postgres",
  "embedding_models": ["text-embedding-3-small"]
}

→ download → load → aggregate → summarize → generate embeddings
→ Progress via GET /ingestion/jobs/{job_id}
```

### Consideraciones de tamaño

- Raw events JSON por partido: ~2-5 MB
- Summaries por partido: ~100-200 KB (360 buckets × ~500 chars)
- Embeddings por partido (1536 dims × 360 buckets): ~2-4 MB (JSON con floats)
- **Total seed para 2 partidos: ~15-20 MB** — aceptable para git

### Valor

- **Onboarding en < 5 min**: `docker compose up && make seed-load` → sistema funcional.
- **Sin coste de API**: El seed evita que cada nuevo desarrollador gaste tokens.
- **Tests de integración**: El seed sirve como fixture para tests con DB real.
- **Demos**: Siempre hay datos disponibles para demostraciones.

---

## Área 9: Mejoras técnicas transversales

### Propuesta

| Tarea | Prioridad | Complejidad | Descripción |
|-------|-----------|-------------|-------------|
| Integration tests | Alta | Alta | `backend/tests/integration/` — tests con DB real via Docker |
| Frontend tests | Media | Media | Vitest + Testing Library para componentes React |
| Structured logging | Media | Media | request_id, match_id, latency, token_usage en JSON |
| Query caching | Media | Media | Cache de embeddings de queries frecuentes (Redis o in-memory) |
| CD pipeline | Media | Alta | Deploy automático (al menos a staging) |
| Endpoint de evaluación | Baja | Media | `POST /api/v1/evaluate` con golden set |
| Métricas de búsqueda | Baja | Media | Precision@k, recall@k, latencia por algoritmo |
| API versioning | Baja | Baja | Preparar para v2 sin romper v1 |

---

## Área 10: Gobernanza de issues con OpenSpec

### Situación actual

- Las mejoras y bugs se gestionan de forma informal o en conversaciones.
- No hay un flujo definido para que participantes tomen issues y las resuelvan.
- OpenSpec se usa para spec-driven development, pero no cubre el ciclo de issues.

### Propuesta

| Tarea | Prioridad | Complejidad |
|-------|-----------|-------------|
| Definir flujo de issues en `openspec/specs/governance/spec.md` | Alta | Media |
| Crear labels estándar en GitHub Issues alineadas con OpenSpec | Alta | Baja |
| Documentar proceso de asignación y resolución en `CONTRIBUTING.md` | Alta | Media |
| Template de issue con campos OpenSpec (spec asociada, change requerido) | Media | Baja |
| Integrar issues con el ciclo `/opsx:propose` → `/opsx:apply` → `/opsx:archive` | Media | Media |

### Flujo propuesto

```
┌─────────────────────────────────────────────────────────────┐
│                  Ciclo de vida de un Issue                   │
│                                                             │
│  1. CREAR ISSUE                                             │
│     - Cualquier participante crea issue en GitHub           │
│     - Labels: área (backend/frontend/infra), tipo           │
│       (bug/feature/chore), prioridad (P0/P1/P2)            │
│     - Si requiere diseño → label "needs-spec"               │
│                                                             │
│  2. TRIAGE                                                  │
│     - Revisar si existe spec relacionada en openspec/specs/ │
│     - Si no existe y es feature → /opsx:propose primero     │
│     - Asignar prioridad y estimación de complejidad         │
│                                                             │
│  3. ASIGNACIÓN                                              │
│     - Participante se auto-asigna (o se le asigna)          │
│     - Crea rama: feature/NNN-desc o fix/NNN-desc            │
│     - Si tiene spec → /opsx:apply para implementar          │
│                                                             │
│  4. RESOLUCIÓN                                              │
│     - PR contra develop (siguiendo git-workflow)             │
│     - Tests pasan, coverage ≥ 80%                           │
│     - CHANGELOG actualizado                                 │
│                                                             │
│  5. CIERRE                                                  │
│     - PR mergeado → issue se cierra automáticamente         │
│     - Si tenía spec → /opsx:archive                         │
│     - Si el issue generó una decisión → actualizar spec     │
└─────────────────────────────────────────────────────────────┘
```

### Labels propuestas

| Label | Color | Descripción |
|-------|-------|-------------|
| `area:backend` | azul | Cambios en backend Python/FastAPI |
| `area:frontend` | verde | Cambios en frontend React/TS |
| `area:infra` | gris | Docker, CI/CD, scripts |
| `area:docs` | amarillo | Documentación, tutoriales |
| `type:bug` | rojo | Corrección de error |
| `type:feature` | morado | Nueva funcionalidad |
| `type:chore` | naranja | Mantenimiento, refactor |
| `priority:P0` | rojo oscuro | Crítico — bloquea desarrollo |
| `priority:P1` | naranja | Importante — resolver en la fase actual |
| `priority:P2` | amarillo | Deseable — backlog |
| `needs-spec` | blanco | Requiere propuesta OpenSpec antes de implementar |
| `good-first-issue` | verde claro | Ideal para nuevos participantes |

### Relación con OpenSpec

```
GitHub Issue (problema/necesidad)
    │
    ├─ Simple (bug, chore) → rama + PR directo
    │
    └─ Complejo (feature, rediseño) → /opsx:propose
         │
         ├─ openspec/changes/<name>/proposal.md
         ├─ openspec/changes/<name>/design.md
         ├─ openspec/changes/<name>/tasks.md
         │
         └─ /opsx:apply → implementar → PR → merge
              │
              └─ /opsx:archive → mover a archive/
```

### Valor

- **Orden**: Los participantes saben qué hacer y cómo empezar.
- **Trazabilidad**: Cada cambio de código está vinculado a un issue.
- **Onboarding**: Nuevos participantes buscan `good-first-issue` y siguen el flujo.
- **Didáctico**: El propio proceso enseña spec-driven development.

---

## Priorización recomendada

### Fase 0 — Fundamentos (1 semana)

1. Setup automático con seed data (Área 8) — onboarding inmediato
2. Gobernanza de issues con OpenSpec (Área 10) — preparar para colaboración
3. Limpiar documentación legacy Azure (Área 5)

### Fase 1 — Quick wins (1-2 semanas)

4. Crear índices HNSW en SQL Server (Área 1)
5. Deprecar `ada-002`, estandarizar en `t3-small` 1536 dims (Área 2)
6. Crear golden set de evaluación (Área 7)

### Fase 2 — Multi-proveedor (2-3 semanas)

7. Interfaz `LLMProvider` + implementación OpenAI/OpenRouter (Área 4)
8. Soporte Ollama para desarrollo local sin coste (Área 4)
9. Frontend: selector de proveedor (Área 4)

### Fase 3 — Ingestion & calidad (2-3 semanas)

10. Refactorizar `IngestionService` con Repository Pattern (Área 6)
11. Generación de summaries en el pipeline (Área 6)
12. Integration tests con Docker (Área 9)

### Fase 4 — Qdrant & didáctica (3-4 semanas)

13. Añadir Qdrant como tercer backend (Área 3)
14. Tutoriales paso a paso (Área 7)
15. Notebooks interactivos (Área 7)
16. Simplificación de esquema (columna única de embedding) (Área 2)

---

## Decisiones abiertas

| # | Decisión | Opciones | Recomendación |
|---|----------|----------|---------------|
| D1 | ¿Eliminar `ada-002` completamente o mantener como legacy read-only? | Eliminar / Legacy | Legacy en fase 1, eliminar en fase 4 |
| D2 | ¿Qdrant como opción adicional o reemplazo de pgvector? | Adicional / Reemplazo | Adicional — mantener los 3 backends |
| D3 | ¿OpenRouter o LiteLLM como capa de abstracción? | OpenRouter / LiteLLM | OpenRouter primero (más simple), LiteLLM si se necesita más |
| D4 | ¿Esquema unificado (1 columna embedding) o mantener multi-columna? | Unificado / Multi | Unificado a medio plazo (fase 4) |
| D5 | ¿Notebooks en el repo o en un repo separado? | Mismo repo / Separado | Mismo repo en `docs/tutorials/notebooks/` |
| D6 | ¿Seed data en git (LFS?) o descargable desde release? | Git / Git LFS / Release asset | Git directo si < 50 MB; Git LFS si crece |
| D7 | ¿Issues solo en GitHub o también en Linear/Jira? | GitHub / Externo | GitHub Issues — mantener todo en un sitio |

---

## Referencias

| Recurso | URL |
|---------|-----|
| SQL Server 2025 vector indexes | https://learn.microsoft.com/en-us/sql/relational-databases/vectors/vectors-sql-server |
| Qdrant documentation | https://qdrant.tech/documentation/ |
| OpenRouter API docs | https://openrouter.ai/docs |
| Ollama API docs | https://github.com/ollama/ollama/blob/main/docs/openai.md |
| pgvector HNSW tuning | https://github.com/pgvector/pgvector#hnsw |
| OpenAI embedding models | https://platform.openai.com/docs/guides/embeddings |
| LiteLLM (alternativa) | https://github.com/BerriAI/litellm |
