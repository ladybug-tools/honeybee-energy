# coding=utf-8
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee.room import Room

import pytest


def test_crack():
    """Test the initialization of AFNCrack."""
    vent_afn = AFNCrack(air_mass_flow_coefficient_reference=0.01,
                        air_mass_flow_exponent=0.65, crack_factor=1)

    vent_afn.__repr__()  # Test str

    assert vent_afn.air_mass_flow_coefficient_reference == pytest.approx(0.01, abs=1e-10)
    assert vent_afn.air_mass_flow_exponent == pytest.approx(0.65, abs=1e-10)
    assert vent_afn.crack_factor == pytest.approx(1, abs=1e-10)

    # Test setting values
    with pytest.raises(AssertionError):
        vent_afn.air_mass_flow_coefficient_reference = -1
    with pytest.raises(AssertionError):
        vent_afn.air_mass_flow_exponent = 2
    with pytest.raises(AssertionError):
        vent_afn.crack_factor = 2


def test_ventilation_crack_parent():
    """Test the AFNCrack with a parent."""
    room = Room.from_box('ShoeBoxZone', 5, 10, 3)
    south_face = room[3]

    vent_crack = AFNCrack(0.01)
    assert not vent_crack.has_parent
    assert vent_crack.parent is None

    south_face.properties.energy.vent_crack = vent_crack

    assert vent_crack.has_parent
    assert vent_crack.parent.identifier == south_face.identifier


def test_ventilation_opening_equality():
    """Test the equality of AFNCrack objects."""
    ventilation = AFNCrack(0.01, 0.65, 1)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = AFNCrack(0.02, 0.7, 0.5)

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.air_mass_flow_coefficient_reference = 0.02
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_ventilation_opening_lockability():
    """Test the lockability of AFNCrack objects."""
    ventilation = AFNCrack(0.01, 0.65, 1)

    ventilation.crack_factor = 0.3
    ventilation.lock()
    with pytest.raises(AttributeError):
        ventilation.crack_factor = 0.5
    ventilation.unlock()
    ventilation.crack_factor = 0.5


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    ventilation = AFNCrack(0.01, 0.65, 1)

    vent_dict = ventilation.to_dict()
    new_ventilation = AFNCrack.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    # Test values
    vent_dict['air_mass_flow_coefficient_reference'] == \
        pytest.approx(0.01, abs=1e-10)
    vent_dict['air_mass_flow_exponent'] == pytest.approx(0.65, abs=1e-10)
    new_ventilation.air_mass_flow_coefficient_reference == \
        pytest.approx(0.01, abs=1e-10)
    new_ventilation.air_mass_flow_exponent == \
        pytest.approx(0.65, abs=1e-10)