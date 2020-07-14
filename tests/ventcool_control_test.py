# coding=utf-8
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.schedules import always_on
import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time

import pytest


def test_ventilation_control_init():
    """Test the initialization of VentilationControl and basic properties."""
    ventilation = VentilationControl()
    str(ventilation)  # test the string representation

    assert ventilation.min_indoor_temperature == -100
    assert ventilation.max_indoor_temperature == 100
    assert ventilation.min_outdoor_temperature == -100
    assert ventilation.max_outdoor_temperature == 100
    assert ventilation.delta_temperature == -100
    assert ventilation.schedule == always_on

    ventilation.min_indoor_temperature = 22
    ventilation.max_indoor_temperature = 28
    ventilation.min_outdoor_temperature = 12
    ventilation.max_outdoor_temperature = 32
    ventilation.delta_temperature = 0

    assert ventilation.min_indoor_temperature == 22
    assert ventilation.max_indoor_temperature == 28
    assert ventilation.min_outdoor_temperature == 12
    assert ventilation.max_outdoor_temperature == 32
    assert ventilation.delta_temperature == 0


def test_ventilation_control_init_schedule():
    """Test the initialization of VentilationControl with a schedule."""
    simple_office = ScheduleDay('Simple Flush', [1, 0, 1],
                                [Time(0, 0), Time(9, 0), Time(22, 0)])
    schedule = ScheduleRuleset('Night Flush Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = VentilationControl(100, schedule=schedule)
    str(ventilation)  # test the string representation

    assert ventilation.min_indoor_temperature == 100
    assert ventilation.schedule.identifier == 'Night Flush Schedule'
    assert ventilation.schedule.schedule_type_limit == schedule_types.fractional
    assert ventilation.schedule == schedule


def test_ventilation_control_equality():
    """Test the equality of VentilationControl objects."""
    simple_office = ScheduleDay('Simple Flush', [1, 0, 1],
                                [Time(0, 0), Time(9, 0), Time(22, 0)])
    schedule = ScheduleRuleset('Night Flush Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = VentilationControl(18, schedule=schedule)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = VentilationControl(20)
    ventilation_alt.schedule = schedule

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.delta_temperature = -2
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_ventilation_control_lockability():
    """Test the lockability of Ventilation objects."""
    ventilation = VentilationControl(20)

    ventilation.delta_temperature = -2
    ventilation.lock()
    with pytest.raises(AttributeError):
        ventilation.min_indoor_temperature = 22
    ventilation.unlock()
    ventilation.min_indoor_temperature = 22


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Flush', [1, 0, 1],
                                [Time(0, 0), Time(9, 0), Time(22, 0)])
    schedule = ScheduleRuleset('Night Flush Schedule', simple_office,
                               None, schedule_types.fractional)
    ventilation = VentilationControl(22, 28, 12, 32, 0)

    vent_dict = ventilation.to_dict()
    new_ventilation = VentilationControl.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    ventilation.schedule = schedule
    vent_dict = ventilation.to_dict()
    new_ventilation = VentilationControl.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()
