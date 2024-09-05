
-- Drop the 'lineups' table if it already exists
DROP TABLE IF EXISTS lineups;

-- Create the 'lineups' table
CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,  -- Unique identifier for the lineup
    match_id INTEGER,  -- Relationship with the 'matches' table -- from the filename
    -- from the lineups
    home_team_id INTEGER NOT NULL,
    home_team_name VARCHAR(255) NOT NULL,
    away_team_id INTEGER NOT NULL,
    away_team_name VARCHAR(255) NOT NULL,
    -- from the match
    -- home_team_id INTEGER NULL,
    -- away_team_id INTEGER NULL,
    -- home_score INTEGER NULL,
    -- away_score INTEGER NULL,
    -- data
    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'lineups' table
SELECT * FROM lineups;

-- Drop the 'events' table if it already exists
DROP TABLE IF EXISTS events;

-- Create the 'events' table
CREATE TABLE events (
    id SERIAL PRIMARY KEY,         -- Unique identifier for the event
    match_id INTEGER,              -- Relationship with the 'matches' table
    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'events' table
SELECT * FROM events;

-- Drop the 'events_details' table if it already exists
DROP TABLE IF EXISTS events_details;

-- Create the 'events_details' table
CREATE TABLE events_details (
    id SERIAL PRIMARY KEY,         -- Unique identifier for the event details
    match_id INTEGER,              -- Relationship with the 'matches' table
    timestamp VARCHAR(255) NULL,      -- Timestamp of the event
    period INT NULL,               -- Event period
    type VARCHAR(255) NOT NULL,    -- Event type
    possession_team VARCHAR(255) NOT NULL, -- Team in possession
    play_pattern VARCHAR(255) NOT NULL,    -- Play pattern
    team VARCHAR(255) NOT NULL,    -- Team involved in the event
    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'events_details' table
SELECT * FROM events_details;

-- Drop the 'matches' table if it already exists
DROP TABLE IF EXISTS matches;

-- Create the 'matches' table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    match_date DATE,
    competition_id INTEGER,
    competition_name VARCHAR(255),
    season_id INTEGER,
    season_name VARCHAR(255),
    home_team_id INTEGER,
    home_team_name VARCHAR(255),
    away_team_id INTEGER,
    away_team_name VARCHAR(255),
    home_score INTEGER,
    away_score INTEGER,
    stadium_id INTEGER,
    stadium_name VARCHAR(255),
    referee_id INTEGER,
    referee_name VARCHAR(255),
    result VARCHAR(255),
    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'matches' table
SELECT * FROM matches;