from honeybee_energy.boundarycondition import Adiabatic


def test_adiabatic():
    bc = Adiabatic()
    assert bc.name == 'Adiabatic'
    assert bc.sun_exposure_idf == 'NoSun'
    assert bc.wind_exposure_idf == 'NoWind'
    assert bc.view_factor == 'autocalculate'


def test_adiabatic_to_dict():
    bc = Adiabatic()
    outdict = bc.to_dict()
    assert outdict['type'] == 'Adiabatic'
    assert 'sun_exposure' not in outdict
    assert 'wind_exposure' not in outdict
    assert 'view_factor' not in outdict
