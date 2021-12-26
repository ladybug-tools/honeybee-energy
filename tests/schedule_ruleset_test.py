# coding=utf-8
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Date, Time
from ladybug.datatype import fraction
from ladybug.analysisperiod import AnalysisPeriod

import pytest
import json
from .fixtures.userdata_fixtures import userdatadict

def test_schedule_ruleset_init(userdatadict):
    """Test the ScheduleRuleset initialization and basic properties."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)
    summer_office = ScheduleDay('Summer Office Occupancy', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(22, 0)])
    winter_office = ScheduleDay('Winter Office Occupancy', [0])
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional,
                               sunday_office, summer_office, winter_office)
    schedule.user_data = userdatadict
    str(schedule)  # test the string representation

    assert schedule.identifier == 'Office Occupancy'
    assert schedule.default_day_schedule == weekday_office
    assert schedule.holiday_schedule == sunday_office
    assert schedule.summer_designday_schedule == summer_office
    assert schedule.winter_designday_schedule == winter_office
    assert schedule.schedule_type_limit == schedule_types.fractional
    assert schedule.user_data == userdatadict
    assert len(schedule.schedule_rules) == 2
    assert len(schedule.day_schedules) == 5

    schedule.remove_rule(1)
    assert len(schedule.schedule_rules) == 1
    schedule.add_rule(sun_rule)
    assert len(schedule.schedule_rules) == 2

    with pytest.raises(ValueError):
        schedule = ScheduleRuleset('Office Occupancy', weekday_office)


def test_schedule_ruleset_equality(userdatadict):
    """Test the equality of ScheduleRuleset objects."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    schedule.user_data = userdatadict
    schedule_dup = schedule.duplicate()
    residential_schedule = ScheduleRuleset.from_daily_values(
        'Residence Occupancy', [1, 1, 1, 1, 1, 1, 1, 0.5, 0, 0, 0, 0, 0, 0, 0, 0,
                                0.25, 0.5, 0.5, 0.5, 0.5, 1, 1, 1])

    assert schedule is schedule
    assert schedule is not schedule_dup
    assert schedule == schedule_dup
    schedule_dup.schedule_rules[0].apply_friday = True
    assert schedule != schedule_dup
    assert schedule != residential_schedule


def test_schedule_ruleset_lockability(userdatadict):
    """Test the lockability of ScheduleRuleset objects."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    schedule.user_data = userdatadict

    schedule.schedule_rules[0].apply_monday = True
    schedule.lock()
    with pytest.raises(AttributeError):
        schedule.schedule_rules[0].apply_monday = False
    with pytest.raises(AttributeError):
        schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    schedule.unlock()
    schedule.schedule_rules[0].apply_monday = False
    schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_schedule_ruleset_values():
    """Test the ScheduleRuleset values method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)

    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional)

    assert len(schedule.values()) == 8760
    assert len(schedule.values(leap_year=True)) == 8784

    sch_week_vals = schedule.values(end_date=Date(1, 7))
    assert len(sch_week_vals) == 24 * 7
    assert sch_week_vals[:24] == sunday_office.values_at_timestep()
    assert sch_week_vals[24:48] == weekday_office.values_at_timestep()
    assert sch_week_vals[144:] == saturday_office.values_at_timestep()

    sch_week_vals_10_min = schedule.values(6, end_date=Date(1, 7))
    assert len(sch_week_vals_10_min) == 24 * 7 * 6


def test_schedule_ruleset_data_collection():
    """Test the ScheduleRuleset data_collection method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)

    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional)

    sch_data = schedule.data_collection()
    assert len(sch_data) == 8760
    assert isinstance(sch_data.header.data_type, fraction.Fraction)
    assert sch_data.header.unit == 'fraction'
    assert sch_data.header.analysis_period == AnalysisPeriod()


def test_schedule_ruleset_shift_by_step():
    """Test the ScheduleRuleset shift_by_step method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)

    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional)
    shift_schedule = schedule.shift_by_step(-1)

    default_vals = weekday_office.values_at_timestep()
    shift_vals = default_vals[1:] + [default_vals[0]]
    assert shift_schedule.default_day_schedule.values_at_timestep() == shift_vals


def test_schedule_ruleset_from_constant_value():
    """Test the initialization of ScheduleRuleset from_constant_value."""
    sched = ScheduleRuleset.from_constant_value('Shade Transmittance', 0.5)

    assert sched.identifier == 'Shade Transmittance'
    assert len(sched.default_day_schedule.values) == 1
    assert sched.default_day_schedule.values[0] == 0.5
    assert len(sched.schedule_rules) == 0
    assert sched.summer_designday_schedule is None
    assert sched.winter_designday_schedule is None


def test_schedule_ruleset_from_daily_values():
    """Test the initialization of ScheduleRuleset from_daily_values."""
    test_vals = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1, 1, 1,
                 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5]
    sched = ScheduleRuleset.from_daily_values('Simple Repeating', test_vals)
    day_sched = ScheduleDay(
        'Simple Repeating_Day Schedule', [0.5, 1, 0.5, 1, 0.5],
        [Time(0, 0), Time(6, 0), Time(12, 0), Time(16, 0), Time(20, 0)])
    sched_alt = ScheduleRuleset('Simple Repeating', day_sched)

    assert sched.identifier == 'Simple Repeating'
    assert len(sched.schedule_rules) == 0
    assert sched.summer_designday_schedule is None
    assert sched.winter_designday_schedule is None
    assert sched == sched_alt


def test_schedule_ruleset_from_week_daily_values():
    """Test the initialization of ScheduleRuleset from_week_daily_values."""
    weekday = [0, 0, 0, 0, 0, 0, 0, 0.1, 0.25, 1, 1, 1,
               0.5, 1, 1, 1, 1, 0.5, 0.5, 0.25, 0, 0, 0, 0]
    sat = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0.25, 0.25, 0.25,
           0.25, 0.25, 0.25, 0.25, 0.25, 0, 0, 0, 0, 0, 0, 0]
    sun = [0 for i in range(24)]

    schedule = ScheduleRuleset.from_week_daily_values(
        'Office Occ', sun, weekday, weekday, weekday, weekday, weekday, sat, sun,
        schedule_type_limit=schedule_types.fractional)

    assert schedule.identifier == 'Office Occ'
    assert len(schedule.schedule_rules) == 2
    assert schedule.summer_designday_schedule.values_at_timestep() == weekday
    assert schedule.winter_designday_schedule.values_at_timestep() == sun

    sch_week_vals = schedule.values(end_date=Date(1, 7))
    assert sch_week_vals == sun + weekday + weekday + weekday + weekday + weekday + sat


def test_schedule_ruleset_from_week_day_schedules():
    """Test the initialization of ScheduleRuleset from_week_day_schedules."""
    weekday_vals = [0, 0, 0, 0, 0, 0, 0, 0.1, 0.25, 1, 1, 1,
                    0.5, 1, 1, 1, 1, 0.5, 0.5, 0.25, 0, 0, 0, 0]
    sat_vals = [0, 0, 0, 0, 0, 0, 0, 0, 0, 0.25, 0.25, 0.25,
                0.25, 0.25, 0.25, 0.25, 0.25, 0, 0, 0, 0, 0, 0, 0]
    sun_vals = [0 for i in range(24)]
    weekday = ScheduleDay.from_values_at_timestep('Weekday Office Occ', weekday_vals)
    sat = ScheduleDay.from_values_at_timestep('Saturday Office Occ', sat_vals)
    sun = ScheduleDay.from_values_at_timestep('Sunday Office Occ', sun_vals)

    schedule = ScheduleRuleset.from_week_day_schedules(
        'Office Occ', sun, weekday, weekday, weekday, weekday, weekday, sat, sun,
        weekday, sun, schedule_types.fractional)

    assert schedule.identifier == 'Office Occ'
    assert len(schedule.schedule_rules) == 2
    assert schedule.summer_designday_schedule.values_at_timestep() == weekday_vals
    assert schedule.winter_designday_schedule.values_at_timestep() == sun_vals

    sch_week_vals = schedule.values(end_date=Date(1, 7))
    assert sch_week_vals == sun_vals + weekday_vals + weekday_vals + weekday_vals + \
        weekday_vals + weekday_vals + sat_vals


def test_schedule_ruleset_from_idf_file():
    """Test the initalization of ScheduleRuleset from file."""
    office_sched_idf = './tests/idf/OfficeOccupancySchedule.idf'
    office_scheds = ScheduleRuleset.extract_all_from_idf_file(office_sched_idf)

    office_occ = office_scheds[0]

    assert office_occ.identifier == 'Medium Office Bldg Occ'
    assert isinstance(office_occ.default_day_schedule, ScheduleDay)
    assert office_occ.default_day_schedule.identifier == \
        'Medium Office Bldg Occ Sunday Schedule'
    assert office_occ.summer_designday_schedule.identifier == \
        'Medium Office Bldg Occ Summer Design Day'
    assert office_occ.winter_designday_schedule.identifier == \
        'Medium Office Bldg Occ Winter Design Day'
    assert len(office_occ.schedule_rules) == 2
    assert office_occ.schedule_rules[0].schedule_day.identifier == \
        'Medium Office Bldg Occ Default Schedule'
    assert office_occ.schedule_rules[1].schedule_day.identifier == \
        'Medium Office Bldg Occ Saturday Schedule'

    assert isinstance(office_occ.schedule_type_limit, ScheduleTypeLimit)


def test_schedule_ruleset_from_idf_file_compact():
    """Test the initalization of ScheduleRuleset from file with Schedule:Week:Compact
    and Schedule:Compact.
    """
    office_sched_idf = './tests/idf/OfficeOccupancySchedule_Compact.idf'
    office_scheds = ScheduleRuleset.extract_all_from_idf_file(office_sched_idf, True)

    office_occ = office_scheds[0]

    assert office_occ.identifier == 'Medium Office Bldg Occ'
    assert isinstance(office_occ.default_day_schedule, ScheduleDay)
    assert office_occ.default_day_schedule.identifier == \
        'Medium Office Bldg Occ Default Schedule'
    assert office_occ.summer_designday_schedule.identifier == \
        'Medium Office Bldg Occ Summer Design Day'
    assert office_occ.winter_designday_schedule.identifier == \
        'Medium Office Bldg Occ Winter Design Day'
    assert len(office_occ.schedule_rules) == 2
    assert office_occ.schedule_rules[0].schedule_day.identifier == \
        'Medium Office Bldg Occ Saturday Schedule'
    assert office_occ.schedule_rules[1].schedule_day.identifier == \
        'Medium Office Bldg Occ Sunday Schedule'

    office_occ = office_scheds[1]
    assert office_occ.schedule_rules[0].schedule_day.identifier == \
        "saturday"

    assert isinstance(office_occ.schedule_type_limit, ScheduleTypeLimit)


def test_schedule_ruleset_from_idf_file_cross_referenced():
    """Test ScheduleRuleset from_idf_file with cross-referenced ScheduleDay."""
    cool_sched_idf = './tests/idf/cross_referenced_schedule_day.idf'
    cooling_avail_schs = ScheduleRuleset.extract_all_from_idf_file(cool_sched_idf)

    cooling_avail = cooling_avail_schs[0]
    assert len(cooling_avail.schedule_rules) == 2


def test_schedule_ruleset_to_from_idf(userdatadict):
    """Test the ScheduleRuleset to_idf and from_idf methods."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    week_rule = ScheduleRule(weekday_office)
    week_rule.apply_weekday = True
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    summer_office = ScheduleDay('Summer Office Occupancy', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(22, 0)])
    winter_office = ScheduleDay('Winter Office Occupancy', [0])
    schedule = ScheduleRuleset('Office Occupancy', sunday_office,
                               [week_rule, sat_rule], schedule_types.fractional,
                               summer_office, winter_office)
    schedule.user_data = userdatadict

    year_sched, week_scheds = schedule.to_idf()
    assert len(week_scheds) == 1

    day_scheds = (weekday_office.to_idf(), saturday_office.to_idf(),
                  sunday_office.to_idf(), summer_office.to_idf(),
                  winter_office.to_idf())
    sch_type = schedule_types.fractional.to_idf()

    rebuilt_schedule = ScheduleRuleset.from_idf(year_sched, week_scheds,
                                                day_scheds, sch_type)
    rebuilt_year_sched, rebuilt_week_scheds = rebuilt_schedule.to_idf()

    assert rebuilt_year_sched == year_sched
    assert rebuilt_week_scheds[0] == week_scheds[0]


def test_schedule_ruleset_to_idf_date_range():
    """Test the ScheduleRuleset to_idf and from_idf methods."""
    weekday_school = ScheduleDay('Weekday School Year', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(8, 0), Time(15, 0), Time(18, 0)])
    weekend_school = ScheduleDay('Weekend School Year', [0])
    weekday_summer = ScheduleDay('Weekday Summer', [0, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_summer = ScheduleDay('Weekend Summer', [0])

    summer_weekday_rule = ScheduleRule(
        weekday_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekday_rule.apply_weekday = True
    summer_weekend_rule = ScheduleRule(
        weekend_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekend_rule.apply_weekend = True
    school_weekend_rule = ScheduleRule(weekend_school)
    school_weekend_rule.apply_weekend = True

    summer_design = ScheduleDay('School Summer Design', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(18, 0)])
    winter_design = ScheduleDay('School Winter Design', [0])

    schedule = ScheduleRuleset('School Occupancy', weekday_school,
                               [summer_weekday_rule, summer_weekend_rule,
                                school_weekend_rule],
                               schedule_types.fractional, summer_design, winter_design)

    year_sched, week_scheds = schedule.to_idf()

    assert len(year_sched.split(',')) > 6
    assert len(week_scheds) == 2


def test_schedule_ruleset_dict_methods(userdatadict):
    """Test the ScheduleRuleset to/from dict methods."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)
    summer_office = ScheduleDay('Summer Office Occupancy', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(22, 0)])
    winter_office = ScheduleDay('Winter Office Occupancy', [0])
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional,
                               summer_office, winter_office)
    schedule.user_data = userdatadict

    sch_dict = schedule.to_dict()
    new_schedule = ScheduleRuleset.from_dict(sch_dict)
    assert new_schedule == schedule
    assert sch_dict == new_schedule.to_dict()


def test_schedule_ruleset_to_rules():
    """Test the ScheduleRuleset to_rules method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    sunday_office = ScheduleDay('Sunday Office Occupancy', [0])
    sat_rule = ScheduleRule(saturday_office, apply_saturday=True)
    sun_rule = ScheduleRule(sunday_office, apply_sunday=True)
    schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                               [sat_rule, sun_rule], schedule_types.fractional)

    rules = schedule.to_rules(Date(6, 1), Date(8, 31))

    assert len(rules) == 3
    for rule in rules:
        assert rule.start_date == Date(6, 1)
        assert rule.end_date == Date(8, 31)


def test_schedule_ruleset_average_schedules():
    """Test the average_schedules method."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Occupancy', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Occupancy', [0])
    weekend_lobby = ScheduleDay('Weekend Office Occupancy', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Occupancy', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_avg = ScheduleRuleset.average_schedules(
        'Office Average', [office_schedule, lobby_schedule])
    week_vals = office_avg.values(end_date=Date(1, 7))

    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals
    assert (len(office_avg.schedule_rules)) == 1


def test_schedule_ruleset_average_schedules_weights():
    """Test the average_schedules method with weights."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(8, 0), Time(17, 0), Time(20, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Occupancy', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Occupancy', [0])
    weekend_lobby = ScheduleDay('Weekend Office Occupancy', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Occupancy', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_avg = ScheduleRuleset.average_schedules(
        'Office Average', [office_schedule, lobby_schedule], [0.75, 0.25])
    week_vals = office_avg.values(end_date=Date(1, 7))

    avg_vals = [0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 0.025, 1.0,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.625, 0.625,
                0.625, 0.025, 0.025, 0.025, 0.025]
    assert week_vals[:24] == [0.025] * 24
    assert week_vals[24:48] == avg_vals
    assert (len(office_avg.schedule_rules)) == 1


def test_schedule_ruleset_average_schedules_date_range():
    """Test the ScheduleRuleset average_schedules method with schedules over a date range."""
    weekday_school = ScheduleDay('Weekday School Year', [0.1, 1, 0.1],
                                 [Time(0, 0), Time(8, 0), Time(17, 0)])
    weekend_school = ScheduleDay('Weekend School Year', [0.1])
    weekday_summer = ScheduleDay('Weekday Summer', [0, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_summer = ScheduleDay('Weekend Summer', [0])

    summer_weekday_rule = ScheduleRule(
        weekday_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekday_rule.apply_weekday = True
    summer_weekend_rule = ScheduleRule(
        weekend_summer, start_date=Date(7, 1), end_date=Date(9, 1))
    summer_weekend_rule.apply_weekend = True
    school_weekend_rule = ScheduleRule(weekend_school)
    school_weekend_rule.apply_weekend = True

    summer_design = ScheduleDay('School Summer Design', [0, 1, 0.25],
                                [Time(0, 0), Time(6, 0), Time(18, 0)])
    winter_design = ScheduleDay('School Winter Design', [0])

    all_rules = [summer_weekday_rule, summer_weekend_rule, school_weekend_rule]
    school_schedule = ScheduleRuleset(
        'School Occupancy', weekday_school, all_rules, schedule_types.fractional,
        summer_design, winter_design)
    lobby_schedule = ScheduleRuleset.from_constant_value(
        'Lobby Occupancy', 0.1, schedule_types.fractional)

    school_avg = ScheduleRuleset.average_schedules(
        'Office Average', [school_schedule, lobby_schedule])

    week_vals = school_avg.values(end_date=Date(1, 7))
    avg_vals = [0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.1, 0.55,
                0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.55, 0.1, 0.1,
                0.1, 0.1, 0.1, 0.1, 0.1]
    assert week_vals[:24] == [0.1] * 24
    assert week_vals[24:48] == avg_vals

    week_vals = school_avg.values(start_date=Date(7, 1), end_date=Date(7, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.3, 0.3, 0.3,
                0.3, 0.3, 0.3, 0.3, 0.3, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals


def test_schedule_ruleset_reversed():
    """Test the to_idf method with a reversed rule."""
    rev_sch_file = 'tests/json/reversed_sch_ruleset.json'
    with open(rev_sch_file) as sf:
        sch_dict = json.load(sf)
    school_schedule = ScheduleRuleset.from_dict(sch_dict)

    year_schedule, week_schedules = school_schedule.to_idf()
    assert len(year_schedule.split('\n')) == 18
    assert len(week_schedules) == 2
