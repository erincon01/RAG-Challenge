-- SQL Server schema for RAG Challenge (local Docker - SQL Server 2025 Express)
-- Portable version for local development

IF NOT EXISTS (SELECT * FROM sys.databases WHERE name = 'rag_challenge')
BEGIN
    CREATE DATABASE rag_challenge;
END;
GO

USE rag_challenge;
GO

------------------------------------------------------------
-- matches
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'matches')
BEGIN
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
        embeddings VECTOR(1536) NULL
    );

    CREATE NONCLUSTERED INDEX nci_competition_name_season_name
        ON matches (competition_name, season_name)
        INCLUDE (match_id, home_team_name, away_team_name, home_score, away_score);

    CREATE INDEX nci_matches_match_id ON matches(match_id);
END;
GO

------------------------------------------------------------
-- lineups
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'lineups')
BEGIN
    CREATE TABLE lineups (
        id INT IDENTITY PRIMARY KEY,
        match_id INTEGER,
        home_team_id INTEGER NOT NULL,
        home_team_name VARCHAR(255) NOT NULL,
        away_team_id INTEGER NOT NULL,
        away_team_name VARCHAR(255) NOT NULL,
        json_ TEXT NULL,
        embeddings VECTOR(1536) NULL
    );

    CREATE INDEX nci_lineups_match_id ON lineups(match_id);
END;
GO

------------------------------------------------------------
-- players
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'players')
BEGIN
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

    CREATE INDEX nci_players_match_id ON players(match_id);
END;
GO

------------------------------------------------------------
-- events (raw JSON per match)
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'events')
BEGIN
    CREATE TABLE events (
        id INT IDENTITY PRIMARY KEY,
        match_id INTEGER,
        json_ NVARCHAR(MAX) NULL,
        embeddings VECTOR(1536) NULL
    );

    CREATE INDEX nci_events_match_id ON events(match_id);
END;
GO

------------------------------------------------------------
-- events_details
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'events_details')
BEGIN
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
        json_ NVARCHAR(MAX) NULL,
        embeddings VECTOR(1536) NULL
    );

    CREATE INDEX nci_events_details_match_id ON events_details(match_id);
END;
GO

------------------------------------------------------------
-- events_details__15secs_agg (15-second aggregation)
------------------------------------------------------------
IF NOT EXISTS (SELECT * FROM sys.tables WHERE name = 'events_details__15secs_agg')
BEGIN
    CREATE TABLE events_details__15secs_agg (
        id INT IDENTITY,
        match_id BIGINT,
        period INT,
        minute INT,
        _15secs INT,
        count INT,
        json_ NVARCHAR(MAX),
        summary NVARCHAR(MAX),
        embedding_3_small VECTOR(1536),
        embedding_ada_002 VECTOR(1536),
        -- Embedding lifecycle tracking
        embedding_status VARCHAR(20) DEFAULT 'pending',  -- pending | done | error
        embedding_updated_at DATETIME2,
        embedding_error NVARCHAR(MAX),
        PRIMARY KEY (match_id, period, minute, _15secs)
    );
END;
GO

PRINT 'RAG Challenge database schema initialized successfully.';
GO
