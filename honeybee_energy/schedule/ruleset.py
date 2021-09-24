# coding=utf-8
"""Complete annual schedule object built from ScheduleDay and rules for applying them."""
from __future__ import division

import os
import re

from honeybee._lockable import lockable
from honeybee.typing import tuple_with_length, valid_ep_string
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datatype.generic import GenericType
from ladybug.dt import Date, Time
from ladybug.header import Header

from ..reader import parse_idf_string
from ..writer import generate_idf_string
from .day import ScheduleDay
from .rule import ScheduleRule
from .typelimit import ScheduleTypeLimit


@lockable
class ScheduleRuleset(object):
    """A complete schedule assembled from ScheduleDay and ScheduleRules.

    Args:
        identifier: Text string for a unique Schedule ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        default_day_schedule: A ScheduleDay object that will be used for all
            days where there is no ScheduleRule applied.
        schedule_rules: A list of ScheduleRule objects that note exceptions
            to the default_day_schedule. These rules should be ordered from
            highest to lowest priority.
        schedule_type_limit: A ScheduleTypeLimit object that will be used to
            validate schedule values against upper/lower limits and assign units
            to the schedule values. If None, no validation will occur.
        summer_designday_schedule: A ScheduleDay object that will be used for
            the summer design day (used to size the cooling system).
        winter_designday_schedule: A ScheduleDay object that will be used for
            the winter design day (used to size the heating system).
        holiday_schedule: A ScheduleDay object that will be used for holidays.

    Properties:
        * identifier
        * display_name
        * default_day_schedule
        * schedule_rules
        * schedule_type_limit
        * summer_designday_schedule
        * winter_designday_schedule
        * holiday_schedule
        * day_schedules
        * is_constant
        * is_single_week
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_default_day_schedule',
                 '_schedule_rules', '_holiday_schedule', '_summer_designday_schedule',
                 '_winter_designday_schedule', '_schedule_type_limit',
                 '_locked', '_user_data')
    _dow_text_to_int = {'sunday': 1, 'monday': 2, 'tuesday': 3, 'wednesday': 4,
                        'thursday': 2, 'friday': 3, 'saturday': 7}
    _schedule_week_comments = (
        'name', 'sunday', 'monday', 'tuesday', 'wednesday', 'thursday', 'friday',
        'saturday', 'holiday', 'summer design day', 'winter design day',
        'custom day 1', 'custom day 2')

    def __init__(self, identifier, default_day_schedule, schedule_rules=None,
                 schedule_type_limit=None, holiday_schedule=None,
                 summer_designday_schedule=None, winter_designday_schedule=None):
        """Initialize Schedule Ruleset."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.default_day_schedule = default_day_schedule
        self.schedule_rules = schedule_rules
        self.schedule_type_limit = schedule_type_limit
        self.holiday_schedule = holiday_schedule
        self.summer_designday_schedule = summer_designday_schedule
        self.winter_designday_schedule = winter_designday_schedule
        self._user_data = None

    @property
    def identifier(self):
        """Get or set the text string for schedule unique identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'schedule ruleset identifier')

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
    def default_day_schedule(self):
        """Get or set the DaySchedule object that will be used by default."""
        return self._default_day_schedule

    @default_day_schedule.setter
    def default_day_schedule(self, schedule):
        assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
            'ScheduleRuleset default_day_schedule. Got {}.'.format(type(schedule))
        self._check_schedule_parent(schedule, 'default_day_schedule')
        self._default_day_schedule = schedule

    @property
    def schedule_rules(self):
        """Get or set an array of ScheduleRules that note exceptions to the default.

        These rules are ordered from highest priority to lowest priority meaning that,
        if two rules cover the same date range and day of the week, the rule that comes
        first in this list will take precedence. Following this logic, you typically
        want rules that only apply for part of a year to precede rules that are
        applied over the whole year. This way, the schedule over the whole year doesn't
        overwrite the partial-year schedule underneath it.
        """
        return tuple(self._schedule_rules)

    @schedule_rules.setter
    def schedule_rules(self, rules):
        self._schedule_rules = self._check_schedule_rules(rules)

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
    def holiday_schedule(self):
        """Get or set the DaySchedule that will be used for holidays.

        Note that, if this property is None, the default_day_schedule is
        ultimately written into the IDF for the holidays.
        """
        return self._holiday_schedule

    @holiday_schedule.setter
    def holiday_schedule(self, schedule):
        if schedule is not None:
            assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
                'ScheduleRuleset holiday_schedule. Got {}.'.format(
                    type(schedule))
            self._check_schedule_parent(schedule, 'holiday_schedule')
        self._holiday_schedule = schedule

    @property
    def summer_designday_schedule(self):
        """Get or set the DaySchedule that will be used for the summer design day.

        Note that, if this property is None, the default_day_schedule is
        ultimately written into the IDF for the summer design day.
        """
        return self._summer_designday_schedule

    @summer_designday_schedule.setter
    def summer_designday_schedule(self, schedule):
        if schedule is not None:
            assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
                'ScheduleRuleset summer_designday_schedule. Got {}.'.format(
                    type(schedule))
            self._check_schedule_parent(schedule, 'summer_designday_schedule')
        self._summer_designday_schedule = schedule

    @property
    def winter_designday_schedule(self):
        """Get or set the DaySchedule that will be used for the winter design day.

        Note that, if this property is None, the default_day_schedule is
        ultimately written into the IDF for the winter design day.
        """
        return self._winter_designday_schedule

    @winter_designday_schedule.setter
    def winter_designday_schedule(self, schedule):
        if schedule is not None:
            assert isinstance(schedule, ScheduleDay), 'Expected ScheduleDay for ' \
                'ScheduleRuleset winter_designday_schedule. Got {}.'.format(
                    type(schedule))
            self._check_schedule_parent(schedule, 'winter_designday_schedule')
        self._winter_designday_schedule = schedule

    @property
    def day_schedules(self):
        """Get a list of all unique ScheduleDay objects used in this ScheduleRuleset."""
        day_scheds = [self.default_day_schedule]
        if self._summer_designday_schedule is not None and not \
                self._instance_in_array(self._summer_designday_schedule, day_scheds):
            day_scheds.append(self._summer_designday_schedule)
        if self._winter_designday_schedule is not None and not \
                self._instance_in_array(self._winter_designday_schedule, day_scheds):
            day_scheds.append(self._winter_designday_schedule)
        if self._holiday_schedule is not None and not \
                self._instance_in_array(self._holiday_schedule, day_scheds):
            day_scheds.append(self._holiday_schedule)
        for rule in self.schedule_rules:
            if not self._instance_in_array(rule._schedule_day, day_scheds):
                day_scheds.append(rule._schedule_day)
        return day_scheds

    @property
    def is_constant(self):
        """Boolean noting whether the schedule is representable with a single value."""
        return self.default_day_schedule.is_constant and self._schedule_rules == [] and \
            self._summer_designday_schedule is None and \
            self._winter_designday_schedule is None and self._holiday_schedule is None

    @property
    def is_single_week(self):
        """Boolean noting whether this schedule is representable with one week schedule.
        """
        if self._schedule_rules == []:
            return True
        elif all([sch._start_doy == 1 and sch._end_doy == 365
                  for sch in self._schedule_rules]):
            return True
        return False
    
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


    def add_rule(self, rule):
        """Add a ScheduleRule to this ScheduleRuleset.

        Note that adding a rule here will add it as highest priority in the full list
        of schedule_rules, meaning it may overwrite other rules underneath it.

        Args:
            rule: A ScheduleRule object to be added to this ScheduleRuleset.
                ScheduleRule objects note the exceptions to the default_day_schedule.
        """
        self._check_rule(rule)
        self._check_schedule_parent(rule.schedule_day, 'schedule_rule')
        self._schedule_rules.insert(0, rule)

    def remove_rule(self, rule_index):
        """Remove a ScheduleRule from the schedule by its index in schedule_rules.

        Args:
            rule_index: An integer for the index of the rule to remove.
        """
        self._schedule_rules[rule_index].schedule_day._parent = None
        del self._schedule_rules[rule_index]

    def reorder_rule(self, rule_index, new_index=0):
        """Change the priority of a ScheduleRule in the full schedule_rules list.

        Lower indices (ordered first) in the schedule_rules indicate the rule has
        a higher priority.

        Args:
            rule_index: An integer for the index of the rule to reorder.
            new_index: An integer for the new index of the rule. The default is 0,
                which will re-insert the selected rule at the top of the
                priority list.
        """
        self._schedule_rules.insert(new_index, self._schedule_rules.pop(rule_index))

    def values(self, timestep=1, start_date=Date(1, 1), end_date=Date(12, 31),
               start_dow='Sunday', holidays=None, leap_year=False):
        """Get a list of sequential schedule values over the year at a given timestep.

        Note that there are two possible ways that these values can be mapped to
        corresponding times. See the ScheduleDay.values_at_timestep method
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
        hol_vals = None
        if self.holiday_schedule is not None and holidays is not None:
            hol_vals = self.holiday_schedule.values_at_timestep(timestep)
        # ensure that everything is consistent across leap years
        if start_date.leap_year is not leap_year:
            start_date = Date(start_date.month, start_date.day, leap_year)
        if end_date.leap_year is not leap_year:
            end_date = Date(end_date.month, end_date.day, leap_year)
        # ensure start date is before end date
        assert start_date <= end_date, 'ScheduleRuleset values() start_date must come ' \
            'before end_date. {} comes after {}.'.format(start_date, end_date)
        # process the holidays if they are input
        if holidays is not None:
            hol_doy = []
            for hol in holidays:
                if hol.leap_year is not leap_year:
                    hol = Date(hol.month, hol.day, leap_year)
                hol_doy.append(hol.doy)
        else:
            hol_doy = []
        # process the start_dow into an integer.
        dow = self._dow_text_to_int[start_dow.lower()]
        # generate the full list of annual values
        if not leap_year:
            return self._get_sch_values(
                sch_day_vals, dow, start_date, end_date, hol_doy, hol_vals)
        else:
            return self._get_sch_values_leap_year(
                sch_day_vals, dow, start_date, end_date, hol_doy, hol_vals)

    def data_collection(self, timestep=1, start_date=Date(1, 1), end_date=Date(12, 31),
                        start_dow='Sunday', holidays=None, leap_year=False):
        """Get a ladybug DataCollection representing this schedule at a given timestep.

        Note that ladybug DataCollections always follow the "Ladybug Tools
        Interpretation" of date time values as noted in the
        ScheduleDay.values_at_timestep documentation.

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
                                  end_date.month, end_date.day, 23,
                                  timestep, leap_year)
        if self.schedule_type_limit is not None:
            data_type = self.schedule_type_limit.data_type
            unit = self.schedule_type_limit.unit
        else:
            unit = 'unknown'
            data_type = GenericType('Unknown Data Type', unit)
        header = Header(data_type, unit, a_period, metadata={'schedule': self.identifier})
        values = self.values(timestep, start_date, end_date, start_dow,
                             holidays, leap_year)
        return HourlyContinuousCollection(header, values)

    def shift_by_step(self, step_count=1, timestep=1):
        """Get a version of this object where the day_schedule values are shifted.

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
                while 60 indicates that each step is a minute. (Default: 1).
        """
        # shift all of the day schedules according to the inputs
        day_scheds = self.day_schedules
        shift_dict = {sch.identifier: sch.shift_by_step(step_count, timestep)
                      for sch in day_scheds}
        # figure out where each of the shifted schedules belong
        new_default = shift_dict[self.default_day_schedule.identifier]
        new_summer = shift_dict[self._summer_designday_schedule.identifier] \
            if self._summer_designday_schedule is not None else None
        new_winter = shift_dict[self._winter_designday_schedule.identifier] \
            if self._winter_designday_schedule is not None else None
        new_holiday = shift_dict[self._holiday_schedule.identifier] \
            if self._holiday_schedule is not None else None
        new_rules = []
        for rule in self.schedule_rules:
            new_rule = rule.duplicate()
            new_rule.schedule_day = shift_dict[rule.schedule_day.identifier]
            new_rules.append(new_rule)
        # retrun the shifted schedule
        new_id = '{}_Shift_{}mins'.format(
            self.identifier, int((60 / timestep) * step_count))
        return ScheduleRuleset(
            new_id, new_default, new_rules, self.schedule_type_limit, new_holiday,
            new_summer, new_winter)

    @classmethod
    def from_constant_value(cls, identifier, value, schedule_type_limit=None):
        """Create a ScheduleRuleset fromm a single constant value.

        Args:
            identifier: Text string for a unique Schedule ID. Must be < 100 characters
                and not contain any EnergyPlus special characters. This will be used to
                identify the object across a model and in the exported IDF.
            value: A single constant value to be applied throughout the whole year.
            schedule_type_limit: A ScheduleTypeLimit object that will be used to
                validate schedule values against upper/lower limits and assign
                units to the schedule values.
        """
        default_sched = ScheduleDay('{}_Day Schedule'.format(identifier), [value])
        return cls(identifier, default_sched, None, schedule_type_limit)

    @classmethod
    def from_daily_values(cls, identifier, daily_values, timestep=1,
                          schedule_type_limit=None):
        """Create a ScheduleRuleset from a list of repeating daily values at a timestep.

        Args:
            identifier: Text string for a unique Schedule ID. Must be < 100 characters
                and not contain any EnergyPlus special characters. This will be used to
                identify the object across a model and in the exported IDF.
            daily_values: A list of [24 * timestep] numbers for schedule values.
            timestep: An integer for the number of steps per hour that the input
                values correspond to.  For example, if each value represents 30
                minutes, the timestep is 2. For 15 minutes, it is 4. Default is 1,
                meaning each value represents a single hour. Must be one of the
                following: (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60).
            schedule_type_limit: A ScheduleTypeLimit object that will be used to
                validate schedule values against upper/lower limits and assign units
                to the schedule values.
        """
        default_sched = ScheduleDay.from_values_at_timestep(
            '{}_Day Schedule'.format(identifier), daily_values, timestep)
        return cls(identifier, default_sched, None, schedule_type_limit)

    @classmethod
    def from_week_daily_values(
            cls, identifier, sunday_values, monday_values, tuesday_values,
            wednesday_values, thursday_values, friday_values, saturday_values,
            holiday_values, timestep=1, schedule_type_limit=None,
            summer_designday_values=None, winter_designday_values=None):
        """Create a ScheduleRuleset from lists of daily values for each day of the week.

        Args:
            identifier: Text string for a unique Schedule ID. Must be < 100 characters
                and not contain any EnergyPlus special characters. This will be used to
                identify the object across a model and in the exported IDF.
            sunday_values: A list of [24 * timestep] numerical values for Sundays.
            monday_values: A list of [24 * timestep] numerical values for Mondays.
            tuesday_values: A list of [24 * timestep] numerical values for Tuesdays.
            wednesday_values: A list of [24 * timestep] numerical values for Wednesdays.
            thursday_values: A list of [24 * timestep] numerical values for Thursdays.
            friday_values: A list of [24 * timestep] numerical values for Fridays.
            saturday_values: A list of [24 * timestep] numerical values for Saturdays.
            holiday_values: A list of [24 * timestep] numerical values for Holidays.
            timestep: An integer for the number of steps per hour that the input
                values correspond to.  For example, if each value represents 30
                minutes, the timestep is 2. For 15 minutes, it is 4. Default is 1,
                meaning each value represents a single hour. Must be one of the
                following: (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60).
            schedule_type_limit: A ScheduleTypeLimit object that will be used to
                validate schedule values against upper/lower limits and assign
                units to the schedule values.
            summer_designday_values: A list of [24 * timestep] numerical values for
                the summer design day. If None, the daily schedule with the highest
                average value will be used.
            winter_designday_values: A list of [24 * timestep] numerical values for
                the winter design day. If None, the daily schedule with the lowest
                average value will be used.
        """
        # process the rules for the days of the week
        schedule_rules = []
        applied_day_values = []
        all_vals = (sunday_values, monday_values, tuesday_values, wednesday_values,
                    thursday_values, friday_values, saturday_values)
        for i, day_vals in enumerate(all_vals):
            if day_vals not in applied_day_values:  # make a new ScheduleDay and rule
                d_id = '{}_{}'.format(
                    identifier, cls._schedule_week_comments[i + 1].title())
                sch_day = ScheduleDay.from_values_at_timestep(d_id, day_vals, timestep)
                rule = ScheduleRule(sch_day)
                rule.apply_day_by_dow(i + 1)
                schedule_rules.append(rule)
                applied_day_values.append(day_vals)
            else:  # edit one of the existing rules to apply it to the new day
                for count, sch in enumerate(applied_day_values):
                    if day_vals == sch:
                        sch_rule_index = count
                rule = schedule_rules[sch_rule_index]
                rule.apply_day_by_dow(i + 1)

        # get ScheduleDay for the holidays
        holiday = ScheduleDay.from_values_at_timestep(
            '{}_Hol'.format(identifier), holiday_values, timestep)

        # get ScheduleDay for summer and winter design days
        avg_day_vals = [sum(vals) / len(vals) for vals in applied_day_values]
        if summer_designday_values is None:
            sch_i = avg_day_vals.index(max(avg_day_vals))
            summer = schedule_rules[sch_i]._schedule_day.duplicate()
            summer.identifier = '{}_SmrDsn'.format(summer.identifier)
        else:
            summer = ScheduleDay.from_values_at_timestep(
                '{}_SmrDsn'.format(identifier), summer_designday_values, timestep)
        if winter_designday_values is None:
            sch_i = avg_day_vals.index(min(avg_day_vals))
            winter = schedule_rules[sch_i]._schedule_day.duplicate()
            winter.identifier = '{}_WntrDsn'.format(summer.identifier)
        else:
            winter = ScheduleDay.from_values_at_timestep(
                '{}_WntrDsn'.format(identifier), winter_designday_values, timestep)

        return cls(identifier, schedule_rules[0].schedule_day, schedule_rules[1:],
                   schedule_type_limit, holiday, summer, winter)

    @classmethod
    def from_week_day_schedules(
            cls, identifier, sunday_schedule, monday_schedule, tuesday_schedule,
            wednesday_schedule, thursday_schedule, friday_schedule, saturday_schedule,
            holiday_schedule, summer_designday_schedule, winter_designday_schedule,
            schedule_type_limit=None):
        """Create a ScheduleRuleset from ScheduleDay objects for each day of the week.

        Args:
            identifier: Text string for a unique Schedule ID. Must be < 100 characters
                and not contain any EnergyPlus special characters. This will be used to
                identify the object across a model and in the exported IDF.
            sunday_schedule: A ScheduleDay for Sundays.
            monday_schedule: A ScheduleDay for Mondays.
            tuesday_schedule: A ScheduleDay for Tuesdays.
            wednesday_schedule: A ScheduleDay for Wednesdays.
            thursday_schedule: A ScheduleDay for Thursdays.
            friday_schedule: A ScheduleDay for Fridays.
            saturday_schedule: A ScheduleDay for Saturdays.
            holiday_schedule: A ScheduleDay for Holidays.
            summer_designday_schedule: A ScheduleDay for the summer design day.
            winter_designday_schedule: A ScheduleDay for the winter design day.
            schedule_type_limit: A ScheduleTypeLimit object that will be used to
                validate schedule values against upper/lower limits and assign
                units to the schedule values.
        """
        schedule_rules = []
        applied_day_ids = []
        all_sched = (sunday_schedule, monday_schedule, tuesday_schedule,
                     wednesday_schedule, thursday_schedule, friday_schedule,
                     saturday_schedule)
        for i, day_sch in enumerate(all_sched):
            if day_sch.identifier not in applied_day_ids:  # make a new rule
                rule = ScheduleRule(day_sch)
                rule.apply_day_by_dow(i + 1)
                schedule_rules.append(rule)
                applied_day_ids.append(day_sch.identifier)
            else:  # edit one of the existing rules to apply it to the new day
                sch_rule_index = applied_day_ids.index(day_sch.identifier)
                rule = schedule_rules[sch_rule_index]
                rule.apply_day_by_dow(i + 1)

        # get ScheduleDay for the holidays
        if holiday_schedule.identifier in applied_day_ids:  # avoid duplicate
            holiday_schedule = holiday_schedule.duplicate()
            holiday_schedule.identifier = '{}_Hol'.format(holiday_schedule.identifier)

        # get ScheduleDay for summer and winter design days
        if summer_designday_schedule.identifier in applied_day_ids:  # avoid duplicate
            summer_designday_schedule = summer_designday_schedule.duplicate()
            summer_designday_schedule.identifier = \
                '{}_SmrDsn'.format(summer_designday_schedule.identifier)
        if winter_designday_schedule.identifier in applied_day_ids:  # avoid duplicate
            winter_designday_schedule = winter_designday_schedule.duplicate()
            winter_designday_schedule.identifier = \
                '{}_WntrDsn'.format(winter_designday_schedule.identifier)
        return cls(identifier, schedule_rules[0].schedule_day, schedule_rules[1:],
                   schedule_type_limit, holiday_schedule, summer_designday_schedule,
                   winter_designday_schedule)

    @classmethod
    def from_idf(cls, year_idf_string, week_idf_strings, day_idf_strings,
                 type_idf_string=None):
        """Create a ScheduleRuleset from an EnergyPlus IDF text strings.

        Args:
            year_idf_string: A text string fully describing an EnergyPlus
                Schedule:Year.
            week_idf_strings: A list of text strings for all of the Schedule:Week
                objects used in the Schedule:Year.
            day_idf_strings: A list of text strings for all of the Schedule:Day
                objects used in the week_idf_strings.
            type_idf_string: An optional text string for the ScheduleTypeLimits.
                If None, the resulting schedule will have no ScheduleTypeLimit.
        """
        # process the schedule components
        day_schedule_dict = cls._idf_day_schedule_dictionary(day_idf_strings)
        week_sch_dict, week_dd_dict = cls._idf_week_schedule_dictionary(
            week_idf_strings, day_schedule_dict)
        schedule_type = ScheduleTypeLimit.from_idf(type_idf_string) if type_idf_string \
            is not None else None

        # use the year schedule to bring it all together
        year_sch = parse_idf_string(year_idf_string)
        all_rules = []
        for i in range(2, len(year_sch), 5):
            rules = week_sch_dict[year_sch[i]]
            st_date = Date(int(year_sch[i + 1]), int(year_sch[i + 2]))
            end_date = Date(int(year_sch[i + 3]), int(year_sch[i + 4]))
            for rule in rules:
                rule.start_date = st_date
                rule.end_date = end_date
            all_rules.extend(rules)
        default_day_schedule = all_rules[0].schedule_day
        holiday_sch, summer_dd_sch, winter_dd_sch = week_dd_dict[year_sch[2]]
        sched = cls(year_sch[0], default_day_schedule, all_rules[1:], schedule_type)
        cls._apply_designdays_with_check(
            sched, holiday_sch, summer_dd_sch, winter_dd_sch)
        return sched

    @classmethod
    def from_idf_constant(cls, idf_string, type_idf_string=None):
        """Create a ScheduleRuleset from an EnergyPlus Schedule:Constant string.

        Args:
            idf_string: A text string fully describing an EnergyPlus Schedule:Constant.
            type_idf_string: An optional text string for the ScheduleTypeLimits.
                If None, the resulting schedule will have no ScheduleTypeLimit.
        """
        const_sch = parse_idf_string(idf_string)
        sched_val = float(const_sch[2]) if const_sch[2] != '' else 0
        schedule_type = ScheduleTypeLimit.from_idf(type_idf_string) if type_idf_string \
            is not None else None
        return ScheduleRuleset.from_constant_value(
            const_sch[0], sched_val, schedule_type)

    @classmethod
    def from_dict(cls, data):
        """Create a ScheduleRuleset from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: ScheduleRuleset dictionary following the format below.

        .. code-block:: python

            {
            "type": 'ScheduleRuleset',
            "identifier": 'Office_Occ_900_1700_weekends',
            "display_name": 'Office Occupancy',
            "day_schedules": [], # Array of ScheduleDay dictionary representations
            "default_day_schedule": str, # ScheduleDay identifier
            "schedule_rules": [], # list of ScheduleRuleAbridged dictionaries
            "schedule_type_limit": {}, # ScheduleTypeLimit dictionary representation
            "holiday_schedule": str, # ScheduleDay identifier
            "summer_designday_schedule": str, # ScheduleDay identifier
            "winter_designday_schedule": str # ScheduleDay identifier
            }
        """
        assert data['type'] == 'ScheduleRuleset', \
            'Expected ScheduleRuleset. Got {}.'.format(data['type'])

        sch_day_dict = {}
        for day_sch in data['day_schedules']:
            sch_day_dict[day_sch['identifier']] = ScheduleDay.from_dict(day_sch)

        default_sched = sch_day_dict[data['default_day_schedule']]
        rules = None
        if 'schedule_rules' in data and data['schedule_rules'] is not None:
            rules = []
            for rule in data['schedule_rules']:
                sch_day = sch_day_dict[rule['schedule_day']]
                rules.append(ScheduleRule.from_dict_abridged(rule, sch_day))
        holiday_sched = None
        if 'holiday_schedule' in data and data['holiday_schedule'] is not None:
            holiday_sched = sch_day_dict[data['holiday_schedule']]
        summer_sched = None
        if 'summer_designday_schedule' in data and \
                data['summer_designday_schedule'] is not None:
            summer_sched = sch_day_dict[data['summer_designday_schedule']]
        winter_sched = None
        if 'winter_designday_schedule' in data and \
                data['winter_designday_schedule'] is not None:
            winter_sched = sch_day_dict[data['winter_designday_schedule']]

        sched_type = None
        if 'schedule_type_limit' in data and data['schedule_type_limit'] is not None:
            sched_type = ScheduleTypeLimit.from_dict(data['schedule_type_limit'])

        new_obj = cls(data['identifier'], default_sched, rules, sched_type,
                      holiday_sched, summer_sched, winter_sched)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_type_limits):
        """Create a ScheduleRuleset from an abridged dictionary.

        Args:
            data: ScheduleRulesetAbridged dictionary.
            schedule_type_limits: A dictionary with identifiers of schedule type limits
                as keys and Python schedule type limit objects as values.

        .. code-block:: python

            {
            "type": 'ScheduleRulesetAbridged',
            "identifier": 'Office_Occ_900_1700_weekends',
            "display_name": 'Office Occupancy',
            "day_schedules": [], # Array of ScheduleDay dictionary representations
            "default_day_schedule": str, # ScheduleDay identifier
            "schedule_rules": [], # list of ScheduleRuleAbridged dictionaries
            "schedule_type_limit": str, # ScheduleTypeLimit identifier
            "holiday_schedule": str, # ScheduleDay identifier
            "summer_designday_schedule": str, # ScheduleDay identifier
            "winter_designday_schedule": str # ScheduleDay identifier
            }
        """
        assert data['type'] == 'ScheduleRulesetAbridged', \
            'Expected ScheduleRulesetAbridged. Got {}.'.format(data['type'])

        data = data.copy()  # copy original dictionary so we don't edit it
        typ_lim = None
        if 'schedule_type_limit' in data:
            typ_lim = data['schedule_type_limit']
            data['schedule_type_limit'] = None
        data['type'] = 'ScheduleRuleset'
        schedule = cls.from_dict(data)
        schedule.schedule_type_limit = schedule_type_limits[typ_lim] if \
            typ_lim is not None else None
        if 'display_name' in data and data['display_name'] is not None:
            schedule.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            schedule.user_data = data['user_data']
        return schedule

    def to_rules(self, start_date, end_date):
        """Get all of rules needed to implement this ScheduleRuleset over a date range.

        This is useful when you want to apply this entire ScheduleRuleset over a
        particular time period of another ScheduleRuleset.

        Args:
            start_date: A ladybug Date object for the start of the period that rules
                should be obtained.
            end_date: A ladybug Date object for the end of the period that rules
                should be obtained.
        """
        # check the date inputs
        ScheduleRule._check_date(start_date)
        ScheduleRule._check_date(end_date)
        st_doy = ScheduleRule._doy_non_leap_year(start_date)
        end_doy = ScheduleRule._doy_non_leap_year(end_date)

        # assemble all of the rules already applied to this ScheduleRuleset
        rules = []
        for rule in self._schedule_rules:
            if (rule._start_doy < st_doy and rule._end_doy < st_doy) or \
                    (rule._start_doy > st_doy and rule._end_doy > end_doy):
                pass  # no overlap with input period
            else:
                new_rule = rule.duplicate()
                if rule._start_doy < st_doy:
                    new_rule.start_date = start_date
                if rule._end_doy > end_doy:
                    new_rule.end_date = end_date
                rules.append(new_rule)

        # add the default_day_schedule for all days not covered by rules
        default_rule = ScheduleRule(self.default_day_schedule.duplicate(),
                                    start_date=start_date, end_date=end_date)
        for dow in range(7):
            for rule in rules:
                if rule.week_apply_tuple[dow]:
                    break
            else:  # no rule applies; use default_day_schedule.
                default_rule.apply_day_by_dow(dow + 1)
        rules.append(default_rule)

        return rules

    def to_idf(self):
        """IDF string representation of the schedule.

        Note that this method only outputs Schedule:Year and Schedule:Week objects
        (or a Schedule:Constant object if applicable). However, to write the full
        schedule into an IDF, the schedules's day_schedules must also be
        written as well as the ScheduleTypeLimit object.

        The method is set up this way primarily to give better control over the export
        process. For example, you usually want to see if there are other schedules
        in a model using the same ScheduleTypeLimit object and then write it into
        the IDF only once rather than writing it multiple times for each schedule
        that references it. ScheduleDay objects can often follow a similar logic
        where the same ScheduleDay objects are used by multiple ScheduleRulesets.

        Returns:
            A tuple with two elements

            -   year_schedule: Text string representation of the Schedule:Year
                describing this schedule. This will be a Schedule:Constant if this
                schedule can be described as such.

            -   week_schedules: A list of Schedule:Week:Daily test strings that are
                referenced in the year_schedule. Will be None when year_schedule is
                a Schedule:Constant.
        """
        # beginning fields used for all schedules
        year_fields = [self.identifier]
        shc_typ = self._schedule_type_limit.identifier if \
            self._schedule_type_limit is not None else ''
        year_fields.append(shc_typ)
        year_comments = ['schedule name', 'schedule type limits']

        # check if this schedule can simply be represented with a Schedule:Constant
        if self.is_constant:
            year_fields.append(self.default_day_schedule[0])
            year_comments.append('value')
            year_schedule = generate_idf_string(
                'Schedule:Constant', year_fields, year_comments)
            return year_schedule, None

        # prepare to create a full Schedule:Year
        date_comments = ['start month {}', 'start day {}', 'end month {}', 'end day {}']
        week_schedules = []

        if self.is_single_week:  # create the only one week schedule
            wk_sch, wk_sch_id = \
                self._idf_week_schedule_from_rule_indices(range(len(self)), 1)
            week_schedules.append(wk_sch)
            yr_wk_s_ids = [wk_sch_id]
            yr_wk_dt_range = [[Date(1, 1), Date(12, 31)]]
        else:  # create a set of week schedules throughout the year
            # loop through 365 days of the year to find unique combinations of rules
            rules_each_day = []
            for doy in range(1, 366):
                rules_on_doy = tuple(i for i, rule in enumerate(self._schedule_rules)
                                     if rule._start_doy <= doy <= rule._end_doy)
                rules_each_day.append(rules_on_doy)
            unique_rule_sets = set(rules_each_day)
            # check if any combination yield the same week schedule and remove duplicates
            week_tuples = [tuple(self._get_week_list(rule_set))
                           for rule_set in unique_rule_sets]
            unique_week_tuples = list(set(week_tuples))
            # create the unique week schedules from the combinations of rules
            week_sched_ids = []
            for i, week_list in enumerate(unique_week_tuples):
                wk_schedule, wk_sch_id = \
                    self._idf_week_schedule_from_week_list(week_list, i + 1)
                week_schedules.append(wk_schedule)
                week_sched_ids.append(wk_sch_id)
            # create a dictionary mapping unique rule index lists to week schedule ids
            rule_set_map = {}
            for rule_i, week_list in zip(unique_rule_sets, week_tuples):
                unique_week_i = unique_week_tuples.index(week_list)
                rule_set_map[rule_i] = week_sched_ids[unique_week_i]
            # loop through all 365 days of the year to find when rules change
            yr_wk_s_ids = []
            yr_wk_dt_range = []
            prev_week_sched = None
            for doy in range(1, 366):
                week_sched = rule_set_map[rules_each_day[doy - 1]]
                if week_sched != prev_week_sched:  # change to a new rule set
                    yr_wk_s_ids.append(week_sched)
                    if doy != 1:
                        yr_wk_dt_range[-1].append(Date.from_doy(doy - 1))
                        yr_wk_dt_range.append([Date.from_doy(doy)])
                    else:
                        yr_wk_dt_range.append([Date(1, 1)])
                    prev_week_sched = week_sched
            yr_wk_dt_range[-1].append(Date(12, 31))

        # create the year fields and comments
        for i, (wk_sch_id, dt_range) in enumerate(zip(yr_wk_s_ids, yr_wk_dt_range)):
            year_fields.append(wk_sch_id)
            count = i + 1
            year_comments.append('week schedule name {}'.format(count))
            year_fields.extend([dt_range[0].month, dt_range[0].day,
                                dt_range[1].month, dt_range[1].day])
            for com in date_comments:
                year_comments.append(com.format(count))

        year_schedule = generate_idf_string('Schedule:Year', year_fields, year_comments)
        return year_schedule, week_schedules

    def to_dict(self, abridged=False):
        """Schedule Ruleset dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifier of the ScheduleTypeLimit.
                Default: False.
        """
        # required properties
        base = {'type': 'ScheduleRuleset'} if not \
            abridged else {'type': 'ScheduleRulesetAbridged'}
        base['identifier'] = self.identifier
        base['day_schedules'] = [sch_day.to_dict() for sch_day in self.day_schedules]
        base['default_day_schedule'] = self.default_day_schedule.identifier

        # optional properties
        if len(self._schedule_rules) != 0:
            base['schedule_rules'] = [rule.to_dict(True) for rule in self._schedule_rules]
        if self._holiday_schedule is not None:
            base['holiday_schedule'] = self._holiday_schedule.identifier
        if self._summer_designday_schedule is not None:
            base['summer_designday_schedule'] = self._summer_designday_schedule.identifier
        if self._winter_designday_schedule is not None:
            base['winter_designday_schedule'] = self._winter_designday_schedule.identifier

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

    def lock(self):
        """The lock() method also locks the ScheduleDay and ScheduleRule objects."""
        self._locked = True
        self._default_day_schedule.lock()
        if self._holiday_schedule is not None:
            self._holiday_schedule.lock()
        if self._summer_designday_schedule is not None:
            self._summer_designday_schedule.lock()
        if self._winter_designday_schedule is not None:
            self._winter_designday_schedule.lock()
        for rule in self._schedule_rules:
            rule.lock()

    def unlock(self):
        """The unlock() method also unlocks the ScheduleDay and ScheduleRule objects."""
        self._locked = False
        self._default_day_schedule.unlock()
        if self._holiday_schedule is not None:
            self._holiday_schedule.unlock()
        if self._summer_designday_schedule is not None:
            self._summer_designday_schedule.unlock()
        if self._winter_designday_schedule is not None:
            self._winter_designday_schedule.unlock()
        for rule in self._schedule_rules:
            rule.unlock()

    @staticmethod
    def extract_all_from_idf_file(idf_file, import_compact=False):
        """Extract all ScheduleRuleset objects from an EnergyPlus IDF file.

        Args:
            idf_file: A path to an IDF file containing objects for Schedule:Year and
                corresponding Schedule:Week and Schedule:Day objects. The Schedule:Year
                will be used to assemble all of these into a ScheduleRuleset.
            import_compact: Boolean to note whether to parse Schedule:Compact (True)
                or not (False).
                Default: False.

        Returns:
            schedules --
            A list of all Schedule:Year objects in the IDF file as honeybee_energy
            ScheduleRuleset objects.
        """
        # check the file
        assert os.path.isfile(idf_file), 'Cannot find an idf file at {}'.format(idf_file)
        with open(idf_file, 'r') as ep_file:
            file_contents = ep_file.read()
        # extract all of the ScheduleDay objects
        day_pattern1 = re.compile(r"(?i)(Schedule:Day:Interval,[\s\S]*?;)")
        day_pattern2 = re.compile(r"(?i)(Schedule:Day:Hourly,[\s\S]*?;)")
        day_pattern3 = re.compile(r"(?i)(Schedule:Day:List,[\s\S]*?;)")
        day_sch_str = day_pattern1.findall(file_contents) + \
            day_pattern2.findall(file_contents) + day_pattern3.findall(file_contents)
        day_schedule_dict = ScheduleRuleset._idf_day_schedule_dictionary(day_sch_str)
        # extract all of the Schedule:Week objects
        week_pattern_1 = re.compile(r"(?i)(Schedule:Week:Daily,[\s\S]*?;)")
        week_pattern_2 = re.compile(r"(?i)(Schedule:Week:Compact,[\s\S]*?;)")
        week_sch_str = week_pattern_1.findall(file_contents) + week_pattern_2.findall(file_contents)
        week_sch_dict, week_dd_dict = ScheduleRuleset._idf_week_schedule_dictionary(
            week_sch_str, day_schedule_dict)
        # extract all of the ScheduleTypeLimit objects
        type_pattern = re.compile(r"(?i)(ScheduleTypeLimits,[\s\S]*?;)")
        sch_type_str = type_pattern.findall(file_contents)
        sch_type_dict = ScheduleRuleset._idf_schedule_type_dictionary(sch_type_str)
        # extract all of the Schedule:Year objects and convert to ScheduleRuleset
        year_pattern = re.compile(r"(?i)(Schedule:Year,[\s\S]*?;)")
        year_props = tuple(parse_idf_string(idf_string) for
                           idf_string in year_pattern.findall(file_contents))
        # extract all of the Schedule:Constant objects and convert to ScheduleRuleset
        constant_pattern = re.compile(r"(?i)(Schedule:Constant,[\s\S]*?;)")
        constant_props = tuple(parse_idf_string(idf_string) for
                               idf_string in constant_pattern.findall(file_contents))
        # extract all of the Schedule:Compact objects and convert to ScheduleRuleset
        conpact_pattern = re.compile(r"(?i)(Schedule:Compact,[\s\S]*?;)")
        compact_props = (
            tuple(
                parse_idf_string(idf_string)
                for idf_string in conpact_pattern.findall(file_contents)
            )
            if import_compact  # only if user chooses so.
            else []
        )

        # compile all of the ScheduleRuleset objects from extracted properties
        schedules = []
        for year_sch in year_props:
            # gather the rules
            all_rules = []
            for i in range(2, len(year_sch), 5):
                rules = week_sch_dict[year_sch[i]]
                st_date = Date(int(year_sch[i + 1]), int(year_sch[i + 2]))
                end_date = Date(int(year_sch[i + 3]), int(year_sch[i + 4]))
                for rule in rules:
                    rule.end_date = end_date
                    rule.start_date = st_date
                all_rules.extend(rules)
            # gather the other day schedules
            holiday_sch, summer_dd_sch, winter_dd_sch = week_dd_dict[year_sch[2]]
            schedule_type = sch_type_dict[year_sch[1]] if year_sch[1] != '' else None
            # check to be sure the schedule days don't already have a parent
            for rule in all_rules:
                if rule.schedule_day._parent is not None:
                    rule.schedule_day = rule.schedule_day.duplicate()
            if holiday_sch._parent is not None:
                holiday_sch = holiday_sch.duplicate()
            if summer_dd_sch._parent is not None:
                summer_dd_sch = summer_dd_sch.duplicate()
            if winter_dd_sch._parent is not None:
                winter_dd_sch = summer_dd_sch.duplicate()
            # create the ScheduleRuleset
            default_day_schedule = all_rules[0].schedule_day
            sch_ruleset = ScheduleRuleset(
                year_sch[0], default_day_schedule, all_rules[1:], schedule_type)
            ScheduleRuleset._apply_designdays_with_check(
                sch_ruleset, holiday_sch, summer_dd_sch, winter_dd_sch)
            schedules.append(sch_ruleset)
        for const_sch in constant_props:
            sched_val = float(const_sch[2]) if const_sch[2] != '' else 0
            schedule_type = sch_type_dict[const_sch[1]] if const_sch[1] != '' else None
            sch_ruleset = ScheduleRuleset.from_constant_value(
                const_sch[0], sched_val, schedule_type)
            schedules.append(sch_ruleset)
        for compact_sch in compact_props:
            schedule_type = (
                sch_type_dict[compact_sch[1]] if compact_sch[1] != "" else None
            )
            schedule_rules = []
            holiday_schedule = None
            winter_designday_schedule = None
            summer_designday_schedule = None
            start_date = Date.from_doy(1)
            end_date = Date.from_doy(365)
            untils = [Time(0, 0)]  # initialize list of until times.
            n = -1  # initialize the n-th until time
            rules = []  # initialize list of rules.
            for field in compact_sch[2:]:
                field = field.lower()
                if "through" in field:
                    # Each `through` field generates a new ScheduleRule
                    # initialize rule with ScheduleDay as placeholder.
                    rule = ScheduleRule(ScheduleDay(compact_sch[0], [0], [Time(0, 0)]))

                    # start_date is either Jan 1st or end_date from previous
                    # `through` field
                    start_date = (
                        start_date if end_date == Date.from_doy(365) else end_date
                    )

                    _, date = field.split(":")  # get end_date from field
                    month, day = date.split("/")
                    end_date = Date.from_dict({"month": int(month), "day": int(day)})
                elif "for" in field:
                    # reset values for new set; each `for` is a new rule
                    n = -1  # reset the n-th until time
                    untils = [Time(0, 0)]  # reset list of until times.
                    rules = []  # reset list of rules for this `for` field.

                    # Create a rule; all different `if` statements because we want to
                    # catch more than one case,
                    # eg. `For: Sunday Holidays AllOtherDays, !- Field 54`
                    def create_rule_for(apply_to):
                        """Return ScheduleRule with the `apply_to` rule set to True."""
                        apply_to_attr_map = {
                            "alldays": "apply_all",
                            "weekdays": "apply_weekday",
                            "weekends": "apply_weekend",
                            "sunday": "apply_sunday",
                            "monday": "apply_monday",
                            "tuesday": "apply_tuesday",
                            "wednesday": "apply_wednesday",
                            "thursday": "apply_thursday",
                            "friday": "apply_friday",
                            "saturday": "apply_saturday",
                        }
                        rule = ScheduleRule(ScheduleDay(apply_to, [0], [Time(0, 0)]))
                        setattr(rule, apply_to_attr_map[apply_to], True)
                        return rule

                    # Create rules for regular days
                    for rule_name in [
                        "alldays",
                        "weekdays",
                        "weekends",
                        "sunday",
                        "monday",
                        "tuesday",
                        "wednesday",
                        "thursday",
                        "friday",
                        "saturday",
                    ]:
                        if rule_name in field:
                            rule = create_rule_for(rule_name)
                            rules.append(rule)

                    # Create rules for holidays and designdays
                    if "holiday" in field:
                        rule = ScheduleRule(ScheduleDay("holiday", [0], [Time(0, 0)]))
                        holiday_schedule = rule.schedule_day
                        rules.append(rule)
                    if "summerdesignday" in field:
                        rule = ScheduleRule(ScheduleDay("summerdesignday", [0], [Time(0, 0)]))
                        summer_designday_schedule = rule.schedule_day
                        rules.append(rule)
                    if "winterdesignday" in field:
                        rule = ScheduleRule(ScheduleDay("winterdesignday", [0], [Time(0, 0)]))
                        winter_designday_schedule = rule.schedule_day
                        rules.append(rule)
                    if "allotherdays" in field:
                        rule = ScheduleRule(ScheduleDay("allotherdays", [0], [Time(0, 0)]))
                        apply_mtx = [rul.week_apply_tuple for rul in schedule_rules]
                        if not apply_mtx:  # situation if allotherdays is the only rule.
                            rule.apply_all = True
                        else:
                            for j, dow in enumerate(zip(*apply_mtx)):
                                if not any(dow):
                                    rule.apply_day_by_dow(j + 1)
                        rules.append(rule)

                    for rule in rules:
                        # for each created rule in this `for` field, add rules to
                        # ScheduleRuleset list of rules and set start_date and end_date.
                        if len(rule.days_applied) != 0:
                            schedule_rules.append(rule)

                        # set range for rule (from previous `through` field)
                        rule.start_date = start_date
                        rule.end_date = end_date
                elif "until" in field:
                    _, hour, min = field.split(":")  # get hour and minutes

                    # value is applied `until` a certain Time, but `ScheduleDay` is
                    # applied `from` a certain Time. Also, Time is 0:23 Hours while IDF
                    # is 1:24 Hours.
                    until = Time(int(hour) - 1, int(min))  # to 0:23 Hours repr
                    untils.append(until)

                    # increment n
                    n += 1
                elif "interpolate" in field:
                    # Set interpolate on all rules for this `for` field
                    _, interpolate = field.split(":")
                    for rule in rules:
                        rule.schedule_day.interpolate = interpolate != "no"
                else:
                    begin = untils[n]  # index list of `until` times
                    for rule in rules:
                        # apply field value for each created rules; try to replace the
                        # placeholder value first, else add the value.
                        try:
                            rule.schedule_day.replace_value_by_time(begin, float(field))
                        except ValueError:
                            rule.schedule_day.add_value(float(field), begin)
            default_day_schedule = schedule_rules[0].schedule_day
            sch_ruleset = ScheduleRuleset(
                default_day_schedule=default_day_schedule,
                identifier=compact_sch[0],
                schedule_type_limit=schedule_type,
                schedule_rules=schedule_rules[1:]
            )
            ScheduleRuleset._apply_designdays_with_check(
                sch_ruleset,
                holiday_schedule,
                summer_designday_schedule,
                winter_designday_schedule)
            schedules.append(sch_ruleset)
        return schedules

    @staticmethod
    def average_schedules(identifier, schedules, weights=None, timestep_resolution=1):
        """Create a ScheduleRuleset that is a weighted average between other ScheduleRulesets.

        Args:
            identifier: Text string for a unique ID for the new unique ScheduleRuleset.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a
                model and in the exported IDF.
            schedules: A list of ScheduleRuleset objects that will be averaged together
                to make a new ScheduleRuleset.
            weights: An optional list of fractional numbers with the same length
                as the input schedules that sum to 1. These will be used to weight
                each of the ScheduleRuleset objects in the resulting average schedule.
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
            assert abs(sum(weights) - 1.0) <= 1e-9, 'Average schedule weights must ' \
                'sum to 1. Got {}.'.format(sum(weights))

        # if all input schedules are single week, the averaging process is a lot simpler
        if all([sched.is_single_week for sched in schedules]):
            rule_indices = [range(len(sched)) for sched in schedules]
            return ScheduleRuleset._get_avg_week(
                identifier, schedules, weights, timestep_resolution, rule_indices)
        else:
            # loop through 365 days of the year to find unique combinations of rules
            rules_each_day = []
            for doy in range(1, 366):
                rules_on_doy = tuple(tuple(
                    i for i, rule in enumerate(sched._schedule_rules)
                    if rule._start_doy <= doy <= rule._end_doy)
                    for sched in schedules)
                rules_each_day.append(rules_on_doy)
            unique_rule_sets = set(rules_each_day)
            # create the average week schedules from the unique combinations of rules
            week_schedules = []
            for i, rule_indices in enumerate(unique_rule_sets):
                week_identifier = '{}_{}'.format(identifier, i)
                week_sched = ScheduleRuleset._get_avg_week(week_identifier, schedules, weights,
                                                           timestep_resolution, rule_indices)
                week_schedules.append(week_sched)
            # create a dictionary mapping unique rule index lists to average week schedules
            rule_set_map = {}
            for rule_i, week_sched in zip(unique_rule_sets, week_schedules):
                rule_set_map[rule_i] = week_sched
            # loop through all 365 days of the year to find when rules change
            yr_wk_scheds = []
            yr_wk_dt_range = []
            prev_week_rules = None
            for doy in range(1, 366):
                week_rules = rules_each_day[doy - 1]
                if week_rules != prev_week_rules:  # change to a new rule set
                    yr_wk_scheds.append(rule_set_map[week_rules])
                    if doy != 1:
                        yr_wk_dt_range[-1].append(Date.from_doy(doy - 1))
                        yr_wk_dt_range.append([Date.from_doy(doy)])
                    else:
                        yr_wk_dt_range.append([Date(1, 1)])
                    prev_week_rules = week_rules
            yr_wk_dt_range[-1].append(Date(12, 31))

            # convert week ScheduleRulesets to_rules and assign start + end dates
            final_rules = []
            for wk_sch, dt_range in zip(yr_wk_scheds, yr_wk_dt_range):
                final_rules.extend(wk_sch.to_rules(dt_range[0], dt_range[1]))

            # add all rules to a final average ScheduleRuleset
            default_day_schedule = final_rules[0].schedule_day
            holiday_sch = yr_wk_scheds[0].holiday_schedule.duplicate()
            summer_dd_sch = yr_wk_scheds[0].summer_designday_schedule.duplicate()
            winter_dd_sch = yr_wk_scheds[0].winter_designday_schedule.duplicate()
            schedule_type = schedules[0].schedule_type_limit
            return ScheduleRuleset(
                identifier, default_day_schedule, final_rules[1:], schedule_type,
                holiday_sch, summer_dd_sch, winter_dd_sch)

    def _get_sch_values(self, sch_day_vals, dow, start_date, end_date,
                        hol_doy, hol_vals):
        """Get a list of values over a date range for a typical year."""
        values = []
        for doy in range(start_date.doy, end_date.doy + 1):
            if dow > 7:  # reset the day of the week to sunday
                dow = 1
            if doy in hol_doy:
                if hol_vals is not None:
                    values.extend(hol_vals)
                else:  # no holiday values; use default_day_schedule.
                    values.extend(sch_day_vals[-1])
            else:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.does_rule_apply(doy, dow):
                        values.extend(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.extend(sch_day_vals[-1])
            dow += 1
        return values

    def _get_sch_values_leap_year(self, sch_day_vals, dow, start_date, end_date,
                                  hol_doy, hol_vals):
        """Get a list of values over a date range for a leap year."""
        values = []
        for doy in range(start_date.doy, end_date.doy + 1):
            if dow > 7:  # reset the day of the week to sunday
                dow = 1
            if doy in hol_doy:
                if hol_vals is not None:
                    values.extend(hol_vals)
                else:  # no holiday values; use default_day_schedule.
                    values.extend(sch_day_vals[-1])
            else:
                for i, rule in enumerate(self._schedule_rules):  # see if rules apply
                    if rule.does_rule_apply_leap_year(doy, dow):
                        values.extend(sch_day_vals[i])
                        break
                else:  # no rule applies; use default_day_schedule.
                    values.extend(sch_day_vals[-1])
            dow += 1
        return values

    def _get_week_list(self, rule_indices):
        """Get a list of the ScheduleDay identifiers applied on each day of the week."""
        week_list = []
        for dow in range(7):
            for i in rule_indices:
                if self._schedule_rules[i].week_apply_tuple[dow]:
                    week_list.append(self._schedule_rules[i].schedule_day.identifier)
                    break
            else:  # no rule applies; use default_day_schedule.
                week_list.append(self.default_day_schedule.identifier)
        return week_list

    def _get_extra_week_fields(self):
        """Get schedule identifiers of extra days in Schedule:Week."""
        # add summer and winter design days
        week_fields = []
        if self._holiday_schedule is not None:
            week_fields.append(self._holiday_schedule.identifier)
        else:
            week_fields.append(self._default_day_schedule.identifier)
        if self._summer_designday_schedule is not None:
            week_fields.append(self._summer_designday_schedule.identifier)
        else:
            week_fields.append(self._default_day_schedule.identifier)
        if self._winter_designday_schedule is not None:
            week_fields.append(self._winter_designday_schedule.identifier)
        else:
            week_fields.append(self._default_day_schedule.identifier)
        for _ in range(2):  # add the extra 2 custom days that are rarely used in E+
            week_fields.append(self.default_day_schedule.identifier)
        return week_fields

    def _idf_week_schedule_from_rule_indices(self, rule_indices, week_index):
        """Create an IDF string of a week schedule from a list of rules indices."""
        week_sch_id = '{}_Week {}'.format(self.identifier, week_index)
        week_fields = [week_sch_id]
        # check rules that apply for the days of the week
        week_fields.extend(self._get_week_list(rule_indices))
        # add extra days (including summer and winter design days)
        week_fields.extend(self._get_extra_week_fields())
        week_schedule = generate_idf_string(
            'Schedule:Week:Daily', week_fields, self._schedule_week_comments)
        return week_schedule, week_sch_id

    def _idf_week_schedule_from_week_list(self, week_list, week_index):
        """Create an IDF string of a week schedule from a list ScheduleDay identifiers.
        """
        week_sch_id = '{}_Week {}'.format(self.identifier, week_index)
        week_fields = [week_sch_id]
        week_fields.extend(week_list)
        week_fields.extend(self._get_extra_week_fields())
        week_schedule = generate_idf_string(
            'Schedule:Week:Daily', week_fields, self._schedule_week_comments)
        return week_schedule, week_sch_id

    def _check_schedule_parent(self, schedule, sch_type='child'):
        """Used to ensure that a ScheduleDay object has only one parent ScheduleRuleset.

        This is important to ensure ScheduleRulesets remain self-contained units
        and that editing one ScheduleRuleset does not edit another one.
        """
        if schedule._parent is None or schedule._parent is self:
            schedule._parent = self
        else:
            raise ValueError(
                'ScheduleDay objects can be assigned to a ScheduleRuleset only once.\n'
                'ScheduleDay "{}" cannot be the {} of ScheduleRuleset "{}" since it is '
                'already assigned to "{}".\nTry duplicating the ScheduleDay, changing '
                'its identifier, and then assigning it to this ScheduleRuleset.'.format(
                    schedule.identifier, sch_type, self.identifier,
                    schedule._parent.identifier))

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
            self._check_schedule_parent(rule.schedule_day, 'schedule_rule')
        return rules

    @staticmethod
    def _check_rule(rule):
        """Check that an individual rule is a ScheduleRule."""
        assert isinstance(rule, ScheduleRule), \
            'Expected ScheduleRule for ScheduleRuleset. Got {}.'.format(type(rule))

    @staticmethod
    def _apply_designdays_with_check(sched, holiday_sch, summer_dd_sch, winter_dd_sch):
        """Apply summer + winter design day schedules with a check for duplicates."""
        try:
            sched.holiday_schedule = holiday_sch
        except ValueError:  # summer design day schedule is not unique
            holiday_sch = holiday_sch.duplicate()
            holiday_sch.identifier = '{}_Hol'.format(holiday_sch.identifier)
            sched.holiday_schedule = holiday_sch
        try:
            sched.summer_designday_schedule = summer_dd_sch
        except ValueError:  # summer design day schedule is not unique
            summer_dd_sch = summer_dd_sch.duplicate()
            summer_dd_sch.identifier = '{}_SmrDsn'.format(summer_dd_sch.identifier)
            sched.summer_designday_schedule = summer_dd_sch
        try:
            sched.winter_designday_schedule = winter_dd_sch
        except ValueError:  # winter design day schedule is not unique
            winter_dd_sch = winter_dd_sch.duplicate()
            winter_dd_sch.identifier = '{}_WntrDsn'.format(winter_dd_sch.identifier)
            sched.winter_designday_schedule = winter_dd_sch

    @staticmethod
    def _idf_day_schedule_dictionary(day_idf_strings):
        """Get a dictionary of DaySchedule objects from an IDF string list."""
        day_schedule_dict = {}
        for sch_str in day_idf_strings:
            sch_str = sch_str.strip()
            sch_obj = ScheduleDay.from_idf(sch_str)
            day_schedule_dict[sch_obj.identifier] = sch_obj
        return day_schedule_dict

    @staticmethod
    def _idf_week_schedule_dictionary(week_idf_strings, day_sch_dict):
        """Get a dictionary of ScheduleRule objects from Schedule:Week strings."""
        week_schedule_dict = {}
        week_designday_dict = {}
        for sch_str in week_idf_strings:
            sch_str = sch_str.strip()
            rules = ScheduleRule.extract_all_from_schedule_week(sch_str, day_sch_dict)
            if sch_str.startswith('Schedule:Week:Daily,'):
                ep_strs = parse_idf_string(sch_str)
                holiday = day_sch_dict[ep_strs[8]]
                summer_dd = day_sch_dict[ep_strs[9]]
                winter_dd = day_sch_dict[ep_strs[10]]
            else:
                ep_strs = parse_idf_string(sch_str, 'Schedule:Week:Compact,')
                holiday = summer_dd = winter_dd = rules[-1].schedule_day
                for i in range(1, len(ep_strs), 2):
                    day_type, day_sch_id = ep_strs[i].lower(), ep_strs[i + 1]
                    if 'holiday' in day_type:
                        holiday = day_sch_dict[day_sch_id]
                    elif 'summerdesignday' in day_type:
                        summer_dd = day_sch_dict[day_sch_id]
                    elif 'winterdesignday' in day_type:
                        winter_dd = day_sch_dict[day_sch_id]
            sch_week_id = ep_strs[0]
            week_schedule_dict[sch_week_id] = rules
            week_designday_dict[sch_week_id] = [holiday, summer_dd, winter_dd]
        return week_schedule_dict, week_designday_dict

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

    @staticmethod
    def _get_avg_week(identifier, schedules, weights, timestep_resolution, rule_indices):
        """Get an average week schedule across several schedules and rule_indices."""
        # get matrix with each ruleset schedule in rows and each day of week in cols
        val_mtx = []
        for s_i, sched in enumerate(schedules):
            week_list = []
            for dow in range(7):
                for i in rule_indices[s_i]:  # see if rules apply
                    if sched[i].week_apply_tuple[dow]:
                        week_list.append(sched[i].schedule_day)
                        break
                else:  # no rule applies; use default_day_schedule.
                    week_list.append(sched.default_day_schedule)

            # check the rules applied for holidays + summer and winter design days
            holiday = sched.default_day_schedule if sched._holiday_schedule \
                is None else sched._holiday_schedule
            week_list.append(holiday)
            summer = sched.default_day_schedule if sched._summer_designday_schedule \
                is None else sched._summer_designday_schedule
            week_list.append(summer)
            winter = sched.default_day_schedule if sched._winter_designday_schedule \
                is None else sched._winter_designday_schedule
            week_list.append(winter)
            # add all values to the matrix
            val_mtx.append([day_sch.values_at_timestep(timestep_resolution)
                            for day_sch in week_list])
        # transpose the matrix and compute weighted average values for each dow
        avg_mtx = []
        for dow_list in zip(*val_mtx):
            sch_vals = [sum([val * weights[i] for i, val in enumerate(values)])
                        for values in zip(*dow_list)]
            avg_mtx.append(sch_vals)
        # create the final ScheduleRuleset from the values
        return ScheduleRuleset.from_week_daily_values(
            identifier, avg_mtx[0], avg_mtx[1], avg_mtx[2], avg_mtx[3], avg_mtx[4],
            avg_mtx[5], avg_mtx[6], avg_mtx[7], timestep_resolution,
            schedules[0].schedule_type_limit, avg_mtx[8], avg_mtx[9])

    @staticmethod
    def _instance_in_array(object_instance, object_array):
        """Check if a specific object instance is already in an array.

        This can be much faster than  `if object_instance in object_array`
        when you expect to be testing a lot of the same instance of an object for
        inclusion in an array since the builtin method uses an == operator to
        test inclusion.
        """
        for val in object_array:
            if val is object_instance:
                return True
        return False

    def __len__(self):
        return len(self._schedule_rules)

    def __getitem__(self, key):
        return self._schedule_rules[key]

    def __iter__(self):
        return iter(self._schedule_rules)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, hash(self.default_day_schedule),
                hash(self.holiday_schedule), hash(self.summer_designday_schedule),
                hash(self.winter_designday_schedule), hash(self.schedule_type_limit)) + \
            tuple(hash(rule) for rule in self.schedule_rules)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ScheduleRuleset) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        holiday = self._holiday_schedule.duplicate() if \
            self._holiday_schedule is not None else None
        summer = self._summer_designday_schedule.duplicate() if \
            self._summer_designday_schedule is not None else None
        winter = self._winter_designday_schedule.duplicate() if \
            self._winter_designday_schedule is not None else None
        new_obj = ScheduleRuleset(
            self.identifier, self.default_day_schedule.duplicate(),
            [rule.duplicate() for rule in self._schedule_rules],
            self._schedule_type_limit, holiday, summer, winter)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ScheduleRuleset: {} [default day: {}] [{} rules]'.format(
            self.display_name, self.default_day_schedule.display_name,
            len(self._schedule_rules))
