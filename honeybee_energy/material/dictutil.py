# coding=utf-8
"""Utilities to convert material dictionaries to Python objects."""
from .opaque import EnergyMaterial, EnergyMaterialNoMass
from .glazing import EnergyWindowMaterialGlazing, EnergyWindowMaterialSimpleGlazSys
from .gas import EnergyWindowMaterialGas, EnergyWindowMaterialGasMixture, \
    EnergyWindowMaterialGasCustom
from .shade import EnergyWindowMaterialShade, EnergyWindowMaterialBlind


MATERIAL_TYPES = ('EnergyMaterial', 'EnergyMaterialNoMass', 'EnergyWindowMaterialGlazing',
                  'EnergyWindowMaterialSimpleGlazSys', 'EnergyWindowMaterialGas',
                  'EnergyWindowMaterialGasMixture', 'EnergyWindowMaterialGasCustom',
                  'EnergyWindowMaterialShade', 'EnergyWindowMaterialBlind')


def dict_to_material(mat_dict, raise_exception=True):
    """Get a Python object of any Material from a dictionary.

    Args:
        mat_dict: A dictionary of any Honeybee energy material.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a material. Default: True.

    Returns:
        A Python object derived from the input mat_dict.
    """
    try:  # get the type key from the dictionary
        mat_type = mat_dict['type']
    except KeyError:
        raise ValueError('Material dictionary lacks required "type" key.')

    if mat_type == 'EnergyMaterial':
        return EnergyMaterial.from_dict(mat_dict)
    elif mat_type == 'EnergyMaterialNoMass':
        return EnergyMaterialNoMass.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialGlazing':
        return EnergyWindowMaterialGlazing.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialSimpleGlazSys':
        return EnergyWindowMaterialSimpleGlazSys.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialGas':
        return EnergyWindowMaterialGas.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialGasMixture':
        return EnergyWindowMaterialGasMixture.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialGasCustom':
        return EnergyWindowMaterialGasCustom.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialShade':
        return EnergyWindowMaterialShade.from_dict(mat_dict)
    elif mat_type == 'EnergyWindowMaterialBlind':
        return EnergyWindowMaterialBlind.from_dict(mat_dict)
    elif raise_exception:
        raise ValueError('{} is not a recognized Energy Material type'.format(mat_type))
