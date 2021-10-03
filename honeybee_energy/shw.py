# coding=utf-8
"""Detailed Service Hot Water (SHW) system template used to meet hot water demand."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, valid_string, float_positive
from honeybee.altnumber import autocalculate


@lockable
class SHWSystem(object):
    """Detailed Service Hot Water (SHW) system template used to meet hot water demand.

    Args:
        identifier: Text string for the system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        equipment_type: Text for the specific type of the system and equipment. (Default:
            Gas_WaterHeater) Choose from.

            * Gas_WaterHeater
            * Electric_WaterHeater
            * HeatPump_WaterHeater
            * Gas_TanklessHeater
            * Electric_TanklessHeater

        heater_efficiency: A number for the efficiency of the heater within
            the system. For Gas systems, this is the efficiency of the burner.
            For HeatPump systems, this is the rated COP of the system. For electric
            systems, this should usually be set to 1. If set to None or Autocalculate,
            this value will automatically be set based on the equipment_type. See below
            for the default value for each equipment type. (Default: None).

            * Gas_WaterHeater - 0.8
            * Electric_WaterHeater - 1.0
            * HeatPump_WaterHeater - 3.5
            * Gas_TanklessHeater - 0.8
            * Electric_TanklessHeater - 1.0

        ambient_condition: A number for the ambient temperature in which the hot
            water tank is located [C]. This can also be the identifier of a Room
            in which the tank is located. (Default: 22).
        ambient_loss_coefficient: A number for the loss of heat from the water heater
            tank to the surrounding ambient conditions [W/K]. (Default: 6 W/K).

    Properties:
        * identifier
        * display_name
        * equipment_type
        * heater_efficiency
        * ambient_condition
        * ambient_loss_coefficient
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_equipment_type', '_heater_efficiency',
                 '_ambient_condition', '_ambient_loss_coefficient',
                 '_locked', '_user_data')

    EQUIPMENT_TYPES = (
        'Gas_WaterHeater',
        'Electric_WaterHeater',
        'HeatPump_WaterHeater',
        'Gas_TanklessHeater',
        'Electric_TanklessHeater'
    )
    DEFAULT_EFFICIENCIES = {
        'Gas_WaterHeater': 0.8,
        'Electric_WaterHeater': 1.0,
        'HeatPump_WaterHeater': 3.5,
        'Gas_TanklessHeater': 0.8,
        'Electric_TanklessHeater': 1.0
    }

    def __init__(self, identifier, equipment_type='Gas_WaterHeater',
                 heater_efficiency=autocalculate, ambient_condition=22,
                 ambient_loss_coefficient=6):
        """Initialize SHWSystem."""
        # assign the identifier and general properties
        self.identifier = identifier
        self._display_name = None
        self._user_data = None

        # set some dummy values that will get overwritten but let the checks pass
        self._heater_efficiency = None
        self._ambient_condition = ''

        # set the main features of the HVAC system
        self.equipment_type = equipment_type
        self.heater_efficiency = heater_efficiency
        self.ambient_condition = ambient_condition
        self.ambient_loss_coefficient = ambient_loss_coefficient

    @property
    def identifier(self):
        """Get or set the text string for HVAC system identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'HVAC system identifier')

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def equipment_type(self):
        """Get or set text to indicate the type of the equipment."""
        return self._equipment_type

    @equipment_type.setter
    def equipment_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.EQUIPMENT_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'equipment_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.EQUIPMENT_TYPES))
        self._equipment_type = value
        self._check_efficiency_equipment_type()
        self._check_condition_equipment_type()

    @property
    def heater_efficiency(self):
        """Get or set a number for the efficiency of the heater within the system."""
        return self._heater_efficiency if self._heater_efficiency is not None \
            else self.DEFAULT_EFFICIENCIES[self._equipment_type]

    @heater_efficiency.setter
    def heater_efficiency(self, value):
        if value == autocalculate:
            value = None
        elif value is not None:
            value = float_positive(value, 'shw heater efficiency')
        self._heater_efficiency = value
        self._check_efficiency_equipment_type()

    @property
    def ambient_condition(self):
        """Get or set a number for the ambient temperature where the tank is located [C].

        This can also be the identifier of a Room in which the tank is located.
        """
        return self._ambient_condition

    @ambient_condition.setter
    def ambient_condition(self, value):
        try:
            value = float_positive(value, 'shw ambient condition')
        except Exception:
            assert isinstance(value, str), 'SHW ambient_condition must be either a ' \
                'temperature in Celsius or the identifier of a Room to locate the ' \
                'tank. Got {}.'.format(type(value))
            value = valid_ep_string(value)
        self._ambient_condition = value
        self._check_condition_equipment_type()

    @property
    def ambient_loss_coefficient(self):
        """Get or set a number the loss to the surrounding ambient conditions [W/K]."""
        return self._ambient_loss_coefficient

    @ambient_loss_coefficient.setter
    def ambient_loss_coefficient(self, value):
        self._ambient_loss_coefficient = \
            float_positive(value, 'shw ambient loss coefficient')

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    @classmethod
    def from_dict(cls, data):
        """Create a SHWSystem object from a dictionary.

        Args:
            data: A SHWSystem dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SHWSystem",
            "identifier": "HP SHW System 3.8",  # identifier for the SHWSystem
            "display_name": "Bathroom Service Hot Water",  # name for the SHWSystem
            "equipment_type": 'HeatPump_WaterHeater',  # Equipment type
            "heater_efficiency": 3.8,  # Heater efficiency/COP
            "ambient_condition": "Basement Room",  # Identifier for room with the tank
            "ambient_loss_coefficient": 5  # Ambient loss from the tank [W/K]
            }
        """
        assert data['type'] == 'SHWSystem', \
            'Expected SHWSystem dictionary. Got {}.'.format(data['type'])

        # extract the key features and properties of the SHW
        equip = data['equipment_type'] if 'equipment_type' in data and \
            data['equipment_type'] is not None else 'Gas_WaterHeater'
        eff = data['heater_efficiency'] if 'heater_efficiency' in data and \
            data['heater_efficiency'] != autocalculate.to_dict() else None
        cond = data['ambient_condition'] if 'ambient_condition' in data and \
            data['ambient_condition'] is not None else 22
        coeff = data['ambient_loss_coefficient'] if 'ambient_loss_coefficient' \
            in data and data['ambient_loss_coefficient'] is not None else 6

        new_obj = cls(data['identifier'], equip, eff, cond, coeff)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_dict(self):
        """SHWSystem dictionary representation."""
        base = {'type': 'SHWSystem'}
        base['identifier'] = self.identifier
        base['equipment_type'] = self.equipment_type
        base['heater_efficiency'] = self.heater_efficiency
        base['ambient_condition'] = self.ambient_condition
        base['ambient_loss_coefficient'] = self.ambient_loss_coefficient
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def _check_efficiency_equipment_type(self):
        """Check that the efficiency is suitable for the equipment type"""
        if self._heater_efficiency is not None:
            if self._equipment_type != 'HeatPump_WaterHeater':
                assert self.heater_efficiency <= 1, 'heater_efficiency must be less ' \
                    'then 1 when using {} equipment_tpe. Got {}.'.format(
                        self._equipment_type, self._heater_efficiency)

    def _check_condition_equipment_type(self):
        """Check that the ambient condition is suitable for th equipment type"""
        if self._equipment_type == 'HeatPump_WaterHeater':
                assert isinstance(self.ambient_condition, str), 'ambient_condition ' \
                    'must be a Room when using HeatPump_WaterHeater.'

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        new_obj = SHWSystem(
            self._identifier, self._equipment_type, self._heater_efficiency,
            self._ambient_condition, self._ambient_loss_coefficient)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (
            self._identifier, self._equipment_type, self._heater_efficiency,
            self._ambient_condition, self._ambient_loss_coefficient)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SHWSystem) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'SHWSystem: {}'.format(self.display_name)
