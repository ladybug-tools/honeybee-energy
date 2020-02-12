"""Load all schedules from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval

from ._loadtypelimits import _idf_schedule_type_limits

import os
import json


# empty dictionaries to hold idf-loaded schedules
_idf_schedules = {}


# load schedules from the default and user-supplied files
for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            schedule_rulesets = ScheduleRuleset.extract_all_from_idf_file(f_path)
            for sch in schedule_rulesets:
                sch.lock()
                _idf_schedules[sch.name] = sch
        elif f_path.endswith('.json'):  # parse as a honeybee JSON
            with open(f_path) as json_file:
                data = json.load(json_file)
            for sch_name in data:
                try:
                    sch_dict = data[sch_name]
                    if sch_dict['type'] == 'ScheduleRuleset':
                        _idf_schedules[sch_dict['name']] = \
                            ScheduleRuleset.from_dict_abridged(
                                sch_dict, _idf_schedule_type_limits)
                    elif sch_dict['type'] == 'ScheduleFixedInterval':
                        _idf_schedules[sch_dict['name']] = \
                            ScheduleFixedInterval.from_dict_abridged(
                                sch_dict, _idf_schedule_type_limits)
                except KeyError:
                    pass  # not a Honeybee JSON file with Schedules
