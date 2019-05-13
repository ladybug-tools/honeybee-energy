from honeybee_energy.boundarycondition import BoundaryConditions

bcs = BoundaryConditions()

def test_outdoors():
    bc = bcs.outdoors
    assert bc.name == 'Outdoors'
    assert bc.sun_exposure == True
    assert bc.sun_exposure_idf == 'SunExposed'
    assert bc.wind_exposure == True
    assert bc.wind_exposure_idf == 'WindExposed'
    assert bc.boundary_condition_object == None
    assert bc.boundary_condition_object_idf == ''

def test_outdoors_to_dict():
    bc = bcs.outdoors
    outdict = bc.to_dict
    assert outdict['boundary_condition'] == 'Outdoors'
    assert outdict['boundary_condition_object'] == ''
    assert outdict['sun_exposure'] == 'SunExposed'
    assert outdict['wind_exposure'] == 'WindExposed'
    assert outdict['view_factor'] == 'autocalculate'


