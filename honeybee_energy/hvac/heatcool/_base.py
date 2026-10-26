# coding=utf-8
"""Base class for all heating/cooling systems without any ventilation."""
from __future__ import division
import os

from honeybee._lockable import lockable
from honeybee.typing import float_in_range
from honeybee.altnumber import autosize

from .._template import _TemplateSystem, _EnumerationBase
from ..idealair import IdealAirSystem
from ...properties.extension import HeatCoolSystemProperties


@lockable
class _HeatCoolBase(_TemplateSystem):
    """Base class for all heating/cooling systems without any ventilation.

    Args:
        identifier: Text string for system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        vintage: Text for the vintage of the template system. This will be used
            to set efficiencies for various pieces of equipment within the system.
            Choose from the following.

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013
            * ASHRAE_2016
            * ASHRAE_2019

        equipment_type: Text for the specific type of the system and equipment.
            For example, 'Baseboard gas boiler'.
        unit_ventilators: Boolean to note whether individual zone ventilators are
            included with the basic heating and cooling system (True) or the system only
            performs heating and cooling without any ventilation (False). Unlike a DOAS,
            unit ventilators do not pass the outdoor air through heating or cooling
            coils to condition it for the space. However, heat recovery effectiveness
            can be specified, which can temper the air supplied to the zone by the
            ventilator with exhaust air. All air flow through this ventilator
            is always balanced for each zone between supply and exhaust and the
            total flow rate is determined by checking the ventilation and exhaust
            requirements of the rooms to which the system is assigned. (Default: False).
        sensible_heat_recovery: A number between 0 and 1 for the effectiveness of
            sensible heat recovery within unit ventilators if specified. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness of
            latent heat recovery within unit ventilators if specified. (Default: 0).
        vent_availability_schedule: An optional On/Off discrete schedule to specify when
            unit ventilators shut off (assuming that the unit_ventilators is True).
            This will not only reduce heating and cooling load by preventing
            outdoor air from flowing but will also shut off the fans, which can
            result in more energy savings when spaces served by the ventilators
            are completely unoccupied. If None, the unit ventilators will be
            always on. (Default: None).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * unit_ventilators
        * sensible_heat_recovery
        * latent_heat_recovery
        * vent_availability_schedule
        * has_air_loop
        * has_district_heating
        * has_district_cooling
        * balances_exhaust
        * user_data
        * properties
    """
    __slots__ = (
        '_unit_ventilators', '_sensible_heat_recovery', '_latent_heat_recovery',
        '_vent_availability_schedule', '_properties'
    )
    COOL_ONLY_TYPES = (
        'EvapCoolers', 'FCU_Chiller', 'FCU_ACChiller', 'FCU_DCW',
        'ResidentialAC', 'WindowAC'
    )
    HEAT_ONLY_TYPES = (
        'ElectricBaseboard', 'BoilerBaseboard', 'ASHPBaseboard',
        'DHWBaseboard', 'GasHeaters', 'ResidentialHPNoCool', 'ResidentialFurnace'
    )

    def __init__(
        self, identifier, vintage='ASHRAE_2019', equipment_type=None,
        unit_ventilators=False, sensible_heat_recovery=0, latent_heat_recovery=0,
        vent_availability_schedule=None
    ):
        # initialize base HVAC system properties
        _TemplateSystem.__init__(self, identifier, vintage, equipment_type)
        self.unit_ventilators = unit_ventilators
        self.sensible_heat_recovery = sensible_heat_recovery
        self.latent_heat_recovery = latent_heat_recovery
        self.vent_availability_schedule = vent_availability_schedule
        self._properties = HeatCoolSystemProperties(self)

    @property
    def unit_ventilators(self):
        """Get or set a boolean for whether the system includes unit ventilators."""
        return self._unit_ventilators

    @unit_ventilators.setter
    def unit_ventilators(self, value):
        self._unit_ventilators = bool(value)

    @property
    def sensible_heat_recovery(self):
        """Get or set a number for the effectiveness of sensible heat recovery."""
        return self._sensible_heat_recovery

    @sensible_heat_recovery.setter
    def sensible_heat_recovery(self, value):
        if value is None or value == 0:
            self._sensible_heat_recovery = 0
        else:
            self._sensible_heat_recovery = \
                float_in_range(value, 0.0, 1.0, 'hvac sensible heat recovery')

    @property
    def latent_heat_recovery(self):
        """Get or set a number for the effectiveness of latent heat recovery."""
        return self._latent_heat_recovery

    @latent_heat_recovery.setter
    def latent_heat_recovery(self, value):
        if value is None:
            self._latent_heat_recovery = 0
        else:
            self._latent_heat_recovery = \
                float_in_range(value, 0.0, 1.0, 'hvac latent heat recovery')

    @property
    def vent_availability_schedule(self):
        """Get or set am on/off schedule for availability of the ventilators.
        """
        return self._vent_availability_schedule

    @vent_availability_schedule.setter
    def vent_availability_schedule(self, value):
        if value is not None:
            self._check_schedule(value, 'vent_availability_schedule')
            value.lock()   # lock editing in case schedule has multiple references
        self._vent_availability_schedule = value

    @property
    def schedules(self):
        """Get an array of all the schedules associated with the HVAC system."""
        schedules = []
        if self._vent_availability_schedule is not None:
            schedules.append(self._vent_availability_schedule)
        return schedules

    @property
    def has_air_loop(self):
        """Always False for HeatCool systems."""
        return False

    @property
    def balances_exhaust(self):
        """Always False for HeatCool systems."""
        return False

    def to_ideal_air_equivalent(self):
        """Get a version of this HVAC as an IdealAirSystem."""
        i_sys = IdealAirSystem(self.identifier)
        if self.equipment_type in self.COOL_ONLY_TYPES:
            i_sys.heating_limit = 0
        if self.equipment_type in self.HEAT_ONLY_TYPES:
            i_sys.cooling_limit = 0
        i_sys.economizer_type = 'NoEconomizer'
        i_sys._display_name = self._display_name
        return i_sys

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A HeatCool dictionary in following the format below.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "unit_ventilators": True,  # boolean for unit ventilators
            "sensible_heat_recovery": 0.75,  # sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # latent heat recovery effectiveness
            "vent_availability_schedule": {},  # Schedule for DOAS availability or None
            "properties": { ... } # HeatCoolSystemProperties as a dict
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the schedule
        vent_avail = cls._get_schedule_from_dict(data['vent_availability_schedule']) if \
            'vent_availability_schedule' in data and \
            data['vent_availability_schedule'] is not None else None
        # extract the key features and properties of the HVAC
        erv, sensible, latent = cls._properties_from_dict(data)
        # create the object
        new_obj = cls(
            data['identifier'], data['vintage'], data['equipment_type'],
            erv, sensible, latent, vent_avail
        )
        # add all optional properties
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a HVAC object from an abridged dictionary.

        Args:
            data: A HeatCool abridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Setpoint object.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "unit_ventilators": True,  # boolean for unit ventilators
            "sensible_heat_recovery": 0.75,  # sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # latent heat recovery effectiveness
            "vent_availability_schedule": ""  # Schedule id for ventilation availability
            "properties": { ... } # dict of the HeatCoolSystemProperties
            }
        """
        assert cls.__name__ in data['type'], \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the schedule
        vent_avail = None
        if 'vent_availability_schedule' in data and \
                data['vent_availability_schedule'] is not None:
            try:
                vent_avail = schedule_dict[data['vent_availability_schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        # extract the key features and properties of the HVAC
        erv, sensible, latent = cls._properties_from_dict(data)
        # create the object
        new_obj = cls(
            data['identifier'], data['vintage'], data['equipment_type'],
            erv, sensible, latent, vent_avail
        )
        # add all optional properties
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_dict(self, abridged=False):
        """HeatCool system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """

        """Get a base dictionary of the HeatCool system."""
        base = {'type': self.__class__.__name__}
        base['identifier'] = self.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        base['vintage'] = self.vintage
        base['equipment_type'] = self.equipment_type
        if self.unit_ventilators:
            base['unit_ventilators'] = self.unit_ventilators
        if self.sensible_heat_recovery != 0:
            base['sensible_heat_recovery'] = self.sensible_heat_recovery
        if self.latent_heat_recovery != 0:
            base['latent_heat_recovery'] = self.latent_heat_recovery
        if self.vent_availability_schedule is not None:
            base['vent_availability_schedule'] = \
                self.vent_availability_schedule.identifier if \
                abridged else self.vent_availability_schedule.to_dict()
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    @staticmethod
    def _properties_from_dict(data):
        """Extract basic properties from a dictionary and assign defaults."""
        erv = data['unit_ventilators'] if 'unit_ventilators' in data else False
        sensible = data['sensible_heat_recovery'] if \
            'sensible_heat_recovery' in data else 0
        sensible = sensible if sensible != autosize.to_dict() else 0
        latent = data['latent_heat_recovery'] if \
            'latent_heat_recovery' in data else 0
        latent = latent if latent != autosize.to_dict() else 0
        return erv, sensible, latent

    def __copy__(self):
        new_obj = self.__class__(
            self._identifier, self.vintage, self._equipment_type, self._unit_ventilators,
            self._sensible_heat_recovery, self._latent_heat_recovery,
            self._vent_availability_schedule
        )
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._unit_ventilators,
                self._sensible_heat_recovery, self._latent_heat_recovery,
                hash(self._vent_availability_schedule))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)


class _HeatCoolEnumeration(_EnumerationBase):
    """Enumerates the systems that inherit from _HeatCoolBase."""

    def __init__(self, import_modules=True):
        if import_modules:
            self._import_modules(
                os.path.dirname(__file__), 'honeybee_energy.hvac.heatcool')

        self._HVAC_TYPES = {}
        self._EQUIPMENT_TYPES = {}
        for clss in _HeatCoolBase.__subclasses__():
            self._HVAC_TYPES[clss.__name__] = clss
            for equip_type in clss.EQUIPMENT_TYPES:
                self._EQUIPMENT_TYPES[equip_type] = clss
