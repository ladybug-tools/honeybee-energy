from honeybee_energy.properties import EnergyProperties
from honeybee.facetype import Wall


def test_defaults():
    ep = EnergyProperties(Wall())
    assert ep.construction.name == 'generic_wall'
    assert ep.boundary_condition.name == 'Outdoors'

def test_to_dict():
    ep = EnergyProperties(Wall())
    ep_dict = ep.to_dict
    assert 'energy' in ep_dict
    assert 'construction' in ep_dict['energy']
    assert ep_dict['energy']['boundary_condition'] == 'Outdoors'
    assert ep_dict['energy']['boundary_condition_object'] == ''
    assert ep_dict['energy']['sun_exposure'] == 'SunExposed'
    assert ep_dict['energy']['wind_exposure'] == 'WindExposed'
    assert ep_dict['energy']['view_factor'] == 'autocalculate'


