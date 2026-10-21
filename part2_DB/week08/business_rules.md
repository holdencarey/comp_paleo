# Tiputini Mammalian Database — Business Rules

# Holden

## 4a — Rule inventory

| # | Rule | Enforceable in SQL? | Constraint type | SQL expression or note |
|---|---|---|---|---|
| 1 | Every taxon must have a scientific name | Yes | NOT NULL | `scientific_name TEXT NOT NULL` |
| 2 | A scientific name can only be entered once | Yes | UNIQUE | `UNIQUE (scientific_name)` |
| 3 | Taxonomic rank must come from the approved list | Yes | CHECK (enum) | `CHECK (taxonomic_rank IN ('species','genus','family','order'))` |
| 4 | Event type must come from the approved list | Yes | CHECK (enum) | `CHECK (event_type IN ('fishing','hunting','pets','sighting','pursuit'))` |
| 5 | The outcome for an animal in an event must come from the approved list | Yes | CHECK (enum) | `CHECK (outcome IN ('seen','pursued','killed'))` |
| 6 | All coordinates must fall within the TBS study area | Yes | CHECK (range) | `CHECK (lat BETWEEN -1.0 AND -0.3 AND long BETWEEN -76.6 AND -75.7)` |
| 7 | A camera detection must show at least one animal | Yes | CHECK (range) + DEFAULT | `number_of_individuals INTEGER NOT NULL DEFAULT 1 CHECK (number_of_individuals >= 1)` |
| 8 | No record can be dated before TBS was established (1994) | Yes | CHECK (range) | `CHECK (start_date >= '1994-01-01')` (same rule on every date field) |
| 9 | A camera cannot be retrieved before it was set | Yes | CHECK (cross-field) | `CHECK (end_date IS NULL OR end_date >= start_date)` |
| 10 | A location must have both lat and long, or neither | Yes | CHECK (cross-field) | `CHECK ((lat IS NULL) = (long IS NULL))` |
| 11 | A deployment must exist before its videos can be logged | Yes | FOREIGN KEY | `deployment_id INTEGER NOT NULL REFERENCES deployments(deployment_id)` |
| 12 | The same species can only be logged once per video | Yes | UNIQUE (composite) | `UNIQUE (deployment_id, video_id, taxon_id)` |
| 13 | A species or person can only be linked to the same event once | Yes | PRIMARY KEY (composite) | `PRIMARY KEY (event_id, taxon_id)` and `PRIMARY KEY (event_id, person_id)` |
| 14 | No record can have a future date | No | Application | SQLite does not allow `'now'` inside a CHECK constraint, so this has to be checked when data is entered |
| 15 | A camera detection must fall within its deployment's start and end dates | No | Trigger / Application | The dates are in two different tables, and a CHECK can only see one row of one table |
| 16 | Community members can only be recorded with IRB-approved consent | No | Workflow | SQL can't verify that consent was actually given; this is handled by the IRB protocol before any data is entered |
| 17 | Camera trap species IDs should be verified by a second person (recommended) | No | Workflow | Would need a `verified_by` field plus a lab protocol; the database can't judge whether an ID is correct |

## 4b — Cross-field constraints

```sql
-- a camera cannot be retrieved before it was set (deployments)
CHECK (end_date IS NULL OR end_date >= start_date)

-- a location must be complete or missing, never half-entered (occurrences, events)
CHECK ((lat IS NULL) = (long IS NULL))
```

The first rule catches a retrieval date typed in the wrong order or the wrong year. Checking each date alone would accept both dates, because each one is a valid date on its own. The second rule catches a GPS reading where only one coordinate was entered, which can't be mapped. Each field passes its own range check, so only a rule that looks at both fields together can catch it.
