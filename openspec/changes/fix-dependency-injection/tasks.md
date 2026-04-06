## 1. API layer

- [x] 1.1 Refactor `health.py:readiness_check()` to accept repositories via `Depends()` instead of instantiating `PostgresEventRepository()` / `SQLServerEventRepository()`
- [x] 1.2 Refactor `capabilities.py:get_sources_status()` with the same pattern
- [x] 1.3 Remove direct imports of concrete repository classes from both handlers

## 2. Tests (TDD — write before implementation)

- [x] 2.1 Write unit test: `test_readiness_check_uses_injected_repos` — verify handler uses DI, not direct instantiation
- [x] 2.2 Write unit test: `test_sources_status_uses_injected_repos` — same for capabilities
- [x] 2.3 Update existing health/capabilities API tests to use `dependency_overrides` if they mock constructors
- [x] 2.4 Write unit test: `test_no_direct_repo_imports_in_handlers` — verify no concrete repo imports in health.py and capabilities.py
- [x] 2.5 Run full test suite and verify 80%+ coverage maintained
