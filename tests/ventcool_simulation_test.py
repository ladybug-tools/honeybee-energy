# coding=utf-8
from honeybee_energy.ventcool.simulation import VentilationSimulationControl

import pytest


def test_simulation_control_init():
    """Test the initialization of VentilationSimulationControl."""
    # Test SingleZone w/ defaults and str
    vent = VentilationSimulationControl('SingleZone')
    vent.__repr__()

    # Test MultiZone
    vent = VentilationSimulationControl(
        'MultiZoneWithoutDistribution', 21, 101325, 0.5, 'LowRise', 90, 0.5)

    assert vent.vent_control_type == 'MultiZoneWithoutDistribution'
    assert vent.reference_temperature == pytest.approx(21, abs=1e-10)
    assert vent.reference_pressure == pytest.approx(101325, abs=1e-10)
    assert vent.reference_humidity_ratio == pytest.approx(0.5, abs=1e-10)
    assert vent.building_type == 'LowRise'
    assert vent.long_axis_angle == pytest.approx(90, abs=1e-10)
    assert vent.aspect_ratio == pytest.approx(0.5, abs=1e-10)

    # Test setting incorrect values
    with pytest.raises(AssertionError):
        vent.vent_control_type = 'SingleZne'
    with pytest.raises(TypeError):
        vent.reference_temperature = 'abc'
    with pytest.raises(AssertionError):
        vent.reference_pressure = 120000.001
    with pytest.raises(AssertionError):
        vent.reference_humidity_ratio = -1
    with pytest.raises(AssertionError):
        vent.building_type = 'MidRise'
    with pytest.raises(AssertionError):
        vent.long_axis_angle = 360
    with pytest.raises(AssertionError):
        vent.aspect_ratio = 0


def test_simulation_control_equality():
    """Test the equality of VentilationSimulationControl objects."""
    ventilation = VentilationSimulationControl(
        'MultiZoneWithoutDistribution', 21, 101325, 0.5, 'LowRise', 90, 0.5)
    ventilation_dup = ventilation.duplicate()
    ventilation_alt = VentilationSimulationControl(
        'MultiZoneWithoutDistribution', 22, 101321, 0.6, 'LowRise', 91, 0.7)

    assert ventilation is ventilation
    assert ventilation is not ventilation_dup
    assert ventilation == ventilation_dup
    ventilation_dup.reference_temperature = 30.0
    assert ventilation != ventilation_dup
    assert ventilation != ventilation_alt


def test_simulation_control_lockability():
    """Test the lockability of VentilationSimultionControl objects."""
    ventilation = VentilationSimulationControl(
        'MultiZoneWithoutDistribution', 21, 101325, 0.5, 'LowRise', 90, 0.5)

    ventilation.reference_pressure = 101340
    ventilation.lock()
    with pytest.raises(AttributeError):
        ventilation.reference_pressure = 30999
    ventilation.unlock()
    ventilation.reference_pressure = 31000


def test_ventilation_dict_methods():
    """Test the to/from dict methods."""
    ventilation = VentilationSimulationControl(
        'MultiZoneWithoutDistribution', 21, 101325, 0.5, 'LowRise', 90, 0.5)

    vent_dict = ventilation.to_dict()
    new_ventilation = VentilationSimulationControl.from_dict(vent_dict)
    assert new_ventilation == ventilation
    assert vent_dict == new_ventilation.to_dict()

    # Test values
    vent_dict['reference_temperature'] == pytest.approx(20, abs=1e-10)
    vent_dict['building_type'] == 'LowRise'

    new_ventilation.reference_pressure == \
        pytest.approx(101325, 1e-10)
    new_ventilation.building_type == 'LowRise'
