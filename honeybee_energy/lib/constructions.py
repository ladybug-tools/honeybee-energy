"""Load all of the constructions and materials from the IDF libraries."""
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.dynamic import WindowConstructionDynamic
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from ._loadconstructions import _opaque_constructions, _window_constructions, \
    _shade_constructions, _opaque_constr_standards_dict, _window_constr_standards_dict, \
    _shade_constr_standards_dict

import honeybee_energy.lib.materials as _m
import honeybee_energy.lib.schedules as _s


# establish variables for the default constructions used across the library
generic_exterior_wall = _opaque_constructions['Generic Exterior Wall']
generic_interior_wall = _opaque_constructions['Generic Interior Wall']
generic_underground_wall = _opaque_constructions['Generic Underground Wall']
generic_exposed_floor = _opaque_constructions['Generic Exposed Floor']
generic_interior_floor = _opaque_constructions['Generic Interior Floor']
generic_ground_slab = _opaque_constructions['Generic Ground Slab']
generic_roof = _opaque_constructions['Generic Roof']
generic_interior_ceiling = _opaque_constructions['Generic Interior Ceiling']
generic_underground_roof = _opaque_constructions['Generic Underground Roof']
generic_double_pane = _window_constructions['Generic Double Pane']
generic_single_pane = _window_constructions['Generic Single Pane']
generic_exterior_door = _opaque_constructions['Generic Exterior Door']
generic_interior_door = _opaque_constructions['Generic Interior Door']
air_boundary = _opaque_constructions['Generic Air Boundary']
generic_context = _shade_constructions['Generic Context']
generic_shade = _shade_constructions['Generic Shade']


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
                mat_key = 'layers' if 'layers' in constr_dict else 'materials'
                for mat in constr_dict[mat_key]:
                    mats[mat] = _m.opaque_material_by_identifier(mat)
                return OpaqueConstruction.from_dict_abridged(constr_dict, mats)
            else:  # AirBoundaryConstruction
                try:
                    sch_id = constr_dict['air_mixing_schedule']
                    schs = {sch_id: _s.schedule_by_identifier(sch_id)}
                except KeyError:  # no air mixing key provided
                    schs = {}
                return AirBoundaryConstruction.from_dict_abridged(constr_dict, schs)
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
            if constr_dict['type'] == 'WindowConstructionAbridged':
                mats = {}
                mat_key = 'layers' if 'layers' in constr_dict else 'materials'
                for mat in constr_dict[mat_key]:
                    mats[mat] = _m.window_material_by_identifier(mat)
                return WindowConstruction.from_dict_abridged(constr_dict, mats)
            elif constr_dict['type'] == 'WindowConstructionShadeAbridged':
                mats = {}
                mat_key = 'layers' if 'layers' in constr_dict['window_construction'] \
                    else 'materials'
                for mat in constr_dict['window_construction'][mat_key]:
                    mats[mat] = _m.window_material_by_identifier(mat)
                shd_mat = constr_dict['shade_material']
                mats[shd_mat] = _m.window_material_by_identifier(shd_mat)
                try:
                    sch_id = constr_dict['schedule']
                    schs = {sch_id: _s.schedule_by_identifier(sch_id)}
                except KeyError:  # no schedule key provided
                    schs = {}
                return WindowConstructionShade.from_dict_abridged(
                    constr_dict, mats, schs)
            elif constr_dict['type'] == 'WindowConstructionDynamicAbridged':
                mats = {}
                for con in constr_dict['constructions']:
                    for mat in constr_dict['materials']:
                        mats[mat] = _m.window_material_by_identifier(mat)
                sch_id = constr_dict['schedule']
                schs = {sch_id: _s.schedule_by_identifier(sch_id)}
                return WindowConstructionDynamic.from_dict_abridged(
                    constr_dict, mats, schs)
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
