

-- con modelo azure_openai.text-embedding-ada-002

UPDATE lineups
SET embeddings = azure_openai.create_embeddings('text-embedding-ada-002', json_)
where id in (
    select id from lineups 
    where embeddings is null and 
    not json_ is null
    limit 10
    )

-- con modelo azure_local_ai: https://huggingface.co/intfloat/multilingual-e5-small

UPDATE lineups
SET embeddings = azure_local_ai.create_embeddings('multilingual-e5-small:v1', json_)
where id in (
    select id from lineups 
    where embeddings is null and 
    not json_ is null
    limit 10
    )


-- con modelo azure_local_ai, los updates se pueden hacer de forma más masiva:
-- ejemplos 

/*

UPDATE matches
SET embeddings = azure_local_ai.create_embeddings('multilingual-e5-small:v1', json_)
where id in (
    select count(*) from matches 
    where embeddings is null and 
    not json_ is null
    limit xxx
    )


UPDATE 250
Total execution time: 00:00:51.810
UPDATE 500
Total execution time: 00:02:18.949

Memory Optimized, E4ds_v5, 4 vCores, 32 GiB RAM, 128 GiB storage

*/