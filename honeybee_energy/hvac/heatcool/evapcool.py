# coding=utf-8
"""Direct evaporative cooling systems (with optional heating)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class EvaporativeCooler(_HeatCoolBase):
    """Direct evaporative cooling systems (with optional heating).

    Each room/zone will receive its own air loop sized to meet the sensible load,
    which contains an evaporative cooler that directly adds humidity to the room
    air to cool it. The loop contains an outdoor air mixer, which is used whenever
    the outdoor air has a lower wet bulb temperature than the return air from
    the room. In the event that the combination of outdoor and room return air
    air is too humid, a backup single-speed direct expansion (DX) cooling coil
    will be used. Heating loads can be met with various options, including
    several types of baseboards, a furnace, or gas unit heaters.

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

            * EvapCoolers_ElectricBaseboard
            * EvapCoolers_BoilerBaseboard
            * EvapCoolers_ASHPBaseboard
            * EvapCoolers_DHWBaseboard
            * EvapCoolers_Furnace
            * EvapCoolers_UnitHeaters
            * EvapCoolers

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'EvapCoolers_ElectricBaseboard',
        'EvapCoolers_BoilerBaseboard',
        'EvapCoolers_ASHPBaseboard',
        'EvapCoolers_DHWBaseboard',
        'EvapCoolers_Furnace',
        'EvapCoolers_UnitHeaters',
        'EvapCoolers'
    )
