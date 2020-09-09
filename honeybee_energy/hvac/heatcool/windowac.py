# coding=utf-8
"""Window Air Conditioning cooling system (with optional heating)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class WindowAC(_HeatCoolBase):
    """Window Air Conditioning cooling system (with optional heating).

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

            * Window AC with baseboard electric
            * Window AC with baseboard gas boiler
            * Window AC with baseboard central air source heat pump
            * Window AC with baseboard district hot water
            * Window AC with forced air furnace
            * Window AC with unit heaters
            * Window AC with no heat

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'Window AC with baseboard electric',
        'Window AC with baseboard gas boiler',
        'Window AC with baseboard central air source heat pump',
        'Window AC with baseboard district hot water',
        'Window AC with forced air furnace',
        'Window AC with unit heaters',
        'Window AC with no heat'
    )
