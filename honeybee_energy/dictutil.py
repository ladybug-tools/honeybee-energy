# coding=utf-8
"""Utilities to convertint any dictionary to Python objects.

Note that importing this module will import almost all modules within the
library in order to be able to re-serialize almost any dictionary produced
from the library.
"""
from honeybee_energy.programtype import ProgramType
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.material.dictutil import dict_to_material, MATERIAL_TYPES
from honeybee_energy.construction.dictutil import dict_to_construction, CONSTRUCTION_TYPES
from honeybee_energy.schedule.dictutil import dict_to_schedule, SCHEDULE_TYPES
from honeybee_energy.load.dictutil import dict_to_load, LOAD_TYPES
from honeybee_energy.simulation.dictutil import dict_to_simulation, SIMULATION_TYPES


def dict_to_object(honeybee_energy_dict, raise_exception=True):
    """Re-serialize a dictionary of almost any object within honeybee_energy.

    This includes any Material, Construction, ConstructionSet, Schedule, Load,
    ProgramType, or Simulation object.

    Args:
        honeybee_energy_dict: A dictionary of any Honeybee energy object. Note
            that this should be a non-abridged dictionary to be valid.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a part of honeybee_energy.
            Default: True.

    Returns:
        A Python object derived from the input honeybee_energy_dict.
    """
    try:  # get the type key from the dictionary
        obj_type = honeybee_energy_dict['type']
    except KeyError:
        raise ValueError('Honeybee_energy dictionary lacks required "type" key.')

    if obj_type == 'ProgramType':
        return ProgramType.from_dict(honeybee_energy_dict)
    elif obj_type == 'ConstructionSet':
        return ConstructionSet.from_dict(honeybee_energy_dict)
    elif obj_type in SCHEDULE_TYPES:
        return dict_to_schedule(honeybee_energy_dict)
    elif obj_type in CONSTRUCTION_TYPES:
        return dict_to_construction(honeybee_energy_dict)
    elif obj_type in MATERIAL_TYPES:
        return dict_to_material(honeybee_energy_dict)
    elif obj_type in LOAD_TYPES:
        return dict_to_load(honeybee_energy_dict)
    elif obj_type in SIMULATION_TYPES:
        return dict_to_simulation(honeybee_energy_dict)
    elif raise_exception:
        raise ValueError('{} is not a recognized honeybee energy object'.format(obj_type))
