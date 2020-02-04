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
from honeybee.typing import float_in_range, float_positive
from honeybee.altnumber import autocalculate


@lockable
class People(_LoadBase):
    """A complete definition of people, including schedules and load.

    Properties:
        * name
        * people_per_area
        * area_per_person
        * occupancy_schedule
        * activity_schedule
        * radiant_fraction
        * latent_fraction
    """
    __slots__ = ('_people_per_area', '_occupancy_schedule', '_activity_schedule',
                 '_radiant_fraction', '_latent_fraction')

    def __init__(self, name, people_per_area, occupancy_schedule, activity_schedule=None,
                 radiant_fraction=0.3, latent_fraction=autocalculate):
        """Initialize People.

        Args:
            name: Text string for the people definition name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            people_per_area: A numerical value for the number of people per square
                meter of floor area.
            occupancy_schedule: A ScheduleRuleset or ScheduleFixedInterval for the
                occupancy over the course of the year. The type of this schedule
                should be Fractional and the fractional values will get multiplied by
                the people_per_area to yield a complete occupancy profile.
            activity_schedule: A ScheduleRuleset or ScheduleFixedInterval for the
                activity of the occupants over the course of the year. The type of
                this schedule should be Power and the values of the schedule equal
                to the number of Watts given off by an individual person in the room.
                If None, it will a default constant schedule with 120 Watts per person
                will be used, which is typical of awake, adult humans who are seated.
            radiant_fraction: A number between 0 and 1 for the fraction of the sensible
                heat given off by people that is radiant (as opposed to convective).
                Default: 0.3.
            latent_fraction: A number between 0 and 1 for the fraction of the heat
                given off by people that is latent (as opposed to sensible). This
                input can also be an Autocalculate object, which will automatically
                estimate the latent fraction based on the occupant's activity level.
                Default: autocalculate.
        """
        _LoadBase.__init__(self, name)
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

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create an People object from an EnergyPlus IDF text string.

        Note that the People idf_string must use the 'people per zone floor area'
        method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus people definition.
            schedule_dict: A dictionary with schedule names as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the People object.

        Returns:
            people: A People object loaded from the idf_string.
            zone_name: The name of the zone to which the People object should
                be assigned.
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

        # return the people object and the zone name for the people object
        obj_name = ep_strs[0].split('..')[0]
        zone_name = ep_strs[1]
        people = cls(obj_name, ep_strs[5], occ_sched, activity_sched,
                     rad_fract, lat_fract)
        return people, zone_name

    @classmethod
    def from_dict(cls, data):
        """Create a People object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A People dictionary in following the format below.

        .. code-block:: json

            {
            "type": 'People',
            "name": 'Open Office People',
            "people_per_area": 0.05, // number of people per square meter of floor area
            "occupancy_schedule": {}, // ScheduleRuleset/ScheduleFixedInterval dictionary
            "activity_schedule": {}, // ScheduleRuleset/ScheduleFixedInterval dictionary
            "radiant_fraction": 0.3, // fraction of sensible heat that is radiant
            "latent_fraction": 0.2 // fraction of total heat that is latent
            }
        """
        assert data['type'] == 'People', \
            'Expected People dictionary. Got {}.'.format(data['type'])
        occ_sched = cls._get_schedule_from_dict(data['occupancy_schedule'])
        act_sched = cls._get_schedule_from_dict(data['activity_schedule']) if \
            'activity_schedule' in data and data['activity_schedule'] is not None else None
        rad_fract, lat_fract = cls._optional_dict_keys(data)
        return cls(data['name'], data['people_per_area'], occ_sched, act_sched,
                   rad_fract, lat_fract)

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a People object from an abridged dictionary.

        Args:
            data: A PeopleAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule names as keys and honeybee schedule
                objects as values (either ScheduleRuleset or ScheduleFixedInterval).
                These will be used to assign the schedules to the People object.

        .. code-block:: json

            {
            "type": "PeopleAbridged",
            "name": "Open Office People",
            "people_per_area": 0.05, // number of people per square meter of floor area
            "occupancy_schedule": "Office Occupancy", // Schedule name
            "activity_schedule": "Office Activity", // Schedule name
            "radiant_fraction": 0.3, // fraction of sensible heat that is radiant
            "latent_fraction": 0.2 // fraction of total heat that is latent
            }
        """
        assert data['type'] == 'PeopleAbridged', \
            'Expected PeopleAbridged dictionary. Got {}.'.format(data['type'])
        act_sch_name = data['activity_schedule'] if 'activity_schedule' in data and \
            data['activity_schedule'] is not None else ''
        occ_sched, activity_sched = cls._get_occ_act_schedules_from_dict(
            schedule_dict, data['occupancy_schedule'], act_sch_name)
        rad_fract, lat_fract = cls._optional_dict_keys(data)
        return cls(data['name'], data['people_per_area'], occ_sched, activity_sched,
                   rad_fract, lat_fract)

    def to_idf(self, zone_name):
        """IDF string representation of People object.

        Note that this method only outputs a single string for the People object and,
        to write everything needed to describe the object into an IDF, this object's
        occupancy_schedule and activity_schedule must also be written. This is done
        to give more control over the export process since you typically want to check
        whether these schedules are used by multiple People objects and write the
        schedule into the IDF only once.

        Args:
            zone_name: Text for the zone name that the People object is assigned to.
        """
        sens_fract = 'autocalculate' if self.latent_fraction == autocalculate else \
            1 - float(self.latent_fraction)
        values = ('{}..{}'.format(self.name, zone_name), zone_name,
                  self.occupancy_schedule.name, 'People/Area',
                  '', self.people_per_area, '', self.radiant_fraction, sens_fract,
                  self.activity_schedule.name)
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
                which only specifies the names of schedules. Default: False.
        """
        base = {'type': 'People'} if not abridged else {'type': 'PeopleAbridged'}
        base['name'] = self.name
        base['people_per_area'] = self.people_per_area
        base['radiant_fraction'] = self.radiant_fraction
        base['latent_fraction'] = self.latent_fraction if \
            isinstance(self.latent_fraction, float) else self.latent_fraction.to_dict()
        if not abridged:
            base['occupancy_schedule'] = self.occupancy_schedule.to_dict()
            base['activity_schedule'] = self.activity_schedule.to_dict()
        else:
            base['occupancy_schedule'] = self.occupancy_schedule.name
            base['activity_schedule'] = self.activity_schedule.name
        return base

    @staticmethod
    def average(name, peoples, weights=None, timestep_resolution=1):
        """Get a People object that's a weighted average between other People objects.

        Args:
            name: A name for the new averaged People object.
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
            '{}_Occ Schedule'.format(name),
            [ppl.occupancy_schedule for ppl in peoples], u_weights, timestep_resolution)
        act_sched = People._average_schedule(
            '{}_Act Schedule'.format(name),
            [ppl.activity_schedule for ppl in peoples], u_weights, timestep_resolution)

        # return the averaged people object
        return People(name, ppl_area, occ_sched, act_sched, rad_fract, lat_fract)

    def _check_activity_schedule_type(self, schedule):
        """Check that the type limit of an input schedule is fractional."""
        if schedule.schedule_type_limit is not None:
            assert schedule.schedule_type_limit.unit == 'W', 'Activity schedule ' \
                'should be in Watts [ActivityLevel]. Got a schedule of unit_type ' \
                '[{}].'.format(schedule.schedule_type_limit.unit_type)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from a People dictionary."""
        rad_fract = data['radiant_fraction'] if 'radiant_fraction' in data else 0.3
        lat_fract = autocalculate if 'latent_fraction' not in data or \
            data['latent_fraction'] == autocalculate.to_dict() else data['latent_fraction']
        return rad_fract, lat_fract

    @staticmethod
    def _get_occ_act_schedules_from_dict(schedule_dict, occ_sch_name, act_sch_name):
        """Get schedule objects from a dictionary."""
        try:
            occ_sched = schedule_dict[occ_sch_name]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        if act_sch_name.lower() == 'seated adult activity':
            activity_sched = None
        else:
            try:
                activity_sched = schedule_dict[act_sch_name]
            except KeyError as e:
                raise ValueError('Failed to find {} in the People schedule_dict.'.format(e))
        return occ_sched, activity_sched

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.name, self.people_per_area, hash(self.occupancy_schedule),
                hash(self.activity_schedule), self.radiant_fraction,
                str(self.latent_fraction))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, People) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return People(
            self.name, self.people_per_area, self.occupancy_schedule,
            self.activity_schedule, self.radiant_fraction, self.latent_fraction)

    def __repr__(self):
        return 'People:\n name: {}\n people per area: {}\n schedule: ' \
            '{}'.format(self.name, self.people_per_area, self.occupancy_schedule.name)
