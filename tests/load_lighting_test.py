# coding=utf-8
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time, Date

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_lighting_init(userdatadict): 
    """Test the initialization of Lighting and basic properties."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Lighting', simple_office,
                               None, schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    lighting.user_data = userdatadict
    str(lighting)  # test the string representation

    assert lighting.identifier == 'Open Office Zone Lighting'
    assert lighting.watts_per_area == 10
    assert lighting.schedule.identifier == 'Office Lighting'
    assert lighting.schedule.schedule_type_limit == schedule_types.fractional
    assert lighting.schedule == schedule
    assert lighting.return_air_fraction == 0
    assert lighting.radiant_fraction == 0.32
    assert lighting.visible_fraction == 0.25
    assert lighting.baseline_watts_per_area == 11.84029
    assert lighting.user_data == userdatadict


def test_lighting_setability(userdatadict):
    """Test the setting of properties of Lighting."""
    simple_office = ScheduleDay('Simple Weekday Light', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Lighting', simple_office,
                               None, schedule_types.fractional)
    constant = ScheduleRuleset.from_constant_value(
        'Constant Light', 1, schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    lighting.user_data = userdatadict

    lighting.identifier = 'Office Zone Lighting'
    assert lighting.identifier == 'Office Zone Lighting'
    lighting.watts_per_area = 6
    assert lighting.watts_per_area == 6
    lighting.schedule = constant
    assert lighting.schedule == constant
    assert lighting.schedule.values() == [1] * 8760
    lighting.return_air_fraction = 0.1
    assert lighting.return_air_fraction == 0.1
    lighting.radiant_fraction = 0.4
    assert lighting.radiant_fraction == 0.4
    lighting.visible_fraction = 0.2
    assert lighting.visible_fraction == 0.2
    lighting.baseline_watts_per_area = 5.0
    assert lighting.baseline_watts_per_area == 5.0
    assert lighting.user_data == userdatadict


def test_lighting_equality(userdatadict):
    """Test the equality of Lighting objects."""
    weekday_office = ScheduleDay('Weekday Office Lighting', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Lighting', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Lighting', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    lighting.user_data = userdatadict
    lighting_dup = lighting.duplicate()
    lighting_alt = Lighting(
        'Open Office Zone Lighting', 10,
        ScheduleRuleset.from_constant_value('Constant', 1, schedule_types.fractional))

    assert lighting is lighting
    assert lighting is not lighting_dup
    assert lighting == lighting_dup
    lighting_dup.watts_per_area = 6
    assert lighting != lighting_dup
    assert lighting != lighting_alt


def test_lighting_lockability(userdatadict):
    """Test the lockability of Lighting objects."""
    weekday_office = ScheduleDay('Weekday Office Lighting', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Lighting', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Lighting', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    lighting.user_data = userdatadict

    lighting.watts_per_area = 6
    lighting.lock()
    with pytest.raises(AttributeError):
        lighting.watts_per_area = 8
    with pytest.raises(AttributeError):
        lighting.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    lighting.unlock()
    lighting.watts_per_area = 8
    with pytest.raises(AttributeError):
        lighting.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_lighting_init_from_idf():
    """Test the initialization of Lighting from_idf."""
    weekday_office = ScheduleDay('Weekday Office Lighting', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Lighting', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Lighting', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    sched_dict = {schedule.identifier: schedule}

    zone_id = 'Test Zone'
    idf_str = lighting.to_idf(zone_id)
    rebuilt_lighting, rebuilt_zone_id = Lighting.from_idf(idf_str, sched_dict)
    assert lighting == rebuilt_lighting
    assert zone_id == rebuilt_zone_id


def test_lighting_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    weekday_office = ScheduleDay('Weekday Office Lighting', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Lighting', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Lighting', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    lighting = Lighting('Open Office Zone Lighting', 10, schedule)
    lighting.user_data = userdatadict

    light_dict = lighting.to_dict()
    new_lighting = Lighting.from_dict(light_dict)
    assert new_lighting == lighting
    assert light_dict == new_lighting.to_dict()
    assert lighting.user_data == new_lighting.user_data

def test_lighting_average():
    """Test the Lighting.average method."""
    weekday_office = ScheduleDay('Weekday Office Lighting', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Lighting', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Lighting', [0])
    weekend_lobby = ScheduleDay('Weekend Office Lighting', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Lighting', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Lighting', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_lights = Lighting('Office Lighting', 10, office_schedule, 0, 0.3, 0.3)
    lobby_lights = Lighting('Lobby Lighting', 6, lobby_schedule, 0.1, 0.4, 0.2)

    office_avg = Lighting.average('Office Average Lighting', [office_lights, lobby_lights])

    assert office_avg.watts_per_area == pytest.approx(8, rel=1e-3)
    assert office_avg.return_air_fraction == pytest.approx(0.05, rel=1e-3)
    assert office_avg.radiant_fraction == pytest.approx(0.35, rel=1e-3)
    assert office_avg.visible_fraction == pytest.approx(0.25, rel=1e-3)

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals
