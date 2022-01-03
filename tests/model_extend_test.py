"""Tests the features that honeybee_energy adds to honeybee_core Model."""
from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.boundarycondition import boundary_conditions, Ground, Outdoors
from honeybee.facetype import face_types

from honeybee_energy.properties.model import ModelEnergyProperties
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.construction.air import AirBoundaryConstruction
from honeybee_energy.internalmass import InternalMass
from honeybee_energy.load.process import Process
from honeybee_energy.material._base import _EnergyMaterialBase
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.load.people import People
from honeybee_energy.ventcool.simulation import VentilationSimulationControl
from honeybee_energy.hvac.allair.vav import VAV

from honeybee_energy.lib.programtypes import office_program, plenum_program
import honeybee_energy.lib.scheduletypelimits as schedule_types
from honeybee_energy.lib.materials import clear_glass, air_gap, roof_membrane, \
    wood, insulation
from honeybee_energy.lib.constructions import generic_exterior_wall, \
    generic_interior_wall, generic_interior_floor, generic_interior_ceiling, \
    generic_double_pane, generic_single_pane

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

import random
import pytest


def test_energy_properties():
    """Test the existence of the Model energy properties."""
    room = Room.from_box('Tiny_House_Zone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))
    fritted_glass_trans = ScheduleRuleset.from_constant_value(
        'Fritted Glass', 0.5, schedule_types.fractional)
    south_face.apertures[0].outdoor_shades[0].properties.energy.transmittance_schedule = \
        fritted_glass_trans
    model = Model('Tiny_House', [room])

    assert hasattr(model.properties, 'energy')
    assert isinstance(model.properties.energy, ModelEnergyProperties)
    assert isinstance(model.properties.host, Model)
    assert len(model.properties.energy.materials) == 0
    for mat in model.properties.energy.materials:
        assert isinstance(mat, _EnergyMaterialBase)
    assert len(model.properties.energy.constructions) == 0
    for cnst in model.properties.energy.constructions:
        assert isinstance(cnst, (WindowConstruction, OpaqueConstruction,
                                 ShadeConstruction, AirBoundaryConstruction))
    assert len(model.properties.energy.face_constructions) == 0
    assert len(model.properties.energy.construction_sets) == 0
    assert len(model.properties.energy.schedule_type_limits) == 3
    assert len(model.properties.energy.schedules) == 8
    assert len(model.properties.energy.shade_schedules) == 1
    assert len(model.properties.energy.room_schedules) == 0
    assert len(model.properties.energy.program_types) == 1


def test_window_construction_by_orientation():
    """Test the window_construction_by_orientation method."""
    room = Room.from_box('Tiny_House_Zone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    room.wall_apertures_by_ratio(0.4)
    model = Model('Tiny_House', [room])

    assert room[1].apertures[0].properties.energy.construction == generic_double_pane
    assert room[3].apertures[0].properties.energy.construction == generic_double_pane
    model.properties.energy.window_construction_by_orientation(generic_single_pane, 0, 45)
    assert room[1].apertures[0].properties.energy.construction == generic_single_pane
    assert room[3].apertures[0].properties.energy.construction == generic_double_pane
    model.properties.energy.window_construction_by_orientation(generic_single_pane, 180, 45)
    assert room[1].apertures[0].properties.energy.construction == generic_single_pane
    assert room[3].apertures[0].properties.energy.construction == generic_single_pane

    model.properties.energy.remove_child_constructions()
    assert room[1].apertures[0].properties.energy.construction == generic_double_pane
    assert room[3].apertures[0].properties.energy.construction == generic_double_pane


def test_check_duplicate_construction_set_identifiers():
    """Test the check_duplicate_construction_set_identifiers method."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    for face in first_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    for face in second_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    base_constr_set = ConstructionSet('Lower Floor Construction Set')
    first_floor.properties.energy.construction_set = base_constr_set
    second_floor.properties.energy.construction_set = base_constr_set

    pts_1 = [Point3D(0, 0, 6), Point3D(0, 10, 6), Point3D(10, 10, 6), Point3D(10, 0, 6)]
    pts_2 = [Point3D(0, 0, 6), Point3D(5, 0, 9), Point3D(5, 10, 9), Point3D(0, 10, 6)]
    pts_3 = [Point3D(10, 0, 6), Point3D(10, 10, 6), Point3D(5, 10, 9), Point3D(5, 0, 9)]
    pts_4 = [Point3D(0, 0, 6), Point3D(10, 0, 6), Point3D(5, 0, 9)]
    pts_5 = [Point3D(10, 10, 6), Point3D(0, 10, 6), Point3D(5, 10, 9)]
    face_1 = Face('AtticFace1', Face3D(pts_1))
    face_2 = Face('AtticFace2', Face3D(pts_2))
    face_3 = Face('AtticFace3', Face3D(pts_3))
    face_4 = Face('AtticFace4', Face3D(pts_4))
    face_5 = Face('AtticFace5', Face3D(pts_5))
    attic = Room('Attic', [face_1, face_2, face_3, face_4, face_5], 0.01, 1)

    constr_set = ConstructionSet('Attic Construction Set')
    polyiso = EnergyMaterial('PolyIso', 0.2, 0.03, 43, 1210, 'MediumRough')
    roof_constr = OpaqueConstruction('Attic Roof Construction',
                                     [roof_membrane, polyiso, wood])
    floor_constr = OpaqueConstruction('Attic Floor Construction',
                                      [wood, insulation, wood])
    constr_set.floor_set.interior_construction = floor_constr
    constr_set.roof_ceiling_set.exterior_construction = roof_constr
    attic.properties.energy.construction_set = constr_set

    Room.solve_adjacency([first_floor, second_floor, attic], 0.01)

    model = Model('MultiZoneSingleFamilyHouse', [first_floor, second_floor, attic])

    assert model.properties.energy.check_duplicate_construction_set_identifiers(False) == ''
    constr_set.unlock()
    constr_set.identifier = 'Lower Floor Construction Set'
    constr_set.lock()
    assert model.properties.energy.check_duplicate_construction_set_identifiers(False) != ''
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_construction_set_identifiers(True)


def test_check_duplicate_construction_identifiers():
    """Test the check_duplicate_construction_identifiers method."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Custom Construction', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    north_face = room[1]
    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('FrontAperture', Face3D(aperture_verts))
    aperture.is_operable = True
    triple_pane = WindowConstruction(
        'CustomWindowConstruction', [clear_glass, air_gap, clear_glass, air_gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    model = Model('TinyHouse', [room])

    assert model.properties.energy.check_duplicate_construction_identifiers(False) == ''
    triple_pane.unlock()
    triple_pane.identifier = 'Custom Construction'
    triple_pane.lock()
    assert model.properties.energy.check_duplicate_construction_identifiers(False) != ''
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_construction_identifiers(True)


def test_check_duplicate_material_identifiers():
    """Test the check_duplicate_material_identifiers method."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)

    stone = EnergyMaterial('Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thin_stone = EnergyMaterial('Thin Stone', 0.05, 2.31, 2322, 832, 'Rough',
                                0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Custom Construction', [stone])
    door_constr = OpaqueConstruction('Custom Door Construction', [thin_stone])
    room[0].properties.energy.construction = thermal_mass_constr

    north_face = room[1]
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('FrontDoor', Face3D(door_verts))
    door.properties.energy.construction = door_constr
    north_face.add_door(door)

    model = Model('TinyHouse', [room])

    assert model.properties.energy.check_duplicate_material_identifiers(False) == ''
    thin_stone.unlock()
    thin_stone.identifier = 'Stone'
    thin_stone.lock()
    assert model.properties.energy.check_duplicate_material_identifiers(False) != ''
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_material_identifiers(True)


def test_check_duplicate_schedule_identifiers():
    """Test the check_duplicate_schedule_identifiers method."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))
    fritted_glass_trans = ScheduleRuleset.from_constant_value(
        'Fritted Glass', 0.6, schedule_types.fractional)
    half_occ = ScheduleRuleset.from_constant_value(
        'Half Occupied', 0.5, schedule_types.fractional)
    south_face.apertures[0].outdoor_shades[0].properties.energy.transmittance_schedule = \
        fritted_glass_trans
    room.properties.energy.people = People('Office Occ', 0.05, half_occ)
    model = Model('TinyHouse', [room])

    assert model.properties.energy.check_duplicate_schedule_identifiers(False) == ''
    half_occ.unlock()
    half_occ.identifier = 'Fritted Glass'
    half_occ.lock()
    assert model.properties.energy.check_duplicate_schedule_identifiers(False) != ''
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_schedule_identifiers(True)


def test_check_duplicate_schedule_type_limit_identifiers():
    """Test the check_duplicate_schedule_type_limit_identifiers method."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))
    fritted_glass_trans = ScheduleRuleset.from_constant_value(
        'Fritted Glass', 0.6, schedule_types.fractional)
    on_off = ScheduleTypeLimit('On-off', 0, 1, 'Discrete')
    full_occ = ScheduleRuleset.from_constant_value('Occupied', 1, on_off)
    south_face.apertures[0].outdoor_shades[0].properties.energy.transmittance_schedule = \
        fritted_glass_trans
    room.properties.energy.people = People('Office Occ', 0.05, full_occ)
    model = Model('TinyHouse', [room])

    assert model.properties.energy.check_duplicate_schedule_type_limit_identifiers(False) == ''
    full_occ.unlock()
    new_sch_type = ScheduleTypeLimit('Fractional', 0, 1, 'Discrete')
    full_occ.schedule_type_limit = new_sch_type
    full_occ.lock()
    assert model.properties.energy.check_duplicate_schedule_type_limit_identifiers(False) != ''
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_schedule_type_limit_identifiers(True)


def test_to_from_dict():
    """Test the Model to_dict and from_dict method with a single zone model."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Thermal Mass Floor', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.apertures[0].move_shades(Vector3D(0, 0, -0.5))
    light_shelf_out = ShadeConstruction('OutdoorLightShelf', 0.5, 0.5)
    light_shelf_in = ShadeConstruction('IndoorLightShelf', 0.7, 0.7)
    south_face.apertures[0].shades[0].properties.energy.construction = light_shelf_out
    south_face.apertures[0].shades[1].properties.energy.construction = light_shelf_in

    north_face = room[1]
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('FrontDoor', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('FrontAperture', Face3D(aperture_verts))
    aperture.is_operable = True
    triple_pane = WindowConstruction(
        'Triple Pane Window', [clear_glass, air_gap, clear_glass, air_gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('TreeCanopy', tree_canopy_geo)
    tree_trans = ScheduleRuleset.from_constant_value(
        'Tree Transmittance', 0.75, schedule_types.fractional)
    tree_canopy.properties.energy.transmittance_schedule = tree_trans

    model = Model('TinyHouse', [room], orphaned_shades=[tree_canopy])
    model_dict = model.to_dict()
    new_model = Model.from_dict(model_dict)
    assert model_dict == new_model.to_dict()

    assert stone in new_model.properties.energy.materials
    assert thermal_mass_constr in new_model.properties.energy.constructions
    assert new_model.rooms[0][0].properties.energy.construction == thermal_mass_constr
    assert new_model.rooms[0][3].apertures[0].indoor_shades[0].properties.energy.construction == light_shelf_in
    assert new_model.rooms[0][3].apertures[0].outdoor_shades[0].properties.energy.construction == light_shelf_out
    assert triple_pane in new_model.properties.energy.constructions
    assert new_model.rooms[0][1].apertures[0].properties.energy.construction == triple_pane
    assert new_model.rooms[0][1].apertures[0].is_operable
    assert len(new_model.orphaned_shades) == 1

    assert new_model.rooms[0][0].type == face_types.floor
    assert new_model.rooms[0][1].type == face_types.wall
    assert isinstance(new_model.rooms[0][0].boundary_condition, Ground)
    assert isinstance(new_model.rooms[0][1].boundary_condition, Outdoors)

    assert new_model.rooms[0].properties.energy.program_type == office_program
    assert len(new_model.properties.energy.schedule_type_limits) == 3
    assert len(model.properties.energy.schedules) == 8
    assert new_model.rooms[0].properties.energy.is_conditioned
    assert new_model.rooms[0].properties.energy.hvac == room.properties.energy.hvac

    assert new_model.orphaned_shades[0].properties.energy.transmittance_schedule == tree_trans


def test_to_dict_single_zone():
    """Test the Model to_dict method with a single zone model."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Thermal Mass Floor', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.move_shades(Vector3D(0, 0, -0.5))
    light_shelf_out = ShadeConstruction('OutdoorLightShelf', 0.5, 0.5)
    light_shelf_in = ShadeConstruction('IndoorLightShelf', 0.7, 0.7)
    south_face.apertures[0].outdoor_shades[0].properties.energy.construction = light_shelf_out
    south_face.apertures[0].indoor_shades[0].properties.energy.construction = light_shelf_in

    north_face = room[1]
    north_face.overhang(0.25, indoor=False)
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('FrontDoor', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('FrontAperture', Face3D(aperture_verts))
    triple_pane = WindowConstruction(
        'Triple Pane Window', [clear_glass, air_gap, clear_glass, air_gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('TreeCanopy', tree_canopy_geo)

    table_geo = Face3D.from_rectangle(2, 2, Plane(o=Point3D(1.5, 4, 1)))
    table = Shade('Table', table_geo)
    room.add_indoor_shade(table)

    int_mass = InternalMass('Stone Fireplace', thermal_mass_constr, 8)
    room.properties.energy.internal_masses = [int_mass]

    model = Model('TinyHouse', [room], orphaned_shades=[tree_canopy])

    model_dict = model.to_dict()

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 3
    assert len(model_dict['properties']['energy']['constructions']) == 4
    assert len(model_dict['properties']['energy']['construction_sets']) == 0

    assert model_dict['rooms'][0]['faces'][0]['properties']['energy']['construction'] == \
        thermal_mass_constr.identifier
    south_ap_dict = model_dict['rooms'][0]['faces'][3]['apertures'][0]
    assert south_ap_dict['outdoor_shades'][0]['properties']['energy']['construction'] == \
        light_shelf_out.identifier
    assert south_ap_dict['indoor_shades'][0]['properties']['energy']['construction'] == \
        light_shelf_in.identifier
    assert model_dict['rooms'][0]['faces'][1]['apertures'][0]['properties']['energy']['construction'] == \
        triple_pane.identifier

    assert model_dict['rooms'][0]['properties']['energy']['program_type'] == \
        office_program.identifier
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == \
        room.properties.energy.hvac.identifier

    assert model_dict['rooms'][0]['properties']['energy']['internal_masses'][0]['identifier'] == \
        int_mass.identifier


def test_to_dict_single_zone_schedule_fixed_interval():
    """Test the Model to_dict method with a single zone model and fixed interval schedules."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    occ_sched = ScheduleFixedInterval(
        'Random Occupancy', [round(random.random(), 4) for i in range(8760)],
        schedule_types.fractional)
    new_people = room.properties.energy.people.duplicate()
    new_people.occupancy_schedule = occ_sched
    room.properties.energy.people = new_people

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.move_shades(Vector3D(0, 0, -0.5))
    light_shelf_out = ShadeConstruction('OutdoorLightShelf', 0.5, 0.5)
    light_shelf_in = ShadeConstruction('IndoorLightShelf', 0.7, 0.7)
    south_face.apertures[0].outdoor_shades[0].properties.energy.construction = light_shelf_out
    south_face.apertures[0].indoor_shades[0].properties.energy.construction = light_shelf_in

    north_face = room[1]
    north_face.overhang(0.25, indoor=False)
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('FrontDoor', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('FrontAperture', Face3D(aperture_verts))
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('TreeCanopy', tree_canopy_geo)
    winter = [0.75] * 2190
    spring = [0.75 - ((x / 2190) * 0.5) for x in range(2190)]
    summer = [0.25] * 2190
    fall = [0.25 + ((x / 2190) * 0.5) for x in range(2190)]
    trans_sched = ScheduleFixedInterval(
        'Seasonal Tree Transmittance', winter + spring + summer + fall,
        schedule_types.fractional)
    tree_canopy.properties.energy.transmittance_schedule = trans_sched

    model = Model('TinyHouse', [room], orphaned_shades=[tree_canopy])

    model_dict = model.to_dict()

    assert 'energy' in model_dict['properties']
    assert 'schedules' in model_dict['properties']['energy']
    assert 'program_types' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['program_types']) == 1
    assert len(model_dict['properties']['energy']['schedules']) == 9

    assert 'people' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['people']['occupancy_schedule'] \
        == 'Random Occupancy'
    assert model_dict['orphaned_shades'][0]['properties']['energy']['transmittance_schedule'] \
        == 'Seasonal Tree Transmittance'

    assert model_dict['rooms'][0]['properties']['energy']['program_type'] == \
        office_program.identifier


def test_to_dict_single_zone_detailed_loads():
    """Test the Model to_dict method with detailed, room-level loads."""
    room = Room.from_box('OfficeTestBox', 5, 10, 3)
    room.properties.energy.program_type = plenum_program
    room.properties.energy.add_default_ideal_air()

    room.properties.energy.people = office_program.people
    room.properties.energy.lighting = office_program.lighting
    room.properties.energy.electric_equipment = office_program.electric_equipment
    room.properties.energy.infiltration = office_program.infiltration
    room.properties.energy.ventilation = office_program.ventilation
    room.properties.energy.setpoint = office_program.setpoint
    
    fireplace = Process('Wood Burning Fireplace', 300,
                        office_program.people.occupancy_schedule, 'OtherFuel1')
    room.properties.energy.process_loads = [fireplace]

    room[0].boundary_condition = boundary_conditions.adiabatic
    room[1].boundary_condition = boundary_conditions.adiabatic
    room[2].boundary_condition = boundary_conditions.adiabatic
    room[4].boundary_condition = boundary_conditions.adiabatic
    room[5].boundary_condition = boundary_conditions.adiabatic

    model = Model('OfficeModel', [room])

    model_dict = model.to_dict()

    assert 'people' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['people']['identifier'] == \
        office_program.people.identifier
    assert 'lighting' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['lighting']['identifier'] == \
        office_program.lighting.identifier
    assert 'electric_equipment' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['electric_equipment']['identifier'] == \
        office_program.electric_equipment.identifier
    assert 'infiltration' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['infiltration']['identifier'] == \
        office_program.infiltration.identifier
    assert 'ventilation' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['ventilation']['identifier'] == \
        office_program.ventilation.identifier
    assert 'setpoint' in model_dict['rooms'][0]['properties']['energy']
    assert model_dict['rooms'][0]['properties']['energy']['setpoint']['identifier'] == \
        office_program.setpoint.identifier
    assert model_dict['rooms'][0]['properties']['energy']['process_loads'][0]['identifier'] == \
        fireplace.identifier


def test_to_dict_shoe_box():
    """Test the Model to_dict method with a shoebox zone model."""
    room = Room.from_box('SimpleShoeBoxZone', 5, 10, 3)
    room[0].boundary_condition = boundary_conditions.adiabatic
    for face in room[2:]:
        face.boundary_condition = boundary_conditions.adiabatic

    north_face = room[1]
    north_face.apertures_by_ratio_rectangle(0.4, 2, 0.7, 2, 0, 0.01)

    constr_set = ConstructionSet('Shoe Box Construction Set')
    constr_set.wall_set.exterior_construction = generic_exterior_wall
    constr_set.wall_set.interior_construction = generic_interior_wall
    constr_set.floor_set.interior_construction = generic_interior_floor
    constr_set.roof_ceiling_set.interior_construction = generic_interior_ceiling
    constr_set.aperture_set.window_construction = generic_double_pane
    room.properties.energy.construction_set = constr_set

    model = Model('ShoeBox', [room])
    model_dict = model.to_dict()
    model_dict['properties']['energy'] = model.properties.energy.to_dict()['energy']

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 10
    assert len(model_dict['properties']['energy']['constructions']) == 5

    assert model_dict['rooms'][0]['faces'][0]['boundary_condition']['type'] == 'Adiabatic'
    assert model_dict['rooms'][0]['faces'][2]['boundary_condition']['type'] == 'Adiabatic'


def test_to_dict_multizone_house():
    """Test the Model to_dict method with a multi-zone house."""
    first_floor = Room.from_box('FirstFloor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('SecondFloor', 10, 10, 3, origin=Point3D(0, 0, 3))
    first_floor.properties.energy.program_type = office_program
    second_floor.properties.energy.program_type = office_program
    first_floor.properties.energy.add_default_ideal_air()
    second_floor.properties.energy.add_default_ideal_air()
    for face in first_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    for face in second_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)

    pts_1 = [Point3D(0, 0, 6), Point3D(0, 10, 6), Point3D(10, 10, 6), Point3D(10, 0, 6)]
    pts_2 = [Point3D(0, 0, 6), Point3D(5, 0, 9), Point3D(5, 10, 9), Point3D(0, 10, 6)]
    pts_3 = [Point3D(10, 0, 6), Point3D(10, 10, 6), Point3D(5, 10, 9), Point3D(5, 0, 9)]
    pts_4 = [Point3D(0, 0, 6), Point3D(10, 0, 6), Point3D(5, 0, 9)]
    pts_5 = [Point3D(10, 10, 6), Point3D(0, 10, 6), Point3D(5, 10, 9)]
    face_1 = Face('AtticFace1', Face3D(pts_1))
    face_2 = Face('AtticFace2', Face3D(pts_2))
    face_3 = Face('AtticFace3', Face3D(pts_3))
    face_4 = Face('AtticFace4', Face3D(pts_4))
    face_5 = Face('AtticFace5', Face3D(pts_5))
    attic = Room('Attic', [face_1, face_2, face_3, face_4, face_5], 0.01, 1)

    constr_set = ConstructionSet('Attic Construction Set')
    polyiso = EnergyMaterial('PolyIso', 0.2, 0.03, 43, 1210, 'MediumRough')
    roof_constr = OpaqueConstruction('Attic Roof Construction',
                                     [roof_membrane, polyiso, wood])
    floor_constr = OpaqueConstruction('Attic Floor Construction',
                                      [wood, insulation, wood])
    constr_set.floor_set.interior_construction = floor_constr
    constr_set.roof_ceiling_set.exterior_construction = roof_constr
    attic.properties.energy.construction_set = constr_set

    Room.solve_adjacency([first_floor, second_floor, attic], 0.01)

    model = Model('MultiZoneSingleFamilyHouse', [first_floor, second_floor, attic])
    model_dict = model.to_dict()

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 4
    assert len(model_dict['properties']['energy']['constructions']) == 2
    assert len(model_dict['properties']['energy']['construction_sets']) == 1

    assert model_dict['rooms'][0]['faces'][5]['boundary_condition']['type'] == 'Surface'
    assert model_dict['rooms'][1]['faces'][0]['boundary_condition']['type'] == 'Surface'
    assert model_dict['rooms'][1]['faces'][5]['boundary_condition']['type'] == 'Surface'
    assert model_dict['rooms'][2]['faces'][0]['boundary_condition']['type'] == 'Surface'

    assert model_dict['rooms'][2]['properties']['energy']['construction_set'] == \
        constr_set.identifier

    assert model_dict['rooms'][0]['properties']['energy']['program_type'] == \
        model_dict['rooms'][1]['properties']['energy']['program_type'] == \
        office_program.identifier
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == \
        first_floor.properties.energy.hvac.identifier
    assert model_dict['rooms'][1]['properties']['energy']['hvac'] == \
        second_floor.properties.energy.hvac.identifier


def test_to_dict_air_walls():
    """Test the Model to_dict method with a multi-zone house."""
    pts_1 = [Point3D(0, 0), Point3D(30, 0), Point3D(20, 10), Point3D(10, 10)]
    pts_2 = [Point3D(0, 0), Point3D(10, 10), Point3D(10, 20), Point3D(0, 30)]
    pts_3 = [Point3D(10, 20), Point3D(20, 20), Point3D(30, 30), Point3D(0, 30)]
    pts_4 = [Point3D(30, 0), Point3D(30, 30), Point3D(20, 20), Point3D(20, 10)]
    verts = [pts_1, pts_2, pts_3, pts_4]
    rooms = []
    for i, f_vert in enumerate(verts):
        pface = Polyface3D.from_offset_face(Face3D(f_vert), 3)
        room = Room.from_polyface3d('PerimeterRoom{}'.format(i), pface)
        room.properties.energy.program_type = office_program
        room.properties.energy.add_default_ideal_air()
        rooms.append(room)
    rooms.append(Room.from_box('CoreRoom', 10, 10, 3, origin=Point3D(10, 10)))
    adj_info = Room.solve_adjacency(rooms, 0.01)
    for face_pair in adj_info['adjacent_faces']:
        face_pair[0].type = face_types.air_boundary
        face_pair[1].type = face_types.air_boundary

    model = Model('CorePerimeterOfficeFloor', rooms)
    model_dict = model.to_dict()
    assert model_dict['rooms'][-1]['faces'][1]['face_type'] == 'AirBoundary'
    new_model = Model.from_dict(model_dict)
    air_face_type = new_model.rooms[-1].faces[1]
    assert air_face_type.type == face_types.air_boundary
    assert isinstance(air_face_type.properties.energy.construction, AirBoundaryConstruction)

    model_idf_str = model.to.idf(model)
    assert model_idf_str.count('Construction:AirBoundary') == 1
    assert model_idf_str.count('ZoneMixing') == 16


def test_from_dict_non_abridged():
    """Test the Model from_dict method with non-abridged objects."""
    first_floor = Room.from_box('FirstFloor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('SecondFloor', 10, 10, 3, origin=Point3D(0, 0, 3))
    first_floor.properties.energy.program_type = office_program
    second_floor.properties.energy.program_type = office_program
    first_floor.properties.energy.add_default_ideal_air()
    second_floor.properties.energy.add_default_ideal_air()
    for face in first_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    for face in second_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)

    pts_1 = [Point3D(0, 0, 6), Point3D(0, 10, 6), Point3D(10, 10, 6), Point3D(10, 0, 6)]
    pts_2 = [Point3D(0, 0, 6), Point3D(5, 0, 9), Point3D(5, 10, 9), Point3D(0, 10, 6)]
    pts_3 = [Point3D(10, 0, 6), Point3D(10, 10, 6), Point3D(5, 10, 9), Point3D(5, 0, 9)]
    pts_4 = [Point3D(0, 0, 6), Point3D(10, 0, 6), Point3D(5, 0, 9)]
    pts_5 = [Point3D(10, 10, 6), Point3D(0, 10, 6), Point3D(5, 10, 9)]
    face_1 = Face('AtticFace1', Face3D(pts_1))
    face_2 = Face('AtticFace2', Face3D(pts_2))
    face_3 = Face('AtticFace3', Face3D(pts_3))
    face_4 = Face('AtticFace4', Face3D(pts_4))
    face_5 = Face('AtticFace5', Face3D(pts_5))
    attic = Room('Attic', [face_1, face_2, face_3, face_4, face_5], 0.01, 1)

    constr_set = ConstructionSet('Attic Construction Set')
    polyiso = EnergyMaterial('PolyIso', 0.2, 0.03, 43, 1210, 'MediumRough')
    roof_constr = OpaqueConstruction('Attic Roof Construction',
                                     [roof_membrane, polyiso, wood])
    floor_constr = OpaqueConstruction('Attic Floor Construction',
                                      [wood, insulation, wood])
    constr_set.floor_set.interior_construction = floor_constr
    constr_set.roof_ceiling_set.exterior_construction = roof_constr
    attic.properties.energy.construction_set = constr_set

    Room.solve_adjacency([first_floor, second_floor, attic], 0.01)

    model = Model('MultiZoneSingleFamilyHouse', [first_floor, second_floor, attic])
    model_dict = model.to_dict()

    model_dict['properties']['energy']['program_types'][0] = office_program.to_dict()
    model_dict['properties']['energy']['construction_sets'][0] = constr_set.to_dict()

    rebuilt_model = Model.from_dict(model_dict)
    assert rebuilt_model.rooms[0].properties.energy.program_type == office_program
    assert rebuilt_model.rooms[2].properties.energy.construction_set == constr_set


def test_writer_to_idf():
    """Test the Model to.idf method."""
    room = Room.from_box('TinyHouseZone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Thermal Mass Floor', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    south_face.apertures[0].overhang(0.5, indoor=False)
    south_face.apertures[0].overhang(0.5, indoor=True)
    south_face.move_shades(Vector3D(0, 0, -0.5))
    light_shelf_out = ShadeConstruction('OutdoorLightShelf', 0.5, 0.5)
    light_shelf_in = ShadeConstruction('IndoorLightShelf', 0.7, 0.7)
    south_face.apertures[0].outdoor_shades[0].properties.energy.construction = light_shelf_out
    south_face.apertures[0].indoor_shades[0].properties.energy.construction = light_shelf_in

    north_face = room[1]
    north_face.overhang(0.25, indoor=False)
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('FrontDoor', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('FrontAperture', Face3D(aperture_verts))
    triple_pane = WindowConstruction(
        'Triple Pane Window', [clear_glass, air_gap, clear_glass, air_gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('TreeCanopy', tree_canopy_geo)

    table_geo = Face3D.from_rectangle(2, 2, Plane(o=Point3D(1.5, 4, 1)))
    table = Shade('Table', table_geo)
    room.add_indoor_shade(table)

    model = Model('TinyHouse', [room], orphaned_shades=[tree_canopy])

    assert hasattr(model.to, 'idf')
    idf_string = model.to.idf(model, schedule_directory='./tests/idf/')
    assert len(idf_string) != 0

    room.properties.energy.hvac = VAV('Test VAV System')
    with pytest.raises(TypeError):
        idf_string = model.to.idf(
            model, schedule_directory='./tests/idf/', use_ideal_air_equivalent=False)


def test_energy_ventilation_simulation_properties():
    """Test the existence of the ventilation simulation control properties."""
    room = Room.from_box('Tiny_House_Zone', 5, 10, 3)
    room.properties.energy.program_type = office_program
    room.properties.energy.add_default_ideal_air()

    # ModelEnergyProperties will set ventilation cooling to single zone
    model = Model('Tiny_House', [room])
    assert hasattr(model.properties.energy, 'ventilation_simulation_control')

    vent = model.properties.energy.ventilation_simulation_control
    assert isinstance(vent, VentilationSimulationControl)
    assert vent.vent_control_type == 'SingleZone'
    assert vent.reference_temperature == pytest.approx(20, abs=1e-10)
    assert vent.reference_pressure == pytest.approx(101325, abs=1e-10)
    assert vent.reference_humidity_ratio == pytest.approx(0, abs=1e-10)
    assert vent.building_type == 'LowRise'
    assert vent.long_axis_angle == pytest.approx(0, abs=1e-10)
    assert vent.aspect_ratio == pytest.approx(1, abs=1e-10)

    # Test to_dict
    data = model.properties.energy.to_dict()
    assert 'ventilation_simulation_control' in data['energy']
    vent_dict = data['energy']['ventilation_simulation_control']
    vent_dict['reference_temperature'] == pytest.approx(20, abs=1e-10)
    vent_dict['building_type'] == 'LowRise'
    new_vent = VentilationSimulationControl.from_dict(vent_dict)
    assert new_vent == VentilationSimulationControl()
    assert vent_dict == new_vent.to_dict()

    # Add sim control obj
    model.properties.energy.ventilation_simulation_control = \
        VentilationSimulationControl('MultiZoneWithoutDistribution', 21, 101320, 0.5)
    vent = model.properties.energy.ventilation_simulation_control
    assert vent.vent_control_type == 'MultiZoneWithoutDistribution'
