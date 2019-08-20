# coding=utf-8
"""Energy schedule type definition."""
from .writer import generate_idf_string, parse_idf_string

from honeybee.typing import valid_ep_string, valid_string, float_in_range
from ladybug.datatype import fraction, temperature, temperaturedelta, power, \
    angle, speed, distance, uvalue


class ScheduleType(object):
    """Energy schedule type definition.

    Schedule types exist for the sole purpose of validating schedule values against
    upper/lower limits and assigning a data type and units to the schedule values.

    Properties:
        name
        lower_limit
        upper_limit
        numeric_type
        unit_type
        data_type
        unit
    """
    _default_lb_unit_type = {
        'Dimensionless': (fraction.Fraction(), 'fraction'),
        'Temperature': (temperature.Temperature(), 'C'),
        'DeltaTemperature': (temperaturedelta.TemperatureDelta(), 'C'),
        'PrecipitationRate': [distance.Distance(), 'm'],
        'Angle': [angle.Angle(), 'degrees'],
        'ConvectionCoefficient': [uvalue.ConvectionCoefficient(), 'W/m2-K'],
        'ActivityLevel': [power.ActivityLevel(), 'W'],
        'Velocity': [speed.Speed(), 'm/s'],
        'Capacity': [power.Power(), 'W'],
        'Power': [power.Power(), 'W'],
        'Availability': [fraction.Fraction(), 'fraction'],
        'Percent': [fraction.Fraction(), '%'],
        'Control': [fraction.Fraction(), 'fraction'],
        'Mode': [fraction.Fraction(), 'fraction']}

    UNIT_TYPES = tuple(_default_lb_unit_type.keys())
    NUMERIC_TYPES = ('Continuous', 'Discrete')

    def __init__(self, name, lower_limit=None, upper_limit=None,
                 numeric_type='Continuous', unit_type='Dimensionless'):
        """Initialize ScheduleType.

        Args:
            name: Text string for schedule type name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            lower_limit: An optional number for the lower limit for values in the
                schedule. If None, there will be no lower limit.
            upper_limit: An optional number for the upper limit for values in the
                schedule. If None, there will be no upper limit.
            numeric_type: Either one of two strings: 'Continuous' or 'Discrete'.
                The latter means that only integers are accepted as schedule values.
                Default: 'Continuous'.
            unit_type: Text for an EnergyPlus unit type, which will be used
                to assign units to the values in the schedule.  Note that this field
                is not used in the actual calculations of EnergyPlus.
                Default: 'Dimensionless'. Choose from the following options:
                'Dimensionless', 'Temperature', 'DeltaTemperature', 'PrecipitationRate',
                'Angle', 'ConvectionCoefficient', 'ActivityLevel', 'Velocity',
                'Capacity', 'Power', 'Availability', 'Percent', 'Control', 'Mode'
        """
        # process the name and limits
        self._name = valid_ep_string(name, 'schedule type name')
        self._lower_limit = float_in_range(lower_limit) if lower_limit is not \
            None else None
        self._upper_limit = float_in_range(upper_limit) if upper_limit is not \
            None else None
        if self._lower_limit is not None and self._upper_limit is not None:
            assert self._lower_limit <= self._upper_limit, 'ScheduleType lower_limit '\
                'must be less than upper_limit. {} > {}.'.format(
                    self._lower_limit, self._upper_limit)

        # process the numeric type
        self._numeric_type = numeric_type.capitalize() or 'Continuous'
        assert self._numeric_type in self.NUMERIC_TYPES, '"{}" is not an acceptable ' \
            'numeric type.  Choose from the following:\n{}'.format(
                numeric_type, self.NUMERIC_TYPES)

        # process the unit type and assign the ladybug data type and unit
        if unit_type is None:
            self._data_type, self._unit = self._default_lb_unit_type['Dimensionless']
            self._unit_type = 'Dimensionless'
        else:
            try:
                self._data_type, self._unit = self._default_lb_unit_type[unit_type]
                self._unit_type = unit_type
            except KeyError:
                clean_input = valid_string(unit_type).lower()
                for key in self.UNIT_TYPES:
                    if key.lower() == clean_input:
                        unit_type = key
                        break
                else:
                    raise ValueError(
                        'unit_type {} is not recognized.\nChoose from the '
                        'following:\n{}'.format(unit_type, self.UNIT_TYPES))
                self._data_type, self._unit = self._default_lb_unit_type[unit_type]
                self._unit_type = unit_type

    @property
    def name(self):
        """Get the text string for schedule type name."""
        return self._name

    @property
    def lower_limit(self):
        """Get the lower limit of the schedule type."""
        return self._lower_limit

    @property
    def upper_limit(self):
        """Get the upper limit of the schedule type."""
        return self._upper_limit

    @property
    def numeric_type(self):
        """Text noting whether schedule values are 'Continuous' or 'Discrete'."""
        return self._numeric_type

    @property
    def unit_type(self):
        """Get the text string describing the energyplus unit type."""
        return self._unit_type

    @property
    def data_type(self):
        """Get the Ladybug DataType object corresponding to the energyplus unit type.

        This object can be used for creating Ladybug DataCollections, performing unit
        conversions of schedule values, etc.
        """
        return self._data_type

    @property
    def unit(self):
        """Get the string describing the units of the schedule values (ie. 'C', 'W')."""
        return self._unit

    @classmethod
    def from_idf(cls, idf_string):
        """Create a ScheduleType from an IDF string of ScheduleTypeLimits.

        Args:
            idf_string: A text string describing EnergyPlus ScheduleTypeLimits.
        """
        prop_types = (str, float, float, str, str)
        ep_strs = parse_idf_string(idf_string, 'ScheduleTypeLimits,')
        ep_fields = [typ(prop) if prop != '' else None
                     for typ, prop in zip(prop_types, ep_strs)]
        return cls(*ep_fields)

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleType from a dictionary.

        Args:
            data: {
                "type": 'ScheduleType',
                "name": 'Fractional',
                "lower_limit": 0,
                "upper_limit": 1,
                "numeric_type": False,
                "unit_type": "Dimensionless"
                }
        """
        assert data['type'] == 'ScheduleType', \
            'Expected ScheduleType dictionary. Got {}.'.format(data['type'])
        lower_limit = data['lower_limit'] if 'lower_limit' in data else None
        upper_limit = data['upper_limit'] if 'upper_limit' in data else None
        numeric_type = data['numeric_type'] if 'numeric_type' in data else 'Continuous'
        unit_type = data['unit_type'] if 'unit_type' in data else 'Dimensionless'
        return cls(data['name'], lower_limit, upper_limit, numeric_type, unit_type)

    def to_idf(self):
        """IDF string for the ScheduleTypeLimits of this object."""
        values = [self.name, self.lower_limit, self.upper_limit,
                  self.numeric_type, self.unit_type]
        if values[1] is None:
            values[1] = ''
        if values[2] is None:
            values[2] = ''
        comments = ('name', 'lower limit value', 'upper limit value',
                    'numeric type', 'unit type')
        return generate_idf_string('ScheduleTypeLimits', values, comments)

    def to_dict(self):
        """Shade construction dictionary representation."""
        base = {'type': 'ScheduleType'}
        base['name'] = self.name
        base['lower_limit'] = self.lower_limit
        base['upper_limit'] = self.upper_limit
        base['numeric_type'] = self.numeric_type
        base['unit_type'] = self.unit_type
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        return ScheduleType(self.name, self._lower_limit, self._upper_limit,
                            self._numeric_type, self._unit_type)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.name, self._lower_limit, self._upper_limit,
                self._numeric_type, self._unit_type)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleType) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return self.to_idf()


class _ScheduleTypes(object):
    """Enumeration of the most commonly used schedule types.

    These can be used on interface side of plugins so that users do not have to
    create an entirely new ScheduleType unless they have a schedule that is truly
    very custom.
    """

    def __init__(self):
        self._fractional = \
            ScheduleType('Fractional', 0, 1, 'Continuous', 'Dimensionless')
        self._on_off = \
            ScheduleType('On-Off', 0, 1, 'Discrete', 'Dimensionless')
        self._temperature = \
            ScheduleType('Temperature', -273.15, None, 'Continuous', 'Temperature')
        self._activity_level = \
            ScheduleType('Activity Level', 0, None, 'Continuous', 'ActivityLevel')
        self._power = \
            ScheduleType('Power', None, None, 'Continuous', 'Power')
        self._angle = \
            ScheduleType('Angle', 0, 180, 'Continuous', 'Angle')
        self._thermostat_control = \
            ScheduleType('Thermostat Control', 0, 4, 'Discrete', 'Dimensionless')
        self._delta_temperature = \
            ScheduleType('Delta Temperature', None, None, 'Continuous',
                         'DeltaTemperature')

    @property
    def fractional(self):
        return self._fractional

    @property
    def on_off(self):
        return self._on_off

    @property
    def temperature(self):
        return self._temperature

    @property
    def delta_temperature(self):
        return self._delta_temperature

    @property
    def activity_level(self):
        return self._activity_level

    @property
    def power(self):
        return self._power

    @property
    def angle(self):
        return self._angle

    @property
    def thermostat_control(self):
        return self._thermostat_control

    def by_name(self, schedule_type_name):
        """Get a Schedule Type instance from its name.

        Args:
            schedule_type_name: A text string for the schedule type (eg. "on_off").
        """
        attr_name = schedule_type_name.replace(' ', '_').lower()
        try:
            return getattr(self, attr_name)
        except AttributeError:
            attr = [atr for atr in dir(self)
                    if not atr.startswith('_') and atr != 'by_name']
            raise AttributeError(
                'Schedule Type "{}" is not in the enumeration of common schedule types.'
                '\nMake a custom ScheduleType or choose from the following:'
                '\n{}'.format(schedule_type_name, attr))

    def __repr__(self):
        return 'Schedule Types:\nfractional\non_off\ntemperature\ndelta_temperature\n' \
            'activity_level\npower\nangle\nthermostat_control'


schedule_types = _ScheduleTypes()
