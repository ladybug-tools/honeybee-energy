# coding=utf-8
"""Utilities to convert load dictionaries to Python objects."""
from honeybee_energy.load.people import People
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.load.equipment import ElectricEquipment, GasEquipment
from honeybee_energy.load.infiltration import Infiltration
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.load.setpoint import Setpoint


LOAD_TYPES = ('People', 'Lighting', 'ElectricEquipment', 'GasEquipment',
              'Infiltration', 'Ventilation', 'Setpoint')


def dict_to_load(load_dict, raise_exception=True):
    """Get a Python object of any Load from a dictionary.

    Args:
        load_dict: A dictionary of any Honeybee energy load. Note
            that this should be a non-abridged dictionary to be valid.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a load. Default: True.

    Returns:
        A Python object derived from the input load_dict.
    """
    try:  # get the type key from the dictionary
        load_type = load_dict['type']
    except KeyError:
        raise ValueError('Load dictionary lacks required "type" key.')

    if load_type == 'People':
        return People.from_dict(load_dict)
    elif load_type == 'Lighting':
        return Lighting.from_dict(load_dict)
    elif load_type == 'ElectricEquipment':
        return ElectricEquipment.from_dict(load_dict)
    elif load_type == 'GasEquipment':
        return GasEquipment.from_dict(load_dict)
    elif load_type == 'Infiltration':
        return Infiltration.from_dict(load_dict)
    elif load_type == 'Ventilation':
        return Ventilation.from_dict(load_dict)
    elif load_type == 'Setpoint':
        return Setpoint.from_dict(load_dict)
    elif raise_exception:
        raise ValueError('{} is not a recognized energy Load type'.format(load_type))
