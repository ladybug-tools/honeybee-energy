"""Load all schedule type limits from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit

import os


# empty dictionaries to hold idf-loaded schedules and schedule types
_idf_schedule_type_limits = {}


# load schedule types from the default and user-supplied files
schedule_lib = os.path.join(folders.template_library_folder, 'schedules')
for f in os.listdir(schedule_lib):
    f_path = os.path.join(schedule_lib, f)
    if os.path.isfile(f_path) and f_path.endswith('.idf'):
        schedule_type_limits = ScheduleTypeLimit.extract_all_from_idf_file(f_path)
        for typ in schedule_type_limits:
            _idf_schedule_type_limits[typ.name] = typ
