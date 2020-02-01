"""honeybee energy translation commands."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee.model import Model

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.run import to_openstudio_osw, run_osw

import sys
import os
import logging
import json

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee JSON files to/from OSM/IDF.')
def translate():
    pass

@translate.command('model-to-osm')
@click.argument('model-json')
@click.option('--sim-par-json', help='Optional Simulation Parameter JSON to be '
              'included as part of the tranlsated OSM.', default=None, show_default=True)
@click.option('--folder', help='Output folder.', default='.', show_default=True)
@click.option('--log-file', help='Optional log file to output the progress of the'
              'translation. By default the list will be printed out to stdout',
              type=click.File('w'), default='-')
def translate_model_to_osm(model_json, sim_par_json, folder, log_file):
    """Simulate a Model JSON file in EnergyPlus.
    \b
    Args:
        model_json: Full path to a Model JSON file.
        sim_par_json: Full path to a honeybee Energy SimulationParameter JSON
            that describes all of the settings for the simulation.
        folder: An optional folder on this computer, into which the IDF and result
            files will be written.
        log_file: Optional log file to output the progress of the translation.
            By default the list will be printed out to stdout.
    """
    try:
        # check that the model JSON is there
        assert os.path.isfile(model_json), \
            'No Model JSON file found at {}.'.format(model_json)
        
        # process the simulation parameters
        if sim_par_json is not None:
            assert os.path.isfile(sim_par_json), \
                'No simulation parameter file found at {}.'.format(sim_par_json)
    
        # Write the osw file to translate the model to osm
        log_file.write('Writing OSW for model translation.\n')
        osw = to_openstudio_osw(folder, model_json, sim_par_json)

        # run the measure to translate the model JSON to an openstudio measure
        log_file.write('Running OSW through OpenStudio CLI.\n')
        if os.path.isfile(osw):
            osm, idf = run_osw(osw)
            # run the resulting idf through EnergyPlus
            if os.path.isfile(idf):
                log_file.write('OpenStudio CLI Model translation successful.\n')
            else:
                raise Exception('Running OpenStudio CLI failed.')
        else:
            raise Exception('Writing OSW file failed.')
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)