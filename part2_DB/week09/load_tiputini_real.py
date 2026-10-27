#!/usr/bin/env python3
"""
load_tiputini.py — Load Tiputini Mammalian Database records

Usage (from the week09 folder, with the venv active):
    psql -d tiputini -f schema.sql
    python load_tiputini.py

Reads two files and fills all nine tables:
    RecordOfSightings.csv    real camera trap records -> taxa, observers,
                             deployments, camera_detections
    monitor_locations.csv    lat/long of each monitoring station, matched to
                             deployments by MonitorID

There is no real data yet for occurrences, events, person, event_taxa or
event_persons, so each gets one row clearly labelled PLACEHOLDER.

Cleaning applied to the camera trap records:
    * Only mammals are loaded; birds and reptiles are skipped and counted.
    * Misspelled or mis-capitalised scientific names are corrected.
    * Records with no scientific name are mapped to a higher taxon when the
      common name allows it (e.g. "Deer" -> genus Mazama); empty or
      unidentifiable videos are skipped and counted.
    * Dates are converted from M/D/YYYY to YYYY-MM-DD.
    * Counts that are not a number become NULL, so the default of 1 is used.

Parents are always inserted before children, so every foreign key points to
a row that already exists. Each row is committed on its own; if a row breaks
a constraint, conn.rollback() undoes only that row and the loader moves on.

Re-running: camera detections are skipped if already present
(ON CONFLICT DO NOTHING), but the placeholder rows have no natural key, so
running the loader twice duplicates them. Always run schema.sql first to
start from empty tables.

Requires config.py in the same folder with: DSN = "postgresql://..."
"""

import csv
import re
import sys
from collections import Counter

import psycopg2
import psycopg2.extras

from config import DSN

CAMERA_FILE = "RecordOfSightings.csv"
LOCATION_FILE = "monitor_locations.csv"


# ── Taxonomy reference tables ─────────────────────────────────────────────────

# Every mammal recorded at TBS in the camera data: name -> (common name, rank).
# Anything not in this list is treated as a non-mammal and skipped.
MAMMALS = {
    "Ateles belzebuth":          ("White-bellied spider monkey", "species"),
    "Cebus yuracus":             ("Humboldt's white-fronted capuchin", "species"),
    "Cuniculus paca":            ("Lowland paca", "species"),
    "Dasyprocta fuliginosa":     ("Black agouti", "species"),
    "Dasypus novemcinctus":      ("Nine-banded armadillo", "species"),
    "Dicotyles tajacu":          ("Collared peccary", "species"),
    "Didelphis marsupialis":     ("Common opossum", "species"),
    "Eira barbara":              ("Tayra", "species"),
    "Hadrosciurus igniventris":  ("Northern Amazon red squirrel", "species"),
    "Hydrochoerus hydrochaeris": ("Capybara", "species"),
    "Leopardus pardalis":        ("Ocelot", "species"),
    "Mazama americana":          ("Red brocket", "species"),
    "Mazama nemorivaga":         ("Amazonian brown brocket", "species"),
    "Mazama zamora":             ("Zamora red brocket", "species"),
    "Myoprocta pratti":          ("Green acouchi", "species"),
    "Nasua nasua":               ("South American coati", "species"),
    "Panthera onca":             ("Jaguar", "species"),
    "Philander andersoni":       ("Anderson's four-eyed opossum", "species"),
    "Priodontes maximus":        ("Giant armadillo", "species"),
    "Puma concolor":             ("Puma", "species"),
    "Speothos venaticus":        ("Bush dog", "species"),
    "Tamandua tetradactyla":     ("Southern tamandua", "species"),
    "Tapirus terrestris":        ("Lowland tapir", "species"),
    # Higher taxa, used for records not identified to species
    "Mazama":                    ("Brocket deer", "genus"),
    "Rodentia":                  ("Rodents", "order"),
    "Didelphimorphia":           ("Opossums", "order"),
    "Mammalia":                  ("Mammals", "class"),
}

# Spelling mistakes found in the field data -> correct name
CORRECTIONS = {
    "Mazama american":       "Mazama americana",
    "Mazama spp.":           "Mazama",
    "Lepardus paradalis":    "Leopardus pardalis",
    "Myopracta pratti":      "Myoprocta pratti",
    "Temandua tetradactyla": "Tamandua tetradactyla",
}

# Records with no scientific name: common name -> higher taxon.
# Common names not listed here (Unknown, None, Bird, Lizard...) are skipped.
UNIDENTIFIED = {
    "mouse":         "Rodentia",
    "deer":          "Mazama",
    "foal":          "Mazama",     # notes say "Red or Brown Brocket"
    "possum":        "Didelphimorphia",
    "large possum":  "Didelphimorphia",
    "mouse/possum":  "Mammalia",   # could be a rodent or an opossum
    "mouse/opussum": "Mammalia",
    "possom/mouse":  "Mammalia",
    "possum/mouse":  "Mammalia",
    "rodent/possum": "Mammalia",
    "mammal":        "Mammalia",
    "small mammal":  "Mammalia",
}

# Records with no scientific name whose common name shows they aren't mammals
NON_MAMMAL_WORDS = ("bird", "tinamou", "lizard", "dove", "quail", "guan")


def standard_name(raw):
    """Fix spacing and capitalisation: 'Cuniculus Paca ' -> 'Cuniculus paca'."""
    words = raw.split()
    if not words:
        return ""
    words = [words[0].capitalize()] + [w.lower() for w in words[1:]]
    return " ".join(words)


def resolve_taxon(row):
    """Return (scientific_name, reason_skipped). Exactly one will be None."""
    raw = (row["ScientificName"] or "").strip()
    if raw.upper() in ("", "N/A"):
        common = row["CommonName"].strip().lower()
        if common in UNIDENTIFIED:
            return UNIDENTIFIED[common], None
        if any(word in common for word in NON_MAMMAL_WORDS):
            return None, "not a mammal"
        return None, "unidentified"
    name = standard_name(raw)
    name = CORRECTIONS.get(name, name)
    if name not in MAMMALS:
        return None, "not a mammal"
    return name, None


# ── Small helpers ─────────────────────────────────────────────────────────────

def clean(value):
    """Strip spaces; turn an empty cell into None (SQL NULL)."""
    if value is None:
        return None
    value = value.strip()
    return value or None


def first_line(error):
    """Postgres errors span several lines; keep just the main message."""
    return str(error).strip().splitlines()[0]


def us_date(text):
    """'6/9/2026' -> '2026-06-09'."""
    month, day, year = (int(part) for part in text.strip().split("/"))
    return f"{year:04d}-{month:02d}-{day:02d}"


def compact_date(text):
    """'20260607' -> '2026-06-07'."""
    return f"{text[:4]}-{text[4:6]}-{text[6:]}"


def read_rows(path, delimiter):
    """Yield each row of a CSV/TSV file as a dict keyed by column name."""
    with open(path, newline="", encoding="utf-8") as fh:
        yield from csv.DictReader(fh, delimiter=delimiter)


# ── Lookup-or-insert functions for parent tables ──────────────────────────────
# Each one checks the cache first, then the database, and only inserts if the
# record is truly new. `added` collects cache keys created during the current
# row, so they can be removed again if that row is rolled back.

def get_taxon(cur, cache, added, sci_name, common_name=None, rank="species"):
    if sci_name in cache:
        return cache[sci_name]
    cur.execute("SELECT taxon_id FROM taxa WHERE scientific_name = %s",
                (sci_name,))
    found = cur.fetchone()
    if found:
        cache[sci_name] = found["taxon_id"]
    else:
        if sci_name in MAMMALS:
            common_name, rank = MAMMALS[sci_name]
        cur.execute(
            """INSERT INTO taxa (scientific_name, common_name, taxonomic_rank)
               VALUES (%s, %s, %s)
               RETURNING taxon_id""",
            (sci_name, common_name, rank))
        cache[sci_name] = cur.fetchone()["taxon_id"]
        added.append((cache, sci_name))
    return cache[sci_name]


def get_observer(cur, cache, added, name, affiliation=None):
    if name in cache:
        return cache[name]
    cur.execute("SELECT observer_id FROM observers WHERE name = %s", (name,))
    found = cur.fetchone()
    if found:
        cache[name] = found["observer_id"]
    else:
        cur.execute(
            """INSERT INTO observers (name, affiliation)
               VALUES (%s, %s)
               RETURNING observer_id""",
            (name, affiliation))
        cache[name] = cur.fetchone()["observer_id"]
        added.append((cache, name))
    return cache[name]


def read_locations():
    """MonitorID -> (lat, long), from the station coordinates file."""
    return {row["MonitorID"].strip(): (row["lat"].strip(), row["lon"].strip())
            for row in read_rows(LOCATION_FILE, ",")}


def get_deployment(cur, cache, added, row, locations):
    # A deployment is one camera during one deployment period,
    # e.g. NWJ20 during DP20260607TO20260614
    camera_id = clean(row["CameraID"])
    period = clean(row["DeploymentPeriodID"])
    key = (camera_id, period)
    if key in cache:
        return cache[key]

    match = re.fullmatch(r"DP(\d{8})TO(\d{8})", period)
    start_date, end_date = compact_date(match[1]), compact_date(match[2])

    cur.execute(
        """SELECT deployment_id FROM deployments
           WHERE camera_id = %s AND start_date = %s""",
        (camera_id, start_date))
    found = cur.fetchone()
    if found:
        cache[key] = found["deployment_id"]
    else:
        monitor_id = clean(row["MonitorID"])
        # A station missing from the locations file gives NULL coordinates,
        # which the NOT NULL constraint rejects, so the row is skipped
        lat, long = locations.get(monitor_id, (None, None))
        cur.execute(
            """INSERT INTO deployments
                   (camera_id, monitor_id, lat, long, start_date, end_date)
               VALUES (%s, %s, %s, %s, %s, %s)
               RETURNING deployment_id""",
            (camera_id, monitor_id, lat, long, start_date, end_date))
        cache[key] = cur.fetchone()["deployment_id"]
        added.append((cache, key))
    return cache[key]


def get_person(cur, cache, added, name):
    if name in cache:
        return cache[name]
    cur.execute("SELECT person_id FROM person WHERE name = %s", (name,))
    found = cur.fetchone()
    if found:
        cache[name] = found["person_id"]
    else:
        cur.execute(
            "INSERT INTO person (name) VALUES (%s) RETURNING person_id",
            (name,))
        cache[name] = cur.fetchone()["person_id"]
        added.append((cache, name))
    return cache[name]


def undo_cache(added):
    """Forget IDs created during a row that was rolled back."""
    for cache, key in added:
        cache.pop(key, None)


# ── Loaders, one per file ─────────────────────────────────────────────────────

def load_camera_traps(conn, cur, caches, counts):
    locations = read_locations()
    for line_no, row in enumerate(read_rows(CAMERA_FILE, ","), start=2):
        sci_name, reason = resolve_taxon(row)
        if reason:
            counts["filtered"][reason] += 1
            continue

        count = clean(row["NumberOfIndividuals"])
        if count is not None and not count.isdigit():
            print(f"  NOTE {CAMERA_FILE} line {line_no}: count {count!r} "
                  "is not a number, using default of 1", file=sys.stderr)
            count = None

        added = []
        try:
            deployment_id = get_deployment(cur, caches["deployments"], added, row,
                                           locations)
            taxon_id = get_taxon(cur, caches["taxa"], added, sci_name)
            observer = clean(row["IdentifiedBy"])
            observer_id = (get_observer(cur, caches["observers"], added, observer)
                           if observer else None)
            cur.execute(
                """INSERT INTO camera_detections
                       (deployment_id, taxon_id, identified_by, video_id,
                        detection_date, detection_time, number_of_individuals,
                        needs_review, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, 1), %s, %s)
                   ON CONFLICT (deployment_id, video_id, taxon_id) DO NOTHING""",
                (deployment_id, taxon_id, observer_id, clean(row["VideoID"]),
                 us_date(row["Date"]), clean(row["Time"]), count,
                 row["NeedsReview"].strip().upper() == "TRUE",
                 clean(row["Notes"])))
            if cur.rowcount == 0:
                counts["filtered"]["duplicate"] += 1
            counts["camera_detections"] += cur.rowcount
            conn.commit()
        except Exception as e:
            conn.rollback()
            undo_cache(added)
            counts["skipped"] += 1
            print(f"  SKIP {CAMERA_FILE} line {line_no}: {first_line(e)}",
                  file=sys.stderr)


def add_placeholders(conn, cur, caches, counts):
    """
    There is no real data yet for direct sightings or human activity events,
    so these five tables each get ONE clearly labelled placeholder row. This
    keeps every table populated (so the Flask pages have something to show)
    without adding fake records that could be mistaken for real ones.
    """
    added = []
    try:
        observer_id = get_observer(cur, caches["observers"], added,
                                   "Placeholder Observer",
                                   "PLACEHOLDER - not a real person")
        taxon_id = get_taxon(cur, caches["taxa"], added, "Mammalia")

        cur.execute(
            """INSERT INTO occurrences (taxon_id, observer_id, obs_date, notes)
               VALUES (%s, %s, %s, %s)""",
            (taxon_id, observer_id, "2026-06-07",
             "PLACEHOLDER - not a real sighting"))

        cur.execute(
            """INSERT INTO events (observer_id, event_type, event_date)
               VALUES (%s, %s, %s)
               RETURNING event_id""",
            (observer_id, "sighting", "2026-06-07"))
        event_id = cur.fetchone()["event_id"]

        cur.execute(
            """INSERT INTO event_taxa (event_id, taxon_id, outcome)
               VALUES (%s, %s, %s)""",
            (event_id, taxon_id, "seen"))

        person_id = get_person(cur, caches["person"], added,
                               "Placeholder Participant")
        cur.execute(
            """INSERT INTO event_persons (event_id, person_id)
               VALUES (%s, %s)""",
            (event_id, person_id))

        conn.commit()
        for table in ("occurrences", "events", "event_taxa", "event_persons"):
            counts[table] += 1
    except Exception as e:
        conn.rollback()
        undo_cache(added)
        counts["skipped"] += 1
        print(f"  SKIP placeholders: {first_line(e)}", file=sys.stderr)


# ── Main ──────────────────────────────────────────────────────────────────────

def main():
    conn = psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)
    cur = conn.cursor()

    caches = {"taxa": {}, "observers": {}, "deployments": {},
              "person": {}, "events": {}}
    counts = {"camera_detections": 0, "occurrences": 0, "events": 0,
              "event_taxa": 0, "event_persons": 0, "skipped": 0,
              "filtered": Counter()}

    load_camera_traps(conn, cur, caches, counts)
    add_placeholders(conn, cur, caches, counts)

    conn.close()

    print("Done.")
    print("Rows loaded:")
    print(f"  taxa:              {len(caches['taxa'])}")
    print(f"  observers:         {len(caches['observers'])}")
    print(f"  deployments:       {len(caches['deployments'])}")
    print(f"  person:            {len(caches['person'])}")
    for table in ("camera_detections", "occurrences", "events",
                  "event_taxa", "event_persons"):
        print(f"  {table + ':':19}{counts[table]}")
    print("Camera records left out:")
    print(f"  not a mammal:      {counts['filtered']['not a mammal']}")
    print(f"  unidentified:      {counts['filtered']['unidentified']}")
    print(f"  duplicate rows:    {counts['filtered']['duplicate']}")
    print(f"Rows rejected by constraints: {counts['skipped']}")


if __name__ == "__main__":
    main()
