# coding=utf-8
"""Base object for all load definitions."""
from __future__ import division

from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class _LoadBase(object):
    """A base object for all load definitions.

    Properties:
        * name
    """
    __slots__ = ('_name', '_locked')

    def __init__(self, name):
        """Initialize LoadBase.

        Args:
            name: Text string for the load definition name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
        """
        self._locked = False  # unlocked by default
        self.name = name

    @property
    def name(self):
        """Get or set the text string for object name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _check_fractional_schedule_type(self, schedule, obj_name=''):
        """Check that the type limit of an input schedule is fractional."""
        if schedule.schedule_type_limit is not None:
            assert schedule.schedule_type_limit.unit == 'fraction', '{} schedule ' \
                'should be fractional [Dimensionless]. Got a schedule of unit_type ' \
                '[{}].'.format(obj_name, schedule.schedule_type_limit.unit_type)

    @staticmethod
    def _average_schedule(name, scheds, weights, timestep):
        """Average a set of schedules together (no matter their type)."""
        try:
            return ScheduleRuleset.average_schedules(name, scheds, weights, timestep)
        except AttributeError:
            return ScheduleFixedInterval.average_schedules(name, scheds, weights)

    @staticmethod
    def _get_schedule_from_dict(sch_dict):
        """Get a schedule object from a schedule dictionary."""
        if sch_dict['type'] == 'ScheduleRuleset':
            return ScheduleRuleset.from_dict(sch_dict)
        elif sch_dict['type'] == 'ScheduleFixedInterval':
            return ScheduleFixedInterval.from_dict(sch_dict)
        else:
            raise NotImplementedError(
                'Schedule {} is not supported.'.format(sch_dict['type']))

    def __copy__(self):
        return _LoadBase(self.name)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Load Base:\n name: {}'.format(self.name)
