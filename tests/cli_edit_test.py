"""Test cli edit module."""
import json
from click.testing import CliRunner

from honeybee.model import Model
from honeybee_energy.cli.edit import reset_resource_ids


def test_reset_resource_ids():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    c_args = [input_hb_model, '-uuid']
    result = runner.invoke(reset_resource_ids, c_args)
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    new_con_set = new_model.properties.energy.construction_sets[0]
    old_id = '2013::ClimateZone5::SteelFramed'
    assert new_con_set.identifier.startswith(old_id)
    assert new_con_set.identifier != old_id


def test_reset_resource_ids_humidification():
    runner = CliRunner()
    input_hb_model = './tests/json/custom_resources.hbjson'

    c_args = [input_hb_model, '-uuid']
    result = runner.invoke(reset_resource_ids, c_args)
    assert result.exit_code == 0
    model_dict = json.loads(result.output)
    new_model = Model.from_dict(model_dict)
    
    assert len(new_model.properties.energy.program_types) == 9
    assert len(new_model.properties.energy.schedules) == 51
    assert len(new_model.properties.energy.construction_sets) == 1
    assert len(new_model.properties.energy.constructions) == 7
