
-- Aggregate the events by match_id, period, minute, and 15-second intervals (json_ is the column with the event details that is concatenated)
-- For this RAG_Challenge, we will only process the games from Euro 2024, Copa America 2024, and FIFA World Cup 2022

DROP TABLE IF EXISTS events_details__15secs_agg;
GO

CREATE TABLE events_details__15secs_agg
(
    match_id BIGINT,
    period INT,
    minute INT,
    _15secs INT,
    count INT,
    json_ NVARCHAR(MAX),
    PRIMARY KEY (match_id, period, minute, _15secs)
);

INSERT INTO events_details__15secs_agg
(
    match_id,
    period,
    minute,
    _15secs,
    count,
    json_
)
SELECT 
    match_id,
    period,
    minute,
    (second / 15) + 1 AS _15secs,
    count(*) AS count,
    STRING_AGG(json_, ', ') AS json_
FROM
    events_details
WHERE 
    match_id IN (SELECT match_id FROM matches WHERE competition_name = 'UEFA Euro' AND season_name = '2024')
    OR match_id IN (SELECT match_id FROM matches WHERE competition_name = 'Copa America' AND season_name = '2024')
    OR match_id IN (SELECT match_id FROM matches WHERE competition_name = 'FIFA World Cup' AND season_name = '2022')
GROUP BY
    match_id,
    period,
    minute,
    (second / 15) + 1;
GO

ALTER TABLE events_details__15secs_agg
ADD summary NVARCHAR(MAX);

ALTER TABLE events_details__15secs_agg
ADD embedding_3_small VECTOR(1536);

ALTER TABLE events_details__15secs_agg
ADD embedding_ada_002 VECTOR(1536);

ALTER TABLE events_details__15secs_agg
ADD id INT IDENTITY;

/*

no indexes created for embeddings

*/
