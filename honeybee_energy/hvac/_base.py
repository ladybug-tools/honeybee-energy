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

    Properties:
        * name
        * is_single_room
        * schedules
    """
    __slots__ = ('_name', '_is_single_room', '_parent', '_locked')

    def __init__(self, name, is_single_room=True):
        """Initialize HVACSystem.

        Args:
            name: Text string for system name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            is_single_room: Boolean to note whether the HVAC system is only assignable
                to a single Room. If True, an error will be raised if the system
                is set to more than one Room and if False, no error will be raised
                in such cases. An example of a single room system is the IdealAirSystem
                and an example of a multi room system is VAVWithReheat.
        """
        self._is_single_room = bool(is_single_room)
        self._parent = None  # this is only used by single room systems
        self.name = name
    
    @property
    def name(self):
        """Get or set the text string for HVAC system name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'HVAC system name')
    
    @property
    def is_single_room(self):
        """Get a boolean noting whether the HVAC system is assignable to only one Room.
        """
        return self._is_single_room
    
    @property
    def schedules(self):
        """Get an array of all the schedules assiciated with the HVAC system.

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
        return _HVACSystem(self.is_single_room)

    def __repr__(self):
        return 'HVACSystem:\n is single room: {}'.format(self.is_single_room)
