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
