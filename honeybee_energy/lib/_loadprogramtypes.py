"""Load all program types from the JSON libraries."""
from honeybee_energy.config import folders
from honeybee_energy.programtype import ProgramType

from ._loadschedules import _idf_schedules

import os
import json


# empty dictionaries to hold json-loaded program types
_json_program_types = {}


# load program types from the default and user-supplied files
for f in os.listdir(folders.programtype_lib):
    f_path = os.path.join(folders.programtype_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.json'):
        with open(f_path, 'r') as json_file:
            p_dict = json.load(json_file)
        for p_name in p_dict:
            try:
                program = ProgramType.from_dict_abridged(p_dict[p_name], _idf_schedules)
                program.lock()
                _json_program_types[program.name] = program
            except ValueError:
                pass  # failed to find the schedule in the schedule library
