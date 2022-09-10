# coding=utf-8
from honeybee_energy.material.frame import EnergyWindowFrame

import pytest
from .fixtures.userdata_fixtures import userdatadict


def test_frame_init(userdatadict):
    """Test the initialization of EnergyMaterial objects and basic properties."""
    wood_frame = EnergyWindowFrame(
        'Wood_Frame_050_032', 0.05, 3.2, 2.6, 0.05, 0.1, 0.95, 0.75, 0.8)
    wood_frame.user_data = userdatadict
    str(wood_frame)  # test the string representation of the material
    wood_frame_dup = wood_frame.duplicate()

    assert wood_frame.identifier == wood_frame_dup.identifier == 'Wood_Frame_050_032'
    assert wood_frame.width == wood_frame_dup.width == 0.05
    assert wood_frame.conductance == wood_frame_dup.conductance == 3.2
    assert wood_frame.edge_to_center_ratio == wood_frame_dup.edge_to_center_ratio == 2.6
    assert wood_frame.outside_projection == wood_frame_dup.outside_projection == 0.05
    assert wood_frame.inside_projection == wood_frame_dup.inside_projection == 0.1
    assert wood_frame.thermal_absorptance == wood_frame_dup.thermal_absorptance == 0.95
    assert wood_frame.solar_absorptance == wood_frame_dup.solar_absorptance == 0.75
    assert wood_frame.visible_absorptance == wood_frame_dup.visible_absorptance == 0.8

    assert wood_frame.u_value == pytest.approx(3.2, rel=1e-2)
    assert wood_frame.r_value == pytest.approx(1 / 3.2, rel=1e-2)

    wood_frame.r_value = 0.5
    assert wood_frame.conductance != wood_frame_dup.conductance
    assert wood_frame.r_value == 0.5
    assert wood_frame.conductance == pytest.approx(2.0, rel=1e-2)
    assert wood_frame.user_data == userdatadict

    with pytest.raises(AssertionError):
        wood_frame.width = 0


def test_frame_equivalency(userdatadict):
    """Test the equality of a material to another EnergyMaterial."""
    wood_frame_1 = EnergyWindowFrame(
        'Wood_Frame_050_032', 0.05, 3.2, 2.6, 0.05, 0.1, 0.95, 0.75, 0.8)
    wood_frame_1.user_data = userdatadict
    wood_frame_2 = wood_frame_1.duplicate()
    steel_frame = EnergyWindowFrame(
        'Steel_Frame_050_032', 0.05, 56.0, 3.2, 0.01, 0.01)

    assert wood_frame_1 == wood_frame_2
    assert wood_frame_1 != steel_frame
    collection = [wood_frame_1, wood_frame_2, steel_frame]
    assert len(set(collection)) == 2

    wood_frame_2.conductance = 3.5
    assert wood_frame_1 != wood_frame_2
    assert len(set(collection)) == 3


def test_frame_lockability(userdatadict):
    """Test the lockability of the EnergyMaterial."""
    wood_frame = EnergyWindowFrame(
        'Wood_Frame_050_032', 0.05, 3.2, 2.6, 0.05, 0.1, 0.95, 0.75, 0.8)
    wood_frame.conductance = 3.5
    wood_frame.user_data = userdatadict
    wood_frame.lock()
    with pytest.raises(AttributeError):
        wood_frame.conductance = 5.0
    wood_frame.unlock()
    wood_frame.conductance = 5.0


def test_frame_defaults():
    """Test the EnergyMaterial default properties."""
    wood_frame = EnergyWindowFrame('Wood_Frame_050_032', 0.05, 3.2)

    assert wood_frame.edge_to_center_ratio == 1
    assert wood_frame.outside_projection == 0
    assert wood_frame.inside_projection == 0
    assert wood_frame.thermal_absorptance == 0.9
    assert wood_frame.solar_absorptance == wood_frame.visible_absorptance == 0.7


def test_frame_invalid():
    """Test the initialization of EnergyMaterial objects with invalid properties."""
    wood_frame = EnergyWindowFrame('Wood_Frame_050_032', 0.05, 3.2)

    with pytest.raises(TypeError):
        wood_frame.identifier = ['test_identifier']
    with pytest.raises(AssertionError):
        wood_frame.width = -1
    with pytest.raises(AssertionError):
        wood_frame.conductance = -1
    with pytest.raises(AssertionError):
        wood_frame.edge_to_center_ratio = -1
    with pytest.raises(AssertionError):
        wood_frame.outside_projection = -0.5
    with pytest.raises(AssertionError):
        wood_frame.inside_projection = -0.5
    with pytest.raises(AssertionError):
        wood_frame.thermal_absorptance = 2
    with pytest.raises(AssertionError):
        wood_frame.solar_absorptance = 2
    with pytest.raises(AssertionError):
        wood_frame.visible_absorptance = 2

    with pytest.raises(AssertionError):
        wood_frame.u_value = -1
    with pytest.raises(AssertionError):
        wood_frame.r_value = -1


def test_frame_to_from_idf():
    """Test the initialization of EnergyMaterial objects from EnergyPlus strings."""
    ep_str_1 = 'WindowProperty:FrameAndDivider,\n' \
        'Picture-Frame,                 !- User Supplied Frame/Divider Name\n' \
        '0.069850,                      !- Frame Width {m}\n' \
        ',                              !- Frame Outside Projection {m}\n' \
        ',                              !- Frame Insider Projection {m}\n' \
        '2.326112,                      !- Frame Conductance {w/m2-K}\n' \
        '2.591818,                      !- Edge to Center-of-glass Conductance Ratio\n' \
        '0.9,                           !- Frame Solar absorptance\n' \
        '0.9,                           !- Frame Visible absorptance\n' \
        '0.9;                           !- Frame Thermal hemispherical Emissivity'
    mat_1 = EnergyWindowFrame.from_idf(ep_str_1)

    ep_str_2 = "WindowProperty:FrameAndDivider, Picture-Frame, 0.06985, " \
        "0.1, 0.1, 2.326, 2.591, 0.9, 0.7, 0.7;"
    mat_2 = EnergyWindowFrame.from_idf(ep_str_2)

    ep_str_3 = "WindowProperty:FrameAndDivider, Picture-Frame, 0.06985, " \
        "0.1, 0.1, 2.326;"
    mat_3 = EnergyWindowFrame.from_idf(ep_str_3)

    assert mat_1.identifier == mat_2.identifier == mat_3.identifier

    idf_str = mat_1.to_idf()
    new_mat_1 = EnergyWindowFrame.from_idf(idf_str)
    assert idf_str == new_mat_1.to_idf()


def test_frame_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    material = EnergyWindowFrame(
        'Wood_Frame_050_032', 0.05, 3.2, 2.6, 0.05, 0.1, 0.95, 0.75, 0.8)
    material.user_data = userdatadict
    material_dict = material.to_dict()
    new_material = EnergyWindowFrame.from_dict(material_dict)
    assert material_dict == new_material.to_dict()
