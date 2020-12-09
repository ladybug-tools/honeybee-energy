# coding=utf-8
from honeybee_energy.result.rdd import RDD
from honeybee_energy.result.zsz import ZSZ
from honeybee_energy.result.err import Err
from honeybee_energy.result.osw import OSW

from ladybug.datatype.power import Power
from ladybug.datatype.massflowrate import MassFlowRate
from ladybug.datacollection import HourlyContinuousCollection


def test_rdd_init():
    """Test the initialization of RDD and basic properties."""
    rdd_path = './tests/result/eplusout.rdd'
    rdd_obj = RDD(rdd_path)
    str(rdd_obj)  # test the string representation

    assert isinstance(rdd_obj.file_path, str)
    assert len(rdd_obj.output_names) == 461
    assert len(rdd_obj.filter_outputs_by_keywords(['Lights'])) == 27


def test_err_init():
    """Test the initialization of error files and basic properties."""
    err_path = './tests/result/eplusout_normal.err'
    err_obj = Err(err_path)
    str(err_obj)  # test the string representation

    assert isinstance(err_obj.file_path, str)
    assert isinstance(err_obj.file_contents, str)
    assert len(err_obj.warnings) == 23
    assert len(err_obj.severe_errors) == 0
    assert len(err_obj.fatal_errors) == 0


def test_err_severe():
    """Test the initialization of error files with severe errors."""
    err_path = './tests/result/eplusout_severe.err'
    err_obj = Err(err_path)
    str(err_obj)  # test the string representation

    assert isinstance(err_obj.file_path, str)
    assert isinstance(err_obj.file_contents, str)
    assert len(err_obj.warnings) == 0
    assert len(err_obj.severe_errors) == 4
    assert len(err_obj.fatal_errors) == 1


def test_zsz_init():
    """Test the properties and methods related to zone sizes."""
    zsz_obj = './tests/result/epluszsz.csv'
    zsz_obj = ZSZ(zsz_obj)

    assert zsz_obj.timestep == 6

    cool_sizes = zsz_obj.cooling_load_data
    heat_sizes = zsz_obj.heating_load_data
    cool_flows = zsz_obj.cooling_flow_data
    heat_flows = zsz_obj.heating_flow_data

    assert len(cool_sizes) == 7
    assert len(heat_sizes) == 7
    assert len(cool_flows) == 7
    assert len(heat_flows) == 7

    for size_obj in cool_sizes:
        assert isinstance(size_obj, HourlyContinuousCollection)
        assert isinstance(size_obj.header.metadata['Zone'], str)
        assert isinstance(size_obj.header.data_type, Power)
        assert size_obj.header.unit == 'W'

    for size_obj in cool_flows:
        assert isinstance(size_obj, HourlyContinuousCollection)
        assert isinstance(size_obj.header.metadata['Zone'], str)
        assert isinstance(size_obj.header.data_type, MassFlowRate)
        assert size_obj.header.unit == 'kg/s'


def test_osw():
    """Test the initialization of osw files with errors."""
    err_path = './tests/result/out.osw'
    osw_obj = OSW(err_path)
    str(osw_obj)  # test the string representation

    assert isinstance(osw_obj.file_path, str)
    assert isinstance(osw_obj.file_dict, dict)
    assert len(osw_obj.stdout) == 1
    assert len(osw_obj.warnings) == 0
    assert len(osw_obj.errors) == 1
    assert len(osw_obj.error_tracebacks) == 1
    assert 'Cannot create a surface with vertices' in osw_obj.stdout[0]
