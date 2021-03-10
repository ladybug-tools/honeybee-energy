"""Load all program types from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.programtype import ProgramType

from ._loadschedules import _schedules

import os
import json


# empty dictionary to hold loaded program types
_program_types = {}


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['program_types']
for pro_dict in default_data:
    program = ProgramType.from_dict_abridged(pro_dict, _schedules)
    program.lock()
    _program_types[pro_dict['identifier']] = program
_default_programs = set(list(_program_types.keys()))


# then load program types from the user-supplied files
def load_program_object(pro_dict):
    """Load a program object from a dictionary and add it to the _program_types dict."""
    try:
        if pro_dict['type'] == 'ProgramTypeAbridged':
            program = ProgramType.from_dict_abridged(pro_dict, _schedules)
        else:
            program = ProgramType.from_dict(pro_dict)
        program.lock()
        assert pro_dict['identifier'] not in _default_programs, 'Cannot overwrite ' \
            'default program type "{}".'.format(pro_dict['identifier'])
        _program_types[pro_dict['identifier']] = program
    except (TypeError, KeyError, ValueError):
        pass  # not a Honeybee ProgramType JSON; possibly a comment


for f in os.listdir(folders.programtype_lib):
    f_path = os.path.join(folders.programtype_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path, 'r') as json_file:
            p_dict = json.load(json_file)
        if 'type' in p_dict:  # single object
            load_program_object(p_dict)
        else:  # a collection of several objects
            for p_id in p_dict:
                load_program_object(p_dict[p_id])


# then load honeybee extension data into a dictionary but don't make the objects yet
_program_types_standards_dict = {}
_program_types_standards_registry = {}
_building_programs_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'programtypes')
    for _p_type_json in os.listdir(_data_dir):
        if _p_type_json.endswith('.json'):
            _p_type_dir = os.path.join(_data_dir, _p_type_json)
            with open(_p_type_dir, 'r') as f:
                _program_types_standards_dict.update(json.load(f))
    _data_dir = os.path.join(ext_folder, 'programtypes_registry')
    if os.path.isdir(_data_dir):
        for _p_type_json in os.listdir(_data_dir):
            if _p_type_json.endswith('_registry.json'):
                _p_type_dir = os.path.join(_data_dir, _p_type_json)
                vintage = _p_type_json.split('_registry.json')[0]
                try:
                    with open(_p_type_dir, 'r') as f:
                        _program_types_standards_registry[vintage] = json.load(f)
                except FileNotFoundError:
                    pass
    _bld_file = os.path.join(ext_folder, 'building_mix.json')
    if os.path.isfile(_bld_file):
        with open(_bld_file, 'r') as f:
            _building_programs_dict.update(json.load(f))
