# coding=utf-8
"""Base class for all HVAC systems with DOAS ventilation."""
from __future__ import division
import os

from honeybee._lockable import lockable
from honeybee.typing import float_in_range
from honeybee.altnumber import autosize

from .._template import _TemplateSystem, _EnumerationBase


@lockable
class _DOASBase(_TemplateSystem):
    """Base class for all HVAC systems with DOAS ventilation.

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
            For example, 'DOAS with fan coil chiller with boiler'.
        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. (Default: 0).
        demand_controlled_ventilation: Boolean to note whether demand controlled
            ventilation should be used on the system, which will vary the amount
            of ventilation air according to the occupancy schedule of the
            Rooms. (Default: False).
        doas_availability_schedule: An optional On/Off discrete schedule to set when
            the dedicated outdoor air system (DOAS) shuts off. This will not only
            prevent any outdoor air from flowing thorough the system but will also
            shut off the fans, which can result in more energy savings when spaces
            served by the DOAS are completely unoccupied. If None, the DOAS will be
            always on. (Default: None).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * demand_controlled_ventilation
        * doas_availability_schedule
        * schedules
        * user_data
    """
    __slots__ = ('_sensible_heat_recovery', '_latent_heat_recovery',
                 '_demand_controlled_ventilation', '_doas_availability_schedule')

    def __init__(self, identifier, vintage='ASHRAE_2019', equipment_type=None,
                 sensible_heat_recovery=0, latent_heat_recovery=0,
                 demand_controlled_ventilation=False, doas_availability_schedule=None):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _TemplateSystem.__init__(self, identifier, vintage, equipment_type)

        # set the main features of the HVAC system
        self.sensible_heat_recovery = sensible_heat_recovery
        self.latent_heat_recovery = latent_heat_recovery
        self.demand_controlled_ventilation = demand_controlled_ventilation
        self.doas_availability_schedule = doas_availability_schedule

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
    def demand_controlled_ventilation(self):
        """Get or set a boolean for whether demand controlled ventilation is present."""
        return self._demand_controlled_ventilation

    @demand_controlled_ventilation.setter
    def demand_controlled_ventilation(self, value):
        self._demand_controlled_ventilation = bool(value)

    @property
    def doas_availability_schedule(self):
        """Get or set am on/off schedule for availability of the DOAS air loop.
        """
        return self._doas_availability_schedule

    @doas_availability_schedule.setter
    def doas_availability_schedule(self, value):
        if value is not None:
            self._check_schedule(value, 'doas_availability_schedule')
            value.lock()   # lock editing in case schedule has multiple references
        self._doas_availability_schedule = value

    @property
    def schedules(self):
        """Get an array of all the schedules associated with the HVAC system."""
        schedules = []
        if self._doas_availability_schedule is not None:
            schedules.append(self._doas_availability_schedule)
        return schedules

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A DOAS dictionary in following the format below.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            "demand_controlled_ventilation": False  # Boolean for DCV
            "doas_availability_schedule": {}  # Schedule for DOAS availability or None
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the key features and properties of the HVAC
        sensible, latent, dcv = cls._properties_from_dict(data)
        # extract the schedule
        doas_avail = cls._get_schedule_from_dict(data['doas_availability_schedule']) if \
            'doas_availability_schedule' in data and \
            data['doas_availability_schedule'] is not None else None

        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent, dcv, doas_avail)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a HVAC object from an abridged dictionary.

        Args:
            data: A DOAS abridged dictionary in following the format below.
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
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            "demand_controlled_ventilation": False  # Boolean for DCV
            "doas_availability_schedule": ""  # Schedule id for DOAS availability
            }
        """
        assert cls.__name__ in data['type'], \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the key features and properties of the HVAC
        sensible, latent, dcv = cls._properties_from_dict(data)
        # extract the schedule
        doas_avail = None
        if 'doas_availability_schedule' in data and \
                data['doas_availability_schedule'] is not None:
            try:
                doas_avail = schedule_dict[data['doas_availability_schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent, dcv, doas_avail)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_dict(self, abridged=False):
        """All air system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """
        class_type = '{}Abridged'.format(self.__class__.__name__) \
            if abridged else self.__class__.__name__
        base = {'type': class_type}
        base['identifier'] = self.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        base['vintage'] = self.vintage
        base['equipment_type'] = self.equipment_type
        if self.sensible_heat_recovery != 0:
            base['sensible_heat_recovery'] = self.sensible_heat_recovery
        if self.latent_heat_recovery != 0:
            base['latent_heat_recovery'] = self.latent_heat_recovery
        base['demand_controlled_ventilation'] = self.demand_controlled_ventilation
        if self.doas_availability_schedule is not None:
            base['doas_availability_schedule'] = \
                self.doas_availability_schedule.identifier if \
                abridged else self.doas_availability_schedule.to_dict()
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    @staticmethod
    def _properties_from_dict(data):
        """Extract basic properties from a dictionary and assign defaults."""
        sensible = data['sensible_heat_recovery'] if \
            'sensible_heat_recovery' in data else 0
        sensible = sensible if sensible != autosize.to_dict() else 0
        latent = data['latent_heat_recovery'] if \
            'latent_heat_recovery' in data else 0
        latent = latent if latent != autosize.to_dict() else 0
        dcv = data['demand_controlled_ventilation'] \
            if 'demand_controlled_ventilation' in data else False
        return sensible, latent, dcv

    def __copy__(self):
        new_obj = self.__class__(
            self._identifier, self._vintage, self._equipment_type,
            self._sensible_heat_recovery, self._latent_heat_recovery,
            self._demand_controlled_ventilation, self._doas_availability_schedule)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._sensible_heat_recovery, self._latent_heat_recovery,
                self._demand_controlled_ventilation,
                hash(self._doas_availability_schedule))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)


class _DOASEnumeration(_EnumerationBase):
    """Enumerates the systems that inherit from _DOASBase."""

    def __init__(self, import_modules=True):
        if import_modules:
            self._import_modules(os.path.dirname(__file__), 'honeybee_energy.hvac.doas')

        self._HVAC_TYPES = {}
        self._EQUIPMENT_TYPES = {}
        for clss in _DOASBase.__subclasses__():
            self._HVAC_TYPES[clss.__name__] = clss
            for equip_type in clss.EQUIPMENT_TYPES:
                self._EQUIPMENT_TYPES[equip_type] = clss
