# coding=utf-8
"""Fan Coil Unit (FCU) heating/cooling system (with no ventilation)."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class FCU(_HeatCoolBase):
    """Fan Coil Unit (FCU) heating/cooling system (with no ventilation).

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

            * FCU_Chiller_Boiler
            * FCU_Chiller_ASHP
            * FCU_Chiller_DHW
            * FCU_Chiller_ElectricBaseboard
            * FCU_Chiller_GasHeaters
            * FCU_Chiller
            * FCU_ACChiller_Boiler
            * FCU_ACChiller_ASHP
            * FCU_ACChiller_DHW
            * FCU_ACChiller_ElectricBaseboard
            * FCU_ACChiller_GasHeaters
            * FCU_ACChiller
            * FCU_DCW_Boiler
            * FCU_DCW_ASHP
            * FCU_DCW_DHW
            * FCU_DCW_ElectricBaseboard
            * FCU_DCW_GasHeaters
            * FCU_DCW

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'FCU_Chiller_Boiler',
        'FCU_Chiller_ASHP',
        'FCU_Chiller_DHW',
        'FCU_Chiller_ElectricBaseboard',
        'FCU_Chiller_GasHeaters',
        'FCU_Chiller',
        'FCU_ACChiller_Boiler',
        'FCU_ACChiller_ASHP',
        'FCU_ACChiller_DHW',
        'FCU_ACChiller_ElectricBaseboard',
        'FCU_ACChiller_GasHeaters',
        'FCU_ACChiller',
        'FCU_DCW_Boiler',
        'FCU_DCW_ASHP',
        'FCU_DCW_DHW',
        'FCU_DCW_ElectricBaseboard',
        'FCU_DCW_GasHeaters',
        'FCU_DCW'
    )
