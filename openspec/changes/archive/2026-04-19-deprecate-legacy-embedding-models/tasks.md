## 1. Domain layer

- [x] 1.1 Add deprecation comments to `EmbeddingModel.ADA_002` and `EmbeddingModel.T3_LARGE` in `backend/app/domain/entities.py`

## 2. Core layer

- [x] 2.1 Update `SOURCE_CAPABILITIES` in `backend/app/core/capabilities.py` to list only `text-embedding-3-small` for both postgres and sqlserver

## 3. Service layer

- [x] 3.1 Update default embedding models in `backend/app/services/ingestion_service.py` to use only `text-embedding-3-small` for both sources

## 4. Tests

- [x] 4.1 Update tests that assert on the number of embedding models or reference deprecated models
- [x] 4.2 Run full test suite: `cd backend && pytest tests/ -v` (530 passed)
- [x] 4.3 Run E2E tests to verify capabilities UI: `cd frontend/webapp && npx playwright test dashboard.spec.ts embeddings.spec.ts chat.spec.ts` (9 passed)

## 5. Verification

- [x] 5.1 Verify `GET /api/v1/capabilities` returns only t3-small per source
- [x] 5.2 Update CHANGELOG.md under `## [Unreleased]`
