import pytest
from honeybee_energy.material.gas import EnergyWindowMaterialGas

@pytest.mark.parametrize('height', [0.5, 1.0, 2.0])
@pytest.mark.parametrize('angle', [60, 65, 75, 89.9])
def test_tilt_interpolates_with_height_over_gap(height, angle):
    gas = EnergyWindowMaterialGas('air', 0.0127)
    ra = gas.rayleigh(15)
    g = 0.5 / (1 + (ra / 3160) ** 20.6) ** 0.1
    nu60 = max((1 + (0.0936 * ra ** 0.314 / (1 + g)) ** 7) ** (1 / 7),
               (0.104 + 0.175 * gas.thickness / height) * ra ** 0.283)
    nu90 = gas.nusselt(15, height)
    expected = nu60 + (nu90 - nu60) * (angle - 60) / 30
    assert gas.nusselt_at_angle(15, height, angle) == pytest.approx(expected)

def test_tilt_continuous_at_vertical():
    gas = EnergyWindowMaterialGas('air', 0.0127)
    assert gas.nusselt_at_angle(angle=89.999999) == pytest.approx(gas.nusselt(), rel=1e-7)
