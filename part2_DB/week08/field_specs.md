# Field Specifications

**Author:** Holden

---

## Table: taxa
Each mammal taxon recorded at TBS, including *Homo sapiens*.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| taxon_id | INTEGER | PK | YES | YES | — | — | Surrogate key; scientific names change with taxonomic revision, so they cannot serve as a stable identifier |
| scientific_name | TEXT | — | YES | YES | — | `length(trim(scientific_name)) > 0 AND scientific_name = trim(scientific_name)` | Every taxon needs a name, and duplicates would split records; the trim check stops `'Tayassu pecari '` from slipping past UNIQUE as a "different" name |
| taxonomic_rank | TEXT | — | YES | NO | `'species'` | `taxonomic_rank IN ('species','genus','family','order')` | Rank is always known when a name is entered, and most records are species-level; controlled vocabulary allows coarser IDs (e.g. *Mazama* sp.) without free-text variation |
| common_name | TEXT | — | NO | NO | — | — | NULL permitted because many Amazonian taxa have no established English or local common name |

## Table: person
Community members who take part in human activity events.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| person_id | INTEGER | PK | YES | YES | — | — | Surrogate key; no reliable natural identifier exists, and it allows participants to be recorded under a pseudonym |
| name | TEXT | — | YES | NO | — | `length(trim(name)) > 0` | A name or pseudonym is needed to match field notes to a person; not UNIQUE because two community members may share a name |
| sex | TEXT | — | NO | NO | — | `sex IN ('male','female')` | Controlled vocabulary prevents variants like `M`, `Male`, `m`; NULL when not recorded in field notes |
| age | INTEGER | — | NO | NO | — | `age BETWEEN 0 AND 120` | Age in years at first record; NULL when unknown; range check rules out data-entry errors such as negative ages |

## Table: observers
Researchers who record sightings and events.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| observer_id | INTEGER | PK | YES | YES | — | — | Surrogate key; researchers have no shared unique identifier across institutions |
| name | TEXT | — | YES | NO | — | `length(trim(name)) > 0` | Every record must be attributable to a named researcher; blank strings are rejected as well as NULL |
| affiliation | TEXT | — | NO | NO | — | — | NULL permitted for independent researchers or when affiliation was not recorded |

## Table: deployments
Each placement of a camera trap at one location for one period of time.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| deployment_id | INTEGER | PK | YES | YES | — | — | Surrogate key; camera_id is reused each time a camera is moved, so it cannot identify a deployment |
| camera_id | TEXT | — | YES | NO | — | `length(trim(camera_id)) > 0` | Physical unit label is needed to trace footage back to hardware; TEXT because labels contain letters; not UNIQUE because one camera has many deployments |
| monitor_id | TEXT | — | NO | NO | — | — | Grid point or station; NULL permitted for opportunistic placements outside the monitoring grid |
| lat | REAL | — | YES | NO | — | `lat BETWEEN -90 AND 90` | A deployment without a location cannot be mapped, so it is required; decimal degrees WGS84 |
| long | REAL | — | YES | NO | — | `long BETWEEN -180 AND 180` | Required for the same reason as lat; decimal degrees WGS84 |
| start_date | TEXT | — | YES | NO | — | `date(start_date) IS start_date AND start_date >= '1994-01-01'` | Required because every deployment has a set date; enforces YYYY-MM-DD and rules out dates before the station existed |
| end_date | TEXT | — | NO | NO | — | `date(end_date) IS end_date AND (end_date IS NULL OR end_date >= start_date)` | NULL means the camera is still deployed; cross-field check stops a retrieval date earlier than the set date |

## Table: camera_detections
Each video in which a mammal was identified. One video showing two species produces two rows.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| detection_id | INTEGER | PK | YES | YES | — | — | Surrogate key; video file names can repeat across memory cards |
| deployment_id | INTEGER | FK → deployments.deployment_id | YES | NO* | — | — | Every detection comes from a deployment, which supplies its location |
| taxon_id | INTEGER | FK → taxa.taxon_id | YES | NO* | — | — | Only videos with an identified mammal are entered, so a taxon is always present |
| video_id | TEXT | — | YES | NO* | — | `length(trim(video_id)) > 0` | File name links the record back to the footage; TEXT because it contains letters |
| detection_date | TEXT | — | YES | NO | — | `date(detection_date) IS detection_date AND detection_date >= '1994-01-01'` | Camera always stamps a date; enforces YYYY-MM-DD |
| detection_time | TEXT | — | NO | NO | — | `time(detection_time) IS detection_time` | HH:MM:SS 24-hour; NULL permitted if the camera clock failed |
| number_of_individuals | INTEGER | — | YES | NO | `1` | `number_of_individuals >= 1` | At least one animal triggered the camera, so 1 is a safe default and zero or negative counts are impossible |

\* **Composite UNIQUE (deployment_id, video_id, taxon_id):** the same video can contain several species, and the same file name can recur on different deployments, but one species should be logged only once per video.

## Table: occurrences
Each direct sighting of a mammal by a researcher.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| occurrence_id | INTEGER | PK | YES | YES | — | — | Surrogate key; no natural identifier exists for a sighting |
| taxon_id | INTEGER | FK → taxa.taxon_id | YES | NO | — | — | A sighting is only recorded once the animal is identified, at least to family |
| observer_id | INTEGER | FK → observers.observer_id | YES | NO | — | — | Every sighting must be attributable to a researcher for data quality review |
| obs_date | TEXT | — | YES | NO | — | `date(obs_date) IS obs_date AND obs_date >= '1994-01-01'` | Date is always known for a sighting; enforces YYYY-MM-DD |
| obs_time | TEXT | — | NO | NO | — | `strftime('%H:%M', obs_time) IS obs_time` | HH:MM 24-hour; NULL permitted when time was not noted |
| lat | REAL | — | NO | NO | — | `lat BETWEEN -90 AND 90` | NULL permitted when there was no GPS fix under canopy |
| long | REAL | — | NO | NO | — | `long BETWEEN -180 AND 180` | NULL permitted for the same reason as lat |
| notes | TEXT | — | NO | NO | — | — | Free-text observer remarks; optional |

**Cross-field (table level):** `(lat IS NULL) = (long IS NULL)`. A coordinate is either complete or absent; half a coordinate cannot be mapped.

## Table: events
Each human activity occasion observed by a researcher.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| event_id | INTEGER | PK | YES | YES | — | — | Surrogate key; an event has no natural identifier |
| observer_id | INTEGER | FK → observers.observer_id | YES | NO | — | — | Every event must be attributable to the researcher who recorded it |
| event_type | TEXT | — | YES | NO | — | `event_type IN ('fishing','hunting','pets','sighting','pursuit')` | Query 4 groups by this field, so inconsistent spellings would split the counts |
| event_date | TEXT | — | YES | NO | — | `date(event_date) IS event_date AND event_date >= '1994-01-01'` | Date is always recorded; enforces YYYY-MM-DD |
| lat | REAL | — | NO | NO | — | `lat BETWEEN -90 AND 90` | NULL permitted when there was no GPS fix |
| long | REAL | — | NO | NO | — | `long BETWEEN -180 AND 180` | NULL permitted when there was no GPS fix |

**Cross-field (table level):** `(lat IS NULL) = (long IS NULL)`.

## Table: event_taxa
Junction table linking each event to the taxa involved.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| event_id | INTEGER | PK (composite), FK → events.event_id | YES | NO* | — | — | Part of the composite key; a link must point to a real event |
| taxon_id | INTEGER | PK (composite), FK → taxa.taxon_id | YES | NO* | — | — | Part of the composite key; a link must point to a real taxon |
| outcome | TEXT | — | NO | NO | — | `outcome IN ('seen','pursued','killed')` | Controlled vocabulary for what happened to the animal; NULL when the outcome was not recorded |

\* The pair (event_id, taxon_id) is unique via the composite primary key, so the same taxon cannot be linked to the same event twice.

## Table: event_persons
Junction table linking each event to the community members who took part.

| Field name | Data type | PK/FK | NOT NULL | UNIQUE | DEFAULT | CHECK | Rationale |
|---|---|---|---|---|---|---|---|
| event_id | INTEGER | PK (composite), FK → events.event_id | YES | NO* | — | `typeof(event_id) = 'integer'` | Part of the composite key; SQLite's loose typing would otherwise accept text in an INTEGER column |
| person_id | INTEGER | PK (composite), FK → person.person_id | YES | NO* | — | `typeof(person_id) = 'integer'` | Part of the composite key; same type-safety reason as event_id |

\* The pair (event_id, person_id) is unique via the composite primary key, so the same person cannot be linked to the same event twice.
