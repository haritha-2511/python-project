# Saves the finished schedule into Member 2's "timetable" table,
# so Member 4 (faculty/student features) can read it later.

from contextlib import closing
from db import get_db


def save_timetable(schedule):
    with closing(get_db()) as conn:
        # room name -> room id
        room_ids = {}
        for r in conn.execute("SELECT id, name FROM rooms"):
            room_ids[r["name"]] = r["id"]

        conn.execute("DELETE FROM timetable")      # remove the old timetable
        for c in schedule:
            conn.execute(
                "INSERT INTO timetable (day, slot, subject_id, faculty_id, room_id, section_id) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (c["day"], c["period"], c["subject_id"], c["faculty_id"],
                 room_ids[c["room"]], c["section_id"]))
        conn.commit()
    return len(schedule)