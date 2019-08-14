"""Tests the features that honeybee_energy adds to honeybee_core Room."""
from honeybee.room import Room
from honeybee.door import Door

from honeybee_energy.properties.room import RoomEnergyProperties
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.programtype import ProgramType
from honeybee_energy.construction import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial

from ladybug_geometry.geometry3d.pointvector import Point3D

import pytest


def test_energy_properties():
    """Test the existence of the Room energy properties."""
    room = Room.from_box('Shoe Box', 5, 10, 3, 90, Point3D(0, 0, 3))

    assert hasattr(room.properties, 'energy')
    assert isinstance(room.properties.energy, RoomEnergyProperties)
    assert isinstance(room.properties.energy.construction_set, ConstructionSet)
    assert isinstance(room.properties.energy.program_type, ProgramType)


def test_default_properties():
    """Test the auto-assigning of Room properties."""
    room = Room.from_box('Shoe Box', 5, 10, 3, 90, Point3D(0, 0, 3))

    assert room.properties.energy.construction_set.name == \
        'Default Generic Construction Set'
    assert room.properties.energy.program_type.name == 'Plenum'


def test_set_construction_set():
    """Test the setting of a ConstructionSet on a Room."""
    room = Room.from_box('Shoe Box', 5, 10, 3)
    door_verts = [[1, 0, 0.1], [2, 0, 0.1], [2, 0, 3], [1, 0, 3]]
    room[3].add_door(Door.from_vertices('test_door', door_verts))

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
    mass_set.wall_set.exterior_construction = thick_constr
    mass_set.roof_ceiling_set.exterior_construction = thin_constr
    mass_set.door_set.exterior_construction = door_constr

    room.properties.energy.construction_set = mass_set
    assert room.properties.energy.construction_set == mass_set
    assert room[1].properties.energy.construction == thick_constr
    assert room[5].properties.energy.construction == thin_constr
    assert room[3].doors[0].properties.energy.construction == door_constr

    with pytest.raises(AttributeError):
        room[1].properties.energy.construction.thickness = 0.3
    with pytest.raises(AttributeError):
        room[5].properties.energy.construction.thickness = 0.3
    with pytest.raises(AttributeError):
        room[3].doors[0].properties.energy.construction.thickness = 0.3


def test_set_program_type():
    """Test the setting of a ProgramType on a Room."""
    room = Room.from_box('Shoe Box', 5, 10, 3)

    lab_program = ProgramType('Laboratory')
    room.properties.energy.program_type = lab_program
    assert room.properties.energy.program_type.name == 'Laboratory'


def test_duplicate():
    """Test what happens to energy properties when duplicating a Room."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room_original = Room.from_box('Shoe Box', 5, 10, 3)
    room_dup_1 = room_original.duplicate()

    assert room_original.properties.energy.host is room_original
    assert room_dup_1.properties.energy.host is room_dup_1
    assert room_original.properties.energy.host is not \
        room_dup_1.properties.energy.host

    assert room_original.properties.energy.construction_set == \
        room_dup_1.properties.energy.construction_set
    room_dup_1.properties.energy.construction_set = mass_set
    assert room_original.properties.energy.construction_set != \
        room_dup_1.properties.energy.construction_set

    room_dup_2 = room_dup_1.duplicate()

    assert room_dup_1.properties.energy.construction_set == \
        room_dup_2.properties.energy.construction_set
    room_dup_2.properties.energy.construction_set = None
    assert room_dup_1.properties.energy.construction_set != \
        room_dup_2.properties.energy.construction_set


def test_to_dict():
    """Test the Room to_dict method with energy properties."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room = Room.from_box('Shoe Box', 5, 10, 3)

    rd = room.to_dict()
    assert 'properties' in rd
    assert rd['properties']['type'] == 'RoomProperties'
    assert 'energy' in rd['properties']
    assert rd['properties']['energy']['type'] == 'RoomEnergyProperties'
    assert rd['properties']['energy']['program_type'] is None
    assert rd['properties']['energy']['construction_set'] is None
    assert rd['properties']['energy']['people'] is None
    assert rd['properties']['energy']['lighting'] is None
    assert rd['properties']['energy']['electric_equipment'] is None
    assert rd['properties']['energy']['gas_equipment'] is None
    assert rd['properties']['energy']['infiltration'] is None
    assert rd['properties']['energy']['ventilation'] is None

    room.properties.energy.construction_set = mass_set
    rd = room.to_dict()
    assert rd['properties']['energy']['construction_set'] is not None


def test_from_dict():
    """Test the Room from_dict method with energy properties."""
    mass_set = ConstructionSet('Thermal Mass Construction Set')
    room = Room.from_box('Shoe Box', 5, 10, 3)
    room.properties.energy.construction_set = mass_set

    rd = room.to_dict()
    new_room = Room.from_dict(rd)
    assert new_room.properties.energy.construction_set.name == \
        'Thermal Mass Construction Set'
    assert new_room.to_dict() == rd
