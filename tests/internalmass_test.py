# coding=utf-8
from honeybee.room import Room
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

from honeybee_energy.internalmass import InternalMass
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial

import pytest
from .fixtures.userdata_fixtures import userdatadict


def test_internal_mass_init(userdatadict):
    """Test the initialization of InternalMass and basic properties."""
    rammed_earth = EnergyMaterial('40cm Rammed Earth', 0.4, 2.31, 2322, 832,
                                  'MediumRough', 0.95, 0.75, 0.8)
    earth_constr = OpaqueConstruction('Rammed Earth Construction', [rammed_earth])
    chimney_mass = InternalMass('Rammed Earth Chimney', earth_constr, 10)
    chimney_mass.user_data = userdatadict
    str(chimney_mass)  # test the string representation

    assert chimney_mass.identifier == chimney_mass.display_name == 'Rammed Earth Chimney'
    assert chimney_mass.construction == earth_constr
    assert chimney_mass.area == 10

    stone = EnergyMaterial('Stone Veneer', 0.1, 2.31, 2322, 832,
                           'MediumRough', 0.95, 0.75, 0.8)
    stone_constr = OpaqueConstruction('Stone Veneer', [stone])

    chimney_mass.construction = stone_constr
    chimney_mass.area = 8

    assert chimney_mass.construction == stone_constr
    assert chimney_mass.area == 8
    assert chimney_mass.user_data == userdatadict


def test_internal_mass_equality(userdatadict):
    """Test the equality of InternalMass objects."""
    rammed_earth = EnergyMaterial('40cm Rammed Earth', 0.4, 2.31, 2322, 832,
                                  'MediumRough', 0.95, 0.75, 0.8)
    earth_constr = OpaqueConstruction('Rammed Earth Construction', [rammed_earth])
    stone = EnergyMaterial('Stone Veneer', 0.1, 2.31, 2322, 832,
                           'MediumRough', 0.95, 0.75, 0.8)
    stone_constr = OpaqueConstruction('Stone Veneer', [stone])

    chimney_mass = InternalMass('Rammed Earth Chimney', earth_constr, 10)
    chimney_mass.user_data = userdatadict
    chimney_mass_dup = chimney_mass.duplicate()
    chimney_mass_alt = InternalMass('Rammed Earth Chimney', stone_constr, 10)

    assert chimney_mass is chimney_mass
    assert chimney_mass is not chimney_mass_dup
    assert chimney_mass == chimney_mass_dup
    chimney_mass_dup.area = 5
    assert chimney_mass != chimney_mass_dup
    assert chimney_mass != chimney_mass_alt


def test_internal_mass_lockability(userdatadict):
    """Test the lockability of InternalMass objects."""
    rammed_earth = EnergyMaterial('40cm Rammed Earth', 0.4, 2.31, 2322, 832,
                                  'MediumRough', 0.95, 0.75, 0.8)
    earth_constr = OpaqueConstruction('Rammed Earth Construction', [rammed_earth])
    chimney_mass = InternalMass('Rammed Earth Chimney', earth_constr, 10)
    chimney_mass.user_data = userdatadict

    chimney_mass.area = 5
    chimney_mass.lock()
    with pytest.raises(AttributeError):
        chimney_mass.area = 8
    chimney_mass.unlock()
    chimney_mass.area = 8


def test_internal_mass_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    rammed_earth = EnergyMaterial('40cm Rammed Earth', 0.4, 2.31, 2322, 832,
                                  'MediumRough', 0.95, 0.75, 0.8)
    rammed_earth.user_data = userdatadict
    earth_constr = OpaqueConstruction('Rammed Earth Construction', [rammed_earth])
    earth_constr.user_data = userdatadict
    chimney_mass = InternalMass('Rammed Earth Chimney', earth_constr, 10)
    chimney_mass.user_data = userdatadict

    mass_dict = chimney_mass.to_dict()
    new_chimney_mass = InternalMass.from_dict(mass_dict)
    assert new_chimney_mass == chimney_mass
    assert mass_dict == new_chimney_mass.to_dict()


def test_internal_mass_idf_methods(userdatadict):
    """Test the to/from IDF methods."""
    rammed_earth = EnergyMaterial('40cm Rammed Earth', 0.4, 2.31, 2322, 832,
                                  'MediumRough', 0.95, 0.75, 0.8)
    earth_constr = OpaqueConstruction('Rammed Earth Construction', [rammed_earth])
    chimney_mass = InternalMass('Rammed Earth Chimney', earth_constr, 10)
    chimney_mass.user_data = userdatadict

    mass_idf = chimney_mass.to_idf('Test Room')
    new_chimney_mass = InternalMass.from_idf(
        mass_idf, {'Rammed Earth Construction': earth_constr})
    assert new_chimney_mass == chimney_mass
    assert mass_idf == new_chimney_mass.to_idf('Test Room')



def test_assign_to_room(userdatadict):
    """Test the assignment of internal masses to rooms."""
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    concrete10 = EnergyMaterial('10cm Concrete', 0.1, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction('Thick Concrete Construction', [concrete20])
    thin_constr = OpaqueConstruction('Thin Concrete Construction', [concrete10])

    room = Room.from_box('ShoeBox', 5, 10, 3, 0)

    table_verts = [Point3D(1, 1, 1), Point3D(2, 1, 1), Point3D(2, 2, 1), Point3D(1, 2, 1)]
    table_geo = Face3D(table_verts)
    table_mass = InternalMass.from_geometry(
        'Concrete Table', thick_constr, [table_geo], 'Meters')
    table_mass.user_data = userdatadict
    chair_mass = InternalMass('Concrete Chair', thin_constr, 1)
    chair_mass.user_data = userdatadict

    assert len(room.properties.energy.internal_masses) == 0
    room.properties.energy.internal_masses = [table_mass]
    assert len(room.properties.energy.internal_masses) == 1
    room.properties.energy.add_internal_mass(chair_mass)

    idf_str = room.to.idf(room)
    assert idf_str.find('InternalMass,') > -1
