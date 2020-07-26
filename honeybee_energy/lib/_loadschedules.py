"""Load all schedules from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.dictutil import dict_abridged_to_schedule, \
    dict_to_schedule

from ._loadtypelimits import _schedule_type_limits

import os
import json


# empty dictionary to hold loaded schedules
_schedules = {}


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['schedules']
for sch_dict in default_data:
    sch_obj = dict_abridged_to_schedule(sch_dict, _schedule_type_limits, False)
    sch_obj.lock()
    _schedules[sch_dict['identifier']] = sch_obj
_default_schedules = set(list(_schedules.keys()))


# then load schedules from the user-supplied files
def lock_and_check_schedule(sch):
    """Lock a schedule and check that it's not overwriting a default."""
    sch.lock()
    assert sch.identifier not in _default_schedules, 'Cannot overwrite ' \
        'default schedule "{}".'.format(sch.identifier)


def load_schedule_object(sch_dict):
    """Load a schedule object from a dictionary and add it to the _schedules dict."""
    try:
        sch_obj = dict_abridged_to_schedule(sch_dict, _schedule_type_limits, False)
        if sch_obj is None:
            sch_obj = dict_to_schedule(sch_dict, False)
        if sch_obj is not None:
            lock_and_check_schedule(sch_obj)
            _schedules[sch_dict['identifier']] = sch_obj
    except (TypeError, KeyError):
        pass  # not a Honeybee Schedule JSON; possibly a comment


for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            schedule_rulesets = ScheduleRuleset.extract_all_from_idf_file(f_path)
            for sch in schedule_rulesets:
                lock_and_check_schedule(sch)
                _schedules[sch.identifier] = sch
        elif f_path.endswith('.json'):  # parse as a honeybee JSON
            with open(f_path) as json_file:
                data = json.load(json_file)
            if 'type' in data:  # single object
                load_schedule_object(data)
            for sch_id in data:  # a collection of several objects
                load_schedule_object(data[sch_id])


# then load honeybee extension data into a dictionary but don't make the objects yet
_schedule_standards_dict = {}

for ext_folder in folders.standards_extension_folders:
    _data_dir = os.path.join(ext_folder, 'schedules', 'schedule.json')
    if os.path.isfile(_data_dir):
        with open(_data_dir, 'r') as f:
            _schedule_standards_dict.update(json.load(f))
