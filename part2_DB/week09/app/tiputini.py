# app/tiputini.py
"""
Tiputini Mammalian Database — Flask web interface

Run from inside the app/ folder, with the venv active:
    flask --app tiputini run

Every table has two routes:
    /<table>       read route: lists the rows in an HTML table
    /<table>/new   insert route: GET shows a blank form, POST inserts the row
                   and redirects back to the list

Foreign keys are chosen from dropdowns filled by a live SELECT, and every
INSERT is wrapped in try/except/finally so a constraint violation re-shows
the form with a readable message instead of crashing.
"""

import psycopg2
import psycopg2.extras
from psycopg2 import errors as pg_errors
from flask import Flask, render_template, request, redirect, url_for

from config import DSN

app = Flask(__name__)


# ── Database helpers ─────────────────────────────────────────────────────────

def get_db():
    return psycopg2.connect(DSN, cursor_factory=psycopg2.extras.RealDictCursor)


def fetch_all(sql, params=()):
    """Run a SELECT and return every row as a list of dicts."""
    conn = get_db()
    cur = conn.cursor()
    cur.execute(sql, params)
    rows = cur.fetchall()
    conn.close()
    return rows


def form_value(name):
    """Read a form field; an empty box becomes None (SQL NULL)."""
    value = request.form.get(name, "").strip()
    return value or None


# ── Dropdown options for foreign keys (live SELECTs) ─────────────────────────

def taxa_options():
    return fetch_all("""SELECT taxon_id, scientific_name, common_name
                        FROM taxa ORDER BY scientific_name""")


def observer_options():
    return fetch_all("SELECT observer_id, name FROM observers ORDER BY name")


def person_options():
    return fetch_all("SELECT person_id, name FROM person ORDER BY name")


def deployment_options():
    return fetch_all("""SELECT deployment_id, camera_id, monitor_id,
                               start_date, end_date
                        FROM deployments ORDER BY camera_id, start_date""")


def event_options():
    return fetch_all("""SELECT event_id, event_type, event_date
                        FROM events ORDER BY event_date, event_id""")


# ── Turning database errors into readable messages ───────────────────────────

# Messages for specific constraints, keyed by the constraint's name in Postgres
CONSTRAINT_MESSAGES = {
    "taxa_scientific_name_key":
        "That scientific name is already in the database.",
    "taxa_scientific_name_check": "Scientific name cannot be blank.",
    "taxa_taxonomic_rank_check":
        "Rank must be species, genus, family, order or class.",
    "person_name_check": "Name cannot be blank.",
    "person_sex_check": "Sex must be male or female (or left blank).",
    "person_age_check": "Age must be between 0 and 120.",
    "observers_name_check": "Name cannot be blank.",
    "deployments_camera_id_check": "Camera ID cannot be blank.",
    "deployments_start_date_check":
        "Start date can't be before TBS was established (1994).",
    "deployments_lat_check":
        "Latitude must be inside the TBS study area (-1.0 to -0.3). "
        "Check for a missing minus sign.",
    "deployments_long_check":
        "Longitude must be inside the TBS study area (-76.6 to -75.7). "
        "Check for a missing minus sign or swapped lat/long.",
    "deployments_check": "The end date can't be before the start date.",
    "camera_detections_deployment_id_video_id_taxon_id_key":
        "This species is already recorded for that video and deployment.",
    "camera_detections_video_id_check": "Video file cannot be blank.",
    "camera_detections_detection_date_check":
        "Date can't be before TBS was established (1994).",
    "camera_detections_number_of_individuals_check":
        "Number of individuals must be at least 1.",
    "occurrences_obs_date_check":
        "Date can't be before TBS was established (1994).",
    "occurrences_lat_check":
        "Latitude must be inside the TBS study area (-1.0 to -0.3).",
    "occurrences_long_check":
        "Longitude must be inside the TBS study area (-76.6 to -75.7).",
    "occurrences_check":
        "Enter both latitude and longitude, or leave both blank.",
    "events_event_date_check":
        "Date can't be before TBS was established (1994).",
    "events_event_type_check":
        "Event type must be fishing, hunting, pets, sighting or pursuit.",
    "events_lat_check":
        "Latitude must be inside the TBS study area (-1.0 to -0.3).",
    "events_long_check":
        "Longitude must be inside the TBS study area (-76.6 to -75.7).",
    "events_check": "Enter both latitude and longitude, or leave both blank.",
    "event_taxa_pkey": "That species is already linked to this event.",
    "event_taxa_outcome_check": "Outcome must be seen, pursued or killed.",
    "event_persons_pkey": "That person is already linked to this event.",
}


def friendly_error(e):
    """Explain a database error in plain words for the person using the form."""
    constraint = getattr(e.diag, "constraint_name", None)
    if constraint in CONSTRAINT_MESSAGES:
        return CONSTRAINT_MESSAGES[constraint]
    if isinstance(e, pg_errors.NotNullViolation):
        column = (e.diag.column_name or "a required field").replace("_", " ")
        return f"A required field was left blank: {column}."
    if isinstance(e, pg_errors.UniqueViolation):
        return "That record already exists."
    if isinstance(e, pg_errors.ForeignKeyViolation):
        return "The selected record no longer exists. Reload the page and try again."
    if isinstance(e, pg_errors.CheckViolation):
        return "One of the values is outside the allowed range."
    if isinstance(e, psycopg2.DataError):
        return "One of the values isn't in the right format (check dates, times and numbers)."
    return "The record could not be saved."


# ── Index ─────────────────────────────────────────────────────────────────────

TABLES = ["taxa", "observers", "person", "deployments", "camera_detections",
          "occurrences", "events", "event_taxa", "event_persons"]


@app.route("/")
def index():
    conn = get_db()
    cur = conn.cursor()
    counts = {}
    for table in TABLES:
        # Table names come from the fixed list above, never from the user
        cur.execute(f"SELECT COUNT(*) AS n FROM {table}")
        counts[table] = cur.fetchone()["n"]
    cur.execute("""
        SELECT t.scientific_name, t.common_name, COUNT(*) AS n
        FROM camera_detections c
        JOIN taxa t ON t.taxon_id = c.taxon_id
        WHERE t.taxonomic_rank = 'species'
        GROUP BY t.scientific_name, t.common_name
        ORDER BY n DESC
        LIMIT 5
    """)
    top_species = cur.fetchall()
    conn.close()
    return render_template("index.html", counts=counts, top_species=top_species)


# ── Taxa ──────────────────────────────────────────────────────────────────────

@app.route("/taxa")
def list_taxa():
    rows = fetch_all("""
        SELECT t.taxon_id, t.scientific_name, t.taxonomic_rank, t.common_name,
               COUNT(c.detection_id) AS n_detections
        FROM taxa t
        LEFT JOIN camera_detections c ON c.taxon_id = t.taxon_id
        GROUP BY t.taxon_id
        ORDER BY t.scientific_name
    """)
    return render_template("taxa_list.html", rows=rows)


@app.route("/taxa/new", methods=["GET", "POST"])
def new_taxon():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO taxa (scientific_name, taxonomic_rank, common_name)
                   VALUES (%s, %s, %s)""",
                (form_value("scientific_name"),
                 form_value("taxonomic_rank") or "species",
                 form_value("common_name")))
            conn.commit()
            return redirect(url_for("list_taxa"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("taxa_form.html", error=error, form=request.form)


# ── Observers ─────────────────────────────────────────────────────────────────

@app.route("/observers")
def list_observers():
    rows = fetch_all("""
        SELECT o.observer_id, o.name, o.affiliation,
               COUNT(c.detection_id) AS n_identified
        FROM observers o
        LEFT JOIN camera_detections c ON c.identified_by = o.observer_id
        GROUP BY o.observer_id
        ORDER BY o.name
    """)
    return render_template("observers_list.html", rows=rows)


@app.route("/observers/new", methods=["GET", "POST"])
def new_observer():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO observers (name, affiliation) VALUES (%s, %s)",
                (form_value("name"), form_value("affiliation")))
            conn.commit()
            return redirect(url_for("list_observers"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("observers_form.html", error=error, form=request.form)


# ── Person ────────────────────────────────────────────────────────────────────

@app.route("/person")
def list_person():
    rows = fetch_all("SELECT * FROM person ORDER BY name")
    return render_template("person_list.html", rows=rows)


@app.route("/person/new", methods=["GET", "POST"])
def new_person():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO person (name, sex, age) VALUES (%s, %s, %s)",
                (form_value("name"), form_value("sex"), form_value("age")))
            conn.commit()
            return redirect(url_for("list_person"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("person_form.html", error=error, form=request.form)


# ── Deployments ───────────────────────────────────────────────────────────────

@app.route("/deployments")
def list_deployments():
    rows = fetch_all("""
        SELECT d.deployment_id, d.camera_id, d.monitor_id, d.lat, d.long,
               d.start_date, d.end_date,
               COUNT(c.detection_id) AS n_detections
        FROM deployments d
        LEFT JOIN camera_detections c ON c.deployment_id = d.deployment_id
        GROUP BY d.deployment_id
        ORDER BY d.camera_id, d.start_date
    """)
    return render_template("deployments_list.html", rows=rows)


@app.route("/deployments/new", methods=["GET", "POST"])
def new_deployment():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO deployments
                       (camera_id, monitor_id, lat, long, start_date, end_date)
                   VALUES (%s, %s, %s, %s, %s, %s)""",
                (form_value("camera_id"), form_value("monitor_id"),
                 form_value("lat"), form_value("long"),
                 form_value("start_date"), form_value("end_date")))
            conn.commit()
            return redirect(url_for("list_deployments"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("deployments_form.html", error=error, form=request.form)


# ── Camera detections ─────────────────────────────────────────────────────────

@app.route("/camera_detections")
def list_camera_detections():
    rows = fetch_all("""
        SELECT c.detection_id, d.camera_id, d.monitor_id, c.video_id,
               c.detection_date, c.detection_time,
               t.scientific_name, t.common_name, c.number_of_individuals,
               o.name AS identified_by, c.needs_review, c.notes
        FROM camera_detections c
        JOIN deployments d ON d.deployment_id = c.deployment_id
        JOIN taxa t        ON t.taxon_id      = c.taxon_id
        LEFT JOIN observers o ON o.observer_id = c.identified_by
        ORDER BY c.detection_date DESC, c.detection_time DESC, c.detection_id DESC
    """)
    return render_template("camera_detections_list.html", rows=rows)


@app.route("/camera_detections/new", methods=["GET", "POST"])
def new_camera_detection():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO camera_detections
                       (deployment_id, taxon_id, identified_by, video_id,
                        detection_date, detection_time, number_of_individuals,
                        needs_review, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, COALESCE(%s, 1), %s, %s)""",
                (form_value("deployment_id"), form_value("taxon_id"),
                 form_value("identified_by"), form_value("video_id"),
                 form_value("detection_date"), form_value("detection_time"),
                 form_value("number_of_individuals"),
                 "needs_review" in request.form,
                 form_value("notes")))
            conn.commit()
            return redirect(url_for("list_camera_detections"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("camera_detections_form.html", error=error,
                           form=request.form,
                           deployments=deployment_options(),
                           taxa=taxa_options(),
                           observers=observer_options())


# ── Occurrences ───────────────────────────────────────────────────────────────

@app.route("/occurrences")
def list_occurrences():
    rows = fetch_all("""
        SELECT oc.occurrence_id, oc.obs_date, oc.obs_time, oc.lat, oc.long,
               t.scientific_name, t.common_name, o.name AS observer, oc.notes
        FROM occurrences oc
        JOIN taxa t      ON t.taxon_id    = oc.taxon_id
        JOIN observers o ON o.observer_id = oc.observer_id
        ORDER BY oc.obs_date DESC, oc.occurrence_id DESC
    """)
    return render_template("occurrences_list.html", rows=rows)


@app.route("/occurrences/new", methods=["GET", "POST"])
def new_occurrence():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO occurrences
                       (taxon_id, observer_id, obs_date, obs_time, lat, long, notes)
                   VALUES (%s, %s, %s, %s, %s, %s, %s)""",
                (form_value("taxon_id"), form_value("observer_id"),
                 form_value("obs_date"), form_value("obs_time"),
                 form_value("lat"), form_value("long"), form_value("notes")))
            conn.commit()
            return redirect(url_for("list_occurrences"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("occurrences_form.html", error=error,
                           form=request.form,
                           taxa=taxa_options(),
                           observers=observer_options())


# ── Events ────────────────────────────────────────────────────────────────────

@app.route("/events")
def list_events():
    rows = fetch_all("""
        SELECT e.event_id, e.event_type, e.event_date, e.lat, e.long,
               o.name AS observer
        FROM events e
        JOIN observers o ON o.observer_id = e.observer_id
        ORDER BY e.event_date DESC, e.event_id DESC
    """)
    return render_template("events_list.html", rows=rows)


@app.route("/events/new", methods=["GET", "POST"])
def new_event():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO events (observer_id, event_type, event_date, lat, long)
                   VALUES (%s, %s, %s, %s, %s)""",
                (form_value("observer_id"), form_value("event_type"),
                 form_value("event_date"), form_value("lat"), form_value("long")))
            conn.commit()
            return redirect(url_for("list_events"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("events_form.html", error=error,
                           form=request.form,
                           observers=observer_options())


# ── Event taxa (linking table) ────────────────────────────────────────────────

@app.route("/event_taxa")
def list_event_taxa():
    rows = fetch_all("""
        SELECT et.event_id, e.event_type, e.event_date,
               t.scientific_name, t.common_name, et.outcome
        FROM event_taxa et
        JOIN events e ON e.event_id = et.event_id
        JOIN taxa t   ON t.taxon_id = et.taxon_id
        ORDER BY e.event_date DESC, et.event_id, t.scientific_name
    """)
    return render_template("event_taxa_list.html", rows=rows)


@app.route("/event_taxa/new", methods=["GET", "POST"])
def new_event_taxon():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                """INSERT INTO event_taxa (event_id, taxon_id, outcome)
                   VALUES (%s, %s, %s)""",
                (form_value("event_id"), form_value("taxon_id"),
                 form_value("outcome")))
            conn.commit()
            return redirect(url_for("list_event_taxa"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("event_taxa_form.html", error=error,
                           form=request.form,
                           events=event_options(),
                           taxa=taxa_options())


# ── Event persons (linking table) ─────────────────────────────────────────────

@app.route("/event_persons")
def list_event_persons():
    rows = fetch_all("""
        SELECT ep.event_id, e.event_type, e.event_date, p.name
        FROM event_persons ep
        JOIN events e ON e.event_id  = ep.event_id
        JOIN person p ON p.person_id = ep.person_id
        ORDER BY e.event_date DESC, ep.event_id, p.name
    """)
    return render_template("event_persons_list.html", rows=rows)


@app.route("/event_persons/new", methods=["GET", "POST"])
def new_event_person():
    error = None
    if request.method == "POST":
        conn = get_db()
        cur = conn.cursor()
        try:
            cur.execute(
                "INSERT INTO event_persons (event_id, person_id) VALUES (%s, %s)",
                (form_value("event_id"), form_value("person_id")))
            conn.commit()
            return redirect(url_for("list_event_persons"))
        except (psycopg2.IntegrityError, psycopg2.DataError) as e:
            conn.rollback()
            error = friendly_error(e)
        finally:
            conn.close()
    return render_template("event_persons_form.html", error=error,
                           form=request.form,
                           events=event_options(),
                           people=person_options())
