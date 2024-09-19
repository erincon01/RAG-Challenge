-- USE THIS SCRIPT TO CREATE THE TABLES INTO SQLITE
-- This script creates the base tables for the football data
-- An embedding column is added to be used for semantic searches

DROP TABLE IF EXISTS matches;

-- Create the 'matches' table
CREATE TABLE matches (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    match_date TEXT, 

    competition_id INTEGER,
    competition_country TEXT,
    competition_name TEXT,
    season_id INTEGER,
    season_name TEXT,

    home_team_id INTEGER,
    home_team_name TEXT,
    home_team_gender TEXT,
    home_team_country TEXT,
    home_team_manager TEXT,
    home_team_manager_country TEXT,

    away_team_id INTEGER,
    away_team_name TEXT,
    away_team_gender TEXT,
    away_team_country TEXT,
    away_team_manager TEXT,
    away_team_manager_country TEXT,

    home_score INTEGER,
    away_score INTEGER,
    result TEXT,
    match_week INTEGER,

    stadium_id INTEGER,
    stadium_name TEXT,
    stadium_country TEXT,

    referee_id INTEGER,
    referee_name TEXT,
    referee_country TEXT,

    json_ TEXT NULL
);

-- Drop the 'lineups' table if it already exists
DROP TABLE IF EXISTS lineups;

-- Create the 'lineups' table
CREATE TABLE lineups (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    home_team_id INTEGER NOT NULL,
    home_team_name TEXT NOT NULL,
    away_team_id INTEGER NOT NULL,
    away_team_name TEXT NOT NULL,

    -- Data
    json_ TEXT NULL
);

-- Select all rows from the 'lineups' table
SELECT * FROM lineups;

DROP TABLE IF EXISTS players;

-- Create the 'players' table
CREATE TABLE players (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER NOT NULL,
    team_id INTEGER NOT NULL,
    team_name TEXT NOT NULL,
    player_id INTEGER NOT NULL,
    player_name TEXT NOT NULL,
    jersey_number INTEGER,
    country_id INTEGER,
    country_name TEXT,
    position_id INTEGER,
    position_name TEXT,
    from_time TEXT,
    to_time TEXT,
    from_period TEXT,
    to_period TEXT,
    start_reason TEXT,
    end_reason TEXT
);

-- Drop the 'events' table if it already exists
DROP TABLE IF EXISTS events;

-- Create the 'events' table
CREATE TABLE events (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    json_ TEXT NULL
);

-- Drop the 'events_details' table if it already exists
DROP TABLE IF EXISTS events_details;

-- Create the 'events_details' table
CREATE TABLE events_details (
    id INTEGER PRIMARY KEY AUTOINCREMENT,
    match_id INTEGER,
    id_guid TEXT NULL,
    index_ INTEGER NULL,
    period INTEGER NULL,
    timestamp TEXT NULL,
    minute INTEGER NULL,
    second INTEGER NULL,
    type_id INTEGER NULL,
    type TEXT NULL,
    possession INTEGER NULL,
    possession_team_id INTEGER NULL,
    possession_team TEXT NULL,
    play_pattern_id INTEGER NULL,
    play_pattern TEXT NULL,

    -- Data
    json_ TEXT NULL
);

-- Create indexes
CREATE INDEX nci_matches_match_id ON matches(match_id);
CREATE INDEX nci_matches_season_id_match_id ON matches(season_id, match_id);
CREATE INDEX nci_matches_season_id ON matches(season_id);

CREATE INDEX nci_lineups_match_id ON lineups(match_id);
CREATE INDEX nci_players_match_id ON players(match_id);

CREATE INDEX nci_events_match_id ON events(match_id);
CREATE INDEX nci_events_details_match_id ON events_details(match_id);
