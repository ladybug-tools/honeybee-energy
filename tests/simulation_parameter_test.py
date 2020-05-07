# coding=utf-8
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.simulation.output import SimulationOutput
from honeybee_energy.simulation.runperiod import RunPeriod
from honeybee_energy.simulation.daylightsaving import DaylightSavingTime
from honeybee_energy.simulation.control import SimulationControl
from honeybee_energy.simulation.shadowcalculation import ShadowCalculation
from honeybee_energy.simulation.sizing import SizingParameter

from ladybug_geometry.geometry2d.pointvector import Vector2D
from ladybug.dt import Date

import pytest


def test_simulation_parameter_init():
    """Test the initialization of SimulationParameter and basic properties."""
    sim_par = SimulationParameter()
    str(sim_par)  # test the string representation

    assert sim_par.output == SimulationOutput()
    assert sim_par.run_period == RunPeriod()
    assert sim_par.timestep == 6
    assert sim_par.simulation_control == SimulationControl()
    assert sim_par.shadow_calculation == ShadowCalculation()
    assert sim_par.sizing_parameter == SizingParameter()
    assert sim_par.north_angle == 0
    assert sim_par.north_vector == Vector2D(0, 1)
    assert sim_par.terrain_type == 'City'


def test_simulation_parameter_setability():
    """Test the setting of properties of SimulationParameter."""
    sim_par = SimulationParameter()

    output = SimulationOutput()
    output.add_zone_energy_use()
    sim_par.output = output
    assert sim_par.output == output
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
    sizing_alt = SizingParameter(None, 1, 1)
    relative_path = './tests/ddy/chicago_monthly.ddy'
    sizing_alt.add_from_ddy(relative_path)
    sim_par.sizing_parameter = sizing_alt
    assert sim_par.sizing_parameter == sizing_alt
    sim_par.north_angle = 20
    assert sim_par.north_angle == 20
    sim_par.terrain_type = 'Ocean'
    assert sim_par.terrain_type == 'Ocean'


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
    output = SimulationOutput()
    output.add_zone_energy_use()
    sim_par.output = output
    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    sim_par.run_period = run_period
    sim_par.timestep = 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    shadow_calc_alt = ShadowCalculation(calculation_frequency=20)
    sim_par.shadow_calculation = shadow_calc_alt
    sizing_alt = SizingParameter(None, 1, 1)
    relative_path = './tests/ddy/chicago.ddy'
    sizing_alt.add_from_ddy_996_004(relative_path)
    sim_par.sizing_parameter = sizing_alt

    idf_str = sim_par.to_idf()
    rebuilt_sim_par = SimulationParameter.from_idf(idf_str)
    rebuilt_sim_par.sizing_parameter.apply_location(sizing_alt[0].location)
    assert sim_par == rebuilt_sim_par
    assert rebuilt_sim_par.to_idf() == idf_str


def test_simulation_parameter_to_dict_simple():
    """Test the to_dict method with a simple SimulationParameter."""
    sim_par = SimulationParameter()
    sim_par_dict = sim_par.to_dict()

    assert 'output' in sim_par_dict
    assert 'run_period' in sim_par_dict
    assert 'timestep' in sim_par_dict
    assert 'simulation_control' in sim_par_dict
    assert 'shadow_calculation' in sim_par_dict
    assert 'sizing_parameter' in sim_par_dict


def test_simulation_parameter_to_dict_detailed():
    """Test the to_dict method with a detailed SimulationParameter."""
    sim_par = SimulationParameter()
    output = SimulationOutput()
    output.add_zone_energy_use()
    output.include_html = True
    output.reporting_frequency = 'Daily'
    output.add_summary_report('Annual Building Utility Performance Summary')
    output.add_summary_report('Climatic Data Summary')
    output.add_summary_report('Envelope Summary')
    sim_par.output = output
    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    run_period.daylight_saving_time = DaylightSavingTime(Date(3, 12), Date(11, 5))
    run_period.start_day_of_week = 'Monday'
    run_period.holidays = [Date(1, 1), Date(3, 17), Date(7, 4)]
    sim_par.run_period = run_period
    sim_par.timestep = 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    shadow_calc_alt = ShadowCalculation(calculation_frequency=20)
    sim_par.shadow_calculation = shadow_calc_alt
    sizing_alt = SizingParameter(None, 1, 1)
    relative_path = './tests/ddy/chicago.ddy'
    sizing_alt.add_from_ddy_996_004(relative_path)
    sim_par.sizing_parameter = sizing_alt

    sim_par_dict = sim_par.to_dict()

    assert 'outputs' in sim_par_dict['output']
    assert 'holidays' in sim_par_dict['run_period']
    assert 'daylight_saving_time' in sim_par_dict['run_period']
    assert 'design_days' in sim_par_dict['sizing_parameter']


def test_simulation_parameter_dict_methods():
    """Test the to/from dict methods."""
    sim_par = SimulationParameter()
    output = SimulationOutput()
    output.add_zone_energy_use()
    sim_par.output = output
    run_period = RunPeriod(Date(1, 1), Date(6, 21))
    sim_par.run_period = run_period
    sim_par.timestep = 4
    sim_control_alt = SimulationControl(run_for_sizing_periods=True,
                                        run_for_run_periods=False)
    sim_par.simulation_control = sim_control_alt
    shadow_calc_alt = ShadowCalculation(calculation_frequency=20)
    sim_par.shadow_calculation = shadow_calc_alt
    sizing_alt = SizingParameter(None, 1, 1)
    relative_path = './tests/ddy/chicago.ddy'
    sizing_alt.add_from_ddy_996_004(relative_path)
    sim_par.sizing_parameter = sizing_alt

    sim_par_dict = sim_par.to_dict()
    new_sim_par = SimulationParameter.from_dict(sim_par_dict)
    new_sim_par.sizing_parameter.apply_location(sizing_alt[0].location)
    assert new_sim_par == sim_par
    assert sim_par_dict == new_sim_par.to_dict()
