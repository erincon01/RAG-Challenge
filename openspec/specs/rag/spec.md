# RAG Pipeline Specification

**Domain:** rag  
**Status:** Current system (brownfield baseline)  
**Last updated:** 2026-04-02  
**ADR references:** [ADR-001 Layered Architecture](../../../docs/adr/ADR-001-layered-architecture.md)

---

## Overview

The RAG (Retrieval Augmented Generation) pipeline answers natural language questions about
football matches by combining vector similarity search with LLM generation. The pipeline
is implemented in `SearchService.search_and_chat()` and orchestrates repositories and the
OpenAI adapter.

---

## Pipeline Steps

```
┌──────────────┐    ┌──────────────┐    ┌──────────────┐
│  1. NORMALIZE │───▶│  2. EMBED    │───▶│  3. SEARCH   │
│     QUERY     │    │    QUERY     │    │   (vector)   │
└──────────────┘    └──────────────┘    └──────┬───────┘
                                               │
                                        ┌──────▼───────┐    ┌──────────────┐
                                        │  4. BUILD    │───▶│  5. GENERATE │
                                        │    CONTEXT   │    │    ANSWER    │
                                        └──────────────┘    └──────────────┘
```

### Step 1 — Normalize Query

- **Input:** `query` (str), `language` (str)
- **Output:** `normalized_question` (str, English)
- **Behavior:**
  - Given `language == "english"`, When normalization runs, Then return query unchanged.
  - Given `language != "english"`, When normalization runs, Then translate to English via `OpenAIAdapter.translate_to_english()`.
  - Given translation fails, When normalization runs, Then return original query as fallback.

### Step 2 — Generate Embedding

- **Input:** `normalized_question` (str), `embedding_model` (EmbeddingModel enum)
- **Output:** `query_embedding` (List[float])
- **Behavior:**
  - When an embedding is requested, Then call `OpenAIAdapter.create_embedding(text, model)`.
  - Given embedding generation fails after 5 retries, Then raise `EmbeddingGenerationError`.

**Supported embedding models:**

| Model | Alias | Dimensions | Sources |
|-------|-------|------------|---------|
| text-embedding-ada-002 | ADA_002 | 1536 | postgres, sqlserver |
| text-embedding-3-small | T3_SMALL | 1536 | postgres, sqlserver |
| text-embedding-3-large | T3_LARGE | 3072 | postgres only |

### Step 3 — Vector Search

- **Input:** `SearchRequest`, `query_embedding`
- **Output:** `List[SearchResult]` ranked by similarity score
- **Behavior:**
  - When search is invoked, Then call `EventRepository.search_by_embedding(search_request, query_embedding)`.
  - The repository selects the distance function based on `search_algorithm`.
  - Given `top_n = N`, Then return at most N results ordered by descending similarity.

**Supported search algorithms:**

| Algorithm | Postgres | SQL Server |
|-----------|----------|------------|
| cosine | YES (`<=>`) | YES |
| inner_product | YES (`<#>`) | YES |
| l2_euclidean | YES (`<->`) | YES |
| l1_manhattan | YES | NO |

### Step 4 — Build Context

- **Input:** `search_results`, `match_info` (optional), `include_match_info` flag
- **Output:** Context string for LLM prompt
- **Behavior:**
  - Given `include_match_info == true`, When context is built, Then fetch Match entity from `MatchRepository.get_by_id()`.
  - Context string MUST include:
    - Competition name, season name.
    - Match date, result (home_score - away_score).
    - For each search result: `time_description` + `summary`.

### Step 5 — Generate Answer

- **Input:** Context string, question, system_message, temperature, max_output_tokens
- **Output:** `answer` (str)
- **Behavior:**
  - When answer generation is invoked, Then build LLM messages array with system + user roles.
  - **System message (default):** "Answer the QUESTION using EVENTS or GAME_RESULT above..."
  - **User message:** `{context}\n\nQUESTION: {question}`
  - Then call `OpenAIAdapter.create_chat_completion(messages, model, temperature, max_tokens)`.
  - Given LLM call fails after 5 retries, Then return "ERROR: Failed to generate answer. Please try again."

---

## Token Management

| Parameter | Default | Scope | Enforced? |
|-----------|---------|-------|-----------|
| `max_input_tokens` | 10000 | Context window guidance | NO (not enforced in code) |
| `max_output_tokens` | 5000 | LLM `max_tokens` parameter | YES (passed to OpenAI API) |
| `temperature` | 0.1 | LLM sampling | YES (validated 0.0-2.0 in domain) |
| `top_n` | 10 | Number of search results | YES (validated 1-100 in domain) |

**Known gap:** `max_input_tokens` parameter exists in `SearchRequest` but is NOT enforced.
The context passed to the LLM may exceed this value if many search results are returned.

---

## Retry Strategy

All OpenAI API calls use the same retry logic via `OpenAIAdapter._call_with_retry()`:

| Setting | Value |
|---------|-------|
| Max retries | 5 |
| Initial backoff | 1 second |
| Backoff formula | `min(1s * 2^attempt, 60s)` |
| Exceptions handled | `RateLimitError`, `APIError` |
| Final failure | `EmbeddingGenerationError` |

---

## OpenAI Adapter

### Provider Selection

| Provider | Client | Authentication |
|----------|--------|---------------|
| `azure` (default) | `AzureOpenAI(endpoint, api_key, api_version="2024-06-01")` | Endpoint + Key |
| `openai` | `OpenAI(api_key)` | API Key only |

### Methods

| Method | Purpose | Retry |
|--------|---------|-------|
| `create_embedding(text, model)` | Single embedding generation | YES (5x) |
| `create_embeddings_batch(texts, model)` | Batch embedding (chunks of 50) | YES per chunk |
| `create_chat_completion(messages, model, temperature, max_tokens)` | LLM response generation | YES (5x) |
| `translate_to_english(text, source_language)` | Translation via LLM prompt | YES (via chat completion) |

---

## Response Contract

```
ChatResponse {
  question: str              # Original user query
  normalized_question: str   # English-translated query
  answer: str                # LLM-generated answer
  search_results: List[SearchResult {
    event: EventDetail       # Matched event data
    similarity_score: float  # Distance metric result
    rank: int                # Position in results
  }]
  match_info: Optional[Match] # Full match entity (if include_match_info)
  metadata: Dict {
    match_id: int
    language: str
    search_algorithm: str
    embedding_model: str
    results_count: int
  }
}
```
