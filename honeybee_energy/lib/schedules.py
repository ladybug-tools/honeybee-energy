"""Establish the default schedule types within the honeybee_energy library."""
from honeybee_energy.schedule.dictutil import dict_abridged_to_schedule
from ._loadschedules import _schedules, _schedule_standards_dict

import honeybee_energy.lib.scheduletypelimits as _stl


# establish variables for the default schedules used across the library
seated_activity = _schedules['Seated Adult Activity']
always_on = _schedules['Always On']
generic_office_occupancy = _schedules['Generic Office Occupancy']
generic_office_lighting = _schedules['Generic Office Lighting']
generic_office_equipment = _schedules['Generic Office Equipment']
generic_office_infiltration = _schedules['Generic Office Infiltration']
generic_office_heating = _schedules['Generic Office Heating']
generic_office_cooling = _schedules['Generic Office Cooling']


# make lists of schedules to look up items in the library
SCHEDULES = tuple(_schedules.keys()) + tuple(_schedule_standards_dict.keys())


def schedule_by_identifier(schedule_identifier):
    """Get a schedule from the library given its identifier.

    Args:
        schedule_identifier: A text string for the identifier of the schedule.
    """
    try:  # first check the default data
        return _schedules[schedule_identifier]
    except KeyError:
        try:  # search the extension data
            _sch_dict = _schedule_standards_dict[schedule_identifier]
            try:
                _tl = _stl.schedule_type_limit_by_identifier(
                    _sch_dict['schedule_type_limit'])
            except KeyError:
                _tl = _stl.fractional
            return dict_abridged_to_schedule(_sch_dict, {_tl.identifier: _tl})
        except KeyError:  # schedule is nowhere to be found; raise an error
            raise ValueError('"{}" was not found in the schedule library.'.format(
                schedule_identifier))


def lib_dict_abridged_to_schedule(sch_dict, schedule_type_limits):
    """Get a Python object of any Schedule from an abridged dictionary.

    Args:
        sch_dict: A dictionary of any Honeybee energy schedules. Note
            that this should be a non-abridged dictionary to be valid.
        schedule_type_limits: Dictionary of all schedule type limit objects that
            might be used in the schedule with the type limit identifiers as the keys.

    Returns:
        A Python object derived from the input sch_dict.
    """
    if 'schedule_type_limit' in sch_dict and sch_dict['schedule_type_limit'] is not None:
        if sch_dict['schedule_type_limit'] not in schedule_type_limits:
            schedule_type_limits[sch_dict['schedule_type_limit']] = \
                _stl.schedule_type_limit_by_identifier(sch_dict['schedule_type_limit'])
    return dict_abridged_to_schedule(sch_dict, schedule_type_limits)
