# Conversation Log — RAG-Challenge

This file documents the AI-assisted development journey of RAG-Challenge as a brownfield adoption case study.
It is **append-only** — past entries must never be edited or deleted.

Purpose: capture what the user requested, what was decided, and why. This serves as the living record
of how this project evolves from an existing codebase into a fully AI-governed, spec-driven project.

---

> **NOTE — Architecture pivot (2026-04-02):**
> Sessions 1–8 were conducted against the `main` branch (Streamlit + `python_modules/` architecture).
> Starting from Session 9, all work is on the `develop` branch (FastAPI + React TypeScript architecture),
> which is the active production line going forward. The Streamlit governance is preserved in
> `feature/spec-kit-streamlit-app` for reference.

---

### [2026-04-02] Session 1 — spec-kit adoption plan

**User asked:** Incorporate spec-kit into this brownfield project (RAG-Challenge) to accelerate and organize development. Requested a plan before executing. Referenced the `mnriem/spec-kit-aspnet-brownfield-demo` as the reference pattern. Also asked to verify whether a specific version/tag should be used instead of `main`.

**Decision:** Researched the spec-kit repo and brownfield demo. Confirmed that:
- The latest stable tag is `v0.4.4` (as of 2026-04-02); installing from `main` is discouraged
- The brownfield pattern matches exactly: no prior specs or constitution, agent analyzes the existing codebase
- The install command is `uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.4.4`
- Initialization: `specify init . --here --force --ai copilot --script ps`
- The constitution agent derives project principles from the actual code — no pre-authoring needed

Produced a full step-by-step plan covering installation, initialization, constitution generation, and repeatable feature workflow (specify → clarify → plan → analyze → tasks → implement).

**Artifacts created/modified:**
- `docs/spec-kit-migration-plan.md` — full migration plan

---

### [2026-04-02] Session 2 — governance: TDD, CI/CD, git norms, Copilot instructions

**User asked:** Before adopting spec-kit, establish all CI/CD practices, code editing rules, validations, git norms, etc. Create a battery of project-specific Copilot instructions to align the team. Also confirmed this is a brownfield migration, not greenfield. Explicitly required TDD.

**Decision:** Created a full governance layer using VS Code Copilot instruction files, placed in `.github/` so they are version-controlled and shared across the team. Chose `.instructions.md` files with `applyTo` patterns for automatic loading by Copilot when working on relevant files. Also created `copilot-instructions.md` as the always-on workspace baseline.

Trade-off considered: skills vs instructions. Instructions were chosen because these are always-applicable constraints (not on-demand workflows). Skills would be appropriate for optional processes like spec-kit phases.

**Artifacts created/modified:**
- `.github/copilot-instructions.md` — workspace baseline (TDD, git, security, CI/CD)
- `.github/instructions/tdd.instructions.md` — TDD cycle, pytest, mocks, coverage targets
- `.github/instructions/python-modules.instructions.md` — module conventions, `decode_source()`, type hints
- `.github/instructions/git-workflow.instructions.md` — branch naming, conventional commits, PR checklist
- `.github/instructions/sql-embeddings.instructions.md` — pgvector, parameterized SQL, DDL patterns
- `.gitignore` — added spec-kit draft entries
- `docs/spec-kit-migration-plan.md` — updated to reference instruction files

---

### [2026-04-02] Session 3 — CHANGELOG and conversation_log mandatory rules

**User asked:** Add a CHANGELOG.md to track what changes with each PR. Also create a `conversation_log.md` to capture user requests and AI decisions over time. The goal is for this project to serve as a brownfield adoption case study (existing project → fully AI-governed with spec-kit). Established that both documents are **mandatory** and must be followed strictly.

**Decision:** Added CHANGELOG.md and conversation_log.md as first-class project artifacts with explicit governance rules:
- CHANGELOG follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/) format; every code-changing PR must include an entry under `[Unreleased]`
- conversation_log is append-only; every significant AI session must be logged
- Both rules embedded in `copilot-instructions.md` (always-on) and the PR checklist in `git-workflow.instructions.md`

**Artifacts created/modified:**
- `CHANGELOG.md` — created at root with initial `[Unreleased]` and `[0.1.0]` entries
- `docs/conversation_log.md` — this file; created with sessions 1–3 documented
- `.github/copilot-instructions.md` — added CHANGELOG and conversation_log mandatory sections
- `.github/instructions/git-workflow.instructions.md` — updated PR checklist

---

### [2026-04-02] Session 4 — Cobertura documental: spec-kit vs. PRD, ADR, TechStack

**User asked:** Does spec-kit cover PRD, ADR, TechStack, User Stories, and testing documentation? Should these be defined before or during spec-kit adoption?

**Decision:** spec-kit covers user stories and requirements (via `spec.md`), technical design and decision rationale (via `plan.md`), and architectural principles and tech stack (via `constitution.md`). It does NOT natively generate formal PRDs, standalone ADRs, or explicit test traceability. Decided to implement the gaps:
- ADR structure created in `docs/adr/` with a template and the first real ADR documenting the existing multi-source DB pattern
- `spec-kit-migration-plan.md` updated with a full coverage map

**Artifacts created/modified:**
- `docs/adr/README.md` — ADR directory with index and usage rules
- `docs/adr/000-template.md` — reusable ADR template
- `docs/adr/001-multi-source-database-pattern.md` — first ADR documenting the existing `decode_source()` pattern
- `docs/spec-kit-migration-plan.md` — added "Cobertura documental" section

---

### [2026-04-02] Session 5 — Branching strategy, CI/CD, git governance and test infrastructure

**User asked:** Branch management, PR workflow, naming, develop/main branches, environment promotion — before or after spec-kit?

**Decision:** Before. spec-kit agents will create branches and open PRs — they need the rules in place first.

- **Branching strategy**: simplified GitFlow — `main` (production) + `develop` (staging/integration).
- **CI** extended to run on PRs targeting both `main` and `develop`.
- **CD** workflow created as a skeleton with staging/production jobs.
- **PR template** created — enforces the checklist on every PR in the GitHub UI.
- **Test infrastructure**: `tests/conftest.py` with `mock_env` autouse fixture; 20 parametrized tests for `decode_source()`.

**Artifacts created/modified:**
- `.github/workflows/ci.yml` — updated to run on `develop` and `main`
- `.github/workflows/cd.yml` — new
- `.github/pull_request_template.md` — enforces PR checklist in GitHub UI
- `.github/instructions/git-workflow.instructions.md` — full branching strategy
- `tests/conftest.py` — shared fixtures with autouse mock_env
- `tests/test_module_data.py` — 20 parametrized tests for `decode_source()`
- `requirements.txt` — added pytest, pytest-cov, ruff, mypy

---

### [2026-04-02] Session 6 — Lint baseline, pyproject.toml, 3-level test strategy

**User asked:** "toda la parte de lint tb falta" and "tests e2e, test unitarios, integración tdd" → implement a complete 3-level test strategy.

**Decision:** Fixed 96 ruff lint errors, created `pyproject.toml`, implemented 3-level test pyramid.

**Artifacts created/modified:**
- `pyproject.toml` — ruff + mypy + pytest + coverage configuration (`fail_under = 80`)
- `tests/conftest.py` — added `sys.modules` stubs; extended mock_env
- `tests/test_module_data.py` — 23 parametrized tests PASSING
- `tests/integration/test_db_connections.py` — integration test structure
- `tests/e2e/test_rag_pipeline.py` — E2E test structure
- `.github/instructions/tdd.instructions.md` — updated with 3-level test strategy
- `.github/workflows/ci.yml` — split into `unit-tests` + `integration-tests` jobs

---

### [2026-04-02] Session 7 — Documentation: architecture, tech stack, use cases, broken link fixes, lint alignment

**User asked:** Review documentation — missing architecture, use cases, technology sections. Fix 186 lint problems. Fix broken file references.

**Decision:** Created 3 new docs, fixed flake8/ruff alignment, fixed 14 broken links.

**Artifacts created/modified:**
- `docs/architecture.md` — new (component diagram, RAG data flow, deployment topology)
- `docs/tech-stack.md` — new (authoritative technology reference)
- `docs/use-cases.md` — new (7 use cases)
- `.flake8` — new; aligns flake8 with ruff (120 char limit)
- `README.md` — index reorganized
- `.github/copilot-instructions.md`, `docs/*.md` — 14 broken hrefs fixed
- `app.py`, `python_modules/*.py` — E266/E262/F401 lint fixes (no logic changes)

---

### [2026-04-02] Session 8 — spec-kit FASE 0+1+2: instalación, inicialización y constitución

**User asked:** ¿Podemos poner en marcha ya la parte de spec-kit? / Hazlo tú.

**Decision:** Ejecutado `specify init` (FASE 0+1) y `/speckit.constitution` (FASE 2). Constitución v1.0.0 generada con 8 principios derivados del codebase brownfield Streamlit: (I) portabilidad multi-fuente, (II) disciplina de módulos, (III) TDD, (IV) integridad RAG pipeline, (V) SQL seguro, (VI) secrets-first, (VII) performance, (VIII) deployment discipline.

**Artifacts created/modified:**
- `.specify/scripts/powershell/` — 5 scripts ps1
- `.specify/templates/` — 6 templates .md
- `.specify/memory/constitution.md` — constitución v1.0.0

---

### [2026-04-02] Session 9 — Pivot: governance adaptation to FastAPI/React architecture (develop branch)

**User asked:** Revisar el estado de git — todo está en main sin commitear. Decidir qué hacer con las dos arquitecturas (Streamlit legacy en main vs FastAPI/React en develop).

**Decision:** El análisis reveló que `develop` y `main` tienen arquitecturas completamente distintas e incompatibles:
- `main`: Streamlit + `python_modules/` (la que analizamos en sessions 1-8)
- `develop`: FastAPI + React TypeScript (la arquitectura activa y futura)

Decisión tomada: **`develop` es la línea principal**. Acción:
1. Todo el governance de sessions 1-8 se commiteó en `feature/spec-kit-streamlit-app` (pusheado → preservado)
2. Se creó `feature/spec-kit-governance` desde `develop`
3. Se copiaron los archivos `.github/` y `.specify/` como base
4. Se adaptaron todos los archivos a la nueva arquitectura FastAPI/React

Cambios clave en la adaptación:
- `copilot-instructions.md`: stack actualizado (FastAPI, React TS, no Streamlit); arquitectura en capas (api/service/repository/domain/adapters/core)
- `tdd.instructions.md`: paths `backend/tests/`, cobertura `--cov=app`, patrón FastAPI TestClient + DI overrides, markers `unit/api/integration` (no `e2e`)
- `python-modules.instructions.md`: reescrito para repository pattern (BaseRepository ABC), Pydantic Settings, inyección de dependencias, domain entities
- `ci.yml`: lint/typecheck/tests sobre `backend/`, `pip install -r backend/requirements.txt`
- `cd.yml`: referencias a `backend/requirements.txt`
- `pyproject.toml`: `src = ["backend/app"]`, `testpaths = ["backend/tests"]`, markers `unit/api/integration`
- `docs/conversation_log.md`: creado en develop con historial completo (sessions 1-9)
- `.specify/memory/constitution.md`: pendiente de re-ejecución de `speckit.constitution` sobre la nueva arquitectura

**Artifacts created/modified:**
- `.github/copilot-instructions.md` — adaptado a FastAPI/React
- `.github/instructions/tdd.instructions.md` — adaptado a backend/tests/ y TestClient
- `.github/instructions/python-modules.instructions.md` — reescrito para repository pattern
- `.github/workflows/ci.yml` — apunta a backend/
- `.github/workflows/cd.yml` — apunta a backend/requirements.txt
- `pyproject.toml` — apunta a backend/app y backend/tests
- `docs/conversation_log.md` — este archivo; creado en develop con historial completo
- `feature/spec-kit-streamlit-app` (rama) — preserva todo el governance para la arquitectura Streamlit
