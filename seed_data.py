"""
Member 2 - FIXED DATA for the college.
Edit this file only if the fixed data (timings, rooms, subjects per section) changes.
Subject codes are placeholders.
"""

DEPARTMENTS = ["CSE", "IT", "ECE", "EEE", "Mechanical", "Science & Humanities"]

WORKING_DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# (label, start, end, is_break)
PERIOD_GRID = [
    ("Period 1", "8:10 AM", "9:00 AM", False),
    ("Period 2", "9:00 AM", "9:50 AM", False),
    ("Break", "9:50 AM", "10:10 AM", True),
    ("Period 3", "10:10 AM", "11:00 AM", False),
    ("Period 4", "11:00 AM", "11:50 AM", False),
    ("Lunch", "11:50 AM", "12:50 PM", True),
    ("Period 5", "12:50 PM", "1:40 PM", False),
    ("Period 6", "1:40 PM", "2:30 PM", False),
    ("Break", "2:30 PM", "2:40 PM", True),
    ("Period 7", "2:40 PM", "3:30 PM", False),
]

# Which kind of lab a subject's lab periods need
LAB_TYPES = {
    "NONE": "No lab (theory only)",
    "PHYSICS": "Physics lab",
    "CHEMISTRY": "Chemistry lab",
    "COMPUTER": "Computer lab",
    "MAKERS": "Makers space lab",
    "ELECTRONICS": "Electronics & digital lab",
    "CLASSROOM": "Held in the section's classroom",
}

# (name, type, lab_uses)
ROOMS = [(str(n), "Classroom", "") for n in (101, 102, 103, 104, 105, 201, 202, 203, 204, 205)] + [
    ("Physics Lab", "Lab", "PHYSICS"),
    ("Physics & Chemistry Lab", "Lab", "PHYSICS,CHEMISTRY"),
    ("Computer Lab", "Lab", "COMPUTER"),
    ("Makers Space Lab", "Lab", "MAKERS"),
    ("Electronics & Digital Lab", "Lab", "ELECTRONICS"),
]

# (section name, department, home classroom)
SECTIONS = [
    ("CSE-A", "CSE", "101"), ("CSE-B", "CSE", "102"),
    ("IT-A", "IT", "103"), ("IT-B", "IT", "104"),
    ("ECE-A", "ECE", "105"), ("ECE-B", "ECE", "201"),
    ("EEE-A", "EEE", "202"), ("EEE-B", "EEE", "203"),
    ("Mechanical-A", "Mechanical", "204"), ("Mechanical-B", "Mechanical", "205"),
]

SH = "Science & Humanities"

# (code, name, department, theory periods [L+T], lab periods [P], lab type)
SUBJECTS = [
    ("MA101", "Matrices and Calculus", SH, 4, 0, "NONE"),
    ("MA102", "Mathematics I", SH, 4, 0, "NONE"),
    ("PH101", "Engineering Physics", SH, 3, 0, "NONE"),
    ("PH102", "Engineering Physics Laboratory", SH, 0, 4, "PHYSICS"),
    ("CY101", "Engineering Chemistry", SH, 2, 2, "CHEMISTRY"),
    ("HS101", "Communicative English", SH, 2, 2, "CLASSROOM"),
    ("HS102", "Communicative English (Theory)", SH, 3, 0, "NONE"),
    ("HS103", "Professional Ethics and Human Values", SH, 2, 0, "NONE"),
    ("ME101", "Engineering Graphics", "Mechanical", 2, 2, "CLASSROOM"),
    ("ME102", "Engineering Mechanics", "Mechanical", 3, 0, "NONE"),
    ("ME103", "Makers Space Laboratory", "Mechanical", 0, 4, "MAKERS"),
    ("EE101", "Circuit Theory", "EEE", 3, 0, "NONE"),
    ("EE102", "Electromagnetic Theory", "EEE", 3, 0, "NONE"),
    ("EE103", "Basic Electrical Technology", "EEE", 2, 0, "NONE"),
    ("EC101", "Electron Devices and Circuits", "ECE", 3, 0, "NONE"),
    ("EC102", "Circuit Analysis", "ECE", 3, 0, "NONE"),
    ("EC103", "Electronics Engineering Practice", "ECE", 0, 4, "ELECTRONICS"),
    ("EC104", "Digital Design + Lab", "ECE", 2, 2, "ELECTRONICS"),
    ("CS101", "Programming in Python for Data Science", "CSE", 1, 2, "COMPUTER"),
    ("CS102", "Problem Solving and Programming in C", "CSE", 2, 4, "COMPUTER"),
    ("IT101", "Computational Thinking and Problem Solving with Python", "IT", 2, 2, "COMPUTER"),
    ("IT102", "Introduction to Web Programming", "IT", 2, 2, "COMPUTER"),
    ("IT103", "Open-Source Tools and Prompt Engineering", "IT", 0, 4, "COMPUTER"),
]

# Subject codes studied by BOTH sections (A and B) of each department
DEPT_SUBJECTS = {
    "CSE": ["HS102", "MA102", "PH101", "PH102", "CS102", "EE103", "EC104"],
    "IT": ["MA102", "PH101", "HS101", "IT101", "IT102", "HS103", "PH102", "IT103"],
    "ECE": ["MA101", "PH101", "HS101", "EC101", "EC102", "HS103", "EC103", "PH102"],
    "EEE": ["MA101", "PH101", "HS101", "EE101", "EE102", "HS103", "PH102", "ME103"],
    "Mechanical": ["MA101", "CY101", "HS101", "ME101", "ME102", "HS103", "CS101", "ME103"],
}


def seed_fixed_data(conn):
    """Insert the fixed data once (does nothing if sections already exist)."""
    if conn.execute("SELECT COUNT(*) FROM sections").fetchone()[0]:
        return

    for name, rtype, uses in ROOMS:
        conn.execute("INSERT OR IGNORE INTO rooms (name, room_type, lab_uses) VALUES (?,?,?)",
                     (name, rtype, uses))
    for row in SUBJECTS:
        conn.execute("""INSERT OR IGNORE INTO subjects
                        (code, name, department, theory_periods, lab_periods, lab_type)
                        VALUES (?,?,?,?,?,?)""", row)

    room_id = {r["name"]: r["id"] for r in conn.execute("SELECT id, name FROM rooms")}
    subject_id = {r["code"]: r["id"] for r in conn.execute("SELECT id, code FROM subjects")}

    for name, dept, room in SECTIONS:
        cur = conn.execute("INSERT INTO sections (name, department, year, home_room_id) VALUES (?,?,1,?)",
                           (name, dept, room_id[room]))
        for code in DEPT_SUBJECTS[dept]:
            conn.execute("INSERT INTO section_subjects (section_id, subject_id) VALUES (?,?)",
                         (cur.lastrowid, subject_id[code]))
