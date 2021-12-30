# coding=utf-8
"""Annual schedule defined by a list of values at a fixed interval or timestep."""
from __future__ import division

from .typelimit import ScheduleTypeLimit
from ..reader import parse_idf_string, clean_idf_file_contents
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, float_in_range, int_in_range, \
    tuple_with_length

from ladybug.datacollection import HourlyContinuousCollection
from ladybug.header import Header
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import Date, DateTime
from ladybug.datatype.generic import GenericType
from ladybug.futil import write_to_file, csv_to_matrix

import os
import re
try:
    from collections.abc import Iterable  # python < 3.7
except ImportError:
    from collections import Iterable  # python >= 3.8
try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


@lockable
class ScheduleFixedInterval(object):
    """An annual schedule defined by a list of values at a fixed interval or timestep.

    Args:
        identifier: Text string for a unique Schedule ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        values: A list of values occuring at a fixed interval over the simulation.
            Typically, this should be a list of 8760 values for each hour of the
            year but it can be a shorter list if you don't plan on using it in
            an annual simulation. In this case, the start_date should probably be
            different than the default 1 Jan (it should instead be the start date
            of your simulation). This list can also have a length much greater
            than 8760 if a timestep greater than 1 is used.
        schedule_type_limit: A ScheduleTypeLimit object that will be used to
            validate schedule values against upper/lower limits and assign units
            to the schedule values. If None, no validation will occur.
        timestep: An integer for the number of steps per hour that the input
            values correspond to.  For example, if each value represents 30
            minutes, the timestep is 2. For 15 minutes, it is 4. Default is 1,
            meaning each value represents a single hour. Must be one of the
            following: (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60).
        start_date: A ladybug Date object to note when the input values begin
            to take effect. Default is 1 Jan for a non-leap year. Note that this
            default usually should not be changed unless you plan to run a
            simulation that is much shorter than a year and/or you plan to run
            the simulation for a leap year.
        placeholder_value: A value that will be used for all times not covered
            by the input values. Typically, your simulation should not need to
            use this value if the input values completely cover the simulation
            period. However, a default value may still be necessary for EnergyPlus
            to run. Default: 0.
        interpolate: Boolean to note whether values in between intervals should be
            linearly interpolated or whether successive values should take effect
            immediately upon the beginning time corresponding to them. Default: False

    Properties:
        * identifier
        * display_name
        * values
        * schedule_type_limit
        * timestep
        * start_date
        * placeholder_value
        * interpolate
        * end_date_time
        * is_leap_year
        * is_constant
        * data_collection
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_values', '_schedule_type_limit',
                 '_start_date', '_placeholder_value', '_timestep', '_interpolate',
                 '_locked', '_user_data')
    _schedule_file_comments = \
        ('schedule name', 'schedule type limits', 'file name', 'column number',
         'rows to skip', 'number of hours of data', 'column separator',
         'interpolate to timestep', 'minutes per item')
    VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)

    def __init__(self, identifier, values, schedule_type_limit=None, timestep=1,
                 start_date=Date(1, 1), placeholder_value=0, interpolate=False):
        """Initialize Schedule FixedInterval."""
        self._locked = False  # unlocked by default

        # set all of the properties that impact how many values can be assigned
        self._timestep = int_in_range(timestep, 1, 60, 'schedule timestep')
        assert self._timestep in self.VALIDTIMESTEPS, 'ScheduleFixedInterval timestep ' \
            '"{}" is invalid. Must be one of the following:\n{}'.format(
                timestep, self.VALIDTIMESTEPS)
        start_date = Date(1, 1) if start_date is None else start_date
        assert isinstance(start_date, Date), 'Expected ladybug Date for ' \
            'ScheduleFixedInterval start_date. Got {}.'.format(type(start_date))
        self._start_date = start_date

        # set the values and all properties that can be re-set
        self.identifier = identifier
        self._display_name = None
        self.values = values
        self.schedule_type_limit = schedule_type_limit
        self.placeholder_value = placeholder_value
        self.interpolate = interpolate
        self._user_data = None

    @property
    def identifier(self):
        """Get or set the text string for unique schedule identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(
            identifier, 'schedule fixed interval identifier')

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
        """Get or set the schedule's numerical values, which occur at a fixed interval.
        """
        return self._values

    @values.setter
    def values(self, values):
        self._values = self._check_values(values)

    @property
    def schedule_type_limit(self):
        """Get or set a ScheduleTypeLimit object used to assign units to schedule values.
        """
        return self._schedule_type_limit

    @schedule_type_limit.setter
    def schedule_type_limit(self, schedule_type):
        if schedule_type is not None:
            assert isinstance(schedule_type, ScheduleTypeLimit), 'Expected ' \
                'ScheduleTypeLimit for ScheduleRuleset schedule_type_limit. ' \
                'Got {}.'.format(type(schedule_type))
        self._schedule_type_limit = schedule_type

    @property
    def placeholder_value(self):
        """Get or set the value to be used for all times not covered by the input values.
        """
        return self._placeholder_value

    @placeholder_value.setter
    def placeholder_value(self, value):
        self._placeholder_value = float_in_range(
            value, input_name='schedule fixed interval placeholder_value')

    @property
    def interpolate(self):
        """Get or set a boolean noting whether values should be interpolated."""
        return self._interpolate

    @interpolate.setter
    def interpolate(self, interpolate):
        self._interpolate = bool(interpolate)

    @property
    def timestep(self):
        """Get the integer for the schedule's number of steps per hour."""
        return self._timestep

    @property
    def start_date(self):
        """Get the ladybug Date object noting when the the input values take effect."""
        return self._start_date

    @property
    def end_date_time(self):
        """Get a ladybug DateTime object for the end time of the schedule's values."""
        num_hoys = (len(self._values) - 1) / self.timestep
        end_hoy = (self.start_date.doy - 1) * 24 + num_hoys
        if not self.is_leap_year:
            end_dt = DateTime.from_hoy(end_hoy) if end_hoy < 8760 else \
                DateTime.from_hoy(end_hoy - 8760)
        else:
            end_dt = DateTime.from_hoy(end_hoy, True) if end_hoy < 8784 else \
                DateTime.from_hoy(end_hoy - 8760, True)
        return end_dt

    @property
    def is_leap_year(self):
        """Get a boolean noting whether the schedule is over a leap year.

        Note that this property originates from the leap_year property on the
        input start_date.
        """
        return self._start_date.leap_year

    @property
    def is_constant(self):
        """Boolean noting whether the schedule is representable with a single value."""
        val_1 = self._values[0]
        return all(element == val_1 for element in self._values)

    @property
    def data_collection(self):
        """DataCollection of schedule values at this schedule's start_date and timestep.
        """
        end_dt = self.end_date_time
        a_period = AnalysisPeriod(self.start_date.month, self.start_date.day, 0,
                                  end_dt.month, end_dt.day, end_dt.hour, self.timestep,
                                  self.is_leap_year)
        data_type, unit = self._get_lb_data_type_and_unit()
        header = Header(data_type, unit, a_period, metadata={'schedule': self.identifier})
        return HourlyContinuousCollection(header, self._values)
    
    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    def values_at_timestep(
            self, timestep=1, start_date=None, end_date=None):
        """Get a list of sequential schedule values over the year at a given timestep.

        Note that there are two possible ways that these values can be mapped to
        corresponding times:

        * The EnergyPlus interpretation that uses "time until"
        * The Ladybug Tools interpretation that uses "time of beginning"

        The EnergyPlus interpretation should be used when aligning the schedule
        with EnergyPlus results while the Ladybug Tools interpretation should be
        used when aligning the schedule with ladybug DataCollections or other
        ladybug objects. See the ScheduleDay.values_at_timestep method
        documentation for a complete description of these two interpretations.

        Args:
            timestep: An integer for the number of steps per hour at which to return
                the resulting values.
            start_date: An optional ladybug Date object for when to start the list
                of values. Default: 1 Jan with a leap year equal to self.start_date.
            end_date: An optional ladybug Date object for when to end the list
                of values. Default: 31 Dec with a leap year equal to self.start_date.
        """
        # ensure that the input start_date and end_date are valid
        if start_date is None:
            start_date = Date(1, 1, self.is_leap_year)
        else:
            if start_date.leap_year is not self.is_leap_year:
                start_date = Date(start_date.month, start_date.day, self.is_leap_year)
        if end_date is None:
            end_date = Date(12, 31, self.is_leap_year)
        else:
            if end_date.leap_year is not self.is_leap_year:
                end_date = Date(end_date.month, end_date.day, self.is_leap_year)
        assert start_date <= end_date, 'ScheduleFixedInterval values_at_timestep()' \
            'start_date must come before end_date. {} comes after {}.'.format(
                start_date, end_date)

        # convert the schedule's values to the desired timestep
        timestep = int_in_range(timestep, 1, 60, 'schedule timestep')
        assert timestep in self.VALIDTIMESTEPS, 'ScheduleFixedInterval timestep ' \
            '"{}" is invalid. Must be one of the following:\n{}'.format(
                timestep, self.VALIDTIMESTEPS)
        if timestep == self.timestep:
            vals_at_step = list(self._values)
        elif timestep < self.timestep:
            assert self.timestep % timestep == 0, \
                'Schedule timestep({}) must be evenly divisible by target timestep({})' \
                .format(self.timestep, timestep)
            vals_at_step = []
            ind = 0
            step_ratio = self.timestep / timestep
            for _ in xrange(int(len(self._values) / step_ratio)):
                vals_at_step.append(self._values[int(ind)])
                ind += step_ratio
        else:
            assert timestep % self.timestep == 0, \
                'Target timestep({}) must be evenly divisible by schedule timestep({})' \
                .format(timestep, self.timestep)
            vals_at_step = []
            if self.interpolate:
                data_len = len(self._values)
                for d in xrange(data_len):
                    for _v in self._xxrange(self[d], self[(d + 1) % data_len], timestep):
                        vals_at_step.append(_v)
            else:
                n_step = int(timestep / self.timestep)
                for val in self._values:
                    for _ in xrange(n_step):
                        vals_at_step.append(val)

        # build up the full list of values accounting for start and end dates
        end_dt = self.end_date_time
        if self.start_date.doy <= end_dt.doy:
            start_filler = []
            end_filler = []
            if start_date < self.start_date:
                num_vals = int((self.start_date.doy - start_date.doy) * 24 * timestep)
                start_filler = [self.placeholder_value for i in xrange(num_vals)]
            elif start_date > self.start_date:
                start_i = int((start_date.doy - self.start_date.doy) * 24 * timestep)
                vals_at_step = vals_at_step[start_i:]
            if ((end_dt.int_hoy + 1) / 24) < end_date.doy:
                num_vals = int((end_date.doy * 24 * timestep) - 1 - (
                    end_dt.hoy * timestep))
                end_filler = [self.placeholder_value for i in xrange(num_vals)]
            elif ((end_dt.int_hoy + 1) / 24) > end_date.doy:
                end_diff = int((end_dt.hoy * timestep) - (end_date.doy * 24 * timestep))
                end_i = len(vals_at_step) - end_diff - 1
                vals_at_step = vals_at_step[:end_i]
            return start_filler + vals_at_step + end_filler
        else:
            n_dpy = 365 if not self.is_leap_year else 366
            start_yr_i = int((n_dpy - self.start_date.doy + 1) * 24 * timestep)
            n_mid = (8760 * timestep) - len(vals_at_step)
            end_vals = vals_at_step[:start_yr_i]
            start_vals = vals_at_step[start_yr_i:]
            mid_vals = [self.placeholder_value for i in xrange(n_mid)]
            all_vals = start_vals + mid_vals + end_vals
            start_i = (start_date.doy - 1) * 24 * timestep
            end_i = end_date.doy * 24 * timestep
            return all_vals[start_i:end_i]

    def data_collection_at_timestep(
            self, timestep=1, start_date=Date(1, 1), end_date=Date(12, 31)):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

        Note that ladybug DataCollections always follow the "Ladybug Tools
        Interpretation" of date time values as noted in the
        ScheduleDay.values_at_timestep documentation.

        Args:
            timestep: An integer for the number of steps per hour at which to make
                the resulting DataCollection.
            start_date: An optional ladybug Date object for when to start the
                DataCollection. Default: 1 Jan on a non-leap year.
            end_date: An optional ladybug Date object for when to end the
                DataCollection. Default: 31 Dec on a non-leap year.
        """
        a_period = AnalysisPeriod(start_date.month, start_date.day, 0,
                                  end_date.month, end_date.day, 23, timestep,
                                  self.is_leap_year)
        data_type, unit = self._get_lb_data_type_and_unit()
        header = Header(data_type, unit, a_period, metadata={'schedule': self.identifier})
        values = self.values_at_timestep(timestep, start_date, end_date)
        return HourlyContinuousCollection(header, values)

    @classmethod
    def from_idf(cls, idf_string, type_idf_string=None):
        """Create a ScheduleFixedInterval from an EnergyPlus IDF text strings.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                Schedule:File.
            type_idf_string: An optional text string for the ScheduleTypeLimits.
                If None, the resulting schedule will have no ScheduleTypeLimit.
        """
        # process the schedule inputs
        sch_fields = parse_idf_string(idf_string, 'Schedule:File')
        schedule_type = ScheduleTypeLimit.from_idf(type_idf_string) if type_idf_string \
            is not None else None
        timestep = 60 / int(sch_fields[8]) if sch_fields[8] != '' else 1
        start_date = Date(1, 1, False) if sch_fields[5] == '8760' else Date(1, 1, True)
        interpolate = False if sch_fields[7] == 'No' or sch_fields[7] == '' else True

        # load the data from the CSV file referenced in the string
        assert os.path.isfile(sch_fields[2]), \
            'CSV Schedule:File "{}" was not found on this system.'.format(sch_fields[2])
        all_data = csv_to_matrix(sch_fields[2])
        transposed_data = tuple(zip(*all_data))
        csv_data = (float(x) for x in
                    transposed_data[int(sch_fields[3]) - 1][int(sch_fields[4]):])

        return cls(sch_fields[0], csv_data, schedule_type, timestep, start_date,
                   0, interpolate)

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleFixedInterval from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: ScheduleFixedInterval dictionary following the format below.

        .. code-block:: python

            {
            "type": 'ScheduleFixedInterval',
            "identifier": 'Awning_Transmittance_X45NF23U',
            "display_name": 'Automated Awning Transmittance',
            "values": [], # list of numbers for the values of the schedule
            "schedule_type_limit": {}, # ScheduleTypeLimit dictionary representation
            "timestep": 1, # Integer for the timestep of the schedule
            "start_date": (1, 1), # Date dictionary representation
            "placeholder_value": 0, # Number for the values out of range
            "interpolate": False # Boolean noting whether to interpolate between values
            }
        """
        assert data['type'] == 'ScheduleFixedInterval', \
            'Expected ScheduleFixedInterval. Got {}.'.format(data['type'])

        sched_type = None
        if 'schedule_type_limit' in data and data['schedule_type_limit'] is not None:
            sched_type = ScheduleTypeLimit.from_dict(data['schedule_type_limit'])
        timestep = 1
        if 'timestep' in data and data['timestep'] is not None:
            timestep = data['timestep']
        start_date = Date(1, 1)
        if 'start_date' in data and data['start_date'] is not None:
            start_date = Date.from_array(data['start_date'])
        placeholder_value = 0
        if 'placeholder_value' in data and data['placeholder_value'] is not None:
            placeholder_value = data['placeholder_value']
        interpolate = False
        if 'interpolate' in data and data['interpolate'] is not None:
            interpolate = data['interpolate']

        new_obj = cls(data['identifier'], data['values'], sched_type, timestep,
                      start_date, placeholder_value, interpolate)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_type_limits):
        """Create a ScheduleFixedInterval from an abridged dictionary.

        Args:
            data: ScheduleFixedIntervalAbridged dictionary with format below.
            schedule_type_limits: A dictionary with identifiers of schedule type limits
                as keys and Python schedule type limit objects as values.

        .. code-block:: python

            {
            "type": 'ScheduleFixedIntervalAbridged',
            "identifier": 'Awning_Transmittance_X45NF23U',
            "display_name": 'Automated Awning Transmittance',
            "values": [], # list of numbers for the values of the schedule
            "schedule_type_limit": "", # ScheduleTypeLimit identifier
            "timestep": 1, # Integer for the timestep of the schedule
            "start_date": (1, 1), # Date dictionary representation
            "placeholder_value": 0, # Number for the values out of range
            "interpolate": False # Boolean noting whether to interpolate between values
            }
        """
        assert data['type'] == 'ScheduleFixedIntervalAbridged', \
            'Expected ScheduleFixedIntervalAbridged. Got {}.'.format(data['type'])

        data = data.copy()  # copy original dictionary so we don't edit it
        typ_lim = None
        if 'schedule_type_limit' in data:
            typ_lim = data['schedule_type_limit']
            data['schedule_type_limit'] = None
        data['type'] = 'ScheduleFixedInterval'
        schedule = cls.from_dict(data)
        schedule.schedule_type_limit = schedule_type_limits[typ_lim] if \
            typ_lim is not None else None
        if 'display_name' in data and data['display_name'] is not None:
            schedule.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            schedule.user_data = data['user_data']
        return schedule

    def to_idf(self, schedule_directory, include_datetimes=False):
        """IDF string representation of the schedule.

        Note that this method does both the production of the IDF string
        representation of the Schedule:File as well as the actual writing of
        the schedule to a CSV format that can be read in by EnergyPlus.

        Args:
            schedule_directory: [Required] Text string of a path to a folder on this
                machine to which the CSV version of the file will be written.
            include_datetimes: Boolean to note whether a column of datetime objects
                should be written into the CSV alongside the data. Default is False,
                which will keep the resulting CSV lighter in file size but you may
                want to include such datetimes in order to verify that values align with
                the expected timestep. Note that the included datetimes will follow the
                EnergyPlus interpretation of aligning values to timesteps in which case
                the timestep to which the value is matched means that the value was
                utilized over all of the previous timestep.

        Returns:
            schedule_file --
            Text string representation of the Schedule:File describing this schedule.
        """
        # gather all of the data to be written into the CSV
        sched_data = [str(val) for val in self.values_at_timestep(self.timestep)]
        if include_datetimes:
            sched_a_per = AnalysisPeriod(timestep=self.timestep,
                                         is_leap_year=self.is_leap_year)
            sched_data = ('{},{}'.format(dt, val) for dt, val in
                          zip(sched_a_per.datetimes, sched_data))
        file_path = os.path.join(schedule_directory,
                                 '{}.csv'.format(self.identifier.replace(' ', '_')))

        # write the data into the file
        write_to_file(file_path, ',\n'.join(sched_data), True)

        # generate the IDF strings
        shc_typ = self._schedule_type_limit.identifier if \
            self._schedule_type_limit is not None else ''
        col_num = 1 if not include_datetimes else 2
        num_hrs = 8760 if not self.is_leap_year else 8784
        interp = 'No' if not self.interpolate else 'Yes'
        min_per_step = int(60 / self.timestep)
        fields = (self.identifier, shc_typ, file_path, col_num, 0, num_hrs, 'Comma',
                  interp, min_per_step)
        schedule_file = generate_idf_string('Schedule:File', fields,
                                            self._schedule_file_comments)
        return schedule_file

    def to_idf_compact(self):
        """IDF string representation of the schedule as a Schedule:Compact.

        Schedule:Compact strings contain all of the schedule values and can be
        written directly into IDF files. So they are sometimes preferable to
        Schedule:Files objects when it's important that all simulation data be
        represented in a single IDF file. However, such a representation of the
        schedule often prevents the IDF from being read by programs such as the
        IDFEditor and it can increase the overall size of the schedule in the
        resulting files by an order of magnitude.
        """
        # initialize the list of IDF properties
        shc_typ = self._schedule_type_limit.identifier if \
            self._schedule_type_limit is not None else ''
        fields = [self.identifier, shc_typ]

        # loop through all datetimes of the schedule and append them.
        sched_data = self.values_at_timestep(self.timestep)
        datetimes = AnalysisPeriod(timestep=self.timestep,
                                   is_leap_year=self.is_leap_year).datetimes
        day = 0
        for val, d_t in zip(sched_data, datetimes):
            if d_t.day != day:
                fields.append('Through: {}/{}'.format(d_t.month, d_t.day))
                fields.append('For: AllDays')
                day = d_t.day
            hour = 0 if d_t.hour == 24 and d_t.minute != 0 else d_t.hour + 1
            fields.append('Until: {}:{}'.format(hour, d_t.strftime('%M')))
            fields.append(val)

        # return the IDF string
        return generate_idf_string('Schedule:Compact', fields)

    def to_dict(self, abridged=False):
        """ScheduleFixedInterval dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifier of the ScheduleTypeLimit.
                Default: False.
        """
        # required properties
        base = {'type': 'ScheduleFixedInterval'} if not \
            abridged else {'type': 'ScheduleFixedIntervalAbridged'}
        base['identifier'] = self.identifier
        base['values'] = self.values

        # optional properties
        base['timestep'] = self.timestep
        base['start_date'] = self.start_date.to_array()
        base['placeholder_value'] = self.placeholder_value
        base['interpolate'] = self.interpolate

        # optional properties that can be abridged
        if self._schedule_type_limit is not None:
            if not abridged:
                base['schedule_type_limit'] = self._schedule_type_limit.to_dict()
            else:
                base['schedule_type_limit'] = self._schedule_type_limit.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    @staticmethod
    def to_idf_collective_csv(schedules, schedule_directory, file_name,
                              include_datetimes=False):
        """Write several ScheduleFixedIntervals into the same CSV file and get IDF text.

        This method is useful when several ScheduleFixedInterval objects are serving a
        similar purpose and the data would be more easily managed if they all were in
        the same file.

        Args:
            schedules: A list of ScheduleFixedInterval objects to be written into
                the same CSV.
            schedule_directory: [Required] Text string of a full path to a folder on
                this machine to which the CSV version of the file will be written.
            file_name: Text string for the name to be used for the CSV file that
                houses all of the schedule data.
            include_datetimes: Boolean to note whether a column of datetime objects
                should be written into the CSV alongside the data. Default is False,
                which will keep the resulting CSV lighter in file size but you may
                want to include such datetimes in order to verify that values align with
                the expected timestep.

        Returns:
            schedule_files --
            A list of IDF text string representations of the Schedule:File describing
            this schedule.
        """
        # ensure that all is_leap_year values are the same
        init_lp_yr = schedules[0].is_leap_year
        for sch in schedules:
            assert sch.is_leap_year is init_lp_yr, 'All is_leap_year properties must ' \
                'match for several ScheduleFixedIntervals to be in the same CSV.'
        # find the greatest timestep of all the schedules
        max_timestep = max([sched.timestep for sched in schedules])
        # gather all of the data to be written into the CSV
        sch_ids = [sched.identifier for sched in schedules]
        sched_vals = [sched.values_at_timestep(max_timestep) for sched in schedules]
        sched_data = [','.join([str(x) for x in row]) for row in zip(*sched_vals)]
        if include_datetimes:
            sched_a_per = AnalysisPeriod(timestep=max_timestep, is_leap_year=init_lp_yr)
            sched_data = ('{},{}'.format(dt, val) for dt, val in
                          zip(sched_a_per.datetimes, sched_data))
            sch_ids = [''] + sch_ids
        sched_data = [','.join(sch_ids)] + sched_data
        file_path = os.path.join(schedule_directory,
                                 '{}.csv'.format(file_name.replace(' ', '_')))

        # write the data into the file
        write_to_file(file_path, ',\n'.join(sched_data), True)

        # generate the IDF strings
        schedule_files = []
        for i, sched in enumerate(schedules):
            shc_typ = sched._schedule_type_limit.identifier if \
                sched._schedule_type_limit is not None else ''
            col_num = 1 + i if not include_datetimes else 2 + i
            num_hrs = 8760 if not sched.is_leap_year else 8784
            interp = 'No' if not sched.interpolate else 'Yes'
            min_per_step = int(60 / max_timestep)
            fields = (sched.identifier, shc_typ, file_path, col_num, 1, num_hrs, 'Comma',
                      interp, min_per_step)
            schedule_files.append(generate_idf_string(
                'Schedule:File', fields, ScheduleFixedInterval._schedule_file_comments))
        return schedule_files

    @staticmethod
    def extract_all_from_idf_file(idf_file):
        """Extract all ScheduleFixedInterval objects from an EnergyPlus IDF file.

        Args:
            idf_file: A path to an IDF file containing objects for Schedule:File
                which should have correct file paths to CSVs storing the schedule
                values.

        Returns:
            schedules --
            A list of all Schedule:File objects in the IDF file as honeybee_energy
            ScheduleFixedInterval objects.
        """
        # read the file and remove lines of comments
        file_contents = clean_idf_file_contents(idf_file)
        # extract all of the ScheduleTypeLimit objects
        type_pattern = re.compile(r"(?i)(ScheduleTypeLimits,[\s\S]*?;)")
        sch_type_str = type_pattern.findall(file_contents)
        sch_type_dict = ScheduleFixedInterval._idf_schedule_type_dictionary(sch_type_str)
        # extract all of the Schedule:File objects and convert to Schedule
        schedules = []
        sch_pattern = re.compile(r"(?i)(Schedule:File,[\s\S]*?;)")
        for sch_string in sch_pattern.findall(file_contents):
            schedule = ScheduleFixedInterval.from_idf(sch_string)
            sch_props = parse_idf_string(sch_string)
            if sch_props[1] != '':
                schedule.schedule_type_limit = sch_type_dict[sch_props[1]]
            schedules.append(schedule)
        return schedules

    @staticmethod
    def average_schedules(identifier, schedules, weights=None):
        """Get a ScheduleFixedInterval that's a weighted average between other schedules.

        Args:
            identifier: A unique ID text string for the new unique ScheduleFixedInterval.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a
                model and in the exported IDF.
            schedules: A list of ScheduleFixedInterval objects that will be averaged
                together to make a new ScheduleFixedInterval. This list may also contain
                ScheduleRulesets but it is recommend there be at least one
                ScheduleFixedInterval. Otherwise, the ScheduleRuleset.average_schedules
                method should be used.
            weights: An optional list of fractional numbers with the same length
                as the input schedules that sum to 1. These will be used to weight
                each of the ScheduleFixedInterval objects in the resulting average
                schedule. If None, the individual schedules will be weighted equally.
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
            assert abs(sum(weights) - 1.0) <= 1e-9, 'Average schedule weights must ' \
                'sum to 1.  Got {}.'.format(sum(weights))

        # determine the max timestep and leap year for the resulting schedule
        t_steps = [1]
        lp_yrs = []
        for sched in schedules:
            try:
                t_steps.append(sched.timestep)
                lp_yrs.append(sched.is_leap_year)
            except AttributeError:
                pass  # ScheduleRuleset
        timestep = max(t_steps)
        lp_yr = lp_yrs[0] if len(lp_yrs) != 0 else False
        for lp in lp_yrs:
            assert lp is lp_yr, \
                'All is_leap_year properties must match to make an average schedule.'

        # collect all of the values at the timestep
        all_values = []
        for sched in schedules:
            if isinstance(sched, ScheduleFixedInterval):
                all_values.append(sched.values_at_timestep(timestep))
            else:
                try:
                    all_values.append(sched.values(timestep, leap_year=lp_yr))
                except AttributeError:
                    raise TypeError('"{}" is not an acceptable input type for '
                                    'ScheduleFixedInterval.average_schedules.'.format(
                                        type(sched)))

        sch_vals = [sum([val * weights[i] for i, val in enumerate(values)])
                    for values in zip(*all_values)]

        # return the final schedule
        return ScheduleFixedInterval(identifier, sch_vals, schedules[0].schedule_type_limit,
                                     timestep, start_date=Date(1, 1, lp_yr))

    def _check_values(self, values):
        """Check values whenever they come through the values setter."""
        assert isinstance(values, Iterable) and not \
            isinstance(values, (str, dict, bytes, bytearray)), \
            'values should be a list or tuple. Got {}'.format(type(values))
        if not isinstance(values, tuple):
            try:
                values = tuple(float(val) for val in values)
            except (ValueError, TypeError):
                raise TypeError('ScheduleDay values must be numbers.')
        max_hour = 8760 if not self.is_leap_year else 8784
        assert self._timestep * 24 <= len(values) <= self._timestep * max_hour, \
            'Length of values must be at least {} and no more than {} when timestep ' \
            'is {} and start_date leap-year value is {}. Got {}.'.format(
                self._timestep * 24, self._timestep * max_hour, self._timestep,
                self.is_leap_year, len(values))
        return values

    def _get_lb_data_type_and_unit(self):
        """Get the ladybug data type and unit from the schedule_type_limit."""
        if self.schedule_type_limit is not None:
            data_type = self.schedule_type_limit.data_type
            unit = self.schedule_type_limit.unit
        else:
            unit = 'unknown'
            data_type = GenericType('Unknown Data Type', unit)
        return data_type, unit

    def _xxrange(self, start, end, step_count):
        """Generate n values between start and end."""
        _step = (end - start) / float(step_count)
        return (start + (i * _step) for i in xrange(int(step_count)))

    @staticmethod
    def _idf_schedule_type_dictionary(type_idf_strings):
        """Get a dictionary of ScheduleTypeLimit objects from ScheduleTypeLimits strings.
        """
        sch_type_dict = {}
        for type_str in type_idf_strings:
            type_str = type_str.strip()
            type_obj = ScheduleTypeLimit.from_idf(type_str)
            sch_type_dict[type_obj.identifier] = type_obj
        return sch_type_dict

    def __len__(self):
        return len(self._values)

    def __getitem__(self, key):
        return self._values[key]

    def __iter__(self):
        return iter(self._values)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self._placeholder_value, self._interpolate,
                self._timestep, hash(self._start_date),
                hash(self.schedule_type_limit)) + self._values

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleFixedInterval) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = ScheduleFixedInterval(
            self.identifier, self._values, self._schedule_type_limit, self._timestep,
            self._start_date, self._placeholder_value, self._interpolate)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ScheduleFixedInterval: {} [{} - {}] [timestep: {}]'.format(
            self.display_name, self.start_date,
            self.end_date_time.strftime('%d %b'), self.timestep)
