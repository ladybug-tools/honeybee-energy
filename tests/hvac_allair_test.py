# coding=utf-8
from honeybee_energy.hvac.allair.vav import VAV
from honeybee_energy.hvac.allair.pvav import PVAV
from honeybee_energy.hvac.allair.psz import PSZ
from honeybee_energy.hvac.allair.ptac import PTAC
from honeybee_energy.hvac.allair.furnace import ForcedAirFurnace

from honeybee.model import Model
from honeybee.room import Room
from honeybee.altnumber import autosize

from ladybug_geometry.geometry3d.pointvector import Point3D

import pytest


def test_vav_init():
    """Test the initialization of VAV and basic properties."""
    hvac_sys = VAV('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'VAV chiller with gas boiler reheat'
    assert hvac_sys.economizer_type == 'Inferred'
    assert hvac_sys.sensible_heat_recovery == autosize
    assert hvac_sys.latent_heat_recovery == autosize

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'VAV district chilled water with district hot water reheat'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'VAV district chilled water with district hot water reheat'
    assert hvac_sys.economizer_type == 'DifferentialDryBulb'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65


def test_vav_equality():
    """Test the equality of VAV objects."""
    hvac_sys = VAV('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = VAV(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_vav_multi_room():
    """Test that VAV systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = VAV('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_vav_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = VAV('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'VAV district chilled water with district hot water reheat'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = VAV.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_pvav_init():
    """Test the initialization of PVAV and basic properties."""
    hvac_sys = PVAV('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'PVAV with gas boiler reheat'
    assert hvac_sys.economizer_type == 'Inferred'
    assert hvac_sys.sensible_heat_recovery == autosize
    assert hvac_sys.latent_heat_recovery == autosize

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PVAV with district hot water reheat'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'PVAV with district hot water reheat'
    assert hvac_sys.economizer_type == 'DifferentialDryBulb'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65


def test_pvav_equality():
    """Test the equality of PVAV objects."""
    hvac_sys = PVAV('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = PVAV(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_pvav_multi_room():
    """Test that PVAV systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = PVAV('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_pvav_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = PVAV('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PVAV with district hot water reheat'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = PVAV.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_psz_init():
    """Test the initialization of PSZ and basic properties."""
    hvac_sys = PSZ('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'PSZ-AC with baseboard electric'
    assert hvac_sys.economizer_type == 'Inferred'
    assert hvac_sys.sensible_heat_recovery == autosize
    assert hvac_sys.latent_heat_recovery == autosize

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PSZ-AC district chilled water with baseboard district hot water'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'PSZ-AC district chilled water with baseboard district hot water'
    assert hvac_sys.economizer_type == 'DifferentialDryBulb'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65


def test_psz_equality():
    """Test the equality of PSZ objects."""
    hvac_sys = PSZ('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = PSZ(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_psz_multi_room():
    """Test that PSZ systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = PSZ('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_psz_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = PSZ('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PSZ-AC district chilled water with baseboard district hot water'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = PSZ.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_ptac_init():
    """Test the initialization of PTAC and basic properties."""
    hvac_sys = PTAC('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'PTAC with baseboard electric'
    assert hvac_sys.economizer_type == 'Inferred'
    assert hvac_sys.sensible_heat_recovery == autosize
    assert hvac_sys.latent_heat_recovery == autosize

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PTAC with district hot water'
    with pytest.raises(AssertionError):
        hvac_sys.economizer_type = 'DifferentialDryBulb'
    with pytest.raises(AssertionError):
        hvac_sys.sensible_heat_recovery = 0.8
    with pytest.raises(AssertionError):
        hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'PTAC with district hot water'


def test_ptac_equality():
    """Test the equality of PTAC objects."""
    hvac_sys = PTAC('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = PTAC(
        'Test System', equipment_type='PTAC with district hot water')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.equipment_type = 'PTAC with gas coil'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_ptac_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = PTAC('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'PTAC with district hot water'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = PTAC.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_furnace_init():
    """Test the initialization of ForcedAirFurnace and basic properties."""
    hvac_sys = ForcedAirFurnace('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Forced air furnace'
    assert hvac_sys.economizer_type == 'Inferred'
    assert hvac_sys.sensible_heat_recovery == autosize
    assert hvac_sys.latent_heat_recovery == autosize

    hvac_sys.vintage = '90.1-2010'
    with pytest.raises(ValueError):
        hvac_sys.equipment_type = 'Air furnace'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8
    hvac_sys.latent_heat_recovery = 0.65
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.economizer_type == 'DifferentialDryBulb'
    assert hvac_sys.sensible_heat_recovery == 0.8
    assert hvac_sys.latent_heat_recovery == 0.65


def test_furnace_equality():
    """Test the equality of ForcedAirFurnace objects."""
    hvac_sys = ForcedAirFurnace('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = ForcedAirFurnace(
        'Test System', sensible_heat_recovery=0.75, latent_heat_recovery=0.6)

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.sensible_heat_recovery = 0.6
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_furnace_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = ForcedAirFurnace('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.economizer_type = 'DifferentialDryBulb'
    hvac_sys.sensible_heat_recovery = 0.8

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = ForcedAirFurnace.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()
