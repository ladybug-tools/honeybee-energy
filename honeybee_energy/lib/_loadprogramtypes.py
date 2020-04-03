"""Load all program types from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.programtype import ProgramType

from ._loadschedules import _schedules

import os
import json


# empty dictionaries to hold json-loaded program types
_program_types = {}


# load program types from the default and user-supplied files
for f in os.listdir(folders.programtype_lib):
    f_path = os.path.join(folders.programtype_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path, 'r') as json_file:
            p_dict = json.load(json_file)
        for p_id in p_dict:
            try:
                program = ProgramType.from_dict_abridged(p_dict[p_id], _schedules)
                program.lock()
                _program_types[program.identifier] = program
            except ValueError:
                pass  # failed to find schedule in the library; not a valid program


# empty dictionaries to hold extension data
_program_types_standards_dict = {}
_program_types_standards_registry = {}

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
