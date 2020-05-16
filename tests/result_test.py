# coding=utf-8
from honeybee_energy.result.sql import SQLiteResult, ZoneSize, ComponentSize
from honeybee_energy.result.rdd import RDD
from honeybee_energy.result.zsz import ZSZ
from honeybee_energy.result.err import Err

from ladybug.datatype.energy import Energy
from ladybug.datatype.temperature import Temperature
from ladybug.datatype.power import Power
from ladybug.datatype.massflowrate import MassFlowRate
from ladybug.dt import DateTime
from ladybug.location import Location
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datacollection import HourlyContinuousCollection, DailyCollection, \
    MonthlyCollection

import pytest


def test_sqlite_init():
    """Test the initialization of SQLiteResult and basic properties."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)
    str(sql_obj)  # test the string representation

    assert isinstance(sql_obj.file_path, str)
    assert isinstance(sql_obj.location, Location)
    assert sql_obj.location.latitude == 42.37


def test_sqlite_zone_sizing():
    """Test the properties and methods related to zone sizes."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    cool_sizes = sql_obj.zone_cooling_sizes
    heat_sizes = sql_obj.zone_heating_sizes

    assert len(cool_sizes) == 7
    assert len(heat_sizes) == 7

    for size_obj in cool_sizes:
        assert isinstance(size_obj, ZoneSize)
        assert isinstance(size_obj.zone_name, str)
        assert size_obj.load_type == 'Cooling'
        assert isinstance(size_obj.calculated_design_load, float)
        assert isinstance(size_obj.final_design_load, float)
        assert isinstance(size_obj.calculated_design_flow, float)
        assert isinstance(size_obj.final_design_flow, float)
        assert size_obj.design_day_name == 'BOSTON LOGAN INTL ARPT ANN CLG .4% CONDNS DB=>MWB'
        assert isinstance(size_obj.peak_date_time, DateTime)
        assert isinstance(size_obj.peak_temperature, float)
        assert isinstance(size_obj.peak_humidity_ratio, float)
        assert isinstance(size_obj.peak_outdoor_air_flow, float)
    
    for size_obj in heat_sizes:
        assert size_obj.load_type == 'Heating'
        assert size_obj.design_day_name == 'BOSTON LOGAN INTL ARPT ANN HTG 99.6% CONDNS DB'


def test_sqlite_component_sizing():
    """Test the properties and methods related to component sizes."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    comp_sizes = sql_obj.component_sizes
    comp_size_type = sql_obj.component_sizes_by_type('ZoneHVAC:IdealLoadsAirSystem')
    comp_types = sql_obj.component_types

    assert len(comp_sizes) == 7
    assert len(comp_size_type) == 7
    assert comp_types == ['ZoneHVAC:IdealLoadsAirSystem']

    for size_obj in comp_sizes:
        assert isinstance(size_obj, ComponentSize)
        assert size_obj.component_type == 'ZoneHVAC:IdealLoadsAirSystem'
        assert isinstance(size_obj.component_name, str)
        assert all(isinstance(desc, str) for desc in size_obj.descriptions)
        assert all(isinstance(prop, str) for prop in size_obj.properties)
        assert all(isinstance(val, float) for val in size_obj.values)
        assert all(isinstance(unit, str) for unit in size_obj.units)
        assert isinstance(size_obj.properties_dict, dict)
        assert len(size_obj.properties_dict) == 4


def test_sqlite_data_collections_by_output_name():
    """Test the data_collections_by_output_name method."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 7
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Mean Radiant Temperature')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Temperature)
        assert coll.header.unit == 'C'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Electric Equipment Electric Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Mean Air Temperature')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Air Relative Humidity')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Heating Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Cooling Energy')


def test_sqlite_data_collections_by_output_name_single():
    """Test the data_collections_by_output_name method with a single data."""
    sql_path = './tests/result/eplusout_openstudio_error.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    assert len(data_colls) == 1
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'


def test_sqlite_data_collections_by_output_names():
    """Test the data_collections_by_output_name method with multiple names."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        ('Zone Lights Electric Energy', 'Zone Mean Radiant Temperature'))
    assert len(data_colls) == 14
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, (Energy, Temperature))


def test_sqlite_data_collections_by_output_name_openstudio():
    """Test the data_collections_by_output_name method with openstudio values."""
    sql_path = './tests/result/eplusout_openstudio.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == len(coll.header.analysis_period.hoys)
        assert isinstance(coll.header.data_type, Energy)
        assert coll.header.unit == 'kWh'

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Electric Equipment Electric Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Heating Energy')
    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Ideal Loads Supply Air Total Cooling Energy')


def test_sqlite_data_collections_by_output_name_timestep():
    """Test the data_collections_by_output_name method with timestep values."""
    sql_path = './tests/result/eplusout_timestep.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, HourlyContinuousCollection)
        assert len(coll) == 7 * 24 * 6


def test_sqlite_data_collections_by_output_name_daily():
    """Test the data_collections_by_output_name method with daily values."""
    sql_path = './tests/result/eplusout_daily.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, DailyCollection)
        assert coll.header.analysis_period.is_annual
        assert len(coll) == 365


def test_sqlite_data_collections_by_output_name_monthly():
    """Test the data_collections_by_output_name method with monthly values."""
    sql_path = './tests/result/eplusout_monthly.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    for coll in data_colls:
        assert isinstance(coll, MonthlyCollection)
        print (coll.header.analysis_period)
        assert coll.header.analysis_period.is_annual
        assert len(coll) == 12


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
