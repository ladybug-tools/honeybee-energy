# coding=utf-8
"""AirBoundary Construction."""
from __future__ import division

from ..schedule.dictutil import dict_to_schedule
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..writer import generate_idf_string
from ..lib.schedules import always_on

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, float_positive


@lockable
class AirBoundaryConstruction(object):
    """Construction for Faces with an AirBoundary face type.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        air_mixing_per_area: A positive number for the amount of air mixing
            between Rooms across the air boundary surface [m3/s-m2].
            Default: 0.1 [m3/s-m2]. This corresponds to average indoor air
            speeds of 0.1 m/s (roughly 20 fpm), which is typical of what
            would be induced by a HVAC system.
        air_mixing_schedule: A fractional schedule for the air mixing schedule
            across the construction.

    Properties:
        * identifier
        * display_name
        * air_mixing_per_area
        * air_mixing_schedule
    """

    __slots__ = ('_identifier', '_display_name', '_air_mixing_per_area',
                 '_air_mixing_schedule', '_locked')

    def __init__(self, identifier, air_mixing_per_area=0.1,
                 air_mixing_schedule=always_on):
        """Initialize AirBoundaryConstruction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.air_mixing_per_area = air_mixing_per_area
        self.air_mixing_schedule = air_mixing_schedule

    @property
    def identifier(self):
        """Get or set the text string for construction identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'construction identifier')

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
    def air_mixing_per_area(self):
        """Get or set the air mixing per area across the AirBoundary in [m3/s-m2]."""
        return self._air_mixing_per_area

    @air_mixing_per_area.setter
    def air_mixing_per_area(self, value):
        self._air_mixing_per_area = float_positive(value, 'air mixing per area')

    @property
    def air_mixing_schedule(self):
        """Get or set a fractional schedule for the air mixing schedule."""
        return self._air_mixing_schedule

    @air_mixing_schedule.setter
    def air_mixing_schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected schedule for air wall mixing schedule. ' \
                'Got {}.'.format(type(value))
            if value.schedule_type_limit is not None:
                assert value.schedule_type_limit.unit == 'fraction', 'Air mixing ' \
                    'schedule should be fractional [Dimensionless]. Got a schedule ' \
                    'of unit_type [{}].'.format(value.schedule_type_limit.unit_type)
            value.lock()  # lock editing in case schedule has multiple references
            self._air_mixing_schedule = value
        else:
            self._air_mixing_schedule = always_on

    @classmethod
    def from_dict(cls, data):
        """Create a AirBoundaryConstruction from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'AirBoundaryConstruction',
            "identifier": 'Generic Air Boundary Construction 020',
            "display_name": 'Air Boundary',
            "air_mixing_per_area": 0.2,
            "air_mixing_schedule": {}  # dictionary of a schedule
            }
    """
        assert data['type'] == 'AirBoundaryConstruction', \
            'Expected AirBoundaryConstruction. Got {}.'.format(data['type'])
        a_mix = data['air_mixing_per_area'] if 'air_mixing_per_area' in data else 0.1
        if 'air_mixing_schedule' in data:
            a_sch = dict_to_schedule(data['air_mixing_schedule'])
        else:
            a_sch = always_on
        new_obj = cls(data['identifier'], a_mix, a_sch)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a AirBoundaryConstruction from an abridged dictionary.

        Args:
            data: A AirBoundaryConstructionAbridged dictionary with the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values. These will be used to
                assign the schedule to the AirBoundaryConstruction object.

        .. code-block:: python

            {
            "type": 'AirBoundaryConstructionAbridged',
            "identifier": 'Generic Air Boundary Construction',
            "display_name": 'Air Boundary',
            "air_mixing_schedule": ""  # identifier of a schedule
            }
        """
        assert data['type'] == 'AirBoundaryConstructionAbridged', \
            'Expected AirBoundaryConstructionAbridged. Got {}.'.format(data['type'])
        a_mix = data['air_mixing_per_area'] if 'air_mixing_per_area' in data else 0.1
        a_sch = schedule_dict[data['air_mixing_schedule']] if \
            'air_mixing_schedule' in data else always_on
        new_obj = cls(data['identifier'], a_mix, a_sch)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self):
        """IDF string for the Construction:AirBoundary of this object.

        Note that the to_air_mixing_idf method must also be used to write air
        mixing objects into the IDF for each Face that has the construction
        assigned to it.
        """
        values = [self.identifier, 'GroupedZones', 'GroupedZones', 'None']
        comments = ('construction name', 'solar and daylight method',
                    'radiant exchange method', 'air exchange method')
        return generate_idf_string('Construction:AirBoundary', values, comments)

    def to_air_mixing_idf(self, face, room_identifier):
        """IDF string for the ZoneMixing of this object.

        Args:
            face: A Face object to which this construction is assigned. This
                Face must have a parent Room.
            room_identifier: A identifier for the Room to which the Face is adjacent.
        """
        flow_rate = face.area * self.air_mixing_per_area
        values = ['{}_Mixing'.format(face.identifier), face.parent.identifier,
                  self.air_mixing_schedule.identifier, 'Flow/Zone',
                  flow_rate, '', '', '', room_identifier]
        comments = ('name', 'zone name', 'schedule name', 'flow method', 'flow rate',
                    'flow per floor area', 'flow per person', 'ach', 'source zone name')
        return generate_idf_string('ZoneMixing', values, comments)

    def to_dict(self, abridged=False):
        """Air boundary construction dictionary representation."""
        base = {'type': 'AirBoundaryConstruction'} if not \
            abridged else {'type': 'AirBoundaryConstructionAbridged'}
        base['identifier'] = self.identifier
        base['air_mixing_per_area'] = self.air_mixing_per_area
        base['air_mixing_schedule'] = self.air_mixing_schedule.identifier if abridged \
            else self.air_mixing_schedule.to_dict()
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def __copy__(self):
        new_con = AirBoundaryConstruction(
            self.identifier, self._air_mixing_per_area, self._air_mixing_schedule)
        new_con._display_name = self._display_name
        return new_con

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._air_mixing_per_area,
                hash(self._air_mixing_schedule))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, AirBoundaryConstruction) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'AirBoundaryConstruction: {} [{} m3/s-m2] [schedule: {}]'.format(
                self.display_name, round(self.air_mixing_per_area, 4),
                self.air_mixing_schedule.display_name)
