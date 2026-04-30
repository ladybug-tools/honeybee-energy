"""Test cli lib module."""
from click.testing import CliRunner
from honeybee_energy.cli.lib import opaque_materials_cli, window_materials_cli, \
    opaque_constructions_cli, window_constructions_cli, shade_constructions_cli, \
    construction_sets_cli, schedule_type_limits_cli, schedules_cli, program_types_cli, \
    opaque_material_by_id_cli, window_material_by_id_cli, opaque_construction_by_id_cli, \
    window_construction_by_id_cli, shade_construction_by_id_cli, construction_set_by_id_cli, \
    schedule_type_limit_by_id_cli, schedule_by_id_cli, program_type_by_id_cli, \
    materials_by_id_cli, constructions_by_id_cli, construction_sets_by_id_cli, \
    schedule_type_limits_by_id_cli, schedules_by_id_cli, program_types_by_id_cli, \
    purge_lib, add_to_lib

from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.programtype import ProgramType

import json


def test_lib_constructions():
    """Test the existence of construction objects in the library."""
    runner = CliRunner()

    result = runner.invoke(opaque_materials_cli)
    assert result.exit_code == 0

    result = runner.invoke(window_materials_cli)
    assert result.exit_code == 0

    result = runner.invoke(opaque_constructions_cli)
    assert result.exit_code == 0

    result = runner.invoke(window_constructions_cli)
    assert result.exit_code == 0

    result = runner.invoke(shade_constructions_cli)
    assert result.exit_code == 0

    result = runner.invoke(construction_sets_cli)
    assert result.exit_code == 0


def test_lib_schedules():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limits_cli)
    assert result.exit_code == 0

    result = runner.invoke(schedules_cli)
    assert result.exit_code == 0

    result = runner.invoke(program_types_cli)
    assert result.exit_code == 0


def test_construction_from_lib():
    """Test the existence of construction objects in the library."""
    runner = CliRunner()

    result = runner.invoke(opaque_material_by_id_cli, ['Generic Gypsum Board'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyMaterial.from_dict(mat_dict), EnergyMaterial)

    result = runner.invoke(window_material_by_id_cli, ['Generic Low-e Glass'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyWindowMaterialGlazing.from_dict(mat_dict),
                      EnergyWindowMaterialGlazing)

    result = runner.invoke(opaque_construction_by_id_cli, ['Generic Exterior Wall'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(OpaqueConstruction.from_dict(con_dict), OpaqueConstruction)

    result = runner.invoke(window_construction_by_id_cli, ['Generic Double Pane'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(WindowConstruction.from_dict(con_dict), WindowConstruction)

    result = runner.invoke(shade_construction_by_id_cli, ['Generic Context'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(ShadeConstruction.from_dict(mat_dict), ShadeConstruction)

    result = runner.invoke(construction_set_by_id_cli, ['Default Generic Construction Set'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(ConstructionSet.from_dict(con_dict), ConstructionSet)


def test_schedule_from_lib():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limit_by_id_cli, ['Fractional'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleTypeLimit.from_dict(sch_dict), ScheduleTypeLimit)

    result = runner.invoke(schedule_by_id_cli, ['Generic Office Occupancy'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleRuleset.from_dict(sch_dict), ScheduleRuleset)

    result = runner.invoke(program_type_by_id_cli, ['Generic Office Program'])
    assert result.exit_code == 0
    prog_dict = json.loads(result.output)
    assert isinstance(ProgramType.from_dict(prog_dict), ProgramType)


def test_constructions_from_lib():
    """Test the existence of construction objects in the library."""
    runner = CliRunner()

    result = runner.invoke(
        materials_by_id_cli, ['Generic Gypsum Board', 'Generic Low-e Glass'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyMaterial.from_dict(mat_dict[0]), EnergyMaterial)

    result = runner.invoke(
        constructions_by_id_cli,
        ['Generic Exterior Wall', 'Generic Double Pane', 'Generic Context'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(OpaqueConstruction.from_dict(con_dict[0]), OpaqueConstruction)

    result = runner.invoke(construction_sets_by_id_cli, ['Default Generic Construction Set'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(ConstructionSet.from_dict(con_dict[0]), ConstructionSet)


def test_schedules_from_lib():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limits_by_id_cli, ['Fractional', 'Temperature'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleTypeLimit.from_dict(sch_dict[0]), ScheduleTypeLimit)

    result = runner.invoke(
        schedules_by_id_cli, ['Generic Office Occupancy', 'Generic Office Lighting'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleRuleset.from_dict(sch_dict[0]), ScheduleRuleset)

    result = runner.invoke(program_types_by_id_cli, ['Generic Office Program', 'Plenum'])
    assert result.exit_code == 0
    prog_dict = json.loads(result.output)
    assert isinstance(ProgramType.from_dict(prog_dict[0]), ProgramType)


def test_add_to_lib():
    """Test the add_to_lib command."""
    runner = CliRunner()

    resource_file = './tests/json/sample_energy_properties.json'
    result = runner.invoke(add_to_lib, [resource_file])
    assert result.exit_code == 0
    assert 'AZ Construction Set' in result.output
    assert 'Program: AZ LAB program' in result.output


def test_purge_lib():
    """Test the purge_lib command."""
    runner = CliRunner()

    result = runner.invoke(purge_lib)
    assert result.exit_code == 0
