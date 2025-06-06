"""Test cli simulate module."""
from click.testing import CliRunner
from honeybee_energy.cli.simulate import simulate_model, simulate_osm, simulate_idf
from honeybee.config import folders
from ladybug.futil import nukedir

import os


def test_simulate_idf():
    runner = CliRunner()
    input_idf = './tests/idf/test_shoe_box.idf'
    input_epw = './tests/epw/chicago.epw'

    result = runner.invoke(simulate_idf, [input_idf, input_epw])
    assert result.exit_code == 0

    folder = os.path.join(folders.default_simulation_folder, 'test_shoe_box')
    output_sql = os.path.join(folder, 'eplusout.sql')
    assert os.path.isfile(output_sql)
    nukedir(folder)


def test_simulate_osm():
    runner = CliRunner()
    input_osm = './tests/osm/shoe_box.osm'
    input_epw = './tests/epw/chicago.epw'

    result = runner.invoke(simulate_osm, [input_osm, input_epw])
    assert result.exit_code == 0

    folder = os.path.join(folders.default_simulation_folder, 'shoe_box')
    output_sql = os.path.join(folder, 'eplusout.sql')
    assert os.path.isfile(output_sql)
    nukedir(folder)


def test_simulate_model():
    runner = CliRunner()
    input_model = './tests/json/ShoeBox.json'
    input_epw = './tests/epw/chicago.epw'
    input_ground = './tests/idf/monthly_ground.idf'

    in_args = [
        input_model, input_epw, '--additional-string',
        'Output:Variable, *, Surface Window System Solar Transmittance, Timestep;',
        '--additional-idf', input_ground
    ]

    result = runner.invoke(simulate_model, in_args)
    print(result.output)
    assert result.exit_code == 0

    folder = os.path.join(folders.default_simulation_folder, 'shoebox')
    output_sql = os.path.join(folder, 'openstudio', 'run', 'eplusout.sql')
    assert os.path.isfile(output_sql)
    nukedir(folder)


def test_simulate_model_with_osm():
    runner = CliRunner()
    input_model = './tests/osm/shoe_box.osm'
    input_epw = './tests/epw/chicago.epw'
    input_ground = './tests/idf/monthly_ground.idf'

    in_args = [
        input_model, input_epw, '--additional-string',
        'Output:Variable, *, Surface Window System Solar Transmittance, Timestep;',
        '--additional-idf', input_ground
    ]

    result = runner.invoke(simulate_model, in_args)
    print(result.output)
    assert result.exit_code == 0

    folder = os.path.join(folders.default_simulation_folder, 'shoe_box')
    output_sql = os.path.join(folder, 'openstudio', 'run', 'eplusout.sql')
    assert os.path.isfile(output_sql)
    nukedir(folder)
