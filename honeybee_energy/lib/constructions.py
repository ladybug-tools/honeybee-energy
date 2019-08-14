"""Load all of the constructions and materials from the IDF libraries."""
from honeybee_energy.construction import OpaqueConstruction, \
    WindowConstruction
from ._loadconstructions import _idf_opaque_constructions, _idf_window_constructions
import honeybee_energy.lib.materials as _m


# generic wall constructions
if 'Generic Exterior Wall' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Exterior Wall'] = OpaqueConstruction(
        'Generic Exterior Wall', [_m.brick, _m.concrete_lw, _m.insulation,
                                  _m.wall_gap, _m.gypsum])
    _idf_opaque_constructions['Generic Exterior Wall'] .lock()
if 'Generic Interior Wall' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Interior Wall'] = OpaqueConstruction(
        'Generic Interior Wall', [_m.gypsum, _m.wall_gap, _m.gypsum])
    _idf_opaque_constructions['Generic Interior Wall'].lock()
if 'Generic Underground Wall' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Underground Wall'] = OpaqueConstruction(
        'Generic Underground Wall', [_m.insulation, _m.concrete_hw,
                                     _m.wall_gap, _m.gypsum])
    _idf_opaque_constructions['Generic Underground Wall'].lock()

# generic floor constructions
if 'Generic Exposed Floor' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Exposed Floor'] = OpaqueConstruction(
        'Generic Exposed Floor', [_m.painted_metal, _m.ceiling_gap,
                                  _m.insulation, _m.concrete_lw])
    _idf_opaque_constructions['Generic Exposed Floor'].lock()
if 'Generic Interior Floor' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Interior Floor'] = OpaqueConstruction(
        'Generic Interior Floor', [_m.acoustic_tile, _m.ceiling_gap, _m.concrete_lw])
    _idf_opaque_constructions['Generic Interior Floor'].lock()
if 'Generic Ground Slab' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Ground Slab'] = OpaqueConstruction(
        'Generic Ground Slab', [_m.insulation, _m.concrete_hw])
    _idf_opaque_constructions['Generic Ground Slab'].lock()

# generic roof/ceiling constructions
if 'Generic Roof' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Roof'] = OpaqueConstruction(
        'Generic Roof', [_m.roof_membrane, _m.insulation, _m.concrete_lw,
                         _m.ceiling_gap, _m.acoustic_tile])
    _idf_opaque_constructions['Generic Roof'].lock()
if 'Generic Interior Ceiling' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Interior Ceiling'] = OpaqueConstruction(
        'Generic Interior Ceiling', [_m.concrete_lw, _m.ceiling_gap, _m.acoustic_tile])
    _idf_opaque_constructions['Generic Interior Ceiling'].lock()
if 'Generic Underground Roof' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Underground Roof'] = OpaqueConstruction(
        'Generic Underground Roof', [_m.insulation, _m.concrete_hw,
                                     _m.ceiling_gap, _m.acoustic_tile])
    _idf_opaque_constructions['Generic Underground Roof'].lock()

# generic window constructions
if 'Generic Double Pane' not in _idf_window_constructions:
    _idf_window_constructions['Generic Double Pane'] = WindowConstruction(
        'Generic Double Pane', [_m.lowe_glass, _m.air_gap, _m.clear_glass])
    _idf_window_constructions['Generic Double Pane'].lock()
if 'Generic Single Pane' not in _idf_window_constructions:
    _idf_window_constructions['Generic Single Pane'] = WindowConstruction(
        'Generic Single Pane', [_m.clear_glass])
    _idf_window_constructions['Generic Single Pane'].lock()

# generic door constructions
if 'Generic Exterior Door' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Exterior Door'] = OpaqueConstruction(
        'Generic Exterior Door', [_m.painted_metal, _m.insulation_thin,
                                  _m.painted_metal])
    _idf_opaque_constructions['Generic Exterior Door'].lock()
if 'Generic Interior Door' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Generic Interior Door'] = OpaqueConstruction(
        'Generic Interior Door', [_m.wood])
    _idf_opaque_constructions['Generic Interior Door'].lock()

# air wall construction
if 'Air Wall' not in _idf_opaque_constructions:
    _idf_opaque_constructions['Air Wall'] = OpaqueConstruction(
        'Air Wall', [_m.air])
    _idf_opaque_constructions['Air Wall'].lock()

# establish the default constructions used across the library
generic_exterior_wall = _idf_opaque_constructions['Generic Exterior Wall']
generic_interior_wall = _idf_opaque_constructions['Generic Interior Wall']
generic_underground_wall = _idf_opaque_constructions['Generic Underground Wall']
generic_exposed_floor = _idf_opaque_constructions['Generic Exposed Floor']
generic_interior_floor = _idf_opaque_constructions['Generic Interior Floor']
generic_ground_slab = _idf_opaque_constructions['Generic Ground Slab']
generic_roof = _idf_opaque_constructions['Generic Roof']
generic_interior_ceiling = _idf_opaque_constructions['Generic Interior Ceiling']
generic_underground_roof = _idf_opaque_constructions['Generic Underground Roof']
generic_double_pane = _idf_window_constructions['Generic Double Pane']
generic_single_pane = _idf_window_constructions['Generic Single Pane']
generic_exterior_door = _idf_opaque_constructions['Generic Exterior Door']
generic_interior_door = _idf_opaque_constructions['Generic Interior Door']
air_wall = _idf_opaque_constructions['Air Wall']

# make lists of construction and material names to look up items in the library
OPAQUE_CONSTRUCTIONS = tuple(_idf_opaque_constructions.keys())
WINDOW_CONSTRUCTIONS = tuple(_idf_window_constructions.keys())


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
