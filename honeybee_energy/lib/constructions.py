"""Load all of the constructions and materials from the IDF libraries."""
from honeybee_energy.construction import OpaqueConstruction, \
    WindowConstruction, ShadeConstruction
from ._loadconstructions import _idf_opaque_constructions, _idf_window_constructions
import honeybee_energy.lib.materials as _m


# establish variables for the default constructions used across the library
# and auto-generate constructions if they were not loaded from default.idf
try:
    generic_exterior_wall = _idf_opaque_constructions['Generic Exterior Wall']
except KeyError:
    generic_exterior_wall = OpaqueConstruction(
        'Generic Exterior Wall', [_m.brick, _m.concrete_lw, _m.insulation,
                                  _m.wall_gap, _m.gypsum])
    generic_exterior_wall.lock()
    _idf_opaque_constructions['Generic Exterior Wall'] = generic_exterior_wall

try:
    generic_interior_wall = _idf_opaque_constructions['Generic Interior Wall']
except KeyError:
    generic_interior_wall = OpaqueConstruction(
        'Generic Interior Wall', [_m.gypsum, _m.wall_gap, _m.gypsum])
    generic_interior_wall.lock()
    _idf_opaque_constructions['Generic Interior Wall'] = generic_interior_wall

try:
    generic_underground_wall = _idf_opaque_constructions['Generic Underground Wall']
except KeyError:
    generic_underground_wall = OpaqueConstruction(
        'Generic Underground Wall', [_m.insulation, _m.concrete_hw,
                                     _m.wall_gap, _m.gypsum])
    generic_underground_wall.lock()
    _idf_opaque_constructions['Generic Underground Wall'] = generic_underground_wall

try:
    generic_exposed_floor = _idf_opaque_constructions['Generic Exposed Floor']
except KeyError:
    generic_exposed_floor = OpaqueConstruction(
        'Generic Exposed Floor', [_m.painted_metal, _m.ceiling_gap,
                                  _m.insulation, _m.concrete_lw])
    generic_exposed_floor.lock()
    _idf_opaque_constructions['Generic Exposed Floor'] = generic_exposed_floor

try:
    generic_interior_floor = _idf_opaque_constructions['Generic Interior Floor']
except KeyError:
    generic_interior_floor = OpaqueConstruction(
        'Generic Interior Floor', [_m.acoustic_tile, _m.ceiling_gap, _m.concrete_lw])
    generic_interior_floor.lock()
    _idf_opaque_constructions['Generic Interior Floor'] = generic_interior_floor

try:
    generic_ground_slab = _idf_opaque_constructions['Generic Ground Slab']
except KeyError:
    generic_ground_slab = OpaqueConstruction(
        'Generic Ground Slab', [_m.insulation, _m.concrete_hw])
    generic_ground_slab.lock()
    _idf_opaque_constructions['Generic Ground Slab'] = generic_ground_slab

try:
    generic_roof = _idf_opaque_constructions['Generic Roof']
except KeyError:
    generic_roof = OpaqueConstruction(
        'Generic Roof', [_m.roof_membrane, _m.insulation, _m.concrete_lw,
                         _m.ceiling_gap, _m.acoustic_tile])
    generic_roof.lock()
    _idf_opaque_constructions['Generic Roof'] = generic_roof

try:
    generic_interior_ceiling = _idf_opaque_constructions['Generic Interior Ceiling']
except KeyError:
    generic_interior_ceiling = OpaqueConstruction(
        'Generic Interior Ceiling', [_m.concrete_lw, _m.ceiling_gap, _m.acoustic_tile])
    generic_interior_ceiling.lock()
    _idf_opaque_constructions['Generic Interior Ceiling'] = generic_interior_ceiling

try:
    generic_underground_roof = _idf_opaque_constructions['Generic Underground Roof']
except KeyError:
    generic_underground_roof = OpaqueConstruction(
        'Generic Underground Roof', [_m.insulation, _m.concrete_hw,
                                     _m.ceiling_gap, _m.acoustic_tile])
    generic_underground_roof.lock()
    _idf_opaque_constructions['Generic Underground Roof'] = generic_underground_roof

try:
    generic_double_pane = _idf_window_constructions['Generic Double Pane']
except KeyError:
    generic_double_pane = WindowConstruction(
        'Generic Double Pane', [_m.lowe_glass, _m.air_gap, _m.clear_glass])
    generic_double_pane.lock()
    _idf_window_constructions['Generic Double Pane'] = generic_double_pane

try:
    generic_single_pane = _idf_window_constructions['Generic Single Pane']
except KeyError:
    generic_single_pane = WindowConstruction('Generic Single Pane', [_m.clear_glass])
    generic_single_pane.lock()
    _idf_window_constructions['Generic Single Pane'] = generic_single_pane

try:
    generic_exterior_door = _idf_opaque_constructions['Generic Exterior Door']
except KeyError:
    generic_exterior_door = OpaqueConstruction(
        'Generic Exterior Door', [_m.painted_metal, _m.insulation_thin,
                                  _m.painted_metal])
    generic_exterior_door.lock()
    _idf_opaque_constructions['Generic Exterior Door'] = generic_exterior_door

try:
    generic_interior_door = _idf_opaque_constructions['Generic Interior Door']
except KeyError:
    generic_interior_door = OpaqueConstruction('Generic Interior Door', [_m.wood])
    generic_interior_door.lock()
    _idf_opaque_constructions['Generic Interior Door'] = generic_interior_door

try:
    air_wall = _idf_opaque_constructions['Air Wall']
except KeyError:
    air_wall = OpaqueConstruction('Air Wall', [_m.air])
    air_wall.lock()
    _idf_opaque_constructions['Air Wall'] = air_wall


# make a dictionary of default shade constructions
generic_context = ShadeConstruction('Generic Context')
generic_shade = ShadeConstruction('Generic Shade', 0.35, 0.35)
_idf_shade_constructions = {generic_context.name: generic_context,
                            generic_shade.name: generic_shade}


# make lists of construction and material names to look up items in the library
OPAQUE_CONSTRUCTIONS = tuple(_idf_opaque_constructions.keys())
WINDOW_CONSTRUCTIONS = tuple(_idf_window_constructions.keys())
SHADE_CONSTRUCTIONS = tuple(_idf_shade_constructions.keys())


# methods to look up constructions from the library


def opaque_construction_by_name(construction_name):
    """Get an opaque construction from the library given the construction name.

    Args:
        construction_name: A text string for the name of the construction.
    """
    try:
        return _idf_opaque_constructions[construction_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the opaque energy construction library.'.format(
                construction_name))


def window_construction_by_name(construction_name):
    """Get an window construction from the library given the construction name.

    Args:
        construction_name: A text string for the name of the construction.
    """
    try:
        return _idf_window_constructions[construction_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the window energy construction library.'.format(
                construction_name))


def shade_construction_by_name(construction_name):
    """Get an shade construction from the library given the construction name.

    Args:
        construction_name: A text string for the name of the construction.
    """
    try:
        return _idf_shade_constructions[construction_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the shade energy construction library.'.format(
                construction_name))
