# coding=utf-8
from honeybee_energy.simulation.sizing import SizingParameter

from ladybug.ddy import DDY
from ladybug.designday import DesignDay

import pytest


def test_sizing_parameter_init():
    """Test the initialization of SizingParameter and basic properties."""
    sizing = SizingParameter()
    str(sizing)  # test the string representation

    assert len(sizing.design_days) == 0
    assert len(sizing) == 0
    assert sizing.heating_factor == 1.25
    assert sizing.cooling_factor == 1.15


def test_sizing_parameter_setability():
    """Test the setting of properties of SizingParameter."""
    sizing = SizingParameter()

    relative_path = './tests/ddy/chicago_monthly.ddy'
    sizing.add_from_ddy(relative_path)
    assert len(sizing.design_days) == 12
    assert len(sizing) == 12
    assert isinstance(sizing[0], DesignDay)
    sizing.heating_factor = 1
    assert sizing.heating_factor == 1
    sizing.cooling_factor = 1
    assert sizing.cooling_factor == 1


def test_sizing_parameter_equality():
    """Test the equality of SizingParameter objects."""
    sizing = SizingParameter()
    relative_path = './tests/ddy/chicago_monthly.ddy'
    sizing.add_from_ddy(relative_path)
    sizing_dup = sizing.duplicate()
    sizing_alt = SizingParameter(None, 1)

    assert sizing is sizing
    assert sizing is not sizing_dup
    assert sizing == sizing_dup
    sizing_dup.cooling_factor = 1
    assert sizing != sizing_dup
    assert sizing != sizing_alt


def test_sizing_parameter_init_from_idf():
    """Test the initialization of SimulationControl from_idf."""
    sizing = SizingParameter(None, 1)
    relative_path = './tests/ddy/chicago.ddy'
    sizing.add_from_ddy_996_004(relative_path)

    des_days, idf_str = sizing.to_idf()
    rebuilt_sizing = SizingParameter.from_idf(des_days, idf_str)
    rebuilt_sizing.apply_location(sizing[0].location)
    assert sizing == rebuilt_sizing
    assert rebuilt_sizing.to_idf()[1] == idf_str
    for dday1, dday2 in zip(des_days, rebuilt_sizing.to_idf()[0]):
        assert dday1 == dday2


def test_sizing_parameter_dict_methods():
    """Test the to/from dict methods."""
    sizing = SizingParameter(None, 1)
    relative_path = './tests/ddy/chicago.ddy'
    sizing.add_from_ddy_996_004(relative_path)

    sizing_dict = sizing.to_dict()
    new_sizing = SizingParameter.from_dict(sizing_dict)
    new_sizing.apply_location(sizing[0].location)
    assert new_sizing == sizing
    assert sizing_dict == new_sizing.to_dict()


def test_sizing_parameter_to_ddy():
    """Test the setting of properties of SizingParameter."""
    sizing = SizingParameter()
    relative_path = './tests/ddy/chicago_monthly.ddy'
    sizing.add_from_ddy(relative_path)
    ddy_obj = DDY.from_ddy_file(relative_path)

    assert sizing.to_ddy() == ddy_obj
