# coding=utf-8
"""Window Air Conditioning cooling system (with optional heating)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class WindowAC(_HeatCoolBase):
    """Window Air Conditioning cooling system (with optional heating).

    Each room/zone will receive its own Packaged Terminal Air Conditioner (PTAC)
    with properties set to reflect a typical window air conditioning (AC) unit.
    No ventilation air is supplied by the unit and the cooling coil within the
    unit is a single-speed direct expansion (DX) cooling coil. Heating loads
    can be met with various options, including several types of baseboards,
    a furnace, or gas unit heaters.

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

            * WindowAC_ElectricBaseboard
            * WindowAC_BoilerBaseboard
            * WindowAC_ASHPBaseboard
            * WindowAC_DHWBaseboard
            * WindowAC_Furnace
            * WindowAC_GasHeaters
            * WindowAC

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'WindowAC_ElectricBaseboard',
        'WindowAC_BoilerBaseboard',
        'WindowAC_ASHPBaseboard',
        'WindowAC_DHWBaseboard',
        'WindowAC_Furnace',
        'WindowAC_GasHeaters',
        'WindowAC'
    )
