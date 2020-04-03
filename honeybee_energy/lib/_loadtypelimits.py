"""Load all schedule type limits from the IDF libraries."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit

import os
import json


# empty dictionaries to hold idf-loaded schedule type limits
_schedule_type_limits = {}


# load schedule types from the default and user-supplied files
for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            schedule_type_limits = ScheduleTypeLimit.extract_all_from_idf_file(f_path)
            for typ in schedule_type_limits:
                _schedule_type_limits[typ.identifier] = typ
        elif f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            for stl_id in data:
                try:
                    stl_dict = data[stl_id]
                    if stl_dict['type'] == 'ScheduleTypeLimit':
                        _schedule_type_limits[stl_dict['identifier']] = \
                            ScheduleTypeLimit.from_dict(stl_dict)
                except KeyError:
                    pass  # not a Honeybee JSON file with ScheduleTypeLimits
