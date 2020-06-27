"""Establish the default schedule types within the honeybee_energy library."""
from ._loadtypelimits import _schedule_type_limits


# establish variables for the default schedule types used across the library
fractional = _schedule_type_limits['Fractional']
on_off = _schedule_type_limits['On-Off']
temperature = _schedule_type_limits['Temperature']
activity_level = _schedule_type_limits['Activity Level']
power = _schedule_type_limits['Power']
humidity = _schedule_type_limits['Humidity']
angle = _schedule_type_limits['Angle']
delta_temperature = _schedule_type_limits['Delta Temperature']


# make lists of schedule types to look up items in the library
SCHEDULE_TYPE_LIMITS = tuple(_schedule_type_limits.keys())


def schedule_type_limit_by_identifier(schedule_type_limit_identifier):
    """Get a schedule type from the library given its identifier.

    Args:
        schedule_type_limit_identifier: A text string for the identifier of the
            schedule type.
    """
    try:
        return _schedule_type_limits[schedule_type_limit_identifier]
    except KeyError:
        raise ValueError('"{}" was not found in the schedule type limits '
                         'library.'.format(schedule_type_limit_identifier))
