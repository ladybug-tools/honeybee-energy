"""Load all schedules from the IDF libraries."""
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import os


# empty dictionaries to hold idf-loaded schedules
_idf_schedules = {}


# load other materials and constructions from user-supplied files
cur_dir = os.path.dirname(__file__)
schedule_lib = os.path.join(cur_dir, 'idf', 'schedules')
for f in os.listdir(schedule_lib):
    f_path = os.path.join(schedule_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.idf'):
        schedule_rulesets = ScheduleRuleset.extract_all_from_idf_file(f_path)
        for sch in schedule_rulesets:
            sch.lock()
            _idf_schedules[sch.name] = sch
