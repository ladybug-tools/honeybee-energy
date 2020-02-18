"""Establish the default schedule types within the honeybee_energy library."""
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.dictutil import dict_abridged_to_schedule
from ._loadschedules import _schedules, _schedule_standards_dict

import honeybee_energy.lib.scheduletypelimits as _stl


# establish variables for the default schedules used across the library
# and auto-generate schedules if they were not loaded from default.idf
try:
    seated_activity = _schedules['Seated Adult Activity']
except KeyError:
    seated_activity = ScheduleRuleset.from_constant_value(
        'Seated Adult Activity', 120, _stl.activity_level)
    seated_activity.lock()
    _schedules['Seated Adult Activity'] = seated_activity

try:
    always_on = _schedules['Always On']
except KeyError:
    always_on = ScheduleRuleset.from_constant_value('Always On', 1, _stl.fractional)
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
SCHEDULES = tuple(_schedules.keys()) + tuple(_schedule_standards_dict.keys())


def schedule_by_name(schedule_name):
    """Get a schedule from the library given its name.

    Args:
        schedule_name: A text string for the name of the schedule.
    """
    try:  # first check the default data
        return _schedules[schedule_name]
    except KeyError:
        try:  # search the extension data
            _sch_dict = _schedule_standards_dict[schedule_name]
            try:
                _tl = _stl.schedule_type_limit_by_name(_sch_dict['schedule_type_limit'])
            except KeyError:
                _tl = _stl.fractional
            return dict_abridged_to_schedule(_sch_dict, {_tl.name: _tl})
        except KeyError:  # schedule is nowhere to be found; raise an error
            raise ValueError('"{}" was not found in the schedule library.'.format(
                schedule_name))
