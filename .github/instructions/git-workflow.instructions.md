---
description: "Use when creating branches, writing commit messages, opening PRs, or reviewing git workflow. Covers branch naming, conventional commits, PR requirements, CHANGELOG update rules, and what must never be committed."
---

# Git Workflow

## Branching Strategy

This project uses a **simplified GitFlow** with two permanent branches:

```
main      → production environment (Azure, stable)
develop   → staging/integration environment (pre-production)
```

### Flow diagram

```
feature/NNN  ──┐
fix/NNN      ──┼──► develop ──► release/vX.Y.Z ──► main  (tag vX.Y.Z)
refactor/NNN ──┘                                      │
                                                       └──► hotfix/NNN ──► main + develop
```

### Rules per branch

| Branch | Purpose | Who merges | Direct push |
|--------|---------|-----------|-------------|
| `main` | Production — always deployable | Tech lead via PR from `release/*` or `hotfix/*` | ❌ Never |
| `develop` | Integration — staging deploy on every merge | Any dev via PR | ❌ Never |
| `feature/NNN-*` | New functionality | Self via PR → `develop` | ✅ Own branch |
| `fix/NNN-*` | Bug fixes (non-urgent) | Self via PR → `develop` | ✅ Own branch |
| `hotfix/NNN-*` | Urgent production fix | Tech lead via PR → `main` + back-merge to `develop` | ✅ Own branch |
| `release/vX.Y.Z` | Release stabilization | Tech lead via PR → `main` | ✅ Own branch |
| `chore/*` | Tooling, deps, config (no code) | Self via PR → `develop` | ✅ Own branch |

---

## Branch Naming

```
feature/NNN-short-description     # New functionality  (base: develop)
fix/NNN-short-description         # Bug fixes          (base: develop)
hotfix/NNN-short-description      # Urgent prod fix    (base: main)
release/vX.Y.Z                    # Release cut        (base: develop)
refactor/NNN-short-description    # Restructure        (base: develop)
test/NNN-short-description        # Tests only         (base: develop)
chore/short-description           # Non-code changes   (base: develop)
```

- `NNN` = zero-padded sequence number (001, 002, ...)
- Use kebab-case, lowercase, no spaces
- Examples:
  - `feature/001-metadata-filtering-rag`
  - `fix/002-postgres-connection-timeout`
  - `hotfix/003-embedding-null-pointer`
  - `release/v1.1.0`
  - `chore/update-requirements`

---

## Environment Promotion

```
feature/* ──PR──► develop  →  auto-deploy to STAGING
                    │
                    └── manual cut ──► release/vX.Y.Z ──PR──► main  →  auto-deploy to PRODUCTION
                                                                 │
                                                              git tag vX.Y.Z
```

- **Staging** deploys automatically on every merge to `develop`
- **Production** deploys only from `main`, only after all CI checks pass
- Never deploy directly from a feature branch
- A `release/*` branch is the only path from `develop` to `main` (except `hotfix/*`)

### Branch protection rules (configure manually in GitHub)

Go to **Settings → Branches → Add rule** for each:

**`main`:**
- Require PR before merging
- Required status checks: `lint`, `typecheck`, `test`
- Require linear history (no merge commits)
- Restrict pushes — only tech lead / admins

**`develop`:**
- Require PR before merging
- Required status checks: `lint`, `typecheck`, `test`
- Allow squash merging only

---

## Conventional Commits

```
feat: add metadata filtering to embedding search
fix: handle psycopg2 connection timeout on retry
test: add unit tests for decode_source normalization
chore: update ruff to 0.4.x
docs: document multi-source pattern in python-modules guide
refactor: extract get_connection into shared helper
perf: add HNSW index to reduce similarity search latency
```

Format: `<type>: <imperative present tense description>`

| Type | When |
|------|------|
| `feat` | New functionality |
| `fix` | Bug fix |
| `test` | Adding or updating tests |
| `chore` | Maintenance, dependencies, tooling |
| `docs` | Documentation only |
| `refactor` | Restructure without behavior change |
| `perf` | Performance improvement |

---

## Pull Request Rules

- PRs to `develop`: any team member can review and approve
- PRs to `main` (`release/*` or `hotfix/*`): tech lead approval required

**PR checklist before requesting review:**

- [ ] Tests pass: `pytest tests/ -v`
- [ ] Coverage ≥ 80%: `pytest tests/ --cov=python_modules --cov-report=term-missing`
- [ ] Linter passes: `ruff check python_modules/ app.py`
- [ ] Formatter applied: `ruff format python_modules/ app.py`
- [ ] No `.env` file included
- [ ] No hardcoded credentials or API keys
- [ ] No `*.pyc`, `*.db`, or generated embeddings committed
- [ ] `.env.example` updated if new env vars added
- [ ] `CHANGELOG.md` updated under `## [Unreleased]` (skip only for docs/chore with justification)
- [ ] `docs/conversation_log.md` updated if request originated from an AI-assisted session

---

## What Must NEVER Be Committed

```
.env
*.db
*.db-journal
data/events/
data/lineups/
data/matches/
data/openai/
__pycache__/
*.pyc
```

These are in `.gitignore`. If you find yourself about to `git add` any of these, stop.

---

## CI / CD Checks (GitHub Actions)

| Trigger | Workflow | Jobs |
|---------|----------|------|
| PR → `develop` or `main` | `ci.yml` | lint, typecheck, test (coverage ≥ 80%) |
| Push to `develop` | `cd.yml` | deploy to staging |
| Push to `main` | `cd.yml` | deploy to production |

PRs cannot be merged until all CI checks are green.

---

## Commit Hygiene

- One logical change per commit — do not mix features with test additions
- Commit tests in the same commit as the implementation they cover
- Squash WIP commits before opening a PR
- Write commit message bodies to explain the *why*, not the *what*
- On merge to `develop`: use **squash merge** (clean history)
- On merge to `main`: use **merge commit** with version tag
