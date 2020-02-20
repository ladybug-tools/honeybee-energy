# coding=utf-8
from honeybee_energy.result.sql import SQLiteResult

from ladybug.datatype.energy import Energy
from ladybug.datatype.temperature import Temperature
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

    assert isinstance(sql_obj.location, Location)
    assert sql_obj.location.latitude == 42.37
    assert isinstance(sql_obj.run_period, AnalysisPeriod)
    assert sql_obj.run_period.st_month == sql_obj.run_period.end_month == 1
    assert sql_obj.run_period.st_day == 6
    assert sql_obj.run_period.end_day == 12
    assert sql_obj.run_period.st_hour == 0
    assert sql_obj.run_period.end_hour == 23


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


def test_sqlite_data_collections_by_output_name_timestep():
    """Test the data_collections_by_output_name method with timestep values."""
    sql_path = './tests/result/eplusout_timestep.sql'
    sql_obj = SQLiteResult(sql_path)

    assert sql_obj.run_period.st_month == sql_obj.run_period.end_month == 1
    assert sql_obj.run_period.st_day == 6
    assert sql_obj.run_period.end_day == 12
    assert sql_obj.run_period.st_hour == 0
    assert sql_obj.run_period.end_hour == 23
    assert sql_obj.run_period.timestep == 6

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
