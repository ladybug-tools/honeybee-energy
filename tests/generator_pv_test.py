# coding=utf-8
from honeybee_energy.generator.pv import PVProperties

from honeybee.shade import Shade

import pytest


def test_pv_properties_init():
    """Test the initialization of PVProperties and basic properties."""
    pv_props = PVProperties('Standard PV Product')
    str(pv_props)  # test the string representation

    assert pv_props.identifier == 'Standard PV Product'
    assert pv_props.rated_efficiency == 0.15
    assert pv_props.active_area_fraction == 0.9
    assert pv_props.module_type == 'Standard'
    assert pv_props.mounting_type == 'FixedOpenRack'
    assert pv_props.system_loss_fraction == 0.14
    assert pv_props.tracking_ground_coverage_ratio == 0.4

    pv_props.rated_efficiency = 0.19
    pv_props.active_area_fraction = 0.92
    pv_props.module_type = 'Premium'
    pv_props.mounting_type = 'OneAxisBacktracking'
    pv_props.system_loss_fraction = 0.12
    pv_props.tracking_ground_coverage_ratio = 0.35

    assert pv_props.rated_efficiency == 0.19
    assert pv_props.active_area_fraction == 0.92
    assert pv_props.module_type == 'Premium'
    assert pv_props.mounting_type == 'OneAxisBacktracking'
    assert pv_props.system_loss_fraction == 0.12
    assert pv_props.tracking_ground_coverage_ratio == 0.35


def test_pv_properties_assignment():
    """Test the PVProperties assignment to a parent Shade."""
    shade = Shade.from_vertices(
        'pv_shade_object', [[0, 0, 1], [10, 0, 1], [10, 1, 2], [0, 1, 2]])
    pv_props = PVProperties('Standard PV Product')
    shade.properties.energy.pv_properties = pv_props

    assert shade.properties.energy.pv_properties == pv_props


def test_pv_properties_equality():
    """Test the equality of PVProperties objects."""
    pv_props = PVProperties('Premium PV Product', 0.19, 0.92, 'Premium',
                            'OneAxisBacktracking', 0.12, 0.35)
    pv_props_dup = pv_props.duplicate()
    pv_props_alt = PVProperties(
        'Premium PV Product', 0.19, 0.90, 'Premium',
        'OneAxisBacktracking', 0.12, 0.35)

    assert pv_props is pv_props
    assert pv_props is not pv_props_dup
    assert pv_props == pv_props_dup
    pv_props_dup.active_area_fraction = 0.85
    assert pv_props != pv_props_dup
    assert pv_props != pv_props_alt


def test_pv_properties_to_from_idf():
    """Test the initialization of PVProperties from_idf."""
    shade = Shade.from_vertices(
        'pv_shade_object', [[0, 0, 1], [10, 0, 1], [10, 1, 2], [0, 1, 2]])
    pv_props = PVProperties('Standard PV Product')
    shade.properties.energy.pv_properties = pv_props

    idf_str = pv_props.to_idf(shade)
    assert shade.identifier in idf_str
    assert pv_props.identifier in idf_str

    new_pv_props = PVProperties.from_idf(idf_str, shade)
    assert new_pv_props.identifier == pv_props.identifier
    assert new_pv_props.rated_efficiency == pv_props.rated_efficiency
    assert new_pv_props.active_area_fraction == pv_props.active_area_fraction
    assert new_pv_props.module_type == pv_props.module_type
    assert new_pv_props.mounting_type == pv_props.mounting_type
    assert new_pv_props.tracking_ground_coverage_ratio == pv_props.tracking_ground_coverage_ratio
    assert new_pv_props.system_loss_fraction == pv_props.system_loss_fraction
    assert new_pv_props == pv_props
    assert idf_str == new_pv_props.to_idf(shade)


def test_pv_properties_to_from_dict():
    """Test the initialization of PVProperties from_dict."""
    pv_props = PVProperties('Standard PV Product')

    pv_props_dict = pv_props.to_dict()
    new_pv_props = PVProperties.from_dict(pv_props_dict)
    assert new_pv_props == pv_props
    assert pv_props_dict == new_pv_props.to_dict()


def test_pv_properties_loss_fraction_from_components():
    """Test the PVProperties.loss_fraction_from_components method"""
    assert PVProperties.loss_fraction_from_components() == pytest.approx(0.14, abs=1e-2)
    assert PVProperties.loss_fraction_from_components(0.2) > \
        PVProperties.loss_fraction_from_components(0.0)
