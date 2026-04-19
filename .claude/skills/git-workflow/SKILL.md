---
name: git-workflow
description: Git workflow for RAG-Challenge. Branch model with develop (integration) and main (production). Use this when creating branches, committing, pushing, or opening PRs.
---

# Git Workflow

Git workflow for RAG-Challenge. Uses a **simplified GitFlow** with `develop` (integration) and `main` (production).

## Rules

- **Never push directly to `main` or `develop`** — all changes via feature branch + PR
- **Conventional Commits** format in English: `type(scope): description`
- **No AI attribution** in commits or PRs (`Co-Authored-By`, `Generated with`, etc.)
- **Never force push**
- **Always update CHANGELOG.md** under `## [Unreleased]` in code PRs

## Branch naming

```
feature/NNN-description   # New functionality (from develop)
fix/NNN-description       # Bug fixes (from develop)
hotfix/NNN-description    # Urgent production fixes (from main)
chore/description         # Maintenance, tooling, config (from develop)
refactor/description      # Restructure without behavior change (from develop)
```

`NNN` = zero-padded sequence number (e.g., `016`, `040`). Get next available from repo.

## Commit types

| Type | When |
|------|------|
| `feat(scope)` | New functionality |
| `fix(scope)` | Bug fix |
| `docs` | Documentation only |
| `test(scope)` | Adding or updating tests |
| `chore(scope)` | Maintenance, CI/CD, dependencies |
| `refactor(scope)` | Restructure without behavior change |
| `style` | Formatting only |
| `perf(scope)` | Performance improvement |

## Workflow for a feature/fix

```bash
# 1. Start from develop
git checkout develop && git pull origin develop

# 2. Create branch
git checkout -b feature/NNN-description

# 3. Work (TDD: tests first, then implementation)
# ... make changes ...

# 4. Stage and commit
git add <specific-files>
git commit -m "feat(scope): description"

# 5. Push
git push -u origin feature/NNN-description

# 6. Create PR → develop
gh pr create --base develop --title "feat(scope): description" --body "..."

# 7. After CI green + review → merge (squash if many commits)
# 8. Delete branch after merge
```

## OpenSpec integration

For non-trivial changes, use the OpenSpec workflow first:

1. `/opsx:propose <change-name>` — creates proposal, design, specs, tasks
2. Create branch: `git checkout -b feature/NNN-description`
3. `/opsx:apply` — implements tasks with TDD
4. Push, PR, merge
5. `/opsx:archive` — archives completed change

## PR checklist

- [ ] Branch naming follows `<type>/NNN-description`
- [ ] Conventional Commits in English
- [ ] Tests pass: `cd backend && pytest tests/ -v`
- [ ] Coverage >= 80%
- [ ] Lint clean: `ruff check backend/app && ruff format --check backend/app`
- [ ] Type check: `mypy backend/app`
- [ ] CHANGELOG.md updated under `## [Unreleased]`
- [ ] `docs/conversation_log.md` updated if AI-assisted session

## Releases

- PR `develop → main` with title `release: vX.Y.Z`
- Follow Semantic Versioning (MAJOR.MINOR.PATCH)
- Tag on main after merge: `git tag vX.Y.Z && git push origin vX.Y.Z`
- Promote `[Unreleased]` to `[X.Y.Z] - YYYY-MM-DD` in CHANGELOG
- Update version in `backend/app/main.py`, `README.md`, `PROJECT_STATUS.md`
