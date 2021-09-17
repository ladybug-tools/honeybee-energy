"""Tests the features that honeybee_energy adds to honeybee_core Door."""
from honeybee.room import Room
from honeybee.face import Face
from honeybee.door import Door

from honeybee_energy.properties.door import DoorEnergyProperties
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

import pytest

def test_energy_properties():
    """Test the existence of the Door energy properties."""
    door = Door.from_vertices(
        'wall_door', [[0, 0, 0], [1, 0, 0], [1, 0, 3], [0, 0, 3]])
    assert hasattr(door.properties, 'energy')
    assert isinstance(door.properties.energy, DoorEnergyProperties)
    assert isinstance(door.properties.energy.construction, OpaqueConstruction)
    assert not door.properties.energy.is_construction_set_on_object


def test_default_constructions():
    """Test the auto-assigning of constructions by boundary condition."""
    vertices_parent_wall = [[0, 0, 0], [0, 10, 0], [0, 10, 3], [0, 0, 3]]
    vertices_parent_wall_2 = list(reversed(vertices_parent_wall))
    vertices_wall = [[0, 1, 0], [0, 2, 0], [0, 2, 2], [0, 0, 2]]
    vertices_wall_2 = list(reversed(vertices_wall))
    vertices_floor = [[0, 0, 0], [0, 1, 0], [1, 1, 0], [1, 0, 0]]
    vertices_roof = [[1, 0, 3], [1, 1, 3], [0, 1, 3], [0, 0, 3]]

    wf = Face.from_vertices('wall_face', vertices_parent_wall)
    wdr = Door.from_vertices('wall_door', vertices_wall)
    wf.add_door(wdr)
    Room('Test_Room_1', [wf])
    assert wdr.properties.energy.construction.identifier == 'Generic Exterior Door'

    wf2 = Face.from_vertices('wall_face2', vertices_parent_wall_2)
    wdr2 = Door.from_vertices('wall_door2', vertices_wall_2)
    wf2.add_door(wdr2)
    Room('Test_Room_2', [wf2])
    wdr.set_adjacency(wdr2)
    assert wdr.properties.energy.construction.identifier == 'Generic Interior Door'

    ra = Door.from_vertices('roof_door', vertices_roof)
    assert ra.properties.energy.construction.identifier == 'Generic Exterior Door'
    fa = Door.from_vertices('floor_door', vertices_floor)
    assert fa.properties.energy.construction.identifier == 'Generic Exterior Door'


def test_set_construction():
    """Test the setting of a construction on a Door."""
    vertices_wall = [[0, 0, 0], [0, 10, 0], [0, 10, 3], [0, 0, 3]]
    concrete5 = EnergyMaterial('5cm Concrete', 0.05, 2.31, 2322, 832,
                               'MediumRough', 0.95, 0.75, 0.8)
    mass_constr = OpaqueConstruction('Concrete Door', [concrete5])

    door = Door.from_vertices('wall_door', vertices_wall)
    door.properties.energy.construction = mass_constr

    assert door.properties.energy.construction == mass_constr
    assert door.properties.energy.is_construction_set_on_object

    with pytest.raises(AttributeError):
        door.properties.energy.construction[0].thickness = 0.1


def test_duplicate():
    """Test what happens to energy properties when duplicating a Door."""
    verts = [Point3D(0, 0, 0), Point3D(1, 0, 0), Point3D(1, 0, 3), Point3D(0, 0, 3)]
    concrete5 = EnergyMaterial('5cm Concrete', 0.05, 2.31, 2322, 832,
                               'MediumRough', 0.95, 0.75, 0.8)
    mass_constr = OpaqueConstruction('Concrete Door', [concrete5])

    door_original = Door('wall_door', Face3D(verts))
    door_dup_1 = door_original.duplicate()

    assert door_original.properties.energy.host is door_original
    assert door_dup_1.properties.energy.host is door_dup_1
    assert door_original.properties.energy.host is not \
        door_dup_1.properties.energy.host

    assert door_original.properties.energy.construction == \
        door_dup_1.properties.energy.construction
    door_dup_1.properties.energy.construction = mass_constr
    assert door_original.properties.energy.construction != \
        door_dup_1.properties.energy.construction

    door_dup_2 = door_dup_1.duplicate()

    assert door_dup_1.properties.energy.construction == \
        door_dup_2.properties.energy.construction
    door_dup_2.properties.energy.construction = None
    assert door_dup_1.properties.energy.construction != \
        door_dup_2.properties.energy.construction


def test_to_dict():
    """Test the Door to_dict method with energy properties."""
    door = Door.from_vertices(
        'front_door', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    concrete5 = EnergyMaterial('5cm Concrete', 0.05, 2.31, 2322, 832,
                               'MediumRough', 0.95, 0.75, 0.8)
    mass_constr = OpaqueConstruction('Concrete Door', [concrete5])

    drd = door.to_dict()
    assert 'properties' in drd
    assert drd['properties']['type'] == 'DoorProperties'
    assert 'energy' in drd['properties']
    assert drd['properties']['energy']['type'] == 'DoorEnergyProperties'

    door.properties.energy.construction = mass_constr
    drd = door.to_dict()
    assert 'construction' in drd['properties']['energy']
    assert drd['properties']['energy']['construction'] is not None


def test_from_dict():
    """Test the Door from_dict method with energy properties."""
    door = Door.from_vertices(
        'front_door', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    concrete5 = EnergyMaterial('5cm Concrete', 0.05, 2.31, 2322, 832,
                               'MediumRough', 0.95, 0.75, 0.8)
    mass_constr = OpaqueConstruction('Concrete Door', [concrete5])
    door.properties.energy.construction = mass_constr

    drd = door.to_dict()
    new_door = Door.from_dict(drd)
    assert new_door.properties.energy.construction == mass_constr
    assert new_door.to_dict() == drd


def test_writer_to_idf():
    """Test the Door to_idf method."""
    door = Door.from_vertices(
        'front_door', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    concrete5 = EnergyMaterial('5cm Concrete', 0.05, 2.31, 2322, 832,
                               'MediumRough', 0.95, 0.75, 0.8)
    mass_constr = OpaqueConstruction('ConcreteDoor', [concrete5])
    door.properties.energy.construction = mass_constr

    assert hasattr(door.to, 'idf')
    idf_string = door.to.idf(door)
    assert 'front_door,' in idf_string
    assert 'FenestrationSurface:Detailed,' in idf_string
    assert 'ConcreteDoor' in idf_string
