

-- ###### France - Argentina match_id: 3869685
-- ###### England - Spain match_id: 3943043

drop table if exists events_details__quarter_minute;

SELECT
    match_id,
    period,
    minute,
    (second / 15) + 1 AS quarter_minute, -- Divide los segundos en dos intervalos: 0-29 y 30-59
    count(*) AS count,
    STRING_AGG(json_, ', ') AS json_
INTO events_details__quarter_minute 
FROM
    events_details where match_id in (3869685, 3943043)
GROUP BY
    match_id,
    period,
    minute,
    (second / 15) + 1
ORDER BY
    match_id,
    period,
    minute,
    (second / 15) + 1;

ALTER TABLE events_details__quarter_minute
ADD COLUMN id SERIAL PRIMARY KEY;

alter table events_details__quarter_minute
add column summary text;

alter table events_details__quarter_minute
add column summary_script text; -- not used 

-- in case you need to insert concrete match_id

/*

insert INTO
    events_details__quarter_minute (
        match_id, 
        period, 
        minute, 
        quarter_minute,
        count, 
        json_
    )
SELECT
    match_id,
    period,
    minute,
    (second / 15) + 1 AS quarter_minute,
    count(*) AS count,
    STRING_AGG(json_, ', ') AS json_
    FROM
    events_details
    where match_id = 3943043
GROUP BY
    match_id,
    period,
    minute,
    (second / 15) + 1
ORDER BY     
    match_id,
    period,
    minute,
    (second / 15) + 1;

*/


-- some statistics
--
select match_id, count(*) c from events_details__quarter_minute
group by match_id;

select minute, period, count(*) c from events_details__quarter_minute
group by minute, period;


ALTER TABLE events_details__quarter_minute
ADD COLUMN summary_embedding vector(384)
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector
        ELSE NULL
    END
) STORED;


ALTER TABLE events_details__quarter_minute
ADD COLUMN summary_embedding_ada_002 VECTOR(1536) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector
        ELSE NULL
    END
) STORED;


ALTER TABLE events_details__quarter_minute
ADD COLUMN summary_embedding_t3_small VECTOR(1536) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-3-small', summary)::vector
        ELSE NULL
    END
) STORED;


ALTER TABLE events_details__quarter_minute
ADD COLUMN summary_embedding_t3_large VECTOR(3072) 
GENERATED ALWAYS AS (
    CASE 
        WHEN summary IS NOT NULL THEN azure_openai.create_embeddings('text-embedding-3-large', summary)::vector
        ELSE NULL
    END
) STORED;


select * from events_details__quarter_minute
where not summary is null
limit 10;


select count(*) from events_details__quarter_minute
where  summary is null
limit 10;


-- re-create indexes
--
DROP INDEX IF EXISTS events_details__qm__se_vIP;
DROP INDEX IF EXISTS events_details__qm__se_cos;
DROP INDEX IF EXISTS events_details__qm__ada_002_vIP;
DROP INDEX IF EXISTS events_details__qm__ada_002_cos;
DROP INDEX IF EXISTS events_details__qm__t3_small_vIP;
DROP INDEX IF EXISTS events_details__qm__t3_small_cos;

CREATE INDEX events_details__qm__se_vIP        ON events_details__quarter_minute USING hnsw (summary_embedding             vector_ip_ops); 
CREATE INDEX events_details__qm__se_cos        ON events_details__quarter_minute USING hnsw (summary_embedding             vector_cosine_ops); 
CREATE INDEX events_details__qm__ada_002_vIP   ON events_details__quarter_minute USING hnsw (summary_embedding_ada_002     vector_ip_ops); 
CREATE INDEX events_details__qm__ada_002_cos   ON events_details__quarter_minute USING hnsw (summary_embedding_ada_002     vector_cosine_ops); 
CREATE INDEX events_details__qm__t3_small_vIP  ON events_details__quarter_minute USING hnsw (summary_embedding_t3_small    vector_ip_ops); 
CREATE INDEX events_details__qm__t3_small_cos  ON events_details__quarter_minute USING hnsw (summary_embedding_t3_small    vector_cosine_ops); 
