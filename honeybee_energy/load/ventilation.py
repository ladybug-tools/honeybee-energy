# coding=utf-8
"""Complete definition of ventilation in a simulation, including schedule and load."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_positive, valid_string

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string
from ..units import convert_ventilation_flow_per_person, \
    convert_ventilation_flow_per_area, convert_ventilation_flow_per_zone, \
    convert_ventilation_air_changes_per_hour
from ..lib.schedules import always_on
import honeybee_energy.lib.scheduletypelimits as _type_lib
from ..properties.extension import VentilationProperties


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
            in ACH. (Default: 0).
        schedule: An optional ScheduleRuleset or ScheduleFixedInterval for the
            ventilation over the course of the year. The type of this schedule
            should be Fractional and the fractional values will get multiplied by
            the total design flow rate (determined from the sum or max of the other
            4 fields) to yield a complete ventilation profile. Setting
            this schedule to be the occupancy schedule of the zone will mimic demand
            controlled ventilation. If None, the design level of ventilation will
            be used throughout all timesteps of the simulation, meaning that
            this schedule is Always On. (Default: None).
        method: Text to set how the different ventilation criteria are reconciled
            against one another. Choose from the options below. (Default: Sum).

            * Sum
            * Max

        effectiveness_cooling: A positive number to note the air distribution
            effectiveness of the ventilation system when it operates in cooling mode
            (or how well the system is able to mix the air when cooling).
            A value of 1 means that air is well mixed and specified air flows are not
            adjusted in the course of simulation. Values less than 1 indicate systems
            that do not mix the air as well and so the specified airflows are increased.
            Values greater than 1 indicate systems that are particularly good at
            delivering outdoor air to the breathing zone of a room and so the
            specified airflows can be reduced. (Default: 1).
        effectiveness_heating: A positive number to note the air distribution
            effectiveness of the ventilation system when it operates in heating mode
            (or how well the system is able to mix the air when heating).
            A value of 1 means that air is well mixed and specified air flows are not
            adjusted in the course of simulation. Values less than 1 indicate systems
            that do not mix the air as well and so the specified airflows are increased.
            Values greater than 1 indicate systems that are particularly good at
            delivering outdoor air to the breathing zone of a room and so the
            specified airflows can be reduced. (Default: 1).
        secondary_recirculation: A number that is greater than or equal to zero,
            which notes the fraction of a zone's recirculation air that
            does not directly mix with the outdoor air. Used in cases where a
            central ventilation system supplies several zones and the return
            air is not collected through ducts back to the central air handler
            (eg. a plenum return system is used). This means unused outdoor
            ventilation air from other zones in the central system can be credited
            to the room. (Default: 0).

    Properties:
        * identifier
        * display_name
        * flow_per_person
        * flow_per_area
        * flow_per_zone
        * air_changes_per_hour
        * schedule
        * method
        * effectiveness_cooling
        * effectiveness_heating
        * secondary_recirculation
        * user_data
    """
    __slots__ = (
        '_flow_per_person', '_flow_per_area', '_flow_per_zone', '_air_changes_per_hour',
        '_schedule', '_method', '_effectiveness_cooling', '_effectiveness_heating',
        '_secondary_recirculation'
    )
    METHODS = ('Sum', 'Max')

    def __init__(
        self, identifier, flow_per_person=0, flow_per_area=0, flow_per_zone=0,
        air_changes_per_hour=0, schedule=None, method='Sum',
        effectiveness_cooling=1, effectiveness_heating=1, secondary_recirculation=0
    ):
        """Initialize Ventilation."""
        _LoadBase.__init__(self, identifier)
        self.flow_per_person = flow_per_person
        self.flow_per_area = flow_per_area
        self.flow_per_zone = flow_per_zone
        self.air_changes_per_hour = air_changes_per_hour
        self.schedule = schedule
        self.method = method
        self.effectiveness_cooling = effectiveness_cooling
        self.effectiveness_heating = effectiveness_heating
        self.secondary_recirculation = secondary_recirculation
        self._properties = VentilationProperties(self)

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
        return self._schedule if self._schedule is not None else always_on

    @schedule.setter
    def schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected ScheduleRuleset or ScheduleFixedInterval for Ventilation ' \
                'schedule. Got {}.'.format(type(value))
            self._check_fractional_schedule_type(value, 'Ventilation')
            value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def method(self):
        """Text to set how the ventilation criteria are reconciled against one another.

        Choose from the options below.

        * Sum
        * Max
        """
        return self._method

    @method.setter
    def method(self, value):
        clean_input = valid_string(value).lower()
        for key in self.METHODS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'Method {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.METHODS))
        self._method = value

    @property
    def effectiveness_cooling(self):
        """Get or set a number for the air distribution effectiveness in cooling mode."""
        return self._effectiveness_cooling

    @effectiveness_cooling.setter
    def effectiveness_cooling(self, value):
        self._effectiveness_cooling = \
            float_positive(value, 'ventilation effectiveness for cooling') \
            if value is not None else 1
        assert self._effectiveness_cooling != 0, \
            'Ventilation effectiveness cannot be zero.'

    @property
    def effectiveness_heating(self):
        """Get or set a number for the air distribution effectiveness in heating mode."""
        return self._effectiveness_heating

    @effectiveness_heating.setter
    def effectiveness_heating(self, value):
        self._effectiveness_heating = \
            float_positive(value, 'ventilation effectiveness for heating') \
            if value is not None else 1
        assert self._effectiveness_heating != 0, \
            'Ventilation effectiveness cannot be zero.'

    @property
    def secondary_recirculation(self):
        """Get or set a number for the fraction of recirculation air not mixed outdoor air.
        """
        return self._secondary_recirculation

    @secondary_recirculation.setter
    def secondary_recirculation(self, value):
        self._secondary_recirculation = \
            float_positive(value, 'ventilation secondary recirculation') \
            if value is not None else 0

    @property
    def flow_per_person_si(self):
        """Get the flow_per_person in the standard SI unit of L/s/person."""
        return convert_ventilation_flow_per_person(self.flow_per_person, 'si')

    @property
    def flow_per_person_ip(self):
        """Get the flow_per_person in the standard IP unit of cfm/person."""
        return convert_ventilation_flow_per_person(self.flow_per_person, 'ip')

    @property
    def flow_per_area_si(self):
        """Get the flow_per_area in the standard SI unit of L/s/m2."""
        return convert_ventilation_flow_per_area(self.flow_per_area, 'si')

    @property
    def flow_per_area_ip(self):
        """Get the flow_per_area in the standard IP unit of cfm/ft2."""
        return convert_ventilation_flow_per_area(self.flow_per_area, 'ip')

    @property
    def flow_per_zone_si(self):
        """Get the flow_per_zone in the standard SI unit of L/s."""
        return convert_ventilation_flow_per_zone(self.flow_per_zone, 'si')

    @property
    def flow_per_zone_ip(self):
        """Get the flow_per_zone in the standard IP unit of cfm."""
        return convert_ventilation_flow_per_zone(self.flow_per_zone, 'ip')

    @property
    def air_changes_per_hour_si(self):
        """Get the air_changes_per_hour in the standard SI unit of ACH."""
        return convert_ventilation_air_changes_per_hour(self.air_changes_per_hour, 'si')

    @property
    def air_changes_per_hour_ip(self):
        """Get the air_changes_per_hour in the standard IP unit of ACH."""
        return convert_ventilation_air_changes_per_hour(self.air_changes_per_hour, 'ip')

    def room_absolute_flow(self, room):
        """Get the total flow rate of outdoor ventilation air for a Room in m3/s.

        The result of this method accounts for all four ways of specifying
        ventilation and appropriately accounts for the Ventilation method.
        It also includes all effects of ventilation effectiveness (using the
        lower of the two ventilation effectiveness between heating and cooling mode).

        It does NOT include the effect of secondary recirculation given that the
        effect of this is impossible to know without having the other rooms
        included within the multi-path system.

        Args:
            room: The honeybee Room to which the ventilation object is assigned.
        """
        total_flows = [self.flow_per_zone]
        if self.flow_per_person != 0:
            people = room.properties.energy.people
            if people is not None:
                person_count = people.people_per_area * room.floor_area
                total_flows.append(self.flow_per_person * person_count)
        if self.flow_per_area != 0:
            total_flows.append(self.flow_per_area * room.floor_area)
        if self.air_changes_per_hour != 0:
            total_flows.append((self.air_changes_per_hour * room.volume) / 3600)
        total_flow = sum(total_flows) if self.method == 'Sum' else max(total_flows)
        vent_eff = min(self.effectiveness_cooling, self.effectiveness_heating)
        return total_flow / vent_eff

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
        method = 'Sum'
        try:
            if ep_strs[1].lower() == 'sum':
                pass
            elif ep_strs[1].lower() == 'maximum':
                method = 'Max'
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
        ventilation = cls(obj_id, person, area, zone, ach, sched, method)
        return ventilation

    @classmethod
    def from_dict(cls, data, schedules=None):
        """Create a Ventilation object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A Ventilation dictionary in following the format below.
            schedules: Optional dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). When specified, these will be prioritized
                over the child objects underneath their unabridged specification.

        .. code-block:: python

            {
            "type": 'Ventilation',
            "identifier": 'Office_Ventilation_0010_000050_0_0',
            "display_name": 'Office Ventilation',
            "flow_per_person": 0.01, # flow per person
            "flow_per_area": 0.0005, # flow per square meter of floor area
            "flow_per_zone": 0, # flow per zone
            "air_changes_per_hour": 0, # air changes per hour
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "method": "Sum",  # text for the ventilation method
            "effectiveness_cooling": 1.0,  # effectiveness during cooling
            "effectiveness_heating": 0.8,  # effectiveness during heating
            "secondary_recirculation": 0  # fraction of secondary recirculated air
            }
        """
        assert data['type'] == 'Ventilation', \
            'Expected Ventilation dictionary. Got {}.'.format(data['type'])
        person, area, zone, ach, method, ce, he, rec = cls._optional_dict_keys(data)
        sched = cls._get_schedule_from_dict(data['schedule'], schedules) \
            if 'schedule' in data and data['schedule'] is not None else None
        new_obj = cls(data['identifier'], person, area, zone, ach,
                      sched, method, ce, he, rec)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
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
            "schedule": "Office Ventilation Schedule", # Schedule identifier
            "method": "Sum",  # text for the ventilation method
            "effectiveness_cooling": 1.0,  # effectiveness during cooling
            "effectiveness_heating": 0.8,  # effectiveness during heating
            "secondary_recirculation": 0  # fraction of secondary recirculated air
            }
        """
        assert data['type'] == 'VentilationAbridged', \
            'Expected VentilationAbridged dictionary. Got {}.'.format(data['type'])
        person, area, zone, ach, method, ce, he, rec = cls._optional_dict_keys(data)
        sched = None
        if 'schedule' in data and data['schedule'] is not None:
            try:
                sched = schedule_dict[data['schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], person, area, zone, ach,
                      sched, method, ce, he, rec)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of Ventilation object.

        Note that this method only outputs a single string for the DesignSpecification:
        OutdoorAir object. To write everything needed to describe the object into an IDF,
        this object's schedule must also be written.

        Args:
            zone_identifier: Text for the zone identifier that the Ventilation
                object is assigned to.

        .. code-block:: shell

            DesignSpecification:OutdoorAir
                ZoneOAData,            !- Name
                Sum,                   !- Outdoor Air Method
                0.00944,               !- Outdoor Air Flow per Person {m3/s}
                0.00305,               !- Outdoor Air Flow per Zone Floor Area {m3/s-m2}
                ,                      !- Outdoor Air Flow per Zone {m3/s}
                ,                      !- Outdoor Air Flow Air Changes per Hour
                OARequirements Sched;  !- Outdoor Air Schedule Name
        """
        sched = self._schedule.identifier if self._schedule is not None else ''
        vent_obj_identifier = '{}..{}'.format(self.identifier, zone_identifier)
        method = 'Maximum' if self.method == 'Max' else 'Sum'
        if self.effectiveness_cooling == 1 and self.effectiveness_heating == 1:
            values = (
                vent_obj_identifier, method,
                self.flow_per_person, self.flow_per_area,
                self.flow_per_zone, self.air_changes_per_hour, sched
            )
        else:  # adjust the outdoor air need using the effectiveness
            eff = min(self.effectiveness_cooling, self.effectiveness_heating)
            values = (
                vent_obj_identifier, method,
                self.flow_per_person / eff, self.flow_per_area / eff,
                self.flow_per_zone / eff, self.air_changes_per_hour / eff, sched
            )
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
        if self._schedule is not None:
            base['schedule'] = self.schedule.to_dict() if not \
                abridged else self.schedule.identifier
        if self.method != 'Sum':
            base['method'] = self.method
        if self.effectiveness_cooling != 1:
            base['effectiveness_cooling'] = self.effectiveness_cooling
        if self.effectiveness_heating != 1:
            base['effectiveness_heating'] = self.effectiveness_heating
        if self.secondary_recirculation != 0:
            base['secondary_recirculation'] = self.secondary_recirculation
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    @staticmethod
    def average(identifier, ventilations, weights=None, timestep_resolution=1):
        """Get a Ventilation object that's an average between other Ventilations.

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
        method = 'Max' if all(vent.method == 'Max' for vent in ventilations) else 'Sum'
        eff_cool = sum([vent.effectiveness_cooling * w
                        for vent, w in zip(ventilations, weights)])
        eff_heat = sum([vent.effectiveness_heating * w
                        for vent, w in zip(ventilations, weights)])
        sec_rec = sum([vent.secondary_recirculation * w
                       for vent, w in zip(ventilations, weights)])
        # round the effectiveness terms to avoid tolerance issues
        eff_cool = round(eff_cool, 3)
        eff_heat = round(eff_heat, 3)
        sec_rec = round(sec_rec, 3)

        # calculate the average schedules
        scheds = [vent._schedule for vent in ventilations]
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
        return Ventilation(identifier, person, area, zone, ach, sched, method,
                           eff_cool, eff_heat, sec_rec)

    @staticmethod
    def combine_room_ventilations(identifier, rooms, timestep_resolution=1):
        """Get a Ventilation object that represents the sum across rooms.

        In this process of combining ventilation requirements, the following
        rules hold: 1. Total flow rates in m3/s are simply added together. 2. Flow per
        floor area gets recomputed using the floor areas of each room. 3. ACH flow
        gets recomputed using the volumes of each room in the inputs. 4. Flow per
        person gets set based on whichever room has the highest ventilation
        requirement per person.

        In the case of ventilation schedules, the strictest schedule governs and
        note that the absence of a ventilation schedule means the schedule is
        Always On. So, if one room has a ventilation schedule and the other
        does not, then the schedule essentially gets removed. If each room has
        a different ventilation schedule, then a new schedule will be created
        using the maximum value across the two schedules at each timestep.

        In the case of ventilation effectiveness and secondary recirculation,
        the minimum effectiveness and recirculation fractions across the rooms
        will be used.

        Args:
            identifier: Text string for a unique ID for the new Ventilation object.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            rooms: A list of Rooms that will have their Ventilation objects
                combined to make a new Ventilation.
            timestep_resolution: An optional integer for the timestep resolution at
                which conflicting ventilation schedules will be resolved. (Default: 1).
        """
        # compute weights based on floor areas and volumes
        ventilations, floor_areas, volumes, scheds = [], [], [], []
        for room in rooms:
            if room.properties.energy.ventilation is None:
                ventilations.append(Ventilation())
            else:
                ventilations.append(room.properties.energy.ventilation)
                scheds.append(room.properties.energy.ventilation._schedule)
            floor_areas.append(room.floor_area)
            volumes.append(room.volume)
        total_floor = sum(floor_areas)
        total_volume = sum(volumes)
        floor_weights = [ar / total_floor for ar in floor_areas]
        vol_weights = [vol / total_volume for vol in volumes]

        # calculate the average values
        person = max(vent.flow_per_person for vent in ventilations)
        area = sum([vent.flow_per_area * w
                    for vent, w in zip(ventilations, floor_weights)])
        zone = sum(vent.flow_per_zone for vent in ventilations)
        ach = sum([vent.air_changes_per_hour * w
                   for vent, w in zip(ventilations, vol_weights)])
        method = 'Max' if all(vent.method == 'Max' for vent in ventilations) else 'Sum'

        # calculate the average schedules
        if len(scheds) == 0 or any(val is None for val in scheds):
            sched = None
        else:
            base_sch = scheds[0]
            if all(sch is base_sch for sch in scheds) or len(set(scheds)) == 1:
                sched = scheds[0]
            else:
                sched = Ventilation._max_schedule(
                    '{} Schedule'.format(identifier), scheds, timestep_resolution)

        # get the minimum effectiveness and secondary recirculation
        eff_cool = min(vent.effectiveness_cooling for vent in ventilations)
        eff_heat = min(vent.effectiveness_heating for vent in ventilations)
        sec_rec = min(vent.secondary_recirculation for vent in ventilations)

        # return the averaged object
        return Ventilation(identifier, person, area, zone, ach, sched, method,
                           eff_cool, eff_heat, sec_rec)

    @staticmethod
    def _optional_dict_keys(data):
        """Get the optional keys from an Ventilation dictionary."""
        person = data['flow_per_person'] if 'flow_per_person' in data else 0
        area = data['flow_per_area'] if 'flow_per_area' in data else 0
        zone = data['flow_per_zone'] if 'flow_per_zone' in data else 0
        ach = data['air_changes_per_hour'] if 'air_changes_per_hour' in data else 0
        method = data['method'] if 'method' in data else 'Sum'
        cool_eff = data['effectiveness_cooling'] if 'effectiveness_cooling' in data else 1
        heat_eff = data['effectiveness_heating'] if 'effectiveness_heating' in data else 1
        rec = data['secondary_recirculation'] if 'secondary_recirculation' in data else 0
        return person, area, zone, ach, method, cool_eff, heat_eff, rec

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (
            self.identifier, self.flow_per_person, self.flow_per_area,
            self.flow_per_zone, self.air_changes_per_hour, hash(self.schedule),
            self.method, self.effectiveness_cooling, self.effectiveness_heating,
            self.secondary_recirculation
        )

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Ventilation) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = Ventilation(
            self._identifier, self._flow_per_person, self._flow_per_area,
            self._flow_per_zone, self._air_changes_per_hour, self._schedule,
            self._method, self.effectiveness_cooling, self.effectiveness_heating,
            self.secondary_recirculation
        )
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def __repr__(self):
        return 'Ventilation: {} [{} m3/s-person] [{} m3/s-m2] [{} ACH]'.format(
            self.display_name, round(self.flow_per_person, 4),
            round(self.flow_per_area, 6), round(self.air_changes_per_hour, 2))
