

-- sample query

WITH vars AS ( -- local embeddings
    SELECT 'WHich players recorded the highest number of carries and passes in both halves, 
    and how did their performances influence the overall strategies of the teams?' AS search_string
)
SELECT match_id, period, minute, summary, summary_script
    , summary_embedding <=> azure_local_ai.create_embeddings('multilingual-e5-small:v1', search_string)::vector AS cos_summary
FROM events_details__quarter_minute, vars
where match_id = 3943043
ORDER BY 6 desc
LIMIT 10;


WITH vars AS ( -- remote embeddings
    SELECT 'Which players recorded the highest number of carries and passes in both halves, 
    and how did their performances influence the overall strategies of the teams?' AS search_string
)
SELECT match_id, period, minute, summary, summary_script
    , summary_embedding_t3_small <=> azure_openai.create_embeddings('text-embedding-3-small', search_string)::vector AS cos_summary_script_t3_small
FROM events_details__quarter_minute, vars
where match_id = 3943043
ORDER BY 6 desc
LIMIT 10;


-- need to enable query store in the database portal
-- connect to azure_sys schema

select * from "query_store"."query_texts" where query_sql_text like 'WITH vars%'
-- query_id -7795894103869418436
select * from "query_store"."query_plans" where query_id = -7795894103869418436

select * from "query_store"."runtime_stats"
where runtime_stats_entry_id in (
    select runtime_stats_entry_id from "query_store"."runtime_stats_entries" where query_id in (
        select query_text_id from "query_store"."query_texts" where query_sql_text like 'WITH vars%'
        )
        and runtime_stats_interval_id = ( select runtime_stats_interval_id from "query_store"."runtime_stats_intervals" order by runtime_stats_interval_id desc limit 1)
)

