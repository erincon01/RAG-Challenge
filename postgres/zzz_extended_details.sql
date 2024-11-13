

-- extended queries for high level of details

SELECT
    rec.match_id,
    (data->>'index')::INT AS index,
    (data->>'period')::INT AS period,
    data->>'timestamp' AS timestamp,
    (data->>'minute')::INT AS minute,
    (data->>'second')::INT AS second,
    data->'type'->>'name' AS type,
    (data->>'possession')::INT AS possession,
    data->'possession_team'->>'name' AS possession_team,
    data->'play_pattern'->>'name' AS play_pattern,

    data->'team'->>'name' AS team_name,
    data->'player'->>'name' AS player_name,
    data->'position'->>'name' AS position_name,

    data->'duel'->'type'->>'name' AS duel_type,
    data->'duel'->'outcome'->>'name' AS duel_outcome,

    data->'pass'->'height'->>'name' AS pass_height,
    data->'pass'->'body_part'->>'name' AS pass_body_part,
    data->'pass'->'outcome'->>'name' AS pass_body_part,

    data->'shot'->'technique'->>'name' AS shot_technique,
    data->'shot'->'type'->>'name' AS shot_type,
    data->'shot'->'outcome'->>'name' AS shot_outcome,

    data AS json_
FROM 
    events AS rec,
    jsonb_array_elements(rec.json_::jsonb) AS data
WHERE 
    rec.match_id = 3943043
LIMIT 1000;

