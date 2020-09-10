"""Test cli translate module."""
from click.testing import CliRunner
from honeybee_energy.cli.baseline import geometry_2004
from honeybee.model import Model

import json


def test_model_to_idf():
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
