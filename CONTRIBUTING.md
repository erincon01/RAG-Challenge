# Contributing to RAG-Challenge

Thanks for your interest in contributing! This guide covers everything you need to get started.

## Prerequisites

- **Docker** and **Docker Compose** (required for all contributors)
- **Git**
- **Node 20+** (frontend development)
- **Python 3.11+** (backend development)

## Quick setup

```bash
git clone https://github.com/<org>/RAG-Challenge.git
cd RAG-Challenge
git checkout develop
docker compose up --build
make seed          # loads seed dataset (no OpenAI key needed)
```

The app is available at `http://localhost:5173` (frontend) and `http://localhost:8000` (backend API).

## Workflow

1. **Pick an issue** — choose from the issue tracker or create one.
2. **Create a branch** from `develop`:
   ```
   git checkout develop && git pull
   git checkout -b feature/NNN-short-description
   ```
   Use `feature/NNN-desc`, `fix/NNN-desc`, or `chore/desc` naming.
3. **If complex, propose a spec first** — run `/opsx:propose <feature-name>` to create an OpenSpec proposal with design and tasks before writing code.
4. **Implement with TDD** — write tests first, then implementation. Target 80%+ coverage.
5. **Update CHANGELOG.md** — add your change under `## [Unreleased]` in the appropriate section.
6. **Open a PR against `develop`** — fill in the PR template, link the issue.
7. **After merge** — if you used OpenSpec, archive the change with `/opsx:archive`.

## Coding standards

See [AGENTS.md](AGENTS.md) for the full set of project rules. Key points:

- **Conventional Commits** in English: `type(scope): description` (e.g., `feat(api): add search endpoint`)
- **80% test coverage** minimum — CI enforces this gate
- **Formatting**: `ruff format backend/app` — no exceptions
- **Linting**: `ruff check backend/app`
- **Type checking**: `mypy backend/app`

## OpenSpec integration

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven development. The cycle is:

1. **Propose** — `/opsx:propose <name>` creates a change proposal in `openspec/changes/<name>/` with design, specs, and tasks.
2. **Apply** — `/opsx:apply` implements the tasks from the change, following the task list.
3. **Archive** — `/opsx:archive` moves the completed change to `openspec/changes/archive/`.

Before implementing any non-trivial feature, check if a spec exists in `openspec/changes/` or `openspec/specs/`. If not, propose one first.

## Issue templates

When creating issues, use the provided templates:

- **Bug Report** — for reporting defects
- **Feature Request** — for suggesting new features or improvements

Issues that require significant design work should be tagged with the `needs-spec` label.
