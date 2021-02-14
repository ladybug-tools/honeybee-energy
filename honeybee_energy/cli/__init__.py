"""honeybee-energy commands which will be added to honeybee command line interface."""
import click
import sys
import logging
import json

from honeybee.cli import main
from ..config import folders
from .lib import lib
from .translate import translate
from .edit import edit
from .settings import settings
from .simulate import simulate
from .result import result
from .baseline import baseline
from .validate import validate

_logger = logging.getLogger(__name__)


# command group for all energy extension commands.
@click.group(help='honeybee energy commands.')
@click.version_option()
def energy():
    pass


@energy.command('config')
@click.option('--output-file', help='Optional file to output the JSON string of '
              'the config object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def config(output_file):
    """Get a JSON object with all configuration information"""
    try:
        config_dict = {
            'openstudio_path': folders.openstudio_path,
            'openstudio_exe': folders.openstudio_exe,
            'openstudio_version': folders.openstudio_version_str,
            'energyplus_path': folders.energyplus_path,
            'energyplus_exe': folders.energyplus_exe,
            'energyplus_version': folders.energyplus_version_str,
            'honeybee_openstudio_gem_path': folders.honeybee_openstudio_gem_path,
            'standards_data_folder': folders.standards_data_folder,
            'construction_lib': folders.construction_lib,
            'constructionset_lib': folders.constructionset_lib,
            'schedule_lib': folders.schedule_lib,
            'programtype_lib': folders.programtype_lib,
            'defaults_file': folders.defaults_file,
            'standards_extension_folders': folders.standards_extension_folders
        }
        output_file.write(json.dumps(config_dict, indent=4))
    except Exception as e:
        _logger.exception('Failed to retrieve configurations.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


# add sub-commands to energy
energy.add_command(lib)
energy.add_command(translate)
energy.add_command(edit)
energy.add_command(settings)
energy.add_command(simulate)
energy.add_command(result)
energy.add_command(baseline)
energy.add_command(validate)

# add energy sub-commands to honeybee CLI
main.add_command(energy)
