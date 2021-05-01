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

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * PSZAC_ElectricBaseboard
            * PSZAC_BoilerBaseboard
            * PSZAC_DHWBaseboard
            * PSZAC_GasHeaters
            * PSZAC_ElectricCoil
            * PSZAC_GasCoil
            * PSZAC_Boiler
            * PSZAC_ASHP
            * PSZAC_DHW
            * PSZAC
            * PSZAC_DCW_ElectricBaseboard
            * PSZAC_DCW_BoilerBaseboard
            * PSZAC_DCW_GasHeaters
            * PSZAC_DCW_ElectricCoil
            * PSZAC_DCW_GasCoil
            * PSZAC_DCW_Boiler
            * PSZAC_DCW_ASHP
            * PSZAC_DCW_DHW
            * PSZAC_DCW
            * PSZHP

        economizer_type: Text to indicate the type of air-side economizer used on
            the system. (Default: NoEconomizer). Choose from the following.

            * NoEconomizer
            * DifferentialDryBulb
            * DifferentialEnthalpy
            * DifferentialDryBulbAndEnthalpy
            * FixedDryBulb
            * FixedEnthalpy
            * ElectronicEnthalpy

        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. (Default: 0).
        demand_controlled_ventilation: Boolean to note whether demand controlled
            ventilation should be used on the system, which will vary the amount
            of ventilation air according to the occupancy schedule of the
            Rooms. (Default: False).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * economizer_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * demand_controlled_ventilation
        * schedules

    Note:
        [1] American Society of Heating, Refrigerating and Air-Conditioning Engineers,
        Inc. (2007). Ashrae standard 90.1. Atlanta, GA. https://www.ashrae.org/\
technical-resources/standards-and-guidelines/read-only-versions-of-ashrae-standards
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'PSZAC_ElectricBaseboard',
        'PSZAC_BoilerBaseboard',
        'PSZAC_DHWBaseboard',
        'PSZAC_GasHeaters',
        'PSZAC_ElectricCoil',
        'PSZAC_GasCoil',
        'PSZAC_Boiler',
        'PSZAC_ASHP',
        'PSZAC_DHW',
        'PSZAC',
        'PSZAC_DCW_ElectricBaseboard',
        'PSZAC_DCW_BoilerBaseboard',
        'PSZAC_DCW_GasHeaters',
        'PSZAC_DCW_ElectricCoil',
        'PSZAC_DCW_GasCoil',
        'PSZAC_DCW_Boiler',
        'PSZAC_DCW_ASHP',
        'PSZAC_DCW_DHW',
        'PSZAC_DCW',
        'PSZHP'
    )
