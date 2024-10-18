-- USE THIS SCRIPT TO CREATE THE TABLES INTO SQLITE
-- This script creates the base tables for the football data.
-- An embedding column is added to be used for semantic searches.

-- Drop the 'events_details' table if it already exists
DROP TABLE IF EXISTS events_details;

-- Create the 'events_details' table
CREATE TABLE events_details (
    [match_id] INTEGER, 
    [id_guid] TEXT, 
    [index_] INTEGER, 
    [period] INTEGER, 
    [timestamp] TEXT, 
    [minute] INTEGER, 
    [second] INTEGER, 
    [type_id] INTEGER, 
    [type] TEXT, 
    [possession] INTEGER, 
    [possession_team_id] INTEGER, 
    [possession_team] TEXT, 
    [play_pattern_id] INTEGER, 
    [play_pattern] TEXT, 
    [json_] TEXT
);

-- Drop the index on 'events_details' if it already exists
DROP INDEX IF EXISTS [nci_events_details_match_id];

-- Create an index on 'match_id' in the 'events_details' table
CREATE INDEX [nci_events_details_match_id] ON [events_details] (match_id);

-- Drop the 'events_details__minute_agg' table if it already exists
DROP TABLE IF EXISTS events_details__minute_agg;

-- Create the 'events_details__minute_agg' table
CREATE TABLE events_details__minute_agg (
    [match_id] INTEGER, 
    [period] INTEGER, 
    [minute] INTEGER, 
    [count] INTEGER, 
    [json_] TEXT,
    [summary] TEXT,
    PRIMARY KEY (match_id, period, minute)
);

-- Drop the 'events_details__15secs_agg' table if it already exists
DROP TABLE IF EXISTS events_details__15secs_agg;

-- Create the 'events_details__15secs_agg' table
CREATE TABLE events_details__15secs_agg (
    [match_id] INTEGER, 
    [period] INTEGER, 
    [minute] INTEGER, 
    [_15secs] INTEGER, 
    [count] INTEGER, 
    [json_] TEXT,
    [summary] TEXT,
    PRIMARY KEY (match_id, period, minute, _15secs)
);
