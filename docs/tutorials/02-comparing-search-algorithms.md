# Tutorial 2: Comparing Search Algorithms

## What you'll learn

- The difference between cosine, inner product, and L2 Euclidean distance
- How algorithm choice affects search results
- When to use each algorithm

## Prerequisites

- Completed Tutorial 1
- Docker stack running with seed data

## The three distance functions

pgvector (and SQL Server 2025) support multiple distance functions for
comparing embedding vectors. Each measures "how far apart" two vectors are,
but the scale and interpretation differ.

| Algorithm | What it measures | Score range | Lower = more similar? | Best for |
|-----------|-----------------|-------------|----------------------|----------|
| Cosine | Angle between vectors | 0 -- 2 | Yes | General text similarity |
| Inner Product | Dot product (negative) | -inf -- 0 | Yes (more negative = more similar) | Normalized vectors |
| L2 Euclidean | Straight-line distance | 0 -- inf | Yes | Outlier detection |

## Experiment: Same question, three algorithms

We will ask the same question against the **2022 World Cup Final**
(match_id `3869685`): *"Who scored the goals?"*

### Cosine distance

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=postgres" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who scored the goals?",
    "match_id": 3869685,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 3
  }'
```

Scores fall in the **0.51 -- 0.55** range. The top result describes the
Montiel penalty goal at minute 125.

### Inner Product

Same command with `"search_algorithm": "inner_product"`.

Scores fall in the **-0.48 -- -0.45** range. The ranking is identical.

### L2 Euclidean

Same command with `"search_algorithm": "l2_euclidean"`.

Scores fall in the **1.01 -- 1.05** range. Again, the same ranking.

## Analysis: What changed?

The key insight: **the ranking is the same** for all three algorithms when
embeddings are normalized to unit length. OpenAI embeddings (`text-embedding-3-small`
and `text-embedding-3-large`) are always returned as unit vectors, so the three
metrics produce equivalent orderings on different scales.

| Rank | Event | Cosine | Inner Product | L2 Euclidean |
|------|-------|--------|---------------|--------------|
| 1 | Montiel penalty (125') | 0.5175 | -0.4825 | 1.0174 |
| 2 | Kolo Muani penalty | 0.5304 | -0.4696 | 1.0300 |
| 3 | Tchouameni penalty | 0.5463 | -0.4537 | 1.0453 |

**Mathematical relationships for unit vectors:**

- `inner_product = -(1 - cosine)`
- `L2^2 = 2 * cosine`

You can verify these with the numbers above. For example,
`1.0174^2 = 1.0351 ≈ 2 * 0.5175`.

## Experiment: PostgreSQL vs SQL Server

Try the same query against SQL Server by changing the `source` parameter:

```bash
curl -s -X POST "http://localhost:8000/api/v1/chat/search?source=sqlserver" \
  -H "Content-Type: application/json" \
  -d '{
    "query": "Who scored the goals?",
    "match_id": 3869685,
    "embedding_model": "text-embedding-3-small",
    "search_algorithm": "cosine",
    "top_n": 3
  }'
```

SQL Server uses the `VECTOR_DISTANCE()` function instead of pgvector
operators, but the results should be identical for the same data and model.

> **Note:** SQL Server does not support L1 Manhattan distance
> (PostgreSQL does via pgvector's `<+>` operator).

## Which algorithm should I use?

**Use cosine distance** for most cases. It is the API default, the most
intuitive to interpret (0 = identical, 2 = opposite), and works well with
all OpenAI embedding models. Switch to inner product only if you have
pre-normalized vectors and need marginally faster queries in pgvector.

## Checking available algorithms

The capabilities endpoint reports which algorithms each source supports:

```bash
curl -s http://localhost:8000/api/v1/capabilities
```

The response lists `search_algorithms` per source, so you can confirm what
is available before running queries.

## What's next

- Tutorial 3: Understanding how embeddings are created and stored
