# coding=utf-8
"""Packaged Single-Zone (PSZ) HVAC system."""
from __future__ import division

from ._base import _AllAirBase

from honeybee._lockable import lockable


@lockable
class PSZ(_AllAirBase):
    """Packaged Single-Zone (PSZ) HVAC system.

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

            * PSZ-AC with baseboard electric
            * PSZ-AC with baseboard gas boiler
            * PSZ-AC with baseboard district hot water
            * PSZ-AC with gas unit heaters
            * PSZ-AC with electric coil
            * PSZ-AC with gas coil
            * PSZ-AC with gas boiler
            * PSZ-AC with central air source heat pump
            * PSZ-AC with district hot water
            * PSZ-AC with no heat
            * PSZ-AC district chilled water with baseboard electric
            * PSZ-AC district chilled water with baseboard gas boiler
            * PSZ-AC district chilled water with baseboard district hot water
            * PSZ-AC district chilled water with gas unit heaters
            * PSZ-AC district chilled water with electric coil
            * PSZ-AC district chilled water with gas coil
            * PSZ-AC district chilled water with gas boiler
            * PSZ-AC district chilled water with central air source heat pump
            * PSZ-AC district chilled water with district hot water
            * PSZ-AC district chilled water with no heat
            * PSZ-HP

        economizer_type: Text to indicate the type of air-side economizer used on
            the system. If Inferred, the economizer will be set to whatever is
            recommended for the given vintage. (Default: Inferred).
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
        * economizer_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * schedules

    Note:
        [1] American Society of Heating, Refrigerating and Air-Conditioning Engineers,
        Inc. (2007). Ashrae standard 90.1. Atlanta, GA. https://www.ashrae.org/\
technical-resources/standards-and-guidelines/read-only-versions-of-ashrae-standards
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'PSZ-AC with baseboard electric',
        'PSZ-AC with baseboard gas boiler',
        'PSZ-AC with baseboard district hot water',
        'PSZ-AC with gas unit heaters',
        'PSZ-AC with electric coil',
        'PSZ-AC with gas coil',
        'PSZ-AC with gas boiler',
        'PSZ-AC with central air source heat pump',
        'PSZ-AC with district hot water',
        'PSZ-AC with no heat',
        'PSZ-AC district chilled water with baseboard electric',
        'PSZ-AC district chilled water with baseboard gas boiler',
        'PSZ-AC district chilled water with baseboard district hot water',
        'PSZ-AC district chilled water with gas unit heaters',
        'PSZ-AC district chilled water with electric coil',
        'PSZ-AC district chilled water with gas coil',
        'PSZ-AC district chilled water with gas boiler',
        'PSZ-AC district chilled water with central air source heat pump',
        'PSZ-AC district chilled water with district hot water',
        'PSZ-AC district chilled water with no heat',
        'PSZ-HP'
    )
