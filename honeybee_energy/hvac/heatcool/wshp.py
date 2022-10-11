# coding=utf-8
"""Water Source Heat Pump (WSHP) heating/cooling system (with no ventilation)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class WSHP(_HeatCoolBase):
    """Water Source Heat Pump (WSHP) heating/cooling system (with no ventilation).

    Each room/zone receives its own Water Source Heat Pump (WSHP), which meets
    the heating and cooling loads of the space. All WSHPs are connected to the
    same water condenser loop, which has its temperature maintained by the
    equipment_type (eg. Boiler with Cooling Tower).

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
            * ASHRAE_2016
            * ASHRAE_2019

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * WSHP_FluidCooler_Boiler
            * WSHP_CoolingTower_Boiler
            * WSHP_GSHP
            * WSHP_DCW_DHW

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'WSHP_FluidCooler_Boiler',
        'WSHP_CoolingTower_Boiler',
        'WSHP_GSHP',
        'WSHP_DCW_DHW'
    )
