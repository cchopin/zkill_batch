-- Start the server
-- brew services start postgresql@14
-- Creation of the database
CREATE DATABASE ${DB_NAME};

-- Connect to the database
\c ${DB_NAME}

-- Create enum for kill types
CREATE TYPE kill_type AS ENUM ('KILL', 'LOSS');

-- Create systems table to store unique system information
CREATE TABLE systems (
    system_id SERIAL PRIMARY KEY,
    system_name VARCHAR(100) NOT NULL,
    UNIQUE(system_name)
);

-- Create ship_types table to store unique ship type information
CREATE TABLE ship_types (
    ship_type_id SERIAL PRIMARY KEY,
    type_name VARCHAR(100) NOT NULL,
    UNIQUE(type_name)
);

-- Create ships table to store unique ship information
CREATE TABLE ships (
    ship_id SERIAL PRIMARY KEY,
    ship_name VARCHAR(100) NOT NULL,
    ship_type_id INTEGER REFERENCES ship_types(ship_type_id),
    UNIQUE(ship_name)
);

-- Create pilots table to store unique pilot information
CREATE TABLE pilots (
    pilot_id SERIAL PRIMARY KEY,
    pilot_name VARCHAR(100) NOT NULL,
    UNIQUE(pilot_name)
);

-- Create main killmails table
CREATE TABLE killmails (
    killmail_id BIGINT PRIMARY KEY,
    kill_hash VARCHAR(64) NOT NULL,
    kill_datetime TIMESTAMP NOT NULL,
    system_id INTEGER REFERENCES systems(system_id),
    pilot_id INTEGER REFERENCES pilots(pilot_id),
    ship_id INTEGER REFERENCES ships(ship_id),
    value DECIMAL(20, 2) NOT NULL,
    kill_type kill_type NOT NULL,
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    UNIQUE(kill_hash)
);

-- Create indexes for better query performance
CREATE INDEX idx_killmails_datetime ON killmails(kill_datetime);
CREATE INDEX idx_killmails_value ON killmails(value);
CREATE INDEX idx_ships_type ON ships(ship_type_id);

-- Create view for easy querying of kill information
CREATE VIEW kill_details AS
SELECT
    k.killmail_id,
    k.kill_datetime,
    s.system_name,
    p.pilot_name,
    sh.ship_name,
    st.type_name as ship_type,
    k.value,
    k.kill_type
FROM killmails k
JOIN systems s ON k.system_id = s.system_id
JOIN pilots p ON k.pilot_id = p.pilot_id
JOIN ships sh ON k.ship_id = sh.ship_id
JOIN ship_types st ON sh.ship_type_id = st.ship_type_id;

-- Création de la table corporations
CREATE TABLE corporations (
    corporation_id SERIAL PRIMARY KEY,
    corporation_name VARCHAR(100) NOT NULL,
    UNIQUE(corporation_name)
);

-- Ajout de la colonne pour la corporation de la victime dans killmails
ALTER TABLE killmails
ADD COLUMN victim_corporation_id INTEGER REFERENCES corporations(corporation_id);


-- Création de la table killmail_attackers
CREATE TABLE killmail_attackers (
    killmail_attacker_id SERIAL PRIMARY KEY,
    killmail_id BIGINT REFERENCES killmails(killmail_id) ON DELETE CASCADE,
    pilot_id INTEGER,  -- Optionnel : référence vers la table pilots (pour les données globales du pilote)
    pilot_name VARCHAR(100) NOT NULL,
    attacker_corporation_id INTEGER REFERENCES corporations(corporation_id),
    final_blow BOOLEAN,
    damage_done DECIMAL(20,2)
);

-- Create user with environment variables
CREATE USER ${DB_USER} WITH PASSWORD '${DB_PASSWORD}';
GRANT ALL PRIVILEGES ON DATABASE ${DB_NAME} TO ${DB_USER};
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO ${DB_USER};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
GRANT ALL PRIVILEGES ON TABLE killmail_attackers TO ${DB_USER};
GRANT ALL PRIVILEGES ON TABLE corporations TO ${DB_USER};
GRANT USAGE, SELECT ON ALL SEQUENCES IN SCHEMA public TO ${DB_USER};
