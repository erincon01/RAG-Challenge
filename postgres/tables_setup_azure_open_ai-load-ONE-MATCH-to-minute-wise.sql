

-- be careful with this insert because implicitelly calls the embeddings function.
-- if openai embedding are included, be patient to some delay.

insert INTO
    events_details__minutewise (
        match_id, 
        period, 
        minute, 
        count, 
        json_
    )
SELECT
    match_id,
    period,
    minute,
    count(*) AS count,
    STRING_AGG(json_, ', ') AS json_
    FROM
    events_details
    where match_id = 3869685
GROUP BY
    match_id,
    period,
    minute;


-- recreate the indexes

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



-- this update is to replace the word goalkeeper by g_keeper in the summary and summary_script fields
-- embeddings seems to get confused because Goal is similar to Goalkeeper
--

/*
    UPDATE events_details__minutewise
    SET summary = REPLACE(summary, 'goalkeeper', 'g_keeper');

    UPDATE events_details__minutewise
    SET summary = REPLACE(summary, 'Goalkeeper', 'g_keeper');

    UPDATE events_details__minutewise
    SET summary_script = REPLACE(summary_script, 'goalkeeper', 'g_keeper');

    UPDATE events_details__minutewise
    SET summary_script = REPLACE(summary_script, 'Goalkeeper', 'g_keeper');
*/