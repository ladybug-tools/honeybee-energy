# coding=utf-8
"""Complete definition of infiltration in a simulation, including schedule and load."""
from __future__ import division

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_positive


@lockable
class Infiltration(_LoadBase):
    """A complete definition of infiltration, including schedules and load.

    Args:
        identifier: Text string for a unique Infiltration ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        flow_per_exterior_area: A numerical value for the intensity of infiltration
            in m3/s per square meter of exterior surface area. Typical values for
            this property are as follows (note all values are at typical building
            pressures of ~4 Pa):

            * 0.0001 (m3/s per m2 facade) - Tight building
            * 0.0003 (m3/s per m2 facade) - Average building
            * 0.0006 (m3/s per m2 facade) - Leaky building

        schedule: A ScheduleRuleset or ScheduleFixedInterval for the infiltration
            over the course of the year. The type of this schedule should be
            Fractional and the fractional values will get multiplied by the
            flow_per_exterior_area to yield a complete infiltration profile.
        constant_coefficient: A number for the fraction of the infiltration that
            remains constant in spite of exterior wind and the difference
            between interior/exterior temperature. EnergyPlus uses 1 by default but
            BLAST and DOE-2 (the EnergyPlus predecessors) used 0.606 and 0 for
            this coefficient respectively. Default: 1.
        temperature_coefficient: A number that will get multiplied by the difference
            in interior/exterior temperature (in C) to yield a coefficient that
            gets multiplied by the flow_per_exterior_area. EnergyPlus uses 0 by
            default but BLAST and DOE-2 (the EnergyPlus predecessors) used 0.03636
            and 0 for this coefficient respectively. Default: 0.
        velocity_coefficient: A number that will get multiplied by the hourly
            exterior wind velocity (in m/s) to yield a coefficient that gets
            multiplied by the flow_per_exterior_area. EnergyPlus uses 0 by default
            but BLAST and DOE-2 (the EnergyPlus predecessors) used 0.1177 and 0.224
            for this coefficient respectively. Default: 0.

    Properties:
        * identifier
        * display_name
        * flow_per_exterior_area
        * schedule
        * constant_coefficient
        * temperature_coefficient
        * velocity_coefficient
    """
    __slots__ = ('_flow_per_exterior_area', '_schedule', '_constant_coefficient',
                 '_temperature_coefficient', '_velocity_coefficient')

    def __init__(self, identifier, flow_per_exterior_area, schedule,
                 constant_coefficient=1,
                 temperature_coefficient=0, velocity_coefficient=0):
        """Initialize Infiltration."""
        _LoadBase.__init__(self, identifier)
        self.flow_per_exterior_area = flow_per_exterior_area
        self.schedule = schedule
        self.constant_coefficient = constant_coefficient
        self.temperature_coefficient = temperature_coefficient
        self.velocity_coefficient = velocity_coefficient

    @property
    def flow_per_exterior_area(self):
        """Get or set the infiltration in m3/s per square meter of exterior surface area.

        Typical values for this property are as follows:

        * 0.0001 (m3/s per m2 facade) - Tight building
        * 0.0003 (m3/s per m2 facade) - Average building
        * 0.0006 (m3/s per m2 facade) - Leaky building
        """
        return self._flow_per_exterior_area

    @flow_per_exterior_area.setter
    def flow_per_exterior_area(self, value):
        self._flow_per_exterior_area = float_positive(
            value, 'infiltration flow per area')

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for infiltration."""
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for Infiltration ' \
            'schedule. Got {}.'.format(type(value))
        self._check_fractional_schedule_type(value, 'Infiltration')
        value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def constant_coefficient(self):
        """Get or set the fraction of infiltration remaining constant despite outdoors.
        """
        return self._constant_coefficient

    @constant_coefficient.setter
    def constant_coefficient(self, value):
        self._constant_coefficient = float_positive(
            value, 'infiltration constant coefficient')

    @property
    def temperature_coefficient(self):
        """Get or set the coefficient for the interior/exterior temperature difference.
        """
        return self._temperature_coefficient

    @temperature_coefficient.setter
    def temperature_coefficient(self, value):
        self._temperature_coefficient = float_positive(
            value, 'infiltration temperature coefficient')

    @property
    def constant_coefficient(self):
        """Get or set the infiltration fraction remaining constant despite the outdoors.
        """
        return self._constant_coefficient

    @constant_coefficient.setter
    def constant_coefficient(self, value):
        self._constant_coefficient = float_positive(
            value, 'infiltration constant coefficient')

    @property
    def temperature_coefficient(self):
        """Get or set the coefficient for the interior/exterior temperature difference.
        """
        return self._temperature_coefficient

    @temperature_coefficient.setter
    def temperature_coefficient(self, value):
        self._temperature_coefficient = float_positive(
            value, 'infiltration temperature coefficient')

    @property
    def velocity_coefficient(self):
        """Get or set the coefficient for the exterior wind speed."""
        return self._velocity_coefficient

    @velocity_coefficient.setter
    def velocity_coefficient(self, value):
        self._velocity_coefficient = float_positive(
            value, 'infiltration velocity coefficient')

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create an Infiltration object from an EnergyPlus IDF text string.

        Note that the idf_string must use the 'flow per exterior surface area'
        method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                ZoneInfiltration:DesignFlowRate definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the Infiltration object.

        Returns:
            A tuple with two elements

            -   infiltration: An Infiltration object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the Infiltration
                object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'ZoneInfiltration:DesignFlowRate,')
        assert ep_strs[3].lower() == 'flow/exteriorarea', \
            'ZoneInfiltration:DesignFlowRate must use Flow/ExteriorArea method ' \
            'to be loaded from IDF to honeybee.'

        # extract the properties from the string
        const = 1
        temp = 0
        vel = 0
        try:
            const = ep_strs[8] if ep_strs[8] != '' else 0
            temp = ep_strs[9] if ep_strs[9] != '' else 0
            vel = ep_strs[10] if ep_strs[10] != '' else 0
        except IndexError:
            pass  # shorter infiltration definition lacking coefficients

        # extract the schedules from the string
        try:
            sched = schedule_dict[ep_strs[2]]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))

        # return the object and the zone identifier for the object
        obj_id = ep_strs[0].split('..')[0]
        zone_id = ep_strs[1]
        infiltration = cls(obj_id, ep_strs[6], sched, const, temp, vel)
        return infiltration, zone_id

    @classmethod
    def from_dict(cls, data):
        """Create a Infiltration object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A Infiltration dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'Infiltration',
            "identifier": 'Residentail_Infiltration_000030_1_0_0',
            "display_name": 'Residentail Infiltration',
            "flow_per_exterior_area": 0.0003, # flow per square meter of exterior area
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "constant_coefficient": 1, # optional constant coefficient
            "temperature_coefficient": 0, # optional temperature coefficient
            "velocity_coefficient": 0 # optional velocity coefficient
            }
        """
        assert data['type'] == 'Infiltration', \
            'Expected Infiltration dictionary. Got {}.'.format(data['type'])
        sched = cls._get_schedule_from_dict(data['schedule'])
        const, tem, vel = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['flow_per_exterior_area'],
                      sched, const, tem, vel)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a Infiltration object from an abridged dictionary.

        Args:
            data: A InfiltrationAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Infiltration object.

        .. code-block:: python

            {
            "type": 'InfiltrationAbridged',
            "identifier": 'Residentail_Infiltration_000030_1_0_0',
            "display_name": 'Residentail Infiltration',
            "flow_per_exterior_area": 0.0003, # flow per square meter of exterior area
            "schedule": "Residentail Infiltration Schedule", # Schedule identifier
            "constant_coefficient": 1, # optional constant coefficient
            "temperature_coefficient": 0, # optional temperature coefficient
            "velocity_coefficient": 0 # optional velocity coefficient
            }
        """
        assert data['type'] == 'InfiltrationAbridged', \
            'Expected InfiltrationAbridged dictionary. Got {}.'.format(data['type'])
        try:
            sched = schedule_dict[data['schedule']]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        const, tem, vel = cls._optional_dict_keys(data)
        new_obj = cls(data['identifier'], data['flow_per_exterior_area'],
                      sched, const, tem, vel)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of Infiltration object.

        Note that this method only outputs a single string for the ZoneInfiltration:
        DesignFlowRate object and, to write everything needed to describe the
        object into an IDF, this object's schedule must also be written.

        Args:
            zone_identifier: Text for the zone identifier that the ZoneInfiltration:
                DesignFlowRate object is assigned to.
        """
        values = ('{}..{}'.format(self.identifier, zone_identifier), zone_identifier,
                  self.schedule.identifier, 'Flow/ExteriorArea', '', '',
                  self.flow_per_exterior_area, '', self.constant_coefficient,
                  self.temperature_coefficient, self.velocity_coefficient, '')
        comments = ('name', 'zone name', 'schedule name', 'flow rate method',
                    'flow rate {m3/s}', 'flow per floor area {m3/s-m2}',
                    'flow per exterior area {m3/s-m2}', 'air changes per hour {1/hr}',
                    'constant term coefficient', 'temperature term coefficient',
                    'velocity term coefficient', 'velocity squared term coefficient')
        return generate_idf_string('ZoneInfiltration:DesignFlowRate', values, comments)

    def to_dict(self, abridged=False):
        """Infiltration dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        base = {'type': 'Infiltration'} if not abridged \
            else {'type': 'InfiltrationAbridged'}
        base['identifier'] = self.identifier
        base['flow_per_exterior_area'] = self.flow_per_exterior_area
        base['schedule'] = self.schedule.to_dict() if not \
            abridged else self.schedule.identifier
        if self.constant_coefficient != 1:
            base['constant_coefficient'] = self.constant_coefficient
        if self.temperature_coefficient != 0:
            base['temperature_coefficient'] = self.temperature_coefficient
        if self.velocity_coefficient != 0:
            base['velocity_coefficient'] = self.velocity_coefficient
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    @staticmethod
    def average(identifier, infiltrations, weights=None, timestep_resolution=1):
        """Get an Infiltration object that's an average between other Infiltrations.

        Args:
            identifier: Text string for a unique ID for the new averaged Infiltration.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            infiltrations: A list of Infiltration objects that will be averaged
                together to make a new Infiltration.
            weights: An optional list of fractional numbers with the same length
                as the input infiltrations. These will be used to weight each of the
                Infiltration objects in the resulting average. Note that these weights
                can sum to less than 1 in which case the average flow_per_exterior_area
                will assume 0 for the unaccounted fraction of the weights.
                If None, the objects will be weighted equally. Default: None.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        weights, u_weights = \
            Infiltration._check_avg_weights(infiltrations, weights, 'Infiltration')

        # calculate the average values
        fd = sum([inf.flow_per_exterior_area * w
                  for inf, w in zip(infiltrations, weights)])
        const = sum([inf.constant_coefficient * w
                     for inf, w in zip(infiltrations, u_weights)])
        temp = sum([inf.temperature_coefficient * w
                    for inf, w in zip(infiltrations, u_weights)])
        vel = sum([inf.velocity_coefficient * w
                   for inf, w in zip(infiltrations, u_weights)])

        # calculate the average schedules
        sched = Infiltration._average_schedule(
            '{} Schedule'.format(identifier), [inf.schedule for inf in infiltrations],
            u_weights, timestep_resolution)

        # return the averaged infiltration object
        return Infiltration(identifier, fd, sched, const, temp, vel)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from an Infiltration dictionary."""
        const = data['constant_coefficient'] if 'constant_coefficient' in data else 1
        tem = data['temperature_coefficient'] if 'temperature_coefficient' in data else 0
        vel = data['velocity_coefficient'] if 'velocity_coefficient' in data else 0
        return const, tem, vel

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.flow_per_exterior_area, hash(self.schedule),
                self.constant_coefficient, self.temperature_coefficient,
                self.velocity_coefficient)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Infiltration) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = Infiltration(
            self.identifier, self.flow_per_exterior_area, self.schedule,
            self.constant_coefficient, self.temperature_coefficient,
            self.velocity_coefficient)
        new_obj._display_name = self._display_name
        return new_obj

    def __repr__(self):
        return 'Infiltration:\n name: {}\n flow per exterior area: {}\n schedule: ' \
            '{}'.format(self.identifier, self.flow_per_exterior_area,
                        self.schedule.identifier)
