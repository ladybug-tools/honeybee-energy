# coding=utf-8
"""Utilities to convert construction dictionaries to Python objects."""
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction


CONSTRUCTION_TYPES = \
    ('OpaqueConstruction', 'WindowConstruction', 'WindowConstructionShade',
     'ShadeConstruction', 'AirBoundaryConstruction')


def dict_to_construction(constr_dict, raise_exception=True):
    """Get a Python object of any Construction from a dictionary.

    Args:
        constr_dict: A dictionary of any Honeybee energy construction. Note
            that this should be a non-abridged dictionary to be valid.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a construction. Default: True.

    Returns:
        A Python object derived from the input constr_dict.
    """
    try:  # get the type key from the dictionary
        constr_type = constr_dict['type']
    except KeyError:
        raise ValueError('Construction dictionary lacks required "type" key.')

    if constr_type == 'OpaqueConstruction':
        return OpaqueConstruction.from_dict(constr_dict)
    elif constr_type == 'WindowConstruction':
        return WindowConstruction.from_dict(constr_dict)
    elif constr_type == 'WindowConstructionShade':
        return WindowConstructionShade.from_dict(constr_dict)
    elif constr_type == 'ShadeConstruction':
        return ShadeConstruction.from_dict(constr_dict)
    elif constr_type == 'AirBoundaryConstruction':
        return AirBoundaryConstruction.from_dict(constr_dict)
    elif raise_exception:
        raise ValueError(
            '{} is not a recognized energy Construction type'.format(constr_type))


def dict_abridged_to_construction(constr_dict, materials, schedules,
                                  raise_exception=True):
    """Get a Python object of any Construction from an abridged dictionary.

    Args:
        constr_dict: An abridged dictionary of any Honeybee energy construction.
        materials: Dictionary of all material objects that might be used in the
            construction with the material identifiers as the keys.
        schedules: Dictionary of all schedule objects that might be used in the
            construction with the schedule identifiers as the keys.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a construction. Default: True.

    Returns:
        A Python object derived from the input constr_dict.
    """
    try:  # get the type key from the dictionary
        constr_type = constr_dict['type']
    except KeyError:
        raise ValueError('Construction dictionary lacks required "type" key.')

    if constr_type == 'OpaqueConstructionAbridged':
        return OpaqueConstruction.from_dict_abridged(constr_dict, materials)
    elif constr_type == 'WindowConstructionAbridged':
        return WindowConstruction.from_dict_abridged(constr_dict, materials)
    elif constr_type == 'WindowConstructionShade':
        return WindowConstructionShade.from_dict_abridged(
            constr_dict, materials, schedules)
    elif constr_type == 'ShadeConstruction':
        return ShadeConstruction.from_dict(constr_dict)
    elif constr_type == 'AirBoundaryConstructionAbridged':
        return AirBoundaryConstruction.from_dict_abridged(constr_dict, schedules)
    elif constr_type == 'AirBoundaryConstruction':  # special case for ConstructionSet
        return AirBoundaryConstruction.from_dict(constr_dict)
    elif raise_exception:
        raise ValueError(
            '{} is not a recognized energy Construction type'.format(constr_type))
