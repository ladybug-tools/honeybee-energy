"""Establish the default schedule types within the honeybee_energy library."""
from honeybee_energy.schedule.ruleset import ScheduleRuleset

from ._loadschedules import _idf_schedules
from .scheduletypelimits import activity_level


# establish variables for the default schedules used across the library
# and auto-generate materials if they were not loaded from default.idf
try:
    seated_activity = _idf_schedules['Seated Adult Activity']
except KeyError:
    seated_activity = ScheduleRuleset.from_constant_value(
        'Seated Adult Activity', 120, activity_level)
    seated_activity.lock()
    _idf_schedules['Seated Adult Activity'] = seated_activity


# make lists of schedule types to look up items in the library
SCHEDULES = tuple(_idf_schedules.keys())


# methods to look up schedule types from the library


def schedule_by_name(schedule_name):
    """Get a schedule from the library given its name.

    Args:
        schedule_name: A text string for the name of the schedule.
    """
    try:
        return _idf_schedules[schedule_name]
    except KeyError:
        raise ValueError('"{}" was not found in the schedule library.'.format(
            schedule_name))
