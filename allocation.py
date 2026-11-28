"""
Member 2 - Automatic faculty-subject allocation.

For every (section, subject) the system picks ONE faculty who
  1. is able to teach that subject, and
  2. still has room under their maximum periods per week.
Most-constrained subjects (fewest qualified faculty) are handled first, and the
least-loaded eligible faculty is chosen, so the workload stays balanced.
"""


def run_allocation(conn):
    """Rebuild the allocations table. Returns {'assigned': int, 'unallocated': [dict, ...]}."""
    conn.execute("DELETE FROM allocations")

    pairs = conn.execute("""
        SELECT ss.section_id, ss.subject_id, sec.name AS section_name,
               s.code, s.name AS subject_name, s.theory_periods + s.lab_periods AS periods
        FROM section_subjects ss
        JOIN sections sec ON sec.id = ss.section_id
        JOIN subjects s   ON s.id = ss.subject_id
    """).fetchall()

    qualified = {}
    for r in conn.execute("SELECT faculty_id, subject_id FROM faculty_subjects"):
        qualified.setdefault(r["subject_id"], []).append(r["faculty_id"])

    limits = {r["id"]: r["max_periods"] for r in conn.execute("SELECT id, max_periods FROM faculty")}
    load = {fid: 0 for fid in limits}

    pairs = sorted(pairs, key=lambda p: (len(qualified.get(p["subject_id"], [])), -p["periods"], p["section_id"]))

    assigned, unallocated = 0, []
    for p in pairs:
        candidates = qualified.get(p["subject_id"], [])
        options = [f for f in candidates if load[f] + p["periods"] <= limits[f]]
        if not options:
            reason = ("No faculty is able to teach this subject" if not candidates
                      else "All faculty who can teach it have reached their maximum periods")
            unallocated.append({"section": p["section_name"], "code": p["code"],
                                "subject": p["subject_name"], "reason": reason})
            continue
        chosen = min(options, key=lambda f: (load[f], f))
        load[chosen] += p["periods"]
        conn.execute("INSERT INTO allocations (section_id, subject_id, faculty_id) VALUES (?,?,?)",
                     (p["section_id"], p["subject_id"], chosen))
        assigned += 1

    return {"assigned": assigned, "unallocated": unallocated}
