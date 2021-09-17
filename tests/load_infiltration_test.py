# coding=utf-8
from honeybee_energy.load.infiltration import Infiltration
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time, Date

import pytest
from .fixtures.userdata_fixtures import userdatadict


def test_infiltration_init(userdatadict):
    """Test the initialization of Infiltration and basic properties."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    infiltration.user_data = userdatadict
    str(infiltration)  # test the string representation

    assert infiltration.identifier == 'Lobby Infiltration'
    assert infiltration.flow_per_exterior_area == 0.0003
    assert infiltration.schedule.identifier == 'Lobby Infiltration Schedule'
    assert infiltration.schedule.schedule_type_limit == schedule_types.fractional
    assert infiltration.schedule == schedule
    assert infiltration.constant_coefficient == 1
    assert infiltration.temperature_coefficient == 0
    assert infiltration.velocity_coefficient == 0
    assert infiltration.user_data == userdatadict


def test_infiltration_setability(userdatadict):
    """Test the setting of properties of Infiltration."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    constant = ScheduleRuleset.from_constant_value(
        'Constant Infiltration', 1, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    infiltration.user_data = userdatadict

    infiltration.identifier = 'Lobby Zone Infiltration'
    assert infiltration.identifier == 'Lobby Zone Infiltration'
    infiltration.flow_per_exterior_area = 0.0006
    assert infiltration.flow_per_exterior_area == 0.0006
    infiltration.schedule = constant
    assert infiltration.schedule == constant
    assert infiltration.schedule.values() == [1] * 8760
    infiltration.constant_coefficient = 0.606
    assert infiltration.constant_coefficient == 0.606
    infiltration.temperature_coefficient = 0.03636
    assert infiltration.temperature_coefficient == 0.03636
    infiltration.velocity_coefficient = 0.1177
    assert infiltration.velocity_coefficient == 0.1177
    assert infiltration.user_data == userdatadict


def test_infiltration_equality(userdatadict):
    """Test the equality of Infiltration objects."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    constant = ScheduleRuleset.from_constant_value(
        'Constant Infiltration', 1, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    infiltration.user_data = userdatadict
    infiltration_dup = infiltration.duplicate()
    infiltration_alt = Infiltration(
        'Lobby Infiltration', 0.0003, constant)

    assert infiltration is infiltration
    assert infiltration is not infiltration_dup
    assert infiltration == infiltration_dup
    infiltration_dup.flow_per_exterior_area = 0.0006
    assert infiltration != infiltration_dup
    assert infiltration != infiltration_alt


def test_infiltration_lockability(userdatadict):
    """Test the lockability of Infiltration objects."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    infiltration.user_data = userdatadict

    infiltration.flow_per_exterior_area = 0.0006
    infiltration.lock()
    with pytest.raises(AttributeError):
        infiltration.flow_per_exterior_area = 0.0008
    with pytest.raises(AttributeError):
        infiltration.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    infiltration.unlock()
    infiltration.flow_per_exterior_area = 0.0008
    with pytest.raises(AttributeError):
        infiltration.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_infiltration_init_from_idf():
    """Test the initialization of Infiltration from_idf."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    sched_dict = {schedule.identifier: schedule}

    zone_id = 'Test Zone'
    idf_str = infiltration.to_idf(zone_id)
    rebuilt_infiltration, rebuilt_zone_id = Infiltration.from_idf(idf_str, sched_dict)
    assert infiltration == rebuilt_infiltration
    assert zone_id == rebuilt_zone_id


def test_infiltration_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    simple_lobby = ScheduleDay('Simple Weekday', [0, 1, 0],
                               [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Lobby Infiltration Schedule', simple_lobby,
                               None, schedule_types.fractional)
    infiltration = Infiltration('Lobby Infiltration', 0.0003, schedule)
    infiltration.user_data = userdatadict
    inf_dict = infiltration.to_dict()
    new_infiltration = Infiltration.from_dict(inf_dict)
    assert new_infiltration == infiltration
    assert inf_dict == new_infiltration.to_dict()
    assert new_infiltration.user_data == infiltration.user_data


def test_infiltration_average():
    """Test the Infiltration.average method."""
    weekday_office = ScheduleDay('Weekday Office Infiltration', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Infiltration', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Infiltration', [0])
    weekend_lobby = ScheduleDay('Weekend Office Infiltration', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Infiltration', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Infiltration', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_inf = Infiltration('Office Infiltration', 0.0003, office_schedule, 1, 0, 0)
    lobby_inf = Infiltration('Lobby Infiltration', 0.0006, lobby_schedule,
                             0.6, 0.03, 0.1)

    office_avg = Infiltration.average('Average Infiltration', [office_inf, lobby_inf])

    assert office_avg.flow_per_exterior_area == pytest.approx(0.00045, rel=1e-3)
    assert office_avg.constant_coefficient == pytest.approx(0.8, rel=1e-3)
    assert office_avg.temperature_coefficient == pytest.approx(0.015, rel=1e-3)
    assert office_avg.velocity_coefficient == pytest.approx(0.05, rel=1e-3)

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals
