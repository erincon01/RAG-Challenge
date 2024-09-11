
-- aggregate the events by match_id and minute (json_ is the column with the event details that is concatenated)

-- drop table events_details__minutewise;
-- SETUP THE TABLE WITH EMPTY DATA --->>>>   1=0

SELECT
    match_id,
    period,
    minute,
    count(*) count,
    STRING_AGG(json_, ', ') AS json_
INTO events_details__minutewise
FROM
    events_details
    where 1 =0
GROUP BY
    match_id,
    period,
    minute
order by minute;

ALTER TABLE events_details__minutewise
ADD COLUMN id SERIAL PRIMARY KEY;

alter table events_details__minutewise
add column summary text;

alter table events_details__minutewise
add column summary_script text;

-- there are two options:

--- you create the table empty with the default values

-- run the python script to summarize the json events.
-- before creating the embeddings, we need to populate the summary column using python to iterate and call Azure OpenAI API for summarization: create_events_summary_per_pk_from_json_rows_in_database


ALTER TABLE events_details__minutewise
ADD COLUMN summary_embedding vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_script_embedding vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary_script)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_embedding_ada_002 VECTOR(1536) --ADAD embeddings are 1536 dimensions
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector) STORED; -- TEXT string sent to local model

DROP INDEX IF EXISTS events_details__min__se_vIP;

CREATE INDEX events_details__min__se_vIP
ON events_details__minutewise USING hnsw (summary_embedding vector_ip_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS events_details__min__sse_vIP;

CREATE INDEX events_details__min__sse_vIP 
ON events_details__minutewise USING hnsw (summary_script_embedding vector_ip_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS events_details__min__mse_cos;

CREATE INDEX events_details__min__mse_cos
ON events_details__minutewise USING hnsw (summary_embedding vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS events_details__min__msse_cos;

CREATE INDEX events_details__min__msse_cos 
ON events_details__minutewise USING hnsw (summary_script_embedding vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS events_details__min__ada_002_vIP;

CREATE INDEX events_details__min__ada_002_vIP 
ON events_details__minutewise USING hnsw (summary_embedding_ada_002 vector_ip_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)

DROP INDEX IF EXISTS events_details__min__ada_002_cos;

CREATE INDEX events_details__min__ada_002_cos 
ON events_details__minutewise USING hnsw (summary_embedding_ada_002 vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)
