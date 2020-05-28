# coding=utf-8
from honeybee_energy.simulation.shadowcalculation import ShadowCalculation

import pytest


def test_shadow_calculation_init():
    """Test the initialization of ShadowCalculation and basic properties."""
    shadow_calc = ShadowCalculation()
    str(shadow_calc)  # test the string representation

    assert shadow_calc.solar_distribution == 'FullExteriorWithReflections'
    assert shadow_calc.calculation_method == 'PolygonClipping'
    assert shadow_calc.calculation_update_method == 'Periodic'
    assert shadow_calc.calculation_frequency == 30
    assert shadow_calc.maximum_figures == 15000


def test_shadow_calculation_setability():
    """Test the setting of properties of ShadowCalculation."""
    shadow_calc = ShadowCalculation()

    shadow_calc.solar_distribution = 'fullexterior'
    assert shadow_calc.solar_distribution == 'FullExterior'
    shadow_calc.calculation_method = 'pixelcounting'
    assert shadow_calc.calculation_method == 'PixelCounting'
    shadow_calc.calculation_update_method = 'timestep'
    assert shadow_calc.calculation_update_method == 'Timestep'
    shadow_calc.calculation_frequency = 20
    assert shadow_calc.calculation_frequency == 20
    shadow_calc.maximum_figures = 5000
    assert shadow_calc.maximum_figures == 5000


def test_simulation_control_equality():
    """Test the equality of SimulationControl objects."""
    shadow_calc = ShadowCalculation()
    shadow_calc_dup = shadow_calc.duplicate()
    shadow_calc_alt = ShadowCalculation(solar_distribution='FullExterior')

    assert shadow_calc is shadow_calc
    assert shadow_calc is not shadow_calc_dup
    assert shadow_calc == shadow_calc_dup
    shadow_calc_dup.solar_distribution = 'FullExterior'
    assert shadow_calc != shadow_calc_dup
    assert shadow_calc != shadow_calc_alt


def test_simulation_control_init_from_idf():
    """Test the initialization of SimulationControl from_idf."""
    shadow_calc = ShadowCalculation(calculation_frequency=20)

    idf_str = shadow_calc.to_idf()
    rebuilt_shadow_calc = ShadowCalculation.from_idf(idf_str)
    assert shadow_calc == rebuilt_shadow_calc
    assert rebuilt_shadow_calc.to_idf() == idf_str


def test_simulation_control_dict_methods():
    """Test the to/from dict methods."""
    shadow_calc = ShadowCalculation(calculation_frequency=20)

    shadow_dict = shadow_calc.to_dict()
    new_shadow_calc = ShadowCalculation.from_dict(shadow_dict)
    assert new_shadow_calc == shadow_calc
    assert shadow_dict == new_shadow_calc.to_dict()
