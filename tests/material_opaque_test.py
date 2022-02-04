# coding=utf-8
from honeybee_energy.material.opaque import EnergyMaterial, EnergyMaterialNoMass, \
    EnergyMaterialVegetation

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


def test_greenroof_init(userdatadict):
    """Test initialization of EnergyMaterialVegetation Object and basic properties"""
    g_roof = EnergyMaterialVegetation(
        'tall grass', 0.5, 0.45, 1250, 950, 'Rough',
        0.89, 0.65, 0.7, 0.5, 2, 0.35, 0.9, 275)
    g_roof.user_data = userdatadict
    str(g_roof)
    g_roof_dup = g_roof.duplicate()

    assert g_roof.identifier == g_roof_dup.identifier == 'tall grass'
    assert g_roof.thickness == g_roof_dup.thickness == 0.5
    assert g_roof.conductivity == g_roof_dup.conductivity == 0.45
    assert g_roof.density == g_roof_dup.density == 1250
    assert g_roof.specific_heat == g_roof_dup.specific_heat == 950
    assert g_roof.roughness == g_roof_dup.roughness == 'Rough'
    assert g_roof.soil_thermal_absorptance == g_roof_dup.soil_thermal_absorptance == 0.89
    assert g_roof.soil_solar_absorptance == g_roof_dup.soil_solar_absorptance == 0.65
    assert g_roof.soil_visible_absorptance == g_roof_dup.soil_visible_absorptance == 0.7
    assert g_roof.plant_height == g_roof_dup.plant_height == 0.5
    assert g_roof.leaf_area_index == g_roof_dup.leaf_area_index == 2
    assert g_roof.leaf_reflectivity == g_roof_dup.leaf_reflectivity == 0.35
    assert g_roof.leaf_emissivity == g_roof_dup.leaf_emissivity == 0.9
    assert g_roof.min_stomatal_resist == g_roof_dup.min_stomatal_resist == 275

    assert g_roof.sat_vol_moist_cont == g_roof_dup.sat_vol_moist_cont == 0.3
    assert g_roof.residual_vol_moist_cont == g_roof_dup.residual_vol_moist_cont == 0.01
    assert g_roof.init_vol_moist_cont == g_roof_dup.init_vol_moist_cont == 0.1
    assert g_roof.moist_diff_model == g_roof_dup.moist_diff_model == 'Simple'
    assert g_roof.user_data == g_roof_dup.user_data == userdatadict


def test_greenroof_equivalency(userdatadict):
    """Test the equality of a material to another EnergyMaterial."""
    g_roof1 = EnergyMaterialVegetation(
        'tall grass', 0.5, 0.45, 1250, 950, 'Rough',
        0.89, 0.65, 0.7, 0.5, 2, 0.35, 0.9, 275)
    g_roof1.user_data = userdatadict
    g_roof2 = g_roof1.duplicate()
    insulation = EnergyMaterial('Insulation', 0.05, 0.049, 265, 836)

    assert g_roof1 == g_roof2
    assert g_roof1 != insulation
    collection = [g_roof1, g_roof2, insulation]
    assert len(set(collection)) == 2

    g_roof2.plant_height = 0.25
    assert g_roof1 != g_roof2
    assert len(set(collection)) == 3


def test_greenroof_lockability(userdatadict):
    """Test the lockability of the EnergyMaterial."""
    g_roof = EnergyMaterialVegetation(
        'tall grass', 0.5, 0.45, 1250, 950, 'Rough',
        0.89, 0.65, 0.7, 0.5, 2, 0.35, 0.9, 275)
    g_roof.density = 1100
    g_roof.user_data = userdatadict
    g_roof.lock()
    with pytest.raises(AttributeError):
        g_roof.density = 1234
    g_roof.unlock()
    g_roof.density = 1234


def test_greenroof_defaults():
    """Test the EnergyMaterialVegetation default properties."""
    g_roof = EnergyMaterialVegetation('myroof')

    assert g_roof.thickness == 0.1
    assert g_roof.conductivity == 0.35
    assert g_roof.density == 1100.0
    assert g_roof.specific_heat == 1200.0
    assert g_roof.roughness == 'MediumRough'
    assert g_roof.soil_thermal_absorptance == 0.9
    assert g_roof.soil_solar_absorptance == 0.7
    assert g_roof.soil_visible_absorptance == 0.7
    assert g_roof.plant_height == 0.2
    assert g_roof.leaf_area_index == 1.0
    assert g_roof.leaf_reflectivity == 0.22
    assert g_roof.leaf_emissivity == 0.95
    assert g_roof.min_stomatal_resist == 180.0
    assert g_roof.sat_vol_moist_cont == 0.3
    assert g_roof.residual_vol_moist_cont == 0.01
    assert g_roof.init_vol_moist_cont == 0.1
    assert g_roof.moist_diff_model == 'Simple'


def test_greenroof_invalid():
    """Test the initialization of EnergyMaterialVegetation with invalid properties."""
    g_roof = EnergyMaterialVegetation(
        'roofmcroofface', 0.5, 0.45, 1250, 950, 'Rough',
        0.89, 0.65, 0.7, 0.5, 2, 0.35, 0.9, 275)

    with pytest.raises(TypeError):
        g_roof.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        g_roof.thickness = -1
    with pytest.raises(AssertionError):
        g_roof.roughness = 'Shmedium'
    with pytest.raises(AssertionError):
        g_roof.conductivity = -3.25
    with pytest.raises(AssertionError):
        g_roof.density = -15
    with pytest.raises(AssertionError):
        g_roof.specific_heat = 25
    with pytest.raises(AssertionError):
        g_roof.soil_thermal_absorptance = 5
    with pytest.raises(AssertionError):
        g_roof.soil_solar_absorptance = 5
    with pytest.raises(AssertionError):
        g_roof.soil_visible_absorptance = 12.53
    with pytest.raises(AssertionError):
        g_roof.plant_height = 0.0001
    with pytest.raises(AssertionError):
        g_roof.leaf_area_index = 10
    with pytest.raises(AssertionError):
        g_roof.leaf_reflectivity = 1
    with pytest.raises(AssertionError):
        g_roof.leaf_emissivity = 0.1
    with pytest.raises(AssertionError):
        g_roof.min_stomatal_resist = 10
    with pytest.raises(AssertionError):
        g_roof.sat_vol_moist_cont = 1
    with pytest.raises(AssertionError):
        g_roof.residual_vol_moist_cont = 0.4
    with pytest.raises(AssertionError):
        g_roof.init_vol_moist_cont = 5


def test_greenroof_init_from_idf():
    """Test the initialization of EnergyMaterialVegetation objects from strings."""
    ep_st_1 = """Material:RoofVegetation,
           myroof,                   !- name
           0.5,                      !- height of plants
           2.0,                      !- leaf area index
           0.25,                     !- leaf reflectivity
           0.90,                     !- leaf emissivity
           250.0,                    !- minimum stomatal resistance
           GreenRoofDIRT,            !- soil layer name
           MediumRough,              !- roughness
           0.5,                      !- thickness
           0.45,                     !- conductivity of dry soil
           1250.0,                   !- density of dry soil
           950.0,                    !- specific heat of dry soil
           0.74,                     !- thermal absorptance
           0.6,                      !- solar absorptance
           0.5,                      !- visible absorptance
           0.4,                      !- saturation volumetric moisture content of the soil layer
           0.1,                      !- residual volumetric moisture content of the soil layer
           0.4,                      !- initial volumetric moisture content of the soil layer
           Simple;                   !- moisture diffusion calculation method"""
    matter_1 = EnergyMaterialVegetation.from_idf(ep_st_1)

    ep_st_2 = "Material:RoofVegetation, myroof, 0.5, 2.0, 0.25, 0.90, 250.0, " \
        "GreenRoofDIRT, MediumRough, 0.5, 0.45, 1250.0, 950.0, 0.74, 0.6, " \
        "0.5, 0.4, 0.1, 0.4, Simple;"
    matter_2 = EnergyMaterialVegetation.from_idf(ep_st_2)

    assert matter_1.identifier == matter_2.identifier
    assert matter_1 == matter_2

    new_idf_str = matter_1.to_idf()
    new_matter = EnergyMaterialVegetation.from_idf(new_idf_str)
    assert new_idf_str == new_matter.to_idf()


def test_greenroof_dict_methods(userdatadict):
    """Test to/from dict methods"""
    g_roof = EnergyMaterialVegetation(
        'roofmcroofface', 0.5, 0.45, 1250, 950, 'Rough',
        0.89, 0.65, 0.7, 0.5, 2, 0.35, 0.9, 275)
    g_roof.user_data = userdatadict
    grr_dict = g_roof.to_dict()
    new_grr = EnergyMaterialVegetation.from_dict(grr_dict)
    assert grr_dict == new_grr.to_dict()
