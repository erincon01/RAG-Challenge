## Context

The project uses OpenSpec for spec-driven development but has no documented contributor workflow. Issues are created ad-hoc, there are no templates, and default GitHub labels don't match the project structure.

## Goals / Non-Goals

**Goals:**
- Create a clear contributor guide (CONTRIBUTING.md)
- Add issue templates for bugs and features
- Add project-specific labels
- Document how OpenSpec integrates with the issue lifecycle

**Non-Goals:**
- Enforcing label requirements via GitHub Actions
- Setting up project boards or milestones
- Creating a governance spec in `openspec/specs/` (too meta)

## Decisions

### 1. CONTRIBUTING.md at repo root
Standard location. References AGENTS.md for detailed rules and openspec for workflow.

### 2. Two issue templates: bug and feature
Keep it simple. Both templates include fields for OpenSpec context (related spec, needs-spec flag).

### 3. Labels via gh CLI, not committed config
Labels are GitHub API state, not files in the repo. Create them via `gh label create` during implementation.

## File change list

| File | Status | Description |
|------|--------|-------------|
| `CONTRIBUTING.md` | (new) | Contributor guide |
| `.github/ISSUE_TEMPLATE/bug_report.md` | (new) | Bug report template |
| `.github/ISSUE_TEMPLATE/feature_request.md` | (new) | Feature request template |
| `CHANGELOG.md` | (modified) | Update Unreleased |

## Rollback strategy

Delete the new files. Remove labels via `gh label delete`. No code changes.
