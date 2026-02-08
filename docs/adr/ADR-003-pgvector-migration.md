# ADR-003: Migration from Azure AI Extensions to pgvector

## Status

**Proposed** - 2026-02-08

## Context

The current PostgreSQL implementation relies heavily on Azure-specific extensions for embedding management:

### Current Azure-Dependent Architecture

**Extensions Used:**
- `azure_ai` extension for AI integrations
- `azure_local_ai` extension for local AI model execution

**Current Implementation:**
```sql
-- Column definitions with Azure-generated embeddings
CREATE TABLE events (
    -- ...
    summary_embedding_ada_002 vector(1536)
        GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector) STORED,
    summary_embedding_t3_small vector(1536)
        GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-3-small', summary)::vector) STORED,
    summary_embedding_t3_large vector(3072)
        GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-3-large', summary)::vector) STORED
);
```

**Runtime Queries:**
```sql
-- Query-time embedding generation (runtime dependency on Azure)
SELECT * FROM events
WHERE azure_openai.create_embeddings('text-embedding-3-small', $1) <=> summary_embedding_t3_small
ORDER BY distance LIMIT 10;
```

### Problems

1. **Azure PaaS Lock-in**: Cannot run locally without Azure PostgreSQL PaaS
2. **No Local Development**: Developers need Azure credentials and connectivity
3. **Cost**: Every development query costs money (Azure API calls)
4. **Portability**: Cannot deploy to other cloud providers or on-premise
5. **Testing**: Integration tests require Azure infrastructure
6. **Performance**: Network latency for every embedding generation
7. **Migration Risk**: High risk if moving away from Azure in future

## Decision

Migrate to **pgvector with application-managed embeddings**:

### New Architecture

**Extension:**
- Use open-source `pgvector` extension (no Azure dependencies)
- Available in standard PostgreSQL and local Docker

**Embedding Generation:**
- Move from database-generated to **application-generated** embeddings
- Backend service responsible for calling OpenAI API
- Store pre-computed embeddings as physical columns (not generated)

**New Schema:**
```sql
CREATE TABLE events (
    -- ...
    summary TEXT,
    summary_embedding_ada_002 vector(1536) NULL,      -- App-managed
    summary_embedding_t3_small vector(1536) NULL,      -- App-managed
    summary_embedding_t3_large vector(3072) NULL,      -- App-managed

    -- Metadata for tracking
    embedding_status TEXT DEFAULT 'pending',           -- pending, done, error
    embedding_updated_at TIMESTAMP,
    embedding_error TEXT
);
```

**Runtime Queries:**
```sql
-- Pre-compute search term embedding in application
-- Then query with vector similarity
SELECT * FROM events
WHERE summary_embedding_t3_small IS NOT NULL
ORDER BY summary_embedding_t3_small <=> $1::vector  -- $1 is pre-computed in app
LIMIT 10;
```

### Embedding Pipeline

**Worker Service** (can be async background job or part of backend):

```python
async def generate_embeddings_for_event(event_id: int):
    """Generate and store embeddings for an event summary."""

    # 1. Fetch event
    event = await event_repo.get_by_id(event_id)

    # 2. Generate embeddings from OpenAI
    ada_embedding = await openai_client.create_embedding(
        model="text-embedding-ada-002",
        input=event.summary
    )
    t3_small_embedding = await openai_client.create_embedding(
        model="text-embedding-3-small",
        input=event.summary
    )

    # 3. Store in database
    await event_repo.update_embeddings(
        event_id=event_id,
        ada_002=ada_embedding,
        t3_small=t3_small_embedding,
        status="done"
    )
```

**Batch Processing:**
```python
# Process all events without embeddings
pending_events = await event_repo.get_events_by_status("pending")

for event in pending_events:
    try:
        await generate_embeddings_for_event(event.id)
    except Exception as e:
        await event_repo.mark_embedding_error(event.id, str(e))
```

### Vector Indexing

**Create HNSW indexes** for fast similarity search:

```sql
-- Cosine similarity index
CREATE INDEX idx_events_embedding_t3_small_cosine
ON events USING hnsw (summary_embedding_t3_small vector_cosine_ops)
WITH (m = 16, ef_construction = 64);

-- Inner product index
CREATE INDEX idx_events_embedding_t3_small_ip
ON events USING hnsw (summary_embedding_t3_small vector_ip_ops)
WITH (m = 16, ef_construction = 64);

-- L2 distance index
CREATE INDEX idx_events_embedding_t3_small_l2
ON events USING hnsw (summary_embedding_t3_small vector_l2_ops)
WITH (m = 16, ef_construction = 64);
```

**Index Tuning Parameters:**
- `m`: Max connections per layer (default 16, range 2-100)
- `ef_construction`: Size of dynamic candidate list (default 64, higher = better quality, slower build)
- `ef_search`: Runtime search scope (set per query)

## Consequences

### Positive

✅ **Full Local Development**: Works with standard PostgreSQL + pgvector Docker image
✅ **Portability**: No Azure dependencies, can deploy anywhere
✅ **Cost Control**: Control when embeddings are generated (batch vs real-time)
✅ **Flexibility**: Can use any embedding provider (OpenAI, Hugging Face, local models)
✅ **Testing**: Easy to mock embedding generation in tests
✅ **Performance**: Can cache embeddings, no generation on every query
✅ **Observability**: Full control over embedding pipeline (retries, monitoring, logging)
✅ **Incremental Processing**: Generate embeddings in batches during off-peak
✅ **Error Handling**: Graceful degradation if embedding generation fails

### Negative

⚠️ **Application Complexity**: Backend now responsible for embedding lifecycle
⚠️ **Data Staleness**: Embeddings can be out of sync with source text
⚠️ **Storage**: Need to store embeddings (vs generated on-the-fly)
⚠️ **Migration Effort**: Significant work to rewrite SQL and add worker service
⚠️ **Operational Overhead**: Need to monitor embedding generation pipeline
⚠️ **Schema Changes**: Need migrations to add status tracking columns

### Trade-offs

- **Immediacy vs Flexibility**: Lose instant embedding generation, gain portability
- **Simplicity vs Control**: More code to manage, but full control over process
- **Storage vs Computation**: Store pre-computed embeddings vs generate on demand

## Migration Plan

### Phase 1: Schema Migration (Week 4)

1. Add new columns to existing tables:
   - `embedding_status`, `embedding_updated_at`, `embedding_error`
2. Create pgvector indexes
3. Keep existing Azure-generated columns temporarily

### Phase 2: Embedding Worker (Week 4-5)

1. Implement embedding generation service
2. Create batch processing script
3. Add retry logic and error handling
4. Add monitoring and logging

### Phase 3: Data Migration (Week 5)

1. Backfill embeddings for existing data
2. Validate parity with Azure-generated embeddings
3. Performance testing and tuning

### Phase 4: Query Migration (Week 5-6)

1. Update repository layer to use new embedding columns
2. Update search queries to use pre-computed embeddings
3. Remove Azure extension dependencies from queries

### Phase 5: Cleanup (Week 6)

1. Drop Azure-generated columns
2. Remove Azure extension references
3. Update documentation

## Validation & Testing

### Embedding Quality

Compare embedding similarity scores between Azure-generated and app-generated:

```python
# Ensure < 0.01 difference in cosine similarity
assert abs(azure_similarity - pgvector_similarity) < 0.01
```

### Performance Benchmarks

Target metrics (compared to current Azure approach):
- **Query latency (p50)**: < 50ms (currently ~100ms with Azure generation)
- **Query latency (p95)**: < 200ms (currently ~500ms)
- **Embedding generation throughput**: > 100 events/sec
- **Index build time**: < 5 minutes for 1M vectors

### Search Quality

Validate top-k retrieval precision:
```python
# For same query, ensure 80%+ overlap in top-10 results
overlap = len(set(azure_top10) & set(pgvector_top10)) / 10
assert overlap >= 0.8
```

## Alternatives Considered

### Alternative 1: Keep Azure AI Extensions, Add Abstraction Layer
**Rejected** - Doesn't solve fundamental portability issue, just hides it

### Alternative 2: Use Separate Vector Database (Pinecone, Weaviate, Qdrant)
**Rejected** - Adds operational complexity, want to keep data colocated

### Alternative 3: Dual-Write to Both Systems
**Rejected** - Increases complexity, hard to maintain consistency

## Implementation Checklist

- [ ] Install pgvector extension in local Docker PostgreSQL
- [ ] Create migration scripts for schema changes
- [ ] Implement embedding generation service in backend
- [ ] Create batch processing worker
- [ ] Add monitoring for embedding pipeline
- [ ] Write integration tests for embedding generation
- [ ] Backfill existing data with new embeddings
- [ ] Performance testing and index tuning
- [ ] Update repository queries to use new columns
- [ ] Validate search quality parity
- [ ] Update documentation
- [ ] Remove Azure extension dependencies

## References

- [pgvector GitHub Repository](https://github.com/pgvector/pgvector)
- [pgvector Performance Tuning](https://github.com/pgvector/pgvector#performance)
- [HNSW Algorithm Paper](https://arxiv.org/abs/1603.09320)
- [OpenAI Embeddings Guide](https://platform.openai.com/docs/guides/embeddings)

## Related ADRs

- [ADR-001: Adoption of Layered Architecture](ADR-001-layered-architecture.md) - Embedding service fits in adapters layer
- [ADR-004: Local Docker Infrastructure](ADR-004-local-docker-infrastructure.md) - PostgreSQL with pgvector in Docker
