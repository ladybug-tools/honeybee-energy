"""Commands to set honeybee-energy configurations."""
import click
import sys
import logging
import json

from honeybee_energy.config import folders

_logger = logging.getLogger(__name__)


@click.group(help='Commands to set honeybee-energy configurations.')
def set_config():
    pass


@set_config.command('energyplus-path')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def energyplus_path(folder_path):
    """Set the energyplus-path configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the energyplus-path.
            If unspecified, the energyplus-path will be set back to
            the default.
    """
    _set_config_variable(folder_path, 'energyplus_path')


@set_config.command('openstudio-path')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def openstudio_path(folder_path):
    """Set the openstudio-path configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the openstudio-path. This is
            the "bin" directory for OpenStudio installation (the one that contains
            the openstudio executable file). If unspecified, the openstudio-path
            will be set back to the default.
    """
    _set_config_variable(folder_path, 'openstudio_path')


@set_config.command('lbt-measures-path')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def lbt_measures_path(folder_path):
    """Set the lbt-measures-path configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the lbt-measures-path.
            If unspecified, the lbt-measures-path will be set back to
            the default.
    """
    _set_config_variable(folder_path, 'lbt_measures_path')


@set_config.command('honeybee-openstudio-gem-path')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def honeybee_openstudio_gem_path(folder_path):
    """Set the honeybee-openstudio-gem-path configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the honeybee-openstudio-gem-path.
            If unspecified, the honeybee-openstudio-gem-path will be set back to
            the default.
    """
    _set_config_variable(folder_path, 'honeybee_openstudio_gem_path')


@set_config.command('standards-data-folder')
@click.argument('folder-path', required=False, type=click.Path(
    exists=True, file_okay=False, dir_okay=True, resolve_path=True))
def standards_data_folder(folder_path):
    """Set the standards-data-folder configuration variable.

    \b
    Args:
        folder_path: Path to a folder to be set as the standards-data-folder.
            If unspecified, the standards-data-folder will be set back to
            the default.
    """
    _set_config_variable(folder_path, 'standards_data_folder')


def _set_config_variable(folder_path, variable_name):
    var_cli_name = variable_name.replace('_', '-')
    try:
        config_file = folders.config_file
        with open(config_file) as inf:
            data = json.load(inf)
        data[variable_name] = folder_path if folder_path is not None else ''
        with open(config_file, 'w') as fp:
            json.dump(data, fp, indent=4)
        msg_end = 'reset to default' if folder_path is None \
            else 'set to: {}'.format(folder_path)
        print('{} successfully {}.'.format(var_cli_name, msg_end))
    except Exception as e:
        _logger.exception('Failed to set {}.\n{}'.format(var_cli_name, e))
        sys.exit(1)
    else:
        sys.exit(0)
