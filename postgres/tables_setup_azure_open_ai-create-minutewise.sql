
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
ADD COLUMN summary_embedding vector(384) 
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_script_embedding vector(384) 
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary_script)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_embedding_ada_002 VECTOR(1536) 
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_embedding_t3_small VECTOR(1536) 
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-3-small', summary)::vector) STORED; 

ALTER TABLE events_details__minutewise
ADD COLUMN summary_embedding_t3_large VECTOR(3072) 
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-3-large', summary)::vector) STORED; 


DROP INDEX IF EXISTS events_details__min__se_vIP;
DROP INDEX IF EXISTS events_details__min__se_cos;
DROP INDEX IF EXISTS events_details__min__sse_vIP;
DROP INDEX IF EXISTS events_details__min__sse_cos;
DROP INDEX IF EXISTS events_details__min__ada_002_vIP;
DROP INDEX IF EXISTS events_details__min__ada_002_cos;
DROP INDEX IF EXISTS events_details__min__t3_small_vIP;
DROP INDEX IF EXISTS events_details__min__t3_small_cos;

CREATE INDEX events_details__min__se_vIP        ON events_details__minutewise USING hnsw (summary_embedding             vector_ip_ops); 
CREATE INDEX events_details__min__se_cos        ON events_details__minutewise USING hnsw (summary_embedding             vector_cosine_ops); 
CREATE INDEX events_details__min__sse_vIP       ON events_details__minutewise USING hnsw (summary_script_embedding      vector_ip_ops); 
CREATE INDEX events_details__min__sse_cos       ON events_details__minutewise USING hnsw (summary_script_embedding      vector_cosine_ops); 
CREATE INDEX events_details__min__ada_002_vIP   ON events_details__minutewise USING hnsw (summary_embedding_ada_002     vector_ip_ops); 
CREATE INDEX events_details__min__ada_002_cos   ON events_details__minutewise USING hnsw (summary_embedding_ada_002     vector_cosine_ops); 
CREATE INDEX events_details__min__t3_small_vIP  ON events_details__minutewise USING hnsw (summary_embedding_t3_small    vector_ip_ops); 
CREATE INDEX events_details__min__t3_small_cos  ON events_details__minutewise USING hnsw (summary_embedding_t3_small    vector_cosine_ops); 

