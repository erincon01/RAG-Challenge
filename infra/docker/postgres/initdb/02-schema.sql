-- PostgreSQL schema for RAG Challenge (local Docker - pgvector)
-- Portable version: no Azure-specific extensions

------------------------------------------------------------
-- matches
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS matches (
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

    referee_id INTEGER,
    referee_name VARCHAR(255),
    referee_country VARCHAR(255),

    json_ TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_matches_match_id ON matches(match_id);
CREATE INDEX IF NOT EXISTS idx_matches_competition ON matches(competition_name, season_name);

------------------------------------------------------------
-- events (raw JSON per match)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    json_ TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_match_id ON events(match_id);

------------------------------------------------------------
-- events_details (parsed individual events)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events_details (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    id_guid VARCHAR(255) NULL,
    index INTEGER NULL,
    period INTEGER NULL,
    timestamp VARCHAR(255) NULL,
    minute INTEGER NULL,
    second INTEGER NULL,
    type_id INTEGER NULL,
    type VARCHAR(255) NULL,
    possession INTEGER NULL,
    possession_team_id INTEGER NULL,
    possession_team VARCHAR(255) NULL,
    play_pattern_id INTEGER NULL,
    play_pattern VARCHAR(255) NULL,
    json_ TEXT NULL
);

CREATE INDEX IF NOT EXISTS idx_events_details_match_id ON events_details(match_id);

------------------------------------------------------------
-- events_details__quarter_minute (15-second aggregation)
-- Embedding columns are plain VECTOR (app-managed, not Azure-generated)
------------------------------------------------------------
CREATE TABLE IF NOT EXISTS events_details__quarter_minute (
    id SERIAL PRIMARY KEY,
    match_id INTEGER,
    period INTEGER,
    minute INTEGER,
    quarter_minute INTEGER,
    count INTEGER,
    json_ TEXT,
    summary TEXT,
    summary_script TEXT,

    -- Embedding columns (populated by application via OpenAI API, not DB-generated)
    summary_embedding_ada_002       VECTOR(1536),  -- text-embedding-ada-002
    summary_embedding_t3_small      VECTOR(1536),  -- text-embedding-3-small
    summary_embedding_t3_large      VECTOR(3072),  -- text-embedding-3-large

    -- Embedding lifecycle tracking
    embedding_status                VARCHAR(20) DEFAULT 'pending',  -- pending | done | error
    embedding_updated_at            TIMESTAMP,
    embedding_error                 TEXT
);

CREATE INDEX IF NOT EXISTS idx_edqm_match_id ON events_details__quarter_minute(match_id);

-- HNSW indexes for vector similarity search
CREATE INDEX IF NOT EXISTS idx_edqm_ada002_cosine
    ON events_details__quarter_minute USING hnsw (summary_embedding_ada_002 vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_edqm_ada002_ip
    ON events_details__quarter_minute USING hnsw (summary_embedding_ada_002 vector_ip_ops);

CREATE INDEX IF NOT EXISTS idx_edqm_t3small_cosine
    ON events_details__quarter_minute USING hnsw (summary_embedding_t3_small vector_cosine_ops);
CREATE INDEX IF NOT EXISTS idx_edqm_t3small_ip
    ON events_details__quarter_minute USING hnsw (summary_embedding_t3_small vector_ip_ops);
