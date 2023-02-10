# coding=utf-8
"""Packaged Variable Air Volume (PVAV) HVAC system."""
from __future__ import division

from ._base import _AllAirBase

from honeybee._lockable import lockable


@lockable
class PVAV(_AllAirBase):
    """Packaged Variable Air Volume (PVAV) HVAC system (aka. System 5 or 6).

    All rooms/zones are connected to a central air loop that is kept at a constant
    central temperature of 12.8C (55F). The central temperature is maintained by a
    cooling coil, which runs whenever the combination of return air and fresh outdoor
    air is greater than 12.8C, as well as a heating coil, which runs whenever
    the combination of return air and fresh outdoor air is less than 12.8C.

    Each air terminal for the connected rooms/zones contains its own reheat coil,
    which runs whenever the room is not in need of the cooling supplied by the 12.8C
    central air.

    The central cooling coil is always a two-speed direct expansion (DX) coil.
    All heating coils are hot water coils except when Gas Coil equipment_type is
    used (in which case the central coil is gas and all others are electric)
    or when Parallel Fan-Powered (PFP) boxes equipment_type is used (in which case
    coils are electric resistance). Hot water temperature is 82C (180F) for
    boiler/district heating and 49C (120F) when ASHP is used.

    PVAV systems are the traditional baseline system for commercial buildings
    with than 4-5 stories or between 2,300 m2 and 14,000 m2 (25,000 ft2 and
    150,000 ft2) of floor area.

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

            * PVAV_Boiler
            * PVAV_ASHP
            * PVAV_DHW
            * PVAV_PFP
            * PVAV_BoilerElectricReheat

        economizer_type: Text to indicate the type of air-side economizer used on
            the system. (Default: NoEconomizer). Choose from the following.

            * NoEconomizer
            * DifferentialDryBulb
            * DifferentialEnthalpy
            * DifferentialDryBulbAndEnthalpy
            * FixedDryBulb
            * FixedEnthalpy
            * ElectronicEnthalpy

        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. (Default: 0).
        demand_controlled_ventilation: Boolean to note whether demand controlled
            ventilation should be used on the system, which will vary the amount
            of ventilation air according to the occupancy schedule of the
            Rooms. (Default: False).

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * economizer_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * demand_controlled_ventilation
        * schedules
        * has_district_heating
        * has_district_cooling
        * user_data
        * properties

    Note:
        [1] American Society of Heating, Refrigerating and Air-Conditioning Engineers,
        Inc. (2007). Ashrae standard 90.1. Atlanta, GA. https://www.ashrae.org/\
technical-resources/standards-and-guidelines/read-only-versions-of-ashrae-standards
    """
    __slots__ = ()

    EQUIPMENT_TYPES = (
        'PVAV_Boiler',
        'PVAV_ASHP',
        'PVAV_DHW',
        'PVAV_PFP',
        'PVAV_BoilerElectricReheat'
    )
