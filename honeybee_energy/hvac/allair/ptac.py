# coding=utf-8
"""Packaged Terminal Air Conditioning (PTAC) or Heat Pump (PTHP) HVAC system."""
from __future__ import division

from ._base import _AllAirBase

from honeybee._lockable import lockable


@lockable
class PTAC(_AllAirBase):
    """Packaged Terminal Air Conditioning (PTAC/HP) HVAC system. (aka. System 1 or 2).

    Each room/zone receives its own packaged unit that supplies heating, cooling
    and ventilation. Cooling is always done via a single-speed direct expansion (DX)
    cooling coil. Heating can be done via a heating coil in the unit or via an
    external baseboard. Fans are constant volume.

    PTAC/HP systems are the traditional baseline system for residential buildings.

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

            * PTAC_ElectricBaseboard
            * PTAC_BoilerBaseboard
            * PTAC_DHWBaseboard
            * PTAC_GasHeaters
            * PTAC_ElectricCoil
            * PTAC_GasCoil
            * PTAC_Boiler
            * PTAC_ASHP
            * PTAC_DHW
            * PTAC
            * PTHP

        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. When this is not zero,
            heat recovery is modeled using an ERV connected to the PTAC. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. When this is not zero,
            heat recovery is modeled using an ERV connected to the PTAC. (Default: 0).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * schedules
        * has_air_loop
        * has_district_heating
        * has_district_cooling
        * balances_exhaust
        * user_data
        * properties

    Note:
        [1] American Society of Heating, Refrigerating and Air-Conditioning Engineers,
        Inc. (2007). Ashrae standard 90.1. Atlanta, GA. https://www.ashrae.org/\
technical-resources/standards-and-guidelines/read-only-versions-of-ashrae-standards
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'PTAC_ElectricBaseboard',
        'PTAC_BoilerBaseboard',
        'PTAC_DHWBaseboard',
        'PTAC_GasHeaters',
        'PTAC_ElectricCoil',
        'PTAC_GasCoil',
        'PTAC_Boiler',
        'PTAC_ASHP',
        'PTAC_DHW',
        'PTAC',
        'PTHP'
    )
    _has_air_loop = False

    def __init__(
        self, identifier, vintage='ASHRAE_2019', equipment_type=None,
        sensible_heat_recovery=0, latent_heat_recovery=0
    ):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _AllAirBase.__init__(
            self, identifier, vintage, equipment_type,
            sensible_heat_recovery=sensible_heat_recovery,
            latent_heat_recovery=latent_heat_recovery
        )

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A HVAC dictionary in following the format below.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": ""  # text for the HVAC equipment type
            }
        """
        assert cls.__name__ in data['type'], \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        _, sensible, latent, _ = cls._properties_from_dict(data)
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      sensible, latent)
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
            data: An abridged dictionary in following the format below.
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
            "equipment_type": ""  # text for the HVAC equipment type
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
        if self.sensible_heat_recovery != 0:
            base['sensible_heat_recovery'] = self.sensible_heat_recovery
        if self.latent_heat_recovery != 0:
            base['latent_heat_recovery'] = self.latent_heat_recovery
        return base

    def __copy__(self):
        new_obj = self.__class__(
            self.identifier, self.vintage, self.equipment_type,
            self._sensible_heat_recovery, self._latent_heat_recovery
        )
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._sensible_heat_recovery, self._latent_heat_recovery)
