# coding=utf-8
"""Utilities to convert schedule dictionaries to Python objects."""
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval


SCHEDULE_TYPES = ('ScheduleRuleset', 'ScheduleFixedInterval')


def dict_to_schedule(sch_dict, raise_exception=True):
    """Get a Python object of any Schedule from a dictionary.

    Args:
        sch_dict: A dictionary of any Honeybee energy schedules. Note
            that this should be a non-abridged dictionary to be valid.
        raise_exception: Boolean to note whether an exception should be raised
            if the object is not identified as a schedule. Default: True.

    Returns:
        A Python object derived from the input sch_dict.
    """
    try:  # get the type key from the dictionary
        sch_type = sch_dict['type']
    except KeyError:
        raise ValueError('Schedule dictionary lacks required "type" key.')

    if sch_type == 'ScheduleRuleset':
        return ScheduleRuleset.from_dict(sch_dict)
    elif sch_type == 'ScheduleFixedInterval':
        return ScheduleFixedInterval.from_dict(sch_dict)
    elif raise_exception:
        raise ValueError('{} is not a recognized energy Schedule type'.format(sch_type))


def dict_abridged_to_schedule(sch_dict, schedule_type_limits, raise_exception=True):
    """Get a Python object of any Schedule from an abridged dictionary.

    Args:
        sch_dict: A dictionary of any Honeybee energy schedules. Note
            that this should be a non-abridged dictionary to be valid.
        schedule_type_limits: Dictionary of all schedule type limit objects that
            might be used in the schedule with the type limit identifiers as the keys.
        raise_exception: Boolean to note whether an exception should be raised
            if the object is not identified as a schedule. Default: True.

    Returns:
        A Python object derived from the input sch_dict.
    """
    try:  # get the type key from the dictionary
        sch_type = sch_dict['type']
    except KeyError:
        raise ValueError('Schedule dictionary lacks required "type" key.')

    if sch_type == 'ScheduleRulesetAbridged':
        return ScheduleRuleset.from_dict_abridged(sch_dict, schedule_type_limits)
    elif sch_type == 'ScheduleFixedIntervalAbridged':
        return ScheduleFixedInterval.from_dict_abridged(sch_dict, schedule_type_limits)
    elif raise_exception:
        raise ValueError('{} is not a recognized energy Schedule type'.format(sch_type))
