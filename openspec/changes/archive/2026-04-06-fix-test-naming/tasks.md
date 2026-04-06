## 1. Test renames

- [x] 1.1 Rename tests in `backend/tests/api/test_health.py` to follow `test_<method>_<scenario>_<expected>`
- [x] 1.2 Rename tests in `backend/tests/api/test_events.py`
- [x] 1.3 Rename tests in `backend/tests/api/test_chat.py`
- [x] 1.4 Rename tests in `backend/tests/api/test_explorer_embeddings.py`
- [x] 1.5 Rename tests in `backend/tests/unit/test_domain.py`
- [x] 1.6 Rename tests in any other files with naming violations

## 2. Verification

- [x] 2.1 Run full test suite — all tests must pass with new names
- [x] 2.2 Verify no test uses fewer than 3 parts after `test_`
- [x] 2.3 Run coverage check — must remain ≥ 80%
