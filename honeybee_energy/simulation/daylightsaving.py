# coding=utf-8
"""EnergyPlus Daylight Saving Time Period."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string

from ladybug.analysisperiod import AnalysisPeriod
from ladybug.dt import Date


class DaylightSavingTime(object):
    """EnergyPlus Daylight Saving Time Period.

    Args:
        start_date: A ladybug Date object for the start of daylight saving time.
            Must be before the end date and have a leap_year property matching the
            end_date. Default: 12 Mar (daylight savings in the US in 2017)
        end_date: A ladybug Date object for the end of daylight saving time.
            Must be after the start date and have a leap_year property matching the
            start_date. Default: 5 Nov (daylight savings in the US in 2017)

    Properties:
        * start_date
        * end_date
    """
    __slots__ = ('_start_date', '_end_date')

    def __init__(self, start_date=Date(3, 12), end_date=Date(11, 5)):
        """Initialize DaylightSavingTime."""
        # process the dates
        if start_date is not None:
            self._check_date(start_date, 'start_date')
            self._start_date = start_date
        else:
            self._start_date = Date(3, 12)
        self.end_date = end_date

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
            self._start_date = Date(1, 1)
        self._check_start_before_end()

    @property
    def end_date(self):
        """Get or set a ladybug Date object for the end of the period."""
        return self._end_date

    @end_date.setter
    def end_date(self, value):
        if value is not None:
            self._check_date(value, 'start_date')
            self._end_date = value
        else:
            self._end_date = Date(12, 31)
        self._check_start_before_end()

    @classmethod
    def from_analysis_period(cls, analysis_period=AnalysisPeriod(3, 12, 0, 11, 5, 23)):
        """Initialize a DaylightSavingTime object from a ladybug AnalysisPeriod.

        Args:
            analysis_period: A ladybug AnalysisPeriod object that has the start
                and end dates for daylight savings time.
                Default: 12 Mar - 5 Nov (daylight savings in the US in 2017)
        """
        assert isinstance(analysis_period, AnalysisPeriod), 'Expected AnalysisPeriod ' \
            'for DaylightSavingTime.from_analysis_period. Got {}.'.format(
                type(analysis_period))
        st_date = Date(analysis_period.st_month, analysis_period.st_day,
                       analysis_period.is_leap_year)
        end_date = Date(analysis_period.end_month, analysis_period.end_day,
                        analysis_period.is_leap_year)
        return cls(st_date, end_date)

    @classmethod
    def from_idf(cls, idf_string):
        """Create a DaylightSavingTime object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                RunPeriodControl:DaylightSavingTime definition.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'RunPeriodControl:DaylightSavingTime,')
        start_vals = ep_strs[0].split('/')
        end_vals = ep_strs[1].split('/')
        start_date = Date(int(start_vals[0]), int(start_vals[1]))
        end_date = Date(int(end_vals[0]), int(end_vals[1]))
        return cls(start_date, end_date)

    @classmethod
    def from_dict(cls, data):
        """Create a DaylightSavingTime object from a dictionary.

        Args:
            data: A DaylightSavingTime dictionary in following the format below.

        .. code-block:: python

            {
            "type": "DaylightSavingTime",
            "start_date": [3, 12],
            "end_date": [11, 5]
            }
        """
        assert data['type'] == 'DaylightSavingTime', \
            'Expected DaylightSavingTime dictionary. Got {}.'.format(data['type'])
        start_date = Date.from_array(data['start_date']) if 'start_date' in data and \
            data['start_date'] is not None else Date(1, 1)
        end_date = Date.from_array(data['end_date']) if 'end_date' in data and \
            data['end_date'] is not None else Date(12, 31)
        return cls(start_date, end_date)

    def to_idf(self):
        """Get an EnergyPlus string representation of the DaylightSavingTime."""
        values = ('{}/{}'.format(self.start_date.month, self.start_date.day),
                  '{}/{}'.format(self.end_date.month, self.end_date.day))
        comments = ('start date', 'end date')
        return generate_idf_string('RunPeriodControl:DaylightSavingTime',
                                   values, comments)

    def to_dict(self):
        """DaylightSavingTime dictionary representation."""
        return {
            'type': 'DaylightSavingTime',
            'start_date': self.start_date.to_array(),
            'end_date': self.end_date.to_array()
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _check_start_before_end(self):
        """Check that the start_date is before the end_date."""
        assert self.start_date.leap_year is self.end_date.leap_year, \
            'DaylightSavingTime start_date.leap_year must match the end_date.leap_year'
        assert self._start_date <= self._end_date, 'DaylightSavingTime start_date must ' \
            'be before end_date. {} is after {}.'.format(self.start_date, self.end_date)

    @staticmethod
    def _check_date(date, date_name='date'):
        assert isinstance(date, Date), 'Expected ladybug Date for ' \
            'DaylightSavingTime {}. Got {}.'.format(date_name, type(date))

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return DaylightSavingTime(self.start_date, self.end_date)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self.start_date), hash(self.end_date))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, DaylightSavingTime) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()
