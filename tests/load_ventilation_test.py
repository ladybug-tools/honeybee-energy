# coding=utf-8
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time, Date

import pytest


def test_ventilation_init():
    """Test the initialization of Ventilation and basic properties."""
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)
    str(ventilation)  # test the string representation

    assert ventilation.identifier == 'Office Ventilation'
    assert ventilation.flow_per_person == 0.0025
    assert ventilation.flow_per_area == 0.0006
    assert ventilation.flow_per_zone == 0
    assert ventilation.air_changes_per_hour == 0
    assert ventilation.schedule is None


def test_ventilation_init_schedule():
    """Test the initialization of Ventilation with a schedule."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Ventilation Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006, 0, 0, schedule)
    str(ventilation)  # test the string representation

    assert ventilation.identifier == 'Office Ventilation'
    assert ventilation.flow_per_person == 0.0025
    assert ventilation.flow_per_area == 0.0006
    assert ventilation.flow_per_zone == 0
    assert ventilation.air_changes_per_hour == 0
    assert ventilation.schedule.identifier == 'Office Ventilation Schedule'
    assert ventilation.schedule.schedule_type_limit == schedule_types.fractional
    assert ventilation.schedule == schedule


def test_ventilation_setability():
    """Test the setting of properties of Ventilation."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Ventilation Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)

    ventilation.identifier = 'Office Zone Ventilation'
    assert ventilation.identifier == 'Office Zone Ventilation'
    ventilation.flow_per_person = 0.01
    assert ventilation.flow_per_person == 0.01
    ventilation.flow_per_area = 0
    assert ventilation.flow_per_area == 0
    ventilation.flow_per_zone = 1
    assert ventilation.flow_per_zone == 1
    ventilation.air_changes_per_hour = 2
    assert ventilation.air_changes_per_hour == 2
    ventilation.schedule = schedule
    assert ventilation.schedule == schedule


def test_ventilation_equality():
    """Test the equality of Ventilation objects."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Ventilation Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = Ventilation('Office Ventilation', 0.0025, 0.0006)
    ventilation_alt.schedule = schedule

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.flow_per_person = 0.01
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_ventilation_lockability():
    """Test the lockability of Ventilation objects."""
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)

    ventilation.flow_per_person = 0.01
    ventilation.lock()
    with pytest.raises(AttributeError):
        ventilation.flow_per_person = 0.0025
    ventilation.unlock()
    ventilation.flow_per_person = 0.0025


def test_ventilation_init_from_idf():
    """Test the initialization of Ventilation from_idf."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Ventilation Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)
    ventilation.schedule = schedule
    sched_dict = {schedule.identifier: schedule}

    idf_str = ventilation.to_idf('Test Zone')
    rebuilt_ventilation = Ventilation.from_idf(idf_str, sched_dict)
    assert ventilation == rebuilt_ventilation


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Ventilation Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0006)

    vent_dict = ventilation.to_dict()
    new_ventilation = Ventilation.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    ventilation.schedule = schedule
    vent_dict = ventilation.to_dict()
    new_ventilation = Ventilation.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()


def test_ventilation_average():
    """Test the Ventilation.average method."""
    weekday_office = ScheduleDay('Weekday Office Ventilation', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Ventilation', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Ventilation', [0])
    weekend_lobby = ScheduleDay('Weekend Office Ventilation', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Ventilation', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Ventilation', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_vent = Ventilation('Office Ventilation', 0.01, 0.0006, 0, 0, office_schedule)
    lobby_vent = Ventilation('Lobby Ventilation', 0, 0, 0, 1, lobby_schedule)

    office_avg = Ventilation.average('Average Ventilation', [office_vent, lobby_vent])

    assert office_avg.flow_per_person == pytest.approx(0.005, rel=1e-3)
    assert office_avg.flow_per_area == pytest.approx(0.0003, rel=1e-3)
    assert office_avg.flow_per_zone == pytest.approx(0, rel=1e-3)
    assert office_avg.air_changes_per_hour == pytest.approx(0.5, rel=1e-3)

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals

    office_vent.schedule = None
    lobby_vent.schedule = None
    office_avg = Ventilation.average('Average Ventilation', [office_vent, lobby_vent])

    assert office_avg.schedule is None
