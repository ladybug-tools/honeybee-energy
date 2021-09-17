# coding=utf-8
from honeybee_energy.material.gas import EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_gas_init(userdatadict):
    """Test the initalization of gas material objects and basic properties."""
    air = EnergyWindowMaterialGas('Air Gap', 0.0125, 'Air')
    air.user_data = userdatadict
    str(air)  # test the string representation of the material
    air_dup = air.duplicate()

    assert air.identifier == air_dup.identifier == 'Air Gap'
    assert air.thickness == air_dup.thickness == 0.0125
    assert air.gas_type == air_dup.gas_type == 'Air'
    assert air.conductivity == air_dup.conductivity == pytest.approx(0.024069, rel=1e-2)
    assert air.viscosity == air_dup.viscosity == pytest.approx(1.73775e-05, rel=1e-2)
    assert air.specific_heat == air_dup.specific_heat == pytest.approx(1006.1033, rel=1e-2)
    assert air.density == air_dup.density == pytest.approx(1.292, rel=1e-2)
    assert air.prandtl == air_dup.prandtl == pytest.approx(0.7263, rel=1e-2)
    assert air.user_data == userdatadict

def test_gas_defaults():
    """Test the EnergyWindowMaterialGas default properties."""
    air = EnergyWindowMaterialGas('Default Gap')

    assert air.thickness == 0.0125
    assert air.gas_type == 'Air'


def test_gas_properties_at_temperature():
    """Test the initalization of gas material objects and basic properties."""
    air = EnergyWindowMaterialGas('Air Gap', 0.0125, 'Air')

    assert air.conductivity_at_temperature(223) == pytest.approx(0.020177, rel=1e-2)
    assert air.viscosity_at_temperature(223) == pytest.approx(1.487e-05, rel=1e-2)
    assert air.specific_heat_at_temperature(223) == pytest.approx(1005.48, rel=1e-2)
    assert air.density_at_temperature(223) == pytest.approx(1.5832, rel=1e-2)
    assert air.prandtl_at_temperature(223) == pytest.approx(0.74099, rel=1e-2)


def test_gas_invalid():
    """Test EnergyWindowMaterialGlazing objects with invalid properties."""
    air = EnergyWindowMaterialGas('Air Gap', 0.0125, 'Air')

    with pytest.raises(TypeError):
        air.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        air.thickness = -1
    with pytest.raises(AssertionError):
        air.gas_type = 'Helium'


def test_gas_init_from_idf():
    """Test the initialization of gas mixture objects from strings."""
    ep_str_1 = "WindowMaterial:Gas,\n" \
        "Gap_1_W_0_0127,            !- Name\n" \
        "Air,                       !- Gas Type\n" \
        "0.05;                      !- Thickness"
    air = EnergyWindowMaterialGas.from_idf(ep_str_1)

    assert air.identifier == 'Gap_1_W_0_0127'
    assert air.thickness == 0.05
    assert air.gas_type == 'Air'


def test_gas_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    argon = EnergyWindowMaterialGas('Argon Gap', 0.0125, 'Argon')
    argon.user_data = userdatadict
    material_dict = argon.to_dict()
    new_material = EnergyWindowMaterialGas.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
    assert argon.user_data == new_material.user_data


def test_gas_mixture_init(userdatadict):
    """Test the initialization of a gas mixture."""
    air_argon = EnergyWindowMaterialGasMixture(
        'Air Argon Gap', 0.0125, ('Air', 'Argon'), (0.1, 0.9))
    air_argon.user_data = userdatadict
    str(air_argon)  # test the string representation of the material
    aa_dup = air_argon.duplicate()

    assert air_argon.identifier == aa_dup.identifier == 'Air Argon Gap'
    assert air_argon.thickness == aa_dup.thickness == 0.0125
    assert air_argon.gas_types == aa_dup.gas_types == ('Air', 'Argon')
    assert air_argon.gas_fractions == aa_dup.gas_fractions == (0.1, 0.9)
    assert air_argon.conductivity == aa_dup.conductivity == pytest.approx(0.0171, rel=1e-2)
    assert air_argon.viscosity == aa_dup.viscosity == pytest.approx(1.953e-05, rel=1e-2)
    assert air_argon.specific_heat == aa_dup.specific_heat == pytest.approx(570.346, rel=1e-2)
    assert air_argon.density == aa_dup.density == pytest.approx(1.733399, rel=1e-2)
    assert air_argon.prandtl == aa_dup.prandtl == pytest.approx(0.65057, rel=1e-2)


def test_gas_mixture_defaults():
    """Test the EnergyWindowMaterialGasMixture default properties."""
    air_argon = EnergyWindowMaterialGasMixture('Default Gap')

    assert air_argon.thickness == 0.0125
    assert air_argon.gas_types == ('Argon', 'Air')
    assert air_argon.gas_fractions == (0.9, 0.1)


def test_gas_mixture_properties_at_temperature():
    """Test the initalization of gas material objects and basic properties."""
    air_argon = EnergyWindowMaterialGasMixture(
        'Air Argon Gap', 0.0125, ('Air', 'Argon'), (0.1, 0.9))

    assert air_argon.conductivity_at_temperature(223) == pytest.approx(0.0144, rel=1e-2)
    assert air_argon.viscosity_at_temperature(223) == pytest.approx(1.6571e-05, rel=1e-2)
    assert air_argon.specific_heat_at_temperature(223) == pytest.approx(570.284, rel=1e-2)
    assert air_argon.density_at_temperature(223) == pytest.approx(2.12321, rel=1e-2)
    assert air_argon.prandtl_at_temperature(223) == pytest.approx(0.6558, rel=1e-2)


def test_gas_mixture_invalid():
    """Test EnergyWindowMaterialGlazing objects with invalid properties."""
    air_argon = EnergyWindowMaterialGasMixture(
        'Air Argon Gap', 0.0125, ('Air', 'Argon'), (0.1, 0.9))

    with pytest.raises(TypeError):
        air_argon.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        air_argon.thickness = -1
    with pytest.raises(AssertionError):
        air_argon.gas_types = ('Helium', 'Nitrogen')
    with pytest.raises(AssertionError):
        air_argon.gas_fractions = (0.5, 0.7)


def test_gas_mixture_init_from_idf():
    """Test the initialization of gas mixture objects from strings."""
    ep_str_1 = "WindowMaterial:GasMixture,\n" \
        "Argon Mixture,            !- Name\n" \
        "0.01,                     !- Thickness {m}\n" \
        "2,                        !- Number of Gases\n" \
        "Argon,                    !- Gas 1 Type\n" \
        "0.8,                      !- Gas 1 Fraction\n" \
        "Air,                      !- Gas 2 Type\n" \
        "0.2;                      !- Gas 2 Fraction"
    gas_mix = EnergyWindowMaterialGasMixture.from_idf(ep_str_1)

    assert gas_mix.identifier == 'Argon Mixture'
    assert gas_mix.thickness == 0.01
    assert gas_mix.gas_types == ('Argon', 'Air')
    assert gas_mix.gas_fractions == (0.8, 0.2)


def test_gas_mixture_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    air_xenon = EnergyWindowMaterialGasMixture(
        'Air Xenon Gap', 0.0125, ('Air', 'Xenon'), (0.1, 0.9))
    air_xenon.user_data = userdatadict
    material_dict = air_xenon.to_dict()
    new_material = EnergyWindowMaterialGasMixture.from_dict(material_dict)
    assert material_dict == new_material.to_dict()


def test_gas_custom_init(userdatadict):
    """Test the initialization of a custom gas."""
    co2_gap = EnergyWindowMaterialGasCustom('CO2', 0.0125, 0.0146, 0.000014, 827.73)
    co2_gap.specific_heat_ratio = 1.4
    co2_gap.molecular_weight = 44
    co2_gap.user_data = userdatadict
    str(co2_gap)  # test the string representation of the material
    co2_dup = co2_gap.duplicate()

    assert co2_gap.identifier == co2_dup.identifier == 'CO2'
    assert co2_gap.thickness == co2_dup.thickness == 0.0125
    assert co2_gap.conductivity == co2_dup.conductivity == pytest.approx(0.0146, rel=1e-2)
    assert co2_gap.viscosity == co2_dup.viscosity == pytest.approx(0.000014, rel=1e-2)
    assert co2_gap.specific_heat == co2_dup.specific_heat == pytest.approx(827.73, rel=1e-2)
    assert co2_gap.density == co2_dup.density == pytest.approx(1.9631, rel=1e-2)
    assert co2_gap.prandtl == co2_dup.prandtl == pytest.approx(0.7937, rel=1e-2)

    assert co2_gap.conductivity_coeff_b == 0
    assert co2_gap.conductivity_coeff_c == 0
    assert co2_gap.viscosity_coeff_b == 0
    assert co2_gap.viscosity_coeff_c == 0
    assert co2_gap.specific_heat_coeff_b == 0
    assert co2_gap.specific_heat_coeff_c == 0
    assert co2_gap.specific_heat_ratio == 1.4
    assert co2_gap.molecular_weight == 44


def test_gas_custom_properties_at_temperature():
    """Test the initalization of gas material objects and basic properties."""
    co2_gap = EnergyWindowMaterialGasCustom('CO2', 0.0125, 0.0146, 0.000014, 827.73)
    co2_gap.specific_heat_ratio = 1.4
    co2_gap.molecular_weight = 44

    assert co2_gap.conductivity_at_temperature(223) == pytest.approx(0.0146, rel=1e-2)
    assert co2_gap.viscosity_at_temperature(223) == pytest.approx(1.4e-05, rel=1e-2)
    assert co2_gap.specific_heat_at_temperature(223) == pytest.approx(827.73, rel=1e-2)
    assert co2_gap.density_at_temperature(223) == pytest.approx(2.40466, rel=1e-2)
    assert co2_gap.prandtl_at_temperature(223) == pytest.approx(0.7937, rel=1e-2)


def test_gas_custom_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    co2_gap = EnergyWindowMaterialGasCustom('CO2', 0.0125, 0.0146, 0.000014, 827.73)
    co2_gap.specific_heat_ratio = 1.4
    co2_gap.molecular_weight = 44
    co2_gap.user_data = userdatadict
    material_dict = co2_gap.to_dict()
    new_material = EnergyWindowMaterialGasCustom.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
    assert co2_gap.user_data == new_material.user_data
