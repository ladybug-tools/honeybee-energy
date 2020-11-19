"""Test the validate group."""
import sys

from click.testing import CliRunner
from honeybee_energy.cli.validate import validate_sim_par


def test_validate_model_basic():
    input_sim_par = './tests/json/simulation_par_detailed.json'
    if (sys.version_info >= (3, 7)):
        runner = CliRunner()
        result = runner.invoke(validate_sim_par, [input_sim_par])
        assert result.exit_code == 0
