"""honeybee energy simulation running commands."""
import click
import sys
import os
import shutil
import logging
import json

from ladybug.futil import preparedir
from ladybug.epw import EPW
from ladybug.stat import STAT
from honeybee.model import Model
from honeybee.config import folders

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.run import to_openstudio_sim_folder, \
    run_osw, run_idf, output_energyplus_files, _parse_os_cli_failure, HB_OS_MSG
from honeybee_energy.result.err import Err

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
@click.option('--enforce-rooms/--skip-no-rooms', ' /-sr', help='Flag to note whether '
              'the simulation should be skipped if the Model has no Rooms and is '
              'therefore not simulate-able in EnergyPlus. Otherwise, this command '
              'will fail with an explicit error about the lack of rooms. Note that '
              'the input model must be a HBJSON in order for this to work correctly',
              default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (osw, osm, idf, sql, zsz, rdd, html, err) if successfully'
              ' created. By default the list will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def simulate_model(
    model_file, epw_file, sim_par_json, measures, additional_string, additional_idf,
    report_units, viz_variable, folder, enforce_rooms, log_file
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
        stat_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.stat'))

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

        sim_par = None
        if file_type == 'hbjson':
            if sim_par_json is None or not os.path.isfile(sim_par_json):
                sim_par = SimulationParameter()
                sim_par.output.add_zone_energy_use()
                sim_par.output.add_hvac_energy_use()
                sim_par.output.add_electricity_generation()
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
            if sim_par.sizing_parameter.climate_zone is None and \
                    os.path.isfile(stat_file):
                stat_obj = STAT(stat_file)
                sim_par.sizing_parameter.climate_zone = stat_obj.ashrae_climate_zone

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

        # Write the osw file to translate the model to osm
        strings_to_inject = additional_string if additional_string is not None else ''
        if additional_idf is not None and os.path.isfile(additional_idf):
            with open(additional_idf, "r") as add_idf_file:
                strings_to_inject = strings_to_inject + '\n' + add_idf_file.read()

        # run the Model re-serialization and convert to OSM, OSW, and IDF
        osm, osw, idf = None, None, None
        if file_type in ('hbjson', 'osm'):
            if file_type == 'hbjson':
                model = Model.from_hbjson(model_file)
                if not enforce_rooms and len(model.rooms) == 0:
                    sys.exit(0)
                    return None
            else:
                model = model_file
            osm, osw, idf = to_openstudio_sim_folder(
                model, folder, epw_file=epw_file, sim_par=sim_par, enforce_rooms=True,
                base_osw=base_osw, strings_to_inject=strings_to_inject,
                report_units=report_units, viz_variables=viz_variable,
                print_progress=True)
        else:
            idf = os.path.join(folder, 'in.idf')
            if os.path.normcase(model_file) == os.path.normcase(idf):
                shutil.copy(model_file, idf)

        # run the simulation
        sql = None
        if idf is not None:  # run the IDF directly through E+
            gen_files = [idf] if osm is None else [osm, idf]
            sql, zsz, rdd, html, err = run_idf(idf, epw_file)
            if err is not None and os.path.isfile(err):
                gen_files.extend([sql, zsz, rdd, html, err])
            else:
                raise Exception('Running EnergyPlus failed.')
        else:  # run the whole simulation with the OpenStudio CLI
            gen_files = [osw]
            osm, idf = run_osw(osw, measures_only=False)
            if idf is not None and os.path.isfile(idf):
                gen_files.extend([osm, idf])
            else:
                _parse_os_cli_failure(folder)
            sql, zsz, rdd, html, err = output_energyplus_files(os.path.dirname(idf))
            if os.path.isfile(err):
                gen_files.extend([sql, zsz, rdd, html, err])
            else:
                raise Exception('Running EnergyPlus failed.')

        # parse the error log and report any warnings
        err_obj = Err(err)
        for error in err_obj.fatal_errors:
            log_file.write(err_obj.file_contents)  # log before raising the error
            raise Exception(error)
        if sql is not None and os.path.isfile('{}-journal'.format(sql)):
            try:  # try to finish E+'s cleanup
                os.remove('{}-journal'.format(sql))
            except Exception:  # maybe the file is inaccessible
                pass
        log_file.write(json.dumps(gen_files, indent=4))
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
        # check that honeybee-openstudio is installed
        try:
            from honeybee_openstudio.openstudio import openstudio, OSModel
            from honeybee_openstudio.simulation import assign_epw_to_model
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))

        # set the default folder to the default if it's not specified and copy the OSM
        if folder is None:
            proj_name = os.path.basename(osm_file).replace('.osm', '')
            folder = os.path.join(folders.default_simulation_folder, proj_name)
        preparedir(folder, remove_content=False)
        idf = os.path.abspath(os.path.join(folder, 'in.idf'))

        # load the OSM and translate it to IDF
        exist_os_model = OSModel.load(osm_file)
        if exist_os_model.is_initialized():
            os_model = exist_os_model.get()
        assign_epw_to_model(epw_file, os_model)
        idf_translator = openstudio.energyplus.ForwardTranslator()
        workspace = idf_translator.translateModel(os_model)
        workspace.save(idf, overwrite=True)

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

        # parse the error log and report any warnings
        if sql is not None and os.path.isfile('{}-journal'.format(sql)):
            try:  # try to finish E+'s cleanup
                os.remove('{}-journal'.format(sql))
            except Exception:  # maybe the file is inaccessible
                pass
        log_file.write(json.dumps(gen_files, indent=4))
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

        # parse the error log and report any warnings
        if sql is not None and os.path.isfile('{}-journal'.format(sql)):
            try:  # try to finish E+'s cleanup
                os.remove('{}-journal'.format(sql))
            except Exception:  # maybe the file is inaccessible
                pass
        log_file.write(json.dumps(gen_files, indent=4))
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
