# coding=utf-8
"""Residential Air Conditioning, Heat Pump or Furnace system."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable


@lockable
class Residential(_HeatCoolBase):
    """Residential Air Conditioning, Heat Pump or Furnace system.

    Residential HVAC systems are intended primarily for single-family homes and
    include a wide variety of options. In all cases, each room/zone will receive
    its own air loop WITHOUT an outdoor air inlet (air is simply being recirculated
    through the loop). Residential air conditioning (AC) systems are modeled
    using a unitary system with a single-speed direct expansion (DX) cooling
    coil in the loop. Residential heat pump (HP) systems use a single-speed DX
    heating coil in the unitary system and the residential furnace option uses
    a gas coil in the unitary system. In all cases, the properties of these coils
    are set to reflect a typical residential system.

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

            * ResidentialAC_ElectricBaseboard
            * ResidentialAC_BoilerBaseboard
            * ResidentialAC_ASHPBaseboard
            * ResidentialAC_DHWBaseboard
            * ResidentialAC_ResidentialFurnace
            * ResidentialAC
            * ResidentialHP
            * ResidentialHPNoCool
            * ResidentialFurnace

        unit_ventilators: Boolean to note whether individual zone ventilators are
            included with the basic heating and cooling system (True) or the system only
            performs heating and cooling without any ventilation (False). Unlike a DOAS,
            unit ventilators do not pass the outdoor air through heating or cooling
            coils to condition it for the space. However, heat recovery effectiveness
            can be specified, which can temper the air supplied to the zone by the
            ventilator with exhaust air. All air flow through this ventilator
            is always balanced for each zone between supply and exhaust and the
            total flow rate is determined by checking the ventilation and exhaust
            requirements of the rooms to which the system is assigned. (Default: False).
        sensible_heat_recovery: A number between 0 and 1 for the effectiveness of
            sensible heat recovery within unit ventilators if specified. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness of
            latent heat recovery within unit ventilators if specified. (Default: 0).
        vent_availability_schedule: An optional On/Off discrete schedule to specify when
            unit ventilators shut off (assuming that the unit_ventilators is True).
            This will not only reduce heating and cooling load by preventing
            outdoor air from flowing but will also shut off the fans, which can
            result in more energy savings when spaces served by the ventilators
            are completely unoccupied. If None, the unit ventilators will be
            always on. (Default: None).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * unit_ventilators
        * sensible_heat_recovery
        * latent_heat_recovery
        * vent_availability_schedule
        * has_air_loop
        * has_district_heating
        * has_district_cooling
        * balances_exhaust
        * user_data
        * properties
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
