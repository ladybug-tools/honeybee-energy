# coding=utf-8
from honeybee_energy.idealair import IdealAirSystem
from honeybee_energy.load.setpoint import Setpoint
from honeybee_energy.schedule.ruleset import ScheduleRuleset
import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee.room import Room

from ladybug_geometry.geometry3d.pointvector import Point3D

import json
import pytest


def test_ideal_air_system_init():
    """Test the initialization of IdealAirSystem and basic properties."""
    ideal_air = IdealAirSystem()
    str(ideal_air)  # test the string representation

    assert ideal_air.heating_limit == 'autosize'
    assert ideal_air.cooling_limit == 'autosize'
    assert ideal_air.economizer_type == 'DifferentialDryBulb'
    assert not ideal_air.demand_controlled_ventilation
    assert ideal_air.sensible_heat_recovery == 0
    assert ideal_air.latent_heat_recovery == 0


def test_ideal_air_system_setability():
    """Test the setting of properties of IdealAirSystem."""
    ideal_air = IdealAirSystem()

    ideal_air.heating_limit = 1000
    assert ideal_air.heating_limit == 1000
    ideal_air.cooling_limit = 2000
    assert ideal_air.cooling_limit == 2000
    ideal_air.economizer_type = 'DifferentialEnthalpy'
    assert ideal_air.economizer_type == 'DifferentialEnthalpy'
    ideal_air.sensible_heat_recovery = 0.75
    assert ideal_air.sensible_heat_recovery == 0.75
    ideal_air.latent_heat_recovery = 0.65
    assert ideal_air.latent_heat_recovery == 0.65


def test_ideal_air_system_equality():
    """Test the equality of IdealAirSystem objects."""
    ideal_air = IdealAirSystem()
    ideal_air_dup = ideal_air.duplicate()
    ideal_air_alt = IdealAirSystem(sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert ideal_air is ideal_air
    assert ideal_air is not ideal_air_dup
    assert ideal_air == ideal_air_dup
    ideal_air_dup.sensible_heat_recovery = 0.6
    assert ideal_air != ideal_air_dup
    assert ideal_air != ideal_air_alt


def test_ideal_air_init_from_idf():
    """Test the initialization of IdealAirSystem from_idf."""
    ideal_air = IdealAirSystem()
    zone_name = 'ShoeBox'
    room = Room.from_box(zone_name, 5, 10, 3, 90, Point3D(0, 0, 3))
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)

    with pytest.raises(AssertionError):
        ideal_air.to_idf()

    room.properties.energy.hvac = ideal_air
    with pytest.raises(AssertionError):
        ideal_air.to_idf()

    room.properties.energy.setpoint = setpoint
    idf_str = ideal_air.to_idf()
    rebuilt_ideal_air, rebuilt_zone_name = IdealAirSystem.from_idf(idf_str)
    assert ideal_air == rebuilt_ideal_air
    assert zone_name == rebuilt_zone_name


def test_ideal_air_to_dict():
    """Test the to_dict method."""
    ideal_air = IdealAirSystem()
    ideal_air.heating_limit = 2000
    ideal_air.cooling_limit = 3500
    ideal_air.economizer_type = 'DifferentialEnthalpy'
    ideal_air.demand_controlled_ventilation = True
    ideal_air.sensible_heat_recovery = 0.75
    ideal_air.latent_heat_recovery = 0.6

    ideal_air_dict = ideal_air.to_dict()

    assert ideal_air_dict['heating_limit'] == 2000
    assert ideal_air_dict['cooling_limit'] == 3500
    assert ideal_air_dict['economizer_type'] == 'DifferentialEnthalpy'
    assert ideal_air_dict['demand_controlled_ventilation'] == True
    assert ideal_air_dict['sensible_heat_recovery'] == 0.75
    assert ideal_air_dict['latent_heat_recovery'] == 0.6

    """
    f_dir = 'C:/Users/chris/Documents/GitHub/energy-model-schema/app/models/samples/json'
    dest_file = f_dir + '/detailed_ideal_air.json'
    with open(dest_file, 'w') as fp:
        json.dump(ideal_air_dict, fp, indent=4)
    """


def test_ideal_air_dict_methods():
    """Test the to/from dict methods."""
    ideal_air = IdealAirSystem(sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    hvac_dict = ideal_air.to_dict()
    new_ideal_air = IdealAirSystem.from_dict(hvac_dict)
    assert new_ideal_air == ideal_air
    assert hvac_dict == new_ideal_air.to_dict()
