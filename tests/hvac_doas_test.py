# coding=utf-8
from honeybee_energy.hvac.doas.fcu import FCUwithDOAS
from honeybee_energy.hvac.doas.vrf import VRFwithDOAS
from honeybee_energy.hvac.doas.wshp import WSHPwithDOAS

from honeybee.model import Model
from honeybee.room import Room
from honeybee.altnumber import autosize

from ladybug_geometry.geometry3d.pointvector import Point3D

import pytest
from .fixtures.userdata_fixtures import userdatadict

def test_fcu_with_doas_init(userdatadict):
    """Test the initialization of FCUwithDOAS and basic properties."""
    hvac_sys = FCUwithDOAS('Test System')
    hvac_sys.user_data = userdatadict
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == 'ASHRAE_2019'
    assert hvac_sys.equipment_type == 'DOAS_FCU_Chiller_Boiler'
    assert hvac_sys.sensible_heat_recovery == 0
    assert hvac_sys.latent_heat_recovery == 0

    hvac_sys.vintage = 'ASHRAE_2010'
    hvac_sys.equipment_type = 'DOAS_FCU_DCW_DHW'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == 'ASHRAE_2010'
    assert hvac_sys.equipment_type == 'DOAS_FCU_DCW_DHW'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65
    assert hvac_sys.user_data == userdatadict
    
def test_fcu_with_doas_equality(userdatadict):
    """Test the equality of FCUwithDOAS objects."""
    hvac_sys = FCUwithDOAS('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = FCUwithDOAS(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)
    hvac_sys.user_data = userdatadict

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_fcu_with_doas_multi_room(userdatadict):
    """Test that FCUwithDOAS systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = FCUwithDOAS('Test System')
    hvac_sys.user_data = userdatadict

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_fcu_with_doas_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    hvac_sys = FCUwithDOAS('High Efficiency HVAC System')
    hvac_sys.vintage = 'ASHRAE_2010'
    hvac_sys.equipment_type = 'DOAS_FCU_DCW_DHW'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    hvac_sys.user_data = userdatadict

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = FCUwithDOAS.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_vrf_with_doas_init(userdatadict):
    """Test the initialization of VRFwithDOAS and basic properties."""
    hvac_sys = VRFwithDOAS('Test System')
    hvac_sys.user_data = userdatadict
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == 'ASHRAE_2019'
    assert hvac_sys.equipment_type == 'DOAS_VRF'
    assert hvac_sys.sensible_heat_recovery == 0
    assert hvac_sys.latent_heat_recovery == 0
    assert hvac_sys.user_data == userdatadict

    hvac_sys.vintage = 'ASHRAE_2010'
    with pytest.raises(ValueError):
        hvac_sys.equipment_type = 'DOAS with ground sourced VRF'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == 'ASHRAE_2010'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65
    assert hvac_sys.user_data == userdatadict


def test_vrf_with_doas_equality(userdatadict):
    """Test the equality of VRFwithDOAS objects."""
    hvac_sys = VRFwithDOAS('Test System')
    hvac_sys.user_data = userdatadict
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = VRFwithDOAS(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_vrf_with_doas_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    hvac_sys = VRFwithDOAS('High Efficiency HVAC System')
    hvac_sys.vintage = 'ASHRAE_2010'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    hvac_sys.user_data = userdatadict

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = VRFwithDOAS.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_wshp_with_doas_init(userdatadict):
    """Test the initialization of WSHPwithDOAS and basic properties."""
    hvac_sys = WSHPwithDOAS('Test System')
    hvac_sys.user_data = userdatadict
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == 'ASHRAE_2019'
    assert hvac_sys.equipment_type == 'DOAS_WSHP_FluidCooler_Boiler'
    assert hvac_sys.sensible_heat_recovery == 0
    assert hvac_sys.latent_heat_recovery == 0

    hvac_sys.vintage = 'ASHRAE_2010'
    hvac_sys.equipment_type = 'DOAS_WSHP_GSHP'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == 'ASHRAE_2010'
    assert hvac_sys.equipment_type == 'DOAS_WSHP_GSHP'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65
    assert hvac_sys.user_data == userdatadict


def test_wshp_with_doas_equality(userdatadict):
    """Test the equality of WSHPwithDOAS objects."""
    hvac_sys = WSHPwithDOAS('Test System')
    hvac_sys.user_data = userdatadict
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = WSHPwithDOAS(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_wshp_with_doas_dict_methods(userdatadict):
    """Test the to/from dict methods."""
    hvac_sys = WSHPwithDOAS('High Efficiency HVAC System')
    hvac_sys.user_data = userdatadict
    hvac_sys.vintage = 'ASHRAE_2010'
    hvac_sys.equipment_type = 'DOAS_WSHP_GSHP'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = WSHPwithDOAS.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()
