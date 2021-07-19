# coding=utf-8
"""Packaged Terminal Air Conditioning (PTAC) or Heat Pump (PTHP) HVAC system."""
from __future__ import division

from ._base import _AllAirBase

from honeybee._lockable import lockable


@lockable
class PTAC(_AllAirBase):
    """Packaged Terminal Air Conditioning (PTAC) or Heat Pump (PTHP) HVAC system.

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

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules

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

    def __init__(self, identifier, vintage='ASHRAE_2019', equipment_type=None):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _AllAirBase.__init__(self, identifier, vintage, equipment_type)

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
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
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
        return base

    def __copy__(self):
        new_obj = self.__class__(self.identifier, self.vintage, self.equipment_type)
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type)
