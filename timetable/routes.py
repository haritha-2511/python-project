from flask import Blueprint, render_template
from .slots import DAYS, PERIODS, TIMINGS, BREAKS
from .data_loader import get_data
from .generator import generate, class_grid, teacher_grid, get_sections, get_faculty
from .saver import save_timetable

timetable_bp = Blueprint("timetable", __name__,
                         url_prefix="/timetable",
                         template_folder="templates")


# Read Member 2's data and make the schedule (done on every page load,
# so new faculty or allocations show up without restarting)
def make_schedule():
    data = get_data()
    schedule, unplaced = generate(data)
    return data, schedule, unplaced


# Home page: lists all classes and teachers
@timetable_bp.route("/")
def index():
    data, schedule, unplaced = make_schedule()
    return render_template("timetable_pages/index.html",
                           sections=get_sections(data),
                           faculty=get_faculty(data),
                           unplaced=unplaced)


# Timetable of one class, e.g. /timetable/class/IT-A
@timetable_bp.route("/class/<section>")
def show_class(section):
    data, schedule, unplaced = make_schedule()
    grid = class_grid(schedule, section)
    return render_template("timetable_pages/grid.html",
                           title="Class timetable: " + section,
                           days=DAYS, periods=PERIODS,
                           timings=TIMINGS, breaks=BREAKS, grid=grid)


# Timetable of one teacher, e.g. /timetable/teacher/Dr. Ravi
@timetable_bp.route("/teacher/<name>")
def show_teacher(name):
    data, schedule, unplaced = make_schedule()
    grid = teacher_grid(schedule, name)
    return render_template("timetable_pages/grid.html",
                           title="Teacher timetable: " + name,
                           days=DAYS, periods=PERIODS,
                           timings=TIMINGS, breaks=BREAKS, grid=grid)


# Saves the timetable into the database (Member 2's "timetable" table)
@timetable_bp.route("/save", methods=["POST"])
def save():
    data, schedule, unplaced = make_schedule()
    count = save_timetable(schedule)
    return ("Saved " + str(count) + " periods to the database. "
            "<a href='/timetable/'>Back</a>")