# coding=utf-8
from honeybee_energy.simulation.output import SimulationOutput

import pytest


def test_simulation_output_init():
    """Test the initialization of SimulationOutput and basic properties."""
    sim_output = SimulationOutput()
    str(sim_output)  # test the string representation

    assert len(sim_output.outputs) == 0
    sim_output.add_zone_energy_use()
    assert len(sim_output.outputs) > 1
    assert sim_output.reporting_frequency == 'Hourly'
    assert sim_output.include_sqlite
    assert sim_output.include_html
    assert len(sim_output.summary_reports) == 1
    assert sim_output.summary_reports == ('AllSummary',)


def test_simulation_output_setability():
    """Test the setting of properties of SimulationOutput."""
    sim_output = SimulationOutput()

    sim_output.outputs = ['Zone Ideal Loads Supply Air Total Cooling Energy']
    assert sim_output.outputs == ('Zone Ideal Loads Supply Air Total Cooling Energy',)
    sim_output.reporting_frequency = 'Daily'
    assert sim_output.reporting_frequency == 'Daily'
    sim_output.include_sqlite = False
    assert not sim_output.include_sqlite
    sim_output.include_html = True
    assert sim_output.include_html
    sim_output.summary_reports = ['ComponentSizingSummary']
    assert sim_output.summary_reports == ('ComponentSizingSummary',)

    with pytest.raises(AssertionError):
        sim_output.outputs = 'Zone Ideal Loads Supply Air Total Cooling Energy'
    with pytest.raises(AssertionError):
        sim_output.reporting_frequency = 'Biannually'
    with pytest.raises(AssertionError):
        sim_output.outputs = 'ComponentSizingSummary'


def test_simulation_output_add_summary_report():
    """Test the SimulationOutput add_summary_report methods."""
    sim_output = SimulationOutput()

    sim_output.add_summary_report('ComponentSizingSummary')
    assert len(sim_output.summary_reports) == 2


def test_simulation_output_add_output():
    """Test the SimulationOutput add_output methods."""
    sim_output = SimulationOutput()

    sim_output.outputs = ['Zone Ideal Loads Supply Air Total Cooling Energy']
    sim_output.add_output('Zone Ideal Loads Supply Air Total Cooling Energy')
    assert sim_output.outputs == ('Zone Ideal Loads Supply Air Total Cooling Energy',)
    sim_output.add_output('Zone Ideal Loads Supply Air Total Heating Energy')
    assert len(sim_output.outputs) == 2


def test_simulation_output_add_zone_energy_use():
    """Test the SimulationOutput add_zone_energy_use methods."""
    sim_output = SimulationOutput()
    sim_output.add_zone_energy_use('all')
    assert len(sim_output.outputs) == 9

    sim_output = SimulationOutput()
    sim_output.add_zone_energy_use('total')
    assert len(sim_output.outputs) == 8

    sim_output = SimulationOutput()
    sim_output.add_zone_energy_use('sensible')
    assert len(sim_output.outputs) == 10

    sim_output = SimulationOutput()
    sim_output.add_zone_energy_use('latent')
    assert len(sim_output.outputs) == 6

    with pytest.raises(ValueError):
        sim_output.add_zone_energy_use('convective')


def test_simulation_output_add_hvac_energy_use():
    """Test the SimulationOutput add_hvac_energy_use methods."""
    sim_output = SimulationOutput()
    sim_output.add_hvac_energy_use()
    assert len(sim_output.outputs) >= 15


def test_simulation_output_add_gains_and_losses():
    """Test the SimulationOutput add_gains_and_losses methods."""
    sim_output = SimulationOutput()
    sim_output.add_gains_and_losses('total')
    assert len(sim_output.outputs) == 12

    sim_output = SimulationOutput()
    sim_output.add_gains_and_losses('sensible')
    assert len(sim_output.outputs) == 12

    sim_output = SimulationOutput()
    sim_output.add_gains_and_losses('latent')
    assert len(sim_output.outputs) == 11

    with pytest.raises(ValueError):
        sim_output.add_gains_and_losses('convective')


def test_simulation_output_add_comfort_metrics():
    """Test the SimulationOutput add_comfort_metrics methods."""
    sim_output = SimulationOutput()
    sim_output.add_comfort_metrics()
    assert len(sim_output.outputs) == 4


def test_simulation_output_add_stratification_variables():
    """Test the SimulationOutput add_stratification_variables methods."""
    sim_output = SimulationOutput()
    sim_output.add_stratification_variables()
    assert len(sim_output.outputs) == 6


def test_simulation_output_add_surface_temperature():
    """Test the SimulationOutput add_surface_temperature methods."""
    sim_output = SimulationOutput()
    sim_output.add_surface_temperature()
    assert len(sim_output.outputs) == 2


def test_simulation_output_add_surface_energy_flow():
    """Test the SimulationOutput add_surface_temperature methods."""
    sim_output = SimulationOutput()
    sim_output.add_surface_energy_flow()
    assert len(sim_output.outputs) == 3


def test_simulation_output_add_glazing_solar():
    """Test the SimulationOutput add_glazing_solar methods."""
    sim_output = SimulationOutput()
    sim_output.add_glazing_solar()
    assert len(sim_output.outputs) == 3


def test_simulation_output_add_energy_balance_variables():
    """Test the SimulationOutput add_energy_balance_variables methods."""
    sim_output = SimulationOutput()
    sim_output.add_energy_balance_variables()
    assert len(sim_output.outputs) == 23


def test_simulation_output_add_comfort_map_variables():
    """Test the SimulationOutput add_comfort_map_variables methods."""
    sim_output = SimulationOutput()
    sim_output.add_comfort_map_variables(True)
    assert len(sim_output.outputs) == 10

    sim_output = SimulationOutput()
    sim_output.add_comfort_map_variables(False)
    assert len(sim_output.outputs) == 4


def test_simulation_output_equality():
    """Test the equality of SimulationOutput objects."""
    sim_output = SimulationOutput()
    sim_output_dup = sim_output.duplicate()
    sim_output_alt = SimulationOutput(
        outputs=['Zone Ideal Loads Supply Air Total Cooling Energy'])

    assert sim_output is sim_output
    assert sim_output is not sim_output_dup
    assert sim_output == sim_output_dup
    sim_output_dup.include_sqlite = False
    assert sim_output != sim_output_dup
    assert sim_output != sim_output_alt


def test_simulation_output_init_from_idf():
    """Test the initialization of SimulationOutput from_idf."""
    sim_output = SimulationOutput(
        outputs=['Zone Ideal Loads Supply Air Total Cooling Energy'])

    table_style, output_variables, summary_reports, sqlite, rdd, surfaces_list = \
        sim_output.to_idf()
    rebuilt_sim_output = SimulationOutput.from_idf(table_style, output_variables,
                                                   summary_reports, True)
    assert sim_output == rebuilt_sim_output
    assert rebuilt_sim_output.to_idf() == (table_style, output_variables,
                                           summary_reports, sqlite, rdd, surfaces_list)


def test_simulation_output_dict_methods():
    """Test the to/from dict methods."""
    sim_output = SimulationOutput(
        outputs=['Zone Ideal Loads Supply Air Total Cooling Energy'])

    output_dict = sim_output.to_dict()
    new_sim_output = SimulationOutput.from_dict(output_dict)
    assert new_sim_output == sim_output
    assert output_dict == new_sim_output.to_dict()


def test_simulation_output_from_dict():
    """Test for a bug in from_dict that Mingbo found."""
    out_dict = {
        "type": "SimulationOutput",     
        "reporting_frequency": "Hourly",
        "include_sqlite": True,
        "include_html": True
    }

    defalt_out = SimulationOutput.from_dict(out_dict)
    default_dict = defalt_out.to_dict()
    assert tuple(default_dict['summary_reports']) == ('AllSummary',)
