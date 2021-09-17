# coding=utf-8
from honeybee_energy.load.people import People
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee.altnumber import autocalculate

from ladybug.dt import Time, Date

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_people_init(userdatadict):
    """Test the initialization of People and basic properties."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy', simple_office,
                                   None, schedule_types.fractional)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    people.user_data = userdatadict
    str(people)  # test the string representation

    assert people.identifier == 'Open Office Zone People'
    assert people.people_per_area == 0.05
    assert people.area_per_person == 20
    assert people.occupancy_schedule.identifier == 'Office Occupancy'
    assert people.occupancy_schedule.schedule_type_limit == schedule_types.fractional
    assert people.occupancy_schedule == occ_schedule
    assert people.activity_schedule.is_constant
    assert people.activity_schedule.schedule_type_limit == schedule_types.activity_level
    assert people.activity_schedule.values() == [120] * 8760
    assert people.radiant_fraction == 0.3
    assert people.latent_fraction == autocalculate
    assert people.user_data == userdatadict


def test_people_setability(userdatadict):
    """Test the setting of properties of People."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy', simple_office,
                                   None, schedule_types.fractional)
    constant_ppl = ScheduleRuleset.from_constant_value(
        'Constant Occ', 1, schedule_types.fractional)
    sleeping_act = ScheduleRuleset.from_constant_value(
        'Sleeping Activity', 95, schedule_types.activity_level)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    people.user_data = userdatadict

    people.identifier = 'Office Zone People'
    assert people.identifier == 'Office Zone People'
    people.people_per_area = 0.1
    assert people.people_per_area == 0.1
    assert people.area_per_person == 10
    people.area_per_person = 20
    assert people.area_per_person == 20
    assert people.people_per_area == 0.05
    people.occupancy_schedule = constant_ppl
    assert people.occupancy_schedule == constant_ppl
    people.activity_schedule = sleeping_act
    assert people.activity_schedule.schedule_type_limit == schedule_types.activity_level
    assert people.activity_schedule.values() == [95] * 8760
    people.radiant_fraction = 0.4
    assert people.radiant_fraction == 0.4
    people.latent_fraction = 0.2
    assert people.latent_fraction == 0.2


def test_people_equality(userdatadict):
    """Test the equality of People objects."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    occ_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                   [weekend_rule], schedule_types.fractional)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    people.user_data = userdatadict
    people_dup = people.duplicate()
    people_alt = People('Open Office Zone People', 0.05,
                        ScheduleRuleset.from_constant_value(
                            'Constant', 1, schedule_types.fractional))

    assert people is people
    assert people is not people_dup
    assert people == people_dup
    people_dup.people_per_area = 0.06
    assert people != people_dup
    assert people != people_alt


def test_people_lockability(userdatadict):
    """Test the lockability of People objects."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    occ_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                   [weekend_rule], schedule_types.fractional)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    people.user_data = userdatadict

    people.people_per_area = 0.1
    people.lock()
    with pytest.raises(AttributeError):
        people.people_per_area = 0.1
    with pytest.raises(AttributeError):
        people.occupancy_schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    people.unlock()
    people.people_per_area = 0.05
    with pytest.raises(AttributeError):
        people.occupancy_schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_people_init_from_idf():
    """Test the initialization of People from_idf."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    occ_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                   [weekend_rule], schedule_types.fractional)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    sched_dict = {occ_schedule.identifier: occ_schedule}

    zone_id = 'Test Zone'
    idf_str = people.to_idf(zone_id)
    rebuilt_people, rebuilt_zone_id = People.from_idf(idf_str, sched_dict)
    assert people == rebuilt_people
    assert zone_id == rebuilt_zone_id


def test_people_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    weekday_office = ScheduleDay('Weekday Office Occupancy', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Occupancy', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    occ_schedule = ScheduleRuleset('Office Occupancy', weekday_office,
                                   [weekend_rule], schedule_types.fractional)
    people = People('Open Office Zone People', 0.05, occ_schedule)
    people.user_data = userdatadict

    ppl_dict = people.to_dict()
    new_people = People.from_dict(ppl_dict)
    assert new_people == people
    assert ppl_dict == new_people.to_dict()


def test_people_average():
    """Test the People.average method."""
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
    lobby_activity = ScheduleRuleset.from_constant_value('Lobby Activity Sched', 160,
                                                         schedule_types.activity_level)

    office_people = People('Office People', 0.05, office_schedule)
    lobby_people = People('Lobby People', 0.1, lobby_schedule, lobby_activity, 0.4, 0.2)

    office_avg = People.average('Office Average People', [office_people, lobby_people])

    assert office_avg.people_per_area == pytest.approx(0.075, rel=1e-3)
    assert office_avg.radiant_fraction == pytest.approx(0.35, rel=1e-3)
    assert office_avg.latent_fraction == autocalculate

    week_vals = office_avg.occupancy_schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals

    act_vals = office_avg.activity_schedule.values(end_date=Date(1, 1))
    assert act_vals == [140] * 24
