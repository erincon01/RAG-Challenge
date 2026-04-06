# Conversation Log — RAG-Challenge

Registro cronológico de sesiones de trabajo asistidas por IA.
Cada sesión significativa con un agente AI se documenta aquí para auditoría y trazabilidad.

> **NOTE — Governance pivot (2026-04-02):**
> Sessions 1–12 document the spec-kit adoption journey on the `develop` branch.
> Starting from Session 13 (OpenSpec), work moved to `feature/openspec-governance`,
> adopting OpenSpec as the spec-driven governance framework.
> The spec-kit governance is preserved in `feature/spec-kit-governance` for reference.

---

## Fase OpenSpec changes (Sessions 18+, branch: develop)

---

### [2026-04-06] Session 18 — CORS hardening (fix/016-cors-hardening)

**Participants:** Eladio Rincon + Claude Code (Claude Opus 4.6)
**Branch:** fix/016-cors-hardening

#### Decisions taken
- Replace `allow_origins=["*"]` with configurable `CORS_ORIGINS` env var
- Store as `cors_origins_str` (string field) with a `cors_origins` property that splits on commas — avoids pydantic-settings JSON parse issue with `List[str]`
- API test for CORS middleware uses a dedicated mini FastAPI app instead of patching the real app (middleware is configured at import time)
- Cleaned up unused imports (`os`, `Optional`) in `config/settings.py`

#### Files modified
- `config/settings.py` — added `cors_origins_str` field + `cors_origins` property
- `backend/app/main.py` — replaced `allow_origins=["*"]` with `settings.cors_origins`
- `.env.example`, `.env.docker.example` — added `CORS_ORIGINS`
- `backend/tests/unit/test_cors_config.py` — 3 unit tests for Settings parsing
- `backend/tests/api/test_cors_middleware.py` — 2 API tests for middleware allow/reject
- `openspec/changes/cors-hardening/` — full OpenSpec change (proposal, design, specs, tasks)
- `CHANGELOG.md` — added Security entry

---

## Fase spec-kit (Sessions 1-12, branch: develop)

---

### [2026-04-02] Session 1 — spec-kit adoption plan

**User asked:** Incorporate spec-kit into this brownfield project (RAG-Challenge) to accelerate and organize development. Requested a plan before executing. Referenced the `mnriem/spec-kit-aspnet-brownfield-demo` as the reference pattern.

**Decision:** Researched the spec-kit repo and brownfield demo. Confirmed that the latest stable tag is `v0.4.4`. Produced a full step-by-step plan covering installation, initialization, constitution generation, and repeatable feature workflow.

**Artifacts created/modified:**
- `docs/spec-kit-migration-plan.md` — full migration plan

---

### [2026-04-02] Session 2 — governance: TDD, CI/CD, git norms, Copilot instructions

**User asked:** Before adopting spec-kit, establish all CI/CD practices, code editing rules, validations, git norms. Create Copilot instructions.

**Decision:** Created a full governance layer using VS Code Copilot instruction files in `.github/`.

**Artifacts created/modified:**
- `.github/copilot-instructions.md` — workspace baseline
- `.github/instructions/tdd.instructions.md` — TDD cycle, pytest, mocks
- `.github/instructions/python-modules.instructions.md` — module conventions
- `.github/instructions/git-workflow.instructions.md` — branch naming, commits, PR checklist
- `.github/instructions/sql-embeddings.instructions.md` — pgvector, SQL safety

---

### [2026-04-02] Session 3 — CHANGELOG and conversation_log mandatory rules

**User asked:** Add CHANGELOG.md and conversation_log.md as mandatory project artifacts.

**Decision:** Both follow strict governance rules: CHANGELOG uses Keep a Changelog format; conversation_log is append-only.

**Artifacts created/modified:**
- `CHANGELOG.md`, `docs/conversation_log.md`, `.github/copilot-instructions.md`

---

### [2026-04-02] Session 4 — Coverage: spec-kit vs PRD, ADR, TechStack

**Decision:** ADR structure created in `docs/adr/`. spec-kit covers user stories and requirements but not formal PRDs or standalone ADRs.

---

### [2026-04-02] Session 5 — Branching strategy, CI/CD, test infrastructure

**Decision:** Simplified GitFlow: `main` (production) + `develop` (staging/integration). CI/CD workflows created. PR template added. Test infrastructure bootstrapped.

---

### [2026-04-02] Session 6 — Lint baseline, pyproject.toml, 3-level test strategy

**Decision:** Fixed 96 ruff lint errors, created `pyproject.toml`, implemented 3-level test pyramid.

---

### [2026-04-02] Session 7 — Documentation: architecture, tech stack, use cases

**Decision:** Created 3 new docs, fixed 14 broken links, aligned flake8/ruff.

---

### [2026-04-02] Session 8 — spec-kit FASE 0+1+2: installation, initialization, constitution

**Decision:** Executed `specify init` and `/speckit.constitution`. Constitution v1.0.0 generated with 8 principles.

---

### [2026-04-02] Session 9 — Pivot: governance adaptation to FastAPI/React architecture

**Decision:** `develop` (FastAPI/React) is the active production line. All governance adapted from Streamlit to FastAPI architecture. Streamlit governance preserved in `feature/spec-kit-streamlit-app`.

---

### [2026-04-02] Session 10 — Medium article: brownfield-to-spec-kit journey

**Artifacts:** `docs/articles/brownfield-to-speckit-adoption.md`

---

### [2026-04-02] Session 11 — Spec-kit readiness audit and phased adoption plan

**Decision:** 16 deficiencies identified across 3 severity levels. 4-phase adoption plan created.

**Artifacts:** `docs/spec-kit-adoption-plan.md`

---

### [2026-04-02] Session 12 — Execute spec-kit adoption plan (Phases 0-1)

**Decision:** Resolved deficiencies D-01 through D-15. Created `CLAUDE.md`, `specs/README.md`, bash scripts, PR template constitution check.

---

## Fase OpenSpec (Sessions 13+, branch: feature/openspec-governance)

---

### [2026-04-02] Session 13 — Adopción de OpenSpec: preparación del terreno

**Participantes:** Eladio Rincon + GitHub Copilot (Claude Opus 4.6)
**Rama:** `feature/openspec-governance`

### Objetivo
Crear la rama de gobernanza OpenSpec partiendo del estado pre-spec-kit del proyecto,
y generar todos los artefactos manuales necesarios para la adopción.

### Decisiones tomadas
1. Crear la rama desde el commit `c3be08c` (20-Feb-2026) — último commit antes de cualquier
   intento de gobernanza.
2. Traer selectivamente solo `.github/workflows/ci.yml` y `cd.yml` desde `develop`.
3. Adoptar OpenSpec (Fission-AI, v1.2.0) como framework de gobernanza spec-driven en lugar
   de alternativas más rígidas.
4. Crear artefactos manuales de Copilot (instrucciones, agent, TDD, git workflow) que
   complementan los que OpenSpec genera automáticamente (skills, slash commands).
5. Documentar el proceso paso a paso para que la comunidad pueda replicarlo.

### Artefactos creados
- `docs/PLAN_OPENSPEC_ADOPTION.md` — Plan completo con fases, esfuerzo, beneficio
- `.github/copilot-instructions.md` — Instrucciones globales de Copilot
- `.github/instructions/git-workflow.instructions.md` — Reglas de ramas y commits
- `.github/instructions/tdd.instructions.md` — Reglas de TDD
- `AGENTS.md` — Definición del agente de desarrollo

---

### [2026-04-02] Session 14 — Instalación de OpenSpec y soporte multi-herramienta

**Participantes:** Eladio Rincon + GitHub Copilot (Claude Opus 4.6)
**Rama:** `feature/openspec-governance`

### Objetivo
Instalar OpenSpec CLI, inicializar el proyecto para GitHub Copilot y Claude Code,
crear `CLAUDE.md` para soporte multi-agente, y configurar `openspec/config.yaml`.

### Decisiones tomadas
1. `CLAUDE.md` como fichero fino que referencia `AGENTS.md` como fuente de verdad única.
2. OpenSpec v1.2.0 con perfil `core` (propose, explore, apply, archive).
3. `openspec/config.yaml` creado manualmente con contexto del proyecto.

### Artefactos generados
- `CLAUDE.md`, `openspec/config.yaml`
- `.github/prompts/opsx-{propose,apply,archive,explore}.prompt.md`
- `.github/skills/openspec-{propose,apply-change,archive-change,explore}/SKILL.md`
- `.claude/commands/opsx/{propose,apply,archive,explore}.md`
- `.claude/skills/openspec-{propose,apply-change,archive-change,explore}/SKILL.md`

---

### [2026-04-02] Session 15 — Documentación del sistema actual como specs

**Participantes:** Eladio Rincon + GitHub Copilot (Claude Opus 4.6)
**Rama:** `feature/openspec-governance`

### Artefactos creados
- `openspec/specs/api/spec.md` — 10 routers, ~25 endpoints
- `openspec/specs/rag/spec.md` — Pipeline RAG de 5 pasos
- `openspec/specs/data/spec.md` — 14 entities, 5 exceptions
- `openspec/specs/infra/spec.md` — Docker Compose, config, DI, CI/CD

---

### [2026-04-02] Session 16 — Fase 3: primer cambio real (fix-dependency-injection)

**Participantes:** Eladio Rincon + GitHub Copilot (Claude Sonnet 4.6)
**Rama:** `feature/openspec-governance`

### Secuencia seguida (TDD estricto)

1. **Propuesta** — `/opsx:propose fix-dependency-injection` → 4 artefactos creados
2. **Violación detectada y corregida**: se implementó código antes que tests. Revertido.
3. **Fase RED** — 18 tests escritos (ImportError: cannot import providers)
4. **Fase GREEN** — providers creados, rutas migradas a `Depends()`, tests legacy actualizados
5. **Resultado**: 433 tests passing
6. **Archivo**: `openspec archive fix-dependency-injection`

### Archivos modificados
- `backend/app/core/dependencies.py` — 3 new providers + type aliases
- `backend/app/api/v1/{statsbomb,ingestion,embeddings,explorer}.py` — DI migration
- `backend/tests/api/{test_statsbomb,test_ingestion,test_explorer_embeddings}.py`
- `backend/tests/unit/test_dependencies_and_explorer_service.py`

---

### [2026-04-06] Session 17 — Merge develop into openspec-governance

**Participantes:** Eladio Rincon + Claude Opus 4.6
**Rama:** `feature/openspec-governance`

### Objetivo
Consolidar `feature/openspec-governance` con los cambios de `develop` para preparar
PR hacia develop. Resolve 13 merge conflicts.

### Decisiones tomadas
1. Mantener versión OpenSpec de todos los archivos de governance (copilot-instructions,
   git-workflow, tdd, CLAUDE.md, AGENTS.md) — reemplaza spec-kit
2. Mantener versión DI (`Depends()`) de todos los archivos de backend — reemplaza `_service` singletons
3. Mantener versión DI de todos los tests — `dependency_overrides` en lugar de `patch("..._service")`
4. Incorporar fix de ruff de develop: `dict` en lugar de `Dict` (builtin generics)
5. Combinar conversation_log: historial spec-kit (sessions 1-12) + OpenSpec (sessions 13+)
6. Eliminar artefactos spec-kit que ya no aplican (`.specify/`, `.flake8`, `pyproject.toml`,
   `specs/README.md`, agents/prompts/skills de speckit)

### Archivos conflictuados y resolución
- `.github/copilot-instructions.md` → OpenSpec version
- `.github/instructions/git-workflow.instructions.md` → OpenSpec version
- `.github/instructions/tdd.instructions.md` → OpenSpec version
- `.markdownlint.json` → merged (MD033: false from openspec)
- `CLAUDE.md` → OpenSpec version (thin wrapper → AGENTS.md)
- `backend/app/api/v1/{embeddings,explorer,statsbomb}.py` → DI + builtin dict
- `backend/tests/api/{test_explorer_embeddings,test_ingestion,test_statsbomb}.py` → DI overrides
- `backend/tests/unit/test_dependencies_and_explorer_service.py` → with DI provider tests
- `docs/conversation_log.md` → combined history
