# coding=utf-8
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset
import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee.room import Room

from ladybug.dt import Time

import pytest


def test_ventilation_opening_init():
    """Test the initialization of VentilationOpening and basic properties."""
    ventilation = VentilationOpening()
    str(ventilation)  # test the string representation

    assert ventilation.fraction_area_operable == 0.5
    assert ventilation.fraction_height_operable == 1.0
    assert ventilation.discharge_coefficient == 0.45
    assert not ventilation.wind_cross_vent
    assert not ventilation.has_parent
    assert ventilation.parent is None

    ventilation.fraction_area_operable = 0.25
    ventilation.fraction_height_operable = 0.5
    ventilation.discharge_coefficient = 0.25
    ventilation.wind_cross_vent = True

    assert ventilation.fraction_area_operable == 0.25
    assert ventilation.fraction_height_operable == 0.5
    assert ventilation.discharge_coefficient == 0.25
    assert ventilation.wind_cross_vent


def test_ventilation_opening_afn_init():
    """Test the initialization of VentilationOpening and basic properties for AFN."""
    vent_afn = VentilationOpening(
        fraction_area_operable=1, fraction_height_operable=1, discharge_coefficient=0.17,
        wind_cross_vent=False, flow_coefficient_closed=0.001,
        flow_exponent_closed=0.667, two_way_threshold=0.0001)

    assert vent_afn.flow_coefficient_closed == pytest.approx(0.001, abs=1e-10)
    assert vent_afn.flow_exponent_closed == pytest.approx(0.667, abs=1e-10)
    assert vent_afn.two_way_threshold == pytest.approx(0.0001)

    # Test setting values
    with pytest.raises(AssertionError):
        vent_afn.flow_coefficient_closed = -1
    with pytest.raises(AssertionError):
        vent_afn.flow_exponent_closed = 0.1
    with pytest.raises(AssertionError):
        vent_afn.two_way_threshold = -1

    vent_afn.flow_coefficient_closed = 0.002
    vent_afn.flow_exponent_closed = 0.65
    vent_afn.two_way_threshold = 0.001

    assert vent_afn.flow_coefficient_closed == pytest.approx(0.002, abs=1e-10)
    assert vent_afn.flow_exponent_closed == pytest.approx(0.65, abs=1e-10)
    assert vent_afn.two_way_threshold == pytest.approx(0.001)


def test_ventilation_opening_parent():
    """Test the VentilationOpening with a parent."""
    room = Room.from_box('ShoeBoxZone', 5, 10, 3)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    aperture = south_face.apertures[0]

    ventilation = VentilationOpening()
    assert not ventilation.has_parent
    assert ventilation.parent is None

    with pytest.raises(AssertionError):
        aperture.properties.energy.vent_opening = ventilation

    aperture.is_operable = True
    aperture.properties.energy.vent_opening = ventilation
    assert ventilation.has_parent
    assert ventilation.parent.identifier == aperture.identifier


def test_ventilation_opening_equality():
    """Test the equality of Ventilation objects."""
    ventilation = VentilationOpening(0.25, 0.5, 0.25, True, 0.001, 0.667, 1e-3)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = VentilationOpening(0.5, 0.5, 0.25, True, 0.001, 0.667, 1e-3)

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.fraction_area_operable = 0.3
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_ventilation_opening_to_idf():
    """Test the initialization of Ventilation from_idf."""
    room = Room.from_box('ShoeBoxZone', 5, 10, 3)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    aperture = south_face.apertures[0]
    aperture.is_operable = True
    simple_office = ScheduleDay('Simple Flush', [1, 0, 1],
                                [Time(0, 0), Time(9, 0), Time(22, 0)])
    schedule = ScheduleRuleset('Night Flush Schedule', simple_office,
                               None, schedule_types.fractional)
    vent_control = VentilationControl(18, schedule=schedule)
    room.properties.energy.window_vent_control = vent_control

    ventilation = VentilationOpening()
    with pytest.raises(AssertionError):
        ventilation.to_idf()
    aperture.properties.energy.vent_opening = ventilation

    idf_str = ventilation.to_idf()
    assert room.identifier in idf_str
    assert schedule.identifier in idf_str


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    ventilation = VentilationOpening(0.25, 0.5, 0.25, True)

    vent_dict = ventilation.to_dict()
    print(vent_dict)
    new_ventilation = VentilationOpening.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    # Test with afn
    ventilation_afn = VentilationOpening(1, 1, 0.17, False, 0.001, 0.667, 1e-3)
    vent_afn_dict = ventilation_afn.to_dict()
    vent_afn_dict['flow_coefficient_closed'] == pytest.approx(0.002, abs=1e-10)
    vent_afn_dict['flow_exponent_closed'] == pytest.approx(0.667, abs=1e-10)
    vent_afn_dict['two_way_threshold'] == pytest.approx(0.0001)
    new_ventilation_afn = VentilationOpening.from_dict(vent_afn_dict)
    assert new_ventilation_afn == ventilation_afn
    assert vent_afn_dict == new_ventilation_afn.to_dict()
