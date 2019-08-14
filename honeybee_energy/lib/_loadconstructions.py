"""Load all materials and constructions from the IDF libraries."""
from honeybee_energy.construction import OpaqueConstruction, \
    WindowConstruction

import os
import inspect


# empty dictionaries to hold idf-loaded materials and constructions
_idf_opaque_materials = {}
_idf_window_materials = {}
_idf_opaque_constructions = {}
_idf_window_constructions = {}


# load other materials and constructions from user-supplied files
cur_dir = os.path.dirname(os.path.abspath(inspect.getfile(inspect.currentframe())))
construction_lib = cur_dir + '/idf/constructions/'
for f in os.listdir(construction_lib):
    f_path = construction_lib + f
    if f_path.endswith('.idf') and os.path.isfile(f_path):
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
