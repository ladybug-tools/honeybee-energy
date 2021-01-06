"""Test cli baseline module."""
from click.testing import CliRunner
from honeybee_energy.cli.baseline import geometry_2004, lighting_2004, hvac_2004, \
    remove_ecms
from honeybee_energy.hvac.allair.vav import VAV
from honeybee.model import Model

import json
import pytest


def test_geometry_2004():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(geometry_2004, [input_hb_model])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    w_area = new_model.exterior_wall_area
    r_area = new_model.exterior_roof_area
    wr = new_model.exterior_wall_aperture_area / w_area if w_area != 0 else 0
    sr = new_model.exterior_skylight_aperture_area / r_area if r_area != 0 else 0
    assert wr < 0.41
    assert sr < 0.06


def test_lighting_2004():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(lighting_2004, [input_hb_model])
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    assert new_model.rooms[0].properties.energy.lighting.watts_per_area == \
        pytest.approx(11.84029, rel=1e-1)


def test_hvac_2004():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(hvac_2004, [input_hb_model, '5A', '--floor-area', '20000'])
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
