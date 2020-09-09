# coding=utf-8
"""Fan Coil Unit (FCU) heating/cooling system (with no ventilation)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class FCU(_HeatCoolBase):
    """Fan Coil Unit (FCU) heating/cooling system (with no ventilation).

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

            * Fan coil chiller with boiler
            * Fan coil chiller with central air source heat pump
            * Fan coil chiller with district hot water
            * Fan coil chiller with baseboard electric
            * Fan coil chiller with gas unit heaters
            * Fan coil chiller with no heat
            * Fan coil air-cooled chiller with boiler
            * Fan coil air-cooled chiller with central air source heat pump
            * Fan coil air-cooled chiller with district hot water
            * Fan coil air-cooled chiller with baseboard electric
            * Fan coil air-cooled chiller with gas unit heaters
            * Fan coil air-cooled chiller with no heat
            * Fan coil district chilled water with boiler
            * Fan coil district chilled water with central air source heat pump
            * Fan coil district chilled water with district hot water
            * Fan coil district chilled water with baseboard electric
            * Fan coil district chilled water with gas unit heaters
            * Fan coil district chilled water with no heat

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'Fan coil chiller with boiler',
        'Fan coil chiller with central air source heat pump',
        'Fan coil chiller with district hot water',
        'Fan coil chiller with baseboard electric',
        'Fan coil chiller with gas unit heaters',
        'Fan coil chiller with no heat',
        'Fan coil air-cooled chiller with boiler',
        'Fan coil air-cooled chiller with central air source heat pump',
        'Fan coil air-cooled chiller with district hot water',
        'Fan coil air-cooled chiller with baseboard electric',
        'Fan coil air-cooled chiller with gas unit heaters',
        'Fan coil air-cooled chiller with no heat',
        'Fan coil district chilled water with boiler',
        'Fan coil district chilled water with central air source heat pump',
        'Fan coil district chilled water with district hot water',
        'Fan coil district chilled water with baseboard electric',
        'Fan coil district chilled water with gas unit heaters',
        'Fan coil district chilled water with no heat'
    )
