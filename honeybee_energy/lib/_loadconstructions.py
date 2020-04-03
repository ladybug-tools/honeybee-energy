"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.construction.dictutil import dict_abridged_to_construction

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


# load materials and constructions from the default and user-supplied files
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
            for constr_identifier in data:
                try:
                    constr = dict_abridged_to_construction(
                        data[constr_identifier], _all_materials, _schedules, False)
                    if constr:
                        constr.lock()
                        if isinstance(constr, (OpaqueConstruction, AirBoundaryConstruction)):
                            _opaque_constructions[constr_identifier] = constr
                        elif isinstance(constr, WindowConstruction):
                            _window_constructions[constr_identifier] = constr
                        else:
                            _shade_constructions[constr_identifier] = constr
                except KeyError:
                    pass  # not a Honeybee JSON file with Constructions


# empty dictionaries to hold extension data
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
