"""
Shared SQLite helper.
Changing tables here affects everyone -> do it through a Pull Request that all members review.
"""
import sqlite3
from pathlib import Path

DB_PATH = Path(__file__).parent / "timetable.db"

SCHEMA = """
CREATE TABLE IF NOT EXISTS faculty (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    faculty_code  TEXT UNIQUE,
    name          TEXT NOT NULL,
    department    TEXT NOT NULL,
    max_periods   INTEGER NOT NULL DEFAULT 16
);

CREATE TABLE IF NOT EXISTS subjects (
    id              INTEGER PRIMARY KEY AUTOINCREMENT,
    code            TEXT NOT NULL UNIQUE,
    name            TEXT NOT NULL,
    department      TEXT NOT NULL,
    theory_periods  INTEGER NOT NULL DEFAULT 0,   -- L (+ T) periods per week
    lab_periods     INTEGER NOT NULL DEFAULT 0,   -- P periods per week
    lab_type        TEXT NOT NULL DEFAULT 'NONE'  -- which kind of lab is needed
);

CREATE TABLE IF NOT EXISTS rooms (
    id         INTEGER PRIMARY KEY AUTOINCREMENT,
    name       TEXT NOT NULL UNIQUE,
    room_type  TEXT NOT NULL CHECK (room_type IN ('Classroom', 'Lab')),
    lab_uses   TEXT NOT NULL DEFAULT ''           -- e.g. 'PHYSICS,CHEMISTRY'
);

CREATE TABLE IF NOT EXISTS sections (
    id            INTEGER PRIMARY KEY AUTOINCREMENT,
    name          TEXT NOT NULL UNIQUE,           -- e.g. 'CSE-A'
    department    TEXT NOT NULL,
    year          INTEGER NOT NULL DEFAULT 1,
    home_room_id  INTEGER REFERENCES rooms(id)
);

-- which subjects each section studies (fixed)
CREATE TABLE IF NOT EXISTS section_subjects (
    section_id  INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id),
    PRIMARY KEY (section_id, subject_id)
);

-- which subjects a faculty member is able to teach (entered by admin)
CREATE TABLE IF NOT EXISTS faculty_subjects (
    faculty_id  INTEGER NOT NULL REFERENCES faculty(id)  ON DELETE CASCADE,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    PRIMARY KEY (faculty_id, subject_id)
);

-- automatic faculty-subject allocation result (one faculty per section + subject)
CREATE TABLE IF NOT EXISTS allocations (
    section_id  INTEGER NOT NULL REFERENCES sections(id) ON DELETE CASCADE,
    subject_id  INTEGER NOT NULL REFERENCES subjects(id) ON DELETE CASCADE,
    faculty_id  INTEGER NOT NULL REFERENCES faculty(id)  ON DELETE CASCADE,
    PRIMARY KEY (section_id, subject_id)
);

-- filled by the timetable module (Member 3)
CREATE TABLE IF NOT EXISTS timetable (
    id          INTEGER PRIMARY KEY AUTOINCREMENT,
    day         TEXT NOT NULL,
    slot        INTEGER NOT NULL,                 -- 1..7
    subject_id  INTEGER,
    faculty_id  INTEGER,
    room_id     INTEGER,
    section_id  INTEGER
);
"""


def get_db():
    conn = sqlite3.connect(DB_PATH)
    conn.row_factory = sqlite3.Row
    conn.execute("PRAGMA foreign_keys = ON")
    return conn


def init_db():
    from seed_data import seed_fixed_data  # fixed college data (owned by Member 2)

    with get_db() as conn:
        conn.executescript(SCHEMA)
        seed_fixed_data(conn)
