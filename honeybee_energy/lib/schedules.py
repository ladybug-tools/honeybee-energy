"""Establish the default schedule types within the honeybee_energy library."""
from honeybee_energy.schedule.ruleset import ScheduleRuleset

from ._loadschedules import _schedules
from .scheduletypelimits import activity_level, fractional


# establish variables for the default schedules used across the library
# and auto-generate schedules if they were not loaded from default.idf
try:
    seated_activity = _schedules['Seated Adult Activity']
except KeyError:
    seated_activity = ScheduleRuleset.from_constant_value(
        'Seated Adult Activity', 120, activity_level)
    seated_activity.lock()
    _schedules['Seated Adult Activity'] = seated_activity

try:
    always_on = _schedules['Always On']
except KeyError:
    always_on = ScheduleRuleset.from_constant_value('Always On', 1, fractional)
    always_on.lock()
    _schedules['Always On'] = always_on

try:
    generic_office_occupancy = _schedules['Generic Office Occupancy']
    generic_office_activity = _schedules['Generic Office Activity']
    generic_office_lighting = _schedules['Generic Office Lighting']
    generic_office_equipment = _schedules['Generic Office Equipment']
    generic_office_infiltration = _schedules['Generic Office Infiltration']
    generic_office_heating = _schedules['Generic Office Heating']
    generic_office_cooling = _schedules['Generic Office Cooling']
except KeyError:  # the office program isn't critical for the rest of the library
    generic_office_occupancy = None
    generic_office_activity = None
    generic_office_lighting = None
    generic_office_equipment = None
    generic_office_infiltration = None
    generic_office_heating = None
    generic_office_cooling = None


# make lists of schedules to look up items in the library
SCHEDULES = tuple(_schedules.keys())


def schedule_by_name(schedule_name):
    """Get a schedule from the library given its name.

    Args:
        schedule_name: A text string for the name of the schedule.
    """
    try:
        return _schedules[schedule_name]
    except KeyError:
        raise ValueError('"{}" was not found in the schedule library.'.format(
            schedule_name))
