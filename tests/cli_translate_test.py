"""Test cli translate module."""
from click.testing import CliRunner
import os
import json

from ladybug.analysisperiod import AnalysisPeriod
from honeybee.model import Model

from honeybee_energy.cli.translate import model_to_osm_cli, model_to_idf_cli, \
    model_to_gbxml_cli, model_to_trace_gbxml_cli, model_to_sdd_cli, \
    model_from_gbxml_cli, model_from_osm_cli, model_from_idf_cli, \
    construction_from_idf, construction_to_idf, schedule_to_idf, schedule_from_idf, \
    model_occ_schedules, model_trans_schedules, \
    materials_from_osm, constructions_from_osm, construction_sets_from_osm, \
    schedule_type_limits_from_osm, schedules_from_osm, programs_from_osm


def test_model_to_osm():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'
    output_osm = './tests/json/ShoeBox.osm'
    output_idf = './tests/json/ShoeBox.idf'

    in_args = [input_hb_model, '--geometry-names',
               '--osm-file', output_osm, '--idf-file', output_idf]
    result = runner.invoke(model_to_osm_cli, in_args)
    assert result.exit_code == 0

    assert os.path.isfile(output_osm)
    assert os.path.isfile(output_idf)
    os.remove(output_osm)
    os.remove(output_idf)


def test_model_to_idf():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(model_to_idf_cli, [input_hb_model])
    assert result.exit_code == 0

    output_hb_model = './tests/json/ShoeBox.idf'
    result = runner.invoke(
        model_to_idf_cli, [input_hb_model, '--output-file', output_hb_model])
    assert result.exit_code == 0
    assert os.path.isfile(output_hb_model)
    os.remove(output_hb_model)


def test_model_to_gbxml():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    in_args = [input_hb_model, '--reset-geometry-ids', '--reset-resource-ids',
               '--program-name', 'Ladybug Tools', '--program-version', '1.9',
               '--gbxml-schema-version', '5.00']
    result = runner.invoke(model_to_gbxml_cli, in_args)
    assert result.exit_code == 0


def test_model_to_trace_gbxml():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    in_args = [input_hb_model, '--program-name', 'Ladybug Tools',
               '--program-version', '1.9']
    result = runner.invoke(model_to_trace_gbxml_cli, in_args)
    assert result.exit_code == 0


def test_model_to_sdd():
    runner = CliRunner()
    input_hb_model = './tests/json/ShoeBox.json'

    result = runner.invoke(model_to_sdd_cli, [input_hb_model])
    assert result.exit_code == 0


def test_model_from_gbxml():
    runner = CliRunner()
    input_gbxml_model = os.path.abspath('./tests/gbxml/SampleGBXMLfromRevit.xml')

    result = runner.invoke(model_from_gbxml_cli, [input_gbxml_model])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    model = Model.from_dict(result_dict)
    assert isinstance(model, Model)


def test_model_from_osm():
    runner = CliRunner()
    input_osm_model = os.path.abspath('./tests/osm/shoe_box.osm')

    result = runner.invoke(model_from_osm_cli, [input_osm_model])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    model = Model.from_dict(result_dict)
    assert isinstance(model, Model)


def test_model_from_idf():
    runner = CliRunner()
    input_idf_model = os.path.abspath('./tests/idf/test_shoe_box.idf')

    result = runner.invoke(model_from_idf_cli, [input_idf_model])
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


def test_materials_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(materials_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) > 40


def test_constructions_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(constructions_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) > 30


def test_construction_sets_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(construction_sets_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) == 2


def test_schedule_type_limits_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(schedule_type_limits_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) > 10


def test_schedules_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(schedules_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) > 100


def test_programs_from_osm():
    runner = CliRunner()
    input_osm_file = './tests/osm/MidriseApartment-90.1-2019_CZ5.osm'

    result = runner.invoke(programs_from_osm, [input_osm_file])
    assert result.exit_code == 0
    result_dict = json.loads(result.output)
    assert len(result_dict) == 20


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


def test_model_trans_schedules():
    runner = CliRunner()
    input_model = './tests/json/shade_trans_model.hbjson'

    result = runner.invoke(model_trans_schedules, [input_model])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert len(sch_dict) == 1
    assert len(list(sch_dict.values())[0]) == 8760

    a_per = AnalysisPeriod(6, 21, 8, 9, 21, 16)
    result = runner.invoke(model_trans_schedules, [input_model, '--period', str(a_per)])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert len(sch_dict) == 1
    assert len(list(sch_dict.values())[0]) == len(a_per)
