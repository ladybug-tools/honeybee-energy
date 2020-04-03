"""Load all of the constructions and materials from the IDF libraries."""
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from ._loadconstructions import _opaque_constructions, _window_constructions, \
    _shade_constructions, _opaque_constr_standards_dict, _window_constr_standards_dict, \
    _shade_constr_standards_dict

import honeybee_energy.lib.materials as _m
import honeybee_energy.lib.schedules as _s


# materials of all default constructions; used when they are not found in default.idf
_default_prop = {
    'generic_exterior_wall':
        (_m.brick, _m.concrete_lw, _m.insulation, _m.wall_gap, _m.gypsum),
    'generic_interior_wall':
        (_m.gypsum, _m.wall_gap, _m.gypsum),
    'generic_underground_wall':
        (_m.insulation, _m.concrete_hw, _m.wall_gap, _m.gypsum),
    'generic_exposed_floor':
        (_m.painted_metal, _m.ceiling_gap, _m.insulation, _m.concrete_lw),
    'generic_interior_floor':
        (_m.acoustic_tile, _m.ceiling_gap, _m.concrete_lw),
    'generic_ground_slab':
        (_m.insulation, _m.concrete_hw),
    'generic_roof':
        (_m.roof_membrane, _m.insulation, _m.concrete_lw, _m.ceiling_gap, _m.acoustic_tile),
    'generic_interior_ceiling':
        (_m.concrete_lw, _m.ceiling_gap, _m.acoustic_tile),
    'generic_underground_roof':
        (_m.insulation, _m.concrete_hw, _m.ceiling_gap, _m.acoustic_tile),
    'generic_double_pane':
        (_m.lowe_glass, _m.air_gap, _m.clear_glass),
    'generic_single_pane':
        (_m.clear_glass),
    'generic_exterior_door':
        (_m.painted_metal, _m.insulation_thin, _m.painted_metal),
    'generic_interior_door':
        (_m.wood)
}

# establish variables for the default constructions used across the library
# and auto-generate constructions if they were not loaded from default.idf
try:
    generic_exterior_wall = _opaque_constructions['Generic Exterior Wall']
except KeyError:
    generic_exterior_wall = OpaqueConstruction(
        'Generic Exterior Wall', _default_prop['generic_exterior_wall'])
    generic_exterior_wall.lock()
    _opaque_constructions['Generic Exterior Wall'] = generic_exterior_wall

try:
    generic_interior_wall = _opaque_constructions['Generic Interior Wall']
except KeyError:
    generic_interior_wall = OpaqueConstruction(
        'Generic Interior Wall', _default_prop['generic_interior_wall'])
    generic_interior_wall.lock()
    _opaque_constructions['Generic Interior Wall'] = generic_interior_wall

try:
    generic_underground_wall = _opaque_constructions['Generic Underground Wall']
except KeyError:
    generic_underground_wall = OpaqueConstruction(
        'Generic Underground Wall', _default_prop['generic_underground_wall'])
    generic_underground_wall.lock()
    _opaque_constructions['Generic Underground Wall'] = generic_underground_wall

try:
    generic_exposed_floor = _opaque_constructions['Generic Exposed Floor']
except KeyError:
    generic_exposed_floor = OpaqueConstruction(
        'Generic Exposed Floor', _default_prop['generic_exposed_floor'])
    generic_exposed_floor.lock()
    _opaque_constructions['Generic Exposed Floor'] = generic_exposed_floor

try:
    generic_interior_floor = _opaque_constructions['Generic Interior Floor']
except KeyError:
    generic_interior_floor = OpaqueConstruction(
        'Generic Interior Floor', _default_prop['generic_interior_floor'])
    generic_interior_floor.lock()
    _opaque_constructions['Generic Interior Floor'] = generic_interior_floor

try:
    generic_ground_slab = _opaque_constructions['Generic Ground Slab']
except KeyError:
    generic_ground_slab = OpaqueConstruction(
        'Generic Ground Slab', _default_prop['generic_ground_slab'])
    generic_ground_slab.lock()
    _opaque_constructions['Generic Ground Slab'] = generic_ground_slab

try:
    generic_roof = _opaque_constructions['Generic Roof']
except KeyError:
    generic_roof = OpaqueConstruction(
        'Generic Roof', _default_prop['generic_roof'])
    generic_roof.lock()
    _opaque_constructions['Generic Roof'] = generic_roof

try:
    generic_interior_ceiling = _opaque_constructions['Generic Interior Ceiling']
except KeyError:
    generic_interior_ceiling = OpaqueConstruction(
        'Generic Interior Ceiling', _default_prop['generic_interior_ceiling'])
    generic_interior_ceiling.lock()
    _opaque_constructions['Generic Interior Ceiling'] = generic_interior_ceiling

try:
    generic_underground_roof = _opaque_constructions['Generic Underground Roof']
except KeyError:
    generic_underground_roof = OpaqueConstruction(
        'Generic Underground Roof', _default_prop['generic_underground_roof'])
    generic_underground_roof.lock()
    _opaque_constructions['Generic Underground Roof'] = generic_underground_roof

try:
    generic_double_pane = _window_constructions['Generic Double Pane']
except KeyError:
    generic_double_pane = WindowConstruction(
        'Generic Double Pane', _default_prop['generic_double_pane'])
    generic_double_pane.lock()
    _window_constructions['Generic Double Pane'] = generic_double_pane

try:
    generic_single_pane = _window_constructions['Generic Single Pane']
except KeyError:
    generic_single_pane = WindowConstruction(
        'Generic Single Pane', _default_prop['generic_single_pane'])
    generic_single_pane.lock()
    _window_constructions['Generic Single Pane'] = generic_single_pane

try:
    generic_exterior_door = _opaque_constructions['Generic Exterior Door']
except KeyError:
    generic_exterior_door = OpaqueConstruction(
        'Generic Exterior Door', _default_prop['generic_exterior_door'])
    generic_exterior_door.lock()
    _opaque_constructions['Generic Exterior Door'] = generic_exterior_door

try:
    generic_interior_door = _opaque_constructions['Generic Interior Door']
except KeyError:
    generic_interior_door = OpaqueConstruction(
        'Generic Interior Door', _default_prop['generic_interior_door'])
    generic_interior_door.lock()
    _opaque_constructions['Generic Interior Door'] = generic_interior_door

# add a default air boundary construction to the library
try:
    air_boundary = _opaque_constructions['Generic Air Boundary']
except KeyError:
    air_boundary = AirBoundaryConstruction('Generic Air Boundary')
    air_boundary.lock()
    _opaque_constructions['Generic Air Boundary'] = air_boundary


# process the default shade constructions
try:
    generic_context = _shade_constructions['Generic Context']
except KeyError:
    generic_context = ShadeConstruction('Generic Context')
    generic_context.lock()
    _shade_constructions[generic_context.identifier] = generic_context

try:
    generic_shade = _shade_constructions['Generic Shade']
except KeyError:
    generic_shade = ShadeConstruction('Generic Shade', 0.35, 0.35)
    generic_shade.lock()
    _shade_constructions[generic_shade.identifier] = generic_shade


# make lists of construction identifiers to look up items in the library
OPAQUE_CONSTRUCTIONS = tuple(_opaque_constructions.keys()) + \
    tuple(_opaque_constr_standards_dict.keys())
WINDOW_CONSTRUCTIONS = tuple(_window_constructions.keys()) + \
    tuple(_window_constr_standards_dict.keys())
SHADE_CONSTRUCTIONS = tuple(_shade_constructions.keys()) + \
    tuple(_shade_constr_standards_dict.keys())


def opaque_construction_by_identifier(construction_identifier):
    """Get an opaque construction from the library given the construction identifier.

    Args:
        construction_identifier: A text string for the identifier of the construction.
    """
    try:
        return _opaque_constructions[construction_identifier]
    except KeyError:
        try:  # search the extension data
            constr_dict = _opaque_constr_standards_dict[construction_identifier]
            if constr_dict['type'] == 'OpaqueConstructionAbridged':
                mats = {}
                for mat in constr_dict['layers']:
                    mats[mat] = _m.opaque_material_by_identifier(mat)
                return OpaqueConstruction.from_dict_abridged(constr_dict, mats)
            else:  # AirBoundaryConstruction
                try:
                    sch_id = constr_dict['air_mixing_schedule']
                    schs = {sch_id: _s.schedule_by_identifier(sch_id)}
                except KeyError:  # no air mixing key provided
                    schs = {}
                return AirBoundaryConstruction.from_dict_abridged(constr_dict, sch_id)
        except KeyError:  # construction is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the opaque energy construction library.'.format(
                    construction_identifier))


def window_construction_by_identifier(construction_identifier):
    """Get an window construction from the library given the construction identifier.

    Args:
        construction_identifier: A text string for the identifier of the construction.
    """
    try:
        return _window_constructions[construction_identifier]
    except KeyError:
        try:  # search the extension data
            constr_dict = _window_constr_standards_dict[construction_identifier]
            mats = {}
            for mat in constr_dict['layers']:
                mats[mat] = _m.window_material_by_identifier(mat)
            return WindowConstruction.from_dict_abridged(constr_dict, mats)
        except KeyError:  # construction is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the window energy construction library.'.format(
                    construction_identifier))


def shade_construction_by_identifier(construction_identifier):
    """Get an shade construction from the library given the construction identifier.

    Args:
        construction_identifier: A text string for the identifier of the construction.
    """
    try:
        return _shade_constructions[construction_identifier]
    except KeyError:
        try:  # search the extension data
            constr_dict = _shade_constr_standards_dict[construction_identifier]
            return ShadeConstruction.from_dict(constr_dict)
        except KeyError:  # construction is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the shade energy construction library.'.format(
                    construction_identifier))
