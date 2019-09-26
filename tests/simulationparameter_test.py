# coding=utf-8
from honeybee_energy.simulationparameter import SimulationParameter
from honeybee_energy.simulation.runperiod import RunPeriod
from honeybee_energy.simulation.control import SimulationControl
from honeybee_energy.simulation.shadowcalculation import ShadowCalculation
from honeybee_energy.simulation.sizing import SizingParameter

from ladybug.dt import Date

import pytest


def test_simulation_parameter_init():
    """Test the initialization of SimulationParameter and basic properties."""
    sim_par = SimulationParameter()
    str(sim_par)  # test the string representation

    assert sim_par.run_period == RunPeriod()
    assert sim_par.timestep == 6
    assert sim_par.simulation_control == SimulationControl()
    assert sim_par.shadow_calculation == ShadowCalculation()
    assert sim_par.sizing_parameter == SizingParameter()


def test_simulation_parameter_setability():
    """Test the setting of properties of SimulationParameter."""
    sim_par = SimulationParameter()

    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    sim_par.run_period = run_period
    assert sim_par.run_period == run_period
    sim_par.timestep = 4
    assert sim_par.timestep == 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    assert sim_par.simulation_control == sim_control_alt
    shadow_calc_alt = ShadowCalculation('FullExteriorWithReflections')
    sim_par.shadow_calculation = shadow_calc_alt
    assert sim_par.shadow_calculation == shadow_calc_alt
    sizing_alt = SizingParameter(1, 1)
    sim_par.sizing_parameter = sizing_alt
    assert sim_par.sizing_parameter == sizing_alt


def test_simulation_parameter_equality():
    """Test the equality of SimulationParameter objects."""
    sim_par = SimulationParameter()
    sim_par_dup = sim_par.duplicate()
    sim_par_alt = SimulationParameter(timestep=4)

    assert sim_par is sim_par
    assert sim_par is not sim_par_dup
    assert sim_par == sim_par_dup
    sim_par_dup.timestep = 12
    assert sim_par != sim_par_dup
    assert sim_par != sim_par_alt


def test_simulation_parameter_init_from_idf():
    """Test the initialization of SimulationParameter from_idf."""
    sim_par = SimulationParameter()
    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    sim_par.run_period = run_period
    sim_par.timestep = 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    shadow_calc_alt = ShadowCalculation(calculation_frequency=20)
    sim_par.shadow_calculation = shadow_calc_alt
    sizing_alt = SizingParameter(1, 1)
    sim_par.sizing_parameter = sizing_alt

    idf_str = sim_par.to_idf()
    rebuilt_sim_par = SimulationParameter.from_idf(idf_str)
    assert sim_par == rebuilt_sim_par
    assert rebuilt_sim_par.to_idf() == idf_str


def test_simulation_parameter_dict_methods():
    """Test the to/from dict methods."""
    sim_par = SimulationParameter()
    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    sim_par.run_period = run_period
    sim_par.timestep = 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    shadow_calc_alt = ShadowCalculation(calculation_frequency=20)
    sim_par.shadow_calculation = shadow_calc_alt
    sizing_alt = SizingParameter(1, 1)
    sim_par.sizing_parameter = sizing_alt

    sim_par_dict = sim_par.to_dict()
    new_sim_par = SimulationParameter.from_dict(sim_par_dict)
    assert new_sim_par == sim_par
    assert sim_par_dict == new_sim_par.to_dict()
