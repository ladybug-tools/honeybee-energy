# coding=utf-8
"""Load object used to represent various types of specific processes."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, valid_string, \
    valid_ep_string

from ._base import _LoadBase
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..reader import parse_idf_string
from ..writer import generate_idf_string
from ..properties.extension import ProcessProperties


@lockable
class Process(_LoadBase):
    """Load object used to represent various types of specific processes.

    Examples include kilns, manufacturing equipment, and various industrial
    processes. They can also be used to represent wood burning fireplaces
    or certain pieces of equipment to be separated from the other end uses.

    Args:
        identifier: Text string for a unique Process ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        watts: A numerical value for the process load power in Watts.
        schedule: A ScheduleRuleset or ScheduleFixedInterval for the use of process
            over the course of the year. The type of this schedule should be
            Fractional and the fractional values will get multiplied by the
            watts to yield a complete process load profile.
        fuel_type: Text to denote the type of fuel consumed by the process.
            Using the "None" type indicates that no end uses will be associated
            with the process, only the zone gains. Choose from the following.

            * Electricity
            * NaturalGas
            * Propane
            * FuelOilNo1
            * FuelOilNo2
            * Diesel
            * Gasoline
            * Coal
            * Steam
            * DistrictHeating
            * DistrictCooling
            * OtherFuel1
            * OtherFuel2
            * None

        end_use_category: Text to indicate the end-use subcategory, which will identify
            the process load in the output end use table. Examples include
            “Cooking”, “Clothes Drying”, etc. Setting this to "General" will
            result in the process load being reported as part of the other Interior
            Equipment. (Default: Process).
        radiant_fraction: A number between 0 and 1 for the fraction of the total
            load given off as long wave radiant heat. (Default: 0).
        latent_fraction: A number between 0 and 1 for the fraction of the total
            load that is latent (as opposed to sensible). (Default: 0).
        lost_fraction: A number between 0 and 1 for the fraction of the total
            load that is lost outside of the zone and the HVAC system.
            Typically, this is used to represent heat that is exhausted directly
            out of a zone (as you would for a stove). (Default: 0).

    Properties:
        * identifier
        * display_name
        * watts
        * schedule
        * fuel_type
        * end_use_category
        * radiant_fraction
        * latent_fraction
        * lost_fraction
        * convected_fraction
        * user_data
    """
    __slots__ = ('_watts', '_schedule', '_fuel_type', '_end_use_category',
                 '_radiant_fraction', '_latent_fraction', '_lost_fraction')
    FUEL_TYPES = (
        'Electricity',
        'NaturalGas',
        'Propane',
        'FuelOilNo1',
        'FuelOilNo2',
        'Diesel',
        'Gasoline',
        'Coal',
        'Steam',
        'DistrictHeating',
        'DistrictCooling',
        'OtherFuel1',
        'OtherFuel2',
        'None'
    )

    def __init__(self, identifier, watts, schedule, fuel_type,
                 end_use_category='Process', radiant_fraction=0,
                 latent_fraction=0, lost_fraction=0):
        """Initialize Process."""
        _LoadBase.__init__(self, identifier)
        self._latent_fraction = 0  # starting value so that check runs correctly
        self._lost_fraction = 0  # starting value so that check runs correctly

        self.watts = watts
        self.schedule = schedule
        self.fuel_type = fuel_type
        self.end_use_category = end_use_category
        self.radiant_fraction = radiant_fraction
        self.latent_fraction = latent_fraction
        self.lost_fraction = lost_fraction
        self._properties = ProcessProperties(self)

    @property
    def watts(self):
        """Get or set the process total power in Watts."""
        return self._watts

    @watts.setter
    def watts(self, value):
        self._watts = float_positive(value, 'process watts')

    @property
    def schedule(self):
        """Get or set a ScheduleRuleset or ScheduleFixedInterval for process usage."""
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected ScheduleRuleset or ScheduleFixedInterval for process ' \
            'schedule. Got {}.'.format(type(value))
        self._check_fractional_schedule_type(value, 'Equipment')
        value.lock()   # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def fuel_type(self):
        """Get or set text to denote the type of fuel consumed by the process.

        Choose from the following options.

        * Electricity
        * NaturalGas
        * Propane
        * FuelOilNo1
        * FuelOilNo2
        * Diesel
        * Gasoline
        * Coal
        * Steam
        * DistrictHeating
        * DistrictCooling
        * OtherFuel1
        * OtherFuel2
        * None
        """
        return self._fuel_type

    @fuel_type.setter
    def fuel_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.FUEL_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'fuel_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, '\n'.join(self.FUEL_TYPES)))
        self._fuel_type = value

    @property
    def end_use_category(self):
        """Get or set text to indicate the end-use subcategory."""
        return self._end_use_category

    @end_use_category.setter
    def end_use_category(self, value):
        self._end_use_category = valid_ep_string(value)

    @property
    def radiant_fraction(self):
        """Get or set the fraction of process heat given off as long wave radiation."""
        return self._radiant_fraction

    @radiant_fraction.setter
    def radiant_fraction(self, value):
        self._radiant_fraction = float_in_range(
            value, 0.0, 1.0, 'process radiant fraction')
        self._check_fractions()

    @property
    def latent_fraction(self):
        """Get or set the fraction of process heat that is latent."""
        return self._latent_fraction

    @latent_fraction.setter
    def latent_fraction(self, value):
        self._latent_fraction = float_in_range(
            value, 0.0, 1.0, 'process latent fraction')
        self._check_fractions()

    @property
    def lost_fraction(self):
        """Get or set the fraction of process heat that is lost out of the zone."""
        return self._lost_fraction

    @lost_fraction.setter
    def lost_fraction(self, value):
        self._lost_fraction = float_in_range(
            value, 0.0, 1.0, 'process lost fraction')
        self._check_fractions()

    @property
    def convected_fraction(self):
        """Get the fraction of process heat that convects to the zone air."""
        return 1 - sum((self._radiant_fraction, self._latent_fraction,
                        self._lost_fraction))

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create a Process object from an EnergyPlus OtherEquipment IDF text string.

        Note that the OtherEquipment idf_string must use the 'equipment level'
        method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                OtherEquipment definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the OtherEquipment object.

        Returns:
            A tuple with two elements

            -   process: An Process object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the
                Process object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'OtherEquipment,')
        # check the inputs
        if len(ep_strs) > 4:
            assert ep_strs[4].lower() == 'equipmentlevel', 'Equipment must use ' \
                'Watts/Area method to be loaded from IDF to honeybee.'
        # extract the properties from the string
        watts = 0
        rad_fract = 0
        lat_fract = 0
        lost_fract = 0
        cat = 'General'
        try:
            watts = ep_strs[5] if ep_strs[5] != '' else 0
            lat_fract = ep_strs[8] if ep_strs[8] != '' else 0
            rad_fract = ep_strs[9] if ep_strs[9] != '' else 0
            lost_fract = ep_strs[10] if ep_strs[10] != '' else 0
            cat = ep_strs[12] if ep_strs[12] != '' else 'General'
        except IndexError:
            pass  # shorter equipment definition lacking fractions
        # extract the schedules from the string
        try:
            sched = schedule_dict[ep_strs[3]]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))

        # return the equipment object and the zone identifier for the equip object
        obj_id = ep_strs[0].split('..')[0]
        fuel = ep_strs[1] if ep_strs[1] != '' else 'None'
        zone_id = ep_strs[2]
        equipment = cls(obj_id, watts, sched, fuel, cat,
                        rad_fract, lat_fract, lost_fract)
        return equipment, zone_id

    @classmethod
    def from_dict(cls, data):
        """Create a Process object from a dictionary.

        Note that the dictionary must be a non-abridged version for this classmethod
        to work.

        Args:
            data: A Process dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'Process',
            "identifier": 'Wood_Burning_Fireplace_500_03',
            "display_name": 'Hearth',
            "watts": 500, # watts consumed by the process
            "schedule": {}, # ScheduleRuleset/ScheduleFixedInterval dictionary
            "fuel_type": 'OtherFuel1',  # Text for the fuel type
            "end_use_category": "Fireplaces",  # Text for the end use category
            "radiant_fraction": 0.4, # fraction of heat that is long wave radiant
            "latent_fraction": 0, # fraction of heat that is latent
            "lost_fraction": 0.5 # fraction of heat that is lost
            }
        """
        cat, rad_f, lat_f, lost_f = cls._extract_dict_props(data, 'Process')
        sched = cls._get_schedule_from_dict(data['schedule'])
        new_obj = cls(data['identifier'], data['watts'], sched, data['fuel_type'],
                      cat, rad_f, lat_f, lost_f)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a Process object from an abridged dictionary.

        Args:
            data: A ProcessAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the equipment object.

        .. code-block:: python

            {
            "type": 'ProcessAbridged',
            "identifier": 'Wood_Burning_Fireplace_500_03',
            "display_name": 'Hearth',
            "watts": 500, # watts consumed by the process
            "schedule": "Fireplace Usage Schedule", # Schedule identifier
            "fuel_type": 'OtherFuel1',  # Text for the fuel type
            "end_use_category": "Fireplaces",  # Text for the end use category
            "radiant_fraction": 0.4, # fraction of heat that is long wave radiant
            "latent_fraction": 0, # fraction of heat that is latent
            "lost_fraction": 0.5 # fraction of heat that is lost
            }
        """
        cat, rad_f, lat_f, lost_f = cls._extract_dict_props(data, 'ProcessAbridged')
        try:
            sched = schedule_dict[data['schedule']]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], data['watts'], sched, data['fuel_type'],
                      cat, rad_f, lat_f, lost_f)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of Process object.

        Note that this method only outputs a single string for the Process
        object and, to write everything needed to describe the object into an IDF,
        this object's schedule must also be written.

        Args:
            zone_identifier: Text for the zone identifier that the Process
                object is assigned to.
        """
        _idf_comments = (
            'name', 'fuel type', 'zone name', 'schedule name', 'level method',
            'power level {W}', 'power per floor area {W/m2}',
            'power per person {W/ppl}', 'latent fraction', 'radiant fraction',
            'lost fraction', 'co2 generation {m3/s-W', 'end use subcategory'
        )
        _idf_values = (
            '{}..{}'.format(self.identifier, zone_identifier), self.fuel_type,
            zone_identifier, self.schedule.identifier, 'EquipmentLevel', self.watts,
            '', '', self.latent_fraction, self.radiant_fraction, self.lost_fraction,
            '', self.end_use_category
        )
        return generate_idf_string('OtherEquipment', _idf_values, _idf_comments)

    def to_dict(self, abridged=False):
        """Process dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. (Default: False).
        """
        base = {'type': 'Process'} if not abridged else {'type': 'ProcessAbridged'}
        base['identifier'] = self.identifier
        base['watts'] = self.watts
        base['schedule'] = self.schedule.to_dict() if not \
            abridged else self.schedule.identifier
        base['fuel_type'] = self.fuel_type
        base['end_use_category'] = self.end_use_category
        base['radiant_fraction'] = self.radiant_fraction
        base['radiant_fraction'] = self.radiant_fraction
        base['latent_fraction'] = self.latent_fraction
        base['lost_fraction'] = self.lost_fraction
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    def _check_fractions(self):
        tot = (self._radiant_fraction, self._latent_fraction, self._lost_fraction)
        assert sum(tot) <= 1 + 1e-9, 'Sum of process radiant_fraction, ' \
            'latent_fraction and lost_fraction ({}) is greater than 1.'.format(sum(tot))

    @staticmethod
    def _extract_dict_props(data, expected_type):
        """Extract relevant properties from an equipment dictionary."""
        assert data['type'] == expected_type, \
            'Expected {} dictionary. Got {}.'.format(expected_type, data['type'])
        category = data['end_use_category'] if 'end_use_category' in data else 'Process'
        rad_fract = data['radiant_fraction'] if 'radiant_fraction' in data else 0
        lat_fract = data['latent_fraction'] if 'latent_fraction' in data else 0
        lost_fract = data['lost_fraction'] if 'lost_fraction' in data else 0
        return category, rad_fract, lat_fract, lost_fract

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.watts, hash(self.schedule), self.fuel_type,
                self.end_use_category, self.radiant_fraction, self.latent_fraction,
                self.lost_fraction)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, Process) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = Process(
            self.identifier, self.watts, self.schedule, self.fuel_type,
            self.end_use_category, self.radiant_fraction, self.latent_fraction,
            self.lost_fraction)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def __repr__(self):
        return 'Process: {} [{} W] [schedule: {}] [fuel: {}]'.format(
            self.display_name, round(self.watts, 1), self.schedule.display_name,
            self.fuel_type)
