# coding=utf-8
from honeybee_energy.load.equipment import ElectricEquipment, GasEquipment
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.rule import ScheduleRule
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time, Date

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_equipment_init(userdatadict):
    """Test the initialization of ElectricEquipment and basic properties."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Equip', simple_office,
                               None, schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 8, schedule)
    equipment.user_data = userdatadict
    str(equipment)  # test the string representation

    assert equipment.identifier == 'Open Office Zone Equip'
    assert equipment.watts_per_area == 8
    assert equipment.schedule.identifier == 'Office Equip'
    assert equipment.schedule.schedule_type_limit == schedule_types.fractional
    assert equipment.schedule == schedule
    assert equipment.radiant_fraction == 0
    assert equipment.latent_fraction == 0
    assert equipment.lost_fraction == 0
    assert equipment.convected_fraction == 1
    assert equipment.user_data == userdatadict


def test_gas_equipment_init(userdatadict):
    """Test the initialization of GasEquipment and basic properties."""
    simple_office = ScheduleDay('Simple Weekday', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Kitchen Equip', simple_office,
                               None, schedule_types.fractional)
    equipment = GasEquipment('Kitchen Stove Equip', 8, schedule)
    equipment.user_data = userdatadict
    str(equipment)  # test the string representation

    assert equipment.identifier == 'Kitchen Stove Equip'
    assert equipment.watts_per_area == 8
    assert equipment.schedule.identifier == 'Kitchen Equip'
    assert equipment.schedule.schedule_type_limit == schedule_types.fractional
    assert equipment.schedule == schedule
    assert equipment.radiant_fraction == 0
    assert equipment.latent_fraction == 0
    assert equipment.lost_fraction == 0
    assert equipment.convected_fraction == 1
    assert equipment.user_data == userdatadict


def test_equipment_setability():
    """Test the setting of properties of ElectricEquipment."""
    simple_office = ScheduleDay('Simple Weekday Equip', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    schedule = ScheduleRuleset('Office Equip', simple_office,
                               None, schedule_types.fractional)
    constant = ScheduleRuleset.from_constant_value(
        'Constant Equip', 1, schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 8, schedule)

    equipment.identifier = 'Office Zone Equip'
    assert equipment.identifier == 'Office Zone Equip'
    equipment.watts_per_area = 6
    assert equipment.watts_per_area == 6
    equipment.schedule = constant
    assert equipment.schedule == constant
    assert equipment.schedule.values() == [1] * 8760
    equipment.radiant_fraction = 0.4
    assert equipment.radiant_fraction == 0.4
    equipment.latent_fraction = 0.2
    assert equipment.latent_fraction == 0.2
    equipment.lost_fraction = 0.1
    assert equipment.lost_fraction == 0.1


def test_equipment_equality(userdatadict):
    """Test the equality of ElectricEquipment objects."""
    weekday_office = ScheduleDay('Weekday Office Equip', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Equip', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Equip', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 10, schedule)
    equipment.user_data = userdatadict
    equipment_dup = equipment.duplicate()
    equipment_alt = ElectricEquipment(
        'Open Office Zone Equip', 10,
        ScheduleRuleset.from_constant_value('Constant', 1, schedule_types.fractional))

    assert equipment is equipment
    assert equipment is not equipment_dup
    assert equipment == equipment_dup
    equipment_dup.watts_per_area = 6
    assert equipment != equipment_dup
    assert equipment != equipment_alt


def test_equipment_lockability(userdatadict):
    """Test the lockability of ElectricEquipment objects."""
    weekday_office = ScheduleDay('Weekday Office Equip', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Equip', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Equip', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 10, schedule)
    equipment.user_data = userdatadict

    equipment.watts_per_area = 6
    equipment.lock()
    with pytest.raises(AttributeError):
        equipment.watts_per_area = 8
    with pytest.raises(AttributeError):
        equipment.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))
    equipment.unlock()
    equipment.watts_per_area = 8
    with pytest.raises(AttributeError):
        equipment.schedule.default_day_schedule.remove_value_by_time(Time(17, 0))


def test_equipment_init_from_idf():
    """Test the initialization of ElectricEquipment from_idf."""
    weekday_office = ScheduleDay('Weekday Office Equip', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Equip', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Equip', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 10, schedule)
    sched_dict = {schedule.identifier: schedule}

    zone_id = 'Test Zone'
    idf_str = equipment.to_idf(zone_id)
    rebuilt_equipment, rebuilt_zone_id = ElectricEquipment.from_idf(idf_str, sched_dict)
    assert equipment == rebuilt_equipment
    assert zone_id == rebuilt_zone_id


def test_equipment_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    weekday_office = ScheduleDay('Weekday Office Equip', [0, 1, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0)])
    saturday_office = ScheduleDay('Saturday Office Equip', [0, 0.25, 0],
                                  [Time(0, 0), Time(9, 0), Time(17, 0)])
    weekend_rule = ScheduleRule(saturday_office)
    weekend_rule.apply_weekend = True
    schedule = ScheduleRuleset('Office Equip', weekday_office,
                               [weekend_rule], schedule_types.fractional)
    equipment = ElectricEquipment('Open Office Zone Equip', 10, schedule)
    equipment.user_data = userdatadict
    gas_equipment = GasEquipment('Open Office Zone Equip', 10, schedule)
    gas_equipment.user_data = userdatadict

    equip_dict = equipment.to_dict()
    gaseq_dict = gas_equipment.to_dict()
    new_equipment = ElectricEquipment.from_dict(equip_dict)
    new_gassequip = GasEquipment.from_dict(gaseq_dict)
    assert new_equipment == equipment
    assert equip_dict == new_equipment.to_dict()
    assert gaseq_dict == new_gassequip.to_dict()


def test_equipment_average():
    """Test the ElectricEquipment.average method."""
    weekday_office = ScheduleDay('Weekday Office Equip', [0, 1, 0.5, 0],
                                 [Time(0, 0), Time(9, 0), Time(17, 0), Time(19, 0)])
    weekday_lobby = ScheduleDay('Weekday Lobby Equip', [0.1, 1, 0.1],
                                [Time(0, 0), Time(8, 0), Time(20, 0)])
    weekend_office = ScheduleDay('Weekend Office Equip', [0])
    weekend_lobby = ScheduleDay('Weekend Office Equip', [0.1])
    wknd_office_rule = ScheduleRule(weekend_office, apply_saturday=True, apply_sunday=True)
    wknd_lobby_rule = ScheduleRule(weekend_lobby, apply_saturday=True, apply_sunday=True)
    office_schedule = ScheduleRuleset('Office Equip', weekday_office,
                                      [wknd_office_rule], schedule_types.fractional)
    lobby_schedule = ScheduleRuleset('Lobby Equip', weekday_lobby,
                                     [wknd_lobby_rule], schedule_types.fractional)

    office_equip = ElectricEquipment('Office Equip', 10, office_schedule, 0.3, 0.3)
    lobby_equip = ElectricEquipment('Lobby Equip', 6, lobby_schedule, 0.4, 0.2, 0.1)

    office_avg = ElectricEquipment.average('Office Average Equip', [office_equip, lobby_equip])

    assert office_avg.watts_per_area == pytest.approx(8, rel=1e-3)
    assert office_avg.radiant_fraction == pytest.approx(0.35, rel=1e-3)
    assert office_avg.latent_fraction == pytest.approx(0.25, rel=1e-3)
    assert office_avg.lost_fraction == pytest.approx(0.05, rel=1e-3)

    week_vals = office_avg.schedule.values(end_date=Date(1, 7))
    avg_vals = [0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.05, 0.5,
                1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 0.75, 0.75,
                0.5, 0.05, 0.05, 0.05, 0.05]
    assert week_vals[:24] == [0.05] * 24
    assert week_vals[24:48] == avg_vals
