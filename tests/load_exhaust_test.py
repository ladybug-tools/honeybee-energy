# coding=utf-8
from honeybee_energy.load.exhaust import ExhaustAir
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types
from honeybee_energy.lib.schedules import always_on

from ladybug.dt import Time, Date

import pytest


def test_exhaust_air_init():
    """Test the initialization of ExhaustAir and basic properties."""
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)
    str(exhaust)  # test the string representation

    assert exhaust.identifier == 'Bathroom Exhaust Air'
    assert exhaust.flow_per_area == 0.0003304
    assert exhaust.flow_per_fixture == 0.0236
    assert exhaust.fixture_count == 1
    assert exhaust.schedule == always_on
    assert exhaust._schedule is None
    assert exhaust.pressure_rise == 125
    assert exhaust.efficiency == 0.35

    assert exhaust.flow_per_area_si == pytest.approx(0.3304, rel=1e-3)
    assert exhaust.flow_per_fixture_si == pytest.approx(23.6, rel=1e-3)
    assert exhaust.pressure_rise_si == pytest.approx(125, rel=1e-3)

    assert exhaust.flow_per_area_ip == pytest.approx(0.06503924, rel=1e-3)
    assert exhaust.flow_per_fixture_ip == pytest.approx(50.005568, rel=1e-3)
    assert exhaust.pressure_rise_ip == pytest.approx(0.50233125, rel=1e-3)


def test_exhaust_air_init_schedule():
    """Test the initialization of ExhaustAir with a schedule."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Bathroom Exhaust Air Schedule', simple_office,
                               None, schedule_types.fractional)
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236, 8, schedule)
    str(exhaust)  # test the string representation

    assert exhaust.identifier == 'Bathroom Exhaust Air'
    assert exhaust.flow_per_area == 0.0003304
    assert exhaust.flow_per_fixture == 0.0236
    assert exhaust.fixture_count == 8
    assert exhaust.schedule.identifier == 'Bathroom Exhaust Air Schedule'
    assert exhaust.schedule.schedule_type_limit == schedule_types.fractional
    assert exhaust.schedule == schedule


def test_exhaust_air_setability():
    """Test the setting of properties of ExhaustAir."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Bathroom Exhaust Air Schedule', simple_office,
                               None, schedule_types.fractional)
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)

    exhaust.identifier = 'Lab Zone Exhaust Air'
    assert exhaust.identifier == 'Lab Zone Exhaust Air'
    exhaust.flow_per_area = 0.0067
    assert exhaust.flow_per_area == 0.0067
    exhaust.flow_per_fixture = 0.5
    assert exhaust.flow_per_fixture == 0.5
    exhaust.fixture_count = 2
    assert exhaust.fixture_count == 2
    exhaust.schedule = schedule
    assert exhaust.schedule == schedule
    exhaust.pressure_rise = 250
    assert exhaust.pressure_rise == 250
    exhaust.efficiency = 0.5
    assert exhaust.efficiency == 0.5


def test_exhaust_equality():
    """Test the equality of ExhaustAir objects."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office ExhaustAir Schedule', simple_office,
                               None, schedule_types.fractional)
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)
    exhaust_dup = exhaust.duplicate()
    exhaust_alt = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)
    exhaust_alt.schedule = schedule

    assert exhaust is exhaust
    assert exhaust is not exhaust_dup
    assert exhaust == exhaust_dup
    exhaust_dup.flow_per_area = 0.01
    assert exhaust != exhaust_dup
    assert exhaust != exhaust_alt


def test_exhaust_lockability():
    """Test the lockability of ExhaustAir objects."""
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)

    exhaust.flow_per_fixture = 0.01
    exhaust.lock()
    with pytest.raises(AttributeError):
        exhaust.flow_per_fixture = 0.0025
    exhaust.unlock()
    exhaust.flow_per_fixture = 0.0025


def test_exhaust_dict_methods():
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office ExhaustAir Schedule', simple_office,
                               None, schedule_types.fractional)
    exhaust = ExhaustAir('Bathroom Exhaust Air', 0.0003304, 0.0236)

    vent_dict = exhaust.to_dict()
    new_exhaust = ExhaustAir.from_dict(vent_dict)
    assert new_exhaust == exhaust
    assert vent_dict == new_exhaust.to_dict()

    exhaust.schedule = schedule
    vent_dict = exhaust.to_dict()
    new_exhaust = ExhaustAir.from_dict(vent_dict)
    assert new_exhaust == exhaust
    assert vent_dict == new_exhaust.to_dict()


def test_exhaust_average():
    """Test the ExhaustAir.average method."""
    weekday_office = ScheduleDay('Weekday Office ExhaustAir', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby ExhaustAir', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office ExhaustAir', [0])
    weekend_lobby = ScheduleDay('Weekend Office ExhaustAir', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office ExhaustAir', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby ExhaustAir', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_vent = ExhaustAir('Office ExhaustAir', 0.0006, 0, 1, office_schedule)
    lobby_vent = ExhaustAir('Lobby ExhaustAir', 0, 0.01, 8, lobby_schedule)

    office_avg = ExhaustAir.average('Average ExhaustAir', [office_vent, lobby_vent])
    assert office_avg.flow_per_area == pytest.approx(0.0003, rel=1e-3)
    assert office_avg.flow_per_fixture == pytest.approx(0.08, rel=1e-3)
    assert office_avg.fixture_count == 1

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals

    office_vent.schedule = None
    lobby_vent.schedule = None
    office_avg = ExhaustAir.average('Average ExhaustAir', [office_vent, lobby_vent])

    assert office_avg._schedule is None
    assert office_avg.schedule == always_on
