"""Unit tests for the Member 4 workload calculations.

These tests use an in-memory SQLite database.  They do not open or change
the project's timetable.db file.
"""
import sqlite3
import unittest

from routes.workload import get_workload_summary, slot_duration_minutes


class WorkloadTests(unittest.TestCase):
    def setUp(self):
        self.conn = sqlite3.connect(":memory:")
        self.conn.row_factory = sqlite3.Row
        self.conn.executescript("""
            CREATE TABLE faculty (
                id INTEGER PRIMARY KEY,
                faculty_code TEXT,
                name TEXT NOT NULL,
                department TEXT NOT NULL,
                max_periods INTEGER NOT NULL
            );
            CREATE TABLE timetable (
                id INTEGER PRIMARY KEY,
                day TEXT NOT NULL,
                slot INTEGER NOT NULL,
                subject_id INTEGER,
                faculty_id INTEGER,
                room_id INTEGER,
                section_id INTEGER
            );
        """)
        self.conn.executemany("""
            INSERT INTO faculty (id, faculty_code, name, department, max_periods)
            VALUES (?, ?, ?, ?, ?)
        """, [
            (1, "F001", "Asha", "CSE", 2),
            (2, "F002", "Bala", "ECE", 16),
            (3, "F003", "Chitra", "IT", 1),
        ])
        self.conn.executemany("""
            INSERT INTO timetable (id, day, slot, subject_id, faculty_id, room_id, section_id)
            VALUES (?, ?, ?, ?, ?, ?, ?)
        """, [
            (1, "Monday", 1, 1, 1, 1, 1),
            (2, "Tuesday", 5, 1, 1, 1, 1),
            (3, "Thursday", 6, 2, 3, 2, 2),
            (4, "Friday", 7, 2, 3, 2, 2),
            # Library periods deliberately have no faculty and must not count.
            (5, "Friday", 5, None, None, 1, 1),
        ])

    def tearDown(self):
        self.conn.close()

    def summary_by_name(self):
        return {item["name"]: item for item in get_workload_summary(self.conn)}

    def test_existing_slot_timings_are_fifty_minutes(self):
        self.assertEqual(slot_duration_minutes(1), 50)
        self.assertEqual(slot_duration_minutes(5), 50)
        self.assertEqual(slot_duration_minutes(7), 50)

    def test_calculates_periods_minutes_and_hours(self):
        asha = self.summary_by_name()["Asha"]
        self.assertEqual(asha["periods"], 2)
        self.assertEqual(asha["minutes"], 100)
        self.assertAlmostEqual(asha["hours"], 100 / 60)

    def test_includes_faculty_with_zero_scheduled_classes(self):
        bala = self.summary_by_name()["Bala"]
        self.assertEqual(bala["periods"], 0)
        self.assertEqual(bala["minutes"], 0)
        self.assertEqual(bala["hours"], 0)
        self.assertEqual(bala["status"], "No scheduled classes")

    def test_library_entry_with_null_faculty_is_not_counted(self):
        summary = self.summary_by_name()
        self.assertEqual(summary["Asha"]["periods"], 2)
        self.assertEqual(summary["Chitra"]["periods"], 2)

    def test_compares_periods_with_existing_maximum(self):
        summary = self.summary_by_name()
        self.assertEqual(summary["Asha"]["status"], "At limit")
        self.assertEqual(summary["Chitra"]["status"], "Over limit")


if __name__ == "__main__":
    unittest.main()
