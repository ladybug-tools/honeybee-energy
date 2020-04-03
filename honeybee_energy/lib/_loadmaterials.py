"""Load all materials from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.material.dictutil import dict_to_material

import os
import json


# empty dictionaries to hold JSON-loaded materials
_opaque_materials = {}
_window_materials = {}

# load material JSONs from the default and user-supplied files
for f in os.listdir(folders.construction_lib):
    f_path = os.path.join(folders.construction_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path) as json_file:
            data = json.load(json_file)
        for mat_id in data:
            try:
                mat_obj = dict_to_material(data[mat_id], False)
                if mat_obj:
                    mat_obj.lock()
                    if mat_obj.is_window_material:
                        _window_materials[mat_id] = mat_obj
                    else:
                        _opaque_materials[mat_id] = mat_obj
            except KeyError:
                pass  # not a Honeybee JSON file with Materials


# empty dictionaries to hold extension data
_opaque_mat_standards_dict = {}
_window_mat_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'constructions')
    _opaque_dir = os.path.join(_data_dir, 'opaque_material.json')
    if os.path.isfile(_opaque_dir):
        with open(_opaque_dir, 'r') as f:
            _opaque_mat_standards_dict.update(json.load(f))
    _window_dir = os.path.join(_data_dir, 'window_material.json')
    if os.path.isfile(_window_dir):
        with open(_window_dir, 'r') as f:
            _window_mat_standards_dict.update(json.load(f))
