-- schema_draft.sql
-- Tiputini Mammalian Database — Preliminary Schema
-- Week 7 Design Assignment

-- schema_draft.sql
-- Tiputini Mammalian Database
-- Week 7 Assignment, [Your name]

DROP TABLE IF EXISTS event_persons;
DROP TABLE IF EXISTS event_taxa;
DROP TABLE IF EXISTS events;
DROP TABLE IF EXISTS occurrences;
DROP TABLE IF EXISTS camera_detections;
DROP TABLE IF EXISTS deployments;
DROP TABLE IF EXISTS observers;
DROP TABLE IF EXISTS person;
DROP TABLE IF EXISTS taxa;

-- Mammal taxa recorded at TBS, including humans
CREATE TABLE taxa (
    taxon_id        INTEGER PRIMARY KEY,
    scientific_name TEXT NOT NULL,
    taxonomic_rank  TEXT,
    common_name     TEXT
);

-- Community members who take part in events
CREATE TABLE person (
    person_id       INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    sex             TEXT,
    age             INTEGER
);

-- Researchers who record sightings and events
CREATE TABLE observers (
    observer_id     INTEGER PRIMARY KEY,
    name            TEXT NOT NULL,
    affiliation     TEXT
);

-- Camera trap placements
CREATE TABLE deployments (
    deployment_id   INTEGER PRIMARY KEY,
    camera_id       TEXT NOT NULL,
    monitor_id      TEXT,
    lat             REAL NOT NULL,
    long            REAL NOT NULL,
    start_date      TEXT NOT NULL,
    end_date        TEXT
);

-- Camera trap videos with an identified mammal
CREATE TABLE camera_detections (
    detection_id          INTEGER PRIMARY KEY,
    deployment_id         INTEGER NOT NULL REFERENCES deployments(deployment_id),
    taxon_id              INTEGER NOT NULL REFERENCES taxa(taxon_id),
    video_id              TEXT NOT NULL,
    detection_date        TEXT NOT NULL,
    detection_time        TEXT,
    number_of_individuals INTEGER
);

-- Human activity events observed by researchers
CREATE TABLE events (
    event_id        INTEGER PRIMARY KEY,
    observer_id     INTEGER NOT NULL REFERENCES observers(observer_id),
    event_type      TEXT NOT NULL,
    event_date      TEXT NOT NULL,
    lat             REAL,
    long            REAL
);

-- Species involved in each event
CREATE TABLE event_taxa (
    event_id        INTEGER NOT NULL REFERENCES events(event_id),
    taxon_id        INTEGER NOT NULL REFERENCES taxa(taxon_id),
    outcome         TEXT,
    PRIMARY KEY (event_id, taxon_id)
);

-- Community members who took part in each event
CREATE TABLE event_persons (
    event_id        INTEGER NOT NULL REFERENCES events(event_id),
    person_id       INTEGER NOT NULL REFERENCES person(person_id),
    PRIMARY KEY (event_id, person_id)
);

