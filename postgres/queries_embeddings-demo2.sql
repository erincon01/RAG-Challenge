

-- ###### France - Argentina match_id: 3869685
-- ###### England - Spain match_id: 3943043

drop table if exists t1;

create table t1 (match_id int, summary text, id serial primary key);

insert into t1 (match_id, summary) values (1, 'this is a text related a football match');
insert into t1 (match_id, summary) values (2, null);
insert into t1 (match_id, summary) values (3, 'there is a goal in this section');
insert into t1 (match_id, summary) values (5, 'this was a nice change, that did not success as goal');
insert into t1 (match_id, summary) values (6, 'bad chance, however goal was annotated');
insert into t1 (match_id, summary) values (7, 'this is a penalty that ened as goal');
insert into t1 (match_id, summary) values (8, 'goal was conceeded, however referee review detected and off-side, having as result that the goal was rejected');


ALTER TABLE t1
ADD COLUMN summary_embedding vector(384)
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector
        ELSE NULL
    END
) STORED;


ALTER TABLE t1
ADD COLUMN summary_embedding_ada_002 VECTOR(1536) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector
        ELSE NULL
    END
) STORED;

ALTER TABLE t1
ADD COLUMN summary_embedding_t3_small VECTOR(1536) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-3-small', summary)::vector
        ELSE NULL
    END
) STORED;


ALTER TABLE t1
ADD COLUMN summary_embedding_t3_large VECTOR(3072) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-3-large', summary)::vector
        ELSE NULL
    END
) STORED;

-- Retrieve similarities. NIP
SELECT match_id, summary, id
--    , summary_script_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS cos_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS nip_summary
    , summary_embedding_ada_002 <=> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS nip_summary_script_ada_002
    , summary_embedding_t3_small <=> azure_openai.create_embeddings('text-embedding-3-small', 'Goal scored')::vector AS nip_summary_script_t3_small
    , summary_embedding_t3_large <=> azure_openai.create_embeddings('text-embedding-3-large', 'Goal scored')::vector AS nip_summary_script_t3_large
FROM t1
ORDER BY 4;


-- Retrieve similarities. COSINE
SELECT match_id, summary, id
--    , summary_script_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS cos_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal conceded')::vector AS cos_summary
    , summary_embedding_ada_002 <=> azure_openai.create_embeddings('text-embedding-ada-002', 'Goal scored')::vector AS cos_summary_script_ada_002
    , summary_embedding_t3_small <=> azure_openai.create_embeddings('text-embedding-3-small', 'Goal scored')::vector AS cos_summary_script_t3_small
    , summary_embedding_t3_large <=> azure_openai.create_embeddings('text-embedding-3-large', 'Goal scored')::vector AS cos_summary_script_t3_large
FROM t1
ORDER BY 4 desc;





