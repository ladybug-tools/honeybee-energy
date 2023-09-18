"""Load all materials from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.material.dictutil import dict_to_material

import os
import json


# empty dictionaries to hold loaded materials
_opaque_materials = {}
_window_materials = {}


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['materials']
for mat_dict in default_data:
    mat_obj = dict_to_material(mat_dict, False)
    mat_obj.lock()
    if mat_obj.is_window_material:
        _window_materials[mat_dict['identifier']] = mat_obj
    else:
        _opaque_materials[mat_dict['identifier']] = mat_obj
_default_mats = set(list(_opaque_materials.keys()) + list(_window_materials.keys()))


# then load honeybee extension data into a dictionary but don't make the objects yet
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


# then load material JSONs from the default and user-supplied files
def load_material_object(mat_dict, opaque_mats, window_mats):
    """Load a material object from a dictionary and add it to the library dict."""
    try:
        mat_obj = dict_to_material(mat_dict, False)
        if mat_obj is not None:
            mat_obj.lock()
            assert mat_dict['identifier'] not in _default_mats, 'Cannot overwrite ' \
                'default material "{}".'.format(mat_dict['identifier'])
            if mat_obj.is_window_material:
                window_mats[mat_dict['identifier']] = mat_obj
            else:
                opaque_mats[mat_dict['identifier']] = mat_obj
    except (TypeError, KeyError):
        pass  # not a Honeybee Material JSON; possibly a comment


def load_materials_from_folder(construction_lib_folder):
    """Load all of the material layer objects from a construction standards folder.

    Args:
        construction_lib_folder: Path to a constructions sub-folder within a
            honeybee standards folder.
    """
    opaque_mats, window_mats = {}, {}
    for f in os.listdir(construction_lib_folder):
        f_path = os.path.join(construction_lib_folder, f)
        if os.path.isfile(f_path) and f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            if 'type' in data:  # single object
                load_material_object(data, opaque_mats, window_mats)
            else:  # a collection of several objects
                for mat_id in data:
                    load_material_object(data[mat_id], opaque_mats, window_mats)
    return opaque_mats, window_mats


opaque_m, window_m = load_materials_from_folder(folders.construction_lib)
_opaque_materials.update(opaque_m)
_window_materials.update(window_m)
