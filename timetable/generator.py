from .slots import DAYS, PERIODS, LAB_PAIRS, build_empty_grid
from .clash import can_place


# Try to place ONE block (1 period, or 2 periods in a row for labs).
# Returns True if it was placed.
def place_block(schedule, item, size, used_days):
    if size == 2:
        choices = LAB_PAIRS                       # (1,2) (3,4) (5,6)
    else:
        choices = [(p,) for p in PERIODS]         # (1,) (2,) ... (7,)

    for day in DAYS:
        if day in used_days:                      # not twice a day for the same subject
            continue
        for periods in choices:
            for room in item["rooms"]:
                # every period of the block must be free of clashes
                free = True
                for p in periods:
                    if not can_place(schedule, item["section"], day, p,
                                     item["faculty"], room):
                        free = False
                if free:
                    for p in periods:
                        schedule.append({
                            "section_id": item["section_id"], "section": item["section"],
                            "subject_id": item["subject_id"], "subject": item["subject"],
                            "faculty_id": item["faculty_id"], "faculty": item["faculty"],
                            "room": room, "room_type": item["room_type"],
                            "day": day, "period": p,
                        })
                    used_days.append(day)
                    return True
    return False


# Step 1: Make the full schedule (one list that holds EVERY class)
# Returns the schedule and a list of classes that could not be placed.
def generate(data):
    schedule = []
    unplaced = []

    # labs first, because lab rooms are the hardest to find free
    data = sorted(data, key=lambda item: item["room_type"] != "Lab")

    for item in data:
        # split the periods into blocks: labs in 2s, theory in 1s
        blocks = []
        left = item["periods"]
        while left > 0:
            if item["room_type"] == "Lab" and left >= 2:
                blocks.append(2)
                left = left - 2
            else:
                blocks.append(1)
                left = left - 1

        used_days = []
        for size in blocks:
            placed = place_block(schedule, item, size, used_days)
            if not placed:
                # second try: allow the same subject twice on one day
                placed = place_block(schedule, item, size, [])
            if not placed:
                unplaced.append(item["section"] + " - " + item["subject"] +
                                " (" + item["room_type"] + ")")
    return schedule, unplaced


# Shows a room nicely: "Room 103 (Theory)" or "Computer Lab (Lab)"
def room_text(c):
    if c["room"].isdigit():
        name = "Room " + c["room"]
    else:
        name = c["room"]
    return name + " (" + c["room_type"] + ")"


# Step 2: Timetable of ONE class
# Each block shows: subject, teacher name, room (Lab/Theory)
def class_grid(schedule, section):
    grid = build_empty_grid()
    for c in schedule:
        if c["section"] == section:
            grid[c["day"]][c["period"]] = (
                c["subject"] + "\n" + c["faculty"] + "\n" + room_text(c))
    return grid


# Step 3: Timetable of ONE teacher
# Each block shows: class name, room (Lab/Theory)
def teacher_grid(schedule, faculty):
    grid = build_empty_grid()
    for c in schedule:
        if c["faculty"] == faculty:
            grid[c["day"]][c["period"]] = c["section"] + "\n" + room_text(c)
    return grid


# Lists of names for the home page
def get_sections(data):
    names = []
    for item in data:
        if item["section"] not in names:
            names.append(item["section"])
    return names


def get_faculty(data):
    names = []
    for item in data:
        if item["faculty"] not in names:
            names.append(item["faculty"])
    return sorted(names)