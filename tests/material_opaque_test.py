# coding=utf-8
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_material_init(userdatadict):
    """Test the initialization of EnergyMaterial objects and basic properties."""
    concrete = EnergyMaterial('Concrete', 0.2, 0.5, 800, 1200,
                              'MediumSmooth', 0.95, 0.75, 0.8)
    concrete.user_data = userdatadict
    str(concrete)  # test the string representation of the material
    concrete_dup = concrete.duplicate()

    assert concrete.identifier == concrete_dup.identifier == 'Concrete'
    assert concrete.thickness == concrete_dup.thickness == 0.2
    assert concrete.conductivity == concrete_dup.conductivity == 0.5
    assert concrete.density == concrete_dup.density == 800
    assert concrete.specific_heat == concrete_dup.specific_heat == 1200
    assert concrete.roughness == concrete_dup.roughness == 'MediumSmooth'
    assert concrete.thermal_absorptance == concrete_dup.thermal_absorptance == 0.95
    assert concrete.solar_absorptance == concrete_dup.solar_absorptance == 0.75
    assert concrete.visible_absorptance == concrete_dup.visible_absorptance == 0.8

    assert concrete.resistivity == 1 / 0.5
    assert concrete.u_value == pytest.approx(2.5, rel=1e-2)
    assert concrete.r_value == pytest.approx(0.4, rel=1e-2)
    assert concrete.mass_area_density == pytest.approx(160, rel=1e-2)
    assert concrete.area_heat_capacity == pytest.approx(192000, rel=1e-2)

    concrete.r_value = 0.5
    assert concrete.conductivity != concrete_dup.conductivity
    assert concrete.r_value == 0.5
    assert concrete.conductivity == pytest.approx(0.4, rel=1e-2)
    assert concrete.user_data == userdatadict

    with pytest.raises(ValueError):
        concrete.thickness = 0
    with pytest.raises(AssertionError):
        concrete.thickness = 0.000000001
    


def test_material_equivalency(userdatadict):
    """Test the equality of a material to another EnergyMaterial."""
    concrete_1 = EnergyMaterial('Concrete [HW]', 0.2, 0.5, 800, 1200)
    concrete_1.user_data = userdatadict
    concrete_2 = concrete_1.duplicate()
    insulation = EnergyMaterial('Insulation', 0.05, 0.049, 265, 836)

    assert concrete_1 == concrete_2
    assert concrete_1 != insulation
    collection = [concrete_1, concrete_2, insulation]
    assert len(set(collection)) == 2

    concrete_2.density = 600
    assert concrete_1 != concrete_2
    assert len(set(collection)) == 3


def test_material_lockability(userdatadict):
    """Test the lockability of the EnergyMaterial."""
    concrete = EnergyMaterial('Concrete [HW]', 0.2, 0.5, 800, 1200)
    concrete.density = 600
    concrete.user_data = userdatadict
    concrete.lock()
    with pytest.raises(AttributeError):
        concrete.density = 700
    concrete.unlock()
    concrete.density = 700


def test_material_defaults():
    """Test the EnergyMaterial default properties."""
    concrete = EnergyMaterial('Concrete [HW]', 0.2, 0.5, 800, 1200)

    assert concrete.identifier == 'Concrete [HW]'
    assert concrete.roughness == 'MediumRough'
    assert concrete.thermal_absorptance == 0.9
    assert concrete.solar_absorptance == concrete.visible_absorptance == 0.7


def test_material_invalid():
    """Test the initialization of EnergyMaterial objects with invalid properties."""
    concrete = EnergyMaterial('Concrete', 0.2, 0.5, 800, 1200)

    with pytest.raises(TypeError):
        concrete.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        concrete.thickness = -1
    with pytest.raises(AssertionError):
        concrete.conductivity = -1
    with pytest.raises(AssertionError):
        concrete.density = -1
    with pytest.raises(AssertionError):
        concrete.specific_heat = -1
    with pytest.raises(AssertionError):
        concrete.roughness = 'Medium'
    with pytest.raises(AssertionError):
        concrete.thermal_absorptance = 2
    with pytest.raises(AssertionError):
        concrete.solar_absorptance = 2
    with pytest.raises(AssertionError):
        concrete.visible_absorptance = 2

    with pytest.raises(AssertionError):
        concrete.resistivity = -1
    with pytest.raises(AssertionError):
        concrete.u_value = -1
    with pytest.raises(AssertionError):
        concrete.r_value = -1


def test_material_to_from_idf():
    """Test the initialization of EnergyMaterial objects from EnergyPlus strings."""
    ep_str_1 = "Material,\n" \
        " M01 100mm brick,                    !- Name\n" \
        " MediumRough,                            !- Roughness\n" \
        " 0.1016,                                 !- Thickness {m}\n" \
        " 0.89,                                   !- Conductivity {W/m-K}\n" \
        " 1920,                                   !- Density {kg/m3}\n" \
        " 790,                                    !- Specific Heat {J/kg-K}\n" \
        " 0.9,                                    !- Thermal Absorptance\n" \
        " 0.7,                                    !- Solar Absorptance\n" \
        " 0.7;                                    !- Visible Absorptance"
    mat_1 = EnergyMaterial.from_idf(ep_str_1)

    ep_str_2 = "Material, M01 100mm brick, MediumRough, " \
        "0.1016, 0.89, 1920, 790, 0.9, 0.7, 0.7;"
    mat_2 = EnergyMaterial.from_idf(ep_str_2)

    ep_str_3 = "Material, M01 100mm brick, MediumRough, " \
        "0.1016, 0.89, 1920, 790;"
    mat_3 = EnergyMaterial.from_idf(ep_str_3)

    assert mat_1.identifier == mat_2.identifier == mat_3.identifier

    idf_str = mat_1.to_idf()
    new_mat_1 = EnergyMaterial.from_idf(idf_str)
    assert idf_str == new_mat_1.to_idf()


def test_material_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    material = EnergyMaterial('Concrete', 0.2, 0.5, 800, 1200)
    material.user_data = userdatadict
    material_dict = material.to_dict()
    new_material = EnergyMaterial.from_dict(material_dict)
    assert material_dict == new_material.to_dict()


def test_material_nomass_init(userdatadict):
    """Test the initialization of EnergyMaterialNoMass and basic properties."""
    insul_r2 = EnergyMaterialNoMass('Insulation R-2', 2,
                                    'MediumSmooth', 0.95, 0.75, 0.8)
    insul_r2.user_data = userdatadict
    str(insul_r2)  # test the string representation of the material
    insul_r2_dup = insul_r2.duplicate()

    assert insul_r2.identifier == insul_r2_dup.identifier == 'Insulation R-2'
    assert insul_r2.r_value == insul_r2_dup.r_value == 2
    assert insul_r2.roughness == insul_r2_dup.roughness == 'MediumSmooth'
    assert insul_r2.thermal_absorptance == insul_r2_dup.thermal_absorptance == 0.95
    assert insul_r2.solar_absorptance == insul_r2_dup.solar_absorptance == 0.75
    assert insul_r2.visible_absorptance == insul_r2_dup.visible_absorptance == 0.8

    assert insul_r2.u_value == pytest.approx(0.5, rel=1e-2)
    assert insul_r2.r_value == pytest.approx(2, rel=1e-2)

    insul_r2.r_value = 3
    assert insul_r2.r_value == 3


def test_material_nomass_defaults():
    """Test the EnergyMaterialNoMass default properties."""
    insul_r2 = EnergyMaterialNoMass('Insulation [R-2]', 2)

    assert insul_r2.identifier == 'Insulation [R-2]'
    assert insul_r2.roughness == 'MediumRough'
    assert insul_r2.thermal_absorptance == 0.9
    assert insul_r2.solar_absorptance == insul_r2.visible_absorptance == 0.7


def test_material_nomass_invalid():
    """Test the initialization of EnergyMaterial objects with invalid properties."""
    insul_r2 = EnergyMaterialNoMass('Insulation [R-2]', 2)

    with pytest.raises(TypeError):
        insul_r2.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        insul_r2.r_value = -1
    with pytest.raises(AssertionError):
        insul_r2.roughness = 'Medium'
    with pytest.raises(AssertionError):
        insul_r2.thermal_absorptance = 2
    with pytest.raises(AssertionError):
        insul_r2.solar_absorptance = 2
    with pytest.raises(AssertionError):
        insul_r2.visible_absorptance = 2
    with pytest.raises(AssertionError):
        insul_r2.u_value = -1


def test_material_nomass_init_from_idf():
    """Test the initialization of EnergyMaterialNoMass objects from strings."""
    ep_str_1 = "Material:NoMass,\n" \
        "CP02 CARPET PAD,                        !- Name\n" \
        "Smooth,                                 !- Roughness\n" \
        "0.1,                                    !- Thermal Resistance {m2-K/W}\n" \
        "0.9,                                    !- Thermal Absorptance\n" \
        "0.8,                                    !- Solar Absorptance\n" \
        "0.8;                                    !- Visible Absorptance"
    mat_1 = EnergyMaterialNoMass.from_idf(ep_str_1)

    idf_str = mat_1.to_idf()
    new_mat_1 = EnergyMaterialNoMass.from_idf(idf_str)
    assert idf_str == new_mat_1.to_idf()


def test_material_nomass_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    material = EnergyMaterialNoMass('Insulation R-2', 2)
    material.user_data = userdatadict
    material_dict = material.to_dict()
    new_material = EnergyMaterialNoMass.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
