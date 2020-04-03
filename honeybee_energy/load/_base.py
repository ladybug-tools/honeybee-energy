# coding=utf-8
"""Base object for all load definitions."""
from __future__ import division

from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, tuple_with_length


@lockable
class _LoadBase(object):
    """A base object for all load definitions.

    Args:
        identifier: Text string for a unique Load ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.

    Properties:
        * identifier
        * display_name
    """
    __slots__ = ('_identifier', '_display_name', '_locked')

    def __init__(self, identifier):
        """Initialize LoadBase."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None

    @property
    def identifier(self):
        """Get or set the text string for object identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier)

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
    def _check_avg_weights(load_objects, weights, obj_name):
        """Check input weights of an average calculation and generate them if None."""
        if weights is None:
            weights = unity_weights = [1 / len(load_objects)] * len(load_objects) if \
                len(load_objects) > 0 else []
        else:
            weights = tuple_with_length(weights, len(load_objects), float,
                                        'average {} weights'.format(obj_name))
            total_weight = sum(weights)
            assert total_weight <= 1 + 1e-9, 'Average {} weights must be less than ' \
                'or equal to 1. Got {}.'.format(obj_name, sum(weights))
            unity_weights = [w / total_weight for w in weights]

        return weights, unity_weights

    @staticmethod
    def _average_schedule(identifier, scheds, weights, timestep):
        """Average a set of schedules together (no matter their type)."""
        try:
            return ScheduleRuleset.average_schedules(identifier, scheds, weights, timestep)
        except AttributeError:
            return ScheduleFixedInterval.average_schedules(identifier, scheds, weights)

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
        new_obj = _LoadBase(self.identifier)
        new_obj._display_name = self._display_name
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Load Base: {}'.format(self.identifier)
