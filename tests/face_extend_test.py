"""Tests for features add to honeybee by honeybee_energy."""
from honeybee.face import Face
from honeybee.facetype import Wall
from honeybee_energy.properties import EnergyProperties
from honeybee.boundarycondition import boundary_conditions


face = Face.from_vertices(
    'wall_face', [[0, 0, 0], [10, 0, 0], [10, 0, 10], [0, 0, 10]])


def test_energy_properties():
    assert hasattr(face.properties, 'energy')
    assert isinstance(face.properties.energy, EnergyProperties)
    assert face.properties.energy.construction == None


def test_writer_to_idf():
    assert hasattr(face.to, 'energy')
    idf_string = face.to.energy(face)
    assert 'wall_face,' in idf_string
    assert 'BuildingSurface:Detailed,' in idf_string


def test_adiabatic_bc():

    assert hasattr(boundary_conditions, 'adiabatic')
    ad_1 = boundary_conditions.adiabatic
    ad_2 = boundary_conditions.adiabatic

    assert ad_1.name == 'Adiabatic'
    assert ad_1 is ad_2


def test_zone_bc():
    assert hasattr(boundary_conditions, 'zone')
    z = boundary_conditions.zone
    assert z.name == 'Zone'
