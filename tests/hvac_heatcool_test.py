# coding=utf-8
from honeybee_energy.hvac.heatcool.fcu import FCU
from honeybee_energy.hvac.heatcool.vrf import VRF
from honeybee_energy.hvac.heatcool.wshp import WSHP
from honeybee_energy.hvac.heatcool.baseboard import Baseboard
from honeybee_energy.hvac.heatcool.evapcool import EvaporativeCooler
from honeybee_energy.hvac.heatcool.gasunit import GasUnitHeater
from honeybee_energy.hvac.heatcool.residential import Residential
from honeybee_energy.hvac.heatcool.windowac import WindowAC

from honeybee.model import Model
from honeybee.room import Room

from ladybug_geometry.geometry3d.pointvector import Point3D

import pytest


def test_fcu_init():
    """Test the initialization of FCU and basic properties."""
    hvac_sys = FCU('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Fan coil chiller with boiler'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Fan coil district chilled water with district hot water'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Fan coil district chilled water with district hot water'


def test_fcu_equality():
    """Test the equality of FCU objects."""
    hvac_sys = FCU('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = FCU(
        'Test System',
        equipment_type='Fan coil air-cooled chiller with central air source heat pump')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_fcu_multi_room():
    """Test that FCU systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = FCU('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_fcu_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = FCU('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Fan coil district chilled water with district hot water'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = FCU.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_vrf_init():
    """Test the initialization of VRF and basic properties."""
    hvac_sys = VRF('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'VRF'

    hvac_sys.vintage = '90.1-2010'
    with pytest.raises(ValueError):
        hvac_sys.equipment_type = 'Ground sourced VRF'
    assert hvac_sys.vintage == '90.1-2010'


def test_vrf_equality():
    """Test the equality of VRF objects."""
    hvac_sys = VRF('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = VRF('Test System', vintage='90.1-2010')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_vrf_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = VRF('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = VRF.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_wshp_init():
    """Test the initialization of WSHP and basic properties."""
    hvac_sys = WSHP('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Water source heat pumps fluid cooler with boiler'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Water source heat pumps with ground source heat pump'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Water source heat pumps with ground source heat pump'


def test_wshp_equality():
    """Test the equality of WSHP objects."""
    hvac_sys = WSHP('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = WSHP(
        'Test System',
        equipment_type='Water source heat pumps with ground source heat pump')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_wshp_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = WSHP('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Water source heat pumps with ground source heat pump'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = WSHP.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_baseboard_init():
    """Test the initialization of Baseboard and basic properties."""
    hvac_sys = Baseboard('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Baseboard electric'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Baseboard district hot water'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Baseboard district hot water'


def test_baseboard_equality():
    """Test the equality of Baseboard objects."""
    hvac_sys = Baseboard('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = Baseboard(
        'Test System', equipment_type='Baseboard district hot water')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_baseboard_multi_room():
    """Test that Baseboard systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = Baseboard('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_baseboard_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = Baseboard('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Baseboard district hot water'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = Baseboard.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_evap_cool_init():
    """Test the initialization of EvaporativeCooler and basic properties."""
    hvac_sys = EvaporativeCooler('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Direct evap coolers with baseboard electric'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Direct evap coolers with baseboard district hot water'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Direct evap coolers with baseboard district hot water'


def test_evap_cool_equality():
    """Test the equality of EvaporativeCooler objects."""
    hvac_sys = EvaporativeCooler('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = EvaporativeCooler(
        'Test System',
        equipment_type='Direct evap coolers with baseboard district hot water')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_evap_cool_multi_room():
    """Test that EvaporativeCooler systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = EvaporativeCooler('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_evap_cool_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = EvaporativeCooler('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Direct evap coolers with baseboard district hot water'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = EvaporativeCooler.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_gasunit_init():
    """Test the initialization of GasUnitHeater and basic properties."""
    hvac_sys = GasUnitHeater('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Gas unit heaters'

    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys.vintage == '90.1-2010'


def test_gasunit_equality():
    """Test the equality of GasUnitHeater objects."""
    hvac_sys = GasUnitHeater('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = GasUnitHeater('Test System', vintage='90.1-2010')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys_dup.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_gasunit_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = GasUnitHeater('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = GasUnitHeater.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_residential_init():
    """Test the initialization of Residential and basic properties."""
    hvac_sys = Residential('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Residential AC with baseboard electric'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Residential forced air furnace'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Residential forced air furnace'


def test_residential_equality():
    """Test the equality of Residential objects."""
    hvac_sys = Residential('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = Residential(
        'Test System', equipment_type='Residential forced air furnace')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_residential_multi_room():
    """Test that Residential systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = Residential('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_residential_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = Residential('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Residential forced air furnace'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = Residential.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()


def test_window_ac_init():
    """Test the initialization of WindowAC and basic properties."""
    hvac_sys = WindowAC('Test System')
    str(hvac_sys)  # test the string representation

    assert hvac_sys.identifier == 'Test System'
    assert hvac_sys.vintage == '90.1-2013'
    assert hvac_sys.equipment_type == 'Window AC with baseboard electric'

    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Window AC with baseboard central air source heat pump'
    assert hvac_sys.vintage == '90.1-2010'
    assert hvac_sys.equipment_type == 'Window AC with baseboard central air source heat pump'


def test_window_ac_equality():
    """Test the equality of WindowAC objects."""
    hvac_sys = WindowAC('Test System')
    hvac_sys_dup = hvac_sys.duplicate()
    hvac_sys_alt = WindowAC(
        'Test System',
        equipment_type='Window AC with baseboard central air source heat pump')

    assert hvac_sys is hvac_sys
    assert hvac_sys is not hvac_sys_dup
    assert hvac_sys == hvac_sys_dup
    hvac_sys.vintage = '90.1-2010'
    assert hvac_sys != hvac_sys_dup
    assert hvac_sys != hvac_sys_alt


def test_window_ac_multi_room():
    """Test that WindowAC systems can be assigned to multiple Rooms."""
    first_floor = Room.from_box('First_Floor', 10, 10, 3, origin=Point3D(0, 0, 0))
    second_floor = Room.from_box('Second_Floor', 10, 10, 3, origin=Point3D(0, 0, 3))
    hvac_sys = WindowAC('Test System')

    first_floor.properties.energy.hvac = hvac_sys
    second_floor.properties.energy.hvac = hvac_sys

    model = Model('Test_Bldg', [first_floor, second_floor])
    hvacs = model.properties.energy.hvacs
    assert len(hvacs) == 1
    assert hvacs[0] == hvac_sys

    model_dict = model.to_dict()
    assert len(model_dict['properties']['energy']['hvacs']) == 1
    assert model_dict['rooms'][0]['properties']['energy']['hvac'] == hvac_sys.identifier


def test_window_ac_dict_methods():
    """Test the to/from dict methods."""
    hvac_sys = WindowAC('High Efficiency HVAC System')
    hvac_sys.vintage = '90.1-2010'
    hvac_sys.equipment_type = 'Window AC with baseboard central air source heat pump'

    hvac_dict = hvac_sys.to_dict()
    new_hvac_sys = WindowAC.from_dict(hvac_dict)
    assert new_hvac_sys == hvac_sys
    assert hvac_dict == new_hvac_sys.to_dict()
