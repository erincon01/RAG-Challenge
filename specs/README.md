# Feature Specifications (Spec-Driven Development)

This directory contains feature-level specifications managed through the [spec-kit](https://github.com/github/spec-kit) workflow.

## Structure

Each feature lives in its own numbered subdirectory:

```
specs/
├── 001-structured-logging/
│   ├── spec.md          # WHAT and WHY (user stories, requirements, acceptance criteria)
│   ├── plan.md          # HOW (technical approach, constitution check, architecture)
│   ├── tasks.md         # Work breakdown (phased, parallelizable tasks)
│   ├── checklist.md     # Quality gates and validation
│   ├── research.md      # Technical research (optional)
│   ├── data-model.md    # Entity definitions (optional)
│   ├── quickstart.md    # Quick setup guide (optional)
│   └── contracts/       # API contracts (optional)
├── 002-query-caching/
│   └── ...
└── README.md            # This file
```

## Workflow

The SDD (Spec-Driven Development) workflow follows this sequence:

```
/speckit.clarify    → Resolve ambiguities in the feature request
/speckit.specify    → Create spec.md (user stories, requirements)
/speckit.plan       → Create plan.md (technical approach + Constitution Check)
/speckit.tasks      → Create tasks.md (implementation breakdown)
/speckit.analyze    → Verify consistency across all artifacts
/speckit.implement  → Implement following tasks.md
/speckit.checklist  → Validate quality gates
```

## Creating a New Feature

### Option 1: PowerShell (Windows)

```powershell
.specify/scripts/powershell/create-new-feature.ps1 'Add structured logging with request correlation'
```

### Option 2: Bash (Linux/macOS/CI)

```bash
.specify/scripts/bash/create-new-feature.sh 'Add structured logging with request correlation'
```

### Option 3: Manual

1. Create a branch: `git checkout -b feature/NNN-short-name`
2. Create the directory: `mkdir specs/NNN-short-name/`
3. Copy the spec template: `cp .specify/templates/spec-template.md specs/NNN-short-name/spec.md`

## Naming Convention

- Sequential numbering: `001-`, `002-`, `003-`...
- Kebab-case, lowercase
- 2-4 meaningful words describing the feature
- Examples: `001-structured-logging`, `002-query-caching`, `003-frontend-vitest`

## Rules

- **Commit specs before code** — spec.md and plan.md are reviewed artifacts
- **Constitution Check is mandatory** — plan.md must include verification against all 10 principles
- **Each feature is independent** — specs should not cross-reference other feature specs
- **Specs are living documents** — update them if implementation diverges, then re-run `/speckit.analyze`
