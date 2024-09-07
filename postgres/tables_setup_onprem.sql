

-- Drop the 'matches' table if it already exists
DROP TABLE IF EXISTS matches;

-- Create the 'matches' table
CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
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

    json_ TEXT NULL
);

select * from matches;


DROP TABLE IF EXISTS lineups;


CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    home_team_id INTEGER NOT NULL,
    home_team_name VARCHAR(255) NOT NULL,
    away_team_id INTEGER NOT NULL,
    away_team_name VARCHAR(255) NOT NULL,

    -- data
    json_ TEXT NULL
);

select * from lineups;

DROP TABLE IF EXISTS players;

CREATE TABLE players (
    id SERIAL PRIMARY KEY,    
    match_id int NOT NULL,
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

select * from lineups;
select * from players;


-- Drop the 'events' table if it already exists
DROP TABLE IF EXISTS events;

-- Create the 'events' table
CREATE TABLE events (
    id SERIAL PRIMARY KEY,         
    match_id INTEGER,    
    
    -- data          
    json_ TEXT NULL
);

select * from events;

DROP TABLE IF EXISTS events_details;

CREATE TABLE events_details (
    id SERIAL PRIMARY KEY,         
    match_id INTEGER,              
    id_guid VARCHAR(255) NULL,
    index INT NULL,
    period INT NULL,               
    timestamp VARCHAR(255) NULL,   
    minute INT NULL,               
    second INT NULL,               
    type_id INT NULL,               
    type VARCHAR(255) NOT NULL,    
    possession INT NULL,            
    possession_team_id INT NULL,               
    possession_team VARCHAR(255) NOT NULL, 
    play_pattern_id INT NULL,               
    play_pattern VARCHAR(255) NOT NULL,    

    -- data          
    json_ TEXT NULL
);

select * from events_details;

-- indexes creation

create index nci_matches_match_id on matches(match_id);
create index nci_matches_season_id_match_id on matches(season_id, match_id);
create index nci_matches_season_id on matches(season_id);

create index nci_lineups_match_id on lineups(match_id);
create index nci_players_match_id on players(match_id);


create index nci_events_match_id on events(match_id);
create index nci_events_details_match_id on events_details(match_id);


select count(*) c_matches from matches;
select count(*) c_lineups from lineups;
select count(*) c_players from players;
select count(*) c_events from events;
select count(*) c_events_details from events_details;
