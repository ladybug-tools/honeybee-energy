"""Tests the features that honeybee_energy adds to honeybee_core Face."""
from honeybee.face import Face
from honeybee.boundarycondition import boundary_conditions

from honeybee_energy.properties.face import FaceEnergyProperties
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.ventcool.crack import AFNCrack

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D

import pytest


def test_energy_properties():
    """Test the existence of the Face energy properties."""
    face = Face.from_vertices(
        'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    assert hasattr(face.properties, 'energy')
    assert isinstance(face.properties.energy, FaceEnergyProperties)
    assert isinstance(face.properties.energy.construction, OpaqueConstruction)
    assert not face.properties.energy.is_construction_set_on_object
    assert face.properties.energy.vent_crack is None

    with pytest.raises(AssertionError):
        face.properties.energy.vent_crack = AFNCrack(0, 0)
    face.properties.energy.vent_crack = AFNCrack(1e-5, 0.65)
    assert face.properties.energy.vent_crack.flow_coefficient == \
        pytest.approx(1e-5, abs=1e-10)
    assert face.properties.energy.vent_crack.flow_exponent == \
        pytest.approx(0.65, abs=1e-10)

def test_default_constructions():
    """Test the auto-assigning of constructions by face type and boundary condition."""
    vertices_wall = [[0, 0, 0], [0, 10, 0], [0, 10, 3], [0, 0, 3]]
    vertices_floor = [[0, 0, 0], [0, 10, 0], [10, 10, 0], [10, 0, 0]]
    vertices_roof = [[10, 0, 3], [10, 10, 3], [0, 10, 3], [0, 0, 3]]

    wf = Face.from_vertices('wall', vertices_wall)
    assert wf.properties.energy.construction.identifier == 'Generic Exterior Wall'
    rf = Face.from_vertices('roof', vertices_roof)
    assert rf.properties.energy.construction.identifier == 'Generic Roof'
    ff = Face.from_vertices('floor', vertices_floor)
    assert ff.properties.energy.construction.identifier == 'Generic Ground Slab'


def test_set_construction():
    """Test the setting of a construction on a Face."""
    face = Face.from_vertices(
        'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction(
        'Thick Concrete Construction', [concrete20])
    face.properties.energy.construction = thick_constr

    assert face.properties.energy.construction == thick_constr
    assert face.properties.energy.is_construction_set_on_object

    with pytest.raises(AttributeError):
        face.properties.energy.construction[0].thickness = 0.1


def test_duplicate():
    """Test what happens to energy properties when duplicating a Face."""
    verts = [Point3D(0, 0, 0), Point3D(10, 0, 0), Point3D(10, 0, 10), Point3D(0, 0, 10)]
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction(
        'Thick Concrete Construction', [concrete20])

    face_original = Face('wall_face', Face3D(verts))
    face_original.properties.energy.vent_crack = AFNCrack(0.00001, 0.65)
    face_dup_1 = face_original.duplicate()

    assert face_original.properties.energy.host is face_original
    assert face_dup_1.properties.energy.host is face_dup_1
    assert face_original.properties.energy.host is not face_dup_1.properties.energy.host

    assert face_original.properties.energy.construction == \
        face_dup_1.properties.energy.construction
    assert face_original.properties.energy.vent_crack == \
        face_dup_1.properties.energy.vent_crack
    face_dup_1.properties.energy.construction = thick_constr
    face_dup_1.properties.energy.vent_crack = AFNCrack(0.001, 0.7)
    assert face_original.properties.energy.construction != \
        face_dup_1.properties.energy.construction
    assert face_original.properties.energy.vent_crack != \
        face_dup_1.properties.energy.vent_crack

    face_dup_2 = face_dup_1.duplicate()

    assert face_dup_1.properties.energy.construction == \
        face_dup_2.properties.energy.construction
    face_dup_2.properties.energy.construction = None
    face_dup_2.properties.energy.vent_crack = None
    assert face_dup_1.properties.energy.construction != \
        face_dup_2.properties.energy.construction
    assert face_dup_1.properties.energy.vent_crack != \
        face_dup_2.properties.energy.vent_crack


def test_to_dict():
    """Test the Face to_dict method with energy properties."""
    face = Face.from_vertices(
        'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])

    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction(
        'Thick Concrete Construction', [concrete20])

    fd = face.to_dict()
    assert 'properties' in fd
    assert fd['properties']['type'] == 'FaceProperties'
    assert 'energy' in fd['properties']
    assert fd['properties']['energy']['type'] == 'FaceEnergyProperties'
    assert 'vent_crack' not in fd['properties']['energy']

    face.properties.energy.construction = thick_constr
    face.properties.energy.vent_crack = AFNCrack(1e-5, 0.65)
    fd = face.to_dict()
    assert 'construction' in fd['properties']['energy']
    assert fd['properties']['energy']['construction'] is not None
    assert AFNCrack.from_dict(fd['properties']['energy']['vent_crack']) == \
        face.properties.energy.vent_crack


def test_from_dict():
    """Test the Face from_dict method with energy properties."""
    face = Face.from_vertices(
        'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])

    ref_crack = AFNCrack(1e-5, 0.65)
    face.properties.energy.vent_crack = ref_crack

    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction('Thick Concrete Construction', [concrete20])
    face.properties.energy.construction = thick_constr

    fd = face.to_dict()
    new_face = Face.from_dict(fd)
    assert new_face.properties.energy.construction == thick_constr
    assert new_face.properties.energy.vent_crack == ref_crack
    assert new_face.to_dict() == fd


def test_writer_to_idf():
    """Test the Face to_idf method."""
    face = Face.from_vertices(
        'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])
    assert hasattr(face.to, 'idf')
    idf_string = face.to.idf(face)
    assert 'wall_face,' in idf_string
    assert 'BuildingSurface:Detailed,' in idf_string


def test_adiabatic_bc():
    """Test the adiabatic boundary condition."""
    assert hasattr(boundary_conditions, 'adiabatic')
    ad_1 = boundary_conditions.adiabatic
    ad_2 = boundary_conditions.adiabatic

    assert ad_1.name == 'Adiabatic'
    assert ad_1 is ad_2

    verts = [Point3D(0, 0, 0), Point3D(10, 0, 0), Point3D(10, 0, 10), Point3D(0, 0, 10)]
    face = Face('wall_face', Face3D(verts),
                boundary_condition=boundary_conditions.adiabatic)
    assert face.properties.energy.construction.identifier == 'Generic Interior Wall'
