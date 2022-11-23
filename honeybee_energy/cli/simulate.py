"""honeybee energy simulation running commands."""
import click
import sys
import os
import shutil
import logging
import json

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.run import measure_compatible_model_json, to_openstudio_osw, \
    run_osw, run_idf, output_energyplus_files, _parse_os_cli_failure
from honeybee_energy.result.err import Err
from honeybee.config import folders
from ladybug.futil import preparedir
from ladybug.epw import EPW

_logger = logging.getLogger(__name__)


@click.group(help='Commands for simulating Honeybee JSON files in EnergyPlus.')
def simulate():
    pass


@simulate.command('model')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('epw-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for '
              'the simulation. This will be ignored if the input model-file is '
              'an OSM or IDF.', default=None, show_default=True,
              type=click.Path(exists=False, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--measures', '-m', help='Full path to a folder containing an OSW JSON '
              'be used as the base for the execution of the OpenStudio CLI. While this '
              'OSW can contain paths to measures that exist anywhere on the machine, '
              'the best practice is to copy the measures into this measures '
              'folder and use relative paths within the OSW. '
              'This makes it easier to move the inputs for this command from one '
              'machine to another.', default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--additional-string', '-as', help='An additional IDF text string to get '
              'appended to the IDF before simulation. The input should include '
              'complete EnergyPlus objects as a single string following the IDF '
              'format. This input can be used to include small EnergyPlus objects that '
              'are not currently supported by honeybee.', default=None, type=str)
@click.option('--additional-idf', '-ai', help='An IDF file with text to be '
              'appended before simulation. This input can be used to include '
              'large EnergyPlus objects that are not currently supported by honeybee.',
              default=None, show_default=True,
              type=click.Path(exists=False, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--report-units', '-r', help='A text value to set the units of the '
              'OpenStudio Results report that this command can output. Choose from the '
              'following:\nnone - no results report will be produced\nsi - all units '
              'will be in SI\nip - all units will be in IP.',
              type=str, default='none', show_default=True)
@click.option('--viz-variable', '-v', help='Text for an EnergyPlus output variable to '
              'be visualized on the geometry in an output view_data HTML report. '
              'If unspecified, no view_data report is produced. Multiple variables '
              'can be requested by using multiple -v options. For example\n'
              ' -v "Zone Air System Sensible Heating Rate" -v "Zone Air System '
              'Sensible Cooling Rate"',
              type=str, default=None, show_default=True, multiple=True)
@click.option('--folder', '-f', help='Folder on this computer, into which the IDF '
              'and result files will be written. If None, the files will be output '
              'to the honeybee default simulation folder and placed in a project '
              'folder with the same name as the model-file.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether '
              'the Model should be re-serialized to Python and checked before it '
              'is translated to .osm. The check is not needed if the model-file '
              'was exported directly from the honeybee-energy Python library. '
              'It will be automatically bypassed if the model-file is an OSM or IDF.',
              default=True, show_default=True)
@click.option('--enforce-rooms/--skip-no-rooms', ' /-sr', help='Flag to note whether '
              'the simulation should be skipped if the Model has no Rooms and is '
              'therefore not simulate-able in EnergyPlus. Otherwise, this command '
              'will fail with an explicit error about the lack of rooms. Note that '
              'the input model must be a HBJSON and you must NOT --bypass-check in '
              'order for this to work correctly', default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (osw, osm, idf, sql, zsz, rdd, html, err) if successfully'
              ' created. By default the list will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def simulate_model(
    model_file, epw_file, sim_par_json, measures, additional_string, additional_idf,
    report_units, viz_variable, folder, check_model, enforce_rooms, log_file
):
    """Simulate a Model in EnergyPlus.

    \b
    Args:
        model_file: Full path to a Model file as either a HBJSON, OSM, or IDF.
        epw_file: Full path to an .epw file.
    """
    try:
        # get a ddy variable that might get used later
        epw_folder, epw_file_name = os.path.split(epw_file)
        ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))

        # sense what type of file has been input
        file_type = _sense_input_file_type(model_file)
        proj_name = os.path.basename(model_file).lower()

        # set the default folder to the default if it's not specified
        if folder is None:
            for ext in ('.hbjson', '.json', '.osm', '.idf'):
                proj_name = proj_name.replace(ext, '')
            folder = os.path.join(folders.default_simulation_folder, proj_name)
            folder = os.path.join(folder, 'energyplus', 'run') if file_type == 'idf' \
                else os.path.join(folder, 'openstudio')
        elif file_type == 'idf':  # ensure that all of the files end up in the same dir
            folder = os.path.join(folder, 'run')
        preparedir(folder, remove_content=False)

        # process the simulation parameters and write new ones if necessary
        def ddy_from_epw(epw_file, sim_par):
            """Produce a DDY from an EPW file."""
            epw_obj = EPW(epw_file)
            des_days = [epw_obj.approximate_design_day('WinterDesignDay'),
                        epw_obj.approximate_design_day('SummerDesignDay')]
            sim_par.sizing_parameter.design_days = des_days

        def write_sim_par(sim_par):
            """Write simulation parameter object to a JSON."""
            sim_par_dict = sim_par.to_dict()
            sp_json = os.path.abspath(os.path.join(folder, 'simulation_parameter.json'))
            with open(sp_json, 'w') as fp:
                json.dump(sim_par_dict, fp)
            return sp_json

        if file_type == 'hbjson':
            if sim_par_json is None or not os.path.isfile(sim_par_json):
                sim_par = SimulationParameter()
                sim_par.output.add_zone_energy_use()
                sim_par.output.add_hvac_energy_use()
                sim_par.output.reporting_frequency = 'Monthly'
            else:
                with open(sim_par_json) as json_file:
                    data = json.load(json_file)
                sim_par = SimulationParameter.from_dict(data)
            if len(sim_par.sizing_parameter.design_days) == 0 and \
                    os.path.isfile(ddy_file):
                try:
                    sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)
                except AssertionError:  # no design days within the DDY file
                    ddy_from_epw(epw_file, sim_par)
            elif len(sim_par.sizing_parameter.design_days) == 0:
                ddy_from_epw(epw_file, sim_par)
            sim_par_json = write_sim_par(sim_par)
        else:
            sim_par_json = None

        # process the measures input if it is specified
        base_osw = None
        if measures is not None and measures != '' and os.path.isdir(measures):
            for f_name in os.listdir(measures):
                if f_name.lower().endswith('.osw'):
                    base_osw = os.path.join(measures, f_name)
                    # write the path of the measures folder into the OSW
                    with open(base_osw) as json_file:
                        osw_dict = json.load(json_file)
                    osw_dict['measure_paths'] = [os.path.abspath(measures)]
                    with open(base_osw, 'w') as fp:
                        json.dump(osw_dict, fp)
                    break

        # run the Model re-serialization and check if specified
        if check_model and file_type == 'hbjson':
            try:
                model_file = measure_compatible_model_json(
                    model_file, folder, enforce_rooms=True)
            except AssertionError as e:
                if not enforce_rooms and 'Model contains no Rooms' in str(e):
                    sys.exit(0)
                    return None
                else:
                    raise AssertionError(e)

        # Write the osw file to translate the model to osm
        no_report = True if base_osw is None and report_units.lower() == 'none' and \
            (len(viz_variable) == 0 or viz_variable[0] == '') else False
        strings_to_inject = additional_string if additional_string is not None else ''
        if additional_idf is not None and os.path.isfile(additional_idf):
            with open(additional_idf, "r") as add_idf_file:
                strings_to_inject = strings_to_inject + '\n' + add_idf_file.read()
        after_str_to_inject = None
        if no_report and strings_to_inject != '':
            after_str_to_inject = strings_to_inject
            strings_to_inject = ''
        if file_type != 'idf':
            if file_type == 'osm' and not proj_name.endswith('.osm'):
                new_model = os.path.join(folder, 'in.osm')
                shutil.copy(model_file, new_model)
                model_file = new_model
            osw = to_openstudio_osw(
                folder, model_file, sim_par_json, base_osw=base_osw, epw_file=epw_file,
                strings_to_inject=strings_to_inject, report_units=report_units,
                viz_variables=viz_variable)
            gen_files = [osw]

        # run the simulation
        if file_type == 'idf':
            idf = os.path.join(folder, 'in.idf')
            shutil.copy(model_file, idf)
            gen_files = [idf]
            sql, eio, rdd, html, err = run_idf(idf, epw_file)
            if err is not None and os.path.isfile(err):
                gen_files.extend([sql, eio, rdd, html, err])
            else:
                raise Exception('Running EnergyPlus failed.')
        elif no_report:  # separate the OS CLI run from the E+ run
            osm, idf = run_osw(osw)
            # run the resulting idf through EnergyPlus
            if idf is not None and os.path.isfile(idf):
                # process the additional string if specified
                if after_str_to_inject is not None:
                    with open(idf, "a") as idf_file:
                        idf_file.write(after_str_to_inject)
                gen_files.extend([osm, idf])
                sql, eio, rdd, html, err = run_idf(idf, epw_file)
                if err is not None and os.path.isfile(err):
                    gen_files.extend([sql, eio, rdd, html, err])
                else:
                    raise Exception('Running EnergyPlus failed.')
            else:
                _parse_os_cli_failure(folder)
        else:  # run the whole simulation with the OpenStudio CLI
            osm, idf = run_osw(osw, measures_only=False)
            if idf is not None and os.path.isfile(idf):
                gen_files.extend([osm, idf])
            else:
                _parse_os_cli_failure(folder)
            sql, eio, rdd, html, err = output_energyplus_files(os.path.dirname(idf))
            if os.path.isfile(err):
                gen_files.extend([sql, eio, rdd, html, err])
            else:
                raise Exception('Running EnergyPlus failed.')
        log_file.write(json.dumps(gen_files))
    except Exception as e:
        _logger.exception('Model simulation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@simulate.command('osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('epw-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--folder', '-f', help='Folder on this computer, into which the '
              'result files will be written. If None, the files will be output '
              'to the honeybee default simulation folder and placed in a project '
              'folder with the same name as the idf_file.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (osw, osm, idf, sql, zsz, rdd, html, err) if successfully'
              ' created. By default the list will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def simulate_osm(osm_file, epw_file, folder, log_file):
    """Simulate an OSM file in EnergyPlus.

    \b
    Args:
        osm_file: Full path to a simulate-able .osm file.
        epw_file: Full path to an .epw file.
    """
    try:
        # set the default folder to the default if it's not specified and copy the IDF
        if folder is None:
            proj_name = os.path.basename(osm_file).replace('.osm', '')
            folder = os.path.join(folders.default_simulation_folder, proj_name)
        preparedir(folder, remove_content=False)
        base_osm = os.path.join(folder, 'in.osm')
        shutil.copy(osm_file, base_osm)

        # create a blank osw for the translation
        osw_dict = {
            'seed_file': osm_file,
            'weather_file': epw_file
        }
        osw = os.path.join(folder, 'workflow.osw')
        with open(osw, 'w') as fp:
            json.dump(osw_dict, fp, indent=4)

        # run the OSW through OpenStudio CLI
        osm, idf = run_osw(osw)

        # run the file through EnergyPlus
        if idf is not None and os.path.isfile(idf):
            gen_files = [osw, osm, idf]
            sql, eio, rdd, html, err = run_idf(idf, epw_file)
            if err is not None and os.path.isfile(err):
                gen_files.extend([sql, eio, rdd, html, err])
                err_obj = Err(err)
                for error in err_obj.fatal_errors:
                    log_file.write(err_obj.file_contents)  # log before raising the error
                    raise Exception(error)
            else:
                raise Exception('Running EnergyPlus failed.')
        else:
            _parse_os_cli_failure(folder)
        log_file.write(json.dumps(gen_files))
    except Exception as e:
        _logger.exception('OSM simulation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@simulate.command('idf')
@click.argument('idf-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('epw-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--folder', '-f', help='Folder on this computer, into which the '
              'result files will be written. If None, the files will be output '
              'to the honeybee default simulation folder and placed in a project '
              'folder with the same name as the idf_file.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (idf, sql, zsz, rdd, html, err) if successfully'
              ' created. By default the list will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def simulate_idf(idf_file, epw_file, folder, log_file):
    """Simulate an IDF file in EnergyPlus.

    \b
    Args:
        idf_file: Full path to a simulate-able .idf file.
        epw_file: Full path to an .epw file.
    """
    try:
        # set the default folder to the default if it's not specified and copy the IDF
        if folder is None:
            proj_name = os.path.basename(idf_file).replace('.idf', '')
            folder = os.path.join(folders.default_simulation_folder, proj_name)
        preparedir(folder, remove_content=False)
        idf = os.path.join(folder, 'in.idf')
        shutil.copy(idf_file, idf)

        # run the file through EnergyPlus
        gen_files = [idf]
        sql, eio, rdd, html, err = run_idf(idf, epw_file)
        if err is not None and os.path.isfile(err):
            gen_files.extend([sql, eio, rdd, html, err])
            err_obj = Err(err)
            for error in err_obj.fatal_errors:
                log_file.write(err_obj.file_contents)  # log before raising the error
                raise Exception(error)
        else:
            raise Exception('Running EnergyPlus failed.')
        log_file.write(json.dumps(gen_files))
    except Exception as e:
        _logger.exception('IDF simulation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def _sense_input_file_type(model_file):
    """Sense whether an input model_file is a HBJSON, OSM, or IDF.

    Args:
        model_file: A file, which will have its contents evaluated to determine
            the file type.
    """
    # sense the file type from the first character to avoid maxing memory with JSON
    # this is needed since queenbee overwrites all file extensions
    with open(model_file) as inf:
        first_char = inf.read(1)
    if first_char == '{':
        return 'hbjson'
    with open(model_file) as inf:
        inf.readline()
        second_line = inf.readline()
    if 'OS:Version,' in second_line:
        return 'osm'
    return 'idf'
