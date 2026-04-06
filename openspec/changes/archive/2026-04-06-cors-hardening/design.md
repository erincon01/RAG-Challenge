## Context

The FastAPI backend currently configures CORS with `allow_origins=["*"]` in `backend/app/main.py:40`.
This allows any domain to make cross-origin requests, which is a security risk for production.
The project uses Pydantic Settings (`config/settings.py`) for all configuration, but CORS
origins are not yet managed there.

## Goals / Non-Goals

**Goals:**
- Make CORS origins configurable via environment variable (`CORS_ORIGINS`)
- Provide safe defaults for local development (`localhost:5173`, `localhost:8000`)
- Follow existing config pattern: Pydantic Settings → `.env` → `get_settings()`

**Non-Goals:**
- Per-route CORS configuration
- Dynamic CORS (runtime changes without restart)
- CORS preflight caching tuning

## Decisions

### 1. Config location: `config/settings.py` → `Settings` class

**Rationale:** All configuration lives in `config/settings.py` per project convention.
Adding a `cors_origins` field to the top-level `Settings` class keeps it consistent.

**Alternative considered:** Separate `CorsConfig` nested model — rejected because
this is a single field, not a config group.

### 2. Env var format: comma-separated string

```
CORS_ORIGINS=http://localhost:5173,http://localhost:8000
```

**Rationale:** Simple, no JSON parsing needed. Pydantic `field_validator` splits on commas.
Consistent with how other FastAPI projects handle this.

**Alternative considered:** JSON array (`["http://..."]`) — rejected, harder to set in
Docker Compose and `.env` files.

### 3. Default value: local dev origins

Default: `http://localhost:5173,http://localhost:8000`

**Rationale:** Matches current Docker Compose setup. Production MUST override via env var.
The `*` wildcard is never a default.

## File changes

| File | Action | Description |
|------|--------|-------------|
| `config/settings.py` | (modified) | Add `cors_origins` field with validator |
| `backend/app/main.py` | (modified) | Read CORS origins from `get_settings()` |
| `.env.example` | (modified) | Add `CORS_ORIGINS` variable |
| `.env.docker.example` | (modified) | Add `CORS_ORIGINS` variable |
| `backend/tests/unit/test_cors_config.py` | (new) | Unit test for CORS origins parsing |
| `backend/tests/api/test_cors_middleware.py` | (new) | API test for CORS headers |

## Risks / Trade-offs

- **[Risk]** Existing deployments without `CORS_ORIGINS` set → **Mitigation:** defaults to localhost origins, which is safe (rejects external requests)
- **[Risk]** Developers forget to set `CORS_ORIGINS` for non-localhost frontend → **Mitigation:** clear error in docs and `.env.example`

## Rollback strategy

Revert the commit. The only change is config-driven — no data migration, no schema changes.
