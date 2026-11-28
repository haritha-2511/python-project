# "schedule" is a list of classes already placed.
# Each class is a dictionary like this:
# {"section": "IT-A", "day": "Monday", "period": 1, "subject": "Maths",
#  "faculty": "Dr. Ravi", "room": "103", "room_type": "Theory", ...}


# Is this faculty already teaching at this time?
def faculty_busy(schedule, day, period, faculty):
    for c in schedule:
        if c["day"] == day and c["period"] == period and c["faculty"] == faculty:
            return True
    return False


# Is this room already used at this time?
def room_busy(schedule, day, period, room):
    for c in schedule:
        if c["day"] == day and c["period"] == period and c["room"] == room:
            return True
    return False


# Does this section already have a class at this time?
def section_busy(schedule, day, period, section):
    for c in schedule:
        if c["day"] == day and c["period"] == period and c["section"] == section:
            return True
    return False


# Final check: True only if there is no clash of any kind
def can_place(schedule, section, day, period, faculty, room):
    if faculty_busy(schedule, day, period, faculty):
        return False
    if room_busy(schedule, day, period, room):
        return False
    if section_busy(schedule, day, period, section):
        return False
    return True


# Working limit: has this faculty still got room for one more period this week?
# "limit" is the max_periods that Member 2 stored for the faculty.
def has_capacity(schedule, faculty, limit):
    count = 0
    for c in schedule:
        if c["faculty"] == faculty:
            count = count + 1
    return count < limit