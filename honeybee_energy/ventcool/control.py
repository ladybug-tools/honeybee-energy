# coding=utf-8
"""Object to dictate setpoints and schedule for ventilative cooling."""
from __future__ import division

from ..schedule.dictutil import dict_to_schedule
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..lib.schedules import always_on

from honeybee._lockable import lockable
from honeybee.typing import float_in_range


@lockable
class VentilationControl(object):
    """Object to dictate setpoints and schedule for ventilative cooling.

    Note the all of the default setpoints of this object are set to always perform
    ventilative cooling such that users can individually decide which setpoints
    are relevant to a given ventilation strategy.

    Args:
        min_indoor_temperature: A number between -100 and 100 for the minimum
            indoor temperature at which to ventilate in Celsius. Typically,
            this variable is used to initiate ventilation. (Default: -100).
        max_indoor_temperature: A number between -100 and 100 for the maximum
            indoor temperature at which to ventilate in Celsius. This can be
            used to set a maximum temperature at which point ventilation is
            stopped and a cooling system is turned on. (Default: 100).
        min_outdoor_temperature: A number between -100 and 100 for the minimum
            outdoor temperature at which to ventilate in Celsius. This can be
            used to ensure ventilative cooling doesn't happen during the winter
            even if the Room is above the min_indoor_temperature. (Default: -100).
        max_outdoor_temperature: A number between -100 and 100 for the maximum
            outdoor temperature at which to ventilate in Celsius. This can be
            used to set a limit for when it is considered too hot outside for
            ventilative cooling. (Default: 100).
        delta_temperature: A number between -100 and 100 for the temperature
            differential in Celsius between indoor and outdoor below which
            ventilation is shut off.  This should usually be a positive number
            so that ventilation only occurs when the outdoors is cooler than the
            indoors. Negative numbers indicate how much hotter the outdoors can
            be than the indoors before ventilation is stopped. (Default: -100).
        schedule: An optional ScheduleRuleset or ScheduleFixedInterval for the
            ventilation over the course of the year. Note that this is applied
            on top of any setpoints. The type of this schedule should be On/Off
            and values should be either 0 (no possibility of ventilation) or 1
            (ventilation possible). (Default: "Always On")

    Properties:
        * min_indoor_temperature
        * max_indoor_temperature
        * min_outdoor_temperature
        * max_outdoor_temperature
        * delta_temperature
        * schedule
    """
    __slots__ = ('_min_indoor_temperature', '_max_indoor_temperature',
                 '_min_outdoor_temperature', '_max_outdoor_temperature',
                 '_delta_temperature', '_schedule', '_locked')

    def __init__(self, min_indoor_temperature=-100, max_indoor_temperature=100,
                 min_outdoor_temperature=-100, max_outdoor_temperature=100,
                 delta_temperature=-100, schedule=always_on):
        """Initialize VentilationControl."""
        self.min_indoor_temperature = min_indoor_temperature
        self.max_indoor_temperature = max_indoor_temperature
        self.min_outdoor_temperature = min_outdoor_temperature
        self.max_outdoor_temperature = max_outdoor_temperature
        self.delta_temperature = delta_temperature
        self.schedule = schedule

    @property
    def min_indoor_temperature(self):
        """Get or set a number for the minimum indoor temperature for ventilation (C)."""
        return self._min_indoor_temperature

    @min_indoor_temperature.setter
    def min_indoor_temperature(self, value):
        self._min_indoor_temperature = \
            float_in_range(value, -100.0, 100.0, 'min indoor temperature')

    @property
    def max_indoor_temperature(self):
        """Get or set a number for the maximum indoor temperature for ventilation (C)."""
        return self._max_indoor_temperature

    @max_indoor_temperature.setter
    def max_indoor_temperature(self, value):
        self._max_indoor_temperature = \
            float_in_range(value, -100.0, 100.0, 'max indoor temperature')

    @property
    def min_outdoor_temperature(self):
        """Get or set a number for the minimum outdoor temperature for ventilation (C)."""
        return self._min_outdoor_temperature

    @min_outdoor_temperature.setter
    def min_outdoor_temperature(self, value):
        self._min_outdoor_temperature = \
            float_in_range(value, -100.0, 100.0, 'min outdoor temperature')

    @property
    def max_outdoor_temperature(self):
        """Get or set a number for the maximum outdoor temperature for ventilation (C)."""
        return self._max_outdoor_temperature

    @max_outdoor_temperature.setter
    def max_outdoor_temperature(self, value):
        self._max_outdoor_temperature = \
            float_in_range(value, -100.0, 100.0, 'max outdoor temperature')

    @property
    def delta_temperature(self):
        """Get or set the indoor/outdoor temperature difference for ventilation (C)."""
        return self._delta_temperature

    @delta_temperature.setter
    def delta_temperature(self, value):
        self._delta_temperature = \
            float_in_range(value, -100.0, 100.0, 'delta temperature')

    @property
    def schedule(self):
        """Get or set an On/Off schedule for the ventilation.

        Note that this is applied on top of any setpoints.
        """
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected schedule for VentilationControl schedule. ' \
                'Got {}.'.format(type(value))
            if value.schedule_type_limit is not None:
                assert value.schedule_type_limit.unit == 'fraction', 'VentilationControl ' \
                    'schedule should be fractional [Dimensionless]. Got a schedule ' \
                    'of unit_type [{}].'.format(value.schedule_type_limit.unit_type)
            value.lock()  # lock editing in case schedule has multiple references
            self._schedule = value
        else:
            self._schedule = always_on

    @classmethod
    def from_dict(cls, data):
        """Create a VentilationControl from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'VentilationControl',
            "min_indoor_temperature": 22,
            "max_indoor_temperature": 26,
            "min_outdoor_temperature": 12,
            "max_outdoor_temperature": 32,
            "delta_temperature": -4,
            "schedule": {}  # dictionary of a schedule
            }
        """
        assert data['type'] == 'VentilationControl', \
            'Expected VentilationControl. Got {}.'.format(data['type'])
        min_in, max_in, min_out, max_out, delta = cls._default_dict_values(data)
        sch = dict_to_schedule(data['schedule']) if 'schedule' in data and \
            data['schedule'] is not None else always_on
        vent_control = cls(min_in, max_in, min_out, max_out, delta, sch)
        return vent_control

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a VentilationControl from an abridged dictionary.

        Args:
            data: A VentilationControlAbridged dictionary with the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values. These will be used to
                assign the schedule to the VentilationControl object.

        .. code-block:: python

            {
            "type": 'VentilationControlAbridged',
            "min_indoor_temperature": 22,
            "max_indoor_temperature": 26,
            "min_outdoor_temperature": 12,
            "max_outdoor_temperature": 32,
            "delta_temperature": -4,
            "schedule": ""  # identifier of a schedule
            }
        """
        assert data['type'] == 'VentilationControlAbridged', \
            'Expected VentilationControlAbridged. Got {}.'.format(data['type'])
        min_in, max_in, min_out, max_out, delta = cls._default_dict_values(data)
        sch = schedule_dict[data['schedule']] if \
            'schedule' in data and data['schedule'] is not None else always_on
        vent_control = cls(min_in, max_in, min_out, max_out, delta, sch)
        return vent_control

    def to_dict(self, abridged=False):
        """Ventilation Control dictionary representation."""
        base = {'type': 'VentilationControl'} if not \
            abridged else {'type': 'VentilationControlAbridged'}
        base['min_indoor_temperature'] = self.min_indoor_temperature
        base['max_indoor_temperature'] = self.max_indoor_temperature
        base['min_outdoor_temperature'] = self.min_outdoor_temperature
        base['max_outdoor_temperature'] = self.max_outdoor_temperature
        base['delta_temperature'] = self.delta_temperature
        if self.schedule is not always_on:
            base['schedule'] = self.schedule.identifier if abridged \
                else self.schedule.to_dict()
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    @staticmethod
    def _default_dict_values(data):
        """Process dictionary values and include defaults for missing values."""
        min_in = data['min_indoor_temperature'] if 'min_indoor_temperature' in data \
            and data['min_indoor_temperature'] is not None else -100
        max_in = data['max_indoor_temperature'] if 'max_indoor_temperature' in data \
            and data['max_indoor_temperature'] is not None else 100
        min_out = data['min_outdoor_temperature'] if 'min_outdoor_temperature' in data \
            and data['min_outdoor_temperature'] is not None else -100
        max_out = data['max_outdoor_temperature'] if 'max_outdoor_temperature' in data \
            and data['max_outdoor_temperature'] is not None else 100
        delta = data['delta_temperature'] if 'delta_temperature' in data \
            and data['delta_temperature'] is not None else -100
        return min_in, max_in, min_out, max_out, delta

    def __copy__(self):
        return VentilationControl(
            self.min_indoor_temperature, self.max_indoor_temperature,
            self.min_outdoor_temperature, self.max_outdoor_temperature,
            self.delta_temperature, self.schedule)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.min_indoor_temperature, self.max_indoor_temperature,
                self.min_outdoor_temperature, self.max_outdoor_temperature,
                self.delta_temperature, hash(self._schedule))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, VentilationControl) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'VentilationControl, [min in: {}] [max in: {}] [min out: {}] ' \
            '[max out: {}] [delta: {}]'.format(
                self.min_indoor_temperature, self.max_indoor_temperature,
                self.min_outdoor_temperature, self.max_outdoor_temperature,
                self.delta_temperature)
