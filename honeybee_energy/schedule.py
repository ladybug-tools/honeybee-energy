# coding=utf-8
"""Energy schedules."""
from .scheduletype import ScheduleType
from .writer import generate_idf_string, parse_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string

from ladybug.datacollection import HourlyContinuousCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import Date, Time
from ladybug.datatype.generic import GenericType

from collections import Iterable


@lockable
class ScheduleDay(object):
    """Schedule for a single day.

    Note that a ScheduleDay cannot be assigned to Rooms, Shades, etc.  The ScheduleDay
    must be added to a ScheduleRuleset or a ScheduleRule and then the ScheduleRuleset
    can be applied to such objects.

    Properties:
        name
        times
        values
        interpolate
        is_constant
    """
    __slots__ = ('_name', '_values', '_times', '_interpolate', '_locked')

    _start_of_day = Time(0, 0)
    VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)

    def __init__(self, name, values, times=None, interpolate=False):
        """Initialize Schedule Day.

        Args:
            name: Text string for day schedule name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            values: A list of floats or integers for the values of the schedule.
                The length of this list must match the length of the times list.
            times: A list of ladybug Time objects with the same length as the input
                values. Each time represents the time of day that the corresponding
                value begins to take effect. This first item of this input list should
                therefore always be 0:00. If this input is None, the default will be a
                single time at 0:00, indicating the `values` input should be a single
                constant value that goes all of the way until the end of the day.
                Note that these times follow a different convention than EnergyPlus,
                which uses "time until" instead of "time of beginning". This results
                in EnergyPlus schedule times always ending in 24:00, which is not
                necessary here where, instead, all schedules begin with 0:00.
            interpolate: Boolean to note whether values in between times should be
                linearly interpolated or whether successive values should take effect
                immediately upon the beginning time corrsponding to them. Default: False
        """
        self._locked = False  # unlocked by default
        self.name = name

        # assign the times and values
        if times is None:
            self._times = (self._start_of_day,)
        else:
            if not isinstance(times, tuple):
                try:
                    times = tuple(times)
                except (ValueError, TypeError):
                    raise TypeError('ScheduleDay times must be iterable.')
            for time in times:
                self._check_time(time)
            self._times = times
        self.values = values

        # if times are not ordered chronologically, sort them
        if not self._are_chronological(self._times):
            self._times, self._values = zip(*sorted(zip(self._times, self._values)))

        # ensure that the schedule always starts from 0:00
        assert self._times[0] == self._start_of_day, 'ScheduleDay times must always ' \
            'start with 0:00. Got {}.'.format(self._times[0])

        self.interpolate = interpolate

    @property
    def name(self):
        """Get or set the text string for schedule day name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'schedule day')

    @property
    def values(self):
        """Get or set the Schedule's numerical values, which correspond to the times."""
        return self._values

    @values.setter
    def values(self, values):
        self._values = self._check_values(values)

    @property
    def times(self):
        """Get or set the Schedule's times, which correspond to the numerical values."""
        return self._times

    @times.setter
    def times(self, times):
        self._times = self._check_times(times)

    @property
    def interpolate(self):
        """Get or set a boolean noting whether values should be interpolated."""
        return self._interpolate

    @interpolate.setter
    def interpolate(self, interpolate):
        self._interpolate = bool(interpolate)

    @property
    def is_constant(self):
        """Boolean to note whether the schedule is a single constant value."""
        return len(self) == 1

    def add_value(self, value, time):
        """Add a value to the schedule along with the time it begins to take effect.

        Args:
            value: A number for the schedule value.
            time: The ladybug Time object for the time at which the value begins to
                take effect.
        """
        self._check_time(time)
        value = self._check_value(value)
        self._times = self._times + (time,)
        self._values = self._values + (value,)
        if self._times[-1] < self._times[-2]:  # ensure times are chronological
            self._times, self._values = zip(*sorted(zip(self._times, self._values)))

    def remove_value_by_index(self, value_index):
        """Remove a value from the schedule by its index.

        Args:
            value_index: An integer for the index of the value to remove.
        """
        assert len(self._values) > 1, 'ScheduleDay must have at least one value.'
        self._values = tuple(x for i, x in enumerate(self._values) if i != value_index)
        self._times = tuple(x for i, x in enumerate(self._times) if i != value_index)

    def remove_value_by_time(self, time):
        """Remove a value from the schedule by its time in the times property.

        Args:
            time: An ladybug Time for the time and the value to remove.
        """
        self.remove_value_by_index(self._times.index(time))

    def values_at_timestep(self, timestep=1):
        """Get a list of sequential schedule values over the day at a given timestep.

        Note that there are two possible ways that these values can be mapped to
        corresponding times (here referred to as the "Ladybug Tools Interpretation"
        and the "EnergyPlus Interpretation"). Both of these interpretations ultimately
        refer to the exact same schedule in the calculations of EnergyPlus but the
        times of day that each of the values are mapped to differ.

        Ladybug Tools Interpretation - The first value in the returned list here
        corresponds to the time 0:00 and the value for this time is applied over
        the rest of the following timestep. In this way, an office schedule that is set
        to be occupied from 9:00 until 17:00 will show 9:00 as occupied but 17:00 as
        unoccupied.

        EnergyPlus Interpretation - The first value in the returned list here
        corresponds to the timestep after 0:00. For example, if the timestep is 1,
        the time mapped to the first value is 1:00. If the timestep is 6, the first
        value corresponds to 0:10. In this interpretation, the value for this time is
        applied over all of the previous timestep. In this way, an office schedule that
        is set to be occupied from 9:00 until 17:00 will show 9:00 as unoccupied but
        17:00 as occupied.

        Args:
            timestep: An integer for the number of steps per hour at which to return
                the resulting values.
        """
        values = []
        minute_delta = 60 / timestep
        mod = 0  # track the minute of day through iteration
        time_index = 1  # track the index of the next time of change
        until_mod = self._get_until_mod(time_index)  # get the mod of the next change
        if not self.interpolate:
            for step in range(24 * timestep):
                if mod >= until_mod:
                    time_index += 1
                    until_mod = self._get_until_mod(time_index)
                values.append(self._values[time_index - 1])
                mod += minute_delta
        else:
            for step in range(24 * timestep):
                if mod >= until_mod:
                    i = 0
                    delta = self._values[time_index] - self._values[time_index - 1]
                    until_mod = self._get_until_mod(time_index + 1)
                    n_steps = (until_mod - self._times[time_index].mod) / minute_delta
                    values.append(self._values[time_index - 1])
                    time_index += 1
                elif time_index == 1:
                    values.append(self._values[time_index - 1])
                else:
                    i += 1
                    values.append(self._values[time_index - 2] + ((i / n_steps) * delta))
                mod += minute_delta
            del values[0]  # delete first value, which is makes interpolation off by one
            values.append(self._values[-1])  # add the final value that is reached
        return values

    def data_collection_at_timestep(self, date, schedule_type, timestep=1):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

        Note that ladybug DataCollections always follow the "Ladybug Tools
        Interpretation" of date time values as noted in the values_at_timestep()
        documentation.

        Args:
            date: A ladybug Date object for the day of the year the DataCollection
                is representing.
            schedule_type: A ScheduleType object that describes the schedule, which
                will be used to make the header for the DataCollection
            timestep: An integer for the number of steps per hour at which to make
                the resulting DataCollection.
        """
        assert isinstance(date, Date), \
            'Expected ladybug Date. Got {}.'.format(type(date))
        assert isinstance(schedule_type, ScheduleType), \
            'Expected Honeybee ScheduleType. Got {}.'.format(type(schedule_type))
        a_period = AnalysisPeriod(date.month, date.day, 0, date.month, date.day, 23,
                                  timestep, date.leap_year)
        header = Header(schedule_type.data_type, schedule_type.unit, a_period,
                        metadata={'schedule': self.name})
        return HourlyContinuousCollection(header, self.values_at_timestep(timestep))

    @classmethod
    def from_values_at_timestep(cls, name, values, timestep=1, remove_repeated=True):
        """Make a ScheduleDay from a list of values at a certain timestep.

        Args:
            name: Text string for day schedule name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            values: A list of numerical values with a length equal to 24 * timestep.
                Note that the first value of this list is expected to be that at 0:00
                and not at the first simulation timestep as EnergyPlus reports.
            timestep: An integer for the number of steps per hour that the input
                values correspond to.  For example, if each value represents 30
                minutes, the timestep is 2. For 15 minutes, it is 4. Default is 1,
                meaning each value represents a single hour. Must be one of the
                following: (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)
            remove_repeated: Boolean to note whether sequentially repeated values
                should be removed from the resulting `values` and `times` comprising
                the schedule. Default is True, which results in a lighter, more compact
                schedule. However, you may want to set this to False when planning to
                set the schedule's `interpolate` property to True as this avoids
                interpolation over long, multi-hour periods.
        """
        # check the inputs
        assert timestep in cls.VALIDTIMESTEPS, 'ScheduleDay timestep "{}" is invalid.' \
            ' Must be one of the following:\n{}'.format(timestep, cls.VALIDTIMESTEPS)
        n_vals = 24 * timestep
        assert len(values) == n_vals, 'There must be {} ScheduleDay values when' \
            'the timestep is {}. Got {}.'.format(n_vals, timestep, len(values))

        # build the list of schedule values and times
        schedule_times = [cls._start_of_day]
        minute_delta = 60 / timestep
        mod = minute_delta
        if remove_repeated:
            schedule_values = [values[0]]
            for i in range(1, n_vals):
                if values[i] != schedule_values[-1]:  # non-repeated value
                    schedule_times.append(Time.from_mod(mod))
                    schedule_values.append(values[i])
                mod += minute_delta
        else:
            schedule_values = values  # we don't care if there are repeated values
            for i in range(1, n_vals):
                schedule_times.append(Time.from_mod(mod))
                mod += minute_delta

        return cls(name, schedule_values, schedule_times)

    @classmethod
    def from_idf(cls, idf_string):
        """Create a ScheduleDay from an EnergyPlus IDF text string.

        Note that this method can accept all 3 types of EnergyPlus Schedule:Day
        (Schedule:Day:Interval, Schedule:Day:Hourly, and Schedule:Day:List).

        Args:
            idf_string: A text string fully describing an EnergyPlus
                Schedule:Day:Interval.
        """
        if idf_string.startswith('Schedule:Day:Hourly,'):
            ep_strs = parse_idf_string(idf_string)
            hour_vals = [float(val) for val in ep_strs[2:]]
            return cls.from_values_at_timestep(ep_strs[0], hour_vals)
        if idf_string.startswith('Schedule:Day:List,'):
            ep_strs = parse_idf_string(idf_string)
            interpolate = False if ep_strs[2] == 'No' or ep_strs[2] == '' else True
            timestep = int(60 / int(ep_strs[3]))
            timestep_vals = [float(val) for val in ep_strs[4:]]
            remove_repeated = True if not interpolate else False
            sched_day = cls.from_values_at_timestep(
                ep_strs[0], timestep_vals, timestep, remove_repeated)
            sched_day.interpolate = interpolate
            return sched_day
        else:
            ep_strs = parse_idf_string(idf_string, 'Schedule:Day:Interval,')
            interpolate = False if ep_strs[2] == 'No' or ep_strs[2] == '' else True
            length = len(ep_strs)
            values = tuple(float(ep_strs[i]) for i in range(4, length + 1, 2))
            times = [cls._start_of_day]
            for i in range(3, length, 2):
                try:
                    times.append(Time.from_time_string(ep_strs[i]))
                except ValueError:  # 24:00
                    pass
            return cls(ep_strs[0], values, times, interpolate)

    @classmethod
    def from_standards_dict(cls, data):
        """Create a ScheduleDay from an OpenStudio standards gem dictionary.

        Args:
            data:{
                "name": "Large Office Bldg Occ",
                "category": "Occupancy",
                "units": null,
                "day_types": "Default",
                "start_date": "2014-01-01T00:00:00+00:00",
                "end_date": "2014-12-31T00:00:00+00:00",
                "type": "Hourly",
                "notes": "From DOE Reference Buildings ",
                "values": [0.0, 0.0, 0.0, 0.0, 0.0, 0.0, 0.1, 0.2, 0.95, 0.95, 0.95,
                           0.95, 0.5, 0.95, 0.95, 0.95, 0.95, 0.7, 0.4, 0.4, 0.1,
                           0.1, 0.05, 0.05]
                }
        """
        if data['type'] == 'Hourly':
            return cls.from_values_at_timestep(data['name'], data['values'])
        elif data['type'] == 'Constant':
            return cls(data['name'], data['values'])  # single value in the schedule

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleDay from a dictionary.

        Args:
            data: {
                "type": 'ScheduleDay',
                "name": 'Office Occupancy',
                "values": [0, 1, 0],
                "times": [(0, 0), (9, 0), (17, 0)],
                "interpolate": False
                }
        """
        assert data['type'] == 'ScheduleDay', \
            'Expected ScheduleDay. Got {}.'.format(data['type'])

        if 'times' in data and data['times'] is not None:
            times = tuple(Time.from_array(tim) for tim in data['times'])
        else:
            times = None
        interpolate = data['interpolate'] if 'interpolate' in data else None

        return cls(data['name'], data['values'], times, interpolate)

    def to_idf(self):
        """IDF string representation of ScheduleDay object."""
        fields = [self.name, '']
        fields.append('No' if not self.interpolate else 'Linear')
        comments = ['schedule name', 'schedule type limits', 'interpolate to timestep']
        for i in range(len(self._values)):
            count = i + 1
            try:
                fields.append(self._times[count])
            except IndexError:  # the last "time until"
                fields.append('24:00')
            comments.append('time %s {hh:mm}' % count)
            fields.append(self._values[i])
            comments.append('value until time %s' % count)
        return generate_idf_string('Schedule:Day:Interval', fields, comments)

    def to_dict(self):
        """ScheduleDay dictionary representation."""
        base = {'type': 'ScheduleDay'}
        base['name'] = self.name
        base['values'] = self.values
        base['times'] = [time.to_array() for time in self.times]
        base['interpolate'] = self.interpolate
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _get_until_mod(self, time_index):
        """Get the minute of the day until a value is applied given a time_index."""
        try:
            return self._times[time_index].mod
        except IndexError:  # constant value until the end of the day
            return 1440

    def _check_values(self, values):
        """Check values whenever they come through the values setter."""
        assert isinstance(values, Iterable) and not \
            isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        assert len(values) == len(self._times), \
            'Length of values list must match length of times list. {} != {}'.format(
                len(values), len(self._times))
        assert len(values) > 0, 'ScheduleDay must include at least one value.'
        try:
            return tuple(float(val) for val in values)
        except (ValueError, TypeError):
            raise TypeError('ScheduleDay values must be numbers.')

    def _check_times(self, times):
        """Check times whenever they come through the times setter."""
        if not isinstance(times, tuple):
            try:
                times = tuple(times)
            except (ValueError, TypeError):
                raise TypeError('ScheduleDay times must be iterable.')
        for time in times:
            self._check_time(time)
        assert len(times) == len(self._values), \
            'Length of values list must match length of datetimes list. {} != {}'.format(
                len(times), len(self._values))
        if not self._are_chronological(times):
            times, self._values = zip(*sorted(zip(times, self._values)))
        # ensure that the schedule always starts from 0:00
        assert times[0] == self._start_of_day, \
            'ScheduleDay times must always start with 0:00. Got {}.'.format(times[0])
        return times

    @staticmethod
    def _check_value(value):
        """Check that an individual input value is a number."""
        try:
            return float(value)
        except (ValueError, TypeError):
            raise TypeError('ScheduleDay values must be numbers.')

    @staticmethod
    def _check_time(time):
        """Check that an individual time value is a ladybug Time."""
        assert isinstance(time, Time), \
            'Expected ladybug Time for ScheduleDay. Got {}.'.format(type(time))

    @staticmethod
    def _are_chronological(times):
        """Test whether a list of times is chronological."""
        return all(times[i] < times[i + 1] for i in range(len(times) - 1))

    def __len__(self):
        return len(self.values)

    def __getitem__(self, key):
        return self.values[key]

    def __iter__(self):
        return iter(self.values)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.name,) + self.values + tuple(hash(t) for t in self.times) + \
            (self.interpolate,)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleDay) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return ScheduleDay(self.name, self.values, self.times, self.interpolate)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return self.to_idf()


@lockable
class ScheduleRule(object):
    """Schedule rule including a DaySchedule and when it should be applied.

    Note that a ScheduleRule cannot be assigned to Rooms, Shades, etc.  The
    ScheduleRule must be added to a ScheduleRuleset and then the ScheduleRuleset
    can be applied to such objects.

    Properties:
        schedule_day
        apply_sunday
        apply_monday
        apply_tuesday
        apply_wednesday
        apply_thursday
        apply_friday
        apply_saturday
        apply_holiday
        start_date
        end_date
        apply_weekday
        apply_weekend
        analysis_period
        week_apply_tuple
    """
    __slots__ = ('_schedule_day', '_apply_sunday', '_apply_monday', '_apply_tuesday',
                 '_apply_wednesday', '_apply_thursday', '_apply_friday',
                 '_apply_saturday', '_apply_holiday', '_start_date', '_end_date',
                 '_start_doy', '_end_doy', '_locked')

    _year_start = Date(1, 1)
    _year_end = Date(12, 31)

    def __init__(self, schedule_day, apply_sunday=False, apply_monday=False,
                 apply_tuesday=False, apply_wednesday=False, apply_thursday=False,
                 apply_friday=False, apply_saturday=False, apply_holiday=False,
                 start_date=None, end_date=None):
        """Initialize Schedule Rule.

        Args:
            schedule_day: A ScheduleDay object associated with this rule.
            apply_sunday: Boolean noting whether to apply schedule_day on Sundays.
            apply_monday: Boolean noting whether to apply schedule_day on Mondays.
            apply_tuesday: Boolean noting whether to apply schedule_day on Tuesdays.
            apply_wednesday: Boolean noting whether to apply schedule_day on Wednesdays.
            apply_thursday: Boolean noting whether to apply schedule_day on Thursdays.
            apply_friday: Boolean noting whether to apply schedule_day on Fridays.
            apply_saturday: Boolean noting whether to apply schedule_day on Saturdays.
            apply_holiday: Boolean noting whether to apply schedule_day on Holidays.
            start_date: A ladybug Date object for the start of the period over which
                the schedule_day will be applied. If None, Jan 1 will be used.
            end_date: A ladybug Date object for the end of the period over which
                the schedule_day will be applied. If None, Dec 31 will be used.
        """
        self._locked = False  # unlocked by default
        self.schedule_day = schedule_day
        self.apply_sunday = apply_sunday
        self.apply_monday = apply_monday
        self.apply_tuesday = apply_tuesday
        self.apply_wednesday = apply_wednesday
        self.apply_thursday = apply_thursday
        self.apply_friday = apply_friday
        self.apply_saturday = apply_saturday
        self.apply_holiday = apply_holiday

        # process the start date and end date
        if start_date is not None:
            self._check_date(start_date, 'start_date')
            self._start_date = start_date
        else:
            self._start_date = self._year_start
        self._start_doy = self._doy_non_leap_year(self._start_date)
        self.end_date = end_date

    @property
    def schedule_day(self):
        """Get or set the ScheduleDay object associated with this rule.."""
        return self._schedule_day

    @schedule_day.setter
    def schedule_day(self, value):
        assert isinstance(value, ScheduleDay), \
            'Expected ScheduleDay for ScheduleRule. Got {}.'.format(type(value))
        self._schedule_day = value

    @property
    def apply_sunday(self):
        """Get or set a boolean noting whether to apply schedule_day on Sundays."""
        return self._apply_sunday

    @apply_sunday.setter
    def apply_sunday(self, value):
        self._apply_sunday = bool(value)

    @property
    def apply_monday(self):
        """Get or set a boolean noting whether to apply schedule_day on Mondays."""
        return self._apply_monday

    @apply_monday.setter
    def apply_monday(self, value):
        self._apply_monday = bool(value)

    @property
    def apply_tuesday(self):
        """Get or set a boolean noting whether to apply schedule_day on Tuesdays."""
        return self._apply_tuesday

    @apply_tuesday.setter
    def apply_tuesday(self, value):
        self._apply_tuesday = bool(value)

    @property
    def apply_wednesday(self):
        """Get or set a boolean noting whether to apply schedule_day on Wednesdays."""
        return self._apply_wednesday

    @apply_wednesday.setter
    def apply_wednesday(self, value):
        self._apply_wednesday = bool(value)

    @property
    def apply_thursday(self):
        """Get or set a boolean noting whether to apply schedule_day on Thursdays."""
        return self._apply_thursday

    @apply_thursday.setter
    def apply_thursday(self, value):
        self._apply_thursday = bool(value)

    @property
    def apply_friday(self):
        """Get or set a boolean noting whether to apply schedule_day on Fridays."""
        return self._apply_friday

    @apply_friday.setter
    def apply_friday(self, value):
        self._apply_friday = bool(value)

    @property
    def apply_saturday(self):
        """Get or set a boolean noting whether to apply schedule_day on Saturdays."""
        return self._apply_saturday

    @apply_saturday.setter
    def apply_saturday(self, value):
        self._apply_saturday = bool(value)

    @property
    def apply_holiday(self):
        """Get or set a boolean noting whether to apply schedule_day on Holidays."""
        return self._apply_holiday

    @apply_holiday.setter
    def apply_holiday(self, value):
        self._apply_holiday = bool(value)

    @property
    def apply_weekday(self):
        """Get or set a boolean noting whether to apply schedule_day on week days."""
        return self._apply_monday and self._apply_tuesday and self._apply_wednesday and \
            self._apply_thursday and self._apply_friday

    @apply_weekday.setter
    def apply_weekday(self, value):
        self._apply_monday = self._apply_tuesday = self._apply_wednesday = \
            self._apply_thursday = self._apply_friday = bool(value)

    @property
    def apply_weekend(self):
        """Get or set a boolean noting whether to apply schedule_day on weekends."""
        return self._apply_sunday and self._apply_saturday

    @apply_weekend.setter
    def apply_weekend(self, value):
        self._apply_sunday = self._apply_saturday = bool(value)

    @property
    def start_date(self):
        """Get or set a ladybug Date object for the start of the period."""
        return self._start_date

    @start_date.setter
    def start_date(self, value):
        if value is not None:
            self._check_date(value, 'start_date')
            self._start_date = value
        else:
            self._start_date = self._year_start
        self._check_start_before_end()
        self._start_doy = self._doy_non_leap_year(self._start_date)

    @property
    def end_date(self):
        """Get or set a ladybug Date object for the end of the period."""
        return self._end_date

    @end_date.setter
    def end_date(self, value):
        if value is not None:
            self._check_date(value, 'end_date')
            self._end_date = value
        else:
            self._end_date = self._year_end
        self._check_start_before_end()
        self._end_doy = self._doy_non_leap_year(self._end_date)

    @property
    def analysis_period(self):
        """Get a ladybug AnalysisPeriod object using the start_date and end_date."""
        return AnalysisPeriod(st_month=self._start_date.month,
                              st_day=self._start_date.day,
                              end_month=self._end_date.month,
                              end_day=self._end_date.day)

    @property
    def days_applied(self):
        """Get a list of text values for the days applied."""
        day_names = ('sunday', 'monday', 'tuesday', 'wednesday', 'thursday',
                     'friday', 'saturday')
        days = [name for name, apply in zip(day_names, self.week_apply_tuple) if apply]
        if self.apply_holiday:
            days.append('holiday')
        return days

    @property
    def week_apply_tuple(self):
        """Get a tuple of 7 booleans for each of the days of the week."""
        return (self._apply_sunday, self._apply_monday, self._apply_tuesday,
                self._apply_wednesday, self._apply_thursday, self._apply_friday,
                self._apply_saturday)

    def does_rule_apply(self, doy, dow=None):
        """Check if this rule applies to a given day of the year and day of the week.

        Args:
            doy: An integer between 1 anf 365 for the day of the year to test.
            dow: An integer between 1 anf 7 for the day of the week to test. If None,
                this value will be derived from the doy, assuming the first day of
                the year is a Sunday.
        """
        dow = dow if dow is not None else doy % 7
        return self.does_rule_apply_date(doy) and self.week_apply_tuple[dow - 1]

    def does_rule_apply_leap_year(self, doy, dow=None):
        """Check if this rule applies to a given day of a leap year and day of the week.

        Args:
            doy: An integer between 1 anf 366 for the day of the leap year to test.
            dow: An integer between 1 anf 7 for the day of the week to test. If None,
                this value will be derived from the doy, assuming the first day of
                the year is a Sunday.
        """
        dow = dow if dow is not None else doy % 7
        return self.does_rule_apply_doy_leap_year(doy) and self.week_apply_tuple[dow - 1]

    def does_rule_apply_doy(self, doy):
        """Check if this rule applies to a given day of the year.

        Args:
            doy: An integer between 1 anf 365 for the day of the year to test.
        """
        return self._start_doy <= doy <= self._end_doy

    def does_rule_apply_doy_leap_year(self, doy):
        """Check if this rule applies to a given day of a leap year.

        Args:
            doy: An integer between 1 anf 366 for the day of the leap year to test.
        """
        st_doy = self._start_doy if self._start_date.month <= 2 else self._start_doy + 1
        end_doy = self._end_doy if self._end_date.month <= 2 else self._end_doy + 1
        return st_doy <= doy <= end_doy

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleRule from a dictionary.

        Args:
            data: {
                "type": 'ScheduleRule'
                "schedule_day": {
                    "type": 'ScheduleDay',
                    "name": 'Office Occupancy',
                    "values": [0, 1, 0],
                    "times": [(0, 0), (9, 0), (17, 0)],
                    "interpolate": False
                    }
                "apply_sunday": False,
                "apply_monday": True,
                "apply_tuesday": True,
                "apply_wednesday": True,
                "apply_thursday": True,
                "apply_friday": True,
                "apply_saturday": False,
                "apply_holiday": False,
                "start_date": (1, 1),
                "end_date": (12, 31)
                }
        """
        assert data['type'] == 'ScheduleRule', \
            'Expected ScheduleRule. Got {}.'.format(data['type'])

        schedule_day = ScheduleDay.from_dict(data['schedule_day'])
        apply_sunday = data['apply_sunday'] if 'apply_sunday' in data else False
        apply_monday = data['apply_monday'] if 'apply_monday' in data else False
        apply_tuesday = data['apply_tuesday'] if 'apply_tuesday' in data else False
        apply_wednesday = data['apply_wednesday'] if 'apply_wednesday' in data else False
        apply_thursday = data['apply_thursday'] if 'apply_thursday' in data else False
        apply_friday = data['apply_friday'] if 'apply_friday' in data else False
        apply_saturday = data['apply_saturday'] if 'apply_saturday' in data else False
        apply_holiday = data['apply_holiday'] if 'apply_holiday' in data else False
        start_date = Date.from_array(data['start_date']) if \
            'start_date' in data else cls._year_start
        end_date = Date.from_array(data['end_date']) if \
            'end_date' in data else cls._year_end

        return cls(schedule_day, apply_sunday, apply_monday, apply_tuesday,
                   apply_wednesday, apply_thursday, apply_friday, apply_saturday,
                   apply_holiday, start_date, end_date)

    def to_dict(self):
        """ScheduleRule dictionary representation."""
        return {'type': 'ScheduleRule',
                'schedule_day': self.schedule_day.to_dict(),
                'apply_sunday': self.apply_sunday,
                'apply_monday': self.apply_monday,
                'apply_tuesday': self.apply_tuesday,
                'apply_wednesday': self.apply_wednesday,
                'apply_thursday': self.apply_thursday,
                'apply_friday': self.apply_friday,
                'apply_saturday': self.apply_saturday,
                'apply_holiday': self.apply_holiday,
                'start_date': self.start_date.to_array(),
                'end_date': self.end_date.to_array()
                }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def lock(self):
        """The lock() method will also lock the schedule_day."""
        self._locked = True
        self.schedule_day._locked = True

    def unlock(self):
        """The unlock() method will also unlock the schedule_day."""
        self._locked = False
        self.schedule_day._locked = False

    def _check_start_before_end(self):
        """Check that the start_date is before the end_date."""
        assert self._start_date < self._end_date, 'ScheduleRule start_date must come ' \
            'before end_date. {} comes after {}.'.format(self.start_date, self.end_date)

    @staticmethod
    def _check_date(date, date_name='date'):
        assert isinstance(date, Date), 'Expected ladybug Date for ' \
            'ScheduleRule {}. Got {}.'.format(date_name, type(date))

    @staticmethod
    def _doy_non_leap_year(date):
        """Get a doy for a non-leap-year even when the input date is for a leap year."""
        if not date.leap_year:
            return date.doy
        else:
            return date.doy if date <= Date(2, 29, True) else date.doy - 1

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self.schedule_day), self.schedule_day, self.apply_sunday,
                self.apply_monday, self.apply_tuesday, self.apply_wednesday,
                self.apply_thursday, self.apply_friday, self.apply_saturday,
                self.apply_holiday, hash(self.start_date), hash(self.end_date))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleRule) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return ScheduleRule(
            self.schedule_day.duplicate(), self.schedule_day, self.apply_sunday,
            self.apply_monday, self.apply_tuesday, self.apply_wednesday,
            self.apply_thursday, self.apply_friday, self.apply_saturday,
            self.apply_holiday, self.start_date, self.end_date)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ScheduleRule:\n schedule_day: {}\n days applied: {}'.format(
            self.schedule_day.name, ', '.join(self.days_applied))


@lockable
class ScheduleRuleset(object):
    """A complete schedule assembled from DaySchedules and ScheduleRules.

    Properties:
        name
        default_day_schedule
        summer_designday_schedule
        winter_designday_schedule
        schedule_rules
        schedule_type
    """
    __slots__ = ('_name', '_default_day_schedule', '_summer_designday_schedule',
                 '_winter_designday_schedule', '_schedule_rules',
                 '_schedule_type', '_locked')
    _dow_text_to_int = {'sunday': 1, 'monday': 2, 'tuesday': 3, 'wednesday': 4,
                        'thursday': 2, 'friday': 3, 'saturday': 7}

    def __init__(self, name, default_day_schedule, summer_designday_schedule=None,
                 winter_designday_schedule=None, schedule_rules=None,
                 schedule_type=None):
        """Initialize Schedule Ruleset.

        Args:
            name: Text string for the schedule name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            default_day_schedule: A DaySchedule object that will be used for all
                days where there is no ScheduleRule applied.
            summer_designday_schedule: A DaySchedule object that will be used for
                the summer design day (used to size the cooling system).
            winter_designday_schedule: A DaySchedule object that will be used for
                the winter design day (used to size the heating system).
            schedule_rules: A list of ScheduleRule objects that note exceptions
                to the default_day_schedule.
            schedule_type: A ScheduleType object that will be used to validate
                schedule values against upper/lower limits and assign units to
                the schedule values.
        """
        self._locked = False  # unlocked by default
        self.name = name
        self.default_day_schedule = default_day_schedule
        self.summer_designday_schedule = summer_designday_schedule
        self.winter_designday_schedule = winter_designday_schedule
        self.schedule_rules = schedule_rules
        self.schedule_type = schedule_type

    @property
    def name(self):
        """Get or set the text string for schedule name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'schedule ruleset')

    @property
    def default_day_schedule(self):
        """Get or set the DaySchedule object that will be used by default."""
        return self._default_day_schedule

    @default_day_schedule.setter
    def default_day_schedule(self, schedule):
        assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
            'ScheduleRuleset default_day_schedule. Got {}.'.format(type(schedule))
        self._default_day_schedule = schedule

    @property
    def summer_designday_schedule(self):
        """Get or set the DaySchedule that will be used for the summer design day."""
        return self._summer_designday_schedule if self._summer_designday_schedule \
            is not None else self._default_day_schedule

    @summer_designday_schedule.setter
    def summer_designday_schedule(self, schedule):
        if schedule is not None:
            assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
                'ScheduleRuleset summer_designday_schedule. Got {}.'.format(
                    type(schedule))
        self._summer_designday_schedule = schedule

    @property
    def winter_designday_schedule(self):
        """Get or set the DaySchedule that will be used for the winter design day."""
        return self._winter_designday_schedule if self._winter_designday_schedule \
            is not None else self._default_day_schedule

    @winter_designday_schedule.setter
    def winter_designday_schedule(self, schedule):
        if schedule is not None:
            assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
                'ScheduleRuleset winter_designday_schedule. Got {}.'.format(
                    type(schedule))
        self._winter_designday_schedule = schedule

    @property
    def schedule_rules(self):
        """Get or set an array of ScheduleRules that note exceptions to the default."""
        return tuple(self._schedule_rules)

    @schedule_rules.setter
    def schedule_rules(self, rules):
        self._schedule_rules = self._check_schedule_rules(rules)

    @property
    def schedule_type(self):
        """Get or set a ScheduleType object used to assign units to schedule values."""
        return self._schedule_type

    @schedule_type.setter
    def schedule_type(self, schedule_type):
        if schedule_type is not None:
            assert isinstance(schedule_type, ScheduleType), 'Expected ScheduleType ' \
                'for ScheduleRuleset schedule_type. Got {}.'.format(type(schedule_type))
        self._schedule_type = schedule_type

    def add_rule(self, rule):
        """Add a ScheduleRule to this ScheduleRuleset.

        Args:
            rule: A ScheduleRule object to be applied to this ScheduleRuleset.
                ScheduleRule objects note the exceptions to the default_day_schedule.
        """
        self._check_rule(rule)
        self._schedule_rules.append(rule)

    def remove_rule(self, rule_index):
        """Remove a Schedule from the schedule by its index in schedule_rules.

        Args:
            rule_index: An integer for the index of the value to remove.
        """
        del self._schedule_rules[rule_index]

    def values_at_timestep(self, timestep=1, start_date=Date(1, 1), end_date=Date(12, 31),
                           start_dow='Sunday', holidays=None, leap_year=False):
        """Get a list of sequential schedule values over the year at a given timestep.

        Note that there are two possible ways that these values can be mapped to
        corresponding times. See the ScheduleDay.values_at_timestep() method
        documentation for a complete description of these two interpretations.

        Args:
            timestep: An integer for the number of steps per hour at which to return
                the resulting values.
            start_date: An optional ladybug Date object for when to start the list
                of values. Default: 1 Jan.
            end_date: An optional ladybug Date object for when to end the list
                of values. Default: 31 Dec.
            start_dow: An optional text string for the starting day of the week.
                Default: Sunday.
            holidays: An optional list of ladybug Date objects for the holidays. For
                any holiday in this list, schedule rules set to apply_holiday will
                take effect.
            leap_year: Boolean to note whether the generated values should be for a
                leap year (True) or a non-leap year (False). Default: False.
        """
        # get the values over the day for each of the ScheduleDay objects
        sch_day_vals = [rule.schedule_day.values_at_timestep(timestep)
                        for rule in self._schedule_rules]
        sch_day_vals.append(self.default_day_schedule.values_at_timestep(timestep))

        # ensure that everything is consistent across leap years
        if start_date.leap_year is not leap_year:
            start_date = Date(start_date.month, start_date.year, leap_year)
        if end_date.leap_year is not leap_year:
            end_date = Date(end_date.month, end_date.year, leap_year)

        # process the holidays if they are input
        if holidays is not None:
            hol_doy = []
            for hol in holidays:
                if hol.leap_year is not leap_year:
                    hol = Date(hol.month, hol.year, leap_year)
                hol_doy.append(hol.doy)
        else:
            hol_doy = []

        # process the start_dow into an integer.
        dow = self._dow_text_to_int[start_dow.lower()]

        # generate the full list of annual values
        if not leap_year:
            return self._get_sch_values(
                sch_day_vals, dow, start_date, end_date, hol_doy)
        else:
            return self._get_sch_values_leap_year(
                sch_day_vals, dow, start_date, end_date, hol_doy)

    def data_collection_at_timestep(self, timestep=1,
                                    start_date=Date(1, 1), end_date=Date(12, 31),
                                    start_dow='Sunday', holidays=None, leap_year=False):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

        Note that ladybug DataCollections always follow the "Ladybug Tools
        Interpretation" of date time values as noted in the
        ScheduleDay.values_at_timestep() documentation.

        Args:
            timestep: An integer for the number of steps per hour at which to make
                the resulting DataCollection.
            start_date: An optional ladybug Date object for when to start the
                DataCollection. Default: 1 Jan.
            end_date: An optional ladybug Date object for when to end the
                DataCollection. Default: 31 Dec.
            start_dow: An optional text string for the starting day of the week.
                Default: Sunday.
            holidays: An optional list of ladybug Date objects for the holidays. For
                any holiday in this list, schedule rules set to apply_holiday will
                take effect.
            leap_year: Boolean to note whether the generated values should be for a
                leap year (True) or a non-leap year (False). Default: False.
        """
        a_period = AnalysisPeriod(start_date.month, start_date.day, 0,
                                  end_date.month, end_date.day, 23, timestep, leap_year)
        if self.schedule_type is not None:
            data_type, unit = self.schedule_type.data_type, self.schedule_type.unit
        else:
            unit = 'unknown'
            data_type = GenericType('Unknown Data Type', unit)
        header = Header(data_type, unit, a_period, metadata={'schedule': self.name})
        values = self.values_at_timestep(timestep, start_date, end_date, start_dow,
                                         holidays, leap_year)
        return HourlyContinuousCollection(header, values)

    def _get_sch_values(self, sch_day_vals, dow, start_date, end_date, hol_doy):
        """Get a list of values over a date range for a typical year."""
        values = []
        for doy in range(start_date.doy, end_date.doy + 1):
            if dow > 7:  # reset the day of the week to sunday
                dow = 1
            if doy in hol_doy:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.apply_holiday and rule.does_rule_apply_doy(doy):
                        values.append(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.append(sch_day_vals[-1])
            else:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.does_rule_apply(doy, dow):
                        values.append(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.append(sch_day_vals[-1])
            dow += 1
        return values

    def _get_sch_values_leap_year(self, sch_day_vals, dow, start_date, end_date, hol_doy):
        """Get a list of values over a date range for a leap year."""
        values = []
        for doy in range(start_date.doy, end_date.doy + 1):
            if dow > 7:  # reset the day of the week to sunday
                dow = 1
            if doy in hol_doy:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.apply_holiday and rule.does_rule_apply_doy_leap_year(doy):
                        values.append(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.append(sch_day_vals[-1])
            else:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.does_rule_apply_leap_year(doy, dow):
                        values.append(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.append(sch_day_vals[-1])
            dow += 1
        return values

    def _check_schedule_rules(self, rules):
        """Check schedule_rules whenever they come through the setter."""
        if rules is None:
            return []
        if not isinstance(rules, list):
            try:
                rules = list(rules)
            except (ValueError, TypeError):
                raise TypeError('ScheduleRuleset schedule_rules must be iterable.')
        for rule in rules:
            self._check_rule(rule)
        return rules

    @staticmethod
    def _check_rule(rule):
        """Check that an individual rule is a ScheduleRule."""
        assert isinstance(rule, ScheduleRule), \
            'Expected ladybug Time for ScheduleRule. Got {}.'.format(type(rule))

    def __len__(self):
        return len(self._schedule_rules)

    def __getitem__(self, key):
        return self._schedule_rules[key]

    def __iter__(self):
        return iter(self._schedule_rules)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.name, hash(self.default_day_schedule),
                hash(self.summer_designday_schedule),
                hash(self.winter_designday_schedule), hash(self.schedule_type)) + \
            tuple(hash(rule) for rule in self.schedule_rules)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleRuleset) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return ScheduleDay(self.name, self.values, self.times, self.interpolate)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ScheduleRuleset:\n name: {}\n default_day: {}\n' \
            ' schedule_rules:\n {}'.format(self.name, self.default_day_schedule.name,
                                           '\n'.join(self._schedule_rules))
