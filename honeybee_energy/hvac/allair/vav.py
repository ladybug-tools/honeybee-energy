# coding=utf-8
"""Variable Air Volume (VAV) HVAC system."""
from __future__ import division

from ._base import _AllAirBase

from honeybee._lockable import lockable


@lockable
class VAV(_AllAirBase):
    """Variable Air Volume (VAV) HVAC system.

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

            * VAV_Chiller_Boiler
            * VAV_Chiller_ASHP
            * VAV_Chiller_DHW
            * VAV_Chiller_PFP
            * VAV_Chiller_GasCoil
            * VAV_ACChiller_Boiler
            * VAV_ACChiller_ASHP
            * VAV_ACChiller_DHW
            * VAV_ACChiller_PFP
            * VAV_ACChiller_GasCoil
            * VAV_DCW_Boiler
            * VAV_DCW_ASHP
            * VAV_DCW_DHW
            * VAV_DCW_PFP
            * VAV_DCW_GasCoil

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
        'VAV_Chiller_Boiler',
        'VAV_Chiller_ASHP',
        'VAV_Chiller_DHW',
        'VAV_Chiller_PFP',
        'VAV_Chiller_GasCoil',
        'VAV_ACChiller_Boiler',
        'VAV_ACChiller_ASHP',
        'VAV_ACChiller_DHW',
        'VAV_ACChiller_PFP',
        'VAV_ACChiller_GasCoil',
        'VAV_DCW_Boiler',
        'VAV_DCW_ASHP',
        'VAV_DCW_DHW',
        'VAV_DCW_PFP',
        'VAV_DCW_GasCoil'
    )
