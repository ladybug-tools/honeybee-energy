"""Establish the default schedule types within the honeybee_energy library."""
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit

from ._loadtypelimits import _idf_schedule_type_limits


# properties of all default schedule types; used when they are not found in default.idf
_default_prop = {
    'fractional': ('Fractional', 0, 1, 'Continuous', 'Dimensionless'),
    'on_off': ('On-Off', 0, 1, 'Discrete', 'Dimensionless'),
    'temperature': ('Temperature', -273.15, None, 'Continuous', 'Temperature'),
    'activity_level': ('Activity Level', 0, None, 'Continuous', 'ActivityLevel'),
    'power': ('Power', None, None, 'Continuous', 'Power'),
    'angle': ('Angle', 0, 180, 'Continuous', 'Angle'),
    'thermostat_control': ('Thermostat Control', 0, 4, 'Discrete', 'Dimensionless'),
    'delta_temperature': ('Delta Temperature', None, None, 'Continuous', 'DeltaTemperature')
}


# establish variables for the default schedule types used across the library
# and auto-generate materials if they were not loaded from default.idf
try:
    fractional = _idf_schedule_type_limits['Fractional']
except KeyError:
    fractional = ScheduleTypeLimit(*_default_prop['fractional'])
    _idf_schedule_type_limits['Fractional'] = fractional

try:
    on_off = _idf_schedule_type_limits['On-Off']
except KeyError:
    on_off = ScheduleTypeLimit(*_default_prop['on_off'])
    _idf_schedule_type_limits['On-Off'] = on_off

try:
    temperature = _idf_schedule_type_limits['Temperature']
except KeyError:
    temperature = ScheduleTypeLimit(*_default_prop['temperature'])
    _idf_schedule_type_limits['Temperature'] = temperature

try:
    activity_level = _idf_schedule_type_limits['Activity Level']
except KeyError:
    activity_level = ScheduleTypeLimit(*_default_prop['activity_level'])
    _idf_schedule_type_limits['Activity Level'] = activity_level

try:
    power = _idf_schedule_type_limits['Power']
except KeyError:
    power = ScheduleTypeLimit(*_default_prop['power'])
    _idf_schedule_type_limits['Power'] = power

try:
    angle = _idf_schedule_type_limits['Angle']
except KeyError:
    angle = ScheduleTypeLimit(*_default_prop['angle'])
    _idf_schedule_type_limits['Angle'] = angle

try:
    thermostat_control = _idf_schedule_type_limits['Thermostat Control']
except KeyError:
    thermostat_control = ScheduleTypeLimit(*_default_prop['thermostat_control'])
    _idf_schedule_type_limits['Thermostat Control'] = thermostat_control

try:
    delta_temperature = _idf_schedule_type_limits['Delta Temperature']
except KeyError:
    delta_temperature = ScheduleTypeLimit(*_default_prop['delta_temperature'])
    _idf_schedule_type_limits['Delta Temperature'] = delta_temperature


# make lists of schedule types to look up items in the library
SCHEDULE_TYPE_LIMITS = tuple(_idf_schedule_type_limits.keys())


# methods to look up schedule types from the library


def schedule_type_limit_by_name(schedule_type_limit_name):
    """Get a schedule type from the library given its name.

    Args:
        schedule_type_limit_name: A text string for the name of the schedule type.
    """
    try:
        return _idf_schedule_type_limits[schedule_type_limit_name]
    except KeyError:
        raise ValueError('"{}" was not found in the schedule type limits '
                         'library.'.format(schedule_type_limit_name))
