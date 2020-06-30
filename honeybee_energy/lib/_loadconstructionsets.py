"""Load all construction sets from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.constructionset import ConstructionSet

from ._loadconstructions import _opaque_constructions, _window_constructions, \
    _shade_constructions

import os
import json


# make a dictionary of all constructions loaded from JSON
_all_constructions = _opaque_constructions.copy()  # start with opaque constructions
_all_constructions.update(_window_constructions)  # add window constructions
_all_constructions.update(_shade_constructions)  # add shade constructions

# empty dictionary to hold loaded construction sets
_construction_sets = {}


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['construction_sets']
for cset_dict in default_data:
    constructionset = ConstructionSet.from_dict_abridged(cset_dict, _all_constructions)
    constructionset.lock()
    _construction_sets[cset_dict['identifier']] = constructionset
_default_sets = set(list(_construction_sets.keys()))


# then load construction sets from the user-supplied files
def load_construction_set_object(cset_dict):
    """Load a construction set object from a dictionary and add it to the lib dict."""
    try:
        if cset_dict['type'] == 'ConstructionSetAbridged':
            cset = ConstructionSet.from_dict_abridged(cset_dict, _all_constructions)
        else:
            cset = ConstructionSet.from_dict(cset_dict)
        cset.lock()
        assert cset_dict['identifier'] not in _default_sets, 'Cannot overwrite ' \
            'default construction set "{}".'.format(cset_dict['identifier'])
        _construction_sets[cset_dict['identifier']] = cset
    except (TypeError, KeyError, ValueError):
        pass  # not a Honeybee ConstructionSet JSON; possibly a comment


for f in os.listdir(folders.constructionset_lib):
    f_path = os.path.join(folders.constructionset_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path, 'r') as json_file:
            c_dict = json.load(json_file)
        if 'type' in c_dict:  # single object
            load_construction_set_object(c_dict)
        else:  # a collection of several objects
            for c_id in c_dict:
                load_construction_set_object(c_dict[c_id])


# then load honeybee extension data into a dictionary but don't make the objects yet
_construction_set_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'constructionsets')
    for _c_set_json in os.listdir(_data_dir):
        if _c_set_json.endswith('.json'):
            _c_set_dir = os.path.join(_data_dir, _c_set_json)
            with open(_c_set_dir, 'r') as f:
                _construction_set_standards_dict.update(json.load(f))
