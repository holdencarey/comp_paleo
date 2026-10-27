-- schema.sql
-- Tiputini Mammalian Database
-- Author: Holden Carey
-- Date:   October 27, 2026
-- Week 9: PostgreSQL version of the Week 8 schema
--
-- Changes from Week 8 (SQLite):
--   * Removed PRAGMA foreign_keys = ON (SQLite-only; Postgres always enforces FKs)
--   * INTEGER PRIMARY KEY -> SERIAL PRIMARY KEY (Postgres needs SERIAL to auto-number)
--   * Dates stored as DATE and times as TIME instead of TEXT, so Postgres
--     rejects impossible values like '2025-02-30' or '25:00'
--
-- Changes prompted by loading the real camera trap data (RecordOfSightings.csv):
--   * taxonomic_rank also allows 'class', for records only identified as "Mammalia"
--   * deployment coordinates come from monitor_locations.csv, matched by MonitorID
--   * lat/long use DOUBLE PRECISION: Postgres REAL keeps only ~6 digits and was
--     rounding coordinates (SQLite REAL is already double precision)
--   * camera_detections gains identified_by, needs_review and notes,
--     which the field data records for every video
--
-- Run with:  psql -d tiputini -f schema.sql

-- Drop in reverse dependency order (children before parents)
DROP TABLE IF EXISTS event_persons;
DROP TABLE IF EXISTS event_taxa;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS occurrences;
DROP TABLE IF EXISTS camera_detections;
DROP TABLE IF EXISTS deployments;
DROP TABLE IF EXISTS observers;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS taxa;


-- taxa
-- Each mammal taxon recorded at TBS, including Homo sapiens.
CREATE TABLE taxa (
    -- Primary key
    taxon_id        SERIAL  PRIMARY KEY,

    -- Required fields
    scientific_name TEXT    NOT NULL UNIQUE
                    CHECK (length(trim(scientific_name)) > 0),  -- rationale: blocks blank names

    -- Controlled vocabulary
    taxonomic_rank  TEXT    NOT NULL DEFAULT 'species'
                    CHECK (taxonomic_rank IN ('species','genus','family','order','class')),

    -- Optional fields
    common_name     TEXT                       -- NULL permitted: many taxa have no common name
);


-- person
-- Community members who take part in human activity events.
CREATE TABLE person (
    -- Primary key
    person_id       SERIAL  PRIMARY KEY,

    -- Required fields
    name            TEXT    NOT NULL
                    CHECK (length(trim(name)) > 0),  -- name or pseudonym; not UNIQUE, names can repeat

    -- Controlled vocabulary
    sex             TEXT                       -- NULL permitted: not always recorded
                    CHECK (sex IN ('male','female')),

    -- Optional fields
    age             INTEGER                    -- NULL permitted: age unknown
                    CHECK (age BETWEEN 0 AND 120)
);


-- observers
-- Researchers who record sightings and events.
CREATE TABLE observers (
    -- Primary key
    observer_id     SERIAL  PRIMARY KEY,

    -- Required fields
    name            TEXT    NOT NULL
                    CHECK (length(trim(name)) > 0),

    -- Optional fields
    affiliation     TEXT                       -- NULL permitted: independent or not recorded
);


-- deployments
-- Each placement of a camera trap at one location for one period of time.
CREATE TABLE deployments (
    -- Primary key
    deployment_id   SERIAL  PRIMARY KEY,

    -- Required fields
    camera_id       TEXT    NOT NULL
                    CHECK (length(trim(camera_id)) > 0),
    start_date      DATE    NOT NULL
                    CHECK (start_date >= '1994-01-01'),     -- rationale: TBS was established in 1994
    lat             DOUBLE PRECISION NOT NULL
                    CHECK (lat BETWEEN -1.0 AND -0.3),      -- rationale: TBS box catches a dropped minus sign
    long            DOUBLE PRECISION NOT NULL
                    CHECK (long BETWEEN -76.6 AND -75.7),   -- rationale: TBS box catches swapped lat/long

    -- Optional fields
    monitor_id      TEXT,                      -- NULL permitted: placement outside the monitoring grid
    end_date        DATE,                      -- NULL permitted: camera still deployed

    -- Cross-field business rule: a camera can't be retrieved before it was set
    CHECK (end_date IS NULL OR end_date >= start_date)
);


-- camera_detections
-- Each video in which a mammal was identified; one video with two species = two rows.
CREATE TABLE camera_detections (
    -- Primary key
    detection_id          SERIAL  PRIMARY KEY,

    -- Required fields
    video_id              TEXT    NOT NULL
                          CHECK (length(trim(video_id)) > 0),
    detection_date        DATE    NOT NULL
                          CHECK (detection_date >= '1994-01-01'),
    number_of_individuals INTEGER NOT NULL DEFAULT 1
                          CHECK (number_of_individuals >= 1),  -- rationale: at least one animal triggered the camera

    needs_review          BOOLEAN NOT NULL DEFAULT FALSE,     -- flagged for a second look

    -- Optional fields
    detection_time        TIME,                -- NULL permitted: camera clock failed
    notes                 TEXT,

    -- Foreign keys
    deployment_id         INTEGER NOT NULL
                          REFERENCES deployments(deployment_id)
                          ON DELETE RESTRICT
                          ON UPDATE CASCADE,
    taxon_id              INTEGER NOT NULL
                          REFERENCES taxa(taxon_id)
                          ON DELETE RESTRICT
                          ON UPDATE CASCADE,
    identified_by         INTEGER              -- NULL permitted: identifier not recorded
                          REFERENCES observers(observer_id)
                          ON DELETE RESTRICT
                          ON UPDATE CASCADE,

    -- Business rule: one species is logged only once per video
    -- (file names can repeat across deployments, so deployment_id is included)
    UNIQUE (deployment_id, video_id, taxon_id)
);


-- occurrences
-- Each direct sighting of a mammal by a researcher.
CREATE TABLE occurrences (
    -- Primary key
    occurrence_id   SERIAL  PRIMARY KEY,

    -- Required fields
    obs_date        DATE    NOT NULL
                    CHECK (obs_date >= '1994-01-01'),

    -- Optional fields
    obs_time        TIME,                      -- NULL permitted: time not noted
    lat             DOUBLE PRECISION                    -- NULL permitted: no GPS fix under canopy
                    CHECK (lat BETWEEN -1.0 AND -0.3),
    long            DOUBLE PRECISION
                    CHECK (long BETWEEN -76.6 AND -75.7),
    notes           TEXT,

    -- Foreign keys
    taxon_id        INTEGER NOT NULL
                    REFERENCES taxa(taxon_id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,
    observer_id     INTEGER NOT NULL
                    REFERENCES observers(observer_id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,

    -- Cross-field business rule: coordinates are complete or missing, never half-entered
    CHECK ((lat IS NULL) = (long IS NULL))
);


-- events
-- Each human activity occasion observed by a researcher.
CREATE TABLE events (
    -- Primary key
    event_id        SERIAL  PRIMARY KEY,

    -- Required fields
    event_date      DATE    NOT NULL
                    CHECK (event_date >= '1994-01-01'),

    -- Controlled vocabulary
    event_type      TEXT    NOT NULL
                    CHECK (event_type IN ('fishing','hunting','pets','sighting','pursuit')),

    -- Optional fields
    lat             DOUBLE PRECISION                    -- NULL permitted: no GPS fix
                    CHECK (lat BETWEEN -1.0 AND -0.3),
    long            DOUBLE PRECISION
                    CHECK (long BETWEEN -76.6 AND -75.7),

    -- Foreign keys
    observer_id     INTEGER NOT NULL
                    REFERENCES observers(observer_id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,

    -- Cross-field business rule: coordinates are complete or missing
    CHECK ((lat IS NULL) = (long IS NULL))
);


-- event_taxa
-- Linking table: which taxa were involved in each event.
CREATE TABLE event_taxa (
    -- Foreign keys (together form the primary key)
    event_id        INTEGER NOT NULL
                    REFERENCES events(event_id)
                    ON DELETE CASCADE          -- link has no meaning without its event
                    ON UPDATE CASCADE,
    taxon_id        INTEGER NOT NULL
                    REFERENCES taxa(taxon_id)
                    ON DELETE RESTRICT
                    ON UPDATE CASCADE,

    -- Controlled vocabulary
    outcome         TEXT                       -- NULL permitted: outcome not recorded
                    CHECK (outcome IN ('seen','pursued','killed')),

    -- Primary key
    PRIMARY KEY (event_id, taxon_id)
);


-- event_persons
-- Linking table: which community members took part in each event.
CREATE TABLE event_persons (
    -- Foreign keys (together form the primary key)
    event_id        INTEGER NOT NULL
                    CHECK (event_id > 0)
                    REFERENCES events(event_id)
                    ON DELETE CASCADE          -- link has no meaning without its event
                    ON UPDATE CASCADE,
    person_id       INTEGER NOT NULL
                    CHECK (person_id > 0)
                    REFERENCES person(person_id)
                    ON DELETE RESTRICT         -- TODO: RESTRICT vs CASCADE still undecided (see week08/fk_integrity.md)
                    ON UPDATE CASCADE,

    -- Primary key
    PRIMARY KEY (event_id, person_id)
);
