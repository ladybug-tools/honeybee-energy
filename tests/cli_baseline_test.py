"""Test cli baseline module."""
from click.testing import CliRunner
from honeybee_energy.cli.baseline import baseline_geometry, baseline_lighting, \
    baseline_hvac, remove_ecms, compute_appendix_g_summary, compute_leed_v4_summary
from honeybee_energy.hvac.allair.vav import VAV
from honeybee.model import Model

import json
import pytest


def test_baseline_geometry():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(baseline_geometry, [input_hb_model])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    w_area = new_model.exterior_wall_area
    r_area = new_model.exterior_roof_area
    wr = new_model.exterior_wall_aperture_area / w_area if w_area != 0 else 0
    sr = new_model.exterior_skylight_aperture_area / r_area if r_area != 0 else 0
    assert wr < 0.41
    assert sr < 0.06


def test_baseline_lighting():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'
    original_model = Model.from_hbjson(input_hb_model)

    result = runner.invoke(baseline_lighting, [input_hb_model])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    assert new_model.rooms[0].properties.energy.lighting.watts_per_area != \
        original_model.rooms[0].properties.energy.lighting.watts_per_area


def test_baseline_hvac():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(
        baseline_hvac, [input_hb_model, '5A', '--floor-area', '20000'])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    new_hvac = new_model.rooms[0].properties.energy.hvac
    assert isinstance(new_hvac, VAV)
    assert new_hvac.vintage == 'ASHRAE_2004'
    assert new_hvac.equipment_type == 'VAV_Chiller_Boiler'
    assert new_hvac.economizer_type == 'DifferentialDryBulb'


def test_remove_ecms():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(remove_ecms, [input_hb_model])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    assert new_model.rooms[0].properties.energy.window_vent_control is None


def test_appendix_g_summary():
    """Test the appendix_g_summary command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    sql_base_path = './tests/result/sub_folder'
    result = runner.invoke(compute_appendix_g_summary, [sql_path, sql_base_path, '5A'])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert 'baseline_cost' in result_dict
    assert 'proposed_cost' in result_dict
    assert 'pci' in result_dict
    assert 'pci_improvement_2016' in result_dict


def test_leed_v4_summary():
    """Test the leed_v4_summary command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    sql_base_path = './tests/result/sub_folder'
    result = runner.invoke(compute_leed_v4_summary, [sql_path, sql_base_path, '5A'])
    print(result.output)
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert 'baseline_cost' in result_dict
    assert 'proposed_cost' in result_dict
    assert 'baseline_carbon' in result_dict
    assert 'proposed_carbon' in result_dict
    assert 'pci_improvement' in result_dict
    assert 'carbon_improvement' in result_dict
    assert 'leed_points' in result_dict
