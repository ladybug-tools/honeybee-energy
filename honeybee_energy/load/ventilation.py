# coding=utf-8
"""Complete definition of ventilation in a simulation, including schedule and load."""
from __future__ import division

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string

import honeybee_energy.lib.scheduletypelimits as _type_lib

from honeybee._lockable import lockable
from honeybee.typing import float_positive


@lockable
class Ventilation(_LoadBase):
    """A complete definition of ventilation, including schedules and load.

    Note the the 4 ventilation types (flow_per_person, flow_per_area, flow_per_zone,
    and air_changes_per_hour) are ultimately added together to yield the ventilation
    design flow rate used in the simulation.

    Args:
        identifier: Text string for a unique Ventilation ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        flow_per_person: A numerical value for the intensity of ventilation
            in m3/s per person. Note that setting this value here does not mean
            that ventilation is varied based on real-time occupancy but rather
            that the design level of ventilation is determined using this value
            and the People object of the zone. To vary ventilation in real time,
            the ventilation schedule should be used. Most ventilation standards
            support that a value of 0.01 m3/s (10 L/s or ~20 cfm) per person is
            sufficient to remove odors. Accordingly, setting this value to 0.01
            and using 0 for the following ventilation terms will often be suitable
            for many applications. Default: 0.
        flow_per_area: A numerical value for the intensity of ventilation in m3/s
            per square meter of floor area. Default: 0.
        flow_per_zone: A numerical value for the design level of ventilation
            in m3/s for the entire zone. Default: 0.
        air_changes_per_hour: A numerical value for the design level of ventilation
            in air changes per hour (ACH) for the entire zone. This is particularly
            helpful for hospitals, where ventilation standards are often given
            in ACH. Default: 0.
        schedule: An optional ScheduleRuleset or ScheduleFixedInterval for the
            ventilation over the course of the year. The type of this schedule
            should be Fractional and the fractional values will get multiplied by
            the total design flow rate (determined from the sum of the other
            4 fields) to yield a complete ventilation profile. Setting
            this schedule to be the occupancy schedule of the zone will mimic demand
            controlled ventilation. If None, the design level of ventilation will
            be used throughout all timesteps of the simulation. Default: None.

    Properties:
        * identifier
        * display_name
        * flow_per_person
        * flow_per_area
        * flow_per_zone
        * air_changes_per_hour
        * schedule
    """
    __slots__ = ('_flow_per_person', '_flow_per_area', '_flow_per_zone',
                 '_air_changes_per_hour', '_schedule')

    def __init__(self, identifier, flow_per_person=0, flow_per_area=0, flow_per_zone=0,
                 air_changes_per_hour=0, schedule=None):
        """Initialize Ventilation."""
        _LoadBase.__init__(self, identifier)
        self.flow_per_person = flow_per_person
        self.flow_per_area = flow_per_area
        self.flow_per_zone = flow_per_zone
        self.air_changes_per_hour = air_changes_per_hour
        self.schedule = schedule

    @property
    def flow_per_person(self):
        """Get or set the intensity of ventilation in m3/s per person.

        Note that setting this value here does not mean that ventilation is varied
        based on real-time occupancy but rather that the design level of ventilation
        is determined using this value and the People object of the zone. To vary
        ventilation in real time, the ventilation schedule should be used or demand
        controlled ventilation options should be set on the HVAC system.

        Most ventilation standards support that a value of 0.01 m3/s (10 L/s or ~20 cfm)
        per person is sufficient to remove odors. Accordingly, setting this value to
        0.01 and using 0 for the following ventilation terms will often be suitable
        for many applications.
        """
        return self._flow_per_person

    @flow_per_person.setter
    def flow_per_person(self, value):
        self._flow_per_person = float_positive(value, 'ventilation flow per person') if \
            value is not None else 0

    @property
    def flow_per_area(self):
        """Get or set the ventilation in m3/s per square meter of zone floor area."""
        return self._flow_per_area

    @flow_per_area.setter
    def flow_per_area(self, value):
        self._flow_per_area = float_positive(value, 'ventilation flow per area') if \
            value is not None else 0

    @property
    def flow_per_zone(self):
        """Get or set the ventilation in m3/s per zone."""
        return self._flow_per_zone

    @flow_per_zone.setter
    def flow_per_zone(self, value):
        self._flow_per_zone = float_positive(value, 'ventilation flow per zone')if \
            value is not None else 0

    @property
    def air_changes_per_hour(self):
        """Get or set the ventilation in air changes per hour (ACH)."""
        return self._air_changes_per_hour

    @air_changes_per_hour.setter
    def air_changes_per_hour(self, value):
        self._air_changes_per_hour = \
            float_positive(value, 'ventilation air changes per hour') if \
            value is not None else 0

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for ventilation."""
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected ScheduleRuleset or ScheduleFixedInterval for Ventilation ' \
                'schedule. Got {}.'.format(type(value))
            self._check_fractional_schedule_type(value, 'Ventilation')
            value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create an Ventilation object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                DesignSpecification:OutdoorAir definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the Ventilation object.

        Returns:
            ventilation -- An Ventilation object loaded from the idf_string.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'DesignSpecification:OutdoorAir,')

        # extract the numerical properties from the string
        person = 0.00944
        area = 0
        zone = 0
        ach = 0
        try:
            person = ep_strs[2] if ep_strs[2] != '' else 0.00944
            area = ep_strs[3] if ep_strs[3] != '' else 0
            zone = ep_strs[4] if ep_strs[4] != '' else 0
            ach = ep_strs[5] if ep_strs[5] != '' else 0
        except IndexError:
            pass  # shorter ventilation definition lacking values

        # change the values to 0 if 'Sum' method is not used
        try:
            if ep_strs[1].lower() == 'sum':
                pass
            elif ep_strs[1].lower() == 'flow/person':
                area, zone, ach = 0, 0, 0
            elif ep_strs[1].lower() == 'flow/area':
                person, zone, ach = 0, 0, 0
            elif ep_strs[1].lower() == 'flow/zone':
                person, area, ach = 0, 0, 0
            elif ep_strs[1].lower() == 'airchanges/hour':
                person, area, zone = 0, 0, 0
            else:
                raise ValueError('DesignSpecification:OutdoorAir {} method '
                                 'is not supported by honeybee.'.format(ep_strs[1]))
        except IndexError:  # EnergyPlus defaults to flow/person
            area, zone, ach = 0, 0, 0

        # extract the schedules from the string
        try:
            try:
                sched = schedule_dict[ep_strs[6]] if ep_strs[6] != '' else None
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        except IndexError:  # No schedule given
            sched = None

        # return the object and the zone id for the object
        obj_id = ep_strs[0].split('..')[0]
        ventilation = cls(obj_id, person, area, zone, ach, sched)
        return ventilation

    @classmethod
    def from_dict(cls, data):
        """Create a Ventilation object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A Ventilation dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'Ventilation',
            "identifier": 'Office_Ventilation_0010_000050_0_0',
            "display_name": 'Office Ventilation',
            "flow_per_person": 0.01, # flow per person
            "flow_per_area": 0.0005, # flow per square meter of floor area
            "flow_per_zone": 0, # flow per zone
            "air_changes_per_hour": 0, # air changes per hour
            "schedule": {} # ScheduleRuleset/ScheduleFixedInterval dictionary
            }
        """
        assert data['type'] == 'Ventilation', \
            'Expected Ventilation dictionary. Got {}.'.format(data['type'])
        person, area, zone, ach = cls._optional_dict_keys(data)
        sched = cls._get_schedule_from_dict(data['schedule']) if 'schedule' in data and \
            data['schedule'] is not None else None
        new_obj = cls(data['identifier'], person, area, zone, ach, sched)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a Ventilation object from an abridged dictionary.

        Args:
            data: A VentilationAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Ventilation object.

        .. code-block:: python

            {
            "type": 'VentilationAbridged',
            "identifier": 'Office_Ventilation_0010_000050_0_0',
            "display_name": 'Office Ventilation',
            "flow_per_person": 0.01, # flow per person
            "flow_per_area": 0.0005, # flow per square meter of floor area
            "flow_per_zone": 0, # flow per zone
            "air_changes_per_hour": 0, # air changes per hour
            "schedule": "Office Ventilation Schedule" # Schedule identifier
            }
        """
        assert data['type'] == 'VentilationAbridged', \
            'Expected VentilationAbridged dictionary. Got {}.'.format(data['type'])
        person, area, zone, ach = cls._optional_dict_keys(data)
        sched = None
        if 'schedule' in data and data['schedule'] is not None:
            try:
                sched = schedule_dict[data['schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], person, area, zone, ach, sched)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of Ventilation object.

        Note that this method only outputs a single string for the DesignSpecification:
        OutdoorAir object and, to write everything needed to describe the object
        into an IDF, this object's schedule must also be written.

        Args:
            zone_identifier: Text for the zone identifier that the Ventilation
                object is assigned to.
        """
        sched = self.schedule.identifier if self.schedule is not None else ''
        vent_obj_identifier = '{}..{}'.format(self.identifier, zone_identifier)
        values = (vent_obj_identifier, 'Sum', self.flow_per_person, self.flow_per_area,
                  self.flow_per_zone, self.air_changes_per_hour, sched)
        comments = ('name', 'flow rate method', 'flow per person {m3/s-person}',
                    'flow per floor area {m3/s-m2}', 'flow per zone {m3/s}',
                    'air changes per hour {1/hr}', 'outdoor air schedule name')
        return generate_idf_string('DesignSpecification:OutdoorAir', values, comments)

    def to_dict(self, abridged=False):
        """Ventilation dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        base = {'type': 'Ventilation'} if not abridged \
            else {'type': 'VentilationAbridged'}
        base['identifier'] = self.identifier
        if self.flow_per_person != 0:
            base['flow_per_person'] = self.flow_per_person
        if self.flow_per_area != 0:
            base['flow_per_area'] = self.flow_per_area
        if self.flow_per_zone != 0:
            base['flow_per_zone'] = self.flow_per_zone
        if self.air_changes_per_hour != 0:
            base['air_changes_per_hour'] = self.air_changes_per_hour
        if self.schedule is not None:
            base['schedule'] = self.schedule.to_dict() if not \
                abridged else self.schedule.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    @staticmethod
    def average(identifier, ventilations, weights=None, timestep_resolution=1):
        """Get an Ventilation object that's an average between other Ventilations.

        Args:
            identifier: Text string for a unique ID for the new averaged Ventilation.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            ventilations: A list of Ventilation objects that will be averaged
                together to make a new Ventilation.
            weights: An optional list of fractional numbers with the same length
                as the input ventilations. These will be used to weight each of the
                Ventilation objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average flow rates
                will assume 0 for the unaccounted fraction of the weights.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        weights, u_weights = \
            Ventilation._check_avg_weights(ventilations, weights, 'Ventilation')

        # calculate the average values
        person = sum([vent.flow_per_person * w
                      for vent, w in zip(ventilations, weights)])
        area = sum([vent.flow_per_area * w
                    for vent, w in zip(ventilations, weights)])
        zone = sum([vent.flow_per_zone * w
                    for vent, w in zip(ventilations, weights)])
        ach = sum([vent.air_changes_per_hour * w
                   for vent, w in zip(ventilations, weights)])

        # calculate the average schedules
        scheds = [vent.schedule for vent in ventilations]
        if all(val is None for val in scheds):
            sched = None
        else:
            full_vent = ScheduleRuleset.from_constant_value(
                'Full Ventilation', 1, _type_lib.fractional)
            for i, sch in enumerate(scheds):
                if sch is None:
                    scheds[i] = full_vent
            sched = Ventilation._average_schedule(
                '{} Schedule'.format(identifier), scheds, u_weights, timestep_resolution)

        # return the averaged object
        return Ventilation(identifier, person, area, zone, ach, sched)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from an Ventilation dictionary."""
        person = data['flow_per_person'] if 'flow_per_person' in data else 0
        area = data['flow_per_area'] if 'flow_per_area' in data else 0
        zone = data['flow_per_zone'] if 'flow_per_zone' in data else 0
        ach = data['air_changes_per_hour'] if 'air_changes_per_hour' in data else 0
        return person, area, zone, ach

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.flow_per_person, self.flow_per_area,
                self.flow_per_zone, self.air_changes_per_hour, hash(self.schedule))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Ventilation) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = Ventilation(
            self.identifier, self.flow_per_person, self.flow_per_area,
            self.flow_per_zone, self.air_changes_per_hour, self.schedule)
        new_obj._display_name = self._display_name
        return new_obj

    def __repr__(self):
        return 'Ventilation:\n name: {}\n flow per person: {}\n flow per area: ' \
            '{}\n flow per zone: {}\n ACH: {}'.format(
                self.identifier, self.flow_per_person, self.flow_per_area,
                self.flow_per_zone, self.air_changes_per_hour)
