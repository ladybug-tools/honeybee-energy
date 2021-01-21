# coding=utf-8
"""Schedule describing a single day."""
from __future__ import division

from .typelimit import ScheduleTypeLimit
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, tuple_with_length

from ladybug.datacollection import HourlyContinuousCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import Date, Time
from ladybug.datatype.generic import GenericType

from collections import deque
try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8


@lockable
class ScheduleDay(object):
    """Schedule for a single day.

    Note that a ScheduleDay cannot be assigned to Rooms, Shades, etc.  The ScheduleDay
    must be added to a ScheduleRuleset or a ScheduleRule and then the ScheduleRuleset
    can be applied to such objects.

    Args:
        identifier: Text string for a unique ScheduleDay ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        values: A list of floats or integers for the values of the schedule.
            The length of this list must match the length of the times list.
        times: A list of ladybug Time objects with the same length as the input
            values. Each time represents the time of day that the corresponding
            value begins to take effect. For example [0:00, 9:00, 17:00] in
            combination with the values [0, 1, 0] denotes a schedule value of
            0 from 0:00 to 9:00, a value of 1 from 9:00 to 17:00 and 0 from 17:00
            to the end of the day.
            If this input is None, the default will be a single time at 0:00,
            indicating the `values` input should be a single constant value that
            goes all of the way until the end of the day.
            Note that these times follow a different convention than EnergyPlus,
            which uses "time until" instead of "time of beginning".
        interpolate: Boolean to note whether values in between times should be
            linearly interpolated or whether successive values should take effect
            immediately upon the beginning time corresponding to them. Default: False

    Properties:
        * identifier
        * display_name
        * times
        * values
        * interpolate
        * is_constant
    """
    __slots__ = ('_identifier', '_display_name', '_values', '_times',
                 '_interpolate', '_parent', '_locked')

    _start_of_day = Time(0, 0)
    VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)

    def __init__(self, identifier, values, times=None, interpolate=False):
        """Initialize Schedule Day."""
        self._locked = False  # unlocked by default
        self._parent = None  # no parent ScheduleRuleset by default
        self.identifier = identifier
        self._display_name = None

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
    def identifier(self):
        """Get or set a text string for a unique schedule day identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'schedule day identifier')

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def values(self):
        """Get or set the schedule's numerical values, which correspond to the times."""
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
        """Boolean noting whether the schedule is representable with a single value."""
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

    def remove_value(self, value_index):
        """Remove a value from the schedule by its index.

        Args:
            value_index: An integer for the index of the value to remove.
        """
        assert len(self._values) > 1, 'ScheduleDay must have at least one value.'
        assert value_index != 0, 'ScheduleDay cannot remove value at index 0.'
        if value_index < 0:
            value_index = len(self._values) + value_index
        self._values = tuple(x for i, x in enumerate(self._values) if i != value_index)
        self._times = tuple(x for i, x in enumerate(self._times) if i != value_index)

    def remove_value_by_time(self, time):
        """Remove a value from the schedule by its time in the times property.

        Args:
            time: An ladybug Time for the time and the value to remove.
        """
        self.remove_value(self._times.index(time))

    def replace_value(self, value_index, new_value):
        """Replace an existing value in the schedule with a new one.

        Args:
            value_index: An integer for the index of the value to replace.
            new_value: A number for the new value to use at the given index.
        """
        val_list = list(self._values)
        val_list[value_index] = self._check_value(new_value)
        self._values = tuple(val_list)

    def replace_value_by_time(self, time, new_value):
        """Replace an existing value in the schedule using its time.

        Args:
            time: An ladybug Time for the time and the value to replace.
            new_value: A number for the new value to use at the given time.
        """
        self.replace_value(self._times.index(time), new_value)

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
        assert timestep in self.VALIDTIMESTEPS, 'ScheduleDay timestep "{}" is invalid.' \
            ' Must be one of the following:\n{}'.format(timestep, self.VALIDTIMESTEPS)
        values = []
        minute_delta = 60 / timestep
        mod = 0  # track the minute of day through iteration
        time_index = 1  # track the index of the next time of change
        until_mod = self._get_until_mod(time_index)  # get the mod of the next change
        if not self.interpolate:
            for _ in range(24 * timestep):
                if mod >= until_mod:
                    time_index += 1
                    until_mod = self._get_until_mod(time_index)
                values.append(self._values[time_index - 1])
                mod += minute_delta
        else:
            for _ in range(24 * timestep):
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

    def data_collection(self, date=Date(1, 1), schedule_type_limit=None, timestep=1):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

        Note that ladybug DataCollections always follow the "Ladybug Tools
        Interpretation" of date time values as noted in the values_at_timestep
        documentation.

        Args:
            date: A ladybug Date object for the day of the year the DataCollection
                is representing. (Default: 1 Jan)
            schedule_type_limit: A ScheduleTypeLimit object that describes the schedule,
                which will be used to make the header for the DataCollection. If None,
                a generic "Unknown" type will be used. (Default: None)
            timestep: An integer for the number of steps per hour at which to make
                the resulting DataCollection.
        """
        assert isinstance(date, Date), \
            'Expected ladybug Date. Got {}.'.format(type(date))
        if schedule_type_limit is not None:
            assert isinstance(schedule_type_limit, ScheduleTypeLimit), 'Expected ' \
                'Honeybee ScheduleTypeLimit. Got {}.'.format(type(schedule_type_limit))
            d_type = schedule_type_limit.data_type
            unit = schedule_type_limit.unit
        else:
            d_type = GenericType('Unknown Data Type', 'unknown')
            unit = 'unknown'
        a_period = AnalysisPeriod(date.month, date.day, 0, date.month, date.day, 23,
                                  timestep, date.leap_year)
        header = Header(d_type, unit, a_period, metadata={'schedule': self.identifier})
        return HourlyContinuousCollection(header, self.values_at_timestep(timestep))

    def shift_by_step(self, step_count=1, timestep=1):
        """Get a version of this object where the values are shifted in time.
        
        This is useful when attempting to derive a set of diversified schedules
        from a single average schedule.

        Args:
            step_count: An integer for the number of timesteps at which the schedule
                will be shifted. Positive values indicate a shift of values forward
                in time while negative values indicate a shift backwards in
                time. (Default: 1).
            timestep: An integer for the number of timesteps per hour at which the
                shifting is occurring. This must be a value between 1 and 60, which
                is evenly divisible by 60. 1 indicates that each step is an hour
                while 60 indicates that each step is a minute. (Default: 1)
        """
        value_deque = deque(self.values_at_timestep(timestep))
        value_deque.rotate(step_count)
        new_id = '{}_Shift_{}mins'.format(
            self.identifier, int((60 / timestep) * step_count))
        return ScheduleDay.from_values_at_timestep(new_id, list(value_deque), timestep)

    @classmethod
    def from_values_at_timestep(cls, identifier, values, timestep=1,
                                remove_repeated=True):
        """Make a ScheduleDay from a list of values at a certain timestep.

        Args:
            identifier: Text string for a unique Schedule ID. Must be < 100 characters
                and not contain any EnergyPlus special characters. This will be used to
                identify the object across a model and in the exported IDF.
            values: A list of numerical values with a length equal to 24 * timestep.
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

        return cls(identifier, schedule_values, schedule_times)

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
    def from_dict(cls, data):
        """Create a ScheduleDay from a dictionary.

        Args:
            data: ScheduleDay dictionary following the format below.

        .. code-block:: python

            {
            "type": 'ScheduleDay',
            "identifier": 'Office_Occ_900_1700',
            "display_name": 'Office Occupancy',
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

        new_obj = cls(data['identifier'], data['values'], times, interpolate)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, schedule_type_limit=None):
        """IDF string representation of ScheduleDay object.

        Args:
            schedule_type_limits: Optional ScheduleTypeLimit object, which will
                be written into the IDF string in order to validate the values
                within the schedule during the EnergyPlus run.
        """
        fields = [self.identifier, ''] if schedule_type_limit is None else \
            [self.identifier, schedule_type_limit.identifier]
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
        base['identifier'] = self.identifier
        base['values'] = self.values
        base['times'] = [time.to_array() for time in self.times]
        base['interpolate'] = self.interpolate
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    @staticmethod
    def average_schedules(identifier, schedules, weights=None, timestep_resolution=1):
        """Create a ScheduleDay that is a weighted average between other ScheduleDays.

        Args:
            identifier: Text string for a unique ID for the new unique ScheduleDay.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a
                model and in the exported IDF.
            schedules: A list of ScheduleDay objects that will be averaged together
                to make a new ScheduleDay.
            weights: An optional list of fractional numbers with the same length
                as the input schedules that sum to 1. These will be used to weight
                each of the ScheduleDay objects in the resulting average schedule.
                If None, the individual schedules will be weighted equally.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        # check the inputs
        assert isinstance(schedules, (list, tuple)), 'Expected a list of ScheduleDay ' \
            'objects for average_schedules. Got {}.'.format(type(schedules))
        if weights is None:
            weight = 1 / len(schedules)
            weights = [weight for i in schedules]
        else:
            weights = tuple_with_length(weights, len(schedules), float,
                                        'average schedules weights')
            assert sum(weights) == 1, 'Average schedule weights must sum to 1. ' \
                'Got {}.'.format(sum(weights))

        # create a weighted average list of values
        all_values = [sch.values_at_timestep(timestep_resolution) for sch in schedules]
        sch_vals = [sum([val * weights[i] for i, val in enumerate(values)])
                    for values in zip(*all_values)]

        # return the final list
        return ScheduleDay.from_values_at_timestep(identifier, sch_vals, timestep_resolution)

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
        return (self.identifier,) + self.values + tuple(hash(t) for t in self.times) + \
            (self.interpolate,)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleDay) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = ScheduleDay(self.identifier, self.values, self.times, self.interpolate)
        new_obj._display_name = self._display_name
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return self.to_idf()
