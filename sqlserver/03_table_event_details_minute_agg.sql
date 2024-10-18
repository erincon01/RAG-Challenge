
-- Drop the existing table if it exists
DROP TABLE IF EXISTS events_details__minute_agg;
GO

-- Create a new table to aggregate event details by match_id, period, and minute
CREATE TABLE events_details__minute_agg
(
    match_id BIGINT,
    period INT,
    minute INT,
    count INT,
    json_ NVARCHAR(MAX),
    PRIMARY KEY (match_id, period, minute)
);

-- Insert aggregated event details into the new table
INSERT INTO events_details__minute_agg
(
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
WHERE 
    match_id IN (SELECT match_id FROM matches WHERE competition_name = 'UEFA Euro' AND season_name = '2024')
    OR match_id IN (SELECT match_id FROM matches WHERE competition_name = 'Copa America' AND season_name = '2024')
    OR match_id IN (SELECT match_id FROM matches WHERE competition_name = 'FIFA World Cup' AND season_name = '2022')
GROUP BY
    match_id,
    period,
    minute;
GO

-- Add additional columns to the table
ALTER TABLE events_details__minute_agg
ADD summary NVARCHAR(MAX);

ALTER TABLE events_details__minute_agg
ADD embedding_3_small VECTOR(1536);

ALTER TABLE events_details__minute_agg
ADD embedding_ada_002 VECTOR(1536);

ALTER TABLE events_details__minute_agg
ADD id INT IDENTITY;

/*
no indexes created for embeddings

*/