# coding=utf-8
import pytest

from ladybug_geometry.geometry3d.pointvector import Point3D

from honeybee_energy.load.daylight import DaylightingControl


def test_daylighting_control_init():
    """Test the initialization of DaylightingControl and basic properties."""
    position = Point3D(5, 5, 0.8)
    daylight = DaylightingControl(position)
    str(daylight)  # test the string representation

    assert daylight.sensor_position == position
    assert daylight.illuminance_setpoint == 300
    assert daylight.control_fraction == 1
    assert daylight.min_power_input == 0.3
    assert daylight.min_light_output == 0.2
    assert not daylight.off_at_minimum

    daylight.illuminance_setpoint = 500
    daylight.control_fraction = 0.5
    daylight.min_power_input = 0.2
    daylight.min_light_output = 0.1
    daylight.off_at_minimum = True

    assert daylight.illuminance_setpoint == 500
    assert daylight.control_fraction == 0.5
    assert daylight.min_power_input == 0.2
    assert daylight.min_light_output == 0.1
    assert daylight.off_at_minimum


def test_daylighting_control_equality():
    """Test the equality of DaylightingControl objects."""
    position = Point3D(5, 5, 0.8)
    daylight = DaylightingControl(position)
    daylight_dup = daylight.duplicate()
    daylight_alt = DaylightingControl(position, 150)

    assert daylight is daylight
    assert daylight is not daylight_dup
    assert daylight == daylight_dup
    daylight_dup.illuminance_setpoint = 200
    assert daylight != daylight_dup
    assert daylight != daylight_alt


def test_daylighting_control_dict_methods():
    """Test the to/from dict methods."""
    position = Point3D(5, 5, 0.8)
    daylight = DaylightingControl(position, 150)

    dl_dict = daylight.to_dict()
    new_daylight = DaylightingControl.from_dict(dl_dict)
    assert new_daylight == daylight
    assert dl_dict == new_daylight.to_dict()


def test_daylighting_control_idf_methods():
    """Test the to/from idf methods."""
    position = Point3D(5, 5, 0.8)
    daylight = DaylightingControl(position, 150)

    dl_idf, dl_pt_idf = daylight.to_idf()
    new_daylight = DaylightingControl.from_idf(dl_idf, dl_pt_idf)
    assert new_daylight == daylight
    assert dl_idf == new_daylight.to_idf()[0]
