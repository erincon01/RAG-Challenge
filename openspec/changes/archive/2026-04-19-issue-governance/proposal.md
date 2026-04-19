## Why

The project has no `CONTRIBUTING.md`, no issue templates, and uses only default GitHub labels. Contributors don't know how to pick up issues, what workflow to follow, or how OpenSpec integrates with the issue lifecycle. This creates friction for onboarding and makes the project less accessible. Addresses issue #42.

## What Changes

- Create `CONTRIBUTING.md` with step-by-step contributor guide
- Create GitHub issue templates (bug report, feature request)
- Add project-specific labels aligned with the codebase (area:backend, area:frontend, area:infra, area:docs, needs-spec)
- Document the issue → OpenSpec → PR → archive workflow

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
_(none — governance/config only, no behavior changes)_

## Impact

- **Root**: `CONTRIBUTING.md` (new)
- **GitHub config**: `.github/ISSUE_TEMPLATE/` (new)
- **GitHub labels**: created via `gh label create`
- **Backward compatibility**: fully backward-compatible — adds governance artifacts
- **Affected layers**: none
- **Test impact**: none
