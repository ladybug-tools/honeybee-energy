"""honeybee energy simulation running commands."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee.model import Model

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.run import measure_compatible_model_json, to_openstudio_osw, \
    run_osw, run_idf

import sys
import os
import logging
import json

_logger = logging.getLogger(__name__)


@click.group(help='Commands for simulating Honeybee JSON files in EnergyPlus.')
def simulate():
    pass

@simulate.command('model')
@click.argument('model-json')
@click.argument('epw-file')
@click.option('--sim-par-json', help='Simulation Parameter JSON to decribe the type '
              'of simulation to run. If None, an annual simulation will be run.',
              default=None, show_default=True)
@click.option('--folder', help='Output folder.', default=None, show_default=True)
@click.option('--check-model', help='Boolean to note whether the Model should be '
              're-serialized to Python and checked before it is translated to .osm. ',
              default=True, show_default=True)
@click.option('--log-file', help='Optional log file to output the progress of the'
              'translation. By default the list will be printed out to stdout',
              type=click.File('w'), default='-')
def simulate_model(model_json, epw_file, sim_par_json, folder, check_model, log_file):
    """Simulate a Model JSON file in EnergyPlus.
    \b
    Args:
        model_json: Full path to a Model JSON file.
        epw_file: Full path to an .epw file.
        sim_par_json: Full path to a honeybee Energy SimulationParameter JSON
            that describes all of the settings for the simulation. If None,
            some default simulation parameters will automatically be used.
        folder: An optional folder on this computer, into which the IDF and result
            files will be written. If None, the files will be output in the
            same location as the model_json. Defaut: None.
        check_model: Boolean to note whether the Model should be re-serialized to
            Python and checked before it is translated to .osm.
        log_file: Optional log file to output the progress of the translation.
            By default the list will be printed out to stdout.
    """
    try:
        # check that the model JSON and the EPW file is there
        assert os.path.isfile(model_json), \
            'No Model JSON file found at {}.'.format(model_json)
        assert os.path.isfile(epw_file), \
            'No EPW file found at {}.'.format(epw_file)

        # set the default folder if it's not specified
        if folder is None:
            folder = os.path.split(model_json)[0]

        # process the simulation parameters
        if sim_par_json is None:  # generate some default simulation parameters
            sim_par = SimulationParameter()
            sim_par.output.add_zone_energy_use()
            epw_folder, epw_file_name = os.path.split(epw_file)
            ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))
            if os.path.isfile(ddy_file):
                sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)
            # write out the simulation parameters to a JSON
            sim_par_dict = sim_par.to_dict()
            sim_par_json = os.path.abspath(
                os.path.join(folder, 'simulation_parameter.json'))
            with open(sim_par_json, 'w') as fp:
                json.dump(sim_par_dict, fp)
            log_file.write('Default SimulationParameters were auto-generated.\n')
        else:
            assert os.path.isfile(sim_par_json), \
                'No simulation parameter file found at {}.'.format(sim_par_json)
    
        # run the Model re-serialzation and check if specified
        if check_model:
            log_file.write('Checking and re-serailizing model JSON.\n')
            model_json = measure_compatible_model_json(model_json, folder)
            log_file.write('Model check complete.\n')

        # Write the osw file to translate the model to osm
        log_file.write('Writing OSW for model translation.\n')
        osw = to_openstudio_osw(folder, model_json, sim_par_json, epw_file)

        # run the measure to translate the model JSON to an openstudio measure
        log_file.write('Running OSW through OpenStudio CLI.\n')
        if os.path.isfile(osw):
            osm, idf = run_osw(osw)
            # run the resulting idf through EnergyPlus
            if os.path.isfile(idf):
                log_file.write('OpenStudio CLI Model translation successful.\n')
                log_file.write('Running IDF file through EnergyPlus.\n')
                sql, eio, rdd, html, err = run_idf(idf, epw_file)
                if os.path.isfile(err):
                    log_file.write('EnergyPlus simulation successful.\n')
                else:
                    raise Exception('Running EnergyPlus failed.')
            else:
                raise Exception('Running OpenStudio CLI failed.')
        else:
            raise Exception('Writing OSW file failed.')
    except Exception as e:
        _logger.exception('Model simulation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
