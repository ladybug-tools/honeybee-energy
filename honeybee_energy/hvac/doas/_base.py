# coding=utf-8
"""Base class for all HVAC systems with DOAS ventilation."""
from __future__ import division

from .._template import _TemplateSystem, _EnumerationBase

from honeybee._lockable import lockable
from honeybee.typing import float_in_range
from honeybee.altnumber import autosize

import os


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

        equipment_type: Text for the specific type of the system and equipment.
            For example, 'DOAS with fan coil chiller with boiler'.
        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. If None, it will be
            whatever is recommended for the given vintage (Default: autosize).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. If None, it will be
            whatever is recommended for the given vintage (Default: autosize).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * schedules
    """
    __slots__ = ('_sensible_heat_recovery', '_latent_heat_recovery')

    def __init__(self, identifier, vintage='ASHRAE_2013', equipment_type=None,
                 sensible_heat_recovery=autosize, latent_heat_recovery=autosize):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _TemplateSystem.__init__(self, identifier, vintage, equipment_type)

        # set the main features of the HVAC system
        self.sensible_heat_recovery = sensible_heat_recovery
        self.latent_heat_recovery = latent_heat_recovery

    @property
    def sensible_heat_recovery(self):
        """Get or set a number for the effectiveness of sensible heat recovery.

        If None or autosize, it will be whatever is recommended for the given vintage.
        """
        return self._sensible_heat_recovery

    @sensible_heat_recovery.setter
    def sensible_heat_recovery(self, value):
        if value == autosize or value is None:
            self._sensible_heat_recovery = autosize
        else:
            self._sensible_heat_recovery = \
                float_in_range(value, 0.0, 1.0, 'hvac sensible heat recovery')

    @property
    def latent_heat_recovery(self):
        """Get or set a number for the effectiveness of latent heat recovery.

        If None or autosize, it will be whatever is recommended for the given vintage.
        """
        return self._latent_heat_recovery

    @latent_heat_recovery.setter
    def latent_heat_recovery(self, value):
        if value == autosize or value is None:
            self._latent_heat_recovery = autosize
        else:
            self._latent_heat_recovery = \
                float_in_range(value, 0.0, 1.0, 'hvac latent heat recovery')

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
            "vintage": "ASHRAE_2013",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])

        # extract the key features and properties of the HVAC
        sensible = data['sensible_heat_recovery'] if \
            'sensible_heat_recovery' in data else None
        sensible = sensible if sensible != autosize.to_dict() else autosize
        latent = data['latent_heat_recovery'] if \
            'latent_heat_recovery' in data else None
        latent = latent if latent != autosize.to_dict() else autosize

        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
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
            "vintage": "ASHRAE_2013",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            }
        """
        # this is the same as the from_dict method for as long as there are not schedules
        return cls.from_dict(data)

    def to_dict(self, abridged=False):
        """All air system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """
        base = {'type': self.__class__.__name__}
        base['identifier'] = self.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        base['vintage'] = self.vintage
        base['equipment_type'] = self.equipment_type
        if self.sensible_heat_recovery != autosize:
            base['sensible_heat_recovery'] = self.sensible_heat_recovery
        if self.latent_heat_recovery != autosize:
            base['latent_heat_recovery'] = self.latent_heat_recovery
        return base

    def __copy__(self):
        new_obj = self.__class__(
            self._identifier, self._vintage, self._equipment_type,
            self._sensible_heat_recovery, self._latent_heat_recovery)
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._sensible_heat_recovery, self._latent_heat_recovery)

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
