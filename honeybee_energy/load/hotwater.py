# coding=utf-8
"""Complete definition of service hot water, including schedule and load."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, clean_and_id_ep_string

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string
from ..lib.schedules import always_on
from ..properties.extension import ServiceHotWaterProperties


@lockable
class ServiceHotWater(_LoadBase):
    """A complete definition of service hot water, including schedules and load.

    Args:
        identifier: Text string for a unique ServiceHotWater ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        flow_per_area: A numerical value for the total volume flow rate of water
            per unit area of floor (L/h-m2).
        schedule: A ScheduleRuleset or ScheduleFixedInterval for the use of hot water
            over the course of the year. The type of this schedule should be
            Fractional and the fractional values will get multiplied by the
            flow_per_area to yield a complete water usage profile.
        target_temperature: The target temperature of the water out of the tap in
            Celsius. This the temperature after the hot water has been mixed
            with cold water from the water mains. The default essentially assumes
            that the flow_per_area on this object is only for water straight out
            of the water heater. (Default: 60C).
        sensible_fraction: A number between 0 and 1 for the fraction of the total
            hot water load given off as sensible heat in the zone. (Default: 0.2).
        latent_fraction: A number between 0 and 1 for the fraction of the total
            hot water load that is latent (as opposed to sensible). (Default: 0.05).

    Properties:
        * identifier
        * display_name
        * flow_per_area
        * schedule
        * target_temperature
        * sensible_fraction
        * latent_fraction
        * lost_fraction
        * standard_watts_per_area
        * user_data
    """
    __slots__ = ('_flow_per_area', '_schedule', '_target_temperature',
                 '_sensible_fraction', '_latent_fraction')
    WATER_HEAT_CAPACITY = 4179600  # volumetric heat capacity of water at 25 C (J/m3-K)

    def __init__(self, identifier, flow_per_area, schedule, target_temperature=60,
                 sensible_fraction=0.2, latent_fraction=0.05):
        """Initialize ServiceHotWater."""
        _LoadBase.__init__(self, identifier)
        self._latent_fraction = 0  # starting value so that check runs correctly

        self.flow_per_area = flow_per_area
        self.schedule = schedule
        self.target_temperature = target_temperature
        self.sensible_fraction = sensible_fraction
        self.latent_fraction = latent_fraction
        self._properties = ServiceHotWaterProperties(self)

    @property
    def flow_per_area(self):
        """Get or set the hot water volume flow rate per unit area of floor (L/h-m2)."""
        return self._flow_per_area

    @flow_per_area.setter
    def flow_per_area(self, value):
        self._flow_per_area = float_positive(value, 'hot water flow per area')

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for hot water usage."""
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for hot water ' \
            'schedule. Got {}.'.format(type(value))
        self._check_fractional_schedule_type(value, 'ServiceHotWater')
        value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def target_temperature(self):
        """Get or set the temperature out of the tap (C)."""
        return self._target_temperature

    @target_temperature.setter
    def target_temperature(self, value):
        self._target_temperature = float_in_range(
            value, 0.0, 100.0, 'hot water target temperature')

    @property
    def sensible_fraction(self):
        """Get or set the fraction of hot water heat given off as zone sensible heat."""
        return self._sensible_fraction

    @sensible_fraction.setter
    def sensible_fraction(self, value):
        self._sensible_fraction = float_in_range(
            value, 0.0, 1.0, 'hot water sensible fraction')
        self._check_fractions()

    @property
    def latent_fraction(self):
        """Get or set the fraction of hot water heat that is latent."""
        return self._latent_fraction

    @latent_fraction.setter
    def latent_fraction(self, value):
        self._latent_fraction = float_in_range(
            value, 0.0, 1.0, 'hot water latent fraction')
        self._check_fractions()

    @property
    def lost_fraction(self):
        """Get the fraction of hot water heat that is lost down the drain."""
        return 1 - self._sensible_fraction - self._latent_fraction

    @property
    def standard_watts_per_area(self):
        """Get the hot water power density (W/m2) assuming a standard mains temperature.

        Standard water mains temperature is 10C, which is the default water mains
        temperature in EnergyPlus when none is specified.
        """
        flow_m3_s_m2 = self._flow_per_area / (1000. * 3600.)
        delta_t = self.target_temperature - 10
        return flow_m3_s_m2 * self.WATER_HEAT_CAPACITY * delta_t

    def set_watts_per_area(self, watts_per_area, water_mains_temperature=10):
        """Set the volume flow rate per floor area using the hot water power density.

        Args:
            watts_per_area: The desired hot water power density (W/m2).
            water_mains_temperature: The average annual temperature of the water
                mains that supply the water heater in Celsius. This should be
                close to the average annual temperature. (Default: 10C).
        """
        delta_t = self.target_temperature - water_mains_temperature
        flow_m3_s_m2 = watts_per_area / (self.WATER_HEAT_CAPACITY * delta_t)
        self._flow_per_area = flow_m3_s_m2 * 1000. * 3600.

    def diversify(self, count, flow_stdev=20, schedule_offset=1, timestep=1,
                  schedule_indices=None):
        """Get an array of diversified ServiceHotWater derived from this "average" one.

        Approximately 2/3 of the schedules in the output objects will be offset
        from the mean by the input schedule_offset (1/3 ahead and another 1/3 behind).

        Args:
            count: An positive integer for the number of diversified objects to
                generate from this mean object.
            flow_stdev: A number between 0 and 100 for the percent of the flow_per_area
                representing one standard deviation of diversification from
                the mean. (Default 20 percent).
            schedule_offset: A positive integer for the number of timesteps at which
                the lighting schedule of the resulting objects will be shifted - roughly
                1/3 of the objects ahead and another 1/3 behind. (Default: 1).
            timestep: An integer for the number of timesteps per hour at which the
                shifting is occurring. This must be a value between 1 and 60, which
                is evenly divisible by 60. 1 indicates that each step is an hour
                while 60 indicates that each step is a minute. (Default: 1).
            schedule_indices: An optional list of integers from 0 to 2 with a length
                equal to the input count, which will be used to set whether a given
                schedule is behind (0), ahead (2), or the same (1). This can be
                used to coordinate schedules across diversified programs. If None
                a random list of integers will be genrated. (Default: None).
        """
        # generate shifted schedules and a gaussian distribution of flow_per_area
        usage_schs = self._shift_schedule(self.schedule, schedule_offset, timestep)
        stdev = self.flow_per_area * (flow_stdev / 100)
        new_loads, sch_ints = self._gaussian_values(count, self.flow_per_area, stdev)
        sch_ints = sch_ints if schedule_indices is None else schedule_indices

        # generate the new objects and return them
        new_objects = []
        for load_val, sch_int in zip(new_loads, sch_ints):
            new_obj = self.duplicate()
            new_obj.identifier = clean_and_id_ep_string(self.identifier)
            new_obj.flow_per_area = load_val
            new_obj.schedule = usage_schs[sch_int]
            new_objects.append(new_obj)
        return new_objects

    @classmethod
    def from_watts_per_area(
            cls, identifier, watts_per_area, schedule, target_temperature=60,
            sensible_fraction=0.2, latent_fraction=0.05, water_mains_temperature=10):
        """Create a ServiceHotWater object from hot water power density (W/m2).

        Args:
            identifier: Text string for a unique ServiceHotWater ID. Must be < 100
                characters and not contain any EnergyPlus special characters.
                This will be used to identify the object across a model and in
                the exported IDF.
            watts_per_area: The desired hot water power density (W/m2).
            schedule: A ScheduleRuleset or ScheduleFixedInterval for the use of hot
                water over the course of the year. The type of this schedule should be
                Fractional and the fractional values will get multiplied by the
                watts_per_area to yield a complete hot water profile.
            target_temperature: The target temperature of the water out of the tap in
                Celsius. This the temperature after the hot water has been mixed
                with cold water from the water mains. The default essentially assumes
                that the flow_per_area on this object is only for water straight out
                of the water heater. (Default: 60C).
            sensible_fraction: A number between 0 and 1 for the fraction of the total
                hot water load given off as sensible heat in the zone. (Default: 0.2).
            latent_fraction: A number between 0 and 1 for the fraction of the total
                hot water load that is latent (as opposed to sensible). (Default: 0.05).
            water_mains_temperature: The average annual temperature of the water
                mains that supply the water heater in Celsius. This should be
                close to the average annual temperature. (Default: 10C).
        """
        shw = cls(identifier, 0, schedule, target_temperature,
                  sensible_fraction, latent_fraction)
        shw.set_watts_per_area(watts_per_area, water_mains_temperature)
        return shw

    @classmethod
    def from_idf(cls, idf_string, floor_area, schedule_dict):
        """Create a ServiceHotWater object from an IDF WaterUse:Equipment string.

        Args:
            idf_string: A text string of an EnergyPlus WaterUse:Equipment definition.
            floor_area: A number for the floor area of the room to which the
                WaterUse:Equipment definition is assigned.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the ServiceHotWater object.

        Returns:
            A tuple with two elements

            -   shw: A ServiceHotWater object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the ServiceHotWater
                object should be assigned. Will be None if no zone is found.

            -   total_flow: Number for the absolute flow rate of the ServiceHotWater
                object in L/h.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'WaterUse:Equipment,')

        # extract the flow rate
        total_flow = float(ep_strs[2]) * 1000. * 3600.
        flow_per_area = total_flow / floor_area if floor_area != 0 else 0

        # extract the schedule from the string
        sched = always_on
        if len(ep_strs) > 3 and ep_strs[3] != '':
            try:
                sched = schedule_dict[ep_strs[3]]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))

        # try to extract the target temperature
        target = cls._schedule_single_value(ep_strs, 4, None, schedule_dict)
        sens = cls._schedule_single_value(ep_strs, 8, 0, schedule_dict)
        latent = cls._schedule_single_value(ep_strs, 9, 0, schedule_dict)

        # return the hot water object and the zone id if it exists
        obj_id = ep_strs[0].split('..')[0]
        zone_id = ep_strs[7] if len(ep_strs) > 7 and ep_strs[7] != '' else None
        shw = cls(obj_id, flow_per_area, sched, target, sens, latent)
        return shw, zone_id, total_flow

    @classmethod
    def from_dict(cls, data):
        """Create a ServiceHotWater object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A ServiceHotWater dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'ServiceHotWater',
            "identifier": 'Residential_SHW_015',
            "display_name": 'Residential Hot Water',
            "flow_per_area": 0.15, # how water L/h per square meter of floor area
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "target_temperature": 60, # target temperature in C
            "sensible_fraction": 0.2, # fraction of heat that is sensible
            "latent_fraction": 0.05 # fraction of heat that is latent
            }
        """
        assert data['type'] == 'ServiceHotWater', \
            'Expected ServiceHotWater dictionary. Got {}.'.format(data['type'])
        sched = cls._get_schedule_from_dict(data['schedule'])
        target, sens_fract, lat_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['flow_per_area'], sched,
                      target, sens_fract, lat_fract)
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return cls._apply_optional_dict_props(new_obj, data)

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a ServiceHotWater object from an abridged dictionary.

        Args:
            data: A ServiceHotWaterAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the ServiceHotWater object.

        .. code-block:: python

            {
            "type": 'ServiceHotWaterAbridged',
            "identifier": 'Residential_SHW_015',
            "display_name": 'Residential Hot Water',
            "flow_per_area": 0.15, # how water L/h per square meter of floor area
            "schedule": 'Residential DHW Usage', # schedule identifier
            "target_temperature": 60, # target temperature in C
            "sensible_fraction": 0.2, # fraction of heat that is sensible
            "latent_fraction": 0.05 # fraction of heat that is latent
            }
        """
        assert data['type'] == 'ServiceHotWaterAbridged', \
            'Expected ServiceHotWaterAbridged dictionary. Got {}.'.format(data['type'])
        try:
            sched = schedule_dict[data['schedule']]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        target, sens_fract, lat_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['flow_per_area'], sched,
                      target, sens_fract, lat_fract)
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return cls._apply_optional_dict_props(new_obj, data)

    def to_idf(self, room):
        """IDF string representation of ServiceHotWater object.

        Note that this method only outputs a string for the WaterUse:Equipment
        object and a Schedule:Constant for the target temperature.  Thus, to write
        everything needed to describe the object into an IDF, this object's
        schedule must also be written.

        Args:
            room: The honeybee Room to which this ServiceHotWater object is being
                applied. This is needed for both to convert the flow_per_area to
                an absolute flow and to assign the hot water object to the Room
                (such that sensible/latent heat gains are transferred to the Room).

        Returns:
            A tuple with two values.

            -   water_use: A WaterUse:Equipment string for the ServiceHotWater.

            -   schedules: A list of Schedule:Constant strings for the schedules
                needed to describe the target temperatures as well as the sensible
                and latent fractions.
        """
        # create the Schedule:Constant strings
        u_id = '{}..{}'.format(self.identifier, room.identifier)
        s_com, s_obj = ('name', 'schedule type limits', 'value'), 'Schedule:Constant'
        schedules = []
        sens_sch, lat_sch = '', ''
        hot_fields = ('{}_SHW_Target'.format(u_id), '', self.target_temperature)
        schedules.append(generate_idf_string(s_obj, hot_fields, s_com))
        if self.sensible_fraction != 0:
            sens_sch = '{}_SHW_Sensible'.format(u_id)
            sens_fields = (sens_sch, '', self.sensible_fraction)
            schedules.append(generate_idf_string(s_obj, sens_fields, s_com))
        if self.latent_fraction != 0:
            lat_sch = '{}_SHW_Latent'.format(u_id)
            lat_fields = (lat_sch, '', self.latent_fraction)
            schedules.append(generate_idf_string(s_obj, lat_fields, s_com))

        # create the Water Use string
        total_flow = (self.flow_per_area / 3600000.) * room.floor_area
        values = (u_id, 'General', total_flow, self.schedule.identifier, hot_fields[0],
                  hot_fields[0], '', room.identifier, sens_sch, lat_sch)
        comments = ('name', 'end use subcategory', 'peak flow rate {m/s}',
                    'schedule name', 'target temp schedule', 'hot water temp schedule',
                    'cold water temp schedule', 'zone name',
                    'sensible fraction', 'latent fraction')
        water_use = generate_idf_string('WaterUse:Equipment', values, comments)
        return water_use, schedules

    def to_dict(self, abridged=False):
        """ServiceHotWater dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. (Default: False).
        """
        base = {'type': 'ServiceHotWater'} if not abridged else \
            {'type': 'ServiceHotWaterAbridged'}
        base['identifier'] = self.identifier
        base['flow_per_area'] = self.flow_per_area
        base['target_temperature'] = self.target_temperature
        base['sensible_fraction'] = self.sensible_fraction
        base['latent_fraction'] = self.latent_fraction
        base['schedule'] = self.schedule.to_dict() if not \
            abridged else self.schedule.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    @staticmethod
    def average(identifier, hot_waters, weights=None, timestep_resolution=1):
        """Get a ServiceHotWater object that's a weighted average between other objects.

        Args:
            identifier: Text string for a unique ID for the new averaged ServiceHotWater.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            hot_waters: A list of ServiceHotWater objects that will be averaged
                together to make a new ServiceHotWater.
            weights: An optional list of fractional numbers with the same length
                as the input hot_waters. These will be used to weight each of the
                ServiceHotWater objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average flow_per_area will
                assume 0 for the unaccounted fraction of the weights.
                If None, the objects will be weighted equally. (Default: None).
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                (Default: 1).
        """
        weights, u_weights = ServiceHotWater._check_avg_weights(
            hot_waters, weights, 'ServiceHotWater')

        # calculate the average values
        flow_d = sum([s.flow_per_area * w for s, w in zip(hot_waters, weights)])
        target = sum([s.target_temperature * w for s, w in zip(hot_waters, u_weights)])
        sen_fract = sum([s.sensible_fraction * w for s, w in zip(hot_waters, u_weights)])
        lat_fract = sum([s.latent_fraction * w for s, w in zip(hot_waters, u_weights)])

        # calculate the average schedules
        sched = ServiceHotWater._average_schedule(
            '{} Schedule'.format(identifier), [s.schedule for s in hot_waters],
            u_weights, timestep_resolution)

        # return the averaged object
        return ServiceHotWater(identifier, flow_d, sched, target, sen_fract, lat_fract)

    def _check_fractions(self):
        """Check that the fractions sum to less than 1."""
        tot = (self._sensible_fraction, self._latent_fraction)
        assert sum(tot) <= 1 + 1e-9, 'Sum of equipment sensible_fraction and ' \
            'latent_fraction ({}) is greater than 1.'.format(sum(tot))

    @staticmethod
    def _schedule_single_value(ep_strs, index, default, schedule_dict):
        """Extract a single value from a schedule."""
        if len(ep_strs) > index and ep_strs[index] != '':
            try:
                t_sched = schedule_dict[ep_strs[index]]
                if isinstance(t_sched, ScheduleRuleset):
                    return t_sched.default_day_schedule.values[0]
                else:  # FixedInterval schedule
                    return t_sched.values[0]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        return default

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from an ServiceHotWater dictionary."""
        target = data['target_temperature'] if 'target_temperature' in data else 60
        sens_fract = data['sensible_fraction'] if 'sensible_fraction' in data else 0.2
        lat_fract = data['latent_fraction'] if 'latent_fraction' in data else 0.05
        return target, sens_fract, lat_fract

    @staticmethod
    def _apply_optional_dict_props(new_obj, data):
        """Apply optional properties like display_name to an object from a dictionary."""
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.flow_per_area, hash(self.schedule),
                self.target_temperature, self.sensible_fraction, self.latent_fraction)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ServiceHotWater) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = ServiceHotWater(
            self.identifier, self.flow_per_area, self.schedule,
            self.target_temperature, self.sensible_fraction, self.latent_fraction)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def __repr__(self):
        return 'ServiceHotWater: {} [{} L/h-m2] [schedule: {}]'.format(
            self.identifier, self.flow_per_area, self.schedule.identifier)
