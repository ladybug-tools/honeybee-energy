# coding=utf-8
"""Residential Air Conditioning, Heat Pump or Furnace system."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class Residential(_HeatCoolBase):
    """Residential Air Conditioning, Heat Pump or Furnace system.

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

            * Residential AC with baseboard electric
            * Residential AC with baseboard gas boiler
            * Residential AC with baseboard central air source heat pump
            * Residential AC with baseboard district hot water
            * Residential AC with residential forced air furnace
            * Residential AC with no heat
            * Residential heat pump
            * Residential heat pump with no cooling
            * Residential forced air furnace

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'Residential AC with baseboard electric',
        'Residential AC with baseboard gas boiler',
        'Residential AC with baseboard central air source heat pump',
        'Residential AC with baseboard district hot water',
        'Residential AC with residential forced air furnace',
        'Residential AC with no heat',
        'Residential heat pump',
        'Residential heat pump with no cooling',
        'Residential forced air furnace'
    )
