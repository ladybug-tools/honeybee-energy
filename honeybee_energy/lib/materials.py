"""Establish the default materials within the honeybee_energy library."""
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas
from honeybee_energy.material.dictutil import dict_to_material

from ._loadconstructions import _opaque_materials, _window_materials
from ._loadmaterials import _opaque_mat_standards_dict, _window_mat_standards_dict


# properties of all default materials; used when they are not found in default.idf
_default_prop = {
    'brick':
        ('Generic Brick', 0.1, 0.9, 1920, 790, 'MediumRough', 0.9, 0.65, 0.65),
    'concrete_lw':
        ('Generic LW Concrete', 0.1, 0.53, 1280, 840, 'MediumRough', 0.9, 0.8, 0.8),
    'concrete_hw':
        ('Generic HW Concrete', 0.2, 1.95, 2240, 900, 'MediumRough', 0.9, 0.8, 0.8),
    'insulation':
        ('Generic 50mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7),
    'insulation_thin':
        ('Generic 25mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7),
    'gypsum':
        ('Generic Gypsum Board', 0.0127, 0.16, 800, 1090, 'MediumSmooth', 0.9, 0.5, 0.5),
    'acoustic_tile':
        ('Generic Acoustic Tile', 0.02, 0.06, 368, 590, 'MediumSmooth', 0.9, 0.2, 0.2),
    'painted_metal':
        ('Generic Painted Metal', 0.0015, 45, 7690, 410, 'Smooth', 0.9, 0.5, 0.5),
    'roof_membrane':
        ('Generic Roof Membrane', 0.01, 0.16, 1120, 1460, 'MediumRough', 0.9, 0.65, 0.65),
    'wood':
        ('Generic 25mm Wood', 0.0254, 0.15, 608, 1630, 'MediumSmooth', 0.9, 0.5, 0.5),
    'wall_gap':
        ('Generic Wall Air Gap', 0.1, 0.667, 1.28, 1000, 'Smooth'),
    'ceiling_gap':
        ('Generic Ceiling Air Gap', 0.1, 0.556, 1.28, 1000, 'Smooth'),
    'clear_glass':
        ('Generic Clear Glass', 0.006, 0.77, 0.07, 0.88, 0.08, 0, 0.84, 0.84, 1.0),
    'lowe_glass':
        ('Generic Low-e Glass', 0.006, 0.45, 0.36, 0.71, 0.21, 0, 0.84, 0.047, 1.0),
    'air_gap':
        ('Generic Window Air Gap', 0.0127, 'Air'),
    'argon_gap':
        ('Generic Window Argon Gap', 0.0127, 'Argon')
}


# establish variables for the default materials used across the library
# and auto-generate materials if they were not loaded from default.idf
try:
    brick = _opaque_materials['Generic Brick']
except KeyError:
    brick = EnergyMaterial(*_default_prop['brick'])
    brick.lock()
    _opaque_materials['Generic Brick'] = brick

try:
    concrete_lw = _opaque_materials['Generic LW Concrete']
except KeyError:
    concrete_lw = EnergyMaterial(*_default_prop['concrete_lw'])
    concrete_lw.lock()
    _opaque_materials['Generic LW Concrete'] = concrete_lw

try:
    concrete_hw = _opaque_materials['Generic HW Concrete']
except KeyError:
    concrete_hw = EnergyMaterial(*_default_prop['concrete_hw'])
    concrete_hw.lock()
    _opaque_materials['Generic HW Concrete'] = concrete_hw

try:
    insulation = _opaque_materials['Generic 50mm Insulation']
except KeyError:
    insulation = EnergyMaterial(*_default_prop['insulation'])
    insulation.lock()
    _opaque_materials['Generic 50mm Insulation'] = insulation

try:
    insulation_thin = _opaque_materials['Generic 25mm Insulation']
except KeyError:
    insulation_thin = EnergyMaterial(*_default_prop['insulation_thin'])
    insulation_thin.lock()
    _opaque_materials['Generic 25mm Insulation'] = insulation_thin

try:
    gypsum = _opaque_materials['Generic Gypsum Board']
except KeyError:
    gypsum = EnergyMaterial(*_default_prop['gypsum'])
    gypsum.lock()
    _opaque_materials['Generic Gypsum Board'] = gypsum

try:
    acoustic_tile = _opaque_materials['Generic Acoustic Tile']
except KeyError:
    acoustic_tile = EnergyMaterial(*_default_prop['acoustic_tile'])
    acoustic_tile.lock()
    _opaque_materials['Generic Acoustic Tile'] = acoustic_tile

try:
    painted_metal = _opaque_materials['Generic Painted Metal']
except KeyError:
    painted_metal = EnergyMaterial(*_default_prop['painted_metal'])
    painted_metal.lock()
    _opaque_materials['Generic Painted Metal'] = painted_metal

try:
    roof_membrane = _opaque_materials['Generic Roof Membrane']
except KeyError:
    roof_membrane = EnergyMaterial(*_default_prop['roof_membrane'])
    roof_membrane.lock()
    roof_membrane = _opaque_materials['Generic Roof Membrane']

try:
    wood = _opaque_materials['Generic 25mm Wood']
except KeyError:
    wood = EnergyMaterial(*_default_prop['wood'])
    wood.lock()
    _opaque_materials['Generic 25mm Wood'] = wood

try:
    wall_gap = _opaque_materials['Generic Wall Air Gap']
except KeyError:
    wall_gap = EnergyMaterial(*_default_prop['wall_gap'])
    wall_gap.lock()
    _opaque_materials['Generic Wall Air Gap'] = wall_gap

try:
    ceiling_gap = _opaque_materials['Generic Ceiling Air Gap']
except KeyError:
    ceiling_gap = EnergyMaterial(*_default_prop['ceiling_gap'])
    ceiling_gap.lock()
    _opaque_materials['Generic Ceiling Air Gap'] = ceiling_gap

try:
    clear_glass = _window_materials['Generic Clear Glass']
except KeyError:
    clear_glass = EnergyWindowMaterialGlazing(*_default_prop['clear_glass'])
    clear_glass.lock()
    _window_materials['Generic Clear Glass'] = clear_glass

try:
    lowe_glass = _window_materials['Generic Low-e Glass']
except KeyError:
    lowe_glass = EnergyWindowMaterialGlazing(*_default_prop['lowe_glass'])
    lowe_glass.lock()
    _window_materials['Generic Low-e Glass'] = lowe_glass

try:
    air_gap = _window_materials['Generic Window Air Gap']
except KeyError:
    air_gap = EnergyWindowMaterialGas(*_default_prop['air_gap'])
    air_gap.lock()
    _window_materials['Generic Window Air Gap'] = air_gap

try:
    argon_gap = _window_materials['Generic Window Argon Gap']
except KeyError:
    argon_gap = EnergyWindowMaterialGas(*_default_prop['argon_gap'])
    argon_gap.lock()
    _window_materials['Generic Window Argon Gap'] = argon_gap


# make lists of material identifiers to look up items in the library
OPAQUE_MATERIALS = tuple(_opaque_materials.keys()) + \
    tuple(_opaque_mat_standards_dict.keys())
WINDOW_MATERIALS = tuple(_window_materials.keys()) + \
    tuple(_window_mat_standards_dict.keys())


def opaque_material_by_identifier(material_identifier):
    """Get an opaque material from the library given the material identifier.

    Args:
        material_identifier: A text string for the identifier of the material.
    """
    try:  # first check the default data
        return _opaque_materials[material_identifier]
    except KeyError:
        try:  # search the extension data
            _mat_dict = _opaque_mat_standards_dict[material_identifier]
            return dict_to_material(_mat_dict)
        except KeyError:  # material is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the opaque energy material library.'.format(
                    material_identifier))


def window_material_by_identifier(material_identifier):
    """Get an window material from the library given the material identifier.

    Args:
        material_identifier: A text string for the identifier of the material.
    """
    try:  # first check the default data
        return _window_materials[material_identifier]
    except KeyError:
        try:  # search the extension data
            _mat_dict = _window_mat_standards_dict[material_identifier]
            return dict_to_material(_mat_dict)
        except KeyError:  # material is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the window energy material library.'.format(
                    material_identifier))
