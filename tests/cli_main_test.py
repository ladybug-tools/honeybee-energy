"""Test cli lib module."""
from click.testing import CliRunner
from honeybee_energy.cli import config

import json


def test_config():
    """Test the config command."""
    runner = CliRunner()

    result = runner.invoke(config)
    assert result.exit_code == 0
    config_dict = json.loads(result.output)
    assert len(config_dict) >= 12
