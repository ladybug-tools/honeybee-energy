"""Test cli lib module."""
from click.testing import CliRunner
from honeybee_energy.cli.lib import opaque_materials, window_materials, \
    opaque_constructions, window_constructions, shade_constructions, construction_sets, \
    schedule_type_limits, schedules, program_types, opaque_material_by_id, \
    window_material_by_id, opaque_construction_by_id, window_construction_by_id, \
    shade_construction_by_id, construction_set_by_id, schedule_type_limit_by_id, \
    schedule_by_id, program_type_by_id, materials_by_id, constructions_by_id, \
    construction_sets_by_id, schedule_type_limits_by_id, schedules_by_id, \
    program_types_by_id

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

    result = runner.invoke(opaque_materials)
    assert result.exit_code == 0

    result = runner.invoke(window_materials)
    assert result.exit_code == 0

    result = runner.invoke(opaque_constructions)
    assert result.exit_code == 0

    result = runner.invoke(window_constructions)
    assert result.exit_code == 0

    result = runner.invoke(shade_constructions)
    assert result.exit_code == 0

    result = runner.invoke(construction_sets)
    assert result.exit_code == 0


def test_lib_schedules():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limits)
    assert result.exit_code == 0

    result = runner.invoke(schedules)
    assert result.exit_code == 0

    result = runner.invoke(program_types)
    assert result.exit_code == 0


def test_construction_from_lib():
    """Test the existence of construction objects in the library."""
    runner = CliRunner()

    result = runner.invoke(opaque_material_by_id, ['Generic Gypsum Board'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyMaterial.from_dict(mat_dict), EnergyMaterial)

    result = runner.invoke(window_material_by_id, ['Generic Low-e Glass'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyWindowMaterialGlazing.from_dict(mat_dict),
                      EnergyWindowMaterialGlazing)

    result = runner.invoke(opaque_construction_by_id, ['Generic Exterior Wall'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(OpaqueConstruction.from_dict(con_dict), OpaqueConstruction)

    result = runner.invoke(window_construction_by_id, ['Generic Double Pane'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(WindowConstruction.from_dict(con_dict), WindowConstruction)

    result = runner.invoke(shade_construction_by_id, ['Generic Context'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(ShadeConstruction.from_dict(mat_dict), ShadeConstruction)

    result = runner.invoke(construction_set_by_id, ['Default Generic Construction Set'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(ConstructionSet.from_dict(con_dict), ConstructionSet)


def test_schedule_from_lib():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limit_by_id, ['Fractional'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleTypeLimit.from_dict(sch_dict), ScheduleTypeLimit)

    result = runner.invoke(schedule_by_id, ['Generic Office Occupancy'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleRuleset.from_dict(sch_dict), ScheduleRuleset)

    result = runner.invoke(program_type_by_id, ['Generic Office Program'])
    assert result.exit_code == 0
    prog_dict = json.loads(result.output)
    assert isinstance(ProgramType.from_dict(prog_dict), ProgramType)


def test_constructions_from_lib():
    """Test the existence of construction objects in the library."""
    runner = CliRunner()

    result = runner.invoke(
        materials_by_id, ['Generic Gypsum Board', 'Generic Low-e Glass'])
    assert result.exit_code == 0
    mat_dict = json.loads(result.output)
    assert isinstance(EnergyMaterial.from_dict(mat_dict[0]), EnergyMaterial)

    result = runner.invoke(
        constructions_by_id,
        ['Generic Exterior Wall', 'Generic Double Pane', 'Generic Context'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(OpaqueConstruction.from_dict(con_dict[0]), OpaqueConstruction)

    result = runner.invoke(construction_sets_by_id, ['Default Generic Construction Set'])
    assert result.exit_code == 0
    con_dict = json.loads(result.output)
    assert isinstance(ConstructionSet.from_dict(con_dict[0]), ConstructionSet)


def test_schedules_from_lib():
    """Test the existence of schedule objects in the library."""
    runner = CliRunner()

    result = runner.invoke(schedule_type_limits_by_id, ['Fractional', 'Temperature'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleTypeLimit.from_dict(sch_dict[0]), ScheduleTypeLimit)

    result = runner.invoke(
        schedules_by_id, ['Generic Office Occupancy', 'Generic Office Lighting'])
    assert result.exit_code == 0
    sch_dict = json.loads(result.output)
    assert isinstance(ScheduleRuleset.from_dict(sch_dict[0]), ScheduleRuleset)

    result = runner.invoke(program_types_by_id, ['Generic Office Program', 'Plenum'])
    assert result.exit_code == 0
    prog_dict = json.loads(result.output)
    assert isinstance(ProgramType.from_dict(prog_dict[0]), ProgramType)
