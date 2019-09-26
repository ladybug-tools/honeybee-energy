# coding=utf-8
from honeybee_energy.simulation.control import SimulationControl

import pytest


def test_simulation_control_init():
    """Test the initialization of SimulationControl and basic properties."""
    sim_control = SimulationControl()
    str(sim_control)  # test the string representation

    assert sim_control.do_zone_sizing
    assert sim_control.do_system_sizing
    assert sim_control.do_plant_sizing
    assert not sim_control.run_for_sizing_periods
    assert sim_control.run_for_run_periods


def test_simulation_control_setability():
    """Test the setting of properties of SimulationControl."""
    sim_control = SimulationControl()

    sim_control.do_zone_sizing = False
    assert not sim_control.do_zone_sizing
    sim_control.do_system_sizing = False
    assert not sim_control.do_system_sizing
    sim_control.do_plant_sizing = False
    assert not sim_control.do_plant_sizing
    sim_control.run_for_sizing_periods = True
    assert sim_control.run_for_sizing_periods
    sim_control.run_for_run_periods = False
    assert not sim_control.run_for_run_periods


def test_simulation_control_equality():
    """Test the equality of SimulationControl objects."""
    sim_control = SimulationControl()
    sim_control_dup = sim_control.duplicate()
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)

    assert sim_control is sim_control
    assert sim_control is not sim_control_dup
    assert sim_control == sim_control_dup
    sim_control_dup.run_for_sizing_periods = True
    assert sim_control != sim_control_dup
    assert sim_control != sim_control_alt


def test_simulation_control_init_from_idf():
    """Test the initialization of SimulationControl from_idf."""
    sim_control = SimulationControl(run_for_sizing_periods=True,
                                    run_for_run_periods=False)

    idf_str = sim_control.to_idf()
    rebuilt_sim_control = SimulationControl.from_idf(idf_str)
    assert sim_control == rebuilt_sim_control
    assert rebuilt_sim_control.to_idf() == idf_str


def test_simulation_control_dict_methods():
    """Test the to/from dict methods."""
    sim_control = SimulationControl(run_for_sizing_periods=True,
                                    run_for_run_periods=False)

    cntrl_dict = sim_control.to_dict()
    new_sim_control = SimulationControl.from_dict(cntrl_dict)
    assert new_sim_control == sim_control
    assert cntrl_dict == new_sim_control.to_dict()
