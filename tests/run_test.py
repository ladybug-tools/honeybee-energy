# coding=utf-8
from honeybee_energy.run import measure_compatible_model_json

from honeybee.model import Model
from honeybee.room import Room

import os
import json
import pytest


def test_measure_compatible_model_json():
    """Test measure_compatible_model_json."""
    room = Room.from_box('Tiny House Zone', 120, 240, 96)
    inches_conversion = Model.conversion_factor_to_meters('Inches')

    model = Model('Tiny House', [room], units='Inches')
    model_json_path = './tests/simulation/model_inches.json'
    with open(model_json_path, 'w') as fp:
        json.dump(model.to_dict(included_prop=['energy']), fp)

    osm_model_json = measure_compatible_model_json(model_json_path)
    assert os.path.isfile(osm_model_json)

    with open(osm_model_json) as json_file:
        data = json.load(json_file)
    
    parsed_model = Model.from_dict(data)

    assert parsed_model.rooms[0].floor_area == \
        pytest.approx(120 * 240 * (inches_conversion ** 2), rel=1e-3)
    assert parsed_model.rooms[0].volume == \
        pytest.approx(120 * 240 * 96 * (inches_conversion ** 3), rel=1e-3)
    assert parsed_model.units == 'Meters'

    os.remove(model_json_path)
    os.remove(osm_model_json)
