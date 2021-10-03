# coding=utf-8
from honeybee_energy.shw import SHWSystem

from honeybee.altnumber import autocalculate

from .fixtures.userdata_fixtures import userdatadict


def test_shw_system_init():
    """Test the initialization of SHWSystem and basic properties."""
    default_shw = SHWSystem('Test System')
    str(default_shw)  # test the string representation

    assert default_shw.identifier == 'Test System'
    assert default_shw.equipment_type == 'Gas_WaterHeater'
    assert default_shw.heater_efficiency == 0.8
    assert default_shw.ambient_condition == 22
    assert default_shw.ambient_loss_coefficient == 6


def test_default_shw_system_setability(userdatadict):
    """Test the setting of properties of IdealAirSystem."""
    default_shw = SHWSystem('Test System')

    default_shw.identifier = 'Test System2'
    assert default_shw.identifier == 'Test System2'
    default_shw.equipment_type = 'Electric_WaterHeater'
    assert default_shw.equipment_type == 'Electric_WaterHeater'

    default_shw.heater_efficiency = 0.98
    assert default_shw.heater_efficiency == 0.98
    default_shw.heater_efficiency = autocalculate
    assert default_shw.heater_efficiency == 1.0

    default_shw.ambient_condition = 24
    assert default_shw.ambient_condition == 24
    default_shw.ambient_condition = 'Basement Room'
    assert default_shw.ambient_condition == 'Basement Room'

    default_shw.ambient_loss_coefficient = 5
    assert default_shw.ambient_loss_coefficient == 5

    default_shw.user_data = userdatadict
    assert default_shw.user_data == userdatadict


def test_default_shw_system_equality():
    """Test the equality of SHWSystem objects."""
    default_shw = SHWSystem('Test System')
    default_shw_dup = default_shw.duplicate()
    default_shw_alt = SHWSystem(
        'Test System', equipment_type='Electric_WaterHeater')

    assert default_shw is default_shw
    assert default_shw is not default_shw_dup
    assert default_shw == default_shw_dup
    default_shw_dup.heater_efficiency = 0.98
    assert default_shw != default_shw_dup
    assert default_shw != default_shw_alt


def test_default_shw_to_dict(userdatadict):
    """Test the to_dict method."""
    default_shw = SHWSystem('Passive House SHW System')

    default_shw.equipment_type = 'Electric_WaterHeater'
    default_shw.heater_efficiency = 0.98
    default_shw.ambient_condition = 24
    default_shw.ambient_loss_coefficient = 5

    default_shw_dict = default_shw.to_dict()

    assert default_shw_dict['equipment_type'] == 'Electric_WaterHeater'
    assert default_shw_dict['heater_efficiency'] == 0.98
    assert default_shw_dict['ambient_condition'] == 24
    assert default_shw_dict['ambient_loss_coefficient'] == 5


    """Test the to/from dict methods."""
    default_shw = SHWSystem('Passive House SHW System')
    default_shw.equipment_type = 'Electric_WaterHeater'
    default_shw.heater_efficiency = 0.98
    default_shw.ambient_condition = 24
    default_shw.ambient_loss_coefficient = 5

    shw_dict = default_shw.to_dict()
    new_default_shw = SHWSystem.from_dict(shw_dict)
    assert new_default_shw == default_shw
    assert shw_dict == new_default_shw.to_dict()
