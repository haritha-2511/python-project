# THIS IS THE ONLY FILE THAT READS MEMBER 2's DATABASE.
# It uses her get_db() from db.py and her tables:
#   allocations (which faculty teaches which subject to which section),
#   sections, subjects, faculty, rooms.
#
# It returns a list of "items". One item = one kind of class for one section:
#   {"section_id": 1, "section": "IT-A",
#    "subject_id": 5, "subject": "Engineering Physics",
#    "faculty_id": 3, "faculty": "Dr. Ravi",
#    "rooms": ["103"],          # rooms we are allowed to use
#    "room_type": "Theory",     # "Theory" or "Lab"
#    "periods": 3}              # periods needed per week

from contextlib import closing
from db import get_db


def get_data():
    items = []

    with closing(get_db()) as conn:

        # Step 1: which lab rooms can be used for which lab type
        # e.g. {"COMPUTER": ["Computer Lab"], "PHYSICS": ["Physics Lab", ...]}
        lab_rooms = {}
        for r in conn.execute("SELECT name, lab_uses FROM rooms WHERE room_type = 'Lab'"):
            for lab_type in r["lab_uses"].split(","):
                lab_rooms.setdefault(lab_type.strip(), []).append(r["name"])

        # Step 2: every (section, subject, faculty) that Member 2 allocated
        rows = conn.execute("""
            SELECT sec.id AS section_id, sec.name AS section,
                   s.id AS subject_id, s.name AS subject,
                   s.theory_periods, s.lab_periods, s.lab_type,
                   f.id AS faculty_id, f.name AS faculty,
                   home.name AS home_room
            FROM allocations a
            JOIN sections sec ON sec.id = a.section_id
            JOIN subjects s   ON s.id = a.subject_id
            JOIN faculty f    ON f.id = a.faculty_id
            LEFT JOIN rooms home ON home.id = sec.home_room_id
            ORDER BY sec.id, s.code
        """).fetchall()

    # Step 3: make one item for the theory periods and one for the lab periods
    for r in rows:
        base = {
            "section_id": r["section_id"], "section": r["section"],
            "subject_id": r["subject_id"], "subject": r["subject"],
            "faculty_id": r["faculty_id"], "faculty": r["faculty"],
        }

        if r["theory_periods"] > 0:
            item = dict(base)
            item["rooms"] = [r["home_room"]]          # the section's own classroom
            item["room_type"] = "Theory"
            item["periods"] = r["theory_periods"]
            items.append(item)

        if r["lab_periods"] > 0:
            item = dict(base)
            if r["lab_type"] == "CLASSROOM":
                item["rooms"] = [r["home_room"]]      # lab held in the classroom
            else:
                item["rooms"] = lab_rooms.get(r["lab_type"], [])
            item["room_type"] = "Lab"
            item["periods"] = r["lab_periods"]
            items.append(item)

    return items