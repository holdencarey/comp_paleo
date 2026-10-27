-- constraint_tests.sql
-- Tiputini Mammalian Database
-- Holden Carey



PRAGMA foreign_keys = ON;


-- Setup: parent rows the tests below depend on
INSERT INTO observers (observer_id, name, affiliation)
VALUES (1, 'Holden Carey', 'Primate Molecular Ecology and Evolution Lab');

INSERT INTO person (person_id, name, sex, age)
VALUES (1, 'Participant 01', 'male', 34);


-- NOT NULL on taxa.scientific_name

-- SHOULD SUCCEED
INSERT INTO taxa (taxon_id, scientific_name, common_name)
VALUES (1, 'Tayassu pecari', 'White-lipped peccary');

-- SHOULD FAIL: scientific_name is NOT NULL
-- Expected error: NOT NULL constraint failed: taxa.scientific_name
INSERT INTO taxa (taxon_id, scientific_name, common_name)
VALUES (2, NULL, 'Mystery mammal');


-- UNIQUE on taxa.scientific_name

-- SHOULD SUCCEED
INSERT INTO taxa (taxon_id, scientific_name, common_name)
VALUES (3, 'Lagothrix lagotricha', 'Woolly monkey');

-- SHOULD FAIL: 'Tayassu pecari' is already in the taxa table
-- Expected error: UNIQUE constraint failed: taxa.scientific_name
INSERT INTO taxa (taxon_id, scientific_name, common_name)
VALUES (4, 'Tayassu pecari', 'White-lipped Peccary (duplicate)');


-- CHECK (enum) on events.event_type

-- SHOULD SUCCEED
INSERT INTO events (event_id, observer_id, event_type, event_date)
VALUES (1, 1, 'hunting', '2025-06-14');

-- SHOULD FAIL: 'trapping' is not in the controlled vocabulary
-- Expected error: CHECK constraint failed: event_type IN (...)
INSERT INTO events (event_id, observer_id, event_type, event_date)
VALUES (2, 1, 'trapping', '2025-06-15');


-- CHECK (range) on deployments.lat (TBS study area box)

-- SHOULD SUCCEED
INSERT INTO deployments (deployment_id, camera_id, lat, long, start_date)
VALUES (1, 'CAM07', -0.638, -76.150, '2025-01-10');

-- SHOULD FAIL: dropped minus sign puts the camera north of the equator
-- Expected error: CHECK constraint failed: lat BETWEEN -1.0 AND -0.3
INSERT INTO deployments (deployment_id, camera_id, lat, long, start_date)
VALUES (2, 'CAM08', 0.638, -76.150, '2025-01-10');


-- CHECK (range) on camera_detections.number_of_individuals, plus DEFAULT

-- SHOULD SUCCEED: number_of_individuals left out, so DEFAULT 1 is used
INSERT INTO camera_detections (detection_id, deployment_id, taxon_id, video_id, detection_date)
VALUES (1, 1, 1, 'CAM07_0342.MP4', '2025-01-15');

-- Verify the DEFAULT: should show 1
SELECT detection_id, video_id, number_of_individuals FROM camera_detections;

-- SHOULD FAIL: a detection can't show zero animals
-- Expected error: CHECK constraint failed: number_of_individuals >= 1
INSERT INTO camera_detections (detection_id, deployment_id, taxon_id, video_id, detection_date, number_of_individuals)
VALUES (2, 1, 1, 'CAM07_0343.MP4', '2025-01-15', 0);


-- CHECK (cross-field) on deployments: end_date >= start_date

-- SHOULD SUCCEED
INSERT INTO deployments (deployment_id, camera_id, lat, long, start_date, end_date)
VALUES (3, 'CAM09', -0.640, -76.140, '2025-02-01', '2025-04-01');

-- SHOULD FAIL: the camera was "retrieved" before it was set
-- Expected error: CHECK constraint failed: end_date IS NULL OR end_date >= start_date
INSERT INTO deployments (deployment_id, camera_id, lat, long, start_date, end_date)
VALUES (4, 'CAM10', -0.640, -76.140, '2025-04-01', '2025-02-01');


-- CHECK (cross-field) on occurrences: lat and long both present or both NULL

-- SHOULD SUCCEED: no GPS fix, so both coordinates are NULL
INSERT INTO occurrences (occurrence_id, taxon_id, observer_id, obs_date, lat, long)
VALUES (1, 3, 1, '2025-03-02', NULL, NULL);

-- SHOULD FAIL: only one coordinate was entered
-- Expected error: CHECK constraint failed: (lat IS NULL) = (long IS NULL)
INSERT INTO occurrences (occurrence_id, taxon_id, observer_id, obs_date, lat, long)
VALUES (2, 3, 1, '2025-03-02', -0.638, NULL);


-- UNIQUE (composite) on camera_detections: one species once per video

-- SHOULD SUCCEED: same video, different species
INSERT INTO camera_detections (detection_id, deployment_id, taxon_id, video_id, detection_date)
VALUES (3, 1, 3, 'CAM07_0342.MP4', '2025-01-15');

-- SHOULD FAIL: same species logged twice for the same video
-- Expected error: UNIQUE constraint failed: camera_detections.deployment_id, camera_detections.video_id, camera_detections.taxon_id
INSERT INTO camera_detections (detection_id, deployment_id, taxon_id, video_id, detection_date)
VALUES (4, 1, 1, 'CAM07_0342.MP4', '2025-01-15');


-- FOREIGN KEY on insert: a deployment must exist before its videos

-- SHOULD FAIL: deployment 99 does not exist
-- Expected error: FOREIGN KEY constraint failed
INSERT INTO camera_detections (detection_id, deployment_id, taxon_id, video_id, detection_date)
VALUES (5, 99, 1, 'CAM99_0001.MP4', '2025-01-15');


-- FK RESTRICT on camera_detections.deployment_id

-- SHOULD SUCCEED: deployment 3 has no detections
DELETE FROM deployments WHERE deployment_id = 3;

-- SHOULD FAIL: deployment 1 still has detections
-- Expected error: FOREIGN KEY constraint failed
DELETE FROM deployments WHERE deployment_id = 1;


-- FK CASCADE on event_taxa.event_id and event_persons.event_id

INSERT INTO event_taxa (event_id, taxon_id, outcome) VALUES (1, 1, 'killed');

-- Before: event 1 has one taxon link and one person link
SELECT COUNT(*) FROM event_taxa WHERE event_id = 1;
SELECT COUNT(*) FROM event_persons WHERE event_id = 1;

-- SHOULD SUCCEED: deleting the event also deletes its links
DELETE FROM events WHERE event_id = 1;

-- After: both counts should be 0
SELECT COUNT(*) FROM event_taxa WHERE event_id = 1;
SELECT COUNT(*) FROM event_persons WHERE event_id = 1;


