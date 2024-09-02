


/*

select * from lineups limit 10;
select * from events limit 10;
select * from events_details limit 10;

*/

-- https://learn.microsoft.com/en-us/azure/postgresql/flexible-server/generative-ai-azure-openai

UPDATE lineups
SET embeddings = azure_openai.create_embeddings('text-embedding-ada-002', json_)

-- ERROR MESSAGE
-- azure_openai.create_embeddings: 429: Requests to the Embeddings_Create Operation under Azure OpenAI API version 2024-03-01-preview have exceeded call rate limit of your current 
-- OpenAI S0 pricing tier. Please retry after 46 seconds. Please go here: https://aka.ms/oai/quotaincrease if you would like to further increase the default rate limit.

--
-- lineups
--

-- en lotes de 10 filas

DO $$
DECLARE
    batch_size INTEGER := 10;
    affected_rows INTEGER;
    total_updated INTEGER := 0;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    start_time := clock_timestamp();

    LOOP
        WITH rows_to_update AS (
            SELECT id, json_
            FROM lineups
            WHERE embeddings IS NULL
            ORDER BY id
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        UPDATE lineups l
        SET embeddings = azure_openai.create_embeddings('text-embedding-ada-002', rows_to_update.json_)
        FROM rows_to_update
        WHERE l.id = rows_to_update.id;

        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        total_updated := total_updated + affected_rows;

        RAISE NOTICE 'Filas actualizadas en este lote: %', affected_rows;

        EXIT WHEN affected_rows = 0;

        PERFORM pg_sleep(3);  -- Pausa de 3 segundos entre lotes
    END LOOP;

    end_time := clock_timestamp();

    RAISE NOTICE 'Proceso completado. Total de filas actualizadas: %. Tiempo total: %',
                 total_updated, 
                 age(end_time, start_time);
END $$;


SELECT COUNT(*) FROM lineups where embeddings is null;
SELECT * FROM  lineups limit 10;


-- Alternativamente columna calculada

/*

ALTER TABLE lineups
ADD COLUMN embeddings2 vector(1536) -- multilingual-e5 embeddings are 384 dimensions
GENERATED ALWAYS AS (azure_openai.create_embeddings('text-embedding-ada-002', json_)::vector) STORED;

-- DIFICIL de implementar porque rebasa el límite para llamadas a openai.
-- azure_openai.create_embeddings: 429: Requests to the Embeddings_Create Operation under Azure OpenAI API version 2024-03-01-preview have exceeded 
-- call rate limit of your current OpenAI S0 pricing tier. Please retry after 16 seconds. Please go here: https://aka.ms/oai/quotaincrease if you would like to further increase the default rate limit.

*/


--
-- events_details
--

-- en lotes de 10 filas

DO $$
DECLARE
    batch_size INTEGER := 10;
    affected_rows INTEGER;
    total_updated INTEGER := 0;
    start_time TIMESTAMP;
    end_time TIMESTAMP;
BEGIN
    start_time := clock_timestamp();

    LOOP
        WITH rows_to_update AS (
            SELECT id, json_
            FROM events_details
            WHERE embeddings IS NULL
            ORDER BY id
            LIMIT batch_size
            FOR UPDATE SKIP LOCKED
        )
        UPDATE events_details l
        SET embeddings = azure_openai.create_embeddings('text-embedding-ada-002', rows_to_update.json_)
        FROM rows_to_update
        WHERE l.id = rows_to_update.id;

        GET DIAGNOSTICS affected_rows = ROW_COUNT;
        total_updated := total_updated + affected_rows;

        RAISE NOTICE 'Filas actualizadas en este lote: %', affected_rows;

        EXIT WHEN affected_rows = 0;

        PERFORM pg_sleep(3);  -- Pausa de 3 segundos entre lotes
    END LOOP;

    end_time := clock_timestamp();

    RAISE NOTICE 'Proceso completado. Total de filas actualizadas: %. Tiempo total: %',
                 total_updated, 
                 age(end_time, start_time);
END $$;


SELECT COUNT(*) FROM events_details;
SELECT COUNT(*) FROM events_details where embeddings is null;
SELECT * FROM  events_details limit 10;


