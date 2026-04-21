## Context

Operations page needs per-match pipeline visibility. Currently the user sees "6 selected" but no state per match.

## Goals / Non-Goals

**Goals:**
- Backend: one query per source returning per-match counts (events, aggregations, summaries, embeddings)
- Frontend: table showing match status with checkboxes, each step uses selected matches

**Non-Goals:**
- Listing downloaded files from disk (would need filesystem access from API — deferred)
- Per-step progress bars

## Decisions

### 1. Single query per source
One SQL query joins matches with aggregation counts. Returns all matches loaded in the DB for that source.

### 2. Checkboxes in the match table replace catalog selection for steps 2-5
Steps 2-5 operate on DB data, not catalog selection. The match table shows what's in the DB and lets the user pick.
Step 1 (Download) still uses catalog selection since data isn't in the DB yet.

## File change list

| File | Status |
|------|--------|
| `backend/app/api/v1/ingestion.py` | (modified) — new endpoint |
| `backend/app/services/ingestion_service.py` | (modified) — new method |
| `frontend/webapp/src/lib/api/client.ts` | (modified) — new API call |
| `frontend/webapp/src/lib/api/types.ts` | (modified) — new type |
| `frontend/webapp/src/pages/OperationsPage.tsx` | (modified) — match status table |
