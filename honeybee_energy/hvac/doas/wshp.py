# coding=utf-8
"""Water Source Heat Pump (WSHP) with DOAS HVAC system."""
from __future__ import division

from ._base import _DOASBase

from honeybee._lockable import lockable


@lockable
class WSHPwithDOAS(_DOASBase):
    """Water Source Heat Pump (WSHP) with DOAS HVAC system.

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

            * DOAS_WSHP_FluidCooler_Boiler
            * DOAS_WSHP_CoolingTower_Boiler
            * DOAS_WSHP_GSHP
            * DOAS_WSHP_DCW_DHW

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
        'DOAS_WSHP_FluidCooler_Boiler',
        'DOAS_WSHP_CoolingTower_Boiler',
        'DOAS_WSHP_GSHP',
        'DOAS_WSHP_DCW_DHW'
    )
