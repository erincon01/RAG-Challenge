
CREATE OR REPLACE FUNCTION safe_json_extract(json_text TEXT, key TEXT) 
RETURNS TEXT AS $$
DECLARE
    result TEXT;
BEGIN
    BEGIN
        result := (json_text::jsonb ->> key);
    EXCEPTION
        WHEN others THEN
            result := NULL;
    END;
    RETURN result;
END;
$$ LANGUAGE plpgsql;


DROP TABLE IF EXISTS final_match_Spain_England_events_details__10secwise;

WITH event_seconds AS (
    SELECT
        match_id,
        period,
        minute,
        COALESCE((safe_json_extract(json_, 'second'))::int, 0) AS second,
        json_
    FROM
        final_match_spain_england_events_details__minutewise
    WHERE
        match_id = 3943043
),
event_periods AS (
    SELECT
        match_id,
        period,
        minute,
        FLOOR(second / 10) * 10 AS period_10_sec,
        COUNT(*) AS count,
        STRING_AGG(json_, ', ') AS json_
    FROM
        event_seconds
    GROUP BY
        match_id,
        period,
        minute,
        period_10_sec
)
SELECT
    match_id,
    period,
    minute,
    period_10_sec AS sec_period_10,
    count,
    json_,
    NULL AS summary
-- INTO final_match_Spain_England_events_details__10secwise
FROM
    event_periods
ORDER BY
    period,
    minute,
    sec_period_10;


ALTER TABLE final_match_Spain_England_events_details__10secwise
ADD COLUMN id SERIAL PRIMARY KEY;

-- before creating the embeddings, we need to populate the summary column using python to iterate and call Azure OpenAI API for summarization: create_events_summary_per_pk_from_json_rows_in_database

ALTER TABLE final_match_Spain_England_events_details__10secwise
ADD COLUMN embedding_mlt vector(384) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_local_ai.create_embeddings('multilingual-e5-small:v1', summary)::vector) STORED; -- TEXT string sent to local model

CREATE INDEX final_match_Spain_England_events_details__10secwise_embedding 
ON final_match_Spain_England_events_details__10secwise USING hnsw (embedding_MLT vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)


ALTER TABLE final_match_Spain_England_events_details__10secwise
ADD COLUMN embedding_ada VECTOR(1536) --ADAD embeddings are 1536 dimensions
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', summary)::vector) STORED; -- TEXT string sent to local model

CREATE INDEX final_match_Spain_England_events_details__10secwise_embedding2 
ON final_match_Spain_England_events_details__10secwise USING hnsw (embedding_ADA vector_cosine_ops); -- other option: vector_cosine_ops (cosine similarity, vs inner product)


SELECT *
FROM final_match_Spain_England_events_details__10secwise



-- Retrieve top similarity match
-- SELECT azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Oyarzabal goal score')::vector AS query_embedding;

WITH query_embedding AS (
    SELECT azure_openai.create_embeddings('text-embedding-ada-002', 'Jordan Pickford')::vector AS ada,
    azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Jordan Pickford')::vector AS mlt
)
SELECT 
    minute,
    sec_period_10,
    -- v.embedding_ada, v.embedding_mlt,
--    q.ada <-> v.embedding_ada d1_ada,
    q.mlt <-> v.embedding_mlt l2,
--    q.ada <=> v.embedding_ada d2_ada,
    q.mlt <=> v.embedding_mlt coseno,
--    q.ada <#> v.embedding_ada d3_ada,
    q.mlt <#> v.embedding_mlt inp,
--    q.ada <+> v.embedding_ada d4_ada,
    q.mlt <+> v.embedding_mlt l1,
    summary
FROM
    final_match_Spain_England_events_details__10secwise v,
    query_embedding q
    where minute = 85;


select *
from final_match_Spain_England_events_details__10secwise
where minute = 85
limit 10;


-- <-> - L2 distance                -- vector_l2_ops
-- <#> - (negative) inner product   -- vector_ip_ops
-- <=> - cosine distance            -- vector_cosine_ops
-- <+> - L1 distance                -- vector_l1_ops


-- 85th minute | Jordan Pickford | passes | Goalkeeper | Right Back - 85th minute | Kyle Walker | receives | Right Back | Right Back - 85th minute | Kyle Walker | carries | Right Back | Right Center Back - 85th minute | Daniel Olmo Carvajal | pressures | Center Attacking Midfield | Right Back - 85th minute | Daniel Olmo Carvajal | dribbles past | Center Attacking Midfield | Center Attacking Midfield - 85th minute | Kyle Walker | dribbles | Right Back | Right Back - 85th minute | Kyle Walker | carries | Right Back | Right Back - 85th minute | Bukayo Saka | passes | Right Wing | Right Wing - 85th minute | Bukayo Saka | receives | Right Wing | Right Wing - 85th minute | Bukayo Saka | carries | Right Wing | Right Wing - 85th minute | John Stones | passes | Right Center Back | Right Center Back - 85th minute | John Stones | receives | Right Center Back | Right Center Back - 85th minute | John Stones | carries | Right Center Back | Left Center Back - 85th minute | Marc Guehi | passes | Left Center Back | Left Center Back - 85th minute | Marc Guehi | receives | Left Center Back | Left Center Back - 85th minute | Marc Guehi | carries | Left Center Back | Left Center Back - 85th minute | Jordan Pickford | passes | Goalkeeper | Goalkeeper - 85th minute | Jordan Pickford | receives | Goalkeeper | Goalkeeper - 85th minute | Jordan Pickford | carries | Goalkeeper | Goalkeeper - 85th minute | Marc Guehi | passes | Left Center Back | Left Center Back - 85th minute | Marc Guehi | receives | Left Center Back | Left Center Back - 85th minute | Marc Guehi | carries | Left Center Back | Left Center Back - 85th minute | Marc Guehi | passes | Left Center Back | Goalkeeper - 85th minute | Jordan Pickford | receives | Goalkeeper | Goalkeeper - 85th minute | Daniel Carvajal | passes | Right Back | Left Center Back - 85th minute | Aymeric Laporte | receives | Left Center Back | Left Center Back - 85th minute | Aymeric Laporte | carries | Left Center Back | Left Center Back - 85th minute | Fabián Ruiz Peña | passes | Left Defensive Midfield | Left Defensive Midfield - 85th minute | Daniel Olmo Carvajal | receives | Center Attacking Midfield | Center Attacking Midfield - 85th minute | Daniel Olmo Carvajal | carries | Center Attacking Midfield | Center Attacking Midfield - 85th minute | Mikel Oyarzabal Ugarte | passes | Center Forward | Center Forward - 85th minute | Mikel Oyarzabal Ugarte | receives | Center Forward | Center Forward - 85th minute | Marc Cucurella Saseta | passes | Left Back | Left Back - 85th minute | Marc Cucurella Saseta | receives | Left Back | Left Back - 85th minute | 
-- Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute | Jordan Pickford | saves | Goalkeeper | Goalkeeper    

WITH query_embedding AS (
)
SELECT 
    minute,
    sec_period_10,
    summary,
    --v.embedding2, q.embedding2,
    q.embedding <-> v.embedding d1,  
    q.embedding <=> v.embedding d2,  
    q.embedding <#> v.embedding 3,  
    q.embedding <+> v.embedding d4  
FROM
    final_match_Spain_England_events_details__10secwise v,
    query_embedding q
    where minute = 85;
    
    



-- minute 85th minute
-- Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute | Jordan Pickford | saves | Goalkeeper | Goalkeeper

-- <-> - L2 distance                -- vector_l2_ops
-- <#> - (negative) inner product   -- vector_ip_ops
-- <=> - cosine distance            -- vector_cosine_ops
-- <+> - L1 distance                -- vector_l1_ops


-- Retrieve top similarity match
SELECT 
    period, 
    minute, 
    embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute')::vector AS distance1,
    embedding <-> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute')::vector AS distance2,
    embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute')::vector AS distance3,
    embedding <+> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Mikel Oyarzabal Ugarte | shoots | Center Forward | Goal - 85th minute')::vector AS distance4,
    summary
FROM final_match_Spain_England_events_details__10secwise
    where minute = 85;




SELECT period, minute, embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', ' goal')::vector AS distance
FROM final_match_Spain_England_events_details__10secwise
ORDER BY embedding <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'Oyarzabal')::vector
LIMIT 5;

select *
from final_match_Spain_England_events_details__10secwise
where json_ like '%Oyarzabal%'
order by minute, sec_period_10


select *
from "public"."final_match_spain_england_events_details__10secwise"
where minute = 85
limit 10;

