# CLAUDE.md

## Mandatory reading

Read and follow ALL rules in `AGENTS.md` before starting any work.
That file is the single source of truth for project conventions,
architecture rules, testing requirements, and workflow.

Read also these instruction files for specific rules:

- `.github/instructions/git-workflow.instructions.md` — Branch naming, commits, CHANGELOG
- `.github/instructions/tdd.instructions.md` — Testing conventions, coverage, naming

## Project overview

RAG-Challenge is a **Retrieval Augmented Generation** system for football data from StatsBomb.
It allows ingesting competition/match data, generating embeddings, and answering natural-language
questions using vector search + LLM.

**Stack:** FastAPI (Python 3.11+) · React 18 + TypeScript + Tailwind · PostgreSQL (pgvector) ·
SQL Server 2025 · OpenAI API · Docker Compose · GitHub Actions CI

## Git workflow

- **`develop`** is the integration branch — all feature PRs target `develop`.
- **`main`** is production — only admins merge from `develop` via PR.
- Branch naming: `feature/NNN-desc`, `fix/NNN-desc`, `chore/desc` (from `develop`).
- Conventional Commits in English: `type(scope): description`.
- CHANGELOG: update `## [Unreleased]` in every code PR.
- Conversation log: update `docs/conversation_log.md` at end of every AI session.

## OpenSpec governance

This project uses [OpenSpec](https://github.com/Fission-AI/OpenSpec) for spec-driven development.

- **Before implementing a feature**, check if a spec exists in `openspec/changes/` or `openspec/specs/`.
- If no spec exists, run `/opsx:propose <feature-name>` first.
- Implement with `/opsx:apply`, archive with `/opsx:archive`.
- System specs live in `openspec/specs/` (api, rag, data, infra).
- Active changes live in `openspec/changes/`, archived in `openspec/changes/archive/`.

## Claude-specific tools

- OpenSpec slash commands: `.claude/commands/opsx/{propose,apply,archive,explore}.md`
- OpenSpec skills: `.claude/skills/openspec-{propose,apply-change,archive-change,explore}/SKILL.md`
- Settings: `.claude/settings.local.json`

## Key commands

```bash
# Tests
cd backend && pytest tests/ -v
cd backend && pytest tests/ --cov=app --cov-report=term-missing --cov-fail-under=80

# Lint & format
ruff check backend/app
ruff format backend/app

# Type check
mypy backend/app

# Docker
docker compose up --build
```

## Key references

| File | Purpose |
|------|---------|
| `AGENTS.md` | All project rules (architecture, DI, testing, security, git) |
| `openspec/config.yaml` | OpenSpec project context and artifact rules |
| `openspec/specs/` | System specs (api, rag, data, infra) |
| `docs/conversation_log.md` | AI session audit trail |
| `docs/PLAN_OPENSPEC_ADOPTION.md` | OpenSpec adoption plan (phases 0-3 complete) |
| `.github/workflows/ci.yml` | CI pipeline (lint, typecheck, tests + 80% coverage) |
