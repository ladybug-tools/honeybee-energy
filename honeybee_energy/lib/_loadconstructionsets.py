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


# then load honeybee extension data into a dictionary but don't make the objects yet
_construction_set_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'constructionsets')
    for _c_set_json in os.listdir(_data_dir):
        if _c_set_json.endswith('.json'):
            _c_set_dir = os.path.join(_data_dir, _c_set_json)
            with open(_c_set_dir, 'r') as f:
                _construction_set_standards_dict.update(json.load(f))


# then load construction sets from the user-supplied files
def load_construction_set_object(cset_dict, load_cons, con_sets, misc_cons):
    """Load a construction set object from a dictionary and add it to the lib dict."""
    try:
        if cset_dict['type'] == 'ConstructionSetAbridged':
            cset = ConstructionSet.from_dict_abridged(cset_dict, load_cons)
        else:
            cset = ConstructionSet.from_dict(cset_dict)
            misc_cons.extend(cset.modified_constructions)
        cset.lock()
        assert cset_dict['identifier'] not in _default_sets, 'Cannot overwrite ' \
            'default construction set "{}".'.format(cset_dict['identifier'])
        con_sets[cset_dict['identifier']] = cset
    except Exception:
        try:  # see if the construction set is built with constructions in standards
            import honeybee_energy.lib.constructions as _c
            for key in cset_dict:
                if isinstance(cset_dict[key], dict):
                    sub_dict = cset_dict[key]
                    for sub_key in sub_dict:
                        if sub_key == 'type' or sub_key in load_cons:
                            continue
                        if sub_dict[sub_key] is not None and \
                                sub_dict[sub_key] not in load_cons:
                            try:
                                load_cons[sub_dict[sub_key]] = \
                                    _c.opaque_construction_by_identifier(
                                        sub_dict[sub_key])
                            except ValueError:
                                load_cons[sub_dict[sub_key]] = \
                                    _c.window_construction_by_identifier(
                                    sub_dict[sub_key])
                elif key == 'shade_construction' and cset_dict[key] is not None \
                        and cset_dict[key] not in load_cons:
                    load_cons[cset_dict[key]] = \
                        _c.shade_construction_by_identifier(cset_dict[key])
                elif key == 'air_boundary_construction' \
                        and cset_dict[key] is not None \
                        and cset_dict[key] not in load_cons:
                    load_cons[cset_dict[key]] = \
                        _c.opaque_construction_by_identifier(cset_dict[key])
            con_sets[cset_dict['identifier']] = \
                ConstructionSet.from_dict_abridged(cset_dict, load_cons)
        except Exception:
            pass  # not a Honeybee ConstructionSet JSON; possibly a comment


def load_constructionsets_from_folder(constructionset_lib_folder, loaded_constructions):
    """Load all of the ConstructionSet objects from a constructionset standards folder.

    Args:
        constructionset_lib_folder: Path to a constructionsets sub-folder within a
            honeybee standards folder.
        loaded_constructions: A dictionary of constructions that have already
            been loaded from the library.
    """
    con_sets, misc_cons = {}, []
    for f in os.listdir(constructionset_lib_folder):
        f_path = os.path.join(constructionset_lib_folder, f)
        if os.path.isfile(f_path) and f_path.endswith('.json'):
            with open(f_path, 'r') as json_file:
                c_dict = json.load(json_file)
            if 'type' in c_dict:  # single object
                load_construction_set_object(
                    c_dict, loaded_constructions, con_sets, misc_cons)
            else:  # a collection of several objects
                for c_id in c_dict:
                    load_construction_set_object(
                        c_dict[c_id], loaded_constructions, con_sets, misc_cons)
    return con_sets, misc_cons


loaded_sets, misc_c = \
    load_constructionsets_from_folder(folders.constructionset_lib, _all_constructions)
_construction_sets.update(loaded_sets)
