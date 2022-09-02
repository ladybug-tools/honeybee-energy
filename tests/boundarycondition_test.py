from honeybee.altnumber import autocalculate

from honeybee_energy.boundarycondition import Adiabatic, OtherSideTemperature


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


def test_other_side_temperature():
    bc = OtherSideTemperature()
    assert bc.name == 'OtherSideTemperature'
    assert bc.temperature == autocalculate
    assert bc.heat_transfer_coefficient == 0
    assert bc.sun_exposure_idf == 'NoSun'
    assert bc.wind_exposure_idf == 'NoWind'
    assert bc.view_factor == 'autocalculate'

    bc = OtherSideTemperature(20, 0.25)
    assert bc.name == 'OtherSideTemperature'
    assert bc.temperature == 20
    assert bc.heat_transfer_coefficient == 0.25


def test_other_side_temperature_to_from_dict():
    bc = OtherSideTemperature(20, 0.25)
    outdict = bc.to_dict()
    assert outdict['type'] == 'OtherSideTemperature'
    new_bc = OtherSideTemperature.from_dict(outdict)
    assert new_bc.to_dict() == outdict


def test_other_side_temperature_to_idf():
    bc = OtherSideTemperature(20, 0.25)
    assert isinstance(bc.to_idf('test_bc'), str)
