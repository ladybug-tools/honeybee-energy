"""Establish the defauly materials within the honeybee_energy library."""
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas

from ._loadconstructions import _idf_opaque_materials, _idf_window_materials


# auto-generate materials and constructions if they were not loaded
# generic opaque materials
if 'Generic Brick' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Brick'] = EnergyMaterial(
        'Generic Brick', 0.1, 0.9, 1920, 790, 'MediumRough', 0.9, 0.65, 0.65)
    _idf_opaque_materials['Generic Brick'].lock()
if 'Generic LW Concrete' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic LW Concrete'] = EnergyMaterial(
        'Generic LW Concrete', 0.1, 0.53, 1280, 840, 'MediumRough', 0.9, 0.8, 0.8)
    _idf_opaque_materials['Generic LW Concrete'].lock()
if 'Generic HW Concrete' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic HW Concrete'] = EnergyMaterial(
        'Generic HW Concrete', 0.2, 1.95, 2240, 900, 'MediumRough', 0.9, 0.8, 0.8)
    _idf_opaque_materials['Generic HW Concrete'].lock()
if 'Generic 50mm Insulation' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic 50mm Insulation'] = EnergyMaterial(
        'Generic 50mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
    _idf_opaque_materials['Generic 50mm Insulation'].lock()
if 'Generic 25mm Insulation' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic 25mm Insulation'] = EnergyMaterial(
        'Generic 25mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
    _idf_opaque_materials['Generic 25mm Insulation'].lock()
if 'Generic Gypsum Board' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Gypsum Board'] = EnergyMaterial(
        'Generic Gypsum Board', 0.0127, 0.16, 800, 1090, 'MediumSmooth', 0.9, 0.5, 0.5)
    _idf_opaque_materials['Generic Gypsum Board'].lock()
if 'Generic Acoustic Tile' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Acoustic Tile'] = EnergyMaterial(
        'Generic Acoustic Tile', 0.02, 0.06, 368, 590, 'MediumSmooth', 0.9, 0.2, 0.2)
    _idf_opaque_materials['Generic Acoustic Tile'].lock()
if 'Generic Painted Metal' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Painted Metal'] = EnergyMaterial(
        'Generic Painted Metal', 0.0015, 45, 7690, 410, 'Smooth', 0.9, 0.5, 0.5)
    _idf_opaque_materials['Generic Painted Metal'].lock()
if 'Generic Roof Membrane' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Roof Membrane'] = EnergyMaterial(
        'Generic Roof Membrane', 0.01, 0.16, 1120, 1460, 'MediumRough', 0.9, 0.65, 0.65)
    _idf_opaque_materials['Generic Roof Membrane'].lock()
if 'Generic 25mm Wood' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic 25mm Wood'] = EnergyMaterial(
        'Generic 25mm Wood', 0.0254, 0.15, 608, 1630, 'MediumSmooth', 0.9, 0.5, 0.5)
    _idf_opaque_materials['Generic 25mm Wood'].lock()

# generic opqaue air gap materials
if 'Generic Wall Air Gap' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Wall Air Gap'] = EnergyMaterial(
        'Generic Wall Air Gap', 0.1, 0.667, 1.28, 1000, 'Smooth')
    _idf_opaque_materials['Generic Wall Air Gap'].lock()
if 'Generic Ceiling Air Gap' not in _idf_opaque_materials:
    _idf_opaque_materials['Generic Ceiling Air Gap'] = EnergyMaterial(
        'Generic Ceiling Air Gap', 0.1, 0.556, 1.28, 1000, 'Smooth')
    _idf_opaque_materials['Generic Ceiling Air Gap'].lock()
if 'Air Wall Material' not in _idf_opaque_materials:
    _idf_opaque_materials['Air Wall Material'] = EnergyMaterial(
        'Air Wall Material', 0.01, 0.6, 1.28, 1004, 'Smooth', 0.95, 0.95, 0.95)
    _idf_opaque_materials['Air Wall Material'].lock()

# generic glazing materials
if 'Generic Clear Glass' not in _idf_window_materials:
    _idf_window_materials['Generic Clear Glass'] = EnergyWindowMaterialGlazing(
        'Generic Clear Glass', 0.006, 0.77, 0.07, 0.88, 0.08, 0, 0.84, 0.84, 1.0)
    _idf_window_materials['Generic Clear Glass'].lock()
if 'Generic Low-e Glass' not in _idf_window_materials:
    _idf_window_materials['Generic Low-e Glass'] = EnergyWindowMaterialGlazing(
        'Generic Low-e Glass', 0.006, 0.45, 0.36, 0.71, 0.21, 0, 0.84, 0.047, 1.0)
    _idf_window_materials['Generic Low-e Glass'].lock()

# generic window air gap materials
if 'Generic Window Air Gap' not in _idf_window_materials:
    _idf_window_materials['Generic Window Air Gap'] = EnergyWindowMaterialGas(
        'Generic Window Air Gap', 0.0127, 'Air')
    _idf_window_materials['Generic Window Air Gap'].lock()
if 'Generic Window Argon Gap' not in _idf_window_materials:
    _idf_window_materials['Generic Window Argon Gap'] = EnergyWindowMaterialGas(
        'Generic Window Argon Gap', 0.0127, 'Argon')
    _idf_window_materials['Generic Window Argon Gap'].lock()

# establish the default materials used across the library
brick = _idf_opaque_materials['Generic Brick']
concrete_lw = _idf_opaque_materials['Generic LW Concrete']
concrete_hw = _idf_opaque_materials['Generic HW Concrete']
insulation = _idf_opaque_materials['Generic 50mm Insulation']
insulation_thin = _idf_opaque_materials['Generic 25mm Insulation']
gypsum = _idf_opaque_materials['Generic Gypsum Board']
acoustic_tile = _idf_opaque_materials['Generic Acoustic Tile']
painted_metal = _idf_opaque_materials['Generic Painted Metal']
roof_membrane = _idf_opaque_materials['Generic Roof Membrane']
wood = _idf_opaque_materials['Generic 25mm Wood']
wall_gap = _idf_opaque_materials['Generic Wall Air Gap']
ceiling_gap = _idf_opaque_materials['Generic Ceiling Air Gap']
air = _idf_opaque_materials['Air Wall Material']
clear_glass = _idf_window_materials['Generic Clear Glass']
lowe_glass = _idf_window_materials['Generic Low-e Glass']
air_gap = _idf_window_materials['Generic Window Air Gap']
argon_gap = _idf_window_materials['Generic Window Argon Gap']

# make lists of construction and material names to look up items in the library
OPAQUE_MATERIALS = tuple(_idf_opaque_materials.keys())
WINDOW_MATERIALS = tuple(_idf_window_materials.keys())


# methods to look up materials from the library


def opaque_material_by_name(material_name):
    """Get an opaque material from the library given the material name.

    Args:
        material_name: A text string for the name of the material.
    """
    try:
        return _idf_opaque_materials[material_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the opaque energy material library.'.format(
                material_name))


def window_material_by_name(material_name):
    """Get an window material from the library given the material name.

    Args:
        material_name: A text string for the name of the material.
    """
    try:
        return _idf_window_materials[material_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the window energy material library.'.format(
                material_name))
