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
        for mat_name in data:
            try:
                mat_obj = dict_to_material(data[mat_name], False)
                if mat_obj:
                    mat_obj.lock()
                    if mat_obj.is_window_material:
                        _window_materials[mat_name] = mat_obj
                    else:
                        _opaque_materials[mat_name] = mat_obj
            except KeyError:
                pass  # not a Honeybee JSON file with Materials
