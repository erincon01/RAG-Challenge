

UPDATE lineups
SET embeddings = azure_openai.create_embeddings('text-embedding-ada-002', json_)
where id in (
    select id from lineups 
    where embeddings is null and 
    not json_ is null
    limit 1
    )

