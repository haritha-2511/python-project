"""Faculty timetable and workload report routes (Member 4).

This module only reads the shared SQLite database.  Timetable rows are
created by the timetable module; this module does not create or change any
database tables.
"""
from contextlib import closing

from flask import Blueprint, abort, render_template

from db import get_db
from timetable.slots import DAYS, PERIODS, TIMINGS, BREAKS, build_empty_grid


workload_bp = Blueprint("workload", __name__, url_prefix="/workload")


def slot_duration_minutes(slot):
    """Return the number of minutes in one existing timetable slot.

    The timetable's TIMINGS values intentionally use the same 12-hour clock
    format as the shared slot file.  When an end time is numerically earlier
    than its start time (for example, 12:50 - 01:40), it is in the afternoon,
    so twelve hours are added before finding the difference.
    """
    if slot not in TIMINGS:
        raise ValueError("Unknown timetable slot: " + str(slot))

    start_text, end_text = TIMINGS[slot].split(" - ")

    def to_minutes(time_text):
        hours, minutes = [int(value) for value in time_text.split(":")]
        return hours * 60 + minutes

    start = to_minutes(start_text)
    end = to_minutes(end_text)
    if end <= start:
        end += 12 * 60
    return end - start


def workload_status(periods, max_periods):
    """Describe the workload using the existing period-based faculty limit."""
    if periods == 0:
        return "No scheduled classes"
    if periods > max_periods:
        return "Over limit"
    if periods == max_periods:
        return "At limit"
    return "Below limit"


def get_workload_summary(conn):
    """Return weekly totals for every faculty member, including zero-load rows.

    The LEFT JOIN begins with faculty so a faculty member is listed even when
    there are no timetable rows.  Library periods have faculty_id = NULL and
    cannot join to a faculty member, so they are not counted.
    """
    rows = conn.execute("""
        SELECT f.id, f.faculty_code, f.name, f.department, f.max_periods,
               t.id AS timetable_id, t.slot
        FROM faculty f
        LEFT JOIN timetable t
               ON t.faculty_id = f.id
              AND t.faculty_id IS NOT NULL
        ORDER BY f.name, t.day, t.slot
    """).fetchall()

    summary_by_id = {}
    for row in rows:
        faculty_id = row["id"]
        if faculty_id not in summary_by_id:
            summary_by_id[faculty_id] = {
                "id": faculty_id,
                "faculty_code": row["faculty_code"],
                "name": row["name"],
                "department": row["department"],
                "max_periods": row["max_periods"],
                "periods": 0,
                "minutes": 0,
            }

        # A NULL timetable_id is the extra row created by LEFT JOIN for a
        # faculty member with no scheduled classes.
        if row["timetable_id"] is not None:
            summary_by_id[faculty_id]["periods"] += 1
            summary_by_id[faculty_id]["minutes"] += slot_duration_minutes(row["slot"])

    summary = list(summary_by_id.values())
    for item in summary:
        item["hours"] = item["minutes"] / 60
        item["status"] = workload_status(item["periods"], item["max_periods"])
    return summary


def get_faculty_timetable(conn, faculty_id):
    """Return one faculty record and its saved teaching rows for the week."""
    faculty = conn.execute("""
        SELECT id, faculty_code, name, department, max_periods
        FROM faculty WHERE id = ?
    """, (faculty_id,)).fetchone()
    if faculty is None:
        return None, []

    rows = conn.execute("""
        SELECT t.day, t.slot, s.code AS subject_code, s.name AS subject_name,
               sec.name AS section_name, r.name AS room_name
        FROM timetable t
        LEFT JOIN subjects s ON s.id = t.subject_id
        LEFT JOIN sections sec ON sec.id = t.section_id
        LEFT JOIN rooms r ON r.id = t.room_id
        WHERE t.faculty_id = ?
        ORDER BY t.day, t.slot
    """, (faculty_id,)).fetchall()

    classes = []
    for row in rows:
        item = dict(row)
        item["duration_minutes"] = slot_duration_minutes(item["slot"])
        classes.append(item)
    return dict(faculty), classes


def make_faculty_grid(classes):
    """Put saved classes into the same weekday/period grid used by timetable."""
    grid = build_empty_grid()
    for item in classes:
        day, slot = item["day"], item["slot"]
        if day in grid and slot in grid[day]:
            grid[day][slot] = item
    return grid


@workload_bp.route("/")
def summary():
    """Show workload totals for all faculty members."""
    with closing(get_db()) as conn:
        faculty_workloads = get_workload_summary(conn)
    return render_template("workload/summary.html", faculty_workloads=faculty_workloads)


@workload_bp.route("/faculty/<int:faculty_id>")
def faculty_timetable(faculty_id):
    """Show the saved weekly timetable and totals for one selected faculty."""
    with closing(get_db()) as conn:
        faculty, classes = get_faculty_timetable(conn, faculty_id)
        faculty_workloads = get_workload_summary(conn)

    if faculty is None:
        abort(404)

    workload = next(item for item in faculty_workloads if item["id"] == faculty_id)
    return render_template(
        "workload/faculty_timetable.html",
        faculty=faculty,
        workload=workload,
        grid=make_faculty_grid(classes),
        days=DAYS,
        periods=PERIODS,
        timings=TIMINGS,
        breaks=BREAKS,
    )
