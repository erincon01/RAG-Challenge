## 1. Core (DI Wiring)

- [x] 1.1 Add `get_ingestion_service()` provider to `app/core/dependencies.py` — returns `IngestionService()`
- [x] 1.2 Add `get_statsbomb_service()` provider to `app/core/dependencies.py` — returns `StatsBombService()`
- [x] 1.3 Add `get_data_explorer_service()` provider to `app/core/dependencies.py` — returns `DataExplorerService()`
- [x] 1.4 Add type aliases `IngestionSvc`, `StatsBombSvc`, `ExplorerSvc` in `app/core/dependencies.py`

## 2. Service Layer

- [x] 2.1 Update `IngestionService.__init__` to accept `statsbomb: StatsBombService | None = None`
- [x] 2.2 Set `self.statsbomb = statsbomb or StatsBombService()` (preserves current default behavior)

## 3. API Layer

- [x] 3.1 Remove `_service = IngestionService()` from `app/api/v1/ingestion.py`; inject `IngestionSvc` in each handler
- [x] 3.2 Remove `_service = IngestionService()` from `app/api/v1/embeddings.py`; inject `IngestionSvc` in handler
- [x] 3.3 Remove `_service = StatsBombService()` from `app/api/v1/statsbomb.py`; inject `StatsBombSvc` in each handler
- [x] 3.4 Remove `_service = DataExplorerService()` from `app/api/v1/explorer.py`; inject `ExplorerSvc` in each handler

## 4. Tests

- [x] 4.1 Update `tests/api/test_statsbomb.py` — replace any `patch` of `_service` with `app.dependency_overrides[get_statsbomb_service]`
- [x] 4.2 Add/verify tests for ingestion routes using `app.dependency_overrides[get_ingestion_service]`
- [x] 4.3 Add/verify tests for explorer routes using `app.dependency_overrides[get_data_explorer_service]`
- [x] 4.4 Confirm all test teardowns call `app.dependency_overrides.clear()`
- [x] 4.5 Run `pytest --cov --cov-fail-under=80` — all tests green, coverage ≥ 80%
