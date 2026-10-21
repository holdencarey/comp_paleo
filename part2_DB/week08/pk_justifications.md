# Primary Key Justifications
---
## Holden
---
### Table: taxa
Key field(s): taxon_id Key type: Surrogate (INTEGER, auto-increment)

Justification: I chose a surrogate key because scientific names change with taxonomic revision. If scientific_name were the key, every rename would have to be updated in camera_detections, occurrences, and event_taxa. With taxon_id, a rename only changes one field in one row, and all the links stay the same. scientific_name is still stored as a UNIQUE field so it can be searched and duplicates are blocked.

### Table: person
Key field(s): person_id Key type: Surrogate (INTEGER, auto-increment)

Justification: Community members don't have a unique identifier, and names can repeat or be spelled differently across field notes. Using a number also protects privacy, since the data is shared with other institutions and names shouldn't be copied into every event record. This way the name field can hold a pseudonym, and it can be changed without breaking any links.

### Table: observers
Table: observers

Key field(s): observer_id Key type: Surrogate (INTEGER, auto-increment)

Justification: Researchers come from many institutions and don't share a common ID. Names aren't guaranteed to be unique and can change (for example, after marriage). A surrogate key means all of an observer's sightings and events stay linked to them even if their name is updated.

### Table: deployments
Key field(s): deployment_id Key type: Surrogate (INTEGER, auto-increment)

Justification: camera_id can't be the key because the same camera gets moved and redeployed many times. camera_id plus start_date would be unique, but a two-part key would have to be copied into every detection, and fixing a mistyped date would mean changing all of those rows. A surrogate key avoids this, and camera_id is still stored so footage can be traced back to the camera.

### Table: camera_detections
Key field(s): detection_id Key type: Surrogate (INTEGER, auto-increment)

Justification: video_id isn't unique on its own, because file names restart when a memory card is formatted, and one video with two species gets two rows. The combination of deployment_id, video_id, and taxon_id is unique, so I enforce it with a UNIQUE constraint instead of making it a three-part key. detection_id gives each record a simple ID for fixing errors.

### Table: occurrences
Key field(s): occurrence_id Key type: Surrogate (INTEGER, auto-increment)

Justification: A sighting has no natural ID. Observer, taxon, date, and time together come close, but time is optional, and one observer could see two groups of the same species at the same time. A surrogate key is the only way to guarantee every sighting has its own unique ID.

### Table: evenets
Key field(s): event_id Key type: Surrogate (INTEGER, auto-increment)

Justification: Events don't have a natural ID, and a researcher could record two hunts of the same type on the same day, so observer, type, and date together aren't unique. event_id is also used in both junction tables, so keeping it a single integer keeps those tables simple.

### Table: event_taxa
Key field(s): event_id, taxon_id Key type: Composite

Justification: This linking table connects events to the species involved in them. Each pair of event and taxon only appears once, so the two foreign keys together make a unique key. This also stops the same species from being linked to the same event twice. Both values are surrogate keys from their parent tables, so they won't change.

### Table: event_persons
Key field(s): event_id, person_id Key type: Composite

Justification: This linking table connects events to the community members who took part. A person can only be part of a given event once, so event_id and person_id together are unique. A separate ID column would add nothing and would allow duplicate links. 
