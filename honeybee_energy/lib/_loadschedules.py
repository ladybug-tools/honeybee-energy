"""Load all schedules from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import os


# empty dictionaries to hold idf-loaded schedules
_idf_schedules = {}


# load schedules from the default and user-supplied files
for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.idf'):
        schedule_rulesets = ScheduleRuleset.extract_all_from_idf_file(f_path)
        for sch in schedule_rulesets:
            sch.lock()
            _idf_schedules[sch.name] = sch
