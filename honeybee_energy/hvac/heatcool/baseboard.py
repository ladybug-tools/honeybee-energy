# coding=utf-8
"""Baseboard heating system. Intended for spaces only requiring heating."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class Baseboard(_HeatCoolBase):
    """Baseboard heating system. Intended for spaces only requiring heating.

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

            * ElectricBaseboard
            * BoilerBaseboard
            * ASHPBaseboard
            * DHWBaseboard

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'ElectricBaseboard',
        'BoilerBaseboard',
        'ASHPBaseboard',
        'DHWBaseboard'
    )
