# coding=utf-8
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys

import pytest
from .fixtures.userdata_fixtures import userdatadict


def test_glazing_init(userdatadict):
    """Test the initialization of EnergyMaterial objects and basic properties."""
    lowe = EnergyWindowMaterialGlazing(
        'Low-e Glass', 0.00318, 0.4517, 0.359, 0.714, 0.207,
        0, 0.84, 0.046578, 1.0)
    lowe.user_data = userdatadict
    str(lowe)  # test the string representation of the material
    lowe_dup = lowe.duplicate()

    assert lowe.identifier == lowe_dup.identifier == 'Low-e Glass'
    assert lowe.thickness == lowe_dup.thickness == 0.00318
    assert lowe.solar_transmittance == lowe_dup.solar_transmittance == 0.4517
    assert lowe.solar_reflectance == lowe_dup.solar_reflectance == 0.359
    assert lowe.solar_reflectance_back == lowe_dup.solar_reflectance_back == 0.359
    assert lowe.visible_transmittance == lowe_dup.visible_transmittance == 0.714
    assert lowe.visible_reflectance == lowe_dup.visible_reflectance == 0.207
    assert lowe.visible_reflectance_back == lowe_dup.visible_reflectance_back == 0.207
    assert lowe.infrared_transmittance == lowe_dup.infrared_transmittance == 0
    assert lowe.emissivity == lowe_dup.emissivity == 0.84
    assert lowe.emissivity_back == lowe_dup.emissivity_back == 0.046578
    assert lowe.conductivity == lowe_dup.conductivity == 1.0
    assert lowe.dirt_correction == lowe_dup.dirt_correction == 1.0
    assert lowe.solar_diffusing is lowe_dup.solar_diffusing is False
    assert lowe.resistivity == lowe_dup.resistivity == pytest.approx(1.0, rel=1e-2)
    assert lowe.u_value == lowe_dup.u_value == pytest.approx(314.465, rel=1e-2)
    assert lowe.r_value == lowe_dup.r_value == pytest.approx(0.00318, rel=1e-2)
    assert lowe.user_data == userdatadict
    lowe.resistivity = 0.5
    assert lowe.conductivity != lowe_dup.conductivity
    assert lowe.conductivity == pytest.approx(2, rel=1e-2)


def test_glazing_defaults():
    """Test the EnergyWindowMaterialGlazing default properties."""
    clear = EnergyWindowMaterialGlazing('Clear Glass')

    assert clear.identifier == 'Clear Glass'
    assert clear.thickness == 0.003
    assert clear.solar_transmittance == 0.85
    assert clear.solar_reflectance == 0.075
    assert clear.solar_reflectance_back == 0.075
    assert clear.visible_transmittance == 0.9
    assert clear.visible_reflectance == 0.075
    assert clear.visible_reflectance_back == 0.075
    assert clear.infrared_transmittance == 0
    assert clear.emissivity == 0.84
    assert clear.emissivity_back == 0.84
    assert clear.conductivity == 0.9
    assert clear.dirt_correction == 1.0
    assert clear.solar_diffusing is False


def test_glazing_invalid():
    """Test EnergyWindowMaterialGlazing objects with invalid properties."""
    clear = EnergyWindowMaterialGlazing('Clear Glass')

    with pytest.raises(TypeError):
        clear.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        clear.thickness = -1
    with pytest.raises(AssertionError):
        clear.conductivity = -1
    with pytest.raises(AssertionError):
        clear.solar_transmittance = 2
    with pytest.raises(AssertionError):
        clear.solar_reflectance = 2
    with pytest.raises(AssertionError):
        clear.visible_transmittance = 2
    with pytest.raises(AssertionError):
        clear.visible_reflectance = 2
    with pytest.raises(AssertionError):
        clear.infrared_transmittance = 2
    with pytest.raises(AssertionError):
        clear.emissivity = 2
    with pytest.raises(AssertionError):
        clear.emissivity_back = 2

    with pytest.raises(AssertionError):
        clear.resistivity = -1
    with pytest.raises(AssertionError):
        clear.u_value = -1
    with pytest.raises(AssertionError):
        clear.r_value = -1


def test_glazing_init_from_idf():
    """Test the initialization of EnergyMaterial objects from EnergyPlus strings."""
    ep_str_1 = "WindowMaterial:Glazing,\n" \
        "Clear 3mm,                 !- Name\n" \
        "SpectralAverage,           !- Optical Data Type\n" \
        ",                          !- Window Glass Spectral Data Set Name\n" \
        "0.003,                     !- Thickness {m}\n" \
        "0.837,                     !- Solar Transmittance at Normal Incidence\n" \
        "0.075,                     !- Front Side Solar Reflectance at Normal Incidence\n" \
        "0,                         !- Back Side Solar Reflectance at Normal Incidence\n" \
        "0.898,                     !- Visible Transmittance at Normal Incidence\n" \
        "0.081,                     !- Front Side Visible Reflectance at Normal Incidence\n" \
        "0,                         !- Back Side Visible Reflectance at Normal Incidence\n" \
        "0,                         !- Infrared Transmittance at Normal Incidence\n" \
        "0.84,                      !- Front Side Infrared Hemispherical Emissivity\n" \
        "0.84,                      !- Back Side Infrared Hemispherical Emissivity\n" \
        "0.9,                       !- Conductivity {W/m-K}\n" \
        "1,                         !- Dirt Correction Factor for Solar and Visible Transmittance\n" \
        "No;                        !- Solar Diffusing"
    clear_glass = EnergyWindowMaterialGlazing.from_idf(ep_str_1)

    idf_str = clear_glass.to_idf()
    new_mat_1 = EnergyWindowMaterialGlazing.from_idf(idf_str)
    assert idf_str == new_mat_1.to_idf()


def test_glazing_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    lowe = EnergyWindowMaterialGlazing(
        'Low-e Glass', 0.00318, 0.4517, 0.359, 0.714, 0.207,
        0, 0.84, 0.046578, 1.0)
    lowe.user_data = userdatadict
    material_dict = lowe.to_dict()
    new_material = EnergyWindowMaterialGlazing.from_dict(material_dict)
    assert material_dict == new_material.to_dict()


def test_simple_sys_init(userdatadict):
    """Test initialization of EnergyWindowMaterialSimpleGlazSys and properties."""
    lowe_sys = EnergyWindowMaterialSimpleGlazSys(
        'Double Pane Low-e', 1.8, 0.35, 0.55)
    lowe_sys.user_data = userdatadict
    str(lowe_sys)  # test the string representation of the material
    lowe_sys_dup = lowe_sys.duplicate()

    assert lowe_sys.identifier == lowe_sys_dup.identifier == 'Double Pane Low-e'
    assert lowe_sys.u_factor == lowe_sys_dup.u_factor == 1.8
    assert lowe_sys.shgc == lowe_sys_dup.shgc == 0.35
    assert lowe_sys.vt == lowe_sys_dup.vt == 0.55

    assert lowe_sys.r_factor == lowe_sys_dup.r_factor == pytest.approx(1 / 1.8, rel=1e-3)
    assert lowe_sys.r_value == lowe_sys_dup.r_value == pytest.approx(0.38167, rel=1e-3)
    assert lowe_sys.u_value == lowe_sys_dup.u_value == pytest.approx(1 / 0.38167, rel=1e-3)
    assert lowe_sys.solar_transmittance < lowe_sys_dup.shgc


def test_simple_sys_defaults():
    """Test the EnergyWindowMaterialGlazing default properties."""
    clear = EnergyWindowMaterialSimpleGlazSys('Clear Window', 5.5, 0.8)
    assert clear.vt == 0.6


def test_simple_sys_invalid():
    """Test EnergyWindowMaterialGlazing objects with invalid properties."""
    clear = EnergyWindowMaterialSimpleGlazSys('Clear Window', 5.5, 0.8)

    with pytest.raises(TypeError):
        clear.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        clear.u_factor = 20
    with pytest.raises(AssertionError):
        clear.shgc = 2
    with pytest.raises(AssertionError):
        clear.vt = 2


def test_simple_sys_init_from_idf():
    """Test initialization of EnergyWindowMaterialGlazing objects from strings."""
    ep_str_1 = "WindowMaterial:SimpleGlazingSystem,\n" \
        "Fixed Window 2.00-0.40-0.31,            !- Name\n" \
        "1.987,                                  !- U-Factor {W/m2-K}\n" \
        "0.45,                                   !- Solar Heat Gain Coefficient\n" \
        "0.35;                                   !- Visible Transmittance"
    glaz_sys = EnergyWindowMaterialSimpleGlazSys.from_idf(ep_str_1)

    assert glaz_sys.identifier == 'Fixed Window 2.00-0.40-0.31'
    assert glaz_sys.u_factor == 1.987
    assert glaz_sys.shgc == 0.45
    assert glaz_sys.vt == 0.35


def test_simple_sys_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    clear = EnergyWindowMaterialSimpleGlazSys('Clear Window', 5.5, 0.8)
    clear.user_data = userdatadict
    material_dict = clear.to_dict()
    new_material = EnergyWindowMaterialSimpleGlazSys.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
