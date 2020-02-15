# coding=utf-8
from honeybee_energy.dictutil import dict_to_object
from honeybee_energy.programtype import ProgramType
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.load.setpoint import Setpoint
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.material.shade import EnergyWindowMaterialBlind
from honeybee_energy.construction.air import AirBoundaryConstruction

import honeybee_energy.lib.scheduletypelimits as schedule_types

import pytest


def test_dict_to_object_program_type():
    """Test the dict_to_object method with ProgramType objects."""
    program_type_obj = ProgramType('Test Program')
    program_type_dict = program_type_obj.to_dict()
    new_prog_type = dict_to_object(program_type_dict)
    assert isinstance(new_prog_type, ProgramType)


def test_dict_to_object_constr_set():
    """Test the dict_to_object method with ConstructionSet objects."""
    constr_set_obj = ConstructionSet('Test ConstructionSet')
    constr_set_dict = constr_set_obj.to_dict()
    new_constr_set = dict_to_object(constr_set_dict)
    assert isinstance(new_constr_set, ConstructionSet)


def test_dict_to_object_sim_par():
    """Test the dict_to_object method with SimulationParameter objects."""
    sim_par_obj = SimulationParameter()
    sim_par_dict = sim_par_obj.to_dict()
    new_sim_par = dict_to_object(sim_par_dict)
    assert isinstance(new_sim_par, SimulationParameter)


def test_dict_to_object_load():
    """Test the dict_to_object method with Setpoint objects."""
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling', 24, schedule_types.temperature)
    setpoint = Setpoint('Office Setpoint', heat_setpt, cool_setpt)

    setpoint_dict = setpoint.to_dict()
    new_setpoint = dict_to_object(setpoint_dict)
    assert isinstance(new_setpoint, Setpoint)


def test_dict_to_object_material():
    """Test the dict_to_object method with EnergyWindowMaterialBlind objects."""
    material_obj = EnergyWindowMaterialBlind('Test Blind')
    material_dict = material_obj.to_dict()
    new_material = dict_to_object(material_dict)
    assert isinstance(new_material, EnergyWindowMaterialBlind)


def test_dict_to_object_construction():
    """Test the dict_to_object method with AirBoundaryConstruction objects."""
    construction_obj = AirBoundaryConstruction('Test Air Wall')
    construction_dict = construction_obj.to_dict()
    new_construction = dict_to_object(construction_dict)
    assert isinstance(new_construction, AirBoundaryConstruction)


def test_dict_to_object_sch():
    """Test the dict_to_object method with ScheduleRuleset objects."""
    sch_obj = ScheduleRuleset.from_constant_value(
        'Office Heating', 21, schedule_types.temperature)
    sch_dict = sch_obj.to_dict()
    new_sch = dict_to_object(sch_dict)
    assert isinstance(new_sch, ScheduleRuleset)
