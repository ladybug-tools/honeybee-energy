# coding=utf-8
"""Base class to be used for all HVAC systems."""
from __future__ import division

from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class _HVACSystem(object):
    """Base class to be used for all HVAC systems

    Args:
        identifier: Text string for system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.

    Properties:
        * identifier
        * display_name
        * schedules
    """
    __slots__ = ('_identifier', '_display_name', '_locked')

    def __init__(self, identifier):
        """Initialize HVACSystem."""
        self.identifier = identifier
        self._display_name = None

    @property
    def identifier(self):
        """Get or set the text string for HVAC system identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'HVAC system identifier')

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def schedules(self):
        """Get an array of all the schedules associated with the HVAC system.

        This property should be overwritten in each of the classes inheriting from
        the HVACSystem base class since each HVAC system is likely to have it's
        own unique places where schedules are assigned. At a minimum, this property
        should return heating/cooling availability schedules.
        """
        return ()

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    @staticmethod
    def _check_schedule(schedule, obj_name=''):
        """Check that an input schedule is a correct object type."""
        assert isinstance(schedule, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for {} ' \
            'schedule. Got {}.'.format(obj_name, type(schedule))

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
        new_obj = _HVACSystem(self.identifier)
        new_obj._display_name = self._display_name
        return new_obj

    def __repr__(self):
        return 'HVACSystem: {}'.format(self.display_name)
