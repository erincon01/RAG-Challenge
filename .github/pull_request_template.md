## Description

<!-- Describe what this PR does and why. Link to the OpenSpec change or spec if applicable. -->

Closes #<!-- issue number -->

---

## Type of change

- [ ] `feat` — new functionality
- [ ] `fix` — bug fix
- [ ] `test` — adding or updating tests
- [ ] `refactor` — restructure, no behavior change
- [ ] `chore` — dependencies, tooling, config
- [ ] `docs` — documentation only

---

## PR Checklist

### Code quality
- [ ] Tests pass: `cd backend && pytest tests/ -v`
- [ ] Coverage ≥ 80%: `cd backend && pytest tests/ --cov=app --cov-report=term-missing`
- [ ] Linter passes: `ruff check backend/app`
- [ ] Formatter applied: `ruff format backend/app`
- [ ] Type check passes: `mypy backend/app --ignore-missing-imports`
- [ ] Type hints on all new public functions

### Security
- [ ] No `.env` file included
- [ ] No hardcoded credentials, API keys, or connection strings
- [ ] No `*.pyc`, `*.db`, or generated embeddings committed
- [ ] `.env.example` updated if new env vars added

### Documentation
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` *(skip only for pure docs/chore — justify below)*
- [ ] `docs/conversation_log.md` updated if this PR originated from an AI-assisted session

### OpenSpec (if applicable)
- [ ] OpenSpec specs reviewed and accurate (`openspec/specs/`)
- [ ] Design matches implementation (`openspec/changes/`)
- [ ] Tasks marked complete (`tasks.md`)

---

## Architecture Check

<!-- MANDATORY: Verify each applicable principle from AGENTS.md -->

- [ ] **Layered arch**: api → services → repositories → domain flow respected
- [ ] **Repository**: all DB access through abstract repository methods
- [ ] **DI**: collaborators injected via `Depends()`, no direct instantiation in handlers
- [ ] **Config**: new env vars in `config/settings.py` → `.env.example` → `conftest.py`
- [ ] **Test-first**: failing test written before implementation
- [ ] **SQL safety**: all queries parameterized, no f-string SQL
- [ ] **Secrets**: no hardcoded credentials, `.env` gitignored

**N/A justification**: <!-- List any principles marked N/A and why -->

---

## CHANGELOG skip justification

<!-- If you did not update CHANGELOG.md, explain why here. Leave blank if you updated it. -->
