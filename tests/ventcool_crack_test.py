# coding=utf-8
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee.room import Room

import pytest


def test_crack():
    """Test the initialization of AFNCrack."""
    vent_afn = AFNCrack(flow_coefficient=0.01, flow_exponent=0.65)

    vent_afn.__repr__()  # Test str

    assert vent_afn.flow_coefficient == pytest.approx(0.01, abs=1e-10)
    assert vent_afn.flow_exponent == pytest.approx(0.65, abs=1e-10)

    # Test setting values
    with pytest.raises(AssertionError):
        vent_afn.flow_coefficient = -1
    with pytest.raises(AssertionError):
        vent_afn.flow_exponent = 2


def test_ventilation_opening_equality():
    """Test the equality of AFNCrack objects."""
    ventilation = AFNCrack(0.01, 0.65)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = AFNCrack(0.02, 0.7)

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.flow_coefficient = 0.02
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_ventilation_opening_lockability():
    """Test the lockability of AFNCrack objects."""
    ventilation = AFNCrack(0.01, 0.65)

    ventilation.flow_exponent = 0.7
    ventilation.lock()
    with pytest.raises(AttributeError):
        ventilation.flow_exponent = 0.5
    ventilation.unlock()
    ventilation.flow_exponent = 0.5


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    ventilation = AFNCrack(0.01, 0.65)

    vent_dict = ventilation.to_dict()
    new_ventilation = AFNCrack.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    # Test values
    vent_dict['flow_coefficient'] == \
        pytest.approx(0.01, abs=1e-10)
    vent_dict['flow_exponent'] == pytest.approx(0.65, abs=1e-10)
    new_ventilation.flow_coefficient == \
        pytest.approx(0.01, abs=1e-10)
    new_ventilation.flow_exponent == \
        pytest.approx(0.65, abs=1e-10)