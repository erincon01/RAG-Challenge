---
name: changelog
description: Update CHANGELOG.md with recent changes following Keep a Changelog format. Use this when adding features, fixing bugs, or before creating a release.
---

# Changelog

Update CHANGELOG.md following Keep a Changelog format.

## When to use this skill

- After implementing a feature or fix (before creating PR)
- After merging multiple OpenSpec changes
- Before creating a release tag

## Format

Follow [Keep a Changelog](https://keepachangelog.com/en/1.1.0/) format:

```markdown
## [Unreleased]

### Added
- New features, capabilities, endpoints

### Changed
- Modifications to existing behavior, refactors

### Fixed
- Bug fixes, corrections

### Removed
- Removed features, deprecated code

### Security
- Security hardening, vulnerability fixes
```

## Procedure

### Adding entries for a PR

1. Read the current `CHANGELOG.md`
2. Add entry under `## [Unreleased]` in the appropriate section
3. Use concise descriptions referencing the PR number if available
4. Group related changes together

Example:
```markdown
### Added
- Token budget guard for RAG pipeline — truncates context when over budget (#19)
- `CORS_ORIGINS` env var for configurable CORS origins (#16)

### Changed
- DataExplorerService refactored to use Repository Pattern (#17)

### Security
- Replaced `allow_origins=["*"]` with configurable CORS origins (#16)
```

### Creating a release

When the user wants to tag a release:

1. Move `[Unreleased]` content to a new version section `[X.Y.Z] - YYYY-MM-DD`
2. Create empty `[Unreleased]` section
3. Update version in `backend/app/main.py`, `README.md`, `PROJECT_STATUS.md`
4. Versioning:
   - **MAJOR**: breaking API changes
   - **MINOR**: new features, backwards-compatible
   - **PATCH**: bug fixes

## Rules

- ALWAYS write entries in English
- ALWAYS include PR number when available: `(#NN)`
- ALWAYS use ISO dates (YYYY-MM-DD)
- NEVER remove existing entries
- NEVER skip CHANGELOG update in code PRs (docs-only PRs may skip with justification)
- Group entries by type (Added, Changed, Fixed, etc.) — not by PR or date
