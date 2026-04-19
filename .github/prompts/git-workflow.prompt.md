---
description: Git workflow — create branches, commit, push, open PRs following project conventions
---

Follow the RAG-Challenge git workflow:

- **Branch from `develop`**: `feature/NNN-desc`, `fix/NNN-desc`, `chore/desc`
- **Conventional Commits** in English: `type(scope): description`
- **No AI attribution** (`Co-Authored-By`, `Generated with`, etc.)
- **PR to `develop`**, never push directly to `main` or `develop`
- **Update CHANGELOG.md** under `[Unreleased]` in every code PR
- **Update `docs/conversation_log.md`** if AI-assisted session

See `.github/instructions/git-workflow.instructions.md` for full rules.
See `AGENTS.md` for project conventions.
