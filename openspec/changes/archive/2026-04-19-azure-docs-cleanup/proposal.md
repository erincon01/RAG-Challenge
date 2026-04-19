## Why

Documentation still references "Azure SQL Server", "Azure PostgreSQL", "Azure OpenAI" as requirements throughout `docs/app-use-case.md`, `docs/architecture.md`, and `docs/semantic-search.md`. The project migrated to portable Docker infrastructure (ADR-003) and supports both Azure-hosted and local deployments. Azure references mislead developers into thinking Azure is required. The large historical section in `app-use-case.md` (lines 113-307) mixes legacy Streamlit/Azure content with current architecture. Addresses issue #37.

## What Changes

- Move the historical Azure/Streamlit section from `docs/app-use-case.md` to `docs/archive/`
- Update `docs/app-use-case.md` to reflect current FastAPI + React architecture only
- Update `docs/architecture.md` to replace "Azure OpenAI" with "OpenAI / Azure OpenAI"
- Update `docs/semantic-search.md` if Azure-specific references exist
- Document Azure as an **optional deployment target**, not a requirement

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
_(none — documentation only, no behavior changes)_

## Impact

- **Docs**: `docs/app-use-case.md`, `docs/architecture.md`, `docs/semantic-search.md` (modified)
- **Docs archive**: `docs/archive/legacy-azure-streamlit-setup.md` (new — moved content)
- **Backward compatibility**: fully backward-compatible — documentation only
- **Affected layers**: none (docs only)
- **Test impact**: none
