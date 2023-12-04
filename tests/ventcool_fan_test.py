# coding=utf-8
from honeybee.room import Room
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.ventcool.fan import VentilationFan

import pytest


def test_ventilation_fan_init():
    """Test the initialization of VentilationFan and basic properties."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)
    str(vent_fan)  # test the string representation

    assert vent_fan.identifier == vent_fan.display_name == 'Night Flushing Fan'
    assert vent_fan.flow_rate == 1.5
    assert vent_fan.ventilation_type == 'Exhaust'
    assert vent_fan.pressure_rise == 300
    assert vent_fan.efficiency == 0.65
    assert vent_fan.control == night_flush_control


def test_ventilation_fan_default():
    """Test the default properties of VentilationFan."""
    vent_fan = VentilationFan('Night Flushing Fan', 1.5)
    assert vent_fan.pressure_rise == pytest.approx(266.666, rel=1e-3)
    assert vent_fan.efficiency == 0.7

    vent_fan = VentilationFan('Night Flushing Fan', 1.5, pressure_rise=300)
    assert vent_fan.pressure_rise == 300
    assert 0.6 < vent_fan.efficiency < 0.7

    vent_fan = VentilationFan('VAV_default', 6, pressure_rise=1000)
    assert vent_fan.pressure_rise == 1000
    assert 0.5 < vent_fan.efficiency < 0.7

    vent_fan = VentilationFan('Constant_DOAS_Fan', 2, pressure_rise=600)
    assert vent_fan.pressure_rise == 600
    assert 0.5 < vent_fan.efficiency < 0.7

    vent_fan = VentilationFan('ERV_Exhaust_fan', 0.015, pressure_rise=60)
    assert vent_fan.pressure_rise == 60
    assert 0.3 < vent_fan.efficiency < 0.6

    vent_fan = VentilationFan('Fan_Coil_Fan', 0.03, pressure_rise=250)
    assert vent_fan.pressure_rise == 250
    assert 0.1 < vent_fan.efficiency < 0.3


def test_ventilation_fan_equality():
    """Test the equality of VentilationFan objects."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)
    vent_fan_dup = vent_fan.duplicate()
    vent_fan_alt = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 250, 0.65, night_flush_control
    )

    assert vent_fan is vent_fan
    assert vent_fan is not vent_fan_dup
    assert vent_fan == vent_fan_dup
    vent_fan_dup.flow_rate = 2
    assert vent_fan != vent_fan_dup
    assert vent_fan != vent_fan_alt


def test_ventilation_fan_lockability():
    """Test the lockability of VentilationFan objects."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)

    vent_fan.flow_rate = 2
    vent_fan.lock()
    with pytest.raises(AttributeError):
        vent_fan.flow_rate = 3
    vent_fan.unlock()
    vent_fan.flow_rate = 3


def test_ventilation_fan_dict_methods():
    """Test the to/from dict methods."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)

    fan_dict = vent_fan.to_dict()
    new_vent_fan = VentilationFan.from_dict(fan_dict)
    assert new_vent_fan == vent_fan
    assert fan_dict == new_vent_fan.to_dict()


def test_ventilation_fan_idf_methods():
    """Test the to/from IDF methods."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)

    fan_idf = vent_fan.to_idf('Test Room')
    new_vent_fan, zone_id = VentilationFan.from_idf(
        fan_idf, {'Night Flushing Schedule': night_sch})
    assert new_vent_fan == vent_fan
    assert fan_idf == new_vent_fan.to_idf('Test Room')


def test_assign_to_room():
    """Test the assignment of ventilation fans to rooms."""
    night_sch = ScheduleRuleset.from_daily_values(
        'Night Flushing Schedule',
        [1, 1, 1, 1, 1, 1, 1, 1, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 0, 1, 1, 1])
    night_flush_control = VentilationControl(
        min_indoor_temperature=18, delta_temperature=0, schedule=night_sch)
    vent_fan = VentilationFan(
        'Night Flushing Fan', 1.5, 'Exhaust', 300, 0.65, night_flush_control)
    exhaust_fan = VentilationFan('ERV_Exhaust_fan', 0.015, pressure_rise=60)

    room = Room.from_box('ShoeBox', 5, 10, 3, 0)

    assert len(room.properties.energy.fans) == 0
    room.properties.energy.fans = [vent_fan]
    assert len(room.properties.energy.fans) == 1
    room.properties.energy.add_fan(exhaust_fan)
    assert len(room.properties.energy.fans) == 2

    idf_str = room.to.idf(room)
    assert idf_str.find('ZoneVentilation:DesignFlowRate,') > -1
