# coding=utf-8
import json

from honeybee.model import Model

from honeybee_energy.hvac.detailed import DetailedHVAC


def test_detailed_hvac_init():
    """Test the initialization of DetailedHVAC and basic properties."""
    ptac_hvac_file = './tests/ironbug/ironbug_ptac_hvac.json'
    with open(ptac_hvac_file, 'r') as fp:
        ptac_spec = json.load(fp)
    hvac_sys = DetailedHVAC('Test PTAC System', ptac_spec)
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test PTAC System'
    assert hvac_sys.air_loop_count == 0
    assert len(hvac_sys.thermal_zones) == 7

    vav_hvac_file = './tests/ironbug/ironbug_vav_hvac.json'
    with open(vav_hvac_file, 'r') as fp:
        vav_spec = json.load(fp)
    hvac_sys = DetailedHVAC('Test VAV System', vav_spec)

    assert hvac_sys.identifier == 'Test VAV System'
    assert hvac_sys.air_loop_count == 1


def test_apply_detailed_hvac():
    """Test the application of DetailedHVAC to honeybee Rooms."""
    model_file = './tests/ironbug/model.hbjson'
    test_model = Model.from_hbjson(model_file)

    ptac_hvac_file = './tests/ironbug/ironbug_ptac_hvac.json'
    with open(ptac_hvac_file, 'r') as fp:
        ptac_spec = json.load(fp)
    hvac_sys = DetailedHVAC('Test PTAC System', ptac_spec)
    for room in test_model.rooms:
        room.properties.energy.hvac = hvac_sys

    model_hvacs = test_model.properties.energy.hvacs
    assert len(model_hvacs) == 1
    assert isinstance(model_hvacs[0], DetailedHVAC)
    assert model_hvacs[0].identifier == 'Test PTAC System'
    assert test_model.properties.energy.check_detailed_hvac_rooms() == ''

    model_dict = test_model.to_dict()
    new_model = Model.from_dict(model_dict)
    model_hvacs = new_model.properties.energy.hvacs
    assert len(model_hvacs) == 1
    assert isinstance(model_hvacs[0], DetailedHVAC)
    assert model_hvacs[0].identifier == 'Test PTAC System'
    assert new_model.properties.energy.check_detailed_hvac_rooms() == ''

    test_model.rooms[0].identifier = 'Changed_Room'
    assert test_model.properties.energy.check_detailed_hvac_rooms(False) != ''


def test_detailed_hvac_equality():
    """Test the equality of DetailedHVAC objects."""
    vav_hvac_file = './tests/ironbug/ironbug_vav_hvac.json'
    with open(vav_hvac_file, 'r') as fp:
        vav_spec = json.load(fp)
    hvac_sys = DetailedHVAC('Test VAV System', vav_spec)
    hvac_sys_dup = hvac_sys.duplicate()

    ptac_hvac_file = './tests/ironbug/ironbug_ptac_hvac.json'
    with open(ptac_hvac_file, 'r') as fp:
        ptac_spec = json.load(fp)
    hvac_sys_alt = DetailedHVAC('Test PTAC System', ptac_spec)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.identifier = 'Alternate VAV System'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_detailed_hvac_dict_methods():
    """Test the to/from dict methods."""
    vav_hvac_file = './tests/ironbug/ironbug_vav_hvac.json'
    with open(vav_hvac_file, 'r') as fp:
        vav_spec = json.load(fp)
    hvac_sys = DetailedHVAC('Test VAV System', vav_spec)

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = DetailedHVAC.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()
