"""Load all schedule type limits from the standards library."""
from honeybee_energy.config import folders
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit

import os
import json


# empty dictionary to hold loaded schedule type limits
_schedule_type_limits = {}


# first load the honeybee defaults
with open(folders.defaults_file) as json_file:
    default_data = json.load(json_file)['schedule_type_limits']
for stl_dict in default_data:
    stl_obj = ScheduleTypeLimit.from_dict(stl_dict)
    _schedule_type_limits[stl_dict['identifier']] = stl_obj
_default_stls = set(list(_schedule_type_limits.keys()))


# then load schedule types from the user-supplied files
def check_and_add_schedule_type_limit(stl):
    """Check that a schedule type limit is not overwriting a default and add it."""
    # we won't raise an error for this case as schedule types are fairly universal
    if stl.identifier not in _default_stls:
        _schedule_type_limits[stl.identifier] = stl


for f in os.listdir(folders.schedule_lib):
    f_path = os.path.join(folders.schedule_lib, f)
    if os.path.isfile(f_path):
        if f_path.endswith('.idf'):
            schedule_type_limits = ScheduleTypeLimit.extract_all_from_idf_file(f_path)
            for typ in schedule_type_limits:
                check_and_add_schedule_type_limit(typ)
        elif f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            if 'type' in data and data['type'] == 'ScheduleTypeLimit':  # single object
                check_and_add_schedule_type_limit(ScheduleTypeLimit.from_dict(data))
            else:  # a collection of several objects
                for stl_id in data:
                    try:
                        stl_dict = data[stl_id]
                        if stl_dict['type'] == 'ScheduleTypeLimit':
                            check_and_add_schedule_type_limit(
                                ScheduleTypeLimit.from_dict(stl_dict))
                    except (TypeError, KeyError):
                        pass  # not a ScheduleTypeLimit JSON; possibly a comment
