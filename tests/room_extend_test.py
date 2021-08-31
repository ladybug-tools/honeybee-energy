"""Tests the features that honeybee_energy adds to honeybee_core Room."""
from honeybee.room import Room
from honeybee.door import Door

from honeybee_energy.properties.room import RoomEnergyProperties
from honeybee_energy.programtype import ProgramType
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.hvac.idealair import IdealAirSystem
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.schedule.day import ScheduleDay
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.lib.materials import concrete_hw
import honeybee_energy.lib.scheduletypelimits as schedule_types

from honeybee_energy.lib.programtypes import office_program

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

from ladybug.dt import Time

import pytest


def test_energy_properties():
    """Test the existence of the Room energy properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3, 90, Point3D(0, 0, 3))
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    assert hasattr(room.properties, 'energy')
    assert isinstance(room.properties.energy, RoomEnergyProperties)
    assert isinstance(room.properties.energy.construction_set, ConstructionSet)
    assert isinstance(room.properties.energy.program_type, ProgramType)
    assert isinstance(room.properties.energy.hvac, IdealAirSystem)
    assert room.properties.energy.program_type == office_program
    assert room.properties.energy.is_conditioned
    assert room.properties.energy.people == office_program.people
    assert room.properties.energy.lighting == office_program.lighting
    assert room.properties.energy.electric_equipment == office_program.electric_equipment
    assert room.properties.energy.gas_equipment == office_program.gas_equipment
    assert room.properties.energy.infiltration == office_program.infiltration
    assert room.properties.energy.ventilation == office_program.ventilation
    assert room.properties.energy.setpoint == office_program.setpoint


def test_default_properties():
    """Test the auto-assigning of Room properties."""
    room = Room.from_box('ShoeBox', 5, 10, 3, 90, Point3D(0, 0, 3))

    assert room.properties.energy.construction_set.identifier == \
        'Default Generic Construction Set'
    assert room.properties.energy.program_type.identifier == 'Plenum'
    assert room.properties.energy.hvac is None
    assert not room.properties.energy.is_conditioned
    assert room.properties.energy.people is None
    assert room.properties.energy.lighting is None
    assert room.properties.energy.electric_equipment is None
    assert room.properties.energy.gas_equipment is None
    assert room.properties.energy.infiltration is None
    assert room.properties.energy.ventilation is None
    assert room.properties.energy.setpoint is None


def test_set_construction_set():
    """Test the setting of a ConstructionSet on a Room."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    door_verts = [[1, 0, 0.1], [2, 0, 0.1], [2, 0, 3], [1, 0, 3]]
    room[3].add_door(Door.from_vertices('test_door', door_verts))
    room[1].apertures_by_ratio(0.4, 0.01)
    room[1].apertures[0].overhang(0.5, indoor=False)
    room[1].apertures[0].overhang(0.5, indoor=True)
    room[1].apertures[0].move_shades(Vector3D(0, 0, -0.5))

    mass_set = ConstructionSet('Thermal Mass Construction Set')
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    concrete10 = EnergyMaterial('10cm Concrete', 0.1, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    stone_door = EnergyMaterial('Stone Door', 0.05, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction('Thick Concrete Construction', [concrete20])
    thin_constr = OpaqueConstruction('Thin Concrete Construction', [concrete10])
    door_constr = OpaqueConstruction('Stone Door', [stone_door])
    shade_constr = ShadeConstruction('Light Shelf', 0.5, 0.5)
    mass_set.wall_set.exterior_construction = thick_constr
    mass_set.roof_ceiling_set.exterior_construction = thin_constr
    mass_set.door_set.exterior_construction = door_constr
    mass_set.shade_construction = shade_constr

    room.properties.energy.construction_set = mass_set
    assert room.properties.energy.construction_set == mass_set
    assert room[1].properties.energy.construction == thick_constr
    assert room[5].properties.energy.construction == thin_constr
    assert room[3].doors[0].properties.energy.construction == door_constr
    assert room[1].apertures[0].shades[0].properties.energy.construction == shade_constr

    with pytest.raises(AttributeError):
        room[1].properties.energy.construction.thickness = 0.3
    with pytest.raises(AttributeError):
        room[5].properties.energy.construction.thickness = 0.3
    with pytest.raises(AttributeError):
        room[3].doors[0].properties.energy.construction.thickness = 0.3


def test_set_program_type():
    """Test the setting of a ProgramType on a Room."""
    lab_equip_day = ScheduleDay('Daily Lab Equipment', [0.25, 0.5, 0.25],
                                [Time(0, 0), Time(9, 0), Time(20, 0)])
    lab_equipment = ScheduleRuleset('Lab Equipment', lab_equip_day,
                                    None, schedule_types.fractional)
    lab_vent_day = ScheduleDay('Daily Lab Ventilation', [0.5, 1, 0.5],
                               [Time(0, 0), Time(9, 0), Time(20, 0)])
    lab_ventilation = ScheduleRuleset('Lab Ventilation', lab_vent_day,
                                      None, schedule_types.fractional)
    lab_program = office_program.duplicate()
    lab_program.identifier = 'Bio Laboratory'
    lab_program.electric_equipment.watts_per_area = 50
    lab_program.electric_equipment.schedule = lab_equipment
    lab_program.ventilation.flow_per_person = 0
    lab_program.ventilation.flow_per_area = 0
    lab_program.ventilation.air_changes_per_hour = 6
    lab_program.ventilation.schedule = lab_ventilation

    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = lab_program

    assert room.properties.energy.program_type.identifier == 'Bio Laboratory'
    assert room.properties.energy.program_type == lab_program
    assert room.properties.energy.electric_equipment.watts_per_area == 50
    assert room.properties.energy.electric_equipment.schedule == lab_equipment
    assert room.properties.energy.ventilation.flow_per_person == 0
    assert room.properties.energy.ventilation.flow_per_area == 0
    assert room.properties.energy.ventilation.air_changes_per_hour == 6
    assert room.properties.energy.ventilation.schedule == lab_ventilation


def test_set_loads():
    """Test the setting of a load objects on a Room."""
    lab_equip_day = ScheduleDay('Daily Lab Equipment', [0.25, 0.5, 0.25],
                                [Time(0, 0), Time(9, 0), Time(20, 0)])
    lab_equipment = ScheduleRuleset('Lab Equipment', lab_equip_day,
                                    None, schedule_types.fractional)
    lab_vent_day = ScheduleDay('Daily Lab Ventilation', [0.5, 1, 0.5],
                               [Time(0, 0), Time(9, 0), Time(20, 0)])
    lab_ventilation = ScheduleRuleset('Lab Ventilation', lab_vent_day,
                                      None, schedule_types.fractional)

    room = Room.from_box('BioLaboratoryZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    lab_equip = ElectricEquipment('Lab Equipment', 50, lab_equipment)
    lav_vent = Ventilation('Lab Ventilation', 0, 0, 0, 6, lab_ventilation)
    lab_setpt = room.properties.energy.setpoint.duplicate()
    lab_setpt.heating_setpoint = 22
    lab_setpt.cooling_setpoint = 24
    room.properties.energy.electric_equipment = lab_equip
    room.properties.energy.ventilation = lav_vent
    room.properties.energy.setpoint = lab_setpt

    assert room.properties.energy.program_type == office_program
    assert room.properties.energy.electric_equipment.watts_per_area == 50
    assert room.properties.energy.electric_equipment.schedule == lab_equipment
    assert room.properties.energy.ventilation.flow_per_person == 0
    assert room.properties.energy.ventilation.flow_per_area == 0
    assert room.properties.energy.ventilation.air_changes_per_hour == 6
    assert room.properties.energy.ventilation.schedule == lab_ventilation
    assert room.properties.energy.setpoint.heating_setpoint == 22
    assert room.properties.energy.setpoint.heating_setback == 22
    assert room.properties.energy.setpoint.cooling_setpoint == 24
    assert room.properties.energy.setpoint.cooling_setback == 24


def test_loads_absolute():
    """Test the methods that assign loads using an absolute number."""
    room = Room.from_box('ShoeBox', 10000, 10000, 3000)

    room.properties.energy.abolute_people(10, 0.001)
    assert room.properties.energy.people.people_per_area == 0.1
    room.properties.energy.abolute_lighting(1000, 0.001)
    assert room.properties.energy.lighting.watts_per_area == 10
    room.properties.energy.abolute_electric_equipment(1000, 0.001)
    assert room.properties.energy.electric_equipment.watts_per_area == 10
    room.properties.energy.abolute_gas_equipment(1000, 0.001)
    assert room.properties.energy.gas_equipment.watts_per_area == 10
    room.properties.energy.abolute_infiltration(1, 0.001)
    assert room.properties.energy.infiltration.flow_per_exterior_area == \
        pytest.approx(1. / 220., abs=1e-3)
    room.properties.energy.abolute_infiltration_ach(1, 0.001)
    assert room.properties.energy.infiltration.flow_per_exterior_area == \
        pytest.approx(300. / (220. * 3600.), abs=1e-3)
    room.properties.energy.abolute_ventilation(0.5)
    assert room.properties.energy.ventilation.flow_per_zone == \
        pytest.approx(0.5, abs=1e-3)


def test_make_plenum():
    """Test the make_plenum method."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    assert room.properties.energy.people is not None
    assert room.properties.energy.infiltration is not None
    assert room.properties.energy.is_conditioned

    room.properties.energy.make_plenum()
    assert room.properties.energy.people is None
    assert room.properties.energy.infiltration is not None
    assert not room.properties.energy.is_conditioned


def test_make_ground():
    """Test the make_ground method."""
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    assert room.properties.energy.people is not None
    assert room.properties.energy.infiltration is not None
    assert room.properties.energy.is_conditioned

    soil_constr = OpaqueConstruction('Conc_Pavement', [concrete_hw])
    room.properties.energy.make_ground(soil_constr)
    assert room.properties.energy.people is None
    assert room.properties.energy.infiltration is None
    assert not room.properties.energy.is_conditioned


def test_duplicate():
    """Test what happens to energy properties when duplicating a Room."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room_original = Room.from_box('ShoeBox', 5, 10, 3)
    room_original.properties.energy.program_type = office_program
    room_original.properties.energy.add_default_ideal_air()

    room_dup_1 = room_original.duplicate()

    assert room_original.properties.energy.program_type == \
        room_dup_1.properties.energy.program_type
    assert room_original.properties.energy.hvac == \
        room_dup_1.properties.energy.hvac

    assert room_original.properties.energy.host is room_original
    assert room_dup_1.properties.energy.host is room_dup_1
    assert room_original.properties.energy.host is not \
        room_dup_1.properties.energy.host

    assert room_original.properties.energy.construction_set == \
        room_dup_1.properties.energy.construction_set
    room_dup_1.properties.energy.construction_set = mass_set
    assert room_original.properties.energy.construction_set != \
        room_dup_1.properties.energy.construction_set

    room_dup_1.add_prefix('Opt1')
    assert room_dup_1.identifier.startswith('Opt1')

    room_dup_2 = room_dup_1.duplicate()

    assert room_dup_1.properties.energy.construction_set == \
        room_dup_2.properties.energy.construction_set
    room_dup_2.properties.energy.construction_set = None
    assert room_dup_1.properties.energy.construction_set != \
        room_dup_2.properties.energy.construction_set


def test_to_dict():
    """Test the Room to_dict method with energy properties."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room = Room.from_box('ShoeBox', 5, 10, 3)

    rd = room.to_dict()
    assert 'properties' in rd
    assert rd['properties']['type'] == 'RoomProperties'
    assert 'energy' in rd['properties']
    assert rd['properties']['energy']['type'] == 'RoomEnergyProperties'
    assert 'program_type' not in rd['properties']['energy'] or \
        rd['properties']['energy']['program_type'] is None
    assert 'construction_set' not in rd['properties']['energy'] or \
        rd['properties']['energy']['construction_set'] is None
    assert 'hvac' not in rd['properties']['energy'] or \
        rd['properties']['energy']['hvac'] is None
    assert 'people' not in rd['properties']['energy'] or \
        rd['properties']['energy']['people'] is None
    assert 'lighting' not in rd['properties']['energy'] or \
        rd['properties']['energy']['lighting'] is None
    assert 'electric_equipment' not in rd['properties']['energy'] or \
        rd['properties']['energy']['electric_equipment'] is None
    assert 'gas_equipment' not in rd['properties']['energy'] or \
        rd['properties']['energy']['gas_equipment'] is None
    assert 'infiltration' not in rd['properties']['energy'] or \
        rd['properties']['energy']['infiltration'] is None
    assert 'ventilation' not in rd['properties']['energy'] or \
        rd['properties']['energy']['ventilation'] is None
    assert 'setpoint' not in rd['properties']['energy'] or \
        rd['properties']['energy']['setpoint'] is None

    room.properties.energy.construction_set = mass_set
    rd = room.to_dict()
    assert rd['properties']['energy']['construction_set'] is not None


def test_from_dict():
    """Test the Room from_dict method with energy properties."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room = Room.from_box('ShoeBox', 5, 10, 3)
    room.properties.energy.construction_set = mass_set

    rd = room.to_dict()
    new_room = Room.from_dict(rd)
    assert new_room.properties.energy.construction_set.identifier == \
        'Thermal Mass Construction Set'
    assert new_room.to_dict() == rd


def test_writer_to_idf():
    """Test the Room to_idf method."""
    room = Room.from_box('ClosedOffice', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    assert hasattr(room.to, 'idf')
    idf_string = room.to.idf(room)
    assert 'ClosedOffice,' in idf_string
    assert 'Zone,' in idf_string
    assert 'People' in idf_string
    assert 'Lights' in idf_string
    assert 'ElectricEquipment' in idf_string
    assert 'GasEquipment' not in idf_string
    assert 'ZoneInfiltration:DesignFlowRate' in idf_string
    assert 'DesignSpecification:OutdoorAir' in idf_string
    assert 'HVACTemplate:Thermostat' in idf_string
    assert 'HVACTemplate:Zone:IdealLoadsAirSystem' not in idf_string


def test_envelope_components_by_type():

    zone_pts = Face3D(
        [Point3D(0, 0, 0), Point3D(20, 0, 0), Point3D(20, 10, 0), Point3D(0, 10, 0)])
    room = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(zone_pts, 3))

    door_pts = [Point3D(2, 10, 0.01), Point3D(4, 10, 0.01),
                Point3D(4, 10, 2.50), Point3D(2, 10, 2.50)]
    door = Door('FrontDoor', Face3D(door_pts))
    room[3].add_door(door)  # Door to north face
    room[1].apertures_by_ratio(0.3)  # Window on south face

    ext_faces, int_faces = room.properties.energy.envelope_components_by_type()

    walls, roofs, floors, apertures, doors = ext_faces

    assert len(walls) == 4
    assert len(roofs) == 1
    assert len(floors) == 0
    assert len(apertures) == 1
    assert len(doors) == 1

    for types in int_faces:
        assert len(types) == 0


def test_solve_norm_area_flow_coefficient():
    """Test calculation of leakage parameters from infiltration for face area."""

    refn = 0.65
    rep = RoomEnergyProperties
    d = 1.204

    # Test tight envelope @ 0.0001 m3/s per m2 @ 4 Pa
    Cq = rep.solve_norm_area_flow_coefficient(0.0001, refn, d)
    assert Cq == pytest.approx(0.0000488976, abs=1e-9)

    # Test average envelope
    Cq = rep.solve_norm_area_flow_coefficient(0.0003, refn, d)
    assert Cq == pytest.approx(0.000146693, abs=1e-9)

    # Test leaky envelope
    Cq = rep.solve_norm_area_flow_coefficient(0.0006, refn, d)
    assert Cq == pytest.approx(0.000293386, abs=1e-9)


def test_solve_norm_perimeter_flow_coefficient():
    """Test calculation of leakage parameters from infiltration for opening edges."""

    L = 6.0  # 2 x 1 meter opening
    A = 2.0  # m2
    refn = 0.65
    rep = RoomEnergyProperties
    d = 1.204

    # Test tight envelope
    Cqa = rep.solve_norm_area_flow_coefficient(0.0001, refn, d)
    Cql = rep.solve_norm_perimeter_flow_coefficient(Cqa, A, L)
    assert Cql == pytest.approx(0.0000162992, abs=1e-9)

    # Test average envelope
    Cqa = rep.solve_norm_area_flow_coefficient(0.0003, refn, d)
    Cql = rep.solve_norm_perimeter_flow_coefficient(Cqa, A, L)
    assert Cql == pytest.approx(0.0000488976, abs=1e-9)

    # Test leaky envelope
    Cqa = rep.solve_norm_area_flow_coefficient(0.0006, refn, d)
    Cql = rep.solve_norm_perimeter_flow_coefficient(Cqa, A, L)
    assert Cql == pytest.approx(0.0000977952, abs=1e-9)
