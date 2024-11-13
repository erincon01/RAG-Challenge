-- USE THIS SCRIPT TO CREATE THE TABLES INTO SQL PAAS
-- This script creates the base tables for the football data.
-- An embedding column is added to be used for semantic searches.
-- The embedding column is a vector of 1536 floats.
-- Embeddings will be calculated later on.

-- Drop the 'matches' table if it already exists
DROP TABLE IF EXISTS matches;

-- Create the 'matches' table
CREATE TABLE matches (
    id INT IDENTITY PRIMARY KEY,
    match_id INTEGER,
    match_date DATE,

    competition_id INTEGER,
    competition_country VARCHAR(255),
    competition_name VARCHAR(255),
    season_id INTEGER,
    season_name VARCHAR(255),

    home_team_id INTEGER,
    home_team_name VARCHAR(255),
    home_team_gender VARCHAR(255),
    home_team_country VARCHAR(255),
    home_team_manager VARCHAR(255),
    home_team_manager_country VARCHAR(255),

    away_team_id INTEGER,
    away_team_name VARCHAR(255),
    away_team_gender VARCHAR(255),
    away_team_country VARCHAR(255),
    away_team_manager VARCHAR(255),
    away_team_manager_country VARCHAR(255),

    home_score INTEGER,
    away_score INTEGER,
    result VARCHAR(255),
    match_week INTEGER,

    stadium_id INTEGER,
    stadium_name VARCHAR(255),
    stadium_country VARCHAR(255),

    referee_id INT,
    referee_name VARCHAR(255),
    referee_country VARCHAR(255),

    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

CREATE NONCLUSTERED INDEX nci_competition_name_seasion_name
ON [dbo].[matches] ([competition_name],[season_name])
INCLUDE ([match_id],[home_team_name],[away_team_name],[home_score],[away_score]);

-- Select all rows from the 'matches' table
SELECT * FROM matches;

-- Drop the 'lineups' table if it already exists
DROP TABLE IF EXISTS lineups;

-- Create the 'lineups' table
CREATE TABLE lineups (
    id INT IDENTITY PRIMARY KEY,
    match_id INTEGER,
    home_team_id INTEGER NOT NULL,
    home_team_name VARCHAR(255) NOT NULL,
    away_team_id INTEGER NOT NULL,
    away_team_name VARCHAR(255) NOT NULL,

    -- Data
    json_ TEXT NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'lineups' table
SELECT * FROM lineups;

-- Drop the 'players' table if it already exists
DROP TABLE IF EXISTS players;

-- Create the 'players' table
CREATE TABLE players (
    id INT IDENTITY PRIMARY KEY,    
    match_id INT NOT NULL,
    team_id INT NOT NULL,
    team_name VARCHAR(255) NOT NULL,
    player_id INT NOT NULL,
    player_name VARCHAR(255) NOT NULL,
    jersey_number INT,
    country_id INT,
    country_name VARCHAR(255),
    position_id INT,
    position_name VARCHAR(255),
    from_time VARCHAR(10),
    to_time VARCHAR(10),
    from_period VARCHAR(255),
    to_period VARCHAR(255),
    start_reason VARCHAR(255),
    end_reason VARCHAR(255)
);

-- Select all rows from the 'players' table
SELECT * FROM players;

-- Drop the 'events' table if it already exists
DROP TABLE IF EXISTS events;

-- Create the 'events' table
CREATE TABLE events (
    id INT IDENTITY PRIMARY KEY,         
    match_id INTEGER,              
    json_ NVARCHAR(MAX) NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'events' table
SELECT * FROM events;

-- Drop the 'events_details' table if it already exists
DROP TABLE IF EXISTS events_details;

-- Create the 'events_details' table
CREATE TABLE events_details (
    id INT IDENTITY PRIMARY KEY,         
    match_id INTEGER,              
    id_guid VARCHAR(255) NULL,
    index_ INT NULL,
    period INT NULL,               
    timestamp VARCHAR(255) NULL,   
    minute INT NULL,               
    second INT NULL,               
    type_id INT NULL,               
    type VARCHAR(255) NULL,    
    possession INT NULL,            
    possession_team_id INT NULL,               
    possession_team VARCHAR(255) NULL, 
    play_pattern_id INT NULL,               
    play_pattern VARCHAR(255) NULL, 

    -- Data          
    json_ NVARCHAR(MAX) NULL,
    embeddings VECTOR(1536) NULL  -- Embedding vector for semantic searches
);

-- Select all rows from the 'events_details' table
SELECT * FROM events_details;

-- Indexes creation
CREATE INDEX nci_matches_match_id ON matches(match_id);
CREATE INDEX nci_matches_season_id_match_id ON matches(season_id, match_id);
CREATE INDEX nci_matches_season_id ON matches(season_id);

CREATE INDEX nci_lineups_match_id ON lineups(match_id);
CREATE INDEX nci_players_match_id ON players(match_id);

CREATE INDEX nci_events_match_id ON events(match_id);
CREATE INDEX nci_events_details_match_id ON events_details(match_id);
