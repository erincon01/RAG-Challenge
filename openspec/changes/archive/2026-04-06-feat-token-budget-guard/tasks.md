## 1. Dependencies

- [x] 1.1 Add `tiktoken` to `backend/requirements.txt`
- [x] 1.2 Verify `tiktoken` installs correctly in the devcontainer

## 2. Service layer

- [x] 2.1 Add `count_tokens(text: str, model: str) -> int` helper function in `search_service.py`
- [x] 2.2 Add token budget guard in `_generate_answer()` before the LLM call: count system_message + context + question tokens
- [x] 2.3 Implement truncation loop: iteratively remove lowest-ranked search result until tokens fit
- [x] 2.4 Handle edge case: if zero results remain after truncation, return error without calling LLM
- [x] 2.5 Add `input_tokens`, `max_input_tokens`, `results_truncated` to response metadata

## 3. Tests (TDD — write before implementation)

- [x] 3.1 Write unit test: `test_count_tokens_returns_positive_int` — verify tiktoken integration
- [x] 3.2 Write unit test: `test_generate_answer_within_budget_includes_all_results` — no truncation when under budget
- [x] 3.3 Write unit test: `test_generate_answer_over_budget_truncates_lowest_ranked` — verify truncation order
- [x] 3.4 Write unit test: `test_generate_answer_question_exceeds_budget_returns_error` — edge case
- [x] 3.5 Write unit test: `test_response_metadata_includes_token_usage` — verify metadata fields
- [x] 3.6 Run full test suite and verify 80%+ coverage maintained
