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
