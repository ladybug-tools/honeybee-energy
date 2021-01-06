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

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * ResidentialAC_ElectricBaseboard
            * ResidentialAC_BoilerBaseboard
            * ResidentialAC_ASHPBaseboard
            * ResidentialAC_DHWBaseboard
            * ResidentialAC_ResidentialFurnace
            * ResidentialAC
            * ResidentialHP
            * ResidentialHPNoCool
            * ResidentialFurnace

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'ResidentialAC_ElectricBaseboard',
        'ResidentialAC_BoilerBaseboard',
        'ResidentialAC_ASHPBaseboard',
        'ResidentialAC_DHWBaseboard',
        'ResidentialAC_ResidentialFurnace',
        'ResidentialAC',
        'ResidentialHP',
        'ResidentialHPNoCool',
        'ResidentialFurnace'
    )
