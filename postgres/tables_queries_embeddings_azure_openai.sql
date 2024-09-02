-- Retrieve top similarity match
SELECT * FROM
    lineups e
ORDER BY
    e.embeddings <#> azure_openai.create_embeddings('text-embedding-ada-002', 'started position as Left Midfield and then changed position to Center Forward')::vector
LIMIT 10;



