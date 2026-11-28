# Days of the week (same names as Member 2's seed_data.py)
DAYS = ["Monday", "Tuesday", "Wednesday", "Thursday", "Friday"]

# Period numbers of a full day
PERIODS = [1, 2, 3, 4, 5, 6, 7]

# Which periods each day has.
# Monday and Wednesday: college ends at 1:40 (after period 5).
DAY_PERIODS = {
    "Monday":    [1, 2, 3, 4, 5],
    "Tuesday":   [1, 2, 3, 4, 5, 6, 7],
    "Wednesday": [1, 2, 3, 4, 5],
    "Thursday":  [1, 2, 3, 4, 5, 6, 7],
    "Friday":    [1, 2, 3, 4, 5, 6, 7],
}

# Time of each period
TIMINGS = {
    1: "08:10 - 09:00",
    2: "09:00 - 09:50",
    3: "10:10 - 11:00",
    4: "11:00 - 11:50",
    5: "12:50 - 01:40",
    6: "01:40 - 02:30",
    7: "02:40 - 03:30",
}

# Breaks: the number is the period AFTER which the break comes
BREAKS = {
    2: "Break (09:50 - 10:10)",
    4: "Lunch (11:50 - 12:50)",
    6: "Short Break (02:30 - 02:40)",
}

# A lab class is 2 periods in a row. These pairs do not cross a break.
# (5, 6) is only possible on days that have a 6th period.
LAB_PAIRS = [(1, 2), (3, 4), (5, 6)]


# Makes an empty timetable.
# Only the periods that exist on a day are added
# (so Monday and Wednesday have no 6th and 7th period).
def build_empty_grid():
    grid = {}
    for day in DAYS:
        grid[day] = {}
        for period in DAY_PERIODS[day]:
            grid[day][period] = ""
    return grid