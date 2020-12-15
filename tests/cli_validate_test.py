"""Test the validate group."""
import sys

from click.testing import CliRunner
from honeybee_energy.cli.validate import validate_model_properties, validate_sim_par, \
    validate_program_type, validate_schedule, validate_schedule_type_limit, \
    validate_construction_set


def test_validate_model_properties():
    input_json = './tests/json/model_5vertex_sub_faces_interior.hbjson'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_model_properties, [input_json])
        assert result.exit_code == 0


def test_validate_model_basic():
    input_sim_par = './tests/json/simulation_par_detailed.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_sim_par, [input_sim_par])
        assert result.exit_code == 0


def test_validate_program_type():
    input_json = './tests/json/program_type_office.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_program_type, [input_json])
        assert result.exit_code == 0


def test_validate_schedule():
    input_json = './tests/json/schedule_ruleset_office_occupancy.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_schedule, [input_json])
        assert result.exit_code == 0


def test_validate_schedule_type_limit():
    input_json = './tests/json/scheduletypelimit_temperature.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_schedule_type_limit, [input_json])
        assert result.exit_code == 0


def test_validate_construction_set():
    input_json = './tests/json/constructionset_complete.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_construction_set, [input_json])
        assert result.exit_code == 0
