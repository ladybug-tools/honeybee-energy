"""Load all schedules from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.dictutil import dict_abridged_to_schedule, \
    dict_to_schedule

from ._loadtypelimits import _schedule_type_limits

import os
import json


# empty dictionaries to hold idf-loaded schedules
_schedules = {}


# load schedules from the default and user-supplied files
for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            schedule_rulesets = ScheduleRuleset.extract_all_from_idf_file(f_path)
            for sch in schedule_rulesets:
                sch.lock()
                _schedules[sch.identifier] = sch
        elif f_path.endswith('.json'):  # parse as a honeybee JSON
            with open(f_path) as json_file:
                data = json.load(json_file)
            for sch_id in data:
                try:
                    sch_obj = dict_abridged_to_schedule(
                        data[sch_id], _schedule_type_limits, False)
                    if sch_obj is None:
                        sch_obj = dict_to_schedule(data[sch_id], False)
                    if sch_obj:
                        sch_obj.lock()
                        _schedules[sch_id] = sch_obj
                except KeyError:
                    pass  # not a Honeybee JSON file with Schedules


# empty dictionaries to hold extension data
_schedule_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'schedules', 'schedule.json')
    if os.path.isfile(_data_dir):
        with open(_data_dir, 'r') as f:
            _schedule_standards_dict.update(json.load(f))
