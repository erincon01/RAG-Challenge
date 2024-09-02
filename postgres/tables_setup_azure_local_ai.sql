

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

DROP TABLE IF EXISTS events;

CREATE TABLE events (
    id SERIAL PRIMARY KEY,         -- Identificador único de la alineación
    match_id INTEGER,              -- Relación con la tabla de partidos
    json_ TEXT NULL,
    embeddings VECTOR(384) NULL  -- Vector de embedding para búsquedas semánticas
);

select * from events;


DROP TABLE IF EXISTS events_details;

CREATE TABLE events_details (
    id SERIAL PRIMARY KEY,         -- Identificador único de la alineación
    match_id INTEGER,              -- Relación con la tabla de partidos
    timestamp VARCHAR(255) NULL,      -- Marca de tiempo del evento
    period INT NULL,               -- Período del evento
    type VARCHAR(255) NOT NULL,    -- Tipo de evento
    possession_team VARCHAR(255) NOT NULL, -- Equipo en posesión
    play_pattern VARCHAR(255) NOT NULL,    -- Patrón de juego
    team VARCHAR(255) NOT NULL,    -- Equipo involucrado en el evento
    json_ TEXT NULL,
    embeddings VECTOR(384) NULL  -- Vector de embedding para búsquedas semánticas
);

select * from events_details;

DROP TABLE IF EXISTS matches;

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
    embeddings VECTOR(384) NULL  -- Vector de embedding para búsquedas semánticas
);

select * from matches;