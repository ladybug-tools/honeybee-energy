# coding=utf-8
from honeybee_energy.simulation.sizing import SizingParameter

import pytest


def test_sizing_parameter_init():
    """Test the initialization of SizingParameter and basic properties."""
    sizing = SizingParameter()
    str(sizing)  # test the string representation

    assert sizing.heating_factor == 1.25
    assert sizing.cooling_factor == 1.15


def test_sizing_parameter_setability():
    """Test the setting of properties of SizingParameter."""
    sizing = SizingParameter()

    sizing.heating_factor = 1
    assert sizing.heating_factor == 1
    sizing.cooling_factor = 1
    assert sizing.cooling_factor == 1


def test_sizing_parameter_equality():
    """Test the equality of SizingParameter objects."""
    sizing = SizingParameter()
    sizing_dup = sizing.duplicate()
    sizing_alt = SizingParameter(1)

    assert sizing is sizing
    assert sizing is not sizing_dup
    assert sizing == sizing_dup
    sizing_dup.cooling_factor = 1
    assert sizing != sizing_dup
    assert sizing != sizing_alt


def test_simulation_control_init_from_idf():
    """Test the initialization of SimulationControl from_idf."""
    sizing = SizingParameter(1)

    idf_str = sizing.to_idf()
    rebuilt_sizing = SizingParameter.from_idf(idf_str)
    assert sizing == rebuilt_sizing
    assert rebuilt_sizing.to_idf() == idf_str


def test_simulation_control_dict_methods():
    """Test the to/from dict methods."""
    sizing = SizingParameter(1)

    sizing_dict = sizing.to_dict()
    new_sizing = SizingParameter.from_dict(sizing_dict)
    assert new_sizing == sizing
    assert sizing_dict == new_sizing.to_dict()
