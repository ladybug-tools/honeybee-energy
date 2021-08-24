"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.dynamic import WindowConstructionDynamic
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.construction.dictutil import dict_abridged_to_construction, \
    dict_to_construction

from ._loadmaterials import _opaque_materials, _window_materials, _default_mats
from ._loadschedules import _schedules

import os
import json


# dictionary of all materials loaded from JSON
_all_materials = _opaque_materials.copy()  # start with opaque materials
_all_materials.update(_window_materials)  # add window constructions


# empty dictionaries to hold idf-loaded materials and constructions
_opaque_constructions = {}
_window_constructions = {}
_shade_constructions = {}

# groups useful for construction classification
_opa_types = (OpaqueConstruction, AirBoundaryConstruction)
_win_types = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['constructions']
for con_dict in default_data:
    constr = dict_abridged_to_construction(con_dict, _all_materials, _schedules, False)
    constr.lock()
    if isinstance(constr, _opa_types):
        _opaque_constructions[con_dict['identifier']] = constr
    elif isinstance(constr, _win_types):
        _window_constructions[con_dict['identifier']] = constr
    else:  # it's a shade construction
        _shade_constructions[con_dict['identifier']] = constr
_default_constrs = set(
    list(_opaque_constructions.keys()) + list(_window_constructions.keys()) +
    list(_shade_constructions.keys()))


# then load materials and constructions from the user-supplied files
def lock_and_check_material(mat):
    """Lock a material and check that it's not overwriting a default."""
    mat.lock()
    assert mat.identifier not in _default_mats, 'Cannot overwrite ' \
        'default material "{}".'.format(mat.identifier)


def lock_and_check_construction(constr):
    """Lock a construction and check that it's not overwriting a default."""
    constr.lock()
    assert constr.identifier not in _default_constrs, 'Cannot overwrite ' \
        'default construction "{}".'.format(constr.identifier)


def load_construction_object(
        con_dict, load_mats, load_sch, opaque_cons, window_cons, shade_cons,
        misc_mats, misc_sch):
    """Load a construction object from a dictionary and add it to the library dict."""
    try:
        constr = dict_abridged_to_construction(con_dict, load_mats, load_sch, False)
        if constr is None:
            constr = dict_to_construction(con_dict, False)
            try:
                misc_mats.extend(constr.materials)
            except AttributeError:  # construction without materials
                pass
            if isinstance(constr, (WindowConstructionShade, WindowConstructionDynamic)):
                misc_sch.append(constr.schedule)
            elif isinstance(constr, AirBoundaryConstruction):
                misc_sch.append(constr.air_mixing_schedule)
        if constr is not None:
            lock_and_check_construction(constr)
            if isinstance(constr, _opa_types):
                opaque_cons[con_dict['identifier']] = constr
            elif isinstance(constr, _win_types):
                window_cons[con_dict['identifier']] = constr
            else:  # it's a shade construction
                shade_cons[con_dict['identifier']] = constr
    except (TypeError, KeyError):
        pass  # not a Honeybee Construction JSON; possibly a comment


def load_constructions_from_folder(
        construction_lib_folder, loaded_materials, loaded_schedules):
    """Load all of the construction objects from a construction standards folder.
    
    Args:
        construction_lib_folder: Path to a constructions sub-folder within a
            honeybee standards folder.
        loaded_materials: A dictionary of materials that have already been loaded
            from the library.
        loaded_schedules: A dictionary of materials that have already been loaded
            from the library.
    """
    opaque_mats, window_mats = {}, {}
    opaque_cons, window_cons, shade_cons = {}, {}, {}
    misc_mats, misc_sch = [], []
    for f in os.listdir(folders.construction_lib):
        f_path = os.path.join(folders.construction_lib, f)
        if os.path.isfile(f_path):
            if f_path.endswith('.idf'):
                constructions, materials = \
                    OpaqueConstruction.extract_all_from_idf_file(f_path)
                for mat in materials:
                    lock_and_check_material(mat)
                    opaque_mats[mat.identifier] = mat
                for cnstr in constructions:
                    lock_and_check_construction(cnstr)
                    opaque_cons[cnstr.identifier] = cnstr
                constructions, materials = \
                    WindowConstruction.extract_all_from_idf_file(f_path)
                for mat in materials:
                    lock_and_check_material(mat)
                    window_mats[mat.identifier] = mat
                for cnstr in constructions:
                    lock_and_check_construction(cnstr)
                    window_cons[cnstr.identifier] = cnstr
            if f_path.endswith('.json'):
                with open(f_path) as json_file:
                    data = json.load(json_file)
                if 'type' in data:  # single object
                    load_construction_object(
                        data, loaded_materials, loaded_schedules,
                        opaque_cons, window_cons, shade_cons, misc_mats, misc_sch)
                else:  # a collection of several objects
                    for constr_identifier in data:
                        load_construction_object(
                            data[constr_identifier], loaded_materials, loaded_schedules,
                            opaque_cons, window_cons, shade_cons, misc_mats, misc_sch)
    return opaque_cons, window_cons, shade_cons, opaque_mats, window_mats, \
        misc_mats, misc_sch

opaque_c, window_c, shade_c, opaque_m, window_m, misc_m, misc_s = \
    load_constructions_from_folder(folders.construction_lib, _all_materials, _schedules)
_opaque_materials.update(opaque_m)
_window_materials.update(window_m)
_opaque_constructions.update(opaque_c)
_window_constructions.update(window_c)
_shade_constructions.update(shade_c)

# then load honeybee extension data into a dictionary but don't make the objects yet
_opaque_constr_standards_dict = {}
_window_constr_standards_dict = {}
_shade_constr_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'constructions')
    _opaque_dir = os.path.join(_data_dir, 'opaque_construction.json')
    if os.path.isfile(_opaque_dir):
        with open(_opaque_dir, 'r') as f:
            _opaque_constr_standards_dict.update(json.load(f))
    _window_dir = os.path.join(_data_dir, 'window_construction.json')
    if os.path.isfile(_window_dir):
        with open(_window_dir, 'r') as f:
            _window_constr_standards_dict.update(json.load(f))
    _shade_dir = os.path.join(_data_dir, 'shade_construction.json')
    if os.path.isfile(_shade_dir):
        with open(_shade_dir, 'r') as f:
            _shade_constr_standards_dict.update(json.load(f))
