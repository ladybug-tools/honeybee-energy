# coding=utf-8
from honeybee_energy.load.hotwater import ServiceHotWater
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee.room import Room
from ladybug.dt import Time, Date

import pytest
import sys
from .fixtures.userdata_fixtures import userdatadict

def test_service_hot_water_init(userdatadict): 
    """Test the initialization of ServiceHotWater and basic properties."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Water Use', simple_office,
                               None, schedule_types.fractional)
    shw = ServiceHotWater('Office Hot Water', 0.1, schedule)
    shw.user_data = userdatadict
    str(shw)  # test the string representation

    assert shw.identifier == 'Office Hot Water'
    assert shw.flow_per_area == 0.1
    assert shw.schedule.identifier == 'Office Water Use'
    assert shw.schedule.schedule_type_limit == schedule_types.fractional
    assert shw.schedule == schedule
    assert shw.target_temperature == 60
    assert shw.sensible_fraction == 0.2
    assert shw.latent_fraction == 0.05
    assert shw.lost_fraction == 0.75
    assert shw.user_data == userdatadict


def test_init_from_watts_per_area(userdatadict): 
    """Test the initialization of ServiceHotWater from_watts_per_area."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Water Use', simple_office,
                               None, schedule_types.fractional)
    shw = ServiceHotWater.from_watts_per_area('Office Hot Water', 10, schedule)
    shw.user_data = userdatadict

    assert shw.identifier == 'Office Hot Water'
    assert 0.1 < shw.flow_per_area < 0.2
    assert shw.schedule.identifier == 'Office Water Use'
    assert shw.schedule.schedule_type_limit == schedule_types.fractional
    assert shw.schedule == schedule
    assert shw.target_temperature == 60
    assert shw.sensible_fraction == 0.2
    assert shw.latent_fraction == 0.05
    assert shw.lost_fraction == 0.75
    assert shw.user_data == userdatadict


def test_service_hot_water_setability(userdatadict):
    """Test the setting of properties of ServiceHotWater."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Water Use', simple_office,
                               None, schedule_types.fractional)
    constant = ScheduleRuleset.from_constant_value(
        'Constant Water Use', 1, schedule_types.fractional)
    shw = ServiceHotWater('Office Hot Water', 0.1, schedule)
    shw.user_data = userdatadict

    shw.identifier = 'Office Zone Hot Water'
    assert shw.identifier == 'Office Zone Hot Water'
    shw.flow_per_area = 0.05
    assert shw.flow_per_area == 0.05
    shw.schedule = constant
    assert shw.schedule == constant
    assert shw.schedule.values() == [1] * 8760
    shw.target_temperature = 25
    assert shw.target_temperature == 25
    shw.sensible_fraction = 0.25
    assert shw.sensible_fraction == 0.25
    shw.latent_fraction = 0.1
    assert shw.latent_fraction == 0.1
    assert shw.user_data == userdatadict


def test_service_hot_water_equality(userdatadict):
    """Test the equality of ServiceHotWater objects."""
    weekday_office = ScheduleDay('Weekday Office Water Use', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Water Use', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Water Use', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    shw = ServiceHotWater('Open Office Zone Hot Water', 0.1, schedule)
    shw.user_data = userdatadict
    shw_dup = shw.duplicate()
    shw_alt = ServiceHotWater(
        'Open Office Zone Hot Water', 0.1,
        ScheduleRuleset.from_constant_value('Constant', 1, schedule_types.fractional))

    assert shw is shw
    assert shw is not shw_dup
    assert shw == shw_dup
    shw_dup.flow_per_area = 0.2
    assert shw != shw_dup
    assert shw != shw_alt


def test_service_hot_water_lockability(userdatadict):
    """Test the lockability of ServiceHotWater objects."""
    weekday_office = ScheduleDay('Weekday Office Water Use', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Water Use', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Water Use', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    shw = ServiceHotWater('Open Office Zone Hot Water', 0.1, schedule)

    shw.flow_per_area = 0.2
    shw.user_data = userdatadict
    shw.lock()
    with pytest.raises(AttributeError):
        shw.flow_per_area = 0.25
    with pytest.raises(AttributeError):
        shw.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    shw.unlock()
    shw.flow_per_area = 0.25
    with pytest.raises(AttributeError):
        shw.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_service_hot_water_init_from_idf():
    """Test the initialization of Lighting from_idf."""
    weekday_office = ScheduleDay('Weekday Office Water Use', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Water Use', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Water Use', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    shw = ServiceHotWater('Open Office Zone Hot Water', 0.1, schedule)
    sched_dict = {schedule.identifier: schedule}

    room = Room.from_box('Test_Zone', 10, 10, 3)
    idf_str, sch_strs = shw.to_idf(room)
    for sch in sch_strs:
        sch_obj = ScheduleRuleset.from_idf_constant(sch)
        sched_dict[sch_obj.identifier] = sch_obj

    rebuilt_shw, room_id, flow = ServiceHotWater.from_idf(
        idf_str, room.floor_area, sched_dict)
    if (sys.version_info >= (3, 0)):
        assert shw == rebuilt_shw
        assert room_id == room.identifier
        assert flow == shw.flow_per_area * room.floor_area


def test_service_hot_water_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    weekday_office = ScheduleDay('Weekday Office Water Use', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Water Use', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Water Use', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    shw = ServiceHotWater('Open Office Zone Hot Water', 0.1, schedule)
    shw.user_data = userdatadict
    shw_dict = shw.to_dict()
    new_shw = ServiceHotWater.from_dict(shw_dict)
    assert new_shw == shw
    assert shw_dict == new_shw.to_dict()


def test_service_hot_water_average():
    """Test the ServiceHotWater.average method."""
    weekday_office = ScheduleDay('Weekday Office Water Use', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Water Use', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Water Use', [0])
    weekend_lobby = ScheduleDay('Weekend Office Water Use', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Water Use', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Water Use', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_shws = ServiceHotWater(
        'Office Hot Water', 0.05, office_schedule, 60, 0.3, 0.05)
    br_shws = ServiceHotWater(
        'Bathroom Hot Water', 0.1, lobby_schedule, 50, 0.4, 0.1)

    office_avg = ServiceHotWater.average(
        'Office Average Hot Water', [office_shws, br_shws])

    assert office_avg.flow_per_area == pytest.approx(0.075, rel=1e-3)
    assert office_avg.target_temperature == pytest.approx(55.0, rel=1e-3)
    assert office_avg.sensible_fraction == pytest.approx(0.35, rel=1e-3)
    assert office_avg.latent_fraction == pytest.approx(0.075, rel=1e-3)

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals
