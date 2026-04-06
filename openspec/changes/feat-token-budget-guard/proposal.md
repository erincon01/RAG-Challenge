## Why

The RAG pipeline accepts `max_input_tokens` (default 10,000) in `SearchRequest` but never
enforces it. The context string built from search results can grow unbounded — if many events
match, the context + system prompt + question can exceed the model's context window, causing
API errors or silently truncated responses. The RAG spec (rag/spec.md:100-110) documents this
gap. Adding a token budget guard prevents overflows and gives predictable behavior.

## What Changes

- Add token counting before the LLM call in `SearchService._generate_answer()`
- Use `tiktoken` to count tokens in context + system message + question
- If total input tokens exceed `max_input_tokens`, truncate search results (drop lowest-ranked)
  until the budget fits
- Add token usage metadata to the response (input_tokens, output_tokens, budget_used)
- Backwards-compatible: default budget (10,000) matches current `SearchRequest` default

## Capabilities

### New Capabilities

(none — this enforces an existing but unimplemented parameter)

### Modified Capabilities

- `rag`: Pipeline step 5 (generate) gains token budget enforcement with truncation strategy

## Impact

- **Affected layers:** Service (`search_service.py`), Domain (`entities.py` metadata)
- **Affected files:** 2 production files, 1 new dependency (`tiktoken`)
- **API contract:** Response gains optional `token_usage` in metadata (additive, non-breaking)
- **Test impact:** New unit tests for token counting and truncation logic
- **Backwards compatibility:** Fully compatible — existing behavior unchanged for queries under budget
- **Breaking:** None. Queries that previously overflowed silently will now be truncated gracefully
