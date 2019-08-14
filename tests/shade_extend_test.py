"""Tests the features that honeybee_energy adds to honeybee_core Shade."""
from honeybee.shade import Shade

from honeybee_energy.properties.shade import ShadeEnergyProperties

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

import pytest


def test_energy_properties():
    """Test the existence of the Shade energy properties."""
    shade = Shade.from_vertices(
        'overhang', [[0, 0, 3], [1, 0, 3], [1, 1, 3], [0, 1, 3]])

    assert hasattr(shade.properties, 'energy')
    assert isinstance(shade.properties.energy, ShadeEnergyProperties)
    assert isinstance(shade.properties.energy.diffuse_reflectance, float)
    assert isinstance(shade.properties.energy.specular_reflectance, float)
    assert isinstance(shade.properties.energy.transmittance, float)


def test_default_properties():
    """Test the auto-assigning of shade properties."""
    shade = Shade.from_vertices(
        'overhang', [[0, 0, 3], [1, 0, 3], [1, 1, 3], [0, 1, 3]])

    assert shade.properties.energy.diffuse_reflectance == 0.2
    assert shade.properties.energy.specular_reflectance == 0
    assert shade.properties.energy.transmittance == 0
    assert shade.properties.energy.transmittance_schedule is None


def test_set_properties():
    """Test the setting of properties on a Shade."""
    shade = Shade.from_vertices(
        'overhang', [[0, 0, 3], [1, 0, 3], [1, 1, 3], [0, 1, 3]])

    shade.properties.energy.diffuse_reflectance = 0.5
    assert shade.properties.energy.diffuse_reflectance == 0.5

    shade.properties.energy.specular_reflectance = 0.5
    assert shade.properties.energy.specular_reflectance == 0.5

    shade.properties.energy.transmittance = 0.25
    assert shade.properties.energy.transmittance == 0.25

    with pytest.raises(AssertionError):
        shade.properties.energy.diffuse_reflectance = 0.7


def test_duplicate():
    """Test what happens to energy properties when duplicating a Shade."""
    verts = [Point3D(0, 0, 0), Point3D(1, 0, 0), Point3D(1, 0, 3), Point3D(0, 0, 3)]
    shade_original = Shade('overhang', Face3D(verts))
    shade_dup_1 = shade_original.duplicate()

    assert shade_original.properties.energy.host is shade_original
    assert shade_dup_1.properties.energy.host is shade_dup_1
    assert shade_original.properties.energy.host is not \
        shade_dup_1.properties.energy.host

    assert shade_original.properties.energy.diffuse_reflectance == \
        shade_dup_1.properties.energy.diffuse_reflectance
    shade_dup_1.properties.energy.diffuse_reflectance = 0.7
    assert shade_original.properties.energy.diffuse_reflectance != \
        shade_dup_1.properties.energy.diffuse_reflectance

    shade_dup_2 = shade_dup_1.duplicate()

    assert shade_dup_1.properties.energy.diffuse_reflectance == \
        shade_dup_2.properties.energy.diffuse_reflectance
    shade_dup_2.properties.energy.diffuse_reflectance = 0.3
    assert shade_dup_1.properties.energy.diffuse_reflectance != \
        shade_dup_2.properties.energy.diffuse_reflectance


def test_to_dict():
    """Test the Shade to_dict method with energy properties."""
    verts = [Point3D(0, 0, 0), Point3D(1, 0, 0), Point3D(1, 0, 3), Point3D(0, 0, 3)]
    shade = Shade('overhang', Face3D(verts))

    shade_dict = shade.to_dict()
    assert 'properties' in shade_dict
    assert shade_dict['properties']['type'] == 'ShadeProperties'
    assert 'energy' in shade_dict['properties']
    assert shade_dict['properties']['energy']['type'] == 'ShadeEnergyProperties'

    shade.properties.energy.diffuse_reflectance = 0.7
    shade.properties.energy.specular_reflectance = 0.2
    shade.properties.energy.transmittance = 0.1
    shade_dict = shade.to_dict()
    assert 'diffuse_reflectance' in shade_dict['properties']['energy']
    assert 'specular_reflectance' in shade_dict['properties']['energy']
    assert 'transmittance' in shade_dict['properties']['energy']
    assert shade_dict['properties']['energy']['diffuse_reflectance'] == 0.7
    assert shade_dict['properties']['energy']['specular_reflectance'] == 0.2
    assert shade_dict['properties']['energy']['transmittance'] == 0.1


def test_from_dict():
    """Test the Shade from_dict method with energy properties."""
    verts = [Point3D(0, 0, 0), Point3D(1, 0, 0), Point3D(1, 0, 3), Point3D(0, 0, 3)]
    shade = Shade('overhang', Face3D(verts))
    shade.properties.energy.diffuse_reflectance = 0.7
    shade.properties.energy.specular_reflectance = 0.2
    shade.properties.energy.transmittance = 0.1

    shade_dict = shade.to_dict()
    new_shade = Shade.from_dict(shade_dict)
    assert new_shade.properties.energy.diffuse_reflectance == 0.7
    assert new_shade.properties.energy.specular_reflectance == 0.2
    assert new_shade.properties.energy.transmittance == 0.1
    assert new_shade.to_dict() == shade_dict
