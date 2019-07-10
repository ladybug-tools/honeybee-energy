from honeybee_energy.boundarycondition import Adiabatic


def test_adiabatic():
    bc = Adiabatic()
    assert bc.name == 'Adiabatic'
    assert not bc.sun_exposure
    assert bc.sun_exposure_idf == 'NoSun'
    assert not bc.wind_exposure
    assert bc.wind_exposure_idf == 'NoWind'


def test_adiabatic_to_dict():
    bc = Adiabatic()
    outdict = bc.to_dict(full=True)
    assert outdict['type'] == 'Adiabatic'
    assert outdict['sun_exposure'] == 'NoSun'
    assert outdict['wind_exposure'] == 'NoWind'
    assert outdict['view_factor'] == 'autocalculate'
    outdict = bc.to_dict(full=False)
    assert 'sun_exposure' not in outdict
    assert 'wind_exposure' not in outdict
    assert 'view_factor' not in outdict
