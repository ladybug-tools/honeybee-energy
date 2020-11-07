"""Test cli result module."""
from click.testing import CliRunner
from honeybee_energy.cli.result import data_by_output, available_results_info, \
    data_by_outputs, output_csv, zone_sizes, component_sizes, available_results, \
    available_run_period_info, all_available_info, output_csv_queryable, \
    tabular_data, tabular_metadata, load_balance
from honeybee_energy.result.sql import ZoneSize, ComponentSize
from ladybug.datacollection import HourlyContinuousCollection

import json
import os


def test_available_results():
    """Test the available_results command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    result = runner.invoke(available_results, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)

    assert len(all_output) == 8
    assert 'Zone Operative Temperature' in all_output
    assert 'Zone Lights Electric Energy' in all_output
    assert 'Zone Electric Equipment Electric Energy' in all_output
    assert 'Zone Air Relative Humidity' in all_output
    assert 'Zone Ideal Loads Supply Air Total Cooling Energy' in all_output
    assert 'Zone Mean Radiant Temperature' in all_output
    assert 'Zone Ideal Loads Supply Air Total Heating Energy' in all_output


def test_available_results_info():
    """Test the available_results_info command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'

    result = runner.invoke(available_results_info, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)

    assert len(all_output) == 8
    assert all(isinstance(obj, dict) for obj in all_output)
    for outp in all_output:
        if outp['output_name'] == 'Zone Mean Radiant Temperature':
            assert outp['object_type'] == 'Zone'
            assert outp['units'] == 'C'
            assert outp['units_ip'] == 'F'
            assert not outp['cumulative']


def test_available_run_period_info():
    """Test the available_results_info command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'
    result = runner.invoke(available_run_period_info, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)
    assert len(all_output) == 1
    assert all(isinstance(obj, dict) for obj in all_output)

    sql_path = './tests/result/eplusout_dday_runper.sql'
    result = runner.invoke(available_run_period_info, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)
    assert len(all_output) == 8
    assert all(isinstance(obj, dict) for obj in all_output)


def test_all_available_info():
    """Test the all_available_info command."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_hourly.sql'
    result = runner.invoke(all_available_info, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)
    assert len(all_output['outputs']) == 8
    assert all(isinstance(obj, dict) for obj in all_output['outputs'])
    assert len(all_output['run_periods']) == 1
    assert all(isinstance(obj, dict) for obj in all_output['run_periods'])

    sql_path = './tests/result/eplusout_dday_runper.sql'
    result = runner.invoke(all_available_info, [sql_path])
    assert result.exit_code == 0
    all_output = json.loads(result.output)
    assert len(all_output['outputs']) == 13
    assert all(isinstance(obj, dict) for obj in all_output['outputs'])
    assert len(all_output['run_periods']) == 8
    assert all(isinstance(obj, dict) for obj in all_output['run_periods'])


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


def test_tabular_data():
    """Test the tabular_data method."""
    runner = CliRunner()
    sql_path = './tests/result/eplusout_monthly.sql'

    result = runner.invoke(tabular_data, [sql_path, 'Utility Use Per Conditioned Floor Area'])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 4
    assert len(data_list[0]) == 6

    result = runner.invoke(tabular_metadata, [sql_path, 'Utility Use Per Conditioned Floor Area'])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list['row_names']) == 4
    assert len(data_list['column_names']) == 6
    assert 'Electricity Intensity' in data_list['column_names'][0]


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


def test_output_csv_queryable():
    """Test the output_csv_queryable command."""
    runner = CliRunner()
    sql_path = './tests/result/single_family_home_eplusout.sql'
    model_path = './tests/result/single_family_home.json'

    out_names = [
        'Zone Ideal Loads Supply Air Total Cooling Energy',
        'Zone Ideal Loads Supply Air Total Heating Energy',
        'Surface Inside Face Temperature',
        'Surface Outside Face Temperature'
    ]

    result = runner.invoke(output_csv_queryable,
                           [sql_path, model_path, 'RUN PERIOD 1'] + out_names)

    assert result.exit_code == 0
    col_names = json.loads(result.output)
    assert len(col_names['eplusout_room']) == 8
    assert len(col_names['eplusout_face']) == 8

    expected_room_file = './tests/result/eplusout_room.csv'
    expected_face_file = './tests/result/eplusout_face.csv'
    assert os.path.isfile(expected_room_file)
    assert os.path.isfile(expected_face_file)
    os.remove(expected_room_file)
    os.remove(expected_face_file)


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


def test_load_balance():
    """Test the load_balance method."""
    runner = CliRunner()
    model_json = './tests/result/triangulated/TriangleModel.json'
    sql_path = './tests/result/triangulated/eplusout.sql'

    result = runner.invoke(load_balance, [model_json, sql_path])
    assert result.exit_code == 0
    data_list = json.loads(result.output)
    assert len(data_list) == 11
