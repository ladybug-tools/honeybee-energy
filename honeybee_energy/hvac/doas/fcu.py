# coding=utf-8
"""Fan Coil Unit (FCU) with DOAS HVAC system."""
from __future__ import division

from ._base import _DOASBase

from honeybee._lockable import lockable


@lockable
class FCUwithDOAS(_DOASBase):
    """Fan Coil Unit (FCU) with DOAS HVAC system.

    This template is also relatively close to active chilled beams in performance,
    though the energy use of the fans in the units can be zeroed out for this case.

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

            * DOAS_FCU_Chiller_Boiler
            * DOAS_FCU_Chiller_ASHP
            * DOAS_FCU_Chiller_DHW
            * DOAS_FCU_Chiller_ElectricBaseboard
            * DOAS_FCU_Chiller_GasHeaters
            * DOAS_FCU_Chiller
            * DOAS_FCU_ACChiller_Boiler
            * DOAS_FCU_ACChiller_ASHP
            * DOAS_FCU_ACChiller_DHW
            * DOAS_FCU_ACChiller_ElectricBaseboard
            * DOAS_FCU_ACChiller_GasHeaters
            * DOAS_FCU_ACChiller
            * DOAS_FCU_DCW_Boiler
            * DOAS_FCU_DCW_ASHP
            * DOAS_FCU_DCW_DHW
            * DOAS_FCU_DCW_ElectricBaseboard
            * DOAS_FCU_DCW_GasHeaters
            * DOAS_FCU_DCW

        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. (Default: 0).
        demand_controlled_ventilation: Boolean to note whether demand controlled
            ventilation should be used on the system, which will vary the amount
            of ventilation air according to the occupancy schedule of the
            Rooms. (Default: False).
        doas_availability_schedule: An optional On/Off discrete schedule to set when
            the dedicated outdoor air system (DOAS) shuts off. This will not only
            prevent any outdoor air from flowing thorough the system but will also
            shut off the fans, which can result in more energy savings when spaces
            served by the DOAS are completely unoccupied. If None, the DOAS will be
            always on. (Default: None).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * demand_controlled_ventilation
        * doas_availability_schedule
        * schedules
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'DOAS_FCU_Chiller_Boiler',
        'DOAS_FCU_Chiller_ASHP',
        'DOAS_FCU_Chiller_DHW',
        'DOAS_FCU_Chiller_ElectricBaseboard',
        'DOAS_FCU_Chiller_GasHeaters',
        'DOAS_FCU_Chiller',
        'DOAS_FCU_ACChiller_Boiler',
        'DOAS_FCU_ACChiller_ASHP',
        'DOAS_FCU_ACChiller_DHW',
        'DOAS_FCU_ACChiller_ElectricBaseboard',
        'DOAS_FCU_ACChiller_GasHeaters',
        'DOAS_FCU_ACChiller',
        'DOAS_FCU_DCW_Boiler',
        'DOAS_FCU_DCW_ASHP',
        'DOAS_FCU_DCW_DHW',
        'DOAS_FCU_DCW_ElectricBaseboard',
        'DOAS_FCU_DCW_GasHeaters',
        'DOAS_FCU_DCW'
    )
