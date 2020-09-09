# coding=utf-8
"""Fan Coil Unit (FCU) with DOAS HVAC system."""
from __future__ import division

from ._base import _DOASBase

from honeybee._lockable import lockable


@lockable
class FCUwithDOAS(_DOASBase):
    """Fan Coil Unit (FCU) with DOAS HVAC system.

    This template is also relatively close to active chilled beams in performance,
    though the energy use of the fans in the units can be zeroed out for this case.

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

            * DOAS with fan coil chiller with boiler
            * DOAS with fan coil chiller with central air source heat pump
            * DOAS with fan coil chiller with district hot water
            * DOAS with fan coil chiller with baseboard electric
            * DOAS with fan coil chiller with gas unit heaters
            * DOAS with fan coil chiller with no heat
            * DOAS with fan coil air-cooled chiller with boiler
            * DOAS with fan coil air-cooled chiller with central air source heat pump
            * DOAS with fan coil air-cooled chiller with district hot water
            * DOAS with fan coil air-cooled chiller with baseboard electric
            * DOAS with fan coil air-cooled chiller with gas unit heaters
            * DOAS with fan coil air-cooled chiller with no heat
            * DOAS with fan coil district chilled water with boiler
            * DOAS with fan coil district chilled water with central air source heat pump
            * DOAS with fan coil district chilled water with district hot water
            * DOAS with fan coil district chilled water with baseboard electric
            * DOAS with fan coil district chilled water with gas unit heaters
            * DOAS with fan coil district chilled water with no heat

        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. If None, it will be
            whatever is recommended for the given vintage (Default: None).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. If None, it will be
            whatever is recommended for the given vintage (Default: None).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'DOAS with fan coil chiller with boiler',
        'DOAS with fan coil chiller with central air source heat pump',
        'DOAS with fan coil chiller with district hot water',
        'DOAS with fan coil chiller with baseboard electric',
        'DOAS with fan coil chiller with gas unit heaters',
        'DOAS with fan coil chiller with no heat',
        'DOAS with fan coil air-cooled chiller with boiler',
        'DOAS with fan coil air-cooled chiller with central air source heat pump',
        'DOAS with fan coil air-cooled chiller with district hot water',
        'DOAS with fan coil air-cooled chiller with baseboard electric',
        'DOAS with fan coil air-cooled chiller with gas unit heaters',
        'DOAS with fan coil air-cooled chiller with no heat',
        'DOAS with fan coil district chilled water with boiler',
        'DOAS with fan coil district chilled water with central air source heat pump',
        'DOAS with fan coil district chilled water with district hot water',
        'DOAS with fan coil district chilled water with baseboard electric',
        'DOAS with fan coil district chilled water with gas unit heaters',
        'DOAS with fan coil district chilled water with no heat'
    )
