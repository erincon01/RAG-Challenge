# Semantic Search

## Overview

The RAG-Challenge system uses **vector similarity search** to find the most relevant
match events for a given natural language question. Event summaries are pre-embedded
as vectors; at query time, the question is embedded with the same model and compared
against stored vectors using a distance function.

---

## Embedding Models

| Model | API Name | Dimensions | Availability | Notes |
|-------|----------|------------|-------------|-------|
| Ada 002 | `text-embedding-ada-002` | 1536 | Postgres, SQL Server | Legacy model, lower quality |
| 3-Small | `text-embedding-3-small` | 1536 | Postgres, SQL Server | **Recommended** — best cost/quality ratio |
| 3-Large | `text-embedding-3-large` | 3072 | Postgres only | Highest quality, double the dimensions |

**Default model for new features:** `text-embedding-3-small`.

Embeddings are generated via the OpenAI / Azure OpenAI API through
`OpenAIAdapter.create_embedding()`. Batch generation uses chunks of 50 texts
with 100ms delay between batches.

---

## Distance Functions

### How Vector Search Works

```
Question: "Who scored the first goal?"
                │
                ▼
        ┌───────────────┐
        │  Embed query   │  → query_vector [0.012, -0.034, ...]
        └───────┬───────┘
                │
                ▼
    ┌───────────────────────┐
    │  Compare against all   │
    │  event embeddings in   │  → rank by distance
    │  the selected match    │
    └───────────┬───────────┘
                │
                ▼
        top_n closest events
```

### Algorithms Compared

| Algorithm | Mathematical Definition | Intuition | Best For |
|-----------|----------------------|-----------|----------|
| **Cosine** | 1 − (A·B / ‖A‖‖B‖) | Angle between vectors (ignores magnitude) | General-purpose text similarity |
| **Inner Product** | −(A·B) | Dot product (considers magnitude) | Pre-normalized embeddings |
| **L2 Euclidean** | √Σ(aᵢ−bᵢ)² | Straight-line distance in N-dim space | When magnitude matters |
| **L1 Manhattan** | Σ|aᵢ−bᵢ| | Grid-walking distance | Sparse/high-dimensional data |

### Implementation Per Database

#### PostgreSQL (pgvector)

```sql
-- Cosine distance
SELECT *, summary_embedding_t3_small <=> %s::vector AS distance
FROM events_details__quarter_minute
WHERE match_id = %s
ORDER BY distance ASC
LIMIT %s;

-- Inner product (negated for DESC ordering)
SELECT *, (summary_embedding_t3_small <#> %s::vector) * -1 AS similarity
FROM events_details__quarter_minute
WHERE match_id = %s
ORDER BY similarity DESC
LIMIT %s;

-- L2 Euclidean
SELECT *, summary_embedding_t3_small <-> %s::vector AS distance
FROM events_details__quarter_minute
WHERE match_id = %s
ORDER BY distance ASC
LIMIT %s;
```

**Indexing:** HNSW (Hierarchical Navigable Small World) indexes on each embedding
column enable approximate nearest neighbor search in sub-linear time.

#### SQL Server (VECTOR type)

```sql
SELECT TOP (@top_n) *,
       VECTOR_DISTANCE('cosine', summary_embedding_t3_small, @query_vector) AS distance
FROM events_details__15secs_agg
WHERE match_id = @match_id
ORDER BY distance ASC;
```

SQL Server supports `cosine`, `dot` (inner product), and `euclidean` distance types
via the `VECTOR_DISTANCE()` function. L1 Manhattan is not available.

---

## Search Flow in the RAG Pipeline

```
SearchRequest
  ├── match_id          → filters events to a single match
  ├── query             → user's natural language question
  ├── embedding_model   → selects which embedding column to search
  ├── search_algorithm  → selects distance function
  └── top_n             → max results returned (default 10, max 100)
```

1. **Validate capabilities** — check that the requested model + algorithm combination
   is supported by the selected data source.
2. **Normalize query** — translate to English if needed.
3. **Embed query** — generate vector using the same model as the stored embeddings.
4. **Execute search** — run distance query against the matching embedding column.
5. **Return results** — `List[SearchResult]` ranked by similarity score.

---

## Capability Matrix

| Source | Ada 002 | 3-Small | 3-Large | Cosine | Inner Product | L2 Euclidean | L1 Manhattan |
|--------|---------|---------|---------|--------|--------------|-------------|-------------|
| PostgreSQL | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ | ✅ |
| SQL Server | ✅ | ✅ | ❌ | ✅ | ✅ | ✅ | ❌ |

The system validates these capabilities before executing a search. Unsupported
combinations return HTTP 400.

---

## Performance Considerations

| Factor | Impact | Mitigation |
|--------|--------|-----------|
| Embedding dimensions | Higher = better quality but slower search | Use 3-Small (1536d) as default |
| Number of events per match | ~360 quarter-minute records per 90-min match | Small enough for exact search |
| HNSW index | Sub-linear ANN search | Built on each embedding column in Postgres |
| Batch embedding | 50 texts per API call, 100ms delay | Avoids rate limits during ingestion |

---

## References

- [pgvector documentation](https://github.com/pgvector/pgvector)
- [SQL Server VECTOR type](https://learn.microsoft.com/en-us/sql/relational-databases/vectors/vectors-sql-server)
- [OpenAI Embeddings guide](https://platform.openai.com/docs/guides/embeddings)
