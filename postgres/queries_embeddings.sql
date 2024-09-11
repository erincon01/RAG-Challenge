-- The shot was successful
-- Goal conceded  -- **Goal**

-- ###### France - Argentina match_id: 3869685
-- ###### England - Spain match_id: 3943043


-- Retrieve similarities. NIP
SELECT period, minute, summary, summary_script
    , summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS nip_script
    , summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS nip_summary
    , summary_embedding_ada_002 <#> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS nip_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
-- where minute = 85
ORDER BY nip_summary
LIMIT 10;

SELECT period, minute, summary, summary_script
    , summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal')::vector AS nip_script
    , summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal')::vector AS nip_summary
    , summary_embedding_ada_002 <#> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS nip_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
ORDER BY nip_script
LIMIT 10;

SELECT period, minute, summary, summary_script
    , summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal')::vector AS nip_script
    , summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal')::vector AS nip_summary
    , summary_embedding_ada_002 <#> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS nip_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
ORDER BY nip_summary_script_ada_002
LIMIT 10;

-- Retrieve similarities. COSINE
SELECT period, minute, summary, summary_script
    , summary_script_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS cos_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS cos_summary
    , summary_embedding_ada_002 <=> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS cos_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
-- where minute = 85
ORDER BY cos_script
LIMIT 10;

SELECT period, minute, summary, summary_script
    , summary_script_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS cos_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS cos_summary
    , summary_embedding_ada_002 <=> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS cos_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
ORDER BY cos_script
LIMIT 10;


SELECT period, minute, summary, summary_script
    , summary_script_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS cos_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal scored')::vector AS cos_summary
    , summary_embedding_ada_002 <=> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS cos_summary_script_ada_002
FROM events_details__minutewise
where match_id = 3943043
ORDER BY cos_summary_script_ada_002
LIMIT 10;


-- <#> - (negative) inner product   -- vector_ip_ops
-- <=> - cosine distance            -- vector_cosine_ops
-- NOT USED ¿? <-> - L2 distance    -- vector_l2_ops
-- NOT USED ¿? <+> - L1 distance    -- vector_l1_ops

/*
Supported types are:
    vector      - up to 2,000 dimensions
    halfvec     - up to 4,000 dimensions (added in 0.7.0)
    bit         - up to 64,000 dimensions (added in 0.7.0)
    sparsevec   - up to 1,000 non-zero elements (added in 0.7.0)

*/
