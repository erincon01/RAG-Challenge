

DROP TABLE IF EXISTS lineups;


CREATE TABLE lineups (
    id SERIAL PRIMARY KEY,  -- Identificador único de la alineación    
    match_id INTEGER,  -- Relación con la tabla de partidos -- from the filename
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
    embeddings VECTOR(384) NULL  -- Vector de embedding para búsquedas semánticas
);

select * from lineups;


DROP TABLE IF EXISTS players;

CREATE TABLE players (
    id SERIAL PRIMARY KEY,  -- Identificador único de la alineación    
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



DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id SERIAL PRIMARY KEY,         -- Identificador único de la alineación
    match_id INTEGER,              -- Relación con la tabla de partidos
    json_ TEXT NULL
);

select * from events;


DROP TABLE IF EXISTS events_details;

CREATE TABLE events_details (
    id SERIAL PRIMARY KEY,         -- Identificador único de la alineación
    match_id INTEGER,              -- Relación con la tabla de partidos
    id_guid VARCHAR(255) NULL,
    index INT NULL,
    period INT NULL,               -- Período del evento
    timestamp VARCHAR(255) NULL,      -- Marca de tiempo del evento
    minute INT NULL,               -- Minuto del evento
    second INT NULL,               -- Segundo del evento
    type_id INT NULL,               
    type VARCHAR(255) NOT NULL,    -- Tipo de evento
    possession INT NULL,            -- Posesión del balón
    possession_team_id INT NULL,               
    possession_team VARCHAR(255) NOT NULL, -- Equipo en posesión
    play_pattern_id INT NULL,               
    play_pattern VARCHAR(255) NOT NULL,    -- Patrón de juego
    json_ TEXT NULL
);

select count(*) from events_details;
select distinct type from events_details;
select distinct play_pattern from events_details;


DROP TABLE IF EXISTS matches;

CREATE TABLE matches (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    match_date DATE,

    competition_id INTEGER,
    country_name VARCHAR(255),
    competition_name VARCHAR(255),
    season_id INTEGER,
    season_name VARCHAR(255),

    home_team_id INTEGER,
    home_team_name VARCHAR(255),
    home_team_gender VARCHAR(255),
    home_team_country VARCHAR(255),
    home_team_manager VARCHAR(255),
    home_team_mamager_country VARCHAR(255),

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
    referee_name_country VARCHAR(255),

    json_ TEXT NULL
);

select * from matches;

-- indexes creation

create index nci_matches_match_id on matches(match_id);
create index nci_matches_season_id_match_id on matches(season_id, match_id);
create index nci_matches_season_id on matches(season_id);

create index nci_lineups_match_id on lineups(match_id);
create index nci_players_match_id on players(match_id);
create index nci_events_match_id on events(match_id);
create index nci_events_details_match_id on events_details(match_id);






