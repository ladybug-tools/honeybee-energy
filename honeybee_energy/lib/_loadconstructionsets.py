"""Load all construction sets from the JSON libraries."""
from honeybee_energy.constructionset import ConstructionSet

from ._loadconstructions import _idf_opaque_constructions, _idf_window_constructions

import os
import json


# empty dictionaries to hold json-loaded construction sets
_idf_constructions = _idf_opaque_constructions.copy()  # start with opaque constructions
_idf_constructions.update(_idf_window_constructions)  # add window constructions

_json_construction_sets = {}


# load construction sets from the default and user-supplied files
cur_dir = os.path.dirname(__file__)
constr_lib = os.path.join(cur_dir, 'library', 'constructionsets')
for f in os.listdir(constr_lib):
    f_path = os.path.join(constr_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path, 'r') as json_file:
            file_contents = json_file.read()
        c_dict = json.loads(file_contents)
        for c_name in c_dict:
            try:
                constructionset = ConstructionSet.from_dict_abridged(
                    c_dict[c_name], _idf_constructions)
                constructionset.lock()
                _json_construction_sets[constructionset.name] = constructionset
            except ValueError:
                pass  # failed to find the construction in the construction library
