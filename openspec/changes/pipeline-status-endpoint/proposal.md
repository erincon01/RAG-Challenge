## Why

The Operations page shows match IDs but not their pipeline state. The user can't see which matches have been downloaded, loaded, aggregated, summarized, or embedded. They run steps blindly. Need a per-match pipeline status endpoint and a UI table with checkboxes to select which matches to process at each step.

## What Changes

- New backend endpoint `GET /ingestion/pipeline-status?source=X` returning per-match pipeline state
- New frontend match status table in Operations with checkboxes for per-step selection
- Each step's action button uses the selected matches from the table, not from catalog selection

## Capabilities

### New Capabilities
_(none)_

### Modified Capabilities
- `api`: new ingestion endpoint for pipeline status per match

## Impact

- **Backend**: new endpoint in `app/api/v1/ingestion.py`, new service method, new repository queries
- **Frontend**: Operations page gets a match status table with checkboxes
- **Affected layers**: API, Service, Repository, Frontend
- **Test impact**: new backend tests for endpoint, updated E2E tests
