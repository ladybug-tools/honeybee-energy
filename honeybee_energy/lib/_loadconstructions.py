"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction

from ._loadmaterials import _idf_opaque_materials, _idf_window_materials
from ._loadschedules import _idf_schedules

import os
import json


# empty dictionaries to hold idf-loaded materials and constructions
_idf_opaque_constructions = {}
_idf_window_constructions = {}
_idf_shade_constructions = {}


# load materials and constructions from the default and user-supplied files
for f in os.listdir(folders.construction_lib):
    f_path = os.path.join(folders.construction_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            constructions, materials = OpaqueConstruction.extract_all_from_idf_file(f_path)
            for mat in materials:
                mat.lock()
                _idf_opaque_materials[mat.name] = mat
            for cnstr in constructions:
                cnstr.lock()
                _idf_opaque_constructions[cnstr.name] = cnstr
            constructions, materials = WindowConstruction.extract_all_from_idf_file(f_path)
            for mat in materials:
                mat.lock()
                _idf_window_materials[mat.name] = mat
            for cnstr in constructions:
                cnstr.lock()
                _idf_window_constructions[cnstr.name] = cnstr
        if f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            for constr_name in data:
                try:
                    constr_dict = data[constr_name]
                    if constr_dict['type'] == 'OpaqueConstructionAbridged':
                        _idf_opaque_constructions[constr_dict['name']] = \
                            OpaqueConstruction.from_dict_abridged(
                                constr_dict, _idf_opaque_materials)
                    elif constr_dict['type'] == 'WindowConstructionAbridged':
                        _idf_window_constructions[constr_dict['name']] = \
                            WindowConstruction.from_dict_abridged(
                                constr_dict, _idf_window_materials)
                    elif constr_dict['type'] == 'ShadeConstruction':
                        _idf_shade_constructions[constr_dict['name']] = \
                            ShadeConstruction.from_dict(constr_dict)
                    elif constr_dict['type'] == 'AirBoundaryConstructionAbridged':
                        _idf_opaque_constructions[constr_dict['name']] = \
                            AirBoundaryConstruction.from_dict_abridged(
                                constr_dict, _idf_schedules)
                except KeyError:
                    pass  # not a Honeybee JSON file with Constructions
