import pytest
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.construction.window import WindowConstruction

@pytest.mark.parametrize('resistances', [[1, 2, 3], [0.1, 0.003, 0.13], [1, 2, 3, 4, 5]])
def test_layer_source_heat_conservation_and_split(resistances):
    construction = WindowConstruction('glass', [EnergyWindowMaterialGlazing('glass')])
    sources = [0] * len(resistances)
    sources[1] = 12
    temperatures = construction._temperature_profile_from_r_values(resistances, 0, 0, sources)
    outward = temperatures[1] / resistances[0]
    inward = temperatures[-2] / resistances[-1]
    assert outward + inward == pytest.approx(12)
    assert inward == pytest.approx(12 * (resistances[0] + resistances[1] / 2) / sum(resistances))
