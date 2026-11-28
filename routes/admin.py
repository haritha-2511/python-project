"""
Member 2 - Admin module
Faculty (add/edit/delete), Subjects (add/edit/delete), fixed data view,
and automatic faculty-subject allocation.
"""
from contextlib import closing

from flask import Blueprint, abort, flash, redirect, render_template, request, url_for

from allocation import run_allocation
from db import get_db
from seed_data import DEPARTMENTS, LAB_TYPES, PERIOD_GRID, WORKING_DAYS

admin_bp = Blueprint("admin", __name__)

SUBJECT_TYPE_SQL = """CASE WHEN theory_periods > 0 AND lab_periods > 0 THEN 'Theory + Lab'
                           WHEN lab_periods > 0 THEN 'Lab' ELSE 'Theory' END"""

FACULTY_LOAD_SQL = """
    SELECT f.*,
           (SELECT COUNT(*) FROM faculty_subjects fs WHERE fs.faculty_id = f.id) AS n_subjects,
           COALESCE((SELECT SUM(s.theory_periods + s.lab_periods)
                     FROM allocations a JOIN subjects s ON s.id = a.subject_id
                     WHERE a.faculty_id = f.id), 0) AS assigned_periods
    FROM faculty f ORDER BY f.id
"""


def _all_subjects(conn):
    rows = conn.execute(f"""
        SELECT *, {SUBJECT_TYPE_SQL} AS subject_type,
               (SELECT COUNT(*) FROM section_subjects ss WHERE ss.subject_id = subjects.id) AS n_sections,
               (SELECT COUNT(*) FROM faculty_subjects fs WHERE fs.subject_id = subjects.id) AS n_faculty
        FROM subjects ORDER BY department, code""").fetchall()
    return [dict(r) for r in rows]


# ---------------------------------------------------------------- dashboard
@admin_bp.route("/")
def index():
    with closing(get_db()) as conn:
        one = lambda sql: conn.execute(sql).fetchone()[0]
        stats = {
            "faculty": one("SELECT COUNT(*) FROM faculty"),
            "subjects": one("SELECT COUNT(*) FROM subjects"),
            "sections": one("SELECT COUNT(*) FROM sections"),
            "rooms": one("SELECT COUNT(*) FROM rooms"),
            "pairs": one("SELECT COUNT(*) FROM section_subjects"),
            "allocated": one("SELECT COUNT(*) FROM allocations"),
            "needed": one("""SELECT COALESCE(SUM(s.theory_periods + s.lab_periods), 0)
                             FROM section_subjects ss JOIN subjects s ON s.id = ss.subject_id"""),
            "capacity": one("SELECT COALESCE(SUM(max_periods), 0) FROM faculty"),
        }
    return render_template("admin/index.html", stats=stats)


# ------------------------------------------------------------------ faculty
def _read_faculty_form():
    f = request.form
    form = {
        "name": f.get("name", "").strip(),
        "department": f.get("department", ""),
        "max_periods": f.get("max_periods", "").strip(),
        "subject_ids": [int(x) for x in f.getlist("subject_ids") if x.isdigit()],
    }
    errors = []
    if not form["name"]:
        errors.append("Faculty name is required.")
    if form["department"] not in DEPARTMENTS:
        errors.append("Choose a department.")
    if not form["max_periods"].isdigit() or not 1 <= int(form["max_periods"]) <= 35:
        errors.append("Maximum periods per week must be a number from 1 to 35.")
    if not form["subject_ids"]:
        errors.append("Select at least one subject this faculty can teach.")
    return form, errors


def _save_faculty_subjects(conn, faculty_id, subject_ids):
    conn.execute("DELETE FROM faculty_subjects WHERE faculty_id = ?", (faculty_id,))
    conn.executemany("INSERT INTO faculty_subjects (faculty_id, subject_id) VALUES (?, ?)",
                     [(faculty_id, sid) for sid in subject_ids])


@admin_bp.route("/faculty")
def faculty_list():
    with closing(get_db()) as conn:
        faculty = conn.execute(FACULTY_LOAD_SQL).fetchall()
    return render_template("admin/faculty_list.html", faculty=faculty)


@admin_bp.route("/faculty/add", methods=["GET", "POST"])
def faculty_add():
    form = {"name": "", "department": "", "max_periods": "16", "subject_ids": []}
    with closing(get_db()) as conn:
        if request.method == "POST":
            form, errors = _read_faculty_form()
            if not errors:
                cur = conn.execute("INSERT INTO faculty (name, department, max_periods) VALUES (?,?,?)",
                                   (form["name"], form["department"], int(form["max_periods"])))
                fid = cur.lastrowid
                conn.execute("UPDATE faculty SET faculty_code = ? WHERE id = ?", (f"F{fid:03d}", fid))
                _save_faculty_subjects(conn, fid, form["subject_ids"])
                conn.commit()
                flash(f"Faculty {form['name']} added (F{fid:03d}).", "success")
                return redirect(url_for("admin.faculty_list"))
            for e in errors:
                flash(e, "danger")
        return render_template("admin/faculty_form.html", form=form, mode="Add",
                               subjects=_all_subjects(conn), departments=DEPARTMENTS)


@admin_bp.route("/faculty/<int:fid>/edit", methods=["GET", "POST"])
def faculty_edit(fid):
    with closing(get_db()) as conn:
        row = conn.execute("SELECT * FROM faculty WHERE id = ?", (fid,)).fetchone()
        if row is None:
            abort(404)
        form = {
            "name": row["name"], "department": row["department"], "max_periods": str(row["max_periods"]),
            "subject_ids": [r["subject_id"] for r in
                            conn.execute("SELECT subject_id FROM faculty_subjects WHERE faculty_id = ?", (fid,))],
        }
        if request.method == "POST":
            form, errors = _read_faculty_form()
            if not errors:
                conn.execute("UPDATE faculty SET name = ?, department = ?, max_periods = ? WHERE id = ?",
                             (form["name"], form["department"], int(form["max_periods"]), fid))
                _save_faculty_subjects(conn, fid, form["subject_ids"])
                conn.commit()
                flash("Faculty updated. Run the allocation again to refresh assignments.", "success")
                return redirect(url_for("admin.faculty_list"))
            for e in errors:
                flash(e, "danger")
        return render_template("admin/faculty_form.html", form=form, mode="Edit",
                               subjects=_all_subjects(conn), departments=DEPARTMENTS)


@admin_bp.route("/faculty/<int:fid>/delete", methods=["POST"])
def faculty_delete(fid):
    with closing(get_db()) as conn:
        conn.execute("DELETE FROM faculty WHERE id = ?", (fid,))
        conn.commit()
    flash("Faculty deleted. Run the allocation again to refresh assignments.", "warning")
    return redirect(url_for("admin.faculty_list"))


# ----------------------------------------------------------------- subjects
def _read_subject_form():
    f = request.form
    form = {
        "code": f.get("code", "").strip().upper(),
        "name": f.get("name", "").strip(),
        "department": f.get("department", ""),
        "theory_periods": f.get("theory_periods", "").strip(),
        "lab_periods": f.get("lab_periods", "").strip(),
        "lab_type": f.get("lab_type", "NONE"),
    }
    errors = []
    if not form["code"]:
        errors.append("Subject code is required.")
    if not form["name"]:
        errors.append("Subject name is required.")
    if form["department"] not in DEPARTMENTS:
        errors.append("Choose a department.")
    for key, label in (("theory_periods", "Theory"), ("lab_periods", "Lab")):
        if not form[key].isdigit() or not 0 <= int(form[key]) <= 10:
            errors.append(f"{label} periods must be a number from 0 to 10.")
    if not errors:
        theory, lab = int(form["theory_periods"]), int(form["lab_periods"])
        if theory + lab == 0:
            errors.append("A subject needs at least one theory or lab period.")
        if form["lab_type"] not in LAB_TYPES:
            errors.append("Choose a lab type.")
        elif lab > 0 and form["lab_type"] == "NONE":
            errors.append("Choose where the lab periods are held.")
        if lab == 0:
            form["lab_type"] = "NONE"
    return form, errors


@admin_bp.route("/subjects")
def subjects_list():
    with closing(get_db()) as conn:
        subjects = _all_subjects(conn)
    return render_template("admin/subjects_list.html", subjects=subjects, lab_types=LAB_TYPES)


def _subject_form_page(subject_id=None):
    mode = "Edit" if subject_id else "Add"
    form = {"code": "", "name": "", "department": "", "theory_periods": "3", "lab_periods": "0", "lab_type": "NONE"}
    with closing(get_db()) as conn:
        if subject_id:
            row = conn.execute("SELECT * FROM subjects WHERE id = ?", (subject_id,)).fetchone()
            if row is None:
                abort(404)
            form = {k: str(row[k]) for k in form}
        if request.method == "POST":
            form, errors = _read_subject_form()
            if not errors:
                clash = conn.execute("SELECT id FROM subjects WHERE code = ? AND id != ?",
                                     (form["code"], subject_id or 0)).fetchone()
                if clash:
                    errors.append(f"Subject code {form['code']} already exists.")
            if not errors:
                values = (form["code"], form["name"], form["department"], int(form["theory_periods"]),
                          int(form["lab_periods"]), form["lab_type"])
                if subject_id:
                    conn.execute("""UPDATE subjects SET code=?, name=?, department=?, theory_periods=?,
                                    lab_periods=?, lab_type=? WHERE id=?""", values + (subject_id,))
                    flash("Subject updated. Run the allocation again to refresh assignments.", "success")
                else:
                    conn.execute("""INSERT INTO subjects (code, name, department, theory_periods, lab_periods,
                                    lab_type) VALUES (?,?,?,?,?,?)""", values)
                    flash(f"Subject {form['code']} added.", "success")
                conn.commit()
                return redirect(url_for("admin.subjects_list"))
            for e in errors:
                flash(e, "danger")
    return render_template("admin/subject_form.html", form=form, mode=mode,
                           departments=DEPARTMENTS, lab_types=LAB_TYPES)


@admin_bp.route("/subjects/add", methods=["GET", "POST"])
def subject_add():
    return _subject_form_page()


@admin_bp.route("/subjects/<int:sid>/edit", methods=["GET", "POST"])
def subject_edit(sid):
    return _subject_form_page(sid)


@admin_bp.route("/subjects/<int:sid>/delete", methods=["POST"])
def subject_delete(sid):
    with closing(get_db()) as conn:
        used = conn.execute("SELECT COUNT(*) FROM section_subjects WHERE subject_id = ?", (sid,)).fetchone()[0]
        if used:
            flash("This subject is part of a section's fixed subject list, so it can't be deleted.", "danger")
        else:
            conn.execute("DELETE FROM subjects WHERE id = ?", (sid,))
            conn.commit()
            flash("Subject deleted.", "warning")
    return redirect(url_for("admin.subjects_list"))


# --------------------------------------------------------------- fixed data
@admin_bp.route("/fixed-data")
def fixed_data():
    with closing(get_db()) as conn:
        rooms = conn.execute("SELECT * FROM rooms ORDER BY room_type, name").fetchall()
        sections = []
        for sec in conn.execute("""SELECT sec.*, r.name AS room FROM sections sec
                                   LEFT JOIN rooms r ON r.id = sec.home_room_id ORDER BY sec.id"""):
            subs = conn.execute(f"""SELECT s.*, {SUBJECT_TYPE_SQL} AS subject_type
                                    FROM section_subjects ss JOIN subjects s ON s.id = ss.subject_id
                                    WHERE ss.section_id = ? ORDER BY s.code""", (sec["id"],)).fetchall()
            sections.append({"info": sec, "subjects": subs,
                             "theory": sum(s["theory_periods"] for s in subs),
                             "lab": sum(s["lab_periods"] for s in subs)})
    return render_template("admin/fixed_data.html", rooms=rooms, sections=sections,
                           periods=PERIOD_GRID, days=WORKING_DAYS, lab_types=LAB_TYPES)


# --------------------------------------------------------------- allocation
@admin_bp.route("/allocation")
def allocation():
    with closing(get_db()) as conn:
        faculty = conn.execute(FACULTY_LOAD_SQL).fetchall()
        by_section = {}
        for r in conn.execute("""
            SELECT sec.name AS section_name, s.code, s.name AS subject_name,
                   s.theory_periods, s.lab_periods, f.faculty_code, f.name AS faculty_name
            FROM sections sec
            JOIN section_subjects ss ON ss.section_id = sec.id
            JOIN subjects s ON s.id = ss.subject_id
            LEFT JOIN allocations a ON a.section_id = sec.id AND a.subject_id = s.id
            LEFT JOIN faculty f ON f.id = a.faculty_id
            ORDER BY sec.id, s.code"""):
            by_section.setdefault(r["section_name"], []).append(r)
    return render_template("admin/allocation.html", faculty=faculty, by_section=by_section)


@admin_bp.route("/allocation/run", methods=["POST"])
def allocation_run():
    with closing(get_db()) as conn:
        result = run_allocation(conn)
        conn.commit()
    flash(f"Allocated {result['assigned']} section-subject pairs automatically.", "success")
    for u in result["unallocated"]:
        flash(f"Not allocated: {u['section']} - {u['code']} {u['subject']}. {u['reason']}.", "warning")
    return redirect(url_for("admin.allocation"))


@admin_bp.route("/allocation/clear", methods=["POST"])
def allocation_clear():
    with closing(get_db()) as conn:
        conn.execute("DELETE FROM allocations")
        conn.commit()
    flash("All allocations cleared.", "warning")
    return redirect(url_for("admin.allocation"))
