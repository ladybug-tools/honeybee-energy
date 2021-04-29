"""Test cli translate module."""
from click.testing import CliRunner
import os
import json

from ladybug.analysisperiod import AnalysisPeriod
from honeybee.model import Model

from honeybee_energy.cli.translate import model_to_idf, model_to_gbxml, \
    model_from_gbxml, model_from_osm, model_from_idf, \
    construction_from_idf, construction_to_idf, \
    schedule_to_idf, schedule_from_idf, model_occ_schedules


def test_model_to_idf():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(model_to_idf, [input_hb_model])
    assert result.exit_code == 0

    output_hb_model = './tests/json/ShoeBox.idf'
    result = runner.invoke(
        model_to_idf, [input_hb_model, '--output-file', output_hb_model])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_model)
    os.remove(output_hb_model)


def test_model_to_gbxml():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(model_to_gbxml, [input_hb_model])
    assert result.exit_code == 0

    output_hb_model = './tests/gbxml/ShoeBox.gbxml'
    result = runner.invoke(
        model_to_gbxml, [input_hb_model, '--output-file', output_hb_model])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_model)
    os.remove(output_hb_model)


def test_model_from_gbxml():
    runner = CliRunner()
    input_gbxml_model = os.path.abspath('./tests/gbxml/SampleGBXMLfromRevit.xml')

    result = runner.invoke(model_from_gbxml, [input_gbxml_model])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    model = Model.from_dict(result_dict)
    assert isinstance(model, Model)


def test_model_from_osm():
    runner = CliRunner()
    input_osm_model = os.path.abspath('./tests/osm/shoe_box.osm')

    result = runner.invoke(model_from_osm, [input_osm_model])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    model = Model.from_dict(result_dict)
    assert isinstance(model, Model)


def test_model_from_idf():
    runner = CliRunner()
    input_idf_model = os.path.abspath('./tests/idf/test_shoe_box.idf')

    result = runner.invoke(model_from_idf, [input_idf_model])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    model = Model.from_dict(result_dict)
    assert isinstance(model, Model)


def test_construction_to_from_idf():
    runner = CliRunner()
    input_hb_constr = './tests/idf/GlzSys_Triple Clear_Avg.idf'

    result = runner.invoke(construction_from_idf, [input_hb_constr])
    assert result.exit_code == 0

    output_hb_json = './tests/json/GlzSys_Triple_Clear_Avg.json'
    result = runner.invoke(
        construction_from_idf, [input_hb_constr, '--output-file', output_hb_json])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_json)

    result = runner.invoke(construction_to_idf, [output_hb_json])
    assert result.exit_code == 0

    os.remove(output_hb_json)


def test_schedule_to_from_idf():
    runner = CliRunner()
    input_hb_sch = './tests/idf/OfficeOccupancySchedule.idf'

    result = runner.invoke(schedule_from_idf, [input_hb_sch])
    assert result.exit_code == 0

    output_hb_json = './tests/json/OfficeOccupancySchedule.json'
    result = runner.invoke(
        schedule_from_idf, [input_hb_sch, '--output-file', output_hb_json])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_json)

    result = runner.invoke(schedule_to_idf, [output_hb_json])
    assert result.exit_code == 0

    os.remove(output_hb_json)


def test_model_occ_schedules():
    runner = CliRunner()
    input_model = './tests/json/ShoeBox.json'

    result = runner.invoke(model_occ_schedules, [input_model])
    assert result.exit_code == 0
    occ_dict = json.loads(result.output)
    assert len(occ_dict['schedules']) == 1
    assert len(list(occ_dict['schedules'].values())[0]) == 8760

    a_per = AnalysisPeriod(6, 21, 8, 9, 21, 16)
    result = runner.invoke(model_occ_schedules, [input_model, '--period', str(a_per)])
    assert result.exit_code == 0
    occ_dict = json.loads(result.output)
    assert len(occ_dict['schedules']) == 1
    assert len(list(occ_dict['schedules'].values())[0]) == len(a_per)
