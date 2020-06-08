"""Test cli result module."""
from click.testing import CliRunner
from honeybee_energy.cli.result import data_by_output, data_by_outputs, \
    output_csv, zone_sizes, component_sizes
from honeybee_energy.result.sql import ZoneSize, ComponentSize
from ladybug.datacollection import HourlyContinuousCollection

import json


def test_data_by_output():
    """Test the data_by_output command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    result = runner.invoke(data_by_output, [sql_path, "Zone Lights Electric Energy"])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 7
    assert all(isinstance(HourlyContinuousCollection.from_dict(dc), HourlyContinuousCollection)
               for dc in data_list)

    out_names = [
        'Zone Ideal Loads Supply Air Total Cooling Energy',
        'Zone Ideal Loads Supply Air Total Heating Energy'
    ]
    result = runner.invoke(data_by_output, [sql_path, json.dumps(out_names)])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 14
    assert all(isinstance(HourlyContinuousCollection.from_dict(dc), HourlyContinuousCollection)
               for dc in data_list)

    result = runner.invoke(data_by_output, [sql_path, "Zone Lights Total Heating Energy"])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 0


def test_data_by_outputs():
    """Test the data_by_output command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    out_names1 = [
        'Zone Ideal Loads Supply Air Total Cooling Energy',
        'Zone Ideal Loads Supply Air Total Heating Energy'
    ]
    result = runner.invoke(data_by_outputs, [sql_path] + out_names1)
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 2
    assert len(data_list[0]) == 7
    assert all(isinstance(HourlyContinuousCollection.from_dict(dc), HourlyContinuousCollection)
               for dc in data_list[0])

    out_names2 = [
        'Zone Lights Total Heating Energy',
        'Chiller Electric Energy'
    ]
    result = runner.invoke(data_by_outputs, [sql_path] + out_names2)
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 2
    assert len(data_list[0]) == 0

    input_args = [sql_path, json.dumps(out_names1), json.dumps(out_names2)]
    result = runner.invoke(data_by_outputs, input_args)
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 2
    assert len(data_list[0]) == 14
    assert len(data_list[1]) == 0


def test_output_csv():
    """Test the output_csv command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    out_names = [
        'Zone Ideal Loads Supply Air Total Cooling Energy',
        'Zone Ideal Loads Supply Air Total Heating Energy'
    ]
    result = runner.invoke(output_csv, [sql_path] + out_names)
    assert result.exit_code == 0
    first_row = result.output.split('\n')[0]
    assert len(first_row.split(',')) == 15

    result = runner.invoke(output_csv, [sql_path, json.dumps(out_names)])
    assert result.exit_code == 0
    first_row = result.output.split('\n')[0]
    assert len(first_row.split(',')) == 15


def test_zone_sizes():
    """Test the zone_sizes command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    result = runner.invoke(zone_sizes, [sql_path])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list['cooling']) == 7
    assert len(data_list['heating']) == 7
    assert all(isinstance(ZoneSize.from_dict(sz), ZoneSize)
               for sz in data_list['cooling'])


def test_component_sizes():
    """Test the component_sizes command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    result = runner.invoke(component_sizes, [sql_path])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert all(isinstance(ComponentSize.from_dict(comp), ComponentSize)
               for comp in data_list)
