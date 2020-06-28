"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.construction.dictutil import dict_abridged_to_construction, \
    dict_to_construction

from ._loadmaterials import _opaque_materials, _window_materials
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


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['constructions']
for con_dict in default_data:
    constr = dict_abridged_to_construction(con_dict, _all_materials, _schedules, False)
    constr.lock()
    if isinstance(constr, (OpaqueConstruction, AirBoundaryConstruction)):
        _opaque_constructions[con_dict['identifier']] = constr
    elif isinstance(constr, (WindowConstruction, WindowConstructionShade)):
        _window_constructions[con_dict['identifier']] = constr
    else:  # it's a shade construction
        _shade_constructions[con_dict['identifier']] = constr


# then load materials and constructions from the user-supplied files
def load_construction_object(con_dict):
    """Load a construction object from a dictionary and add it to the library dict."""
    try:
        constr = dict_abridged_to_construction(
            con_dict, _all_materials, _schedules, False)
        if constr is None:
            constr = dict_to_construction(con_dict, False)
        if constr:
            constr.lock()
            if isinstance(constr, (OpaqueConstruction, AirBoundaryConstruction)):
                _opaque_constructions[con_dict['identifier']] = constr
            elif isinstance(constr, (WindowConstruction, WindowConstructionShade)):
                _window_constructions[con_dict['identifier']] = constr
            else:  # it's a shade construction
                _shade_constructions[con_dict['identifier']] = constr
    except (TypeError, KeyError):
        pass  # not a Honeybee Construction JSON; possibly a comment


for f in os.listdir(folders.construction_lib):
    f_path = os.path.join(folders.construction_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            constructions, materials = OpaqueConstruction.extract_all_from_idf_file(f_path)
            for mat in materials:
                mat.lock()
                _opaque_materials[mat.identifier] = mat
            for cnstr in constructions:
                cnstr.lock()
                _opaque_constructions[cnstr.identifier] = cnstr
            constructions, materials = WindowConstruction.extract_all_from_idf_file(f_path)
            for mat in materials:
                mat.lock()
                _window_materials[mat.identifier] = mat
            for cnstr in constructions:
                cnstr.lock()
                _window_constructions[cnstr.identifier] = cnstr
        if f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            if 'type' in data:  # single object
                load_construction_object(data)
            else:  # a collection of several objects
                for constr_identifier in data:
                    load_construction_object(data[constr_identifier])


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
