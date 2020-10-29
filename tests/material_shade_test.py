# coding=utf-8
from honeybee_energy.material.shade import EnergyWindowMaterialShade, \
    EnergyWindowMaterialBlind

import pytest


def test_shade_init():
    """Test the initialization of shade material objects and basic properties."""
    shade_mat = EnergyWindowMaterialShade(
        'Low-e Diffusing Shade', 0.025, 0.15, 0.5, 0.25, 0.5, 0, 0.4,
        0.2, 0.1, 0.75, 0.25)
    str(shade_mat)  # test the string representation of the material
    shade_dup = shade_mat.duplicate()

    assert shade_mat.identifier == shade_dup.identifier == 'Low-e Diffusing Shade'
    assert shade_mat.thickness == shade_dup.thickness == 0.025
    assert shade_mat.solar_transmittance == shade_dup.solar_transmittance == 0.15
    assert shade_mat.solar_reflectance == shade_dup.solar_reflectance == 0.5
    assert shade_mat.visible_transmittance == shade_dup.visible_transmittance == 0.25
    assert shade_mat.visible_reflectance == shade_dup.visible_reflectance == 0.5
    assert shade_mat.infrared_transmittance == shade_dup.infrared_transmittance == 0
    assert shade_mat.emissivity == shade_dup.emissivity == 0.4
    assert shade_mat.conductivity == shade_dup.conductivity == 0.2
    assert shade_mat.distance_to_glass == shade_dup.distance_to_glass == 0.1
    assert shade_mat.top_opening_multiplier == shade_dup.top_opening_multiplier == 0.75
    assert shade_mat.bottom_opening_multiplier == shade_dup.bottom_opening_multiplier == 0.75
    assert shade_mat.left_opening_multiplier == shade_dup.left_opening_multiplier == 0.75
    assert shade_mat.right_opening_multiplier == shade_dup.right_opening_multiplier == 0.75
    assert shade_mat.airflow_permeability == shade_dup.airflow_permeability == 0.25
    assert shade_mat.resistivity == shade_dup.resistivity == 5
    assert shade_mat.u_value == shade_dup.u_value == 8
    assert shade_mat.r_value == shade_dup.r_value == 0.125


def test_shade_defaults():
    """Test the EnergyWindowMaterialShade default properties."""
    shade_mat = EnergyWindowMaterialShade('Diffusing Shade')

    assert shade_mat.thickness == 0.005
    assert shade_mat.solar_transmittance == 0.4
    assert shade_mat.solar_reflectance == 0.5
    assert shade_mat.visible_transmittance == 0.4
    assert shade_mat.visible_reflectance == 0.4
    assert shade_mat.infrared_transmittance == 0
    assert shade_mat.emissivity == 0.9
    assert shade_mat.conductivity == 0.05
    assert shade_mat.distance_to_glass == 0.05
    assert shade_mat.top_opening_multiplier == 0.5
    assert shade_mat.bottom_opening_multiplier == 0.5
    assert shade_mat.left_opening_multiplier == 0.5
    assert shade_mat.right_opening_multiplier == 0.5
    assert shade_mat.airflow_permeability == 0
    assert shade_mat.resistivity == pytest.approx(1 / 0.05, rel=1e-2)
    assert shade_mat.u_value == pytest.approx(0.05 / 0.005, rel=1e-2)
    assert shade_mat.r_value == pytest.approx(0.005 / 0.05, rel=1e-2)


def test_shade_invalid():
    """Test EnergyWindowMaterialShade objects with invalid properties."""
    shade_mat = EnergyWindowMaterialShade('Diffusing Shade')

    with pytest.raises(TypeError):
        shade_mat.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        shade_mat.thickness = -1
    with pytest.raises(AssertionError):
        shade_mat.conductivity = -1
    with pytest.raises(AssertionError):
        shade_mat.solar_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.solar_reflectance = 2
    with pytest.raises(AssertionError):
        shade_mat.visible_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.visible_reflectance = 2
    with pytest.raises(AssertionError):
        shade_mat.infrared_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.emissivity = 2

    with pytest.raises(AssertionError):
        shade_mat.resistivity = -1
    with pytest.raises(AssertionError):
        shade_mat.u_value = -1
    with pytest.raises(AssertionError):
        shade_mat.r_value = -1


def test_shade_from_idf():
    """Test the initialization of shade material objects from EnergyPlus strings."""
    ep_str_1 = "WindowMaterial:Shade,\n" \
        "Default Shade,             !- Name\n" \
        "0.05,                      !- Solar Transmittance\n" \
        "0.3,                       !- Front Side Solar Reflectance\n" \
        "0.05,                      !- Visible Transmittance\n" \
        "0.3,                       !- Front Side Visible Reflectance\n" \
        "0.86,                      !- Infrared Hemispherical Emissivity\n" \
        "0.04,                      !- Infrared Transmittance \n" \
        "0.003,                     !- Thickness {m}\n" \
        "0.1,                       !- Conductivity {W/m-K}\n" \
        "0.1,                       !- Distance to Glass {m}\n" \
        "1,                         !- Top Opening Multiplier\n" \
        "1,                         !- Bottom Opening Multiplier\n" \
        "1,                         !- Left Opening Multiplier\n" \
        "1,                         !- Right Opening Multiplier\n" \
        "0.04;                      !- Airflow Permeability"
    shade_mat = EnergyWindowMaterialShade.from_idf(ep_str_1)

    assert shade_mat.thickness == 0.003
    assert shade_mat.solar_transmittance == 0.05
    assert shade_mat.solar_reflectance == 0.3
    assert shade_mat.visible_transmittance == 0.05
    assert shade_mat.visible_reflectance == 0.3
    assert shade_mat.infrared_transmittance == 0.04
    assert shade_mat.emissivity == 0.86
    assert shade_mat.conductivity == 0.1
    assert shade_mat.distance_to_glass == 0.1
    assert shade_mat.top_opening_multiplier == 1
    assert shade_mat.bottom_opening_multiplier == 1
    assert shade_mat.left_opening_multiplier == 1
    assert shade_mat.right_opening_multiplier == 1
    assert shade_mat.airflow_permeability == 0.04


def test_shade_dict_methods():
    """Test the to/from dict methods."""
    shade_mat = EnergyWindowMaterialShade(
        'Low-e Diffusing Shade', 0.025, 0.15, 0.5, 0.25, 0.5, 0, 0.4,
        0.2, 0.1, 0.75, 0.25)
    material_dict = shade_mat.to_dict()
    new_material = EnergyWindowMaterialShade.from_dict(material_dict)
    assert material_dict == new_material.to_dict()


def test_blind_init():
    """Test the initialization of blind material objects and basic properties."""
    shade_mat = EnergyWindowMaterialBlind(
        'Plastic Blind', 'Vertical', 0.025, 0.01875, 0.003, 90, 0.2, 0.05, 0.4,
        0.05, 0.45, 0, 0.95, 0.1, 1)
    str(shade_mat)  # test the string representation of the material
    shade_dup = shade_mat.duplicate()

    assert shade_mat.identifier == shade_dup.identifier == 'Plastic Blind'
    assert shade_mat.slat_orientation == shade_dup.slat_orientation == 'Vertical'
    assert shade_mat.slat_width == shade_dup.slat_width == 0.025
    assert shade_mat.slat_separation == shade_dup.slat_separation == 0.01875
    assert shade_mat.slat_thickness == shade_dup.slat_thickness == 0.003
    assert shade_mat.slat_angle == shade_dup.slat_angle == 90
    assert shade_mat.slat_conductivity == shade_dup.slat_conductivity == 0.2
    assert shade_mat.beam_solar_transmittance == shade_dup.beam_solar_transmittance == 0.05
    assert shade_mat.beam_solar_reflectance == shade_dup.beam_solar_reflectance == 0.4
    assert shade_mat.beam_solar_reflectance_back == shade_dup.beam_solar_reflectance_back == 0.4
    assert shade_mat.diffuse_solar_transmittance == shade_dup.diffuse_solar_transmittance == 0.05
    assert shade_mat.diffuse_solar_reflectance == shade_dup.diffuse_solar_reflectance == 0.4
    assert shade_mat.diffuse_solar_reflectance_back == shade_dup.diffuse_solar_reflectance_back == 0.4
    assert shade_mat.beam_visible_transmittance == shade_dup.beam_visible_transmittance == 0.05
    assert shade_mat.beam_visible_reflectance == shade_dup.beam_visible_reflectance == 0.45
    assert shade_mat.beam_visible_reflectance_back == shade_dup.beam_visible_reflectance_back == 0.45
    assert shade_mat.diffuse_visible_transmittance == shade_dup.diffuse_visible_transmittance == 0.05
    assert shade_mat.diffuse_visible_reflectance == shade_dup.diffuse_visible_reflectance == 0.45
    assert shade_mat.diffuse_visible_reflectance_back == shade_dup.diffuse_visible_reflectance_back == 0.45
    assert shade_mat.infrared_transmittance == shade_dup.infrared_transmittance == 0
    assert shade_mat.emissivity == shade_dup.emissivity == 0.95
    assert shade_mat.emissivity_back == shade_dup.emissivity_back == 0.95
    assert shade_mat.distance_to_glass == shade_dup.distance_to_glass == 0.1
    assert shade_mat.top_opening_multiplier == shade_dup.top_opening_multiplier == 1
    assert shade_mat.bottom_opening_multiplier == shade_dup.bottom_opening_multiplier == 1
    assert shade_mat.left_opening_multiplier == shade_dup.left_opening_multiplier == 1
    assert shade_mat.right_opening_multiplier == shade_dup.right_opening_multiplier == 1
    assert shade_mat.slat_resistivity == shade_dup.slat_resistivity == 1 / 0.2
    assert shade_mat.u_value == shade_dup.u_value == 0.2 / 0.003
    assert shade_mat.r_value == shade_dup.r_value == 0.003 / 0.2


def test_blind_defaults():
    """Test the EnergyWindowMaterialBlind default properties."""
    shade_mat = EnergyWindowMaterialBlind('Metallic Blind')

    assert shade_mat.slat_orientation == 'Horizontal'
    assert shade_mat.slat_width == 0.025
    assert shade_mat.slat_separation == 0.01875
    assert shade_mat.slat_thickness == 0.001
    assert shade_mat.slat_angle == 45
    assert shade_mat.slat_conductivity == 221
    assert shade_mat.beam_solar_transmittance == 0
    assert shade_mat.beam_solar_reflectance == 0.5
    assert shade_mat.beam_solar_reflectance_back == 0.5
    assert shade_mat.diffuse_solar_transmittance == 0
    assert shade_mat.diffuse_solar_reflectance == 0.5
    assert shade_mat.diffuse_solar_reflectance_back == 0.5
    assert shade_mat.beam_visible_transmittance == 0
    assert shade_mat.beam_visible_reflectance == 0.5
    assert shade_mat.beam_visible_reflectance_back == 0.5
    assert shade_mat.diffuse_visible_transmittance == 0
    assert shade_mat.diffuse_visible_reflectance == 0.5
    assert shade_mat.diffuse_visible_reflectance_back == 0.5
    assert shade_mat.infrared_transmittance == 0
    assert shade_mat.emissivity == 0.9
    assert shade_mat.emissivity_back == 0.9
    assert shade_mat.distance_to_glass == 0.05
    assert shade_mat.top_opening_multiplier == 0.5
    assert shade_mat.bottom_opening_multiplier == 0.5
    assert shade_mat.left_opening_multiplier == 0.5
    assert shade_mat.right_opening_multiplier == 0.5


def test_blind_invalid():
    """Test EnergyWindowMaterialShade objects with invalid properties."""
    shade_mat = EnergyWindowMaterialBlind('Metallic Blind')

    with pytest.raises(TypeError):
        shade_mat.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        shade_mat.slat_orientation = 'Diagonal'
    with pytest.raises(AssertionError):
        shade_mat.slat_width = 2
    with pytest.raises(AssertionError):
        shade_mat.slat_separation = 2
    with pytest.raises(AssertionError):
        shade_mat.slat_thickness = -1
    with pytest.raises(AssertionError):
        shade_mat.slat_angle = 270
    with pytest.raises(AssertionError):
        shade_mat.slat_conductivity = -1
    with pytest.raises(AssertionError):
        shade_mat.beam_solar_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.beam_solar_reflectance = 2
    with pytest.raises(AssertionError):
        shade_mat.beam_visible_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.beam_visible_reflectance = 2
    with pytest.raises(AssertionError):
        shade_mat.infrared_transmittance = 2
    with pytest.raises(AssertionError):
        shade_mat.emissivity = 2

    with pytest.raises(AssertionError):
        shade_mat.slat_resistivity = -1
    with pytest.raises(AssertionError):
        shade_mat.u_value = -1
    with pytest.raises(AssertionError):
        shade_mat.r_value = -1


def test_blind_from_idf():
    """Test the initialization of shade material objects from EnergyPlus strings."""
    ep_str_1 = "WindowMaterial:Blind,\n" \
        "Default Shade,      !- Name\n" \
        "Horizontal,         !- Slat Orientation\n" \
        "0.04,               !- Slat Width {m}\n" \
        "0.04,               !- Slat Separation {m}\n" \
        "0.00025,            !- Slat Thickness {m}\n" \
        "90.0,               !- Slat Angle {deg}\n" \
        "221,                !- Slat Conductivity {W/m-K}\n" \
        "0,                  !- Slat Beam Solar Transmittance\n" \
        "0.65,               !- Front Side Slat Beam Solar Reflectance\n" \
        "0.65,               !- Back Side Slat Beam Solar Reflectance\n" \
        "0,                  !- Slat Diffuse Solar Transmittance\n" \
        "0.65,               !- Front Side Slat Diffuse Solar Reflectance\n" \
        "0.65,               !- Back Side Slat Diffuse Solar Reflectance\n" \
        "0,                  !- Slat Beam Visible Transmittance\n" \
        "0.65,               !- Front Side Slat Beam Visible Reflectance\n" \
        "0.65,               !- Back Side Slat Beam Visible Reflectance\n" \
        "0,                  !- Slat Diffuse Visible Transmittance\n" \
        "0.65,               !- Front Side Slat Diffuse Visible Reflectance\n" \
        "0.65,               !- Back Side Slat Diffuse Visible Reflectance\n" \
        "0,                  !- Slat Infrared Hemispherical Transmittance\n" \
        "0.9,                !- Front Side Slat Infrared Hemispherical Emissivity\n" \
        "0.9,                !- Back Side Slat Infrared Hemispherical Emissivity\n" \
        "0.03,               !- Blind to Glass Distance {m}\n" \
        "1.0,                !- Blind Top Opening Multiplier\n" \
        "1.0,                !- Blind Bottom Opening Multiplier\n" \
        "1.0,                !- Blind Left Side Opening Multiplier\n" \
        "1.0,                !- Blind Right Side Opening Multiplier\n" \
        "0,                  !- Minimum Slat Angle {deg}\n" \
        "180;                !- Maximum Slat Angle {deg}"
    shade_mat = EnergyWindowMaterialBlind.from_idf(ep_str_1)

    assert shade_mat.slat_orientation == 'Horizontal'
    assert shade_mat.slat_width == 0.04
    assert shade_mat.slat_separation == 0.04
    assert shade_mat.slat_thickness == 0.00025
    assert shade_mat.slat_angle == 90
    assert shade_mat.slat_conductivity == 221
    assert shade_mat.beam_solar_transmittance == 0
    assert shade_mat.beam_solar_reflectance == 0.65
    assert shade_mat.beam_solar_reflectance_back == 0.65
    assert shade_mat.diffuse_solar_transmittance == 0
    assert shade_mat.diffuse_solar_reflectance == 0.65
    assert shade_mat.diffuse_solar_reflectance_back == 0.65
    assert shade_mat.beam_visible_transmittance == 0
    assert shade_mat.beam_visible_reflectance == 0.65
    assert shade_mat.beam_visible_reflectance_back == 0.65
    assert shade_mat.diffuse_visible_transmittance == 0
    assert shade_mat.diffuse_visible_reflectance == 0.65
    assert shade_mat.diffuse_visible_reflectance_back == 0.65
    assert shade_mat.infrared_transmittance == 0
    assert shade_mat.emissivity == 0.9
    assert shade_mat.emissivity_back == 0.9
    assert shade_mat.distance_to_glass == 0.03
    assert shade_mat.top_opening_multiplier == 1
    assert shade_mat.bottom_opening_multiplier == 1
    assert shade_mat.left_opening_multiplier == 1
    assert shade_mat.right_opening_multiplier == 1


def test_blind_dict_methods():
    """Test the to/from dict methods."""
    shade_mat = EnergyWindowMaterialBlind(
        'Plastic Blind', 'Vertical', 0.025, 0.01875, 0.003, 90, 0.2, 0.05, 0.4,
        0.05, 0.45, 0, 0.95, 0.1, 1)
    material_dict = shade_mat.to_dict()
    new_material = EnergyWindowMaterialBlind.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
