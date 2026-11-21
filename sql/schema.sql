-- PostgreSQL Schema for Swiss Football Economics & Youth Development

DROP TABLE IF EXISTS players CASCADE;
DROP TABLE IF EXISTS clubs CASCADE;
DROP TABLE IF EXISTS municipalities CASCADE;

CREATE TABLE municipalities (
    bfs_id INTEGER PRIMARY KEY,
    municipality_name VARCHAR(120) NOT NULL,
    canton VARCHAR(2) NOT NULL,
    language_region VARCHAR(30) NOT NULL, -- e.g. 'German', 'French', 'Italian'
    postal_code VARCHAR(10),
    population INTEGER,
    youth_share_pct NUMERIC(5,2),
    median_income_chf NUMERIC(12,2),
    tax_strength_index NUMERIC(8,2),
    latitude NUMERIC(9,6),
    longitude NUMERIC(9,6)
);

CREATE TABLE clubs (
    club_id SERIAL PRIMARY KEY,
    club_name VARCHAR(120) NOT NULL UNIQUE,
    league VARCHAR(30) NOT NULL, -- 'Super League' or 'Challenge League'
    season VARCHAR(20) NOT NULL, -- e.g. '2025/26'
    stadium_city VARCHAR(120) NOT NULL,
    postal_code VARCHAR(10),
    bfs_id INTEGER REFERENCES municipalities(bfs_id) ON DELETE SET NULL,
    points INTEGER,
    league_rank INTEGER,
    total_market_value_eur NUMERIC(14,2),
    academy_share_pct NUMERIC(5,2),
    avg_age NUMERIC(4,2)
);

CREATE TABLE players (
    player_id SERIAL PRIMARY KEY,
    club_id INTEGER NOT NULL REFERENCES clubs(club_id) ON DELETE CASCADE,
    player_name VARCHAR(150) NOT NULL,
    age INTEGER,
    position VARCHAR(50),
    nationality VARCHAR(80),
    market_value_eur NUMERIC(12,2),
    is_academy_product BOOLEAN DEFAULT FALSE,
    contract_until DATE
);

CREATE INDEX idx_clubs_bfs_id ON clubs(bfs_id);
CREATE INDEX idx_clubs_league_season ON clubs(league, season);
CREATE INDEX idx_players_club_id ON players(club_id);