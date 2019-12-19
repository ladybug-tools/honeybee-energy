"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction

import os


# empty dictionaries to hold idf-loaded materials and constructions
_idf_opaque_materials = {}
_idf_window_materials = {}
_idf_opaque_constructions = {}
_idf_window_constructions = {}


# load materials and constructions from the default and user-supplied files
for f in os.listdir(folders.construction_lib):
    f_path = os.path.join(folders.construction_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.idf'):
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
