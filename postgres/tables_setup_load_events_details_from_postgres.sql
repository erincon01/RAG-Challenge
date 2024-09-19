/*
    This SQL code block is responsible for loading event details from a PostgreSQL table into another table called events_details.
    It uses a cursor to iterate over the records in the events table and inserts the corresponding data into the events_details table.
    The inserted data includes various attributes such as match_id, id_guid, index, period, timestamp, minute, second, type_id, type, possession, possession_team_id, possession_team, play_pattern_id, play_pattern, and json_.
    After each insertion, it raises a notice message indicating the processed match_id and the total number of records inserted for that match_id.
*/
DO $$
DECLARE
    cur CURSOR FOR
        SELECT *
        FROM events;
    rec RECORD;
BEGIN
    OPEN cur;
    LOOP
        FETCH cur INTO rec;
        EXIT WHEN NOT FOUND;

        -- Inserta en events_details
        INSERT INTO events_details (
            match_id,
            id_guid,
            index,
            period,
            timestamp,
            minute,
            second,
            type_id,
            type,
            possession,
            possession_team_id,
            possession_team,
            play_pattern_id,
            play_pattern,
            json_
        )
        SELECT
            rec.match_id,
            data->>'id' AS id_guid,
            (data->>'index')::INT AS index,
            (data->>'period')::INT AS period,
            data->>'timestamp' AS timestamp,
            (data->>'minute')::INT AS minute,
            (data->>'second')::INT AS second,
            (data->'type'->>'id')::INT AS type_id,
            data->'type'->>'name' AS type,
            (data->>'possession')::INT AS possession,
            (data->'possession_team'->>'id')::INT AS possession_team_id,
            data->'possession_team'->>'name' AS possession_team,
            (data->'play_pattern'->>'id')::INT AS play_pattern_id,
            data->'play_pattern'->>'name' AS play_pattern,
            data AS json_
        FROM jsonb_array_elements((rec.json_)::jsonb) AS elem(data);

        -- Imprime información sobre las filas afectadas
        RAISE NOTICE 'Processed match_id: %, Total records inserted: %',
            rec.match_id,
            (SELECT COUNT(*) FROM events_details WHERE match_id = rec.match_id);

    END LOOP;
    CLOSE cur;
END $$;
