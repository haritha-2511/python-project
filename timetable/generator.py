import random
from .slots import DAYS, DAY_PERIODS, LAB_PAIRS, PERIODS, build_empty_grid
from .clash import can_place, section_busy, has_capacity


# Adds one period of a subject to the schedule
def add_class(schedule, item, room, day, period):
    schedule.append({
        "section_id": item["section_id"], "section": item["section"],
        "subject_id": item["subject_id"], "subject": item["subject"],
        "faculty_id": item["faculty_id"], "faculty": item["faculty"],
        "room": room, "room_type": item["room_type"],
        "day": day, "period": period,
    })


# Try to place ONE block (1 period for theory, 2 periods in a row for a lab).
# Returns True if it was placed.
def place_block(schedule, item, size, used_days):
    for day in DAYS:
        if day in used_days:                      # not twice a day for the same subject
            continue

        if size == 2:
            # lab pairs, only if both periods exist on this day
            choices = [pair for pair in LAB_PAIRS if pair[1] in DAY_PERIODS[day]]
        else:
            choices = [(p,) for p in DAY_PERIODS[day]]

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
                        add_class(schedule, item, room, day, p)
                    used_days.append(day)
                    return True
    return False


# Place all periods of one item. Returns how many blocks could not be placed.
def place_item(schedule, item):
    # a lab is placed in blocks of 2 periods, theory one period at a time
    if item["room_type"] == "Lab":
        blocks = [2] * (item["periods"] // 2)
        if item["periods"] % 2 == 1:
            blocks.append(1)
    else:
        blocks = [1] * item["periods"]

    used_days = []
    failed = 0
    for size in blocks:
        placed = place_block(schedule, item, size, used_days)
        if not placed:
            # second try: allow the same subject twice on one day
            placed = place_block(schedule, item, size, [])
        if not placed:
            failed = failed + 1
    return failed


# Exactly ONE library period per class per week.
# We use the last free period of the week.
def add_library(schedule, section):
    for period in reversed(PERIODS):
        for day in reversed(DAYS):
            if period in DAY_PERIODS[day] and not section_busy(schedule, day, period, section):
                schedule.append({
                    "section_id": None, "section": section,
                    "subject_id": None, "subject": "Library",
                    "faculty_id": None, "faculty": "",
                    "room": "Library", "room_type": "",
                    "day": day, "period": period,
                })
                return


def count_periods(schedule, section, subject):
    n = 0
    for c in schedule:
        if c["section"] == section and c["subject"] == subject:
            n = n + 1
    return n


def subject_on_day(schedule, section, subject, day):
    for c in schedule:
        if c["section"] == section and c["subject"] == subject and c["day"] == day:
            return True
    return False


# Fill every free cell of a section with an extra period of one of its own
# theory subjects. A teacher is used only if he/she is free AND still under
# the weekly limit. Returns the cells that are still empty.
def fill_empty_cells(schedule, section, theory_items):
    empty = []
    for day in DAYS:
        for period in DAY_PERIODS[day]:
            if not section_busy(schedule, day, period, section):
                empty.append((day, period))

    # first pass: not the same subject twice in a day; second pass: allow it
    for avoid_same_day in (True, False):
        for day, period in list(empty):
            # subjects with the fewest periods so far come first
            order = sorted(theory_items,
                           key=lambda it: count_periods(schedule, section, it["subject"]))
            for item in order:
                if avoid_same_day and subject_on_day(schedule, section, item["subject"], day):
                    continue
                if not has_capacity(schedule, item["faculty"], item["faculty_limit"]):
                    continue                          # teacher is at the weekly limit
                room = item["rooms"][0]
                if can_place(schedule, section, day, period, item["faculty"], room):
                    add_class(schedule, item, room, day, period)
                    empty.remove((day, period))
                    break
    return empty


# Makes the schedule once, placing the items in the given order.
# Returns the schedule and a list of problems (not placed / still empty).
def generate_once(data, labs, theory):
    schedule = []
    problems = []

    # labs first (lab rooms are the hardest to find free), then theory
    for item in labs + theory:
        failed = place_item(schedule, item)
        if failed > 0:
            problems.append(item["section"] + " - " + item["subject"] +
                            " (" + item["room_type"] + ") could not be placed")

    # then, for every class: one library period, then fill all free cells
    for section in get_sections(data):
        add_library(schedule, section)
        mine = [i for i in theory if i["section"] == section]
        left = fill_empty_cells(schedule, section, mine)
        for day, period in left:
            problems.append(section + " - " + day + " P" + str(period) +
                            " is empty (teachers are busy or at their weekly limit)")

    return schedule, problems


# Step 1: Make the full schedule (one list that holds EVERY class).
# If the first try leaves a problem, we try again with the classes placed
# in a different order (up to 40 tries) and keep the best result.
def generate(data):
    labs = [i for i in data if i["room_type"] == "Lab"]
    theory = [i for i in data if i["room_type"] == "Theory"]

    best_schedule, best_problems = generate_once(data, labs, theory)

    attempt = 1
    while best_problems and attempt <= 40:
        rng = random.Random(attempt)          # same tries every time = same result
        labs_try = list(labs)
        theory_try = list(theory)
        rng.shuffle(labs_try)
        rng.shuffle(theory_try)
        schedule, problems = generate_once(data, labs_try, theory_try)
        if len(problems) < len(best_problems):
            best_schedule, best_problems = schedule, problems
        attempt = attempt + 1

    return best_schedule, best_problems


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
            if c["subject"] == "Library":
                grid[c["day"]][c["period"]] = "Library"
            else:
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