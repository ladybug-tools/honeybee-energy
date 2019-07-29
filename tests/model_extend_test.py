"""Tests the features that honeybee_energy adds to honeybee_core Model."""
from honeybee.model import Model
from honeybee.room import Room
from honeybee.face import Face
from honeybee.shade import Shade
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.boundarycondition import boundary_conditions, Ground, Outdoors
from honeybee.facetype import face_types
from honeybee.aperturetype import aperture_types

from honeybee_energy.properties.model import ModelEnergyProperties
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.construction import WindowConstruction, OpaqueConstruction, \
    _ConstructionBase
from honeybee_energy.material._base import _EnergyMaterialBase
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.lib.default.face import clear_glass, gap, generic_exterior_wall, \
    generic_interior_wall, generic_interior_floor, generic_interior_ceiling, \
    generic_double_pane, roof_membrane, wood, insulation

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.face import Face3D

import json
import pytest


def test_energy_properties():
    """Test the existence of the Model energy properties."""
    room = Room.from_box('Tiny House Zone', 5, 10, 3)
    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    out_shelf = south_face.apertures[0].overhang(0.5, indoor=False)
    in_shelf = south_face.apertures[0].overhang(0.5, indoor=True)
    out_shelf.move(Vector3D(0, 0, -0.5))
    in_shelf.move(Vector3D(0, 0, -0.5))
    room.add_outdoor_shade(out_shelf)
    room.add_indoor_shade(in_shelf)
    model = Model('Tiny House', [room])

    assert hasattr(model.properties, 'energy')
    assert isinstance(model.properties.energy, ModelEnergyProperties)
    assert isinstance(model.properties.host, Model)
    assert len(model.properties.energy.unique_materials) == 14
    for mat in model.properties.energy.unique_materials:
        assert isinstance(mat, _EnergyMaterialBase)
    assert len(model.properties.energy.unique_constructions) == 13
    for mat in model.properties.energy.unique_constructions:
        assert isinstance(mat, _ConstructionBase)
    assert len(model.properties.energy.unique_face_constructions) == 0
    assert len(model.properties.energy.unique_construction_sets) == 0
    assert isinstance(model.properties.energy.global_construction_set, ConstructionSet)


def test_check_duplicate_construction_set_names():
    """Test the check_duplicate_construction_set_names method."""
    first_floor = Room.from_box('First Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    for face in first_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    for face in second_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)

    pts_1 = [Point3D(0, 0, 6), Point3D(0, 10, 6), Point3D(10, 10, 6), Point3D(10, 0, 6)]
    pts_2 = [Point3D(0, 0, 6), Point3D(5, 0, 9), Point3D(5, 10, 9), Point3D(0, 10, 6)]
    pts_3 = [Point3D(10, 0, 6), Point3D(10, 10, 6), Point3D(5, 10, 9), Point3D(5, 0, 9)]
    pts_4 = [Point3D(0, 0, 6), Point3D(10, 0, 6), Point3D(5, 0, 9)]
    pts_5 = [Point3D(10, 10, 6), Point3D(0, 10, 6), Point3D(5, 10, 9)]
    face_1 = Face('Attic Face 1', Face3D(pts_1))
    face_2 = Face('Attic Face 2', Face3D(pts_2))
    face_3 = Face('Attic Face 3', Face3D(pts_3))
    face_4 = Face('Attic Face 4', Face3D(pts_4))
    face_5 = Face('Attic Face 5', Face3D(pts_5))
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

    Room.solve_adjcency([first_floor, second_floor, attic], 0.01)

    model = Model('Multi Zone Single Family House', [first_floor, second_floor, attic])

    assert model.properties.energy.check_duplicate_construction_set_names(False)
    constr_set.unlock()
    constr_set.name = 'Default Generic Construction Set'
    constr_set.lock()
    assert not model.properties.energy.check_duplicate_construction_set_names(False)
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_construction_set_names(True)


def test_check_duplicate_construction_names():
    """Test the check_duplicate_construction_names method."""
    room = Room.from_box('Tiny House Zone', 5, 10, 3)

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Custom Construction', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    north_face = room[1]
    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('Front Aperture', Face3D(aperture_verts))
    aperture.type = aperture_types.glass_door
    triple_pane = WindowConstruction(
        'Custom Window Construction', [clear_glass, gap, clear_glass, gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    model = Model('Tiny House', [room])

    assert model.properties.energy.check_duplicate_construction_names(False)
    triple_pane.unlock()
    triple_pane.name = 'Custom Construction'
    triple_pane.lock()
    assert not model.properties.energy.check_duplicate_construction_names(False)
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_construction_names(True)


def test_check_duplicate_material_names():
    """Test the check_duplicate_material_names method."""
    room = Room.from_box('Tiny House Zone', 5, 10, 3)

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
    door = Door('Front Door', Face3D(door_verts))
    door.properties.energy.construction = door_constr
    north_face.add_door(door)

    model = Model('Tiny House', [room])

    assert model.properties.energy.check_duplicate_material_names(False)
    thin_stone.unlock()
    thin_stone.name = 'Stone'
    thin_stone.lock()
    assert not model.properties.energy.check_duplicate_material_names(False)
    with pytest.raises(ValueError):
        model.properties.energy.check_duplicate_material_names(True)


def test_to_from_dict():
    """Test the Model to_dict and from_dict method with a single zone model."""
    room = Room.from_box('Tiny House Zone', 5, 10, 3)

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Thermal Mass Floor', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    out_shelf = south_face.apertures[0].overhang(0.5, indoor=False)
    in_shelf = south_face.apertures[0].overhang(0.5, indoor=True)
    out_shelf.move(Vector3D(0, 0, -0.5))
    in_shelf.move(Vector3D(0, 0, -0.5))
    out_shelf.properties.energy.diffuse_reflectance = 0.5
    in_shelf.properties.energy.diffuse_reflectance = 0.7
    room.add_outdoor_shade(out_shelf)
    room.add_indoor_shade(in_shelf)

    north_face = room[1]
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('Front Door', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('Front Aperture', Face3D(aperture_verts))
    aperture.type = aperture_types.glass_door
    triple_pane = WindowConstruction(
        'Triple Pane Window', [clear_glass, gap, clear_glass, gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('Tree Canopy', tree_canopy_geo)
    tree_canopy.properties.energy.transmittance = 0.75

    model = Model('Tiny House', [room], orphaned_shades=[tree_canopy])
    model.north_angle = 15
    model_dict = model.to_dict()
    new_model = Model.from_dict(model_dict)
    assert model_dict == new_model.to_dict()

    assert stone in new_model.properties.energy.unique_materials
    assert thermal_mass_constr in new_model.properties.energy.unique_constructions
    assert new_model.rooms[0][0].properties.energy.construction == thermal_mass_constr
    assert new_model.rooms[0].indoor_shades[0].properties.energy.diffuse_reflectance == 0.7
    assert new_model.rooms[0].outdoor_shades[0].properties.energy.diffuse_reflectance == 0.5
    assert triple_pane in new_model.properties.energy.unique_constructions
    assert new_model.rooms[0][1].apertures[0].properties.energy.construction == triple_pane
    assert new_model.rooms[0][1].apertures[0].type == aperture_types.glass_door
    assert len(new_model.orphaned_shades) == 1
    assert new_model.orphaned_shades[0].properties.energy.transmittance == 0.75
    assert new_model.north_angle == 15

    assert new_model.rooms[0][0].type == face_types.floor
    assert new_model.rooms[0][1].type == face_types.wall
    assert isinstance(new_model.rooms[0][0].boundary_condition, Ground)
    assert isinstance(new_model.rooms[0][1].boundary_condition, Outdoors)


def test_to_dict_single_zone():
    """Test the Model to_dict method with a single zone model."""
    room = Room.from_box('Tiny House Zone', 5, 10, 3)

    stone = EnergyMaterial('Thick Stone', 0.3, 2.31, 2322, 832, 'Rough',
                           0.95, 0.75, 0.8)
    thermal_mass_constr = OpaqueConstruction('Thermal Mass Floor', [stone])
    room[0].properties.energy.construction = thermal_mass_constr

    south_face = room[3]
    south_face.apertures_by_ratio(0.4, 0.01)
    out_shelf = south_face.apertures[0].overhang(0.5, indoor=False)
    in_shelf = south_face.apertures[0].overhang(0.5, indoor=True)
    out_shelf.move(Vector3D(0, 0, -0.5))
    in_shelf.move(Vector3D(0, 0, -0.5))
    out_shelf.properties.energy.diffuse_reflectance = 0.5
    in_shelf.properties.energy.diffuse_reflectance = 0.7
    room.add_outdoor_shade(out_shelf)
    room.add_indoor_shade(in_shelf)

    north_face = room[1]
    door_verts = [Point3D(2, 10, 0.1), Point3D(1, 10, 0.1),
                  Point3D(1, 10, 2.5), Point3D(2, 10, 2.5)]
    door = Door('Front Door', Face3D(door_verts))
    north_face.add_door(door)

    aperture_verts = [Point3D(4.5, 10, 1), Point3D(2.5, 10, 1),
                      Point3D(2.5, 10, 2.5), Point3D(4.5, 10, 2.5)]
    aperture = Aperture('Front Aperture', Face3D(aperture_verts))
    triple_pane = WindowConstruction(
        'Triple Pane Window', [clear_glass, gap, clear_glass, gap, clear_glass])
    aperture.properties.energy.construction = triple_pane
    north_face.add_aperture(aperture)

    tree_canopy_geo = Face3D.from_regular_polygon(
        6, 2, Plane(Vector3D(0, 0, 1), Point3D(5, -3, 4)))
    tree_canopy = Shade('Tree Canopy', tree_canopy_geo)
    tree_canopy.properties.energy.transmittance = 0.75

    model = Model('Tiny House', [room], orphaned_shades=[tree_canopy])
    model.north_angle = 15

    model_dict = model.to_dict()

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']
    assert 'global_construction_set' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 15
    assert len(model_dict['properties']['energy']['constructions']) == 15
    assert len(model_dict['properties']['energy']['construction_sets']) == 1

    assert model_dict['faces'][0]['properties']['energy']['construction'] == \
        thermal_mass_constr.name
    assert model_dict['shades'][0]['properties']['energy']['diffuse_reflectance'] == 0.7
    assert model_dict['shades'][1]['properties']['energy']['diffuse_reflectance'] == 0.5
    assert model_dict['apertures'][0]['properties']['energy']['construction'] == \
        triple_pane.name

    """
    dest_file = 'C:/Users/chris/Documents/GitHub/energy-model-schema/tests/fixtures'
        '/1_single_zone_tiny_house.json'
    with open(dest_file, 'w') as fp:
        json.dump(model_dict, fp, indent=4)
    """


def test_to_dict_shoe_box():
    """Test the Model to_dict method with a shoebox zone model."""
    room = Room.from_box('Simple Shoe Box Zone', 5, 10, 3)
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
    constr_set.aperture_set.fixed_window_construction = generic_double_pane
    room.properties.energy.construction_set = constr_set

    model = Model('Shoe Box', [room])
    model_dict = model.to_dict()
    model_dict['properties']['energy'] = model.properties.energy.to_dict(
        include_global_construction_set=False)['energy']

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 9
    assert len(model_dict['properties']['energy']['constructions']) == 5

    assert model_dict['faces'][0]['boundary_condition']['type'] == 'Adiabatic'
    assert model_dict['faces'][2]['boundary_condition']['type'] == 'Adiabatic'

    """
    dest_file = 'C:/Users/chris/Documents/GitHub/energy-model-schema/tests/fixtures'
        '/2_shoe_box.json'
    with open(dest_file, 'w') as fp:
        json.dump(model_dict, fp, indent=4)
    """


def test_to_dict_multizone_house():
    """Test the Model to_dict method with a multi-zone house."""
    first_floor = Room.from_box('First Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    for face in first_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)
    for face in second_floor[1:5]:
        face.apertures_by_ratio(0.2, 0.01)

    pts_1 = [Point3D(0, 0, 6), Point3D(0, 10, 6), Point3D(10, 10, 6), Point3D(10, 0, 6)]
    pts_2 = [Point3D(0, 0, 6), Point3D(5, 0, 9), Point3D(5, 10, 9), Point3D(0, 10, 6)]
    pts_3 = [Point3D(10, 0, 6), Point3D(10, 10, 6), Point3D(5, 10, 9), Point3D(5, 0, 9)]
    pts_4 = [Point3D(0, 0, 6), Point3D(10, 0, 6), Point3D(5, 0, 9)]
    pts_5 = [Point3D(10, 10, 6), Point3D(0, 10, 6), Point3D(5, 10, 9)]
    face_1 = Face('Attic Face 1', Face3D(pts_1))
    face_2 = Face('Attic Face 2', Face3D(pts_2))
    face_3 = Face('Attic Face 3', Face3D(pts_3))
    face_4 = Face('Attic Face 4', Face3D(pts_4))
    face_5 = Face('Attic Face 5', Face3D(pts_5))
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

    Room.solve_adjcency([first_floor, second_floor, attic], 0.01)

    model = Model('Multi Zone Single Family House', [first_floor, second_floor, attic])
    model_dict = model.to_dict()

    assert 'energy' in model_dict['properties']
    assert 'materials' in model_dict['properties']['energy']
    assert 'constructions' in model_dict['properties']['energy']
    assert 'construction_sets' in model_dict['properties']['energy']
    assert 'global_construction_set' in model_dict['properties']['energy']

    assert len(model_dict['properties']['energy']['materials']) == 15
    assert len(model_dict['properties']['energy']['constructions']) == 15
    assert len(model_dict['properties']['energy']['construction_sets']) == 2

    assert model_dict['faces'][5]['boundary_condition']['type'] == 'Surface'
    assert model_dict['faces'][6]['boundary_condition']['type'] == 'Surface'
    assert model_dict['faces'][11]['boundary_condition']['type'] == 'Surface'
    assert model_dict['faces'][12]['boundary_condition']['type'] == 'Surface'

    assert model_dict['rooms'][2]['properties']['energy']['construction_set'] == \
        constr_set.name

    """
    dest_file = 'C:/Users/chris/Documents/GitHub/energy-model-schema/tests/fixtures'
        '/3_multi_zone_single_family_house.json'
    with open(dest_file, 'w') as fp:
        json.dump(model_dict, fp, indent=4)
    """
