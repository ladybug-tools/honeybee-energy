# coding=utf-8
"""Direct evaporative cooling systems (with optional heating)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class EvaporativeCooler(_HeatCoolBase):
    """Direct evaporative cooling systems (with optional heating).

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

            * Direct evap coolers with baseboard electric
            * Direct evap coolers with baseboard gas boiler
            * Direct evap coolers with baseboard central air source heat pump
            * Direct evap coolers with baseboard district hot water
            * Direct evap coolers with forced air furnace
            * Direct evap coolers with gas unit heaters
            * Direct evap coolers with no heat

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'Direct evap coolers with baseboard electric',
        'Direct evap coolers with baseboard gas boiler',
        'Direct evap coolers with baseboard central air source heat pump',
        'Direct evap coolers with baseboard district hot water',
        'Direct evap coolers with forced air furnace',
        'Direct evap coolers with gas unit heaters',
        'Direct evap coolers with no heat'
    )
