# coding=utf-8
from honeybee_energy.load.setpoint import Setpoint
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time

import pytest


def test_setpoint_init():
    """Test the initialization of Setpoint and basic properties."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)
    str(setpoint)  # test the string representation

    assert setpoint.identifier == 'Office Setpoint'
    assert setpoint.heating_schedule == heat_setpt
    assert setpoint.heating_setpoint == 21
    assert setpoint.heating_setback == 21
    assert setpoint.cooling_schedule == cool_setpt
    assert setpoint.cooling_setpoint == 24
    assert setpoint.cooling_setback == 24
    assert setpoint.humidifying_schedule is None
    assert setpoint.humidifying_setpoint is None
    assert setpoint.humidifying_setback is None
    assert setpoint.dehumidifying_schedule is None
    assert setpoint.dehumidifying_setpoint is None
    assert setpoint.dehumidifying_setback is None


def test_setpoint_init_with_setback():
    """Test the initialization of Setpoint with a setback schedule."""
    simple_heat = ScheduleDay('Simple Weekday HtgSetp', [18, 21, 18],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    simple_cool = ScheduleDay('Simple Weekday ClgSetp', [28, 24, 28],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    heat_setpt = ScheduleRuleset('Office Heating', simple_heat,
                                 None, schedule_types.temperature)
    cool_setpt = ScheduleRuleset('Office Cooling', simple_cool,
                                 None, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)

    assert setpoint.identifier == 'Office Setpoint'
    assert setpoint.heating_schedule == heat_setpt
    assert setpoint.heating_setpoint == 21
    assert setpoint.heating_setback == 18
    assert setpoint.cooling_schedule == cool_setpt
    assert setpoint.cooling_setpoint == 24
    assert setpoint.cooling_setback == 28


def test_setpoint_init_humidity():
    """Test the initialization of Setpoint with humidity setpoints."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)
    setpoint.humidifying_setpoint = 30
    setpoint.dehumidifying_setpoint = 60
    str(setpoint)  # test the string representation

    assert setpoint.identifier == 'Office Setpoint'
    assert setpoint.heating_schedule == heat_setpt
    assert setpoint.heating_setpoint == 21
    assert setpoint.heating_setback == 21
    assert setpoint.cooling_schedule == cool_setpt
    assert setpoint.cooling_setpoint == 24
    assert setpoint.cooling_setback == 24
    assert setpoint.humidifying_schedule.is_constant
    assert setpoint.humidifying_setpoint == 30
    assert setpoint.humidifying_setback == 30
    assert setpoint.dehumidifying_schedule.is_constant
    assert setpoint.dehumidifying_setpoint == 60
    assert setpoint.dehumidifying_setback == 60


def test_setpoint_setability():
    """Test the setting of properties of Setpoint."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)

    setpoint.identifier = 'Office Zone Setpoint'
    assert setpoint.identifier == 'Office Zone Setpoint'
    setpoint.heating_setpoint = 20
    assert setpoint.heating_setpoint == 20
    assert setpoint.heating_setback == 20
    setpoint.cooling_setpoint = 26
    assert setpoint.cooling_setpoint == 26
    assert setpoint.cooling_setback == 26
    setpoint.humidifying_setpoint = 30
    assert setpoint.humidifying_setpoint == 30
    assert setpoint.humidifying_setback == 30
    setpoint.dehumidifying_setpoint = 60
    assert setpoint.dehumidifying_setpoint == 60
    assert setpoint.dehumidifying_setback == 60


def test_setpoint_equality():
    """Test the equality of Setpoint objects."""
    simple_heat = ScheduleDay('Simple Weekday HtgSetp', [18, 21, 18],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    simple_cool = ScheduleDay('Simple Weekday ClgSetp', [28, 24, 28],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    heat_setpt = ScheduleRuleset('Office Heating', simple_heat,
                                 None, schedule_types.temperature)
    cool_setpt = ScheduleRuleset('Office Cooling', simple_cool,
                                 None, schedule_types.temperature)
    heat_setpt_2 = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt_2 = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)

    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)
    setpoint_dup = setpoint.duplicate()
    setpoint_alt = Setpoint('Office Setpoint', heat_setpt_2, cool_setpt_2)

    assert setpoint is setpoint
    assert setpoint is not setpoint_dup
    assert setpoint == setpoint_dup
    setpoint_dup.humidifying_setpoint = 30
    assert setpoint != setpoint_dup
    assert setpoint != setpoint_alt


def test_setpoint_lockability():
    """Test the lockability of Setpoint objects."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)

    setpoint.heating_setpoint = 20
    setpoint.lock()
    with pytest.raises(AttributeError):
        setpoint.heating_setpoint = 22
    setpoint.unlock()
    setpoint.heating_setpoint = 22


def test_setpoint_init_from_idf():
    """Test the initialization of Setpoint from_idf."""
    simple_heat = ScheduleDay('Simple Weekday HtgSetp', [18, 21, 18],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    simple_cool = ScheduleDay('Simple Weekday ClgSetp', [28, 24, 28],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    heat_setpt = ScheduleRuleset('Office Heating', simple_heat,
                                 None, schedule_types.temperature)
    cool_setpt = ScheduleRuleset('Office Cooling', simple_cool,
                                 None, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)
    sched_dict = {heat_setpt.identifier: heat_setpt, cool_setpt.identifier: cool_setpt}

    idf_str = setpoint.to_idf('Test Zone')
    rebuilt_setpoint = Setpoint.from_idf(idf_str, sched_dict)
    assert setpoint == rebuilt_setpoint


def test_setpoint_init_from_idf_humidity():
    """Test the initialization of Setpoint from_idf with humidity setpoints."""
    simple_heat = ScheduleDay('Simple Weekday HtgSetp', [18, 21, 18],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    simple_cool = ScheduleDay('Simple Weekday ClgSetp', [28, 24, 28],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    heat_setpt = ScheduleRuleset('Office Heating', simple_heat,
                                 None, schedule_types.temperature)
    cool_setpt = ScheduleRuleset('Office Cooling', simple_cool,
                                 None, schedule_types.temperature)
    humid_setpt = ScheduleRuleset.from_constant_value(
        'Office Humid', 30, schedule_types.humidity)
    dehumid_setpt = ScheduleRuleset.from_constant_value(
        'Office Dehumid', 60, schedule_types.humidity)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt,
                        humid_setpt, dehumid_setpt)
    sched_dict = {heat_setpt.identifier: heat_setpt, cool_setpt.identifier: cool_setpt,
                  humid_setpt.identifier: humid_setpt,
                  dehumid_setpt.identifier: dehumid_setpt}

    zone_id = 'Test Zone'
    idf_str = setpoint.to_idf(zone_id)
    humid_idf_str = setpoint.to_idf_humidistat(zone_id)
    rebuilt_setpoint = Setpoint.from_idf(idf_str, sched_dict)
    rebuilt_setpoint.add_humidity_from_idf(humid_idf_str, sched_dict)
    assert setpoint == rebuilt_setpoint


def test_setpoint_dict_methods():
    """Test the to/from dict methods."""
    simple_heat = ScheduleDay('Simple Weekday HtgSetp', [18, 21, 18],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    simple_cool = ScheduleDay('Simple Weekday ClgSetp', [28, 24, 28],
                              [Time(0, 0), Time(9, 0), Time(17, 0)])
    heat_setpt = ScheduleRuleset('Office Heating', simple_heat,
                                 None, schedule_types.temperature)
    cool_setpt = ScheduleRuleset('Office Cooling', simple_cool,
                                 None, schedule_types.temperature)
    humid_setpt = ScheduleRuleset.from_constant_value(
        'Office Humid', 30, schedule_types.humidity)
    dehumid_setpt = ScheduleRuleset.from_constant_value(
        'Office Dehumid', 60, schedule_types.humidity)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt,
                        humid_setpt, dehumid_setpt)

    setp_dict = setpoint.to_dict()
    new_setpoint = Setpoint.from_dict(setp_dict)
    assert new_setpoint == setpoint
    assert setp_dict == new_setpoint.to_dict()


def test_setpoint_average():
    """Test the Setpoint.average method."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 22, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    office_setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)
    lobby_setpoint = office_setpoint.duplicate()
    lobby_setpoint.identifier = 'Lobby Setpoint'
    lobby_setpoint.heating_setpoint = 18
    lobby_setpoint.cooling_setpoint = 28

    office_avg = Setpoint.average('Office Average Setpoint',
                                  [office_setpoint, lobby_setpoint])

    assert office_avg.heating_setpoint == pytest.approx(20, rel=1e-3)
    assert office_avg.heating_setback == pytest.approx(20, rel=1e-3)
    assert office_avg.cooling_setpoint == pytest.approx(26, rel=1e-3)
    assert office_avg.cooling_setback == pytest.approx(26, rel=1e-3)
    assert office_avg.humidifying_setpoint is None
    assert office_avg.humidifying_setback is None
    assert office_avg.dehumidifying_setpoint is None
    assert office_avg.dehumidifying_setback is None
