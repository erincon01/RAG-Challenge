## Why

The backend uses `allow_origins=["*"]` in CORS middleware (`app/main.py:40`), which allows
any domain to make cross-origin requests. This is a security risk flagged in `AGENTS.md`
(Security rules: "No `allow_origins=["*"]` in production"). The TODO comment in the code
confirms this was always intended as temporary. Fixing it now because governance is in place
and the project is approaching production readiness.

## What Changes

- Replace hardcoded `allow_origins=["*"]` with a configurable list from `CORS_ORIGINS` env var
- Add `CORS_ORIGINS` to `config/settings.py` (Pydantic Settings) with sensible defaults for local dev
- Update `.env.example` and `.env.docker.example` with the new variable
- Backwards-compatible: defaults to `http://localhost:5173,http://localhost:8000` (current dev setup)

## Capabilities

### New Capabilities

(none — this is a security hardening of existing behavior)

### Modified Capabilities

- `infra`: CORS configuration moves from hardcoded to environment-driven via Pydantic Settings

## Impact

- **Affected layers:** Core (config), API (main.py middleware setup)
- **Affected files:** `config/settings.py`, `backend/app/main.py`, `.env.example`, `.env.docker.example`
- **Test impact:** Unit test for CORS origins parsing; API test to verify middleware rejects unknown origins
- **Backwards compatibility:** Fully compatible — defaults match current dev behavior
- **Breaking:** None. Production deployments must set `CORS_ORIGINS` env var
