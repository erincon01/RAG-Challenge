## Approach

Add a token budget guard in `SearchService._generate_answer()` that counts tokens before
calling the LLM and truncates context if needed. Uses `tiktoken` for accurate token counting.

### Strategy

1. **Add `tiktoken` dependency** — lightweight, offline tokenizer for OpenAI models.
2. **Create a token counting utility** — `count_tokens(text, model)` helper in search_service
   or a small utility module.
3. **Budget check before LLM call** — count tokens for system_message + context + question.
   If total exceeds `max_input_tokens`, iteratively drop the lowest-ranked search result
   from context until it fits.
4. **Add token usage to response metadata** — report `input_tokens`, `budget_limit`,
   `results_truncated` in the response metadata dict.

### Decision: Where to truncate

**Option A:** Truncate the context string by character count (fast but inaccurate).
**Option B:** Iteratively remove lowest-ranked search results until token count fits.

**Choice: Option B** — removing whole results preserves coherent context. Each result
is a discrete event summary, so dropping the least relevant one is semantically clean.

### Decision: Token counting approach

**Option A:** Use `tiktoken` library (accurate, offline, fast).
**Option B:** Estimate ~4 chars per token (rough, no dependency).

**Choice: Option A** — `tiktoken` is the standard for OpenAI models, adds <1MB dependency,
and gives exact counts. The budget guard is useless if counts are wrong.

## File changes

| File | Change |
|------|--------|
| `backend/requirements.txt` | (modified) Add `tiktoken` |
| `backend/app/services/search_service.py` | (modified) Add token counting + budget guard in `_generate_answer()` |
| `backend/app/domain/entities.py` | (modified) Add `token_usage` field to metadata if needed |
| `backend/tests/unit/test_search_service.py` | (modified) Add token budget tests |

## Rollback strategy

Revert the commit and remove `tiktoken` from requirements. No data migration, no env changes.

## Risks

- **[Risk]** `tiktoken` model name mismatch with Azure OpenAI deployment →
  **Mitigation:** Use `tiktoken.encoding_for_model()` with fallback to `cl100k_base` (covers GPT-4 family)
- **[Risk]** Token counting adds latency →
  **Mitigation:** `tiktoken` encoding is ~1ms for typical context sizes; negligible vs LLM API call
