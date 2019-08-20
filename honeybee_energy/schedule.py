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

from collections import Iterable


@lockable
class ScheduleDay(object):
    """Schedule for a single day.

    Note that a ScheduleDay cannot be assigned to Rooms, Shades, etc.  The ScheduleDay
    must be added to a ScheduleRuleSet or a ScheduleRule and then the ScheduleRuleSet
    can be applied to such objects.

    Properties:
        name
        times
        values
        interpolate
    """
    __slots__ = ('_name', '_values', '_times', '_interpolate', '_locked')
    _end_of_day = Time(23, 59)
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
                value is until. If this input is None, the default will be a single
                time at 23:59, indicating the `values` input should be a single constant
                value that goes all of the way until the end of the day.
                Note that, though EnergyPlus uses the time 24:00, Ladybug Tools
                (and Python) use 23:59 to denote the latest time of the day.
            interpolate: Boolean to note whether values in between times should be
                linearly interpolated or whether successive values should take effect
                immediately after the previous "time until" is passed. Default: False
        """
        self._locked = False  # unlocked by default
        self.name = name

        # assign the times and values
        if times is None:
            self._times = (self._end_of_day,)
        else:
            if not isinstance(times, tuple):
                try:
                    times = tuple(times)
                except (ValueError, TypeError):
                    raise TypeError('ScheduleDay times must be iterable.')
            for time in times:
                assert isinstance(time, Time), \
                    'Expected ladybug Time for ScheduleDay. Got {}.'.format(type(time))
            self._times = times
        self.values = values

        # if times are not ordered chronologically, sort them
        if not self._are_chronological(times):
            self._times, self._values = zip(*sorted(zip(self._times, self._values)))

        # ensure that the schedule always goes to the end of the day
        assert times[-1] == self._end_of_day, \
            'Schedule Day times must go until 23:59. Got {}.'.format(times[-1])

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

    def values_at_timestep(self, timestep=1):
        """Get a list of schedule values over the day at a given timestep.

        Note that the first value in the returned list here corresponds to the time 0:00
        but EnergyPlus reports schedule results with the first value as the timestep
        after 0:00. Furthermore, when the input timestep here is 1 (one value per hour),
        this method treats the "time until" in the schedule's times as the start of the
        next interval, which is different than EnergyPlus.

        For example, if an office schedule is set to be occupied from 9:00 until 17:00,
        the output from this method will show 9:00 as occupied but 17:00 as unoccupied
        while the EnergyPlus output will report 9:00 as unoccupied and 17:00 as occupied
        (note that, in the EnergyPlus calculation, the simulation timestep immediatly
        after 9:00 is occupied and immediately after 17:00 is unoccupied).

        Ultimately, this means that the output of this method is a better hourly
        representation of how EnergyPlus interprets the schedule but it is not the
        exact output that EnergyPlus will report when hourly schedule values are
        requested. To get the schedule values exactly how EnergyPlus reports it, the
        values_at_ep_timestep() method should be used.

        Args:
            timestep: An integer for the number of steps per hour at which to return
                the resulting values.
        """
        if not self.interpolate:
            values = []
            minute_delta = 60 / timestep
            t_i = 0  # track the index of the schedule.values used at each step
            mod = 0  # track the minute of day through iteration
            advance_function = self._advance_on_step if timestep == 1 else \
                self._advance_after_step
            for step in range(24 * timestep):
                t_i = advance_function(mod, t_i)
                values.append(self._values[t_i])
                mod += minute_delta
        else:
            values = self._interpolate_to_timestep(timestep)
            if timestep == 1:  # treat "time until" in times as start of next interval
                values.pop(0)
                values.append(self._values[-1])
        return values

    def values_at_ep_timestep(self, timestep=1):
        """Get a list of schedule values as EnergyPlus reports them in its outputs.

        Note that this means the first value corresponds to the timestep after 0:00
        (ie. 1:00 if the timestep is 1, 0:10 if the timestep is 6, etc.). Also note
        that EnergyPlus's representation of schedules at a timestep of 1 can be
        misleading (see values_at_timestep method documentation for more information).

        Args:
            timestep: An integer for the number of steps per hour at which to return
                the resulting values.
        """
        if not self.interpolate:
            values = []
            minute_delta = 60 / timestep
            t_i = 0
            mod = minute_delta
            for step in range(24 * timestep):
                t_i = self._advance_after_step(mod, t_i)
                try:
                    values.append(self._values[t_i])
                except IndexError:  # last timestep in hourly data
                    values.append(self._values[t_i - 1])
                mod += minute_delta
        else:
            values = self._interpolate_to_timestep(timestep)
            values.pop(0)  # delete the value at 0:00
            values.append(self._values[-1])  # add the last value for 24:00
        return values

    def data_collection_at_timestep(self, date, schedule_type, timestep=1):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

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
        schedule_times = []
        minute_delta = 60 / timestep
        mod = minute_delta
        if remove_repeated:
            schedule_values = [values[0]]
            for i in range(1, n_vals):
                if values[i] != schedule_values[-1]:  # non-repeated value
                    time_at_change = Time.from_mod(mod) if timestep == 1 else \
                        Time.from_mod(mod - minute_delta)
                    schedule_times.append(time_at_change)
                    schedule_values.append(values[i])
                mod += minute_delta
        else:
            schedule_values = values  # we don't care if there are repeated values
            for i in range(1, n_vals):
                schedule_times.append(Time.from_mod(mod))
                mod += minute_delta
        schedule_times.append(cls._end_of_day)

        return cls(name, schedule_values, schedule_times)

    @classmethod
    def from_idf(cls, idf_string):
        """Create a ScheduleDay from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                Schedule:Day:Interval.
        """
        ep_strs = parse_idf_string(idf_string, 'Schedule:Day:Interval,')
        interpolate = False if ep_strs[2] == 'No' or ep_strs[2] == '' else True
        length = len(ep_strs)
        values = tuple(float(ep_strs[i]) for i in range(4, length + 1, 2))
        times = []
        for i in range(3, length, 2):
            try:
                times.append(Time.from_time_string(ep_strs[i]))
            except ValueError:  # 24:00
                times.append(cls._end_of_day)
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
        pass

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleDay from a dictionary.

        Args:
            data: {
                "type": 'ScheduleDay',
                "name": 'Office Occupancy',
                "values": [0, 1, 0],
                "times": [(9, 0), (17, 0), (23 59)],
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
            fields.append(self._times[i])
            comments.append('time %s {hh:mm}' % count)
            fields.append(self._values[i])
            comments.append('value until time %s' % count)
        fields[-2] = '24:00'  # convert from ladybug time to IDF time
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
            assert isinstance(time, Time), \
                'Expected ladybug Time for ScheduleDay. Got {}.'.format(type(time))
        assert len(times) == len(self._values), \
            'Length of values list must match length of datetimes list. {} != {}'.format(
                len(times), len(self._values))
        if not self._are_chronological(times):
            times, self._values = zip(*sorted(zip(times, self._values)))
        # ensure that the schedule always goes to the end of the day
        assert times[-1] == self._end_of_day, \
            'Schedule Day times must go until 23:59. Got {}.'.format(times[-1])
        return times

    def _interpolate_to_timestep(self, timestep):
        """Get a list of schedule values interpolated to a timestep as E+ does.

        Note that this method always returns values starting from 0:00 and going
        to the timestep before midnight of the following day.
        """
        values = []
        minute_delta = 60 / timestep
        t_i = 0
        mod = 0
        for step in range(24 * timestep):
            new_t_i = self._advance_on_step(mod, t_i)
            if new_t_i != t_i:
                i_step = 0
                delta = self._values[new_t_i] - self._values[t_i]
                new_mod = self._times[new_t_i].mod
                if new_mod == 1439:  # correct for E+'s use of 24:00
                    new_mod = 1440
                n_steps = (new_mod - self._times[t_i].mod) / minute_delta
                values.append(self._values[t_i])
                t_i = new_t_i
            elif t_i == 0:
                values.append(self._values[t_i])
            else:
                i_step += 1
                values.append(
                    self._values[t_i - 1] + ((i_step / n_steps) * delta))
            mod += minute_delta
        return values

    def _advance_on_step(self, mod, time_index):
        """Advance a time_index to a new value on the step it changes in self.times.
        """
        if mod >= self._times[time_index].mod:
            return time_index + 1
        return time_index

    def _advance_after_step(self, mod, time_index):
        """Advance a time_index to a new value after the step it changes in self.times.
        """
        if mod > self._times[time_index].mod:
            return time_index + 1
        return time_index

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
