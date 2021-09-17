# coding=utf-8
from honeybee_energy.programtype import ProgramType
from honeybee_energy.load.people import People
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.load.infiltration import Infiltration
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.load.setpoint import Setpoint

from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset

import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Time

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_program_type_init(userdatadict):
    """Test the initialization of ProgramType and basic properties."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.00015, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program', people, lighting, equipment,
                                 None, None, infiltration, ventilation, setpoint)
    office_program.user_data = userdatadict

    str(office_program)  # test the string representation

    assert office_program.identifier == 'Open Office Program'
    assert isinstance(office_program.people, People)
    assert office_program.people == people
    assert isinstance(office_program.lighting, Lighting)
    assert office_program.lighting == lighting
    assert isinstance(office_program.electric_equipment, ElectricEquipment)
    assert office_program.electric_equipment == equipment
    assert office_program.gas_equipment is None
    assert isinstance(office_program.infiltration, Infiltration)
    assert office_program.infiltration == infiltration
    assert isinstance(office_program.ventilation, Ventilation)
    assert office_program.ventilation == ventilation
    assert isinstance(office_program.setpoint, Setpoint)
    assert office_program.setpoint == setpoint
    assert len(office_program.schedules) == 7
    assert len(office_program.schedules_unique) == 6
    assert office_program.user_data == userdatadict


def test_program_type_setability(userdatadict):
    """Test the setting of properties of ProgramType."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.00015, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program')

    assert office_program.identifier == 'Open Office Program'
    office_program.identifier = 'Office Program'
    assert office_program.identifier == 'Office Program'
    assert office_program.people is None
    office_program.people = people
    assert office_program.people == people
    assert office_program.lighting is None
    office_program.lighting = lighting
    assert office_program.lighting == lighting
    assert office_program.electric_equipment is None
    office_program.electric_equipment = equipment
    assert office_program.electric_equipment == equipment
    assert office_program.infiltration is None
    office_program.infiltration = infiltration
    assert office_program.infiltration == infiltration
    assert office_program.ventilation is None
    office_program.ventilation = ventilation
    assert office_program.ventilation == ventilation
    assert office_program.setpoint is None
    office_program.setpoint = setpoint
    assert office_program.setpoint == setpoint
    assert office_program.user_data is None
    office_program.user_data = userdatadict
    assert office_program.user_data == userdatadict

    with pytest.raises(AssertionError):
        office_program.people = lighting
    with pytest.raises(AssertionError):
        office_program.lighting = equipment
    with pytest.raises(AssertionError):
        office_program.electric_equipment = people
    with pytest.raises(AssertionError):
        office_program.infiltration = people
    with pytest.raises(AssertionError):
        office_program.ventilation = setpoint
    with pytest.raises(AssertionError):
        office_program.setpoint = ventilation


def test_program_type_equality(userdatadict):
    """Test the equality of ProgramType objects."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    led_lighting = Lighting('LED Office Lighting', 5, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.00015, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program', people, lighting, equipment,
                                 None, None, infiltration, ventilation, setpoint)
    office_program.user_data = userdatadict
    office_program_dup = office_program.duplicate()
    office_program_alt = ProgramType(
        'Open Office Program', people, led_lighting, equipment,
        None, None, infiltration, ventilation, setpoint)

    assert office_program is office_program
    assert office_program is not office_program_dup
    assert office_program == office_program_dup
    office_program_dup.people.people_per_area = 0.1
    assert office_program != office_program_dup
    assert office_program != office_program_alt


def test_program_type_lockability(userdatadict):
    """Test the lockability of ProgramType objects."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    light_schedule = ScheduleRuleset('Office Lighting-Equip Schedule', simple_office,
                                     None, schedule_types.fractional)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    led_lighting = Lighting('LED Office Lighting', 5, light_schedule)
    office_program = ProgramType('Open Office Program', lighting=lighting)
    office_program.user_data = userdatadict

    office_program.lighting.watts_per_area = 6
    office_program.lock()
    with pytest.raises(AttributeError):
        office_program.lighting.watts_per_area = 8
    with pytest.raises(AttributeError):
        office_program.lighting = led_lighting
    office_program.unlock()
    office_program.lighting.watts_per_area = 8
    office_program.lighting = led_lighting


def test_program_type_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.00015, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program', people, lighting, equipment,
                                 None, None, infiltration, ventilation, setpoint)
    office_program.user_data = userdatadict

    prog_dict = office_program.to_dict()
    new_office_program = ProgramType.from_dict(prog_dict)
    assert new_office_program == office_program
    assert prog_dict == new_office_program.to_dict()


def test_program_type_diversify():
    """Test the diversify methods."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.00015, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.0025, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program', people, lighting, equipment,
                                 None, None, infiltration, ventilation, setpoint)

    div_programs = office_program.diversify(10)
    assert len(div_programs) == 10
    for prog in div_programs:
        assert isinstance(prog, ProgramType)
        assert prog.people.people_per_area != people.people_per_area
        assert prog.lighting.watts_per_area != lighting.watts_per_area
        assert prog.electric_equipment.watts_per_area != equipment.watts_per_area
        assert prog.infiltration.flow_per_exterior_area != \
            infiltration.flow_per_exterior_area

    div_programs = office_program.diversify(10, schedule_offset=0)
    for prog in div_programs:
        assert prog.people.occupancy_schedule == people.occupancy_schedule


def test_program_type_average():
    """Test the ProgramType.average method."""
    simple_office = ScheduleDay('Simple Weekday Occupancy', [0, 1, 0],
                                [Time(0, 0), Time(9, 0), Time(17, 0)])
    occ_schedule = ScheduleRuleset('Office Occupancy Schedule', simple_office,
                                   None, schedule_types.fractional)
    light_schedule = occ_schedule.duplicate()
    light_schedule.identifier = 'Office Lighting-Equip Schedule'
    light_schedule.default_day_schedule.values = [0.25, 1, 0.25]
    equip_schedule = light_schedule.duplicate()
    inf_schedule = ScheduleRuleset.from_constant_value(
        'Infiltration Schedule', 1, schedule_types.fractional)
    heat_setpt = ScheduleRuleset.from_constant_value(
        'Office Heating Schedule', 21, schedule_types.temperature)
    cool_setpt = ScheduleRuleset.from_constant_value(
        'Office Cooling Schedule', 24, schedule_types.temperature)

    people = People('Open Office People', 0.05, occ_schedule)
    lighting = Lighting('Open Office Lighting', 10, light_schedule)
    equipment = ElectricEquipment('Open Office Equipment', 10, equip_schedule)
    infiltration = Infiltration('Office Infiltration', 0.0002, inf_schedule)
    ventilation = Ventilation('Office Ventilation', 0.005, 0.0003)
    setpoint = Setpoint('Office Setpoints', heat_setpt, cool_setpt)
    office_program = ProgramType('Open Office Program', people, lighting, equipment,
                                 None, None, infiltration, ventilation, setpoint)
    plenum_program = ProgramType('Plenum Program')

    office_avg = ProgramType.average(
        'Office Average Program', [office_program, plenum_program])

    assert office_avg.people.people_per_area == pytest.approx(0.025, rel=1e-3)
    assert office_avg.people.occupancy_schedule.default_day_schedule.values == \
        office_program.people.occupancy_schedule.default_day_schedule.values
    assert office_avg.people.latent_fraction == \
        office_program.people.latent_fraction
    assert office_avg.people.radiant_fraction == \
        office_program.people.radiant_fraction

    assert office_avg.lighting.watts_per_area == pytest.approx(5, rel=1e-3)
    assert office_avg.lighting.schedule.default_day_schedule.values == \
        office_program.lighting.schedule.default_day_schedule.values
    assert office_avg.lighting.return_air_fraction == \
        office_program.lighting.return_air_fraction
    assert office_avg.lighting.radiant_fraction == \
        office_program.lighting.radiant_fraction
    assert office_avg.lighting.visible_fraction == \
        office_program.lighting.visible_fraction

    assert office_avg.electric_equipment.watts_per_area == pytest.approx(5, rel=1e-3)
    assert office_avg.electric_equipment.schedule.default_day_schedule.values == \
        office_program.electric_equipment.schedule.default_day_schedule.values
    assert office_avg.electric_equipment.radiant_fraction == \
        office_program.electric_equipment.radiant_fraction
    assert office_avg.electric_equipment.latent_fraction == \
        office_program.electric_equipment.latent_fraction
    assert office_avg.electric_equipment.lost_fraction == \
        office_program.electric_equipment.lost_fraction

    assert office_avg.gas_equipment is None

    assert office_avg.infiltration.flow_per_exterior_area == \
        pytest.approx(0.0001, rel=1e-3)
    assert office_avg.infiltration.schedule.default_day_schedule.values == \
        office_program.infiltration.schedule.default_day_schedule.values
    assert office_avg.infiltration.constant_coefficient == \
        office_program.infiltration.constant_coefficient
    assert office_avg.infiltration.temperature_coefficient == \
        office_program.infiltration.temperature_coefficient
    assert office_avg.infiltration.velocity_coefficient == \
        office_program.infiltration.velocity_coefficient

    assert office_avg.ventilation.flow_per_person == pytest.approx(0.0025, rel=1e-3)
    assert office_avg.ventilation.flow_per_area == pytest.approx(0.00015, rel=1e-3)
    assert office_avg.ventilation.flow_per_zone == pytest.approx(0, rel=1e-3)
    assert office_avg.ventilation.air_changes_per_hour == pytest.approx(0, rel=1e-3)
    assert office_avg.ventilation.schedule is None

    assert office_avg.setpoint.heating_setpoint == pytest.approx(21, rel=1e-3)
    assert office_avg.setpoint.cooling_setpoint == pytest.approx(24, rel=1e-3)
