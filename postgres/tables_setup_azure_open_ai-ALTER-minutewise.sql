
-- configure the extensions in the server

SELECT * FROM pg_available_extensions where name like '%vector%' or  name like '%azure%';

SHOW azure.extensions;

CREATE EXTENSION azure_local_ai;
CREATE EXTENSION vector;

SELECT azure_local_ai.get_setting('intra_op_parallelism');
SELECT azure_local_ai.get_setting('inter_op_parallelism');
SELECT azure_local_ai.get_setting('spin_control');

ALTER EXTENSION azure_local_ai UPDATE;
ALTER EXTENSION vector UPDATE;

-- optionally, enable azure_open_ai if you need to use open_ai embeddings

CREATE EXTENSION azure_ai;

select azure_ai.set_setting('azure_openai.endpoint','https://<endpoint>.openai.azure.com'); 
select azure_ai.set_setting('azure_openai.subscription_key', 'key');

select azure_ai.get_setting('azure_openai.endpoint');
select azure_ai.get_setting('azure_openai.subscription_key');
select azure_ai.version();

ALTER EXTENSION azure_ai UPDATE;

-- be careful with this ALTER because it persissts the data in the table immediately
-- takes long time due to embeding generation

ALTER TABLE events_details
ADD COLUMN embedding vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', json_)::vector) STORED; -- TEXT string sent to local model

-- alternatively, you can use the following to generate the embeddings on demand
ALTER TABLE events_details
ADD COLUMN embedding vector(384);

CREATE INDEX events_details_embbeding ON events_details USING hnsw (embedding vector_ip_ops);

-- aggregate the events by match_id and minute (json_ is the column with the event details that is concatenated)

drop table final_match_Spain_England_events_details__minutewise;

SELECT
    match_id,
    period,
    minute,
    count(*) count,
    STRING_AGG(json_, ', ') AS json_
INTO final_match_Spain_England_events_details__minutewise
FROM
    events_details
    where match_id = 3943043
GROUP BY
    match_id,
    period,
    minute
order by minute;

ALTER TABLE final_match_Spain_England_events_details__minutewise
ADD COLUMN id SERIAL PRIMARY KEY;

alter table final_match_Spain_England_events_details__minutewise
add column summary text;

alter table final_match_Spain_England_events_details__minutewise
add column summary_script text;

-- run the python script to summarize the json events.
-- before creating the embeddings, we need to populate the summary column using python to iterate and call Azure OpenAI API for summarization: create_events_summary_per_pk_from_json_rows_in_database


ALTER TABLE final_match_Spain_England_events_details__minutewise
ADD COLUMN summary_embedding vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector) STORED; 

ALTER TABLE final_match_Spain_England_events_details__minutewise
ADD COLUMN summary_script_embedding vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary_script)::vector) STORED; 

DROP INDEX IF EXISTS final_match_Spain_England_events_details__min__se_vIP;

CREATE INDEX final_match_Spain_England_events_details__min__se_vIP
ON final_match_Spain_England_events_details__minutewise USING hnsw (summary_embedding vector_ip_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS final_match_Spain_England_events_details__min__sse_vIP;

CREATE INDEX final_match_Spain_England_events_details__min__sse_vIP 
ON final_match_Spain_England_events_details__minutewise USING hnsw (summary_script_embedding vector_ip_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS final_match_Spain_England_events_details__min__mse_cos;

CREATE INDEX final_match_Spain_England_events_details__min__mse_cos
ON final_match_Spain_England_events_details__minutewise USING hnsw (summary_embedding vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS final_match_Spain_England_events_details__min__msse_cos;

CREATE INDEX final_match_Spain_England_events_details__min__msse_cos 
ON final_match_Spain_England_events_details__minutewise USING hnsw (summary_script_embedding vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)


-- https://learn.microsoft.com/es-es/azure/postgresql/flexible-server/how-to-optimize-performance-pgvector

-- Retrieve top similarity match
SELECT period, minute, summary, summary_script
    , summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'goal score')::vector AS nip_script
    , summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'goal score')::vector AS nip_summary
FROM final_match_Spain_England_events_details__minutewise
ORDER BY nip_script
LIMIT 5;

SELECT period, minute, summary, summary_script
    , 1-(summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'goal score')::vector) AS cos_script
    , 1-(summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'goal score')::vector) AS cos_summary
FROM final_match_Spain_England_events_details__minutewise
ORDER BY cos_script
LIMIT 5;

SELECT period, minute, summary, summary_script, json_
    , (summary_script_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal Conceded')::vector) AS cos_script
    , (summary_embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Goal Conceded')::vector) AS cos_summary
FROM final_match_Spain_England_events_details__minutewise
where -- minute between 76 and 89 and 
json_ like '%Goal Conceded%'


-- <-> - L2 distance                -- vector_l2_ops
-- <#> - (negative) inner product   -- vector_ip_ops
-- <=> - cosine distance            -- vector_cosine_ops
-- <+> - L1 distance                -- vector_l1_ops

/*
Supported types are:
    vector      - up to 2,000 dimensions
    halfvec     - up to 4,000 dimensions (added in 0.7.0)
    bit         - up to 64,000 dimensions (added in 0.7.0)
    sparsevec   - up to 1,000 non-zero elements (added in 0.7.0)

*/


select *
from final_match_Spain_England_events_details__minutewise
where minute = 85;

update final_match_Spain_England_events_details__minutewise
set summary = null
where minute = 85;
