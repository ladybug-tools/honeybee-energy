# coding=utf-8
from honeybee_energy.generator.loadcenter import ElectricLoadCenter

import pytest


def test_load_center_init():
    """Test the initialization of ElectricLoadCenter."""
    # Test SingleZone w/ defaults and str
    load_center = ElectricLoadCenter()
    str(load_center)  # test the string representation

    # Test MultiZone
    load_center = ElectricLoadCenter(0.98, 1.2)
    assert load_center.inverter_efficiency == 0.98
    assert load_center.inverter_dc_to_ac_size_ratio == 1.2

    # Test setting incorrect values
    with pytest.raises(AssertionError):
        load_center.inverter_efficiency = 1.1
    with pytest.raises(AssertionError):
        load_center.inverter_dc_to_ac_size_ratio = -1


def test_load_center_equality():
    """Test the equality of ElectricLoadCenter objects."""
    load_center = ElectricLoadCenter(0.98, 1.2)
    load_center_dup = load_center.duplicate()
    load_center_alt = ElectricLoadCenter(0.98, 1.15)

    assert load_center is load_center
    assert load_center is not load_center_dup
    assert load_center == load_center_dup
    load_center_dup.inverter_efficiency = 0.97
    assert load_center != load_center_dup
    assert load_center != load_center_alt


def test_load_center_dict_methods():
    """Test the to/from dict methods."""
    load_center = ElectricLoadCenter(0.98, 1.2)

    center_dict = load_center.to_dict()
    new_load_center = ElectricLoadCenter.from_dict(center_dict)
    assert new_load_center == load_center
    assert center_dict == new_load_center.to_dict()
