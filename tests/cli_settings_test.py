"""Test cli settings module."""
from click.testing import CliRunner
from honeybee_energy.cli.settings import default_sim_par, load_balance_sim_par, \
    comfort_sim_par, sizing_sim_par, custom_sim_par, run_period
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.simulation.runperiod import RunPeriod
from ladybug.dt import Date

import json


def test_default_sim_par():
    """Test the default_sim_par command."""
    runner = CliRunner()
    ddy_path = './tests/ddy/chicago.ddy'

    result = runner.invoke(default_sim_par, [ddy_path])
    assert result.exit_code == 0
    simpar_dict = json.loads(result.output)
    sim_par = SimulationParameter.from_dict(simpar_dict)

    assert 'Zone Ideal Loads Supply Air Total Cooling Energy' in sim_par.output.outputs
    assert 'Chiller Electric Energy' in sim_par.output.outputs


def test_load_balance_sim_par():
    """Test the load_balance_sim_par command."""
    runner = CliRunner()
    ddy_path = './tests/ddy/chicago.ddy'

    result = runner.invoke(load_balance_sim_par, [ddy_path, '--load-type', 'Sensible'])
    assert result.exit_code == 0
    simpar_dict = json.loads(result.output)
    sim_par = SimulationParameter.from_dict(simpar_dict)

    assert 'Zone Ideal Loads Supply Air Sensible Cooling Energy' in sim_par.output.outputs
    assert 'Zone People Sensible Heating Energy' in sim_par.output.outputs


def test_comfort_sim_par():
    """Test the comfort_sim_par command."""
    runner = CliRunner()
    ddy_path = './tests/ddy/chicago.ddy'

    result = runner.invoke(comfort_sim_par, [ddy_path])
    assert result.exit_code == 0
    simpar_dict = json.loads(result.output)
    sim_par = SimulationParameter.from_dict(simpar_dict)

    assert 'Zone Mean Air Temperature' in sim_par.output.outputs
    assert 'Surface Inside Face Temperature' in sim_par.output.outputs


def test_sizing_sim_par():
    """Test the sizing_sim_par command."""
    runner = CliRunner()
    ddy_path = './tests/ddy/chicago.ddy'

    result = runner.invoke(sizing_sim_par, [ddy_path, '--load-type', 'Sensible'])
    assert result.exit_code == 0
    simpar_dict = json.loads(result.output)
    sim_par = SimulationParameter.from_dict(simpar_dict)

    assert 'Zone Ideal Loads Supply Air Sensible Cooling Energy' in sim_par.output.outputs
    assert 'Zone People Sensible Heating Energy' in sim_par.output.outputs
    assert sim_par.simulation_control.run_for_sizing_periods


def test_custom_sim_par():
    """Test the custom_sim_par command."""
    runner = CliRunner()
    ddy_path = './tests/ddy/chicago.ddy'

    result = runner.invoke(custom_sim_par, [ddy_path, 'Surface Window Transmitted Beam Solar Radiation Energy'])
    assert result.exit_code == 0
    simpar_dict = json.loads(result.output)
    sim_par = SimulationParameter.from_dict(simpar_dict)

    assert 'Surface Window Transmitted Beam Solar Radiation Energy' in sim_par.output.outputs


def test_run_period():
    """Test the run_period command."""
    runner = CliRunner()

    result = runner.invoke(run_period, ['1', '6', '1', '12'])
    assert result.exit_code == 0
    run_per_dict = json.loads(result.output)
    run_per = RunPeriod.from_dict(run_per_dict)

    assert run_per.start_date == Date(1, 6)
    assert run_per.end_date == Date(1, 12)
