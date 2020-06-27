"""Establish the default materials within the honeybee_energy library."""
from honeybee_energy.material.dictutil import dict_to_material

from ._loadconstructions import _opaque_materials, _window_materials
from ._loadmaterials import _opaque_mat_standards_dict, _window_mat_standards_dict


# establish variables for the default materials used across the library
brick = _opaque_materials['Generic Brick']
concrete_lw = _opaque_materials['Generic LW Concrete']
concrete_hw = _opaque_materials['Generic HW Concrete']
insulation = _opaque_materials['Generic 50mm Insulation']
insulation_thin = _opaque_materials['Generic 25mm Insulation']
gypsum = _opaque_materials['Generic Gypsum Board']
acoustic_tile = _opaque_materials['Generic Acoustic Tile']
painted_metal = _opaque_materials['Generic Painted Metal']
roof_membrane = _opaque_materials['Generic Roof Membrane']
wood = _opaque_materials['Generic 25mm Wood']
wall_gap = _opaque_materials['Generic Wall Air Gap']
ceiling_gap = _opaque_materials['Generic Ceiling Air Gap']
clear_glass = _window_materials['Generic Clear Glass']
lowe_glass = _window_materials['Generic Low-e Glass']
air_gap = _window_materials['Generic Window Air Gap']
argon_gap = _window_materials['Generic Window Argon Gap']


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
