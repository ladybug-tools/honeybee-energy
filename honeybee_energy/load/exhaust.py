# coding=utf-8
"""Complete definition of ventilation in a simulation, including schedule and load."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_positive, float_in_range, int_positive

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..units import convert_ventilation_flow_per_area, \
    convert_ventilation_flow_per_zone, convert_pressure_rise
from ..lib.schedules import always_on
import honeybee_energy.lib.scheduletypelimits as _type_lib


@lockable
class ExhaustAir(_LoadBase):
    """A complete definition of exhaust air, including schedules and flow rates.

    Note the the 2 ventilation types (flow_per_area and flow_per_fixture) are
    ultimately added together to yield the final exhaust air flow rate used
    in the simulation.

    Args:
        identifier: Text string for a unique ExhaustAir ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        flow_per_area: A numerical value for the intensity of exhaust air ventilation
            in m3/s per square meter of floor area. (Default: 0).
        flow_per_fixture: A numerical value for the level of exhaust air ventilation
            in m3/s for each fixture in the room. The term "fixture" is used
            broadly as a way to reference a wide variety of contaminant sources
            such as toilets/urinals, shower heads, kitchen hoods, fume hoods,
            etc. (Default: 0).
        fixture_count: An integer for the number of fixtures in the room. This
            is multiplied by the flow_per_fixture, which is then added to the
            flow_per_area to yield the final exhaust air flow rate (Default: 1).
        schedule: An optional ScheduleRuleset or ScheduleFixedInterval for the
            exhaust air ventilation over the course of the year. The type of this
            schedule should be Fractional and the fractional values get multiplied by
            the total design flow rate to yield a complete ventilation profile.
            Values of 0 in the schedule will shut the fan off completely. If None,
            the design level of ventilation will be used throughout all timesteps
            of the simulation, meaning that this schedule is Always On. (Default: None).
        pressure_rise: A number for the the pressure rise across the fan in Pascals
            (N/m2). This is often a function of the fan speed and the conditions in
            which the fan is operating. It plays an important role in determining
            the amount of energy consumed by the fan. Typical kitchen and bathroom
            exhaust fans have pressure rises around 125 Pa but, in healthcare
            settings where filters create more resistance, higher pressures
            around 250 Pa are more common. (Default: 125).
        efficiency: A number between 0 and 1 for the overall efficiency of the fan.
            Specifically, this is the ratio of the power delivered to the fluid
            to the electrical input power. It is the product of the fan motor
            efficiency and the fan impeller efficiency.
            Fans that have a higher blade diameter, no obstructions or filters,
            and operate at lower speeds with smaller pressure rises for
            their size tend to have higher efficiencies. Because motor efficiencies
            are typically between 0.8 and 0.9, the best overall fan efficiencies
            tend to be around 0.7 with most typical fan efficiencies between 0.5 and
            0.7. When filters are added, which is common for most exhaust fans,
            the total efficiency typically ends up between 0.3 and 0.4. (Default: 0.35).

    Properties:
        * identifier
        * display_name
        * flow_per_area
        * flow_per_fixture
        * fixture_count
        * schedule
        * pressure_rise
        * efficiency
        * user_data
    """
    __slots__ = (
        '_flow_per_area', '_flow_per_fixture', '_fixture_count', '_schedule',
        '_pressure_rise', '_efficiency'
    )

    def __init__(
        self, identifier, flow_per_area=0, flow_per_fixture=0, fixture_count=1,
        schedule=None, pressure_rise=125, efficiency=0.35
    ):
        """Initialize ExhaustAir."""
        _LoadBase.__init__(self, identifier)
        self.flow_per_area = flow_per_area
        self.flow_per_fixture = flow_per_fixture
        self.fixture_count = fixture_count
        self.schedule = schedule
        self.pressure_rise = pressure_rise
        self.efficiency = efficiency

    @property
    def flow_per_area(self):
        """Get or set the exhaust ventilation in m3/s per square meter of floor area."""
        return self._flow_per_area

    @flow_per_area.setter
    def flow_per_area(self, value):
        self._flow_per_area = float_positive(value, 'exhaust flow per area') if \
            value is not None else 0

    @property
    def flow_per_fixture(self):
        """Get or set the exhaust ventilation in m3/s per fixture."""
        return self._flow_per_fixture

    @flow_per_fixture.setter
    def flow_per_fixture(self, value):
        self._flow_per_fixture = float_positive(value, 'exhaust flow per fixture') if \
            value is not None else 0

    @property
    def fixture_count(self):
        """Get or set an integer for the number of fixtures in the room."""
        return self._fixture_count

    @fixture_count.setter
    def fixture_count(self, value):
        self._fixture_count = \
            int_positive(value, 'exhaust air fixture count') if \
            value is not None else 1

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for exhaust air."""
        return self._schedule if self._schedule is not None else always_on

    @schedule.setter
    def schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected ScheduleRuleset or ScheduleFixedInterval for ExhaustAir ' \
                'schedule. Got {}.'.format(type(value))
            self._check_fractional_schedule_type(value, 'ExhaustAir')
            value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def pressure_rise(self):
        """Get or set a number for the fan pressure rise in Pa."""
        if self._pressure_rise is not None:
            return self._pressure_rise
        return self._default_pressure_rise()

    @pressure_rise.setter
    def pressure_rise(self, value):
        if value is not None:
            value = float_positive(value, 'fan pressure rise')
        self._pressure_rise = value

    @property
    def efficiency(self):
        """Get or set a number between 0 and 1 for the fan efficiency."""
        if self._efficiency is not None:
            return self._efficiency
        return self._default_efficiency()

    @efficiency.setter
    def efficiency(self, value):
        if value is not None:
            value = float_in_range(value, 0, 1, 'fan efficiency')
        self._efficiency = value

    @property
    def flow_per_area_si(self):
        """Get the flow_per_area in the standard SI unit of L/s/m2."""
        return convert_ventilation_flow_per_area(self.flow_per_area, 'si')

    @property
    def flow_per_area_ip(self):
        """Get the flow_per_area in the standard IP unit of cfm/ft2."""
        return convert_ventilation_flow_per_area(self.flow_per_area, 'ip')

    @property
    def flow_per_fixture_si(self):
        """Get the flow_per_fixture in the standard SI unit of L/s."""
        return convert_ventilation_flow_per_zone(self.flow_per_fixture, 'si')

    @property
    def flow_per_fixture_ip(self):
        """Get the flow_per_fixture in the standard IP unit of cfm."""
        return convert_ventilation_flow_per_zone(self.flow_per_fixture, 'ip')

    @property
    def pressure_rise_si(self):
        """Get the pressure_rise in the standard SI unit of Pa."""
        return convert_pressure_rise(self.pressure_rise, 'si')

    @property
    def pressure_rise_ip(self):
        """Get the pressure_rise in the standard IP unit of inches of H2O."""
        return convert_pressure_rise(self.pressure_rise, 'ip')

    def room_absolute_flow(self, room):
        """Get the total flow rate of exhaust ventilation air for a Room in m3/s.

        The result of this method accounts for both ways of specifying exhaust air.

        Args:
            room: The honeybee Room to which the ventilation object is assigned.
        """
        total_flows = [self.flow_per_fixture * self.fixture_count]
        if self.flow_per_area != 0:
            total_flows.append(self.flow_per_area * room.floor_area)
        return sum(total_flows)

    @classmethod
    def from_dict(cls, data, schedules=None):
        """Create a ExhaustAir object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A ExhaustAir dictionary in following the format below.
            schedules: Optional dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). When specified, these will be prioritized
                over the child objects underneath their unabridged specification.

        .. code-block:: python

            {
            "type": 'ExhaustAir',
            "identifier": 'Bathroom_ExhaustAir_000050_001_1',
            "display_name": 'Bathroom ExhaustAir',
            "flow_per_area": 0.0005, # flow per square meter of floor area
            "flow_per_fixture": 0.01, # flow per fixture
            "fixture_count": 1, # number of fixtures in the room
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "pressure_rise": 125, # fan pressure rise in Pa
            "efficiency": 0.35 # fan efficiency
            }
        """
        assert data['type'] == 'ExhaustAir', \
            'Expected ExhaustAir dictionary. Got {}.'.format(data['type'])
        area, fix_flow, fix_count, press, eff = cls._optional_dict_keys(data)
        sched = cls._get_schedule_from_dict(data['schedule'], schedules) \
            if 'schedule' in data and data['schedule'] is not None else None
        new_obj = cls(data['identifier'], area, fix_flow, fix_count, sched, press, eff)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a ExhaustAir object from an abridged dictionary.

        Args:
            data: A ExhaustAirAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the ExhaustAir object.

        .. code-block:: python

            {
            "type": 'ExhaustAirAbridged',
            "identifier": 'Bathroom_ExhaustAir_000050_001_1',
            "display_name": 'Bathroom ExhaustAir',
            "flow_per_area": 0.0005, # flow per square meter of floor area
            "flow_per_fixture": 0.01, # flow per fixture
            "fixture_count": 1, # number of fixtures in the room
            "schedule": "Bathroom ExhaustAir Schedule", # Schedule identifier
            "pressure_rise": 125, # fan pressure rise in Pa
            "efficiency": 0.35 # fan efficiency
            }
        """
        assert data['type'] == 'ExhaustAirAbridged', \
            'Expected ExhaustAirAbridged dictionary. Got {}.'.format(data['type'])
        area, fix_flow, fix_count, press, eff = cls._optional_dict_keys(data)
        sched = None
        if 'schedule' in data and data['schedule'] is not None:
            try:
                sched = schedule_dict[data['schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], area, fix_flow, fix_count, sched, press, eff)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_dict(self, abridged=False):
        """ExhaustAir dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. (Default: False).
        """
        base = {'type': 'ExhaustAir'} if not abridged \
            else {'type': 'ExhaustAirAbridged'}
        base['identifier'] = self.identifier
        if self.flow_per_area != 0:
            base['flow_per_area'] = self.flow_per_area
        if self.flow_per_fixture != 0:
            base['flow_per_fixture'] = self.flow_per_fixture
        if self.fixture_count != 1:
            base['fixture_count'] = self.fixture_count
        if self._schedule is not None:
            base['schedule'] = self.schedule.to_dict() if not \
                abridged else self.schedule.identifier
        if self.pressure_rise != 125:
            base['pressure_rise'] = self.pressure_rise
        if self.efficiency != 0:
            base['efficiency'] = self.efficiency
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    @staticmethod
    def average(identifier, exhaust_airs, weights=None, timestep_resolution=1):
        """Get a ExhaustAir object that's an average between other ExhaustAirs.

        Args:
            identifier: Text string for a unique ID for the new averaged ExhaustAir.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            exhaust_airs: A list of ExhaustAir objects that will be averaged
                together to make a new ExhaustAir.
            weights: An optional list of fractional numbers with the same length
                as the input exhaust_airs. These will be used to weight each of the
                ExhaustAir objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average flow rates
                will assume 0 for the unaccounted fraction of the weights.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging
                process. (Default: 1).
        """
        weights, u_weights = \
            ExhaustAir._check_avg_weights(exhaust_airs, weights, 'ExhaustAir')

        # calculate the average values
        area = sum([vent.flow_per_area * w
                    for vent, w in zip(exhaust_airs, weights)])
        fixture = sum([vent.flow_per_fixture * vent.fixture_count
                       for vent in exhaust_airs])
        press = sum([vent.pressure_rise * w
                     for vent, w in zip(exhaust_airs, weights)])
        eff = sum([vent.efficiency * w
                   for vent, w in zip(exhaust_airs, weights)])
        # round the effectiveness terms to avoid tolerance issues
        area = round(area, 3)
        press = round(press, 3)
        eff = round(eff, 3)

        # calculate the average schedules
        scheds = [vent._schedule for vent in exhaust_airs]
        if all(val is None for val in scheds):
            sched = None
        else:
            full_vent = ScheduleRuleset.from_constant_value(
                'Full ExhaustAir', 1, _type_lib.fractional)
            for i, sch in enumerate(scheds):
                if sch is None:
                    scheds[i] = full_vent
            sched = ExhaustAir._average_schedule(
                '{} Schedule'.format(identifier), scheds, u_weights, timestep_resolution)

        # return the averaged object
        return ExhaustAir(identifier, area, fixture, 1, sched, press, eff)

    @staticmethod
    def combine_room_exhaust_airs(identifier, rooms, timestep_resolution=1):
        """Get a ExhaustAir object that represents the sum across rooms.

        In this process of combining exhaust air requirements, the following
        rules hold: 1. Flow per floor area gets recomputed using the floor
        areas of each room. 2. Flow defined by fixtures it totaled across
        all of the input rooms and then assigned to the result as a single
        flow value for one fixture.

        In the case of exhaust air schedules, the strictest schedule governs and
        note that the absence of a exhaust air schedule means the schedule is
        Always On. So, if one room has a exhaust air schedule and the other
        does not, then the schedule essentially gets removed. If each room has
        a different exhaust air schedule, then a new schedule will be created
        using the maximum value across the two schedules at each timestep.

        Args:
            identifier: Text string for a unique ID for the new ExhaustAir object.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            rooms: A list of Rooms that will have their ExhaustAir objects
                combined to make a new ExhaustAir.
            timestep_resolution: An optional integer for the timestep resolution at
                which conflicting ventilation schedules will be resolved. (Default: 1).
        """
        # compute weights based on floor areas and volumes
        exhaust_airs, floor_areas, scheds = [], [], []
        for room in rooms:
            if room.properties.energy.exhaust_air is None:
                exhaust_airs.append(ExhaustAir('dummy_ea'))
            else:
                exhaust_airs.append(room.properties.energy.exhaust_air)
                scheds.append(room.properties.energy.ventilation._schedule)
            floor_areas.append(room.floor_area)
        total_floor = sum(floor_areas)
        floor_weights = [ar / total_floor for ar in floor_areas]

        # calculate the average values
        area = sum([vent.flow_per_area * w
                    for vent, w in zip(exhaust_airs, floor_weights)])
        fixture = sum(vent.flow_per_fixture * vent.fixture_count for vent in exhaust_airs)
        press = sum([vent.pressure_rise * w
                     for vent, w in zip(exhaust_airs, floor_weights)])
        eff = sum([vent.efficiency * w
                   for vent, w in zip(exhaust_airs, floor_weights)])

        # calculate the average schedules
        if len(scheds) == 0 or any(val is None for val in scheds):
            sched = None
        else:
            base_sch = scheds[0]
            if all(sch is base_sch for sch in scheds) or len(set(scheds)) == 1:
                sched = scheds[0]
            else:
                sched = ExhaustAir._max_schedule(
                    '{} Schedule'.format(identifier), scheds, timestep_resolution)

        # return the averaged object
        return ExhaustAir(identifier, area, fixture, 1, sched, press, eff)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from an ExhaustAir dictionary."""
        area = data['flow_per_area'] if 'flow_per_area' in data else 0
        flow_per_fixture = data['flow_per_fixture'] if 'flow_per_fixture' in data else 0
        fixture_count = data['fixture_count'] if 'fixture_count' in data else 0
        press = data['pressure_rise'] if 'pressure_rise' in data else 125
        eff = data['efficiency'] if 'efficiency' in data else 0.35
        return area, flow_per_fixture, fixture_count, press, eff

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (
            self.identifier, self.flow_per_area, self.flow_per_fixture,
            self.fixture_count, hash(self.schedule), self.pressure_rise, self.efficiency
        )

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ExhaustAir) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = ExhaustAir(
            self._identifier, self._flow_per_area, self._flow_per_fixture,
            self._fixture_count, self._schedule, self._pressure_rise, self.efficiency
        )
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __repr__(self):
        return 'ExhaustAir: {} [{} m3/s-m2] [{} m3/fixture]'.format(
            self.display_name, round(self.flow_per_area, 6),
            round(self.air_changes_per_hour, 3)
        )
