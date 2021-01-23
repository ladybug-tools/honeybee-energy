# coding=utf-8
"""Complete definition of people in a simulation, including schedule and load."""
from __future__ import division

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string

import honeybee_energy.lib.schedules as _sched_lib

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, clean_and_id_ep_string
from honeybee.altnumber import autocalculate


@lockable
class People(_LoadBase):
    """A complete definition of people, including schedules and load.

    Args:
        identifier: Text string for a unique People ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        people_per_area: A numerical value for the number of people per square
            meter of floor area.
        occupancy_schedule: A ScheduleRuleset or ScheduleFixedInterval for the
            occupancy over the course of the year. The type of this schedule
            should be Fractional and the fractional values will get multiplied by
            the people_per_area to yield a complete occupancy profile.
        activity_schedule: A ScheduleRuleset or ScheduleFixedInterval for the
            activity of the occupants over the course of the year. The type of
            this schedule should be ActivityLevel and the values of the schedule equal
            to the number of Watts given off by an individual person in the room.
            If None, it will a default constant schedule with 120 Watts per person
            will be used, which is typical of awake, adult humans who are seated.
        radiant_fraction: A number between 0 and 1 for the fraction of the
            sensible heat given off by people that is radiant (as opposed to
            convective). (Default: 0.3).
        latent_fraction: A number between 0 and 1 for the fraction of the heat
            given off by people that is latent (as opposed to sensible). This
            input can also be an Autocalculate object, which will automatically
            estimate the latent fraction based on the occupant's activity level.
            (Default: autocalculate).

    Properties:
        * identifier
        * display_name
        * people_per_area
        * area_per_person
        * occupancy_schedule
        * activity_schedule
        * radiant_fraction
        * latent_fraction
    """
    __slots__ = ('_people_per_area', '_occupancy_schedule', '_activity_schedule',
                 '_radiant_fraction', '_latent_fraction')

    def __init__(self, identifier, people_per_area, occupancy_schedule,
                 activity_schedule=None,
                 radiant_fraction=0.3, latent_fraction=autocalculate):
        """Initialize People."""
        _LoadBase.__init__(self, identifier)
        self.people_per_area = people_per_area
        self.occupancy_schedule = occupancy_schedule
        self.activity_schedule = activity_schedule
        self.radiant_fraction = radiant_fraction
        self.latent_fraction = latent_fraction

    @property
    def people_per_area(self):
        """Get or set the number of people per square meter of floor area."""
        return self._people_per_area

    @people_per_area.setter
    def people_per_area(self, value):
        self._people_per_area = float_positive(value, 'people per area')

    @property
    def area_per_person(self):
        """Get or set the number of square meters of floor area per person."""
        return 1 / self._people_per_area if self._people_per_area != 0 else 0

    @area_per_person.setter
    def area_per_person(self, value):
        if float(value) != 0:
            self._people_per_area = 1 / float_positive(value, 'area per person')
        else:
            self._people_per_area = 0

    @property
    def occupancy_schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for the occupancy."""
        return self._occupancy_schedule

    @occupancy_schedule.setter
    def occupancy_schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for People ' \
            'occupancy_schedule. Got {}.'.format(type(value))
        self._check_fractional_schedule_type(value, 'Occupancy')
        value.lock()   # lock editing in case schedule has multiple references
        self._occupancy_schedule = value

    @property
    def activity_schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for the occupancy."""
        return self._activity_schedule

    @activity_schedule.setter
    def activity_schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected ScheduleRuleset or ScheduleFixedInterval for People' \
                ' activity_schedule. Got {}.'.format(type(value))
            self._check_activity_schedule_type(value)
            value.lock()   # lock editing in case schedule has multiple references
            self._activity_schedule = value
        else:
            self._activity_schedule = _sched_lib.seated_activity

    @property
    def radiant_fraction(self):
        """Get or set the radiant fraction of sensible heat given off by people."""
        return self._radiant_fraction

    @radiant_fraction.setter
    def radiant_fraction(self, value):
        self._radiant_fraction = float_in_range(
            value, 0.0, 1.0, 'people radiant fraction')

    @property
    def latent_fraction(self):
        """Get or set the fraction of the heat given off by people that is latent."""
        return self._latent_fraction

    @latent_fraction.setter
    def latent_fraction(self, value):
        if value == autocalculate:
            self._latent_fraction = autocalculate
        else:
            self._latent_fraction = float_in_range(
                value, 0.0, 1.0, 'people latent fraction')

    def diversify(self, count, occupancy_stdev=20, schedule_offset=1, timestep=1,
                  schedule_indices=None):
        """Get an array of diversified People derived from this "average" one.

        Approximately 2/3 of the schedules in the output objects will be offset
        from the mean by the input schedule_offset (1/3 ahead and another 1/3 behind).

        Args:
            count: An positive integer for the number of diversified objects to
                generate from this mean object.
            occupancy_stdev: A number between 0 and 100 for the percent of the
                occupancy people_per_area representing one standard deviation
                of diversification from the mean. (Default 20 percent).
            schedule_offset: A positive integer for the number of timesteps at which
                the occupancy schedule of the resulting objects will be shifted - roughly
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
        # generate shifted schedules and a gaussian distribution of people_per_area
        occ_schs = self._shift_schedule(
            self.occupancy_schedule, schedule_offset, timestep)
        stdev = self.people_per_area * (occupancy_stdev / 100)
        new_loads, sch_ints = self._gaussian_values(count, self.people_per_area, stdev)
        sch_ints = sch_ints if schedule_indices is None else schedule_indices

        # generate the new objects and return them
        new_objects = []
        for load_val, sch_int in zip(new_loads, sch_ints):
            new_obj = self.duplicate()
            new_obj.identifier = clean_and_id_ep_string(self.identifier)
            new_obj.people_per_area = load_val
            new_obj.occupancy_schedule = occ_schs[sch_int]
            new_objects.append(new_obj)
        return new_objects

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create an People object from an EnergyPlus IDF text string.

        Note that the People idf_string must use the 'people per zone floor area'
        method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus people definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the People object.

        Returns:
            A tuple with four elements

            -   people: A People object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the People
                object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'People,')
        assert ep_strs[3].lower() == 'people/area', \
            'People must use People/Area method to be loaded from IDF to honeybee.'

        # extract the properties from the string
        lat_fract = autocalculate if ep_strs[8] == '' or \
            ep_strs[8].lower() == 'autocalculate' else 1 - float(ep_strs[8])
        rad_fract = ep_strs[7] if ep_strs[7] != '' else 0.3

        # extract the schedules from the string
        occ_sched, activity_sched = cls._get_occ_act_schedules_from_dict(
            schedule_dict, ep_strs[2], ep_strs[9])

        # return the people object and the zone id for the people object
        obj_id = ep_strs[0].split('..')[0]
        zone_id = ep_strs[1]
        people = cls(obj_id, ep_strs[5], occ_sched, activity_sched,
                     rad_fract, lat_fract)
        return people, zone_id

    @classmethod
    def from_dict(cls, data):
        """Create a People object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A People dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'People',
            "identifier": 'Open_Office_People_005_03_02',
            "display_name": 'Office People',
            "people_per_area": 0.05, # number of people per square meter of floor area
            "occupancy_schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "activity_schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "radiant_fraction": 0.3, # fraction of sensible heat that is radiant
            "latent_fraction": 0.2 # fraction of total heat that is latent
            }
        """
        assert data['type'] == 'People', \
            'Expected People dictionary. Got {}.'.format(data['type'])
        occ_sched = cls._get_schedule_from_dict(data['occupancy_schedule'])
        act_sched = cls._get_schedule_from_dict(data['activity_schedule']) if \
            'activity_schedule' in data and data['activity_schedule'] is not None else None
        rad_fract, lat_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['people_per_area'], occ_sched, act_sched,
                      rad_fract, lat_fract)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a People object from an abridged dictionary.

        Args:
            data: A PeopleAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the People object.

        .. code-block:: python

            {
            "type": "PeopleAbridged",
            "identifier": 'Open_Office_People_005_03_02',
            "display_name": 'Office People',
            "people_per_area": 0.05, # number of people per square meter of floor area
            "occupancy_schedule": "Office Occupancy", # Schedule identifier
            "activity_schedule": "Office Activity", # Schedule identifier
            "radiant_fraction": 0.3, # fraction of sensible heat that is radiant
            "latent_fraction": 0.2 # fraction of total heat that is latent
            }
        """
        assert data['type'] == 'PeopleAbridged', \
            'Expected PeopleAbridged dictionary. Got {}.'.format(data['type'])
        act_sch_id = data['activity_schedule'] if 'activity_schedule' in data and \
            data['activity_schedule'] is not None else ''
        occ_sched, activity_sched = cls._get_occ_act_schedules_from_dict(
            schedule_dict, data['occupancy_schedule'], act_sch_id)
        rad_fract, lat_fract = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['people_per_area'], occ_sched,
                      activity_sched, rad_fract, lat_fract)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of People object.

        Note that this method only outputs a single string for the People object and,
        to write everything needed to describe the object into an IDF, this object's
        occupancy_schedule and activity_schedule must also be written. This is done
        to give more control over the export process since you typically want to check
        whether these schedules are used by multiple People objects and write the
        schedule into the IDF only once.

        Args:
            zone_identifier: Text for the zone identifier that the People object
                is assigned to.
        """
        sens_fract = 'autocalculate' if self.latent_fraction == autocalculate else \
            1 - float(self.latent_fraction)
        values = ('{}..{}'.format(self.identifier, zone_identifier), zone_identifier,
                  self.occupancy_schedule.identifier, 'People/Area',
                  '', self.people_per_area, '', self.radiant_fraction, sens_fract,
                  self.activity_schedule.identifier)
        comments = ('name', 'zone name', 'occupancy schedule name', 'occupancy method',
                    'number of people {ppl}', 'people per floor area {ppl/m2}',
                    'floor area per person {m2/ppl}', 'radiant fration',
                    'sensible heat fraction', 'activity schedule name')
        return generate_idf_string('People', values, comments)

    def to_dict(self, abridged=False):
        """People dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        base = {'type': 'People'} if not abridged else {'type': 'PeopleAbridged'}
        base['identifier'] = self.identifier
        base['people_per_area'] = self.people_per_area
        base['radiant_fraction'] = self.radiant_fraction
        base['latent_fraction'] = self.latent_fraction if \
            isinstance(self.latent_fraction, float) else self.latent_fraction.to_dict()
        if not abridged:
            base['occupancy_schedule'] = self.occupancy_schedule.to_dict()
            base['activity_schedule'] = self.activity_schedule.to_dict()
        else:
            base['occupancy_schedule'] = self.occupancy_schedule.identifier
            base['activity_schedule'] = self.activity_schedule.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    @staticmethod
    def average(identifier, peoples, weights=None, timestep_resolution=1):
        """Get a People object that's a weighted average between other People objects.

        Args:
            identifier: Text string for a unique ID for the new averaged People.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            peoples: A list of People objects that will be averaged together to make
                a new People.
            weights: An optional list of fractional numbers with the same length
                as the input peoples. These will be used to weight each of the People
                objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average people_per_area will
                assume 0 for the unaccounted fraction of the weights.
                If None, the objects will be weighted equally. Default: None.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        weights, u_weights = People._check_avg_weights(peoples, weights, 'People')

        # calculate the average values
        ppl_area = sum([ppl.people_per_area * w for ppl, w in zip(peoples, weights)])
        rad_fract = sum([ppl.radiant_fraction * w for ppl, w in zip(peoples, u_weights)])
        lat_fracts = []
        for i, ppl in enumerate(peoples):
            if ppl.latent_fraction == autocalculate:
                lat_fract = autocalculate
                break
            lat_fracts.append(ppl.latent_fraction * u_weights[i])
        else:
            lat_fract = sum(lat_fracts)

        # calculate the average schedules
        occ_sched = People._average_schedule(
            '{}_Occ Schedule'.format(identifier),
            [ppl.occupancy_schedule for ppl in peoples], u_weights, timestep_resolution)
        act_sched = People._average_schedule(
            '{}_Act Schedule'.format(identifier),
            [ppl.activity_schedule for ppl in peoples], u_weights, timestep_resolution)

        # return the averaged people object
        return People(identifier, ppl_area, occ_sched, act_sched, rad_fract, lat_fract)

    def _check_activity_schedule_type(self, schedule):
        """Check that the type limit of an input schedule is fractional."""
        if schedule.schedule_type_limit is not None:
            t_lim = schedule.schedule_type_limit
            assert t_lim.unit_type == 'ActivityLevel', 'Activity schedule must have a ' \
                'unit type of ActivityLevel. Got a schedule' \
                ' of unit type [{}].'.format(t_lim.unit_type)
            assert t_lim.lower_limit == 0, 'Activity schedule should have either ' \
                'no type limit or a lower limit of 0. Got a schedule type with ' \
                'lower limit [{}].'.format(t_lim.lower_limit)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from a People dictionary."""
        rad_fract = data['radiant_fraction'] if 'radiant_fraction' in data else 0.3
        lat_fract = autocalculate if 'latent_fraction' not in data or \
            data['latent_fraction'] == autocalculate.to_dict() else data['latent_fraction']
        return rad_fract, lat_fract

    @staticmethod
    def _get_occ_act_schedules_from_dict(schedule_dict, occ_sch_id, act_sch_id):
        """Get schedule objects from a dictionary."""
        try:
            occ_sched = schedule_dict[occ_sch_id]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        if act_sch_id.lower() == 'seated adult activity':
            activity_sched = None
        else:
            try:
                activity_sched = schedule_dict[act_sch_id]
            except KeyError as e:
                raise ValueError('Failed to find {} in the People schedule_dict.'.format(e))
        return occ_sched, activity_sched

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.people_per_area, hash(self.occupancy_schedule),
                hash(self.activity_schedule), self.radiant_fraction,
                str(self.latent_fraction))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, People) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = People(
            self.identifier, self.people_per_area, self.occupancy_schedule,
            self.activity_schedule, self.radiant_fraction, self.latent_fraction)
        new_obj._display_name = self._display_name
        return new_obj

    def __repr__(self):
        return 'People: {} [{} people/m2] [schedule: {}]'.format(
            self.display_name, round(self.people_per_area, 3),
            self.occupancy_schedule.display_name)
