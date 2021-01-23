# coding=utf-8
"""Complete definition of lighting in a simulation, including schedule and load."""
from __future__ import division

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, clean_and_id_ep_string


@lockable
class Lighting(_LoadBase):
    """A complete definition of lighting, including schedules and load.

    Args:
        identifier: Text string for a unique Lighting ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        watts_per_area: A numerical value for the lighting power density in
            Watts per square meter of floor area.
        schedule: A ScheduleRuleset or ScheduleFixedInterval for the use of lights
            over the course of the year. The type of this schedule should be
            Fractional and the fractional values will get multiplied by the
            watts_per_area to yield a complete lighting profile.
        return_air_fraction: A number between 0 and 1 for the fraction of the total
            lighting load that goes into the zone return air (into the zone outlet
            node). (Default: 0.0). (representative of pendant lighting).
        radiant_fraction: A number between 0 and 1 for the fraction of the total
            lighting load given off as long wave radiant heat.
            (Default: 0.32). (representative of pendant lighting).
        visible_fraction: A number between 0 and 1 for the fraction of the total
            lighting load given off as short wave visible light.
            (Default: 0.25).  (representative of pendant lighting).

    Properties:
        * identifier
        * display_name
        * watts_per_area
        * schedule
        * return_air_fraction
        * radiant_fraction
        * visible_fraction
        * convected_fraction
        * baseline_watts_per_area
    """
    __slots__ = ('_watts_per_area', '_schedule', '_return_air_fraction',
                 '_radiant_fraction', '_visible_fraction', '_baseline_watts_per_area')

    def __init__(self, identifier, watts_per_area, schedule, return_air_fraction=0.0,
                 radiant_fraction=0.32, visible_fraction=0.25):
        """Initialize Lighting."""
        _LoadBase.__init__(self, identifier)
        self._radiant_fraction = 0  # starting value so that check runs correctly
        self._visible_fraction = 0  # starting value so that check runs correctly

        self.watts_per_area = watts_per_area
        self.schedule = schedule
        self.return_air_fraction = return_air_fraction
        self.radiant_fraction = radiant_fraction
        self.visible_fraction = visible_fraction
        self.baseline_watts_per_area = None  # can be set by the user later

    @property
    def watts_per_area(self):
        """Get or set the lighting power density in Watts/square meter of floor area."""
        return self._watts_per_area

    @watts_per_area.setter
    def watts_per_area(self, value):
        self._watts_per_area = float_positive(value, 'lighting watts per area')

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for lighting usage."""
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for Lighting ' \
            'schedule. Got {}.'.format(type(value))
        self._check_fractional_schedule_type(value, 'Lighting')
        value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def return_air_fraction(self):
        """Get or set the fraction of lighting heat that goes into the return air."""
        return self._return_air_fraction

    @return_air_fraction.setter
    def return_air_fraction(self, value):
        if value is not None:
            self._return_air_fraction = float_in_range(
                value, 0.0, 1.0, 'lighting return air fraction')
        else:
            self._return_air_fraction = 0
        self._check_fractions()

    @property
    def radiant_fraction(self):
        """Get or set the fraction of lighting heat given off as long wave radiation."""
        return self._radiant_fraction

    @radiant_fraction.setter
    def radiant_fraction(self, value):
        if value is not None:
            self._radiant_fraction = float_in_range(
                value, 0.0, 1.0, 'lighting radiant fraction')
        else:
            self._radiant_fraction = 0.32
        self._check_fractions()

    @property
    def visible_fraction(self):
        """Get or set the fraction of lighting heat given off as visible light."""
        return self._visible_fraction

    @visible_fraction.setter
    def visible_fraction(self, value):
        if value is not None:
            self._visible_fraction = float_in_range(
                value, 0.0, 1.0, 'lighting visible fraction')
        else:
            self._visible_fraction = 0.25
        self._check_fractions()

    @property
    def convected_fraction(self):
        """Get the fraction of lighting heat that convects to the zone air."""
        tot = (self._return_air_fraction, self._radiant_fraction, self._visible_fraction)
        return 1 - sum(tot)

    @property
    def baseline_watts_per_area(self):
        """Get or set the baseline lighting power density in W/m2 of floor area.

        This baseline is useful to track how much better the installed lights are
        in comparison to a standard like ASHRAE 90.1. If set to None, it will
        default to 11.84029 W/m2, which is that ASHRAE 90.1-2004 baseline for
        an office.
        """
        return self._baseline_watts_per_area if self._baseline_watts_per_area \
            is not None else 11.84029

    @baseline_watts_per_area.setter
    def baseline_watts_per_area(self, value):
        if value is not None:
            value = float_positive(value, 'lighting baseline watts per area')
        self._baseline_watts_per_area = value

    def diversify(self, count, watts_stdev=20, schedule_offset=1, timestep=1,
                  schedule_indices=None):
        """Get an array of diversified Lighting derived from this "average" one.

        Approximately 2/3 of the schedules in the output objects will be offset
        from the mean by the input schedule_offset (1/3 ahead and another 1/3 behind).

        Args:
            count: An positive integer for the number of diversified objects to
                generate from this mean object.
            watts_stdev: A number between 0 and 100 for the percent of the
                watts_per_area representing one standard deviation
                of diversification from the mean. (Default 20 percent).
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
        # generate shifted schedules and a gaussian distribution of watts_per_area
        usage_schs = self._shift_schedule(self.schedule, schedule_offset, timestep)
        stdev = self.watts_per_area * (watts_stdev / 100)
        new_loads, sch_ints = self._gaussian_values(count, self.watts_per_area, stdev)
        sch_ints = sch_ints if schedule_indices is None else schedule_indices

        # generate the new objects and return them
        new_objects = []
        for load_val, sch_int in zip(new_loads, sch_ints):
            new_obj = self.duplicate()
            new_obj.identifier = clean_and_id_ep_string(self.identifier)
            new_obj.watts_per_area = load_val
            new_obj.schedule = usage_schs[sch_int]
            new_objects.append(new_obj)
        return new_objects

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create a Lighting object from an EnergyPlus IDF text string.

        Note that the Lighting idf_string must use the 'watts per zone floor area'
        method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus lighting definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the Lighting object.

        Returns:
            A tuple with two elements

            -   lighting: A Lighting object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the Lighting
                object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'Lights,')
        assert ep_strs[3].lower() == 'watts/area', \
            'Lights must use Watts/Area method to be loaded from IDF to honeybee.'

        # extract the properties from the string
        return_fract = 0
        rad_fract = 0
        vis_fract = 0
        try:
            return_fract = ep_strs[7] if ep_strs[7] != '' else 0
            rad_fract = ep_strs[8] if ep_strs[8] != '' else 0
            vis_fract = ep_strs[9] if ep_strs[9] != '' else 0
        except IndexError:
            pass  # shorter lighting definition lacking fractions

        # extract the schedules from the string
        try:
            sched = schedule_dict[ep_strs[2]]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))

        # return the lighting object and the zone id for the lighting object
        obj_id = ep_strs[0].split('..')[0]
        zone_id = ep_strs[1]
        lighting = cls(obj_id, ep_strs[5], sched, return_fract, rad_fract, vis_fract)
        return lighting, zone_id

    @classmethod
    def from_dict(cls, data):
        """Create a Lighting object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A Lighting dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'Lighting',
            "identifier": 'Open_Office_Lighting_100_0_032_025',
            "display_name": 'Office Lighting',
            "watts_per_area": 10, # lighting watts per square meter of floor area
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "return_air_fraction": 0, # fraction of heat going to return air
            "radiant_fraction": 0.32, # fraction of heat that is long wave radiant
            "visible_fraction": 0.25 # fraction of heat that is short wave visible
            }
        """
        assert data['type'] == 'Lighting', \
            'Expected Lighting dictionary. Got {}.'.format(data['type'])
        sched = cls._get_schedule_from_dict(data['schedule'])
        ret_fract, rad_fract, vis_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['watts_per_area'], sched,
                      ret_fract, rad_fract, vis_fract)
        return cls._apply_optional_dict_props(new_obj, data)

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a Lighting object from an abridged dictionary.

        Args:
            data: A LightingAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Lighting object.

        .. code-block:: python

            {
            "type": 'LightingAbridged',
            "identifier": 'Open_Office_Lighting_100_0_032_025',
            "display_name": 'Office Lighting',
            "watts_per_area": 10, # lighting watts per square meter of floor area
            "schedule": "Office Lighting Schedule", # Schedule identifier
            "return_air_fraction": 0, # fraction of heat going to return air
            "radiant_fraction": 0.32, # fraction of heat that is long wave radiant
            "visible_fraction": 0.25 # fraction of heat that is short wave visible
            }
        """
        assert data['type'] == 'LightingAbridged', \
            'Expected LightingAbridged dictionary. Got {}.'.format(data['type'])
        try:
            sched = schedule_dict[data['schedule']]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        ret_fract, rad_fract, vis_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['watts_per_area'], sched,
                      ret_fract, rad_fract, vis_fract)
        return cls._apply_optional_dict_props(new_obj, data)

    def to_idf(self, zone_identifier):
        """IDF string representation of Lighting object.

        Note that this method only outputs a single string for the Lights object and,
        to write everything needed to describe the object into an IDF, this object's
        schedule must also be written. This is done to give more control over the
        export process since you typically want to check whether these schedules are
        used by multiple Lighting objects and write the schedule into the IDF only once.

        Args:
            zone_identifier: Text for the zone identifier that the Lights object
                is assigned to.
        """
        values = ('{}..{}'.format(self.identifier, zone_identifier), zone_identifier,
                  self.schedule.identifier, 'Watts/Area', '', self.watts_per_area, '',
                  self.return_air_fraction, self.radiant_fraction, self.visible_fraction)
        comments = ('name', 'zone name', 'schedule name', 'lighting level method',
                    'lighting power level {W}', 'lighting per floor area {W/m2}',
                    'lighting per person {W/ppl}', 'return air fraction',
                    'radiant fration', 'visible fraction')
        return generate_idf_string('Lights', values, comments)

    def to_dict(self, abridged=False):
        """Lighting dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        base = {'type': 'Lighting'} if not abridged else {'type': 'LightingAbridged'}
        base['identifier'] = self.identifier
        base['watts_per_area'] = self.watts_per_area
        base['return_air_fraction'] = self.return_air_fraction
        base['radiant_fraction'] = self.radiant_fraction
        base['visible_fraction'] = self.visible_fraction
        base['schedule'] = self.schedule.to_dict() if not \
            abridged else self.schedule.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._baseline_watts_per_area is not None:
            base['baseline_watts_per_area'] = self._baseline_watts_per_area
        return base

    @staticmethod
    def average(identifier, lightings, weights=None, timestep_resolution=1):
        """Get a Lighting object that's a weighted average between other Lighting objects.

        Args:
            identifier: Text string for a unique ID for the new averaged Lighting.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            lightings: A list of Lighting objects that will be averaged together to make
                a new Lighting.
            weights: An optional list of fractional numbers with the same length
                as the input lightings. These will be used to weight each of the
                Lighting objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average watts_per_area will
                assume 0 for the unaccounted fraction of the weights.
                If None, the objects will be weighted equally. Default: None.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        weights, u_weights = Lighting._check_avg_weights(lightings, weights, 'Lighting')

        # calculate the average values
        lpd = sum([li.watts_per_area * w for li, w in zip(lightings, weights)])
        ret_fract = sum([li.return_air_fraction * w for li, w in zip(lightings, u_weights)])
        rad_fract = sum([li.radiant_fraction * w for li, w in zip(lightings, u_weights)])
        vis_fract = sum([li.visible_fraction * w for li, w in zip(lightings, u_weights)])

        # calculate the average schedules
        sched = Lighting._average_schedule(
            '{} Schedule'.format(identifier), [li.schedule for li in lightings],
            u_weights, timestep_resolution)

        # return the averaged lighting object
        return Lighting(identifier, lpd, sched, ret_fract, rad_fract, vis_fract)

    def _check_fractions(self):
        tot = (self._return_air_fraction, self._radiant_fraction, self._visible_fraction)
        assert sum(tot) <= 1 + 1e-9, 'Sum of lighting return_air_fraction, ' \
            'radiant_fraction and visible_fraction ({}) is greater than ' \
            '1.'.format(sum(tot))

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from a Lighting dictionary."""
        ret_fract = data['return_air_fraction'] if 'return_air_fraction' in data else 0
        rad_fract = data['radiant_fraction'] if 'radiant_fraction' in data else 0.32
        vis_fract = data['visible_fraction'] if 'visible_fraction' in data else 0.25
        return ret_fract, rad_fract, vis_fract

    @staticmethod
    def _apply_optional_dict_props(new_obj, data):
        """Apply optional properties like display_name to an object from a dictionary."""
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'baseline_watts_per_area' in data and \
                data['baseline_watts_per_area'] is not None:
            new_obj.baseline_watts_per_area = data['baseline_watts_per_area']
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.watts_per_area, hash(self.schedule),
                self.return_air_fraction, self.radiant_fraction, self.visible_fraction)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Lighting) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = Lighting(
            self.identifier, self.watts_per_area, self.schedule,
            self.return_air_fraction, self.radiant_fraction, self.visible_fraction)
        new_obj._display_name = self._display_name
        new_obj._baseline_watts_per_area = self._baseline_watts_per_area
        return new_obj

    def __repr__(self):
        return 'Lighting: {} [{} W/m2] [schedule: {}]'.format(
            self.display_name, round(self.watts_per_area, 1),
            self.schedule.display_name)
