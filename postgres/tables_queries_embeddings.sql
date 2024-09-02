-- Retrieve top similarity match
-- azure_openai: text-embedding-ada-002
SELECT * FROM
    lineups e
ORDER BY
    e.embeddings <#> azure_openai.create_embeddings('text-embedding-ada-002', 'started position as Left Midfield and then changed position to Center Forward')::vector
LIMIT 10;


-- Retrieve top similarity match
-- azure_local_ai: https://huggingface.co/intfloat/multilingual-e5-small
SELECT * FROM
    lineups e
ORDER BY
    e.embeddings <#> azure_local_ai.create_embeddings('multilingual-e5-small:v1', 'started position as Left Midfield and then changed position to Center Forward')::vector
LIMIT 10;

