# Plan de Adopcion de Spec-Kit: RAG-Challenge

**Fecha**: 2026-04-02
**Branch**: `feature/spec-kit-governance`
**Estado del proyecto**: Brownfield — 97% funcional, gobernanza parcial
**Version spec-kit detectada**: v0.4.4 (inicializado)
**Version constitution**: 2.0.0

---

## Resumen Ejecutivo

El proyecto RAG-Challenge tiene una base solida para adoptar spec-kit: arquitectura por capas, tests backend (259), constitution v2.0.0, templates, agentes y scripts PowerShell. Sin embargo, hay **deficiencias criticas** que impiden usar el flujo SDD completo (`specify → clarify → plan → tasks → implement → analyze`). Este plan las identifica y propone un camino faseado para resolverlas.

---

## Diagnostico: Estado Actual vs Expectativas de Spec-Kit

### Lo que YA esta bien (no tocar)

| Area | Estado | Evidencia |
|------|--------|-----------|
| Constitution v2.0.0 | Solida, 10 principios, versionada | `.specify/memory/constitution.md` |
| Templates core | 6 templates personalizados | `.specify/templates/` |
| Agentes spec-kit | 9 agentes definidos | `.github/agents/speckit.*.agent.md` |
| Prompts cognitive layer | 9 prompts (stubs funcionales) | `.github/prompts/speckit.*.prompt.md` |
| Scripts PowerShell | 5 scripts de automatizacion | `.specify/scripts/powershell/` |
| Arquitectura backend | 6 capas, DI, Repository Pattern | `backend/app/` |
| Tests backend | 259 tests locales (unit + api) | `backend/tests/` |
| Pre-commit hooks | ruff + mypy + hygiene | `.pre-commit-config.yaml` |
| CI workflow | lint + typecheck + tests + coverage 80% | `.github/workflows/ci.yml` |
| ADRs | 4 ADRs aceptados e implementados | `docs/adr/` |
| Docker infrastructure | Compose completo, healthchecks, devcontainer v2 | `docker-compose.yml` |
| Copilot instructions | Global + 4 domain-specific | `.github/copilot-instructions.md` + `instructions/` |
| CHANGELOG | Keep a Changelog format, actualizado | `CHANGELOG.md` |

### Deficiencias Detectadas

#### CRITICAS (bloquean el uso de spec-kit)

| # | Deficiencia | Impacto | Ubicacion |
|---|------------|---------|-----------|
| D-01 | **No existe directorio `specs/`** | Sin directorio de features, los agentes no tienen donde leer/escribir spec.md, plan.md, tasks.md. El flujo SDD completo es imposible. | Raiz del proyecto |
| D-02 | **No existe `CLAUDE.md`** | Claude Code no tiene instrucciones de proyecto persistentes. Cada conversacion parte de cero sin contexto. Los agentes spec-kit que corren en Claude Code no heredan las normas del proyecto. | Raiz del proyecto |
| D-03 | **Referencia rota en copilot-instructions.md** | Linea "See docs/spec-kit-migration-plan.md" apunta a un archivo que NO existe. Link muerto en el archivo de gobernanza principal. | `.github/copilot-instructions.md` |
| D-04 | ~~Tests backend sin commit/push/merge~~ | **RESUELTO** — Mergeado a develop via PR #8 (commit `15cbb74`). CI funcional con lint + typecheck + tests + coverage 80%. | `develop` (PR #8) |
| D-05 | **No hay tests de frontend** | Cero tests en React/TypeScript. La constitution (Principio VI) exige TDD pero solo se aplica al backend. spec-kit generara codigo frontend sin red de seguridad. | `frontend/webapp/` |

#### IMPORTANTES (degradan la calidad del flujo SDD)

| # | Deficiencia | Impacto | Ubicacion |
|---|------------|---------|-----------|
| D-06 | **No hay scripts bash para spec-kit** | Solo existen scripts PowerShell. El devcontainer corre Linux; CI corre Ubuntu. Los scripts de spec-kit (check-prerequisites, create-new-feature) no funcionan en esos entornos. | `.specify/scripts/` |
| D-07 | ~~CI no valida adherencia a constitution~~ | **RESUELTO** — Constitution Check section anadida al PR template (`.github/pull_request_template.md`). Los 10 principios son checkboxes obligatorios. | `.github/pull_request_template.md` |
| D-08 | **CD es un placeholder vacio** | `cd.yml` tiene jobs de staging y production pero con `echo "Deploy..."`. No hay deploy real. | `.github/workflows/cd.yml` |
| D-09 | **Deuda tecnica documentada pero no rastreada** | Los 3 TODOs del Brownfield Debt Register (CORS_PRODUCTION, SINGLETON_ADAPTER, CONNECTION_POOLING) estan en la constitution pero no tienen issues en GitHub. | Constitution, seccion "Brownfield Debt Register" |
| D-10 | **MyPy en modo permisivo** | `strict = false` en pyproject.toml. El Principio VI exige type safety pero mypy no la enforce realmente. Codigo generado por spec-kit podria pasar sin types. | `pyproject.toml` |
| D-11 | **`PROJECT_STATUS.md` desactualizado** | Dice "CI/CD not started" pero `ci.yml` ya existe. Dice "last reviewed 2026-02-20" pero estamos en abril. Genera confusion sobre el estado real. | `PROJECT_STATUS.md` |
| D-12 | **Documentacion legacy sin migrar** | `docs/app-use-case.md` aun documenta el workflow Streamlit/Azure. `docs/app-screenshots.md` solo tiene screenshots del Streamlit legacy. | `docs/` |

#### MENORES (nice-to-have para adopcion completa)

| # | Deficiencia | Impacto | Ubicacion |
|---|------------|---------|-----------|
| D-13 | **No hay task runner** | Sin Taskfile.yml, justfile o Makefile. Los comandos de dev estan dispersos en READMEs. spec-kit no lo requiere pero simplificaria el onboarding. | Raiz del proyecto |
| D-14 | **Sin presets organizativos** | No hay `.specify/presets/` para compartir convenciones entre equipos. Solo relevante si hay multiples repositorios. | `.specify/` |
| D-15 | **Constitution no tiene `RATIFICATION_DATE` en frontmatter YAML** | spec-kit espera metadata YAML al inicio; la constitution usa HTML comments. Funcional pero no idiomatico. | `.specify/memory/constitution.md` |
| D-16 | **Frontend types no auto-generados** | `frontend/webapp/src/lib/api/types.ts` se mantiene manualmente. Deberia generarse desde OpenAPI schema para garantizar el Principio IX (Frontend Contract). | `frontend/webapp/src/lib/api/types.ts` |

---

## Plan Faseado de Adopcion

### Fase 0: Prerequisitos Criticos (bloquean todo lo demas)

**Prioridad**: P0 — INMEDIATA
**Esfuerzo estimado**: 1-2 dias
**Resuelve**: D-01, D-02, D-03
**Nota**: D-04 ya resuelto — tests mergeados a develop via PR #8

#### 0.1 Crear directorio `specs/`

```
specs/
└── README.md    # Explica el flujo SDD y como crear una nueva feature
```

El README debe documentar:
- Que es el directorio `specs/` y su relacion con spec-kit
- Como crear una feature nueva: `create-new-feature.ps1` o manual
- Estructura esperada por feature (`spec.md`, `plan.md`, `tasks.md`, `checklist.md`)
- Convencion de nombrado: `NNN-nombre-feature/` (e.g., `001-structured-logging/`)
- Que los specs se commitean **antes** que el codigo

#### 0.2 Crear `CLAUDE.md`

Crear un `CLAUDE.md` en la raiz del proyecto que Claude Code cargue automaticamente. Debe incluir:

- Resumen del proyecto (1 parrafo)
- Stack tecnologico
- Referencia a la constitution: `.specify/memory/constitution.md`
- Comandos esenciales: como correr tests, lint, format, docker
- Referencia a `.github/copilot-instructions.md` para normas detalladas
- Referencia a `specs/` como directorio de features SDD
- Convencion de commits (conventional commits)
- Regla: no commitear `.env`, credenciales, `__pycache__`
- Regla: CHANGELOG obligatorio en cada PR

**No duplicar** lo que ya esta en la constitution o copilot-instructions. Solo apuntar.

#### 0.3 Corregir referencia rota en copilot-instructions.md

Linea actual:
```
See [docs/spec-kit-migration-plan.md](docs/spec-kit-migration-plan.md) for the full SDD workflow with spec-kit.
```

Cambiar a:
```
See [docs/spec-kit-adoption-plan.md](docs/spec-kit-adoption-plan.md) for the full SDD adoption plan with spec-kit.
```

#### 0.4 ~~Promover test suite al remoto~~ — COMPLETADO

Test suite ya mergeada a `develop` via PR #8 (commit `15cbb74`). CI funcional.

---

### Fase 1: Completar la Infraestructura SDD

**Prioridad**: P1 — ALTA
**Esfuerzo estimado**: 2-3 dias
**Resuelve**: D-06, D-07, D-09, D-15

#### 1.1 Crear scripts bash equivalentes

Crear `.specify/scripts/bash/` con equivalentes de:

| PowerShell | Bash equivalente |
|-----------|-----------------|
| `check-prerequisites.ps1` | `check-prerequisites.sh` |
| `create-new-feature.ps1` | `create-new-feature.sh` |
| `setup-plan.ps1` | `setup-plan.sh` |
| `update-agent-context.ps1` | `update-agent-context.sh` |
| `common.ps1` | `common.sh` |

Estos scripts se ejecutan en:
- Devcontainer (Linux)
- GitHub Actions CI (Ubuntu)
- Cualquier maquina Mac/Linux del equipo

**Priorizar `check-prerequisites.sh` y `create-new-feature.sh`** — son los mas usados en el flujo diario.

#### 1.2 Anadir Constitution Check gate en CI

Anadir un job en `ci.yml` que verifique en PRs:
- Que el cuerpo del PR contiene una seccion "Constitution Check" (o equivalente)
- Alternativa: un script que parsee `plan.md` en la feature branch y verifique los 10 gates

Implementacion minima viable:
```yaml
  constitution-check:
    name: Constitution Check
    runs-on: ubuntu-latest
    if: github.event_name == 'pull_request'
    steps:
      - uses: actions/checkout@v4
      - name: Verify PR body contains Constitution Check
        run: |
          PR_BODY=$(gh pr view ${{ github.event.pull_request.number }} --json body -q '.body')
          if ! echo "$PR_BODY" | grep -qi "constitution check"; then
            echo "::error::PR body must contain a 'Constitution Check' section"
            exit 1
          fi
        env:
          GH_TOKEN: ${{ secrets.GITHUB_TOKEN }}
```

#### 1.3 Crear GitHub Issues para deuda tecnica

Crear issues para los 3 TODOs del Brownfield Debt Register:

1. **Issue: Restrict CORS origins before production** — `TODO(CORS_PRODUCTION)`
   - Labels: `security`, `tech-debt`, `P2`
2. **Issue: OpenAI adapter singleton pattern** — `TODO(SINGLETON_ADAPTER)`
   - Labels: `performance`, `tech-debt`, `P3`
3. **Issue: Connection pooling for PostgreSQL** — `TODO(CONNECTION_POOLING)`
   - Labels: `performance`, `tech-debt`, `P3`

Esto los hace visibles y trackeables fuera de la constitution.

#### 1.4 Anadir frontmatter YAML a la constitution (opcional)

Actualmente la constitution usa HTML comments para metadata. spec-kit recomienda frontmatter YAML:

```yaml
---
constitution_version: "2.0.0"
ratification_date: "2025-01-01"
last_amended_date: "2026-04-02"
amendment_procedure: "See Governance section"
---
```

Esto es un PATCH en el versionado de la constitution (solo formato, no contenido).

---

### Fase 2: Primera Feature con Flujo SDD Completo

**Prioridad**: P1 — ALTA
**Esfuerzo estimado**: 1-2 dias
**Resuelve**: Validacion end-to-end del workflow
**Prerequisito**: Fases 0 y 1 completadas

#### 2.1 Elegir una feature pequena y real

Candidatas del backlog actual (de `PROJECT_STATUS.md`):

| Feature | Complejidad | Valor para validar SDD |
|---------|-------------|----------------------|
| **Structured logging** (request_id, match_id) | Media | Toca backend (services + api), cross-cutting |
| **Task runner** (Taskfile.yml) | Baja | Solo infra, no toca codigo de app |
| **Frontend vitest setup** | Media | Toca frontend, valida Principio IX |

**Recomendacion**: Usar **structured logging** como primera feature SDD. Es lo suficientemente compleja para validar el flujo completo sin ser arriesgada.

#### 2.2 Ejecutar el flujo SDD completo

```
1. /speckit.clarify    → Resolver ambiguedades sobre el logging
2. /speckit.specify    → Crear specs/001-structured-logging/spec.md
3. /speckit.plan       → Crear specs/001-structured-logging/plan.md
                         (incluye Constitution Check)
4. /speckit.tasks      → Crear specs/001-structured-logging/tasks.md
5. /speckit.analyze    → Verificar consistencia entre artefactos
6. /speckit.implement  → Implementar siguiendo tasks.md
7. /speckit.checklist  → Validar quality gates
```

#### 2.3 Retrospectiva

Tras completar la feature, documentar:
- Que funciono bien del flujo
- Que templates necesitan ajustes
- Que agentes dieron buen/mal resultado
- Tiempo real vs estimado
- Ajustes necesarios a la constitution

Documentar en `docs/conversation_log.md` como sesion nueva.

---

### Fase 3: Fortalecer la Red de Seguridad

**Prioridad**: P2 — MEDIA
**Esfuerzo estimado**: 1-2 semanas
**Resuelve**: D-05, D-10, D-16

#### 3.1 Setup de tests frontend

El codigo generado por `speckit.implement` para el frontend no tendra tests que lo validen. Esto es un riesgo.

Setup minimo viable:
1. Instalar vitest + @testing-library/react + jsdom
2. Configurar `vitest.config.ts`
3. Crear tests para al menos 2 componentes criticos (ChatPage, AppShell)
4. Anadir job de tests frontend en CI (`ci.yml`)
5. Anadir coverage gate (iniciar en 50%, subir a 70% progresivamente)

#### 3.2 Endurecer MyPy progresivamente

Ruta de endurecimiento en `pyproject.toml`:

```toml
# Fase 3.2a — Habilitar los flags mas impactantes
[tool.mypy]
python_version = "3.11"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true       # Nuevo: forzar types en funciones publicas

# Fase 3.2b (futuro) — Strict completo
# strict = true
```

Hacer esto **despues** de la primera feature SDD para no mezclar refactoring de types con adopcion de spec-kit.

#### 3.3 Auto-generar types frontend desde OpenAPI

Implementar generacion automatica de `types.ts` desde el schema OpenAPI del backend:

1. Usar `openapi-typescript` (npm package)
2. Anadir script en `package.json`: `"generate:types": "openapi-typescript http://localhost:8000/openapi.json -o src/lib/api/types.generated.ts"`
3. Anadir al pre-commit o como paso en CI
4. Actualizar Principio IX de la constitution para referenciar este flujo

---

### Fase 4: Limpieza y Consolidacion

**Prioridad**: P3 — BAJA
**Esfuerzo estimado**: 1 semana
**Resuelve**: D-08, D-11, D-12, D-13

#### 4.1 Actualizar PROJECT_STATUS.md

- Reflejar que CI existe y funciona
- Actualizar metricas reales de cobertura
- Marcar la adopcion de spec-kit como en progreso
- Actualizar "last reviewed" a la fecha actual

#### 4.2 Migrar documentacion legacy

- `docs/app-use-case.md`: Reescribir para reflejar el flujo React actual
- `docs/app-screenshots.md`: Agregar screenshots del frontend React actual (o eliminar si no aportan)

#### 4.3 Implementar task runner

Crear `Taskfile.yml` (o `justfile`) con comandos estandar:

```yaml
tasks:
  bootstrap:     docker compose up -d
  test:          cd backend && pytest tests/ -v
  test:coverage: cd backend && pytest tests/ --cov=app --cov-report=term-missing
  lint:          ruff check backend/app
  format:        ruff format backend/app
  typecheck:     mypy backend/app
  spec:check:    .specify/scripts/bash/check-prerequisites.sh -Json
  spec:new:      .specify/scripts/bash/create-new-feature.sh
```

#### 4.4 Implementar CD real (o eliminarlo)

Decidir:
- **Opcion A**: Implementar deploy a Azure Container Instances o similar
- **Opcion B**: Eliminar `cd.yml` y documentar que el deploy es manual

No dejar placeholders vacios indefinidamente.

---

## Mapa de Dependencias entre Fases

```
Fase 0 (P0: Prerequisitos)
  ├── 0.1 Crear specs/
  ├── 0.2 Crear CLAUDE.md
  ├── 0.3 Fix referencia rota
  └── 0.4 Merge test suite
         │
         ▼
Fase 1 (P1: Infraestructura SDD)
  ├── 1.1 Scripts bash
  ├── 1.2 Constitution Check CI
  ├── 1.3 Issues deuda tecnica
  └── 1.4 Frontmatter constitution
         │
         ▼
Fase 2 (P1: Primera feature SDD)    ← VALIDACION END-TO-END
  ├── 2.1 Elegir feature
  ├── 2.2 Ejecutar flujo completo
  └── 2.3 Retrospectiva
         │
         ▼
Fase 3 (P2: Red de seguridad)       ← EN PARALELO con mas features SDD
  ├── 3.1 Tests frontend
  ├── 3.2 Endurecer MyPy
  └── 3.3 Auto-generar types
         │
         ▼
Fase 4 (P3: Limpieza)               ← EN PARALELO con desarrollo normal
  ├── 4.1 Actualizar PROJECT_STATUS
  ├── 4.2 Migrar docs legacy
  ├── 4.3 Task runner
  └── 4.4 CD real
```

---

## Criterios de Exito

| Hito | Verificacion | Cuando |
|------|-------------|--------|
| `specs/` existe y tiene al menos 1 feature | `ls specs/001-*/spec.md` devuelve resultado | Fin Fase 2 |
| `CLAUDE.md` cargado por Claude Code | Verificar en nueva sesion de Claude Code | Fin Fase 0 |
| CI ejecuta tests y pasa coverage 80% | GitHub Actions green en `develop` | Fin Fase 0 |
| Primera feature completada via SDD | spec.md + plan.md + tasks.md + codigo + tests commiteados | Fin Fase 2 |
| Constitution Check en CI | PR sin seccion rechazado por CI | Fin Fase 1 |
| Frontend tiene tests | `vitest run` pasa en CI | Fin Fase 3 |
| Equipo puede crear feature SDD sin ayuda | Seguir flujo documentado en `specs/README.md` | Fin Fase 2 |

---

## Riesgos y Mitigaciones

| Riesgo | Probabilidad | Impacto | Mitigacion |
|--------|-------------|---------|------------|
| Test suite no pasa en CI (diferencias local vs Ubuntu) | Media | Alto | Correr CI antes de Fase 1; fijar dependencias exactas |
| Templates no encajan con el stack real | Baja | Medio | Fase 2 es explicitamente una validacion; ajustar templates despues |
| Agentes generan codigo que viola la constitution | Media | Medio | Constitution Check en CI + `speckit.analyze` antes de merge |
| Overhead del flujo SDD desanima al equipo | Media | Alto | Empezar con features medianas; retrospectiva honesta en Fase 2.3 |
| MyPy strict rompe demasiado codigo existente | Alta | Medio | Endurecer progresivamente (Fase 3.2), no de golpe |

---

## Referencias

- [spec-kit GitHub](https://github.com/github/spec-kit) — Repositorio oficial
- [Spec-Driven Development](https://github.com/github/spec-kit/blob/main/spec-driven.md) — Metodologia SDD
- [Brownfield Adoption Example](https://github.com/mnriem/spec-kit-aspnet-brownfield-demo) — Demo ASP.NET brownfield
- [Constitution del proyecto](../.specify/memory/constitution.md) — 10 principios, v2.0.0
- [PROJECT_STATUS.md](../PROJECT_STATUS.md) — Estado actual del proyecto
- [Articulo Medium brownfield](articles/brownfield-to-speckit-adoption.md) — Documentacion del journey
