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

            * DOE Ref Pre-1980
            * DOE Ref 1980-2004
            * 90.1-2004
            * 90.1-2007
            * 90.1-2010
            * 90.1-2013

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * PTAC with baseboard electric
            * PTAC with baseboard gas boiler
            * PTAC with baseboard district hot water
            * PTAC with gas unit heaters
            * PTAC with electric coil
            * PTAC with gas coil
            * PTAC with gas boiler
            * PTAC with central air source heat pump
            * PTAC with district hot water
            * PTAC with no heat
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
        'PTAC with baseboard electric',
        'PTAC with baseboard gas boiler',
        'PTAC with baseboard district hot water',
        'PTAC with gas unit heaters',
        'PTAC with electric coil',
        'PTAC with gas coil',
        'PTAC with gas boiler',
        'PTAC with central air source heat pump',
        'PTAC with district hot water',
        'PTAC with no heat',
        'PTHP'
    )
    _has_air_loop = False
