# coding=utf-8
"""Base object for all load definitions."""
from __future__ import division
import random

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, tuple_with_length

from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval


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
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_locked',
                 '_properties', '_user_data')

    def __init__(self, identifier):
        """Initialize LoadBase."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self._user_data = None
        self._properties = None

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
        if value is not None:
            try:
                value = str(value)
            except UnicodeEncodeError:  # Python 2 machine lacking the character set
                pass  # keep it as unicode
        self._display_name = value

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _check_fractional_schedule_type(self, schedule, obj_name=''):
        """Check that the type limit of an input schedule is fractional."""
        if schedule.schedule_type_limit is not None:
            t_lim = schedule.schedule_type_limit
            assert t_lim.unit == 'fraction', '{} schedule should be fractional ' \
                '[Dimensionless]. Got a schedule of unit_type ' \
                '[{}].'.format(obj_name, t_lim.unit_type)
            assert t_lim.lower_limit == 0, '{} schedule should have either no type ' \
                'limit or a lower limit of 0. Got a schedule type with lower limit ' \
                '[{}].'.format(obj_name, t_lim.lower_limit)
            assert t_lim.upper_limit == 1, '{} schedule should have either no type ' \
                'limit or an upper limit of 1. Got a schedule type with upper limit ' \
                '[{}].'.format(obj_name, t_lim.upper_limit)

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
            assert total_weight <= 1 + 1e-3, 'Average {} weights must be less than ' \
                'or equal to 1. Got {}.'.format(obj_name, sum(weights))
            unity_weights = [w / total_weight for w in weights]

        return weights, unity_weights

    @staticmethod
    def _average_schedule(identifier, scheds, weights, timestep):
        """Average a set of schedules together (no matter their type)."""
        try:
            return ScheduleRuleset.average_schedules(
                identifier, scheds, weights, timestep)
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

    @staticmethod
    def _shift_schedule(schedule, schedule_offset, timestep):
        """Take a schedule and shift it behind and then ahead."""
        if schedule_offset == 0 or not isinstance(schedule, ScheduleRuleset):
            return [schedule] * 3
        else:
            behind = schedule.shift_by_step(-schedule_offset, timestep)
            ahead = schedule.shift_by_step(schedule_offset, timestep)
            return [behind, schedule, ahead]

    @staticmethod
    def _gaussian_values(count, load_value, load_stdev):
        """Generate Gaussian values for a load and a corresponding schedule integers."""
        new_loads, sch_int = [], []
        for _ in range(count):
            val = random.gauss(load_value, load_stdev)
            final_val = 1e-6 if val <= 0 else val  # avoid negative values
            new_loads.append(final_val)
            sch_int.append(random.randint(0, 2))
        return new_loads, sch_int

    def __copy__(self):
        new_obj = _LoadBase(self.identifier)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Load Base: {}'.format(self.display_name)
