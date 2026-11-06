import pytest
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.frame import EnergyWindowFrame
from honeybee_energy.construction.window import WindowConstruction

@pytest.mark.parametrize('width', [0.01, 0.05, 0.1])
@pytest.mark.parametrize('prop', ['r_value', 'r_factor', 'r_factor_summer', 'shgc'])
def test_frame_surrounds_unit_square_on_all_sides(width, prop):
    glass = EnergyWindowMaterialGlazing('glass')
    frame = EnergyWindowFrame('frame', width, 3.5)
    bare = WindowConstruction('bare', [glass])
    framed = WindowConstruction('framed', [glass], frame)
    area = (1 + 2 * width) ** 2 - 1
    if prop == 'shgc':
        irr = 783
        _, resistances = framed.temperature_profile_frame(32, 24, solar_irradiance=irr)
        frame_gain = frame.solar_absorptance * (1 - resistances[-1] / sum(resistances))
        expected = (bare.shgc + frame_gain * area) / (1 + area)
    else:
        films = 0 if prop == 'r_value' else (1 / bare.in_h_simple() +
                 1 / (bare.out_h(wind_speed=2.75, t_kelvin=301.15)
                      if prop == 'r_factor_summer' else bare.out_h_simple()))
        expected = (1 + area) / (1 / getattr(bare, prop) + area / (frame.r_value + films))
    assert getattr(framed, prop) == pytest.approx(expected)
