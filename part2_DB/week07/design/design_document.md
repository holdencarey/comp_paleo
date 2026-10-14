# Tiputini Mammalian Database - Preliminary Design Project

**Author:** Holden Carey

**Date:** October 12 2026

**Domain:** Ecology, Primatology, Anthropology

**Research context:** The Tiputini Mammalian Database aims to describe the mammalian and indigenous communities in order to understand the ecosystem at large.

---

The purpose of the Tiputini Mammalian Database is to record information on mammalian occurrence data, including humans, from the Tiputini Biodiversity Station (TBS) in Ecuador, supporting analysis of mammalian biodiversity and human-wildlife overlap. The database serves the Primate Molecular Ecology and Evolution lab and collaborators across many institutions and organizations. 
1: List all mammal taxa recorded at TBS SELECT scientific_name, common_name, taxonomic_rank FROM taxa ORDER BY scientific_name;

2: Find all direct sightings of a given taxon within a date range SELECT oc.obs_date, oc.lat, oc.long FROM occurrences oc JOIN taxa t ON oc.taxon_id = t.taxon_id WHERE t.scientific_name = ? AND oc.obs_date BETWEEN ? AND ?;

3: Produce a species list for each camera trap deployment SELECT d.camera_id, t.scientific_name, COUNT(*) AS n_detections FROM camera_detections cd JOIN deployments d ON cd.deployment_id = d.deployment_id JOIN taxa t ON cd.taxon_id = t.taxon_id GROUP BY d.camera_id, t.scientific_name;

4: Count human activity events by type SELECT event_type, COUNT(*) AS n_events FROM events GROUP BY event_type ORDER BY n_events DESC;

---

## Entities

| Entity | Justification | Example attributes |
|--------|--------------|-------------------|
| taxa | A species exists independently of any sighting, detection, or event; the same taxon is recorded many times across all three record types, so storing it once avoids repeating names and lets a taxonomic revision be updated in one place | scientific_name, taxonomic_rank |
| person | Community members exist independently of any single event and take part in many events over time, so their details are stored once rather than repeated on every event | sex, age |
| observers | Researchers exist independently of the records they collect and record many sightings and events; they are a different subject from community members, with different attributes | name, affiliation |
| deployments | A camera trap placement exists before and independently of any detection, and one deployment produces many detections; storing its location once means every detection can be mapped without repeating coordinates | camera_id, start_date |
| camera_detections | Each video record is a distinct observation with its own date, time, and count; it is a different kind of record from a direct sighting, with attributes that only apply to camera data | video_id, detection_time |
| occurrences | Sightings from both camera detections and events | obs_date, obs_time |
| events | A human activity (e.g. hunting, fishing, pets, sighting, pursuit) exists as one occasion regardless of how many people or species were involved, so it needs its own row rather than being repeated per species or per person | event_type, event_date |


## Field Specifications

### Table: taxa
Each mammal taxon recorded at TBS.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| taxon_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment. Used instead of the scientific name because names change with taxonomic revision |
| scientific_name | TEXT | YES | — | Binomial or higher-rank name, e.g. *Tayassu pecari*; unique |
| taxonomic_rank | TEXT | NO | — | Controlled vocabulary: species, genus, family, order. Allows records identified only to genus or family |
| common_name | TEXT | NO | — | English or local common name; NULL if none is in use |

### Table: person
Community members who take part in human activity events.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| person_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment. Also lets participants be anonymised |
| name | TEXT | YES | — | Name or pseudonym used in field notes |
| sex | TEXT | NO | — | Controlled vocabulary: male, female; NULL if not recorded |
| age | INTEGER | NO | — | Age in years at first record; NULL if unknown |

### Table: observers
Researchers who record sightings and events.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| observer_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment |
| name | TEXT | YES | — | Full name of the researcher |
| affiliation | TEXT | NO | — | Lab or institution, e.g. Primate Molecular Ecology and Evolution lab |

### Table: deployments
Each placement of a camera trap at a location for a period of time.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| deployment_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment. A camera moved to a new spot gets a new deployment |
| camera_id | TEXT | YES | — | Label on the physical camera unit; TEXT because labels may contain letters |
| monitor_id | TEXT | NO | — | Monitoring station or grid point the camera is assigned to |
| lat | REAL | YES | — | Latitude in decimal degrees (WGS84); negative south of the equator |
| long | REAL | YES | — | Longitude in decimal degrees (WGS84); negative west of Greenwich |
| start_date | TEXT | YES | — | Date the camera was set, YYYY-MM-DD |
| end_date | TEXT | NO | — | Date the camera was retrieved, YYYY-MM-DD; NULL means still deployed |

### Table: camera_detections
Each video in which a mammal was identified.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| detection_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment |
| deployment_id | INTEGER | YES (FK) | — | References deployments.deployment_id; gives the detection its location |
| taxon_id | INTEGER | YES (FK) | — | References taxa.taxon_id |
| video_id | TEXT | YES | — | File name of the video, e.g. CAM07_0342.MP4; TEXT because it contains letters |
| detection_date | TEXT | YES | — | Date the video was recorded, YYYY-MM-DD |
| detection_time | TEXT | NO | — | Time the video was recorded, HH:MM:SS (24-hour) |
| number_of_individuals | INTEGER | NO | 1 | Count of individuals visible; default 1 as at least one animal triggered the camera |

### Table: occurrences
Sighting of mammal.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| occurrence_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment |
| taxon_id | INTEGER | YES (FK) | — | References taxa.taxon_id |
| observer_id | INTEGER | YES (FK) | — | References observers.observer_id |
| obs_date | TEXT | YES | — | Date of sighting, YYYY-MM-DD |
| obs_time | TEXT | NO | — | Time of sighting, HH:MM (24-hour) |
| lat | REAL | NO | — | Latitude in decimal degrees (WGS84); NULL if no GPS fix |
| long | REAL | NO | — | Longitude in decimal degrees (WGS84); NULL if no GPS fix |
| notes | TEXT | NO | — | Free text; observer remarks |

### Table: events
Each human activity occasion observed by a researcher.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| event_id | INTEGER | YES (PK) | — | Surrogate key; auto-increment |
| observer_id | INTEGER | YES (FK) | — | References observers.observer_id; the researcher who recorded the event |
| event_type | TEXT | YES | — | Controlled vocabulary: fishing, hunting, pets, sighting, pursuit |
| event_date | TEXT | YES | — | Date of the event, YYYY-MM-DD |
| lat | REAL | NO | — | Latitude in decimal degrees (WGS84); NULL if no GPS fix |
| long | REAL | NO | — | Longitude in decimal degrees (WGS84); NULL if no GPS fix |

### Table: event_taxa
Junction table linking each event to the species involved in it.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| event_id | INTEGER | YES (FK) | — | References events.event_id; part of composite primary key |
| taxon_id | INTEGER | YES (FK) | — | References taxa.taxon_id; part of composite primary key |
| outcome | TEXT | NO | — | Controlled vocabulary: seen, pursued, killed; NULL if not recorded |

### Table: event_persons
Junction table linking each event to the community members who took part.

| Field name | Data type | Required | Default | Notes |
|------------|-----------|----------|---------|-------|
| event_id | INTEGER | YES (FK) | — | References events.event_id; part of composite primary key |
| person_id | INTEGER | YES (FK) | — | References person.person_id; part of composite primary key |


---

## Relationships

| Relationship | Cardinality | Implementation |
|-------------|-------------|---------------|
| One deployment → many camera detections | 1:∞ | camera_detections.deployment_id → deployments.deployment_id |
| One taxon → many camera detections | 1:∞ | camera_detections.taxon_id → taxa.taxon_id |
| One taxon → many occurrences | 1:∞ | occurrences.taxon_id → taxa.taxon_id |
| One observer → many occurrences | 1:∞ | occurrences.observer_id → observers.observer_id |
| One observer → many events | 1:∞ | events.observer_id → observers.observer_id |
| Many events ↔ many taxa | ∞:∞ | Table event_taxa: event_taxa.event_id → events.event_id; event_taxa.taxon_id → taxa.taxon_id |
| Many events ↔ many persons | ∞:∞ | Table event_persons: event_persons.event_id → events.event_id; event_persons.person_id → person.person_id |

---

## Key Choices

Every entity table uses a surrogate INTEGER primary key rather than a natural key. Natural candidates exist but are unstable or not unique. Scientific names change with taxonomic revision. A camera_id is reused each time a camera is moved, so it can't identify a deployment. Video file names may repeat across memory cards. Researchers and community members have no reliable unique identifier, and a surrogate key also lets participants be recorded under a pseudonym. Natural identifiers such as scientific_name, camera_id, and video_id are still stored as regular attributes, so they can be searched and traced back to field records.

The design has two many-to-many relationships. A single event (for example, a hunt) can involve several species, and a species can be involved in many events; this is resolved by event_taxa (event_id, taxon_id, outcome). A single event can include several community members, and a person can take part in many events; this is resolved by event_persons (event_id, person_id). Both junction tables use a composite primary key of their two foreign keys, so the same species or person cannot be linked to the same event twice.
