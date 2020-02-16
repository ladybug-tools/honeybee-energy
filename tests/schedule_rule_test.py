# coding=utf-8
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule

from ladybug.dt import Date, Time

import pytest


def test_schedule_rule_init():
    """Test the ScheduleRule initialization and basic properties."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    sched_rule = ScheduleRule(simple_office)
    sched_rule.apply_weekday = True

    str(sched_rule)  # test the string representation

    assert not sched_rule.apply_sunday
    assert sched_rule.apply_monday
    assert sched_rule.apply_tuesday
    assert sched_rule.apply_wednesday
    assert sched_rule.apply_thursday
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday
    assert sched_rule.apply_weekday
    assert not sched_rule.apply_weekend

    assert sched_rule.start_date == Date(1, 1)
    assert sched_rule.end_date == Date(12, 31)


def test_schedule_rule_equality():
    """Test the equality of ScheduleRule objects."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekday_rule = ScheduleRule(weekday_office)
    weekday_rule.apply_weekday = True
    weekday_rule_dup = weekday_rule.duplicate()
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)

    assert weekday_rule is weekday_rule
    assert weekday_rule is not weekday_rule_dup
    assert weekday_rule == weekday_rule_dup
    weekday_rule_dup.apply_friday = False
    assert weekday_rule != weekday_rule_dup
    assert weekday_rule != sat_rule


def test_schedule_rule_lockability():
    """Test the lockability of the ScheduleRule."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekday_rule = ScheduleRule(weekday_office)
    weekday_rule.apply_weekday = True

    weekday_rule.apply_monday = False
    weekday_rule.lock()
    with pytest.raises(AttributeError):
        weekday_rule.apply_monday = True
    with pytest.raises(AttributeError):
        weekday_rule.schedule_day.remove_value_by_time(Time(17, 0))
    weekday_rule.unlock()
    weekday_rule.apply_monday = True
    weekday_rule.schedule_day.remove_value_by_time(Time(17, 0))


def test_schedule_rule_apply():
    """Test the ScheduleRule apply properties."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    sched_rule = ScheduleRule(simple_office)

    assert not sched_rule.apply_sunday
    sched_rule.apply_sunday = True
    assert sched_rule.apply_sunday
    assert not sched_rule.apply_monday
    sched_rule.apply_monday = True
    assert sched_rule.apply_monday
    assert not sched_rule.apply_tuesday
    sched_rule.apply_tuesday = True
    assert sched_rule.apply_tuesday
    assert not sched_rule.apply_wednesday
    sched_rule.apply_wednesday = True
    assert sched_rule.apply_wednesday
    assert not sched_rule.apply_thursday
    sched_rule.apply_thursday = True
    assert sched_rule.apply_thursday
    assert not sched_rule.apply_friday
    sched_rule.apply_friday = True
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday
    sched_rule.apply_saturday = True
    assert sched_rule.apply_saturday

    assert sched_rule.apply_weekday
    assert sched_rule.apply_weekend
    assert sched_rule.apply_all


def test_schedule_rule_apply_day_by_name():
    """Test the ScheduleRule apply_day_by_name properties."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    sched_rule = ScheduleRule(simple_office)

    assert not sched_rule.apply_sunday
    sched_rule.apply_day_by_name('Sunday')
    assert sched_rule.apply_sunday
    assert not sched_rule.apply_monday
    sched_rule.apply_day_by_name('Monday')
    assert sched_rule.apply_monday
    assert not sched_rule.apply_tuesday
    sched_rule.apply_day_by_name('Tuesday')
    assert sched_rule.apply_tuesday
    assert not sched_rule.apply_wednesday
    sched_rule.apply_day_by_name('Wednesday')
    assert sched_rule.apply_wednesday
    assert not sched_rule.apply_thursday
    sched_rule.apply_day_by_name('Thursday')
    assert sched_rule.apply_thursday
    assert not sched_rule.apply_friday
    sched_rule.apply_day_by_name('Friday')
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday
    sched_rule.apply_day_by_name('Saturday')
    assert sched_rule.apply_saturday

    assert sched_rule.apply_weekday
    assert sched_rule.apply_weekend
    assert sched_rule.apply_all


def test_schedule_rule_apply_day_by_dow():
    """Test the ScheduleRule apply_day_by_dow properties."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    sched_rule = ScheduleRule(simple_office)

    assert not sched_rule.apply_sunday
    sched_rule.apply_day_by_dow(1)
    assert sched_rule.apply_sunday
    assert not sched_rule.apply_monday
    sched_rule.apply_day_by_dow(2)
    assert sched_rule.apply_monday
    assert not sched_rule.apply_tuesday
    sched_rule.apply_day_by_dow(3)
    assert sched_rule.apply_tuesday
    assert not sched_rule.apply_wednesday
    sched_rule.apply_day_by_dow(4)
    assert sched_rule.apply_wednesday
    assert not sched_rule.apply_thursday
    sched_rule.apply_day_by_dow(5)
    assert sched_rule.apply_thursday
    assert not sched_rule.apply_friday
    sched_rule.apply_day_by_dow(6)
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday
    sched_rule.apply_day_by_dow(7)
    assert sched_rule.apply_saturday

    assert sched_rule.apply_weekday
    assert sched_rule.apply_weekend
    assert sched_rule.apply_all


def test_schedule_does_rule_apply():
    """Test the ScheduleRule does_rule_apply properties."""
    weekday_school = ScheduleDay('Weekday School Year', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(8, 0), Time(15, 0), Time(18, 0)])
    weekend_school = ScheduleDay('Weekend School Year', [0])
    weekday_summer = ScheduleDay('Weekday Summer', [0, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_summer = ScheduleDay('Weekend Summer', [0])

    school_weekday_rule = ScheduleRule(weekday_school)
    school_weekday_rule.apply_weekday = True
    school_weekend_rule = ScheduleRule(weekend_school)
    school_weekend_rule.apply_weekend = True

    summer_weekday_rule = ScheduleRule(
        weekday_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekday_rule.apply_weekday = True
    summer_weekend_rule = ScheduleRule(
        weekend_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekend_rule.apply_weekend = True

    assert school_weekday_rule.does_rule_apply(1, 4)
    assert not school_weekday_rule.does_rule_apply(1, 1)

    assert school_weekend_rule.does_rule_apply(1, 1)
    assert not school_weekend_rule.does_rule_apply(1, 4)

    assert summer_weekday_rule.does_rule_apply(Date(7, 15).doy, 4)
    assert not summer_weekday_rule.does_rule_apply(Date(7, 15).doy, 1)
    assert not summer_weekday_rule.does_rule_apply(1, 4)

    assert school_weekend_rule.does_rule_apply(Date(7, 15).doy, 1)
    assert not school_weekend_rule.does_rule_apply(Date(7, 15).doy, 4)
    assert not summer_weekday_rule.does_rule_apply(1, 1)


def test_schedule_rule_from_days_applied():
    """Test the ScheduleRule from_days_applied method."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])

    sched_rule = ScheduleRule.from_days_applied(
        simple_office, ['monday', 'tuesday', 'wednesday', 'thursday', 'friday'])
    assert not sched_rule.apply_sunday
    assert sched_rule.apply_monday
    assert sched_rule.apply_tuesday
    assert sched_rule.apply_wednesday
    assert sched_rule.apply_thursday
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday
    sched_rule = ScheduleRule.from_days_applied(simple_office, ['weekday'])
    assert not sched_rule.apply_sunday
    assert sched_rule.apply_monday
    assert sched_rule.apply_tuesday
    assert sched_rule.apply_wednesday
    assert sched_rule.apply_thursday
    assert sched_rule.apply_friday
    assert not sched_rule.apply_saturday


def test_schedule_day_dict_methods():
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    sched_rule = ScheduleRule(simple_office)
    sched_rule.apply_weekday = True

    rule_dict = sched_rule.to_dict()
    new_sched_rule = ScheduleRule.from_dict(rule_dict)
    assert new_sched_rule == sched_rule
    assert rule_dict == new_sched_rule.to_dict()
