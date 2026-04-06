# Plan de Adopción de OpenSpec — RAG-Challenge (Brownfield)

**Proyecto:** RAG-Challenge  
**Rama:** `feature/openspec-governance`  
**Fecha de inicio:** 2026-04-02  
**Autor:** Eladio Rincon (asistido por GitHub Copilot / Claude Opus 4.6)  
**OpenSpec version:** v1.2.0  
**Perfil seleccionado:** `core` + workflows expandidos  

---

## 1. ¿Qué es OpenSpec y por qué adoptarlo?

**OpenSpec** es un framework ligero de *Spec-Driven Development* (SDD) que añade una capa de especificación entre la intención humana y el código generado por IA. A diferencia de otros frameworks de gobernanza:

| Característica | OpenSpec | Spec Kit (GitHub) | Sin framework |
|---------------|----------|-------------------|---------------|
| Filosofía | Fluido, iterativo | Rígido, fases secuenciales | Ad-hoc |
| Setup | `npm install -g` + `openspec init` | Python + Markdown manual | N/A |
| Brownfield | Diseñado para ello (deltas) | Posible con adaptación | N/A |
| Artefactos | proposal → specs → design → tasks | constitution + specs | Nada |
| Lock-in | Ninguno (20+ herramientas) | GitHub Copilot | N/A |
| Soporte multi-dev | Cambios paralelos con merge de specs | Manual | Conflictos |

**Beneficios clave para RAG-Challenge:**

1. **Orden en un brownfield**: El proyecto ya tiene 80+ commits sin specs. OpenSpec permite documentar el comportamiento actual y gobernar cambios futuros con deltas.
2. **Escalabilidad de equipo**: Pasar de 1 dev a N devs requiere procesos. OpenSpec los proporciona sin burocracia excesiva.
3. **Auditoría nativa**: Cada cambio archivado preserva proposal + design + tasks. Combinado con `conversation_log.md`, se obtiene trazabilidad completa.
4. **Compatible con GitHub Copilot**: OpenSpec genera `.github/prompts/opsx-*.prompt.md` y `.github/skills/openspec-*/SKILL.md` nativamente.

---

## 2. Análisis del estado actual (brownfield)

### 2.1 Stack tecnológico

| Componente | Tecnología | Estado |
|-----------|-----------|--------|
| Backend API | FastAPI (Python 3.11+) | Funcional |
| Frontend | React + TypeScript + Vite + Tailwind | Funcional |
| BD Relacional | PostgreSQL (pgvector) + SQL Server | Funcional |
| Embeddings | OpenAI API | Funcional |
| Infraestructura | Docker Compose + DevContainers | Funcional |
| CI/CD | GitHub Actions (`ci.yml`, `cd.yml`) | Añadido |
| Tests | pytest (416 tests, 80% cobertura) | ✅ |
| Governance | Ninguno → **OpenSpec** (objetivo) | ❌ → 🎯 |

### 2.2 Deuda técnica identificada (a documentar como specs)

| Área | Problema | Urgencia |
|------|----------|----------|
| DI en API handlers | Servicios instanciados a nivel de módulo (`_service = XxxService()`) | Alta |
| DataExplorerService | Conexiones directas psycopg2/pyodbc, ignora Repository Pattern | Crítica |
| CORS | `allow_origins=["*"]` en `main.py` | Alta |
| RAG Pipeline | Sin paso de token budget / sentinel | Alta |
| Adapter en handler | `chat.py` importa `OpenAIAdapter` directamente | Media |
| Test naming | No sigue `test_<method>_<scenario>_<expected>` | Media |
| Frontend .env | No existe `frontend/webapp/.env.example` | Baja |

### 2.3 Artefactos de gobernanza existentes

| Artefacto | Existe | Nota |
|----------|--------|------|
| `.github/workflows/ci.yml` | ✅ | Lint + typecheck + test |
| `.github/workflows/cd.yml` | ✅ | Deploy workflow |
| `.github/copilot-instructions.md` | ❌ | **A crear** |
| `.github/instructions/*.instructions.md` | ❌ | **A crear** |
| `.github/prompts/*.prompt.md` | ❌ | **OpenSpec los genera** |
| `.github/agents/*.agent.md` | ❌ | **A crear** |
| `AGENTS.md` | ❌ | **A crear** |
| `openspec/` | ❌ | **OpenSpec init lo crea** |
| `docs/conversation_log.md` | ❌ | **A crear** |
| `CHANGELOG.md` | ✅ | Existente pero incompleto |
| `docs/adr/` | ✅ | 4 ADRs documentados |

---

## 3. Fases de adopción

### Fase 0 — Preparación del terreno (actual)
**Esfuerzo:** 1 hora | **Beneficio:** Base para todo lo demás

| Paso | Acción | Estado |
|------|--------|--------|
| 0.1 | Crear rama `feature/openspec-governance` desde estado pre-spec-kit | ✅ |
| 0.2 | Añadir `.github/workflows/` (CI/CD) | ✅ |
| 0.3 | Añadir `.coverage` y artefactos pytest a `.gitignore` | ✅ |
| 0.4 | Crear este documento (`docs/PLAN_OPENSPEC_ADOPTION.md`) | ✅ |
| 0.5 | Crear `docs/conversation_log.md` para auditoría | ✅ |
| 0.6 | Crear `.github/copilot-instructions.md` con reglas del proyecto | ✅ |
| 0.7 | Crear `.github/instructions/git-workflow.instructions.md` | ✅ |
| 0.8 | Crear `.github/instructions/tdd.instructions.md` | ✅ |
| 0.9 | Crear `AGENTS.md` o `.github/agents/dev.agent.md` | ✅ |
| 0.10 | Commit y push de todos los artefactos de Fase 0 | ✅ |

### Fase 1 — Instalar OpenSpec
**Esfuerzo:** 30 minutos | **Beneficio:** Slash commands + estructura de specs

| Paso | Acción | Comando |
|------|--------|---------|
| 1.1 | Instalar OpenSpec CLI | `npm install -g @fission-ai/openspec@latest` | ✅ |
| 1.2 | Inicializar para GitHub Copilot | `openspec init --tools "github-copilot"` | ✅ |
| 1.2b | Inicializar para Claude Code | `openspec init --tools "claude"` | ✅ |
| 1.3 | Seleccionar perfil expandido (opcional) | `openspec config profile` → `expanded` | ⬜ (core por ahora) |
| 1.4 | Crear `CLAUDE.md` referenciando AGENTS.md | Manual | ✅ |
| 1.5 | Personalizar `openspec/config.yaml` | Ver sección 5 de este documento | ✅ |
| 1.6 | Commit de la inicialización | `feat: initialize OpenSpec v1.2.0 ...` | ✅ |

**Resultado esperado tras Fase 1:**
```
openspec/
├── specs/              # Vacío (brownfield — se llena progresivamente)
├── changes/            # Vacío (primer cambio pendiente)
└── config.yaml         # Configuración del proyecto

.github/
├── prompts/
│   ├── opsx-propose.prompt.md
│   ├── opsx-apply.prompt.md
│   ├── opsx-explore.prompt.md
│   ├── opsx-archive.prompt.md
│   ├── opsx-verify.prompt.md
│   └── ... (otros slash commands)
├── skills/
│   └── openspec-*/SKILL.md
├── copilot-instructions.md
└── instructions/
    ├── git-workflow.instructions.md
    └── tdd.instructions.md
```

### Fase 2 — Documentar el comportamiento actual como specs
**Esfuerzo:** 4-8 horas | **Beneficio:** Source of truth antes de cambiar nada

Usar `/opsx:explore` para analizar el codebase y luego crear specs iniciales manualmente en `openspec/specs/`:

| Spec domain | Contenido | Prioridad |
|------------|-----------|-----------|
| `api/spec.md` | Endpoints FastAPI, contratos request/response | Alta |
| `rag/spec.md` | Pipeline RAG de 5 pasos (translate→embed→search→enrich→generate) | Alta |
| `data/spec.md` | Repositorios, modelos de dominio, particionado | Media |
| `infra/spec.md` | Docker Compose, DevContainers, CI/CD | Media |
| `frontend/spec.md` | React UI, rutas, componentes principales | Baja |

> **Nota importante para brownfield:** No es necesario documentar TODO el sistema antes de empezar a trabajar. OpenSpec funciona con specs progresivas — documenta lo que vayas a cambiar, cuando lo vayas a cambiar. Las specs crecen orgánicamente conforme se archivan cambios.

### Fase 3 — Primer cambio real con OpenSpec
**Esfuerzo:** 2-4 horas | **Beneficio:** Validar el workflow end-to-end

Ejecutar el onboarding interactivo:
```
/opsx:onboard
```

O crear el primer cambio real desde la deuda técnica:
```
/opsx:propose fix-dependency-injection
```

Esto creará:
```
openspec/changes/fix-dependency-injection/
├── proposal.md        # Por qué: DI vía Depends() en vez de _service = X()
├── specs/api/spec.md  # Delta: MODIFIED requirements para DI
├── design.md          # Cómo: usar core/dependencies.py
└── tasks.md           # Checklist de implementación
```

Workflow completo:
```
/opsx:propose → /opsx:apply → /opsx:verify → /opsx:archive
```

### Fase 4 — Establecer reglas para múltiples desarrolladores
**Esfuerzo:** 2-3 horas | **Beneficio:** Escalabilidad de equipo

| Regla | Implementación |
|-------|---------------|
| Branch naming | `feature/NNN-nombre`, `fix/NNN-nombre` (instrucción en `.github/instructions/`) |
| Conventional commits | `type(scope): description` (pre-commit hook o CI check) |
| PR obligatorio | Requiere 1 review + CI green (branch protection) |
| Spec antes de código | Cada feature branch debe tener un `/opsx:propose` antes de `/opsx:apply` |
| CHANGELOG | Entrada obligatoria bajo `## [Unreleased]` en cada PR |
| Conversation log | Cada sesión AI-assisted debe añadir entrada en `docs/conversation_log.md` |
| Tests | Coverage ≥ 80%, naming `test_method_scenario_expected` |

### Fase 5 — Retroalimentación y mejora continua
**Esfuerzo:** Continuo | **Beneficio:** Madurez del proceso

- [ ] Crear un custom schema `rag-challenge` si el workflow `spec-driven` no encaja
- [ ] Revisar specs archivadas mensualmente
- [ ] Actualizar `openspec/config.yaml` con nuevas rules según se descubran patrones
- [ ] Documentar lecciones aprendidas en este archivo

---

## 4. Artefactos de GitHub Copilot a crear (Fase 0)

### 4.1 `.github/copilot-instructions.md`
Instrucciones globales que GitHub Copilot carga en TODA interacción:
- Arquitectura del proyecto (capas, DI, Repository Pattern)
- Stack tecnológico
- Convenciones de código
- Referencia a archivos de instrucciones específicas

### 4.2 `.github/instructions/git-workflow.instructions.md`
Reglas de gestión de ramas y commits:
- Branch naming: `feature/NNN-*`, `fix/NNN-*`, `chore/*`
- Conventional Commits obligatorios
- CHANGELOG obligatorio
- Conversation log obligatorio
- PR workflow con checklist

### 4.3 `.github/instructions/tdd.instructions.md`
Reglas de test-driven development:
- Coverage mínimo 80%
- Naming: `test_<method>_<scenario>_<expected>`
- `MagicMock(spec=...)` obligatorio
- Factories en `conftest.py`, no inline dicts
- `dependency_overrides.clear()` en teardown

### 4.4 `AGENTS.md` (o `.github/agents/dev.agent.md`)
Definición del agente principal de desarrollo:
- Herramientas disponibles
- Restricciones (no borrar archivos sin confirmar, no push --force)
- Workflow esperado: spec → code → test → commit
- Referencia a conversation_log.md

### 4.5 `docs/conversation_log.md`
Registro cronológico de sesiones AI-assisted:
- Fecha, participantes (humano + modelo AI)
- Objetivo de la sesión
- Decisiones tomadas
- Archivos modificados

---

## 5. Configuración recomendada de OpenSpec

```yaml
# openspec/config.yaml
schema: spec-driven

context: |
  Tech stack: Python 3.11+, FastAPI, React 18, TypeScript, Vite, Tailwind CSS
  Database: PostgreSQL (pgvector) + SQL Server (dual-repo pattern)
  AI: OpenAI API for embeddings and chat completion
  Architecture: Layered (API → Services → Repositories → Domain)
  DI: FastAPI Depends() for all service injection
  Testing: pytest + pytest-cov, 80% minimum coverage
  Infrastructure: Docker Compose, DevContainers, GitHub Actions CI/CD
  This is a brownfield project — existing code must be respected.
  All changes should be backwards-compatible unless explicitly stated.

rules:
  proposal:
    - Include backward compatibility analysis
    - List affected layers (API, Service, Repository, Domain)
    - Identify test impact
  specs:
    - Use Given/When/Then format for scenarios
    - Use RFC 2119 keywords (MUST, SHALL, SHOULD, MAY)
    - Reference existing ADRs when relevant
  design:
    - Include file change list with (new) or (modified) tags
    - Reference the Repository Pattern and DI conventions
    - Include rollback strategy
  tasks:
    - Group by layer (API, Service, Repository, Test)
    - Each task should be completable in < 1 hour
    - Include a test task for each implementation task
```

---

## 6. Mapeo OpenSpec ↔ GitHub Copilot

| OpenSpec artifact | GitHub Copilot equivalent | Ruta |
|------------------|--------------------------|------|
| Skills | `.github/skills/openspec-*/SKILL.md` | Auto-generado por `openspec init` |
| Slash commands | `.github/prompts/opsx-*.prompt.md` | Auto-generado por `openspec init` |
| Agent instructions | `.github/copilot-instructions.md` | Manual (Fase 0) |
| Specific rules | `.github/instructions/*.instructions.md` | Manual (Fase 0) |
| Agent definition | `AGENTS.md` o `.github/agents/*.agent.md` | Manual (Fase 0) |
| Conversation log | `docs/conversation_log.md` | Manual (Fase 0) |

---

## 7. Estimación de esfuerzo y beneficio

| Fase | Esfuerzo | Beneficio | ROI |
|------|----------|-----------|-----|
| Fase 0 — Preparación | 1 h | Base de gobernanza para agentes | 🔴 Crítico |
| Fase 1 — Install OpenSpec | 30 min | Slash commands, estructura | 🟠 Alto |
| Fase 2 — Specs iniciales | 4-8 h | Source of truth documentado | 🟡 Medio |
| Fase 3 — Primer cambio OpenSpec | 2-4 h | Validación del workflow | 🟠 Alto |
| Fase 4 — Reglas multi-dev | 2-3 h | Escalabilidad de equipo | 🟠 Alto |
| Fase 5 — Mejora continua | Continuo | Madurez del proceso | 🟢 Progresivo |

**Total para obtener valor inmediato (Fases 0+1+3):** ~4-6 horas  
**Total completo (todas las fases):** ~12-20 horas

---

## 8. Diario de pasos realizados (para la comunidad)

Este apartado documenta paso a paso lo que se ha ido haciendo, para que otros proyectos brownfield puedan replicar el proceso.

### Paso 1 — Identificar el punto de partida (2026-04-02)

**Problema:** El proyecto tenía 80+ commits, sin ningún framework de gobernanza. Un solo desarrollador había trabajado en todo. Se necesitaba establecer orden antes de escalar a múltiples devs.

**Decisión:** Crear una rama limpia desde el último commit pre-gobernanza (`c3be08c`, 20-Feb-2026) para adoptar OpenSpec sin contaminación de intentos previos.

**Comandos ejecutados:**
```bash
git checkout -b feature/openspec-governance c3be08c
git checkout develop -- .github/workflows/ci.yml .github/workflows/cd.yml
git commit -m "chore: add CI/CD workflow files (ci.yml, cd.yml)"
git push origin feature/openspec-governance
```

**Lección aprendida:** En un brownfield, es mejor crear la rama de gobernanza desde un punto estable conocido y traer selectivamente solo lo que necesitas (como CI/CD), en lugar de intentar "limpiar" la rama actual.

### Paso 2 — Limpiar .gitignore (2026-04-02)

**Problema:** `backend/.coverage` aparecía como untracked. Los artefactos de pytest no estaban ignorados.

**Acción:** Añadir `.coverage`, `.coverage.*`, `htmlcov/`, `.pytest_cache/` a `.gitignore`.

**Lección aprendida:** Antes de establecer gobernanza, asegurar que el repo está limpio de artefactos generados.

### Paso 3 — Crear artefactos de gobernanza manual (2026-04-02)

**Problema:** OpenSpec genera slash commands y skills automáticamente, pero las instrucciones de Copilot, las reglas de git, TDD, y el agente de desarrollo son específicas del proyecto y deben crearse manualmente.

**Artefactos creados:**
1. `docs/PLAN_OPENSPEC_ADOPTION.md` — Este plan
2. `docs/conversation_log.md` — Registro de sesiones AI
3. `.github/copilot-instructions.md` — Instrucciones globales de Copilot
4. `.github/instructions/git-workflow.instructions.md` — Reglas de gestión de ramas
5. `.github/instructions/tdd.instructions.md` — Reglas de TDD
6. `AGENTS.md` — Definición del agente de desarrollo

**Lección aprendida:** La gobernanza tiene dos capas: (1) la que el framework proporciona (OpenSpec → specs, changes, slash commands) y (2) la que el equipo define (instrucciones de agente, workflow git, TDD). Ambas son necesarias.

### Paso 4 — Instalar e inicializar OpenSpec (2026-04-02)

**Problema:** Se necesitaba un framework de spec-driven development que soporte tanto GitHub Copilot como Claude Code.

**Acciones realizadas:**
1. Instalar OpenSpec CLI v1.2.0 globalmente: `npm install -g @fission-ai/openspec@latest`
2. Inicializar para Claude Code: `openspec init --tools "claude"` → genera `.claude/commands/opsx/` + `.claude/skills/openspec-*/`
3. Inicializar para GitHub Copilot: `openspec init --tools "github-copilot"` → genera `.github/prompts/opsx-*.prompt.md` + `.github/skills/openspec-*/`
4. Crear `CLAUDE.md` como fichero fino que referencia `AGENTS.md` (fuente de verdad única compartida Copilot/Claude).
5. Crear `openspec/config.yaml` manualmente con contexto del proyecto, esquema `spec-driven`, y reglas por artefacto.
6. Actualizar `docs/conversation_log.md` con los detalles de esta sesión.
7. Commit y push: `feat: initialize OpenSpec v1.2.0 with GitHub Copilot and Claude Code support`

**Artefactos generados automáticamente por OpenSpec (perfil `core`):**

| Tool | Slash Commands (4) | Skills (4) |
|------|-------------------|------------|
| GitHub Copilot | `.github/prompts/opsx-{propose,apply,archive,explore}.prompt.md` | `.github/skills/openspec-{propose,apply-change,archive-change,explore}/SKILL.md` |
| Claude Code | `.claude/commands/opsx/{propose,apply,archive,explore}.md` | `.claude/skills/openspec-{propose,apply-change,archive-change,explore}/SKILL.md` |

**Lecciones aprendidas:**
- `openspec init --tools "github-copilot,claude"` no funciona: el flag `--tools` solo acepta un valor. Hay que ejecutar `init` una vez por tool.
- `openspec/config.yaml` no se genera en modo no-interactivo. Hay que crearlo manualmente.
- Tener dos entrypoints (`AGENTS.md` para Copilot/Codex, `CLAUDE.md` para Claude Code) con una sola fuente de verdad evita duplicación de reglas.
- OpenSpec genera exactamente 4 skills + 4 commands por herramienta en perfil `core` (propose, apply, archive, explore).

### Paso 5 — Documentar el sistema actual como specs (2026-04-02)

**Problema:** No existían specs formales del sistema. El código era la única fuente de verdad. Para gobernar cambios futuros, necesitamos documentar el comportamiento actual como baseline.

**Acciones realizadas:**
1. Explorar el codebase completo usando un subagente (API, services, repos, domain, adapters, DI, config, infra, frontend).
2. Crear 4 specs iniciales en `openspec/specs/`:
   - `api/spec.md` — 10 routers, ~25 endpoints, contratos request/response, cross-cutting concerns
   - `rag/spec.md` — Pipeline de 5 pasos, token management, retry strategy, response contract
   - `data/spec.md` — Domain entities (14), exceptions (5), repository pattern, dual-repo, DB schema
   - `infra/spec.md` — Docker Compose (4 services), config (Pydantic), DI providers, CI/CD, testing

**Decisión:** No crear `frontend/spec.md` (baja prioridad; el frontend consume la API pero no tiene lógica de negocio crítica).

**Formato de specs:**
- Tablas para contratos y comparativas.
- Given/When/Then para comportamiento clave.
- ASCII diagrams para flujos.
- Sección "Known Deviations" para documentar deuda técnica respecto a las reglas del proyecto.

**Lección aprendida:** En un brownfield, las specs iniciales sirven como "fotografía" del sistema, no como verdad aspiracional. Las desviaciones se documentan explícitamente para que futuros `/opsx:propose` las puedan corregir.

### Paso 6 — Primer cambio real con OpenSpec (2026-04-06)

**Problema:** Validar el workflow completo de OpenSpec end-to-end con un cambio real.

**Cambio elegido:** `cors-hardening` — reemplazar `allow_origins=["*"]` por `CORS_ORIGINS` configurable (deuda técnica identificada en sección 2.2).

**Acciones realizadas:**
1. `/opsx:propose cors-hardening` → generó proposal, design, specs/infra, tasks
2. `/opsx:apply` → implementación TDD (5 tests + código)
3. PR #14 mergeado a `develop`

**Lecciones aprendidas (incorporadas en PR #15):**
- Las tareas se marcaron `[x]` sin ejecutar tests — 4 de 5 fallaban
- Imports incorrectos (`config.settings` vs `app.core.config`) por diferencia de cwd
- `List[str]` en pydantic-settings falla por JSON parse antes de validators
- Middleware CORS no se puede patchear tras import — requiere test app dedicada
- Se añadieron reglas de verificación a AGENTS.md, config.yaml, SKILL.md y tdd.instructions.md

### Paso 7 — Definir workflow de desarrollo paralelo con worktrees (2026-04-06)

**Problema:** El proyecto tiene múltiples items de deuda técnica independientes (DI, DataExplorer, token budget, etc.). Implementarlos secuencialmente es lento. Se necesita un patrón para paralelizar changes.

**Decisión:** Adoptar git worktrees como mecanismo de aislamiento para aplicar múltiples OpenSpec changes en paralelo. Cada change se ejecuta en un worktree independiente con su propia rama.

**Investigación realizada:** Se consultaron las siguientes fuentes para definir best practices:

| Fuente | Aporte clave |
|--------|-------------|
| [Claude Code Worktree Complete Guide](https://claudelab.net/en/articles/claude-code/claude-code-worktree-guide) | `isolation: "worktree"` en subagentes, cleanup automático |
| [Git Worktrees for Multi-Feature Development with AI Agents](https://www.nrmitchi.com/2025/10/using-git-worktrees-for-multi-feature-development-with-ai-agents/) | Patrón branch-per-worktree, límites prácticos |
| [How Git Worktrees Changed My AI Agent Workflow (Nx Blog)](https://nx.dev/blog/git-worktrees-ai-agents) | Aislamiento de agentes, no ejecutar `git gc` con worktrees activos |
| [One-Person Engineering Team: Claude Code Parallel Workflow](https://www.shareuhack.com/en/posts/claude-code-parallel-workflow-guide-2026) | Boris Cherny: 10-15 sesiones paralelas, recomendación práctica 3-5 |
| [Claude Code Common Workflows (docs oficiales)](https://code.claude.com/docs/en/common-workflows) | Soporte nativo de worktrees en Claude Code CLI |
| [Spec-Driven Development with AI (GitHub Blog)](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/) | OpenSpec changes como unidades paralelas independientes |
| [OpenSpec — Repositorio oficial](https://github.com/Fission-AI/OpenSpec) | Modelo de cambios aislados en `changes/` + merge de specs |

**Reglas definidas:**
1. Proponer en `develop` (secuencial) → aplicar en worktrees (paralelo) → PR por change → merge secuencial
2. Solo paralelizar changes que no toquen los mismos ficheros
3. Máximo 2-3 worktrees simultáneos
4. Cada worktree necesita su propio install de dependencias si hay paquetes nuevos
5. No ejecutar `git gc` con worktrees activos

**Artefactos actualizados:**
- `AGENTS.md` § "Parallel development with worktrees"
- `.github/instructions/git-workflow.instructions.md` § "Worktrees para desarrollo paralelo"
- `openspec/config.yaml` → nueva sección `parallel:`
- `.claude/skills/openspec-apply-change/SKILL.md` → bloque "Parallel Apply with Worktrees"
- `CLAUDE.md` → referencia a worktrees en sección OpenSpec governance

---

## 9. Referencias

### OpenSpec
- [OpenSpec — Repositorio oficial](https://github.com/Fission-AI/OpenSpec)
- [OpenSpec — Getting Started](https://github.com/Fission-AI/OpenSpec/blob/main/docs/getting-started.md)
- [OpenSpec — Workflows](https://github.com/Fission-AI/OpenSpec/blob/main/docs/workflows.md)
- [OpenSpec — Commands](https://github.com/Fission-AI/OpenSpec/blob/main/docs/commands.md)
- [OpenSpec — Customization](https://github.com/Fission-AI/OpenSpec/blob/main/docs/customization.md)
- [OpenSpec — Supported Tools](https://github.com/Fission-AI/OpenSpec/blob/main/docs/supported-tools.md)
- [OpenSpec — Concepts](https://github.com/Fission-AI/OpenSpec/blob/main/docs/concepts.md)
- [Spec-Driven Development with AI (GitHub Blog)](https://github.blog/ai-and-ml/generative-ai/spec-driven-development-with-ai-get-started-with-a-new-open-source-toolkit/)

### Git worktrees y desarrollo paralelo con agentes AI
- [Claude Code Common Workflows (docs oficiales)](https://code.claude.com/docs/en/common-workflows)
- [Claude Code Worktree Complete Guide (Claude Lab)](https://claudelab.net/en/articles/claude-code/claude-code-worktree-guide)
- [Git Worktrees for Multi-Feature Development with AI Agents (Nick Mitchinson)](https://www.nrmitchi.com/2025/10/using-git-worktrees-for-multi-feature-development-with-ai-agents/)
- [How Git Worktrees Changed My AI Agent Workflow (Nx Blog)](https://nx.dev/blog/git-worktrees-ai-agents)
- [One-Person Engineering Team: Claude Code Parallel Workflow Guide](https://www.shareuhack.com/en/posts/claude-code-parallel-workflow-guide-2026)
- [Mastering Git Worktrees with Claude Code (Medium)](https://medium.com/@dtunai/mastering-git-worktrees-with-claude-code-for-parallel-development-workflow-41dc91e645fe)
- [Parallel Vibe Coding with Git Worktrees (Dan Does Code)](https://www.dandoescode.com/blog/parallel-vibe-coding-with-git-worktrees)
