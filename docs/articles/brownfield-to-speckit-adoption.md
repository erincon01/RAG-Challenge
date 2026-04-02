# From Brownfield to Spec-Kit Ready: A Practical Guide

*How we took a legacy RAG application and made it AI-governance-ready — so spec-kit agents could actually work.*

---

## The Promise and the Problem

[Spec-kit](https://github.com/github/spec-kit) is GitHub's open-source toolkit for **Spec-Driven Development** — a structured workflow where AI agents transform natural-language specifications into working code through a repeatable pipeline: `constitution → specify → clarify → plan → tasks → implement`. With 84k+ stars and support for every major AI coding agent (Copilot, Claude, Cursor, Windsurf, Gemini, and many more), it is quickly becoming the standard way to get predictable, high-quality output from AI-assisted development.

But here's what no one tells you: **spec-kit works best when your project has its house in order.** If your codebase has no testing norms, no CI pipeline, no defined architecture, and no clear conventions — the AI agents will generate code that doesn't fit, tests that don't run, and PRs that nobody can review.

This article documents exactly how we prepared a real brownfield application — a football analytics RAG system with ~15k lines of Python, SQL, React, and config — for spec-kit adoption. Every step, every trade-off, every mistake. The goal is to give you a repeatable playbook so you can do the same with your own legacy project in a matter of hours, not weeks.

---

## The Starting Point: What We Had

**RAG-Challenge** is a Retrieval-Augmented Generation system for football match analysis, built on top of [StatsBomb open data](https://github.com/statsbomb/open-data). Users ask natural-language questions about a match; the system retrieves the most relevant event summaries via vector search, builds a context window, and sends it to Azure OpenAI for a grounded answer.

The stack when we started:

- **Backend**: FastAPI (Python 3.11) with a 6-layer architecture: `api → services → repositories → domain → adapters → core`
- **Frontend**: React 19 + TypeScript + Tailwind CSS
- **Databases**: PostgreSQL (pgvector) and Azure SQL Server (native `VECTOR` type)
- **AI**: Azure OpenAI (GPT-4o for chat, text-embedding-3-small for vectors)
- **Infrastructure**: Docker Compose for local dev, GitHub Actions CI/CD

What we *didn't* have:

- ❌ No coding conventions documented anywhere
- ❌ No TDD workflow or test coverage requirements
- ❌ No pre-commit hooks
- ❌ No CI/CD aligned with the actual project structure
- ❌ No architecture documentation
- ❌ No branching strategy beyond "push to main"
- ❌ No CHANGELOG or decision log

In other words: a functioning application with zero governance. Exactly the kind of project where AI agents would produce inconsistent, hard-to-integrate code.

---

## The Key Insight: Governance Before Tooling

The [brownfield demos](https://github.com/mnriem/spec-kit-aspnet-brownfield-demo) in the spec-kit community show a streamlined path: clone repo → `specify init` → `speckit.constitution` → start building features. That works if your project is already well-structured.

Ours wasn't. We discovered that **the constitution is only as useful as the conventions it can reference.** If there are no testing norms, the constitution can't enforce them. If there is no CI pipeline, the agents can't verify their output. If there are no module conventions, the generated code will be stylistically inconsistent.

So we flipped the order:

> **Step 0**: Establish governance (instructions, CI, git workflow, TDD norms)
> **Step 1**: *Then* install and initialize spec-kit
> **Step 2**: Generate the constitution from the *now-governed* codebase

This is the single most important lesson: **governance first, spec-kit second.**

---

## Step 0: The Governance Layer

This step took the most effort but delivered the highest ROI. Everything below was done *before* running `specify init`.

### 0.1 — Copilot Instruction Files

We created a set of `.instructions.md` files in `.github/instructions/` that VS Code Copilot loads automatically based on `applyTo` glob patterns. These are not just documentation — they are **active constraints** that shape every Copilot suggestion:

| File | `applyTo` | Purpose |
|------|-----------|---------|
| `python-modules.instructions.md` | `backend/**/*.py` | 6-layer architecture rules, repository pattern, DI via `Depends()`, no `os.getenv()` in handlers |
| `tdd.instructions.md` | `backend/tests/**/*.py` | 9-step TDD workflow, TestClient + dependency overrides, markers (`unit`, `api`, `integration`), coverage ≥ 80% |
| `git-workflow.instructions.md` | — | Branch naming (`feature/NNN-desc`), conventional commits, PR checklist, CHANGELOG rules |
| `sql-embeddings.instructions.md` | `{postgres,sqlserver}/**/*.sql` | Parameterized queries, pgvector operator usage, naming conventions |

Plus a global `copilot-instructions.md` in `.github/` that is always active, covering the tech stack, security rules, and mandatory processes.

**Why this matters for spec-kit:** When `speckit.implement` generates code, Copilot uses these instructions as constraints. Without them, the agents generate code that *might work* but doesn't follow your conventions. With them, generated code is stylistically consistent from day one.

### 0.2 — TDD Infrastructure

We adopted a strict Test-Driven Development workflow — not just as a nice-to-have, but as a requirement *before* spec-kit adoption. The reasoning: `speckit.implement` will generate both code and tests. If there's no test infrastructure, those tests have nowhere to run.

What we set up:

- **Test runner**: `pytest` with `pytest-asyncio` for async endpoints
- **Test layout**: `backend/tests/unit/`, `api/`, `integration/` (matching the architecture layers)
- **Coverage**: `pytest-cov` with `--cov-fail-under=80` in CI
- **Mocking pattern**: FastAPI `app.dependency_overrides` for repositories + `unittest.mock.patch` for adapters
- **Markers**: `@pytest.mark.unit`, `@pytest.mark.api`, `@pytest.mark.integration`

The TDD workflow itself (documented in `tdd.instructions.md`):

```
1. RED    — Write a failing test for the new behavior
2. GREEN  — Write the minimum code to make it pass
3. REFACTOR — Clean up without changing behavior
4. Verify — Run full test suite: cd backend && pytest tests/ -v
5. Coverage — Ensure ≥ 80%: pytest tests/ --cov=app --cov-report=term-missing
```

### 0.3 — CI/CD Pipeline

We created GitHub Actions workflows that mirror the local development workflow:

**CI** (`ci.yml`) — runs on every PR targeting `develop` or `main`:
```
lint (ruff check backend/app/)
  → typecheck (mypy backend/app/)
    → unit+api tests (pytest backend/tests/ --cov=app --cov-fail-under=80)
      → integration tests (with DB services)
```

**CD** (`cd.yml`) — push to `develop` triggers staging deployment; push to `main` triggers production.

### 0.4 — Pre-Commit Hooks

We added `.pre-commit-config.yaml` with hooks that run before every commit:

- **ruff** lint + format on `backend/app/`
- **mypy** type checking
- **Hygiene**: trailing whitespace, check-yaml, check-json, end-of-file-fixer
- **Branch protection**: `no-commit-to-branch` on `main` and `develop`

This ensures that *no code* (whether human-written or AI-generated) reaches the repo without passing basic quality gates.

### 0.5 — Git Workflow

We formalized the branching strategy:

- `main` — production-ready code
- `develop` — integration branch (staging)
- `feature/NNN-description` — all work happens in feature branches
- Conventional commits: `feat:`, `fix:`, `test:`, `chore:`, `docs:`, `refactor:`
- All changes via Pull Request; no direct push to `main` or `develop`

### 0.6 — CHANGELOG and Conversation Log

Two mandatory documents:

- **`CHANGELOG.md`** — follows [Keep a Changelog](https://keepachangelog.com/en/1.0.0/); every PR must add an entry under `[Unreleased]`
- **`docs/conversation_log.md`** — append-only log of every AI-assisted session, capturing what was requested, what was decided, and why. This is invaluable for understanding *why* decisions were made months later.

### 0.7 — Architecture and Tech Stack Documentation

Before the constitution agent analyzes the codebase, it helps enormously if the codebase has documentation that describes its own architecture. We created:

- **`docs/architecture.md`** — layer diagram, all routers, services, repositories, the 6-step RAG pipeline, database model, configuration pattern
- **`docs/tech-stack.md`** — exact versions of every dependency, all environment variables, development tooling
- **`docs/app-use-case.md`** — 6 named use cases (UC-1 through UC-6) with API endpoint references

These documents serve double duty: they help human developers understand the system, AND they give the `speckit.constitution` agent much richer context to derive principles from.

---

## Step 1: Install and Initialize Spec-Kit

With governance in place, spec-kit initialization was straightforward:

```powershell
# Install the CLI (pinned to a stable release)
uv tool install specify-cli --from git+https://github.com/github/spec-kit.git@v0.4.4

# Initialize in the existing project directory
specify init . --here --force --ai copilot --script ps
```

This scaffolded:
- `.specify/scripts/powershell/` — helper scripts for the SDD workflow
- `.specify/templates/` — spec, plan, tasks templates
- `.specify/memory/` — where the constitution lives

**Tip:** Use `--force` when initializing in an existing project so spec-kit merges its structure into yours without interactive prompts.

---

## Step 2: Generate the Constitution

The constitution is the foundation of everything spec-kit does. It's a set of project principles that every subsequent agent (specify, plan, tasks, implement) must respect.

We invoked the `speckit.constitution` agent with this prompt:

> *"As this is a pre-existing brownfield project, analyze the codebase exhaustively and in-depth. Do NOT skim — use multiple iterations to do a deep analysis. Create principles focused on code quality, testing standards, user experience consistency, and performance requirements. Include governance for how these principles should guide technical decisions and implementation choices."*

The agent produced a constitution (`.specify/memory/constitution.md`) with 10 principles derived directly from our code:

1. **Layered Architecture** — one-way dependency rule (`api → services → repositories → domain`)
2. **Repository Pattern** — all DB access through `BaseRepository` ABC
3. **Dependency Injection** — via FastAPI `Depends()`, never global imports
4. **Configuration via Pydantic Settings** — all config from `.env`, accessed via `get_settings()`
5. **RAG Pipeline Integrity** — 6-step pipeline preserved across changes
6. **Test Strategy** — TDD, 80% coverage, markers for test categories
7. **SQL Safety** — parameterized queries, never string concatenation
8. **Secrets-First** — no hardcoded credentials, all via env vars
9. **Frontend Contract** — React communicates exclusively via REST API
10. **Docker Infrastructure** — Docker Compose for local dev, dev containers

Because we had done Step 0 (governance), the constitution captured *real, enforced* conventions rather than aspirational ones. This is the difference between a constitution that says "tests are important" and one that says "tests use `pytest` markers `@pytest.mark.api`, coverage ≥ 80% via `--cov=app --cov-fail-under=80`, mocking via `app.dependency_overrides`."

---

## The Architecture Pivot: When Reality Bites

Here's a curveball we didn't expect. We initially ran the entire governance process (sessions 1‒8) against the `main` branch, which was a legacy **Streamlit** application. Then we discovered that the project had *two* divergent branches:

- `main` — Streamlit + flat `python_modules/` architecture (legacy)
- `develop` — FastAPI + React TypeScript (the active, future architecture)

These branches were 209 files apart. **Everything we'd built for governance was for the wrong architecture.**

What we did:

1. **Preserved** the Streamlit governance in a branch (`feature/spec-kit-streamlit-app`) so nothing was lost
2. **Created** `feature/spec-kit-governance` from `develop`
3. **Adapted** every single governance file to the FastAPI architecture — paths, patterns, conventions, test infrastructure, CI jobs, everything
4. **Regenerated** the constitution on the new architecture (v2.0.0 replacing v1.0.0)

**Lesson learned:** Before starting governance work, verify which branch represents the *actual* future of the project. We wasted effort, but the detour taught us that our governance files were portable — adapting them to a different architecture took hours, not days, because the structure was solid.

---

## The Result: A Spec-Kit-Ready Project

After completing all steps, our project had:

| Artifact | Purpose |
|----------|---------|
| `.github/copilot-instructions.md` | Always-on workspace rules |
| `.github/instructions/*.instructions.md` | Context-specific coding constraints |
| `.github/workflows/ci.yml` | Automated quality gates |
| `.github/workflows/cd.yml` | Staging + production deployment |
| `.pre-commit-config.yaml` | Local quality gates |
| `.github/pull_request_template.md` | PR checklist enforcement |
| `pyproject.toml` | Centralized tool configuration |
| `docs/architecture.md` | System architecture reference |
| `docs/tech-stack.md` | Technology inventory |
| `docs/app-use-case.md` | Use case catalog |
| `docs/conversation_log.md` | AI decision log |
| `CHANGELOG.md` | Change tracking |
| `.specify/memory/constitution.md` | Project principles (auto-derived) |
| `.specify/templates/` | Spec-kit templates |

**The project is now ready for the `specify → clarify → plan → tasks → implement` workflow.** When we invoke `speckit.specify` for a new feature, the agents will:

- Respect our 6-layer architecture (because the constitution says so)
- Generate tests that follow our TDD markers (because `tdd.instructions.md` is loaded)
- Create code that uses `Depends()` for DI (because `python-modules.instructions.md` enforces it)
- Pass CI on the first try (because pre-commit hooks catch issues locally)
- Produce a clean PR with a CHANGELOG entry (because `git-workflow.instructions.md` requires it)

---

## Practical Tips: What We Wish We Knew

### 1. Start with `copilot-instructions.md`, not spec-kit

The most impactful single file is `.github/copilot-instructions.md`. It's always loaded, applies to everything, and shapes every AI interaction. Write this first — even before thinking about spec-kit.

### 2. Instruction files are your real governance

`.instructions.md` files with `applyTo` patterns are remarkably powerful. A well-written instruction file for `backend/**/*.py` does more for code consistency than any amount of spec-kit constitution text, because it's active on every keystroke.

### 3. The constitution should describe *what is*, not *what should be*

Don't write aspirational principles. Let the constitution agent derive them from your actual code. If your code doesn't follow a pattern yet, establish the pattern first (in governance), *then* let the constitution agent discover it.

### 4. Document your architecture before generating the constitution

The richer your `architecture.md` and `tech-stack.md`, the more specific and useful the constitution will be. The agent reads these files during analysis.

### 5. CI must exist before `speckit.implement`

If there's no CI pipeline, there's no way to verify that AI-generated code actually works. The `implement` agent is only as good as the feedback loop it gets.

### 6. Be ready for pivots

Our architecture pivot (Streamlit → FastAPI) cost us real time. But the governance layer was flexible enough to adapt. If you invest in good governance structure, pivots become *adaptation* exercises rather than *rebuilding* exercises.

### 7. The conversation log is surprisingly valuable

We initially treated `conversation_log.md` as busywork. By session 9, it was the single most important document for understanding *why* we made specific decisions. Future developers (and future AI agents) will thank you.

---

## Summary: The Brownfield Playbook

Here's the condensed playbook for taking any legacy project from brownfield to spec-kit-ready:

```
Phase 0 — Governance (before spec-kit)
  ├── 0.1  Write copilot-instructions.md (always-on rules)
  ├── 0.2  Write .instructions.md files (per-context rules)
  ├── 0.3  Set up TDD infrastructure (pytest, markers, coverage)
  ├── 0.4  Create CI pipeline (lint → typecheck → tests)
  ├── 0.5  Add pre-commit hooks (ruff, mypy, hygiene)
  ├── 0.6  Formalize git workflow (branching, commits, PRs)
  ├── 0.7  Create CHANGELOG.md + conversation_log.md
  └── 0.8  Document architecture and tech stack

Phase 1 — Spec-Kit Initialization
  ├── 1.1  Install specify CLI (pinned version)
  └── 1.2  specify init . --here --force --ai copilot

Phase 2 — Constitution
  └── 2.1  Invoke speckit.constitution (deep codebase analysis)

Phase 3 — Ready to Build
  └── 3.x  specify → clarify → plan → tasks → implement (per feature)
```

The entire Phase 0 can be done in a single focused session (we did it in one day, across 9 AI-assisted sessions). Phase 1 takes minutes. Phase 2 takes one agent invocation.

After that, every new feature follows the structured `specify → implement` pipeline, with AI agents that understand your architecture, respect your conventions, and produce code that passes CI on the first try.

**That's the real value of the brownfield investment: not the governance itself, but the compounding returns on every feature built afterward.**

---

*RAG-Challenge is an open-source project by [erincon01](https://github.com/erincon01/RAG-Challenge). The full governance journey — including all instruction files, CI/CD workflows, and the conversation log — is available in the repository.*

*Spec-kit is developed by GitHub. Learn more at [github.com/github/spec-kit](https://github.com/github/spec-kit).*
