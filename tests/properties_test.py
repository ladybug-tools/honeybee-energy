from honeybee_energy.properties import EnergyProperties
from honeybee_energy.lib.constructionset import generic
from honeybee.facetype import face_types
from honeybee.boundarycondition import boundary_conditions


def test_defaults():
    ep = EnergyProperties(face_types.wall, boundary_conditions.outdoors)
    assert ep.construction == None
    assert ep._boundary_condition.name == 'Outdoors'


def test_to_dict():
    ep = EnergyProperties(face_types.wall, boundary_conditions.outdoors)
    ep_dict = ep.to_dict()
    assert 'energy' in ep_dict
    assert 'construction' in ep_dict['energy']
