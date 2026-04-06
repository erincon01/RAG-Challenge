## 1. Configuration

- [x] 1.1 Add `cors_origins` field to `Settings` class in `config/settings.py` with `CORS_ORIGINS` env alias and comma-split validator
- [x] 1.2 Add `CORS_ORIGINS` to `.env.example` with default `http://localhost:5173,http://localhost:8000`
- [x] 1.3 Add `CORS_ORIGINS` to `.env.docker.example` with same default

## 2. API layer

- [x] 2.1 Update `backend/app/main.py` CORS middleware to read origins from `get_settings().cors_origins`

## 3. Tests (TDD — write before implementation)

- [x] 3.1 Write unit test: `test_cors_origins_parsed_from_env` — verify comma-separated string is split into list
- [x] 3.2 Write unit test: `test_cors_origins_default_when_unset` — verify default localhost origins
- [x] 3.3 Write unit test: `test_cors_origins_strips_whitespace` — verify whitespace trimming
- [x] 3.4 Write API test: `test_cors_allows_configured_origin` — verify `Access-Control-Allow-Origin` present for allowed origin
- [x] 3.5 Write API test: `test_cors_rejects_unknown_origin` — verify header absent for unknown origin
