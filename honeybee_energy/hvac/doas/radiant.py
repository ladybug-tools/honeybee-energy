# coding=utf-8
"""Low temperature radiant with DOAS HVAC system."""
from __future__ import division

from ._base import _DOASBase

from honeybee._lockable import lockable
from honeybee.typing import float_positive, valid_string


@lockable
class RadiantwithDOAS(_DOASBase):
    """Low temperature radiant with DOAS HVAC system.

    This HVAC template will change the floor and/or ceiling constructions
    of the Rooms that it is applied to, replacing them with a construction that
    aligns with the radiant_type property (eg. CeilingMetalPanel).

    All rooms/zones in the system are connected to a Dedicated Outdoor Air System
    (DOAS) that supplies a constant volume of ventilation air at the same temperature
    to all rooms/zones. The ventilation air temperature will vary from 21.1C (70F)
    to 15.5C (60F) depending on the outdoor air temperature (the DOAS supplies cooler air
    when outdoor conditions are warmer). The ventilation air temperature is maintained
    by a two-speed direct expansion (DX) cooling coil and a single-speed DX
    heating coil with backup electrical resistance heat.

    The heating and cooling needs of the space are met with the radiant constructions,
    which use chilled water at 12.8C (55F) and a hot water temperature somewhere
    between 32.2C (90F) and 49C (120F) (warmer temperatures are used in colder
    climate zones).

    Note that radiant systems are particularly limited in cooling capacity and
    using them may result in many unmet hours. To reduce unmet hours, one can
    remove carpets, reduce internal loads, reduce solar and envelope gains during
    peak times, add thermal mass, and use an expanded comfort range.

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

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * DOAS_Radiant_Chiller_Boiler
            * DOAS_Radiant_Chiller_ASHP
            * DOAS_Radiant_Chiller_DHW
            * DOAS_Radiant_ACChiller_Boiler
            * DOAS_Radiant_ACChiller_ASHP
            * DOAS_Radiant_ACChiller_DHW
            * DOAS_Radiant_DCW_Boiler
            * DOAS_Radiant_DCW_ASHP
            * DOAS_Radiant_DCW_DHW

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
        radiant_type: Text to indicate which faces are thermally active. Note
            that systems are assumed to be embedded in concrete slabs unless
            CeilingMetalPanel or FloorWithHardwood is specified. Choose from the
            following. (Default: Floor).

            * Floor
            * Ceiling
            * FloorWithCarpet
            * CeilingMetalPanel
            * FloorWithHardwood

        minimum_operation_time: A number for the minimum number of hours of operation
            for the radiant system before it shuts off. Note that this has no effect
            if the radiant_type is not in a slab. (Default: 1).
        switch_over_time: A number for the minimum number of hours for when the system
            can switch between heating and cooling. Note that this has no effect
            if the radiant_type is not in a slab. (Default: 24).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * demand_controlled_ventilation
        * doas_availability_schedule
        * minimum_operation_time
        * switch_over_time
        * radiant_type
        * schedules
        * has_district_heating
        * has_district_cooling
        * user_data
        * properties
    """
    __slots__ = ('_radiant_type', '_minimum_operation_time', '_switch_over_time')

    EQUIPMENT_TYPES = (
        'DOAS_Radiant_Chiller_Boiler',
        'DOAS_Radiant_Chiller_ASHP',
        'DOAS_Radiant_Chiller_DHW',
        'DOAS_Radiant_ACChiller_Boiler',
        'DOAS_Radiant_ACChiller_ASHP',
        'DOAS_Radiant_ACChiller_DHW',
        'DOAS_Radiant_DCW_Boiler',
        'DOAS_Radiant_DCW_ASHP',
        'DOAS_Radiant_DCW_DHW'
    )

    radiant_typeS = ('Floor', 'Ceiling', 'FloorWithCarpet',
                     'CeilingMetalPanel', 'FloorWithHardwood')

    def __init__(self, identifier, vintage='ASHRAE_2019', equipment_type=None,
                 sensible_heat_recovery=0, latent_heat_recovery=0,
                 demand_controlled_ventilation=False, doas_availability_schedule=None,
                 radiant_type='Floor', minimum_operation_time=1, switch_over_time=24):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _DOASBase.__init__(
            self, identifier, vintage, equipment_type, sensible_heat_recovery,
            latent_heat_recovery, demand_controlled_ventilation,
            doas_availability_schedule
        )

        # set the main features of the HVAC system
        self.radiant_type = radiant_type
        self.minimum_operation_time = minimum_operation_time
        self.switch_over_time = switch_over_time

    @property
    def radiant_type(self):
        """Get or set text to indicate the type of radiant system."""
        return self._radiant_type

    @radiant_type.setter
    def radiant_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.radiant_typeS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'radiant_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.radiant_typeS))
        self._radiant_type = value

    @property
    def minimum_operation_time(self):
        """Get or set a the minimum hours of operation before the system shuts off."""
        return self._minimum_operation_time

    @minimum_operation_time.setter
    def minimum_operation_time(self, value):
        self._minimum_operation_time = \
            float_positive(value, 'hvac minimum operation time')

    @property
    def switch_over_time(self):
        """Get or set the minimum hours the system can switch between heating/cooling."""
        return self._switch_over_time

    @switch_over_time.setter
    def switch_over_time(self, value):
        self._switch_over_time = float_positive(value, 'hvac switch over time')

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
            "doas_availability_schedule": {},  # Schedule for DOAS availability or None
            "radiant_type": "Ceiling",
            "minimum_operation_time": 1,
            "switch_over_time": 24
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the key features and properties of the HVAC
        sensible, latent, dcv = cls._properties_from_dict(data)
        f_type, mot, sot = cls._radiant_properties_from_dict(data)
        # extract the schedule
        doas_avail = cls._get_schedule_from_dict(data['doas_availability_schedule']) if \
            'doas_availability_schedule' in data and \
            data['doas_availability_schedule'] is not None else None

        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent, dcv, doas_avail, f_type, mot, sot)
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
            "doas_availability_schedule": "",  # Schedule id for DOAS availability
            "radiant_type": "Ceiling",
            "minimum_operation_time": 1,
            "switch_over_time": 24
            }
        """
        assert cls.__name__ in data['type'], \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the key features and properties of the HVAC
        sensible, latent, dcv = cls._properties_from_dict(data)
        f_type, mot, sot = cls._radiant_properties_from_dict(data)
        # extract the schedule
        doas_avail = None
        if 'doas_availability_schedule' in data and \
                data['doas_availability_schedule'] is not None:
            try:
                doas_avail = schedule_dict[data['doas_availability_schedule']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent, dcv, doas_avail, f_type, mot, sot)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_dict(self, abridged=False):
        """DOAS system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """
        base = self._base_dict(abridged)
        base['radiant_type'] = self.radiant_type
        base['minimum_operation_time'] = self.minimum_operation_time
        base['switch_over_time'] = self.switch_over_time
        return base

    @staticmethod
    def _radiant_properties_from_dict(data):
        """Extract basic radiant properties from a dictionary and assign defaults."""
        mot = data['minimum_operation_time'] if 'minimum_operation_time' in data else 1
        sot = data['switch_over_time'] if 'switch_over_time' in data else 24
        rad_type = data['radiant_type'] if 'radiant_type' in data and \
            data['radiant_type'] is not None else 'Floor'
        return rad_type, mot, sot

    def __copy__(self):
        new_obj = self.__class__(
            self._identifier, self._vintage, self._equipment_type,
            self._sensible_heat_recovery, self._latent_heat_recovery,
            self._demand_controlled_ventilation, self._doas_availability_schedule,
            self._radiant_type, self._minimum_operation_time,
            self._switch_over_time)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._sensible_heat_recovery, self._latent_heat_recovery,
                self._demand_controlled_ventilation,
                hash(self._doas_availability_schedule),
                self._radiant_type, self._minimum_operation_time, self._switch_over_time)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)
