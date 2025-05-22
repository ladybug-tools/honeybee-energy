"""honeybee energy translation commands."""
import click
import sys
import os
import logging
import json
import tempfile

from ladybug.commandutil import process_content_to_output
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.epw import EPW
from ladybug.stat import STAT
from ladybug.futil import preparedir
from honeybee.model import Model
from honeybee.typing import clean_rad_string
from honeybee.config import folders as hb_folders

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.construction.dictutil import dict_to_construction
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.schedule.dictutil import dict_to_schedule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.run import to_openstudio_sim_folder, run_osw, from_osm_osw, \
    _parse_os_cli_failure, HB_OS_MSG
from honeybee_energy.writer import energyplus_idf_version, _preprocess_model_for_trace
from honeybee_energy.config import folders

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee Models files.')
def translate():
    pass


@translate.command('model-to-sim-folder')
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
@click.option('--folder', '-f', help='Folder on this computer, into which the IDF '
              'and result files will be written. If None, the files will be output '
              'to the honeybee default simulation folder and placed in a project '
              'folder with the same name as the model-file.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--log-file', '-log', help='Optional log file to output the paths of the '
              'generated files (osw, osm, idf) if successfully'
              ' created. By default the list will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_sim_folder(
    model_file, epw_file, sim_par_json, measures, additional_string, additional_idf,
    folder, log_file
):
    """Simulate a Model in EnergyPlus.

    \b
    Args:
        model_file: Full path to a Model file as a HBJSON or HBPkl.
        epw_file: Full path to an .epw file.
    """
    try:
        # get a ddy variable that might get used later
        epw_folder, epw_file_name = os.path.split(epw_file)
        ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))
        stat_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.stat'))

        # sense what type of file has been input
        proj_name = os.path.basename(model_file).lower()

        # set the default folder to the default if it's not specified
        if folder is None:
            for ext in ('.hbjson', '.json', '.hbpkl', '.pkl'):
                proj_name = proj_name.replace(ext, '')
            folder = os.path.join(folders.default_simulation_folder, proj_name)
            folder = os.path.join(folder, 'openstudio')
        preparedir(folder, remove_content=False)

        # process the simulation parameters and write new ones if necessary
        def ddy_from_epw(epw_file, sim_par):
            """Produce a DDY from an EPW file."""
            epw_obj = EPW(epw_file)
            des_days = [epw_obj.approximate_design_day('WinterDesignDay'),
                        epw_obj.approximate_design_day('SummerDesignDay')]
            sim_par.sizing_parameter.design_days = des_days

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
        model = Model.from_file(model_file)
        osm, osw, idf = to_openstudio_sim_folder(
            model, folder, epw_file=epw_file, sim_par=sim_par, enforce_rooms=True,
            base_osw=base_osw, strings_to_inject=strings_to_inject,
            print_progress=True)
        gen_files = [osm]
        if osw is not None:
            gen_files.append(osw)
        if idf is not None:
            gen_files.append(idf)

        log_file.write(json.dumps(gen_files, indent=4))
    except Exception as e:
        _logger.exception('Model simulation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-to-osm')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for '
              'the simulation. If None default parameters will be generated.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--epw-file', '-epw', help='Full path to an EPW file to be associated '
              'with the exported OSM. This is typically not necessary but may be '
              'used when a sim-par-json is specified that requests a HVAC sizing '
              'calculation to be run as part of the translation process but no design '
              'days are inside this simulation parameter.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--folder', '-f', help='Deprecated input that is no longer used.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--osm-file', '-osm', help='Optional path where the OSM will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--idf-file', '-idf', help='Optional path where the IDF will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--geometry-ids/--geometry-names', ' /-gn', help='Flag to note whether a '
              'cleaned version of all geometry display names should be used instead '
              'of identifiers when translating the Model to OSM and IDF. '
              'Using this flag will affect all Rooms, Faces, Apertures, '
              'Doors, and Shades. It will generally result in more read-able names '
              'in the OSM and IDF but this means that it will not be easy to map '
              'the EnergyPlus results back to the original Honeybee Model. Cases '
              'of duplicate IDs resulting from non-unique names will be resolved '
              'by adding integers to the ends of the new IDs that are derived from '
              'the name.', default=True, show_default=True)
@click.option('--resource-ids/--resource-names', ' /-rn', help='Flag to note whether a '
              'cleaned version of all resource display names should be used instead '
              'of identifiers when translating the Model to OSM and IDF. '
              'Using this flag will affect all Materials, Constructions, '
              'ConstructionSets, Schedules, Loads, and ProgramTypes. It will generally '
              'result in more read-able names for the resources in the OSM and IDF. '
              'Cases of duplicate IDs resulting from non-unique names will be resolved '
              'by adding integers to the ends of the new IDs that are derived from '
              'the name.', default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths to the '
              'generated OSM and IDF files if they were successfully created. '
              'By default this will be printed out to stdout.',
              type=click.File('w'), default='-', show_default=True)
def model_to_osm_cli(
        model_file, sim_par_json, epw_file, folder, osm_file, idf_file,
        geometry_ids, resource_ids, log_file):
    """Translate a Honeybee Model file into an OpenStudio Model and corresponding IDF.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        geo_names = not geometry_ids
        res_names = not resource_ids
        model_to_osm(
            model_file, sim_par_json, epw_file, folder, osm_file, idf_file,
            geo_names, res_names, log_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_osm(
    model_file, sim_par_json=None, epw_file=None, folder=None,
    osm_file=None, idf_file=None, geometry_names=False, resource_names=False,
    log_file=None, geometry_ids=True, resource_ids=True
):
    """Translate a Honeybee Model file into an OpenStudio Model and corresponding IDF.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        sim_par_json: Full path to a honeybee energy SimulationParameter JSON that
            describes all of the settings for the simulation. If None, default
            parameters will be generated.
        epw_file: Full path to an EPW file to be associated with the exported OSM.
            This is typically not necessary but may be used when a sim-par-json is
            specified that requests a HVAC sizing calculation to be run as part
            of the translation process but no design days are inside this
            simulation parameter.
        folder: Deprecated input that is no longer used.
        osm_file: Optional path where the OSM will be output.
        idf_file: Optional path where the IDF will be output.
        geometry_names: Boolean to note whether a cleaned version of all geometry
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Rooms, Faces,
            Apertures, Doors, and Shades. It will generally result in more read-able
            names in the OSM and IDF but this means that it will not be easy to map
            the EnergyPlus results back to the original Honeybee Model. Cases
            of duplicate IDs resulting from non-unique names will be resolved
            by adding integers to the ends of the new IDs that are derived from
            the name. (Default: False).
        resource_names: Boolean to note whether a cleaned version of all resource
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Materials,
            Constructions, ConstructionSets, Schedules, Loads, and ProgramTypes.
            It will generally result in more read-able names for the resources
            in the OSM and IDF. Cases of duplicate IDs resulting from non-unique
            names will be resolved by adding integers to the ends of the new IDs
            that are derived from the name. (Default: False).
        log_file: Optional log file to output the paths to the generated OSM and]
            IDF files if they were successfully created. By default this string
            will be returned from this method.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.openstudio import openstudio, OSModel
        from honeybee_openstudio.simulation import simulation_parameter_to_openstudio, \
            assign_epw_to_model
        from honeybee_openstudio.writer import model_to_openstudio
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if folder is not None:
        print('--folder is deprecated and no longer used.')

    # initialize the OpenStudio model that will hold everything
    os_model = OSModel()
    # generate default simulation parameters
    if sim_par_json is None:
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        sim_par.output.add_hvac_energy_use()
        sim_par.output.add_electricity_generation()
        sim_par.output.reporting_frequency = 'Monthly'
    else:
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        sim_par = SimulationParameter.from_dict(data)

    # use any specified EPW files to assign design days and the climate zone
    def ddy_from_epw(epw_file, sim_par):
        """Produce a DDY from an EPW file."""
        epw_obj = EPW(epw_file)
        des_days = [epw_obj.approximate_design_day('WinterDesignDay'),
                    epw_obj.approximate_design_day('SummerDesignDay')]
        sim_par.sizing_parameter.design_days = des_days

    if epw_file is not None:
        epw_folder, epw_file_name = os.path.split(epw_file)
        ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))
        stat_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.stat'))
        if len(sim_par.sizing_parameter.design_days) == 0 and \
                os.path.isfile(ddy_file):
            try:
                sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)
            except AssertionError:  # no design days within the DDY file
                ddy_from_epw(epw_file, sim_par)
        elif len(sim_par.sizing_parameter.design_days) == 0:
            ddy_from_epw(epw_file, sim_par)
        if sim_par.sizing_parameter.climate_zone is None and os.path.isfile(stat_file):
            stat_obj = STAT(stat_file)
            sim_par.sizing_parameter.climate_zone = stat_obj.ashrae_climate_zone
        set_cz = True if sim_par.sizing_parameter.climate_zone is None else False
        assign_epw_to_model(epw_file, os_model, set_cz)

    # translate the simulation parameter and model to an OpenStudio Model
    simulation_parameter_to_openstudio(sim_par, os_model)
    model = Model.from_file(model_file)
    model_to_openstudio(
        model, os_model, use_geometry_names=geometry_names,
        use_resource_names=resource_names, print_progress=True)
    gen_files = []

    # write the OpenStudio Model if specified
    if osm_file is not None:
        osm = os.path.abspath(osm_file)
        os_model.save(osm, overwrite=True)
        gen_files.append(osm)

    # write the IDF if specified
    if idf_file is not None:
        idf = os.path.abspath(idf_file)
        idf_translator = openstudio.energyplus.ForwardTranslator()
        workspace = idf_translator.translateModel(os_model)
        workspace.save(idf, overwrite=True)
        gen_files.append(idf)

    return process_content_to_output(json.dumps(gen_files, indent=4), log_file)


@translate.command('model-to-idf')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for the '
              'simulation. If None default parameters will be generated.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--additional-str', '-a', help='Text string for additional lines that '
              'should be added to the IDF.', type=str, default='', show_default=True)
@click.option('--compact-schedules/--csv-schedules', ' /-c', help='Flag to note '
              'whether any ScheduleFixedIntervals in the model should be included '
              'in the IDF string as a Schedule:Compact or they should be written as '
              'CSV Schedule:File and placed in a directory next to the output-file.',
              default=True, show_default=True)
@click.option('--hvac-to-ideal-air/--hvac-check', ' /-h', help='Flag to note '
              'whether any detailed HVAC system templates should be converted to '
              'an equivalent IdealAirSystem upon export. If hvac-check is used'
              'and the Model contains detailed systems, a ValueError will '
              'be raised.', default=True, show_default=True)
@click.option('--geometry-ids/--geometry-names', ' /-gn', help='Flag to note whether a '
              'cleaned version of all geometry display names should be used instead '
              'of identifiers when translating the Model to IDF. Using this flag will '
              'affect all Rooms, Faces, Apertures, Doors, and Shades. It will '
              'generally result in more read-able names in the IDF but this means that '
              'it will not be easy to map the EnergyPlus results back to the original '
              'Honeybee Model. Cases of duplicate IDs resulting from non-unique names '
              'will be resolved by adding integers to the ends of the new IDs that are '
              'derived from the name.', default=True, show_default=True)
@click.option('--resource-ids/--resource-names', ' /-rn', help='Flag to note whether a '
              'cleaned version of all resource display names should be used instead '
              'of identifiers when translating the Model to IDF. Using this flag will '
              'affect all Materials, Constructions, ConstructionSets, Schedules, '
              'Loads, and ProgramTypes. It will generally result in more read-able '
              'names for the resources in the IDF. Cases of duplicate IDs resulting '
              'from non-unique names will be resolved by adding integers to the ends '
              'of the new IDs that are derived from the name.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_idf_cli(model_file, sim_par_json, additional_str, compact_schedules,
                     hvac_to_ideal_air, geometry_ids, resource_ids, output_file):
    """Translate a Model (HBJSON) file to a simplified IDF using direct-to-idf methods.

    The direct-to-idf methods are faster than those that translate the model
    to OSM but certain features like detailed HVAC systems and the Airflow Network
    are not supported.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        csv_schedules = not compact_schedules
        hvac_check = not hvac_to_ideal_air
        geo_names = not geometry_ids
        res_names = not resource_ids
        model_to_idf(
            model_file, sim_par_json, additional_str, csv_schedules,
            hvac_check, geo_names, res_names, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_idf(
    model_file, sim_par_json=None, additional_str='', csv_schedules=False,
    hvac_check=False, geometry_names=False, resource_names=False, output_file=None,
    compact_schedules=True, hvac_to_ideal_air=True, geometry_ids=True, resource_ids=True
):
    """Translate a Honeybee Model file to a simplified IDF using direct-to-idf methods.

    The direct-to-idf methods are faster than those that translate the model
    to OSM but certain features like detailed HVAC systems and the Airflow Network
    are not supported.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        sim_par_json: Full path to a honeybee energy SimulationParameter JSON that
            describes all of the settings for the simulation. If None, default
            parameters will be generated.
        additional_str: Text string for additional lines that should be added
            to the IDF.
        csv_schedules: Boolean to note whether any ScheduleFixedIntervals in the
            model should be included in the IDF string as a Schedule:Compact or
            they should be written as CSV Schedule:File and placed in a directory
            next to the output_file. (Default: False).
        hvac_check: Boolean to note whether any detailed HVAC system templates
            should be converted to an equivalent IdealAirSystem upon export.
            If hvac-check is used and the Model contains detailed systems, a
            ValueError will be raised. (Default: False).
        geometry_names: Boolean to note whether a cleaned version of all geometry
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Rooms, Faces,
            Apertures, Doors, and Shades. It will generally result in more read-able
            names in the OSM and IDF but this means that it will not be easy to map
            the EnergyPlus results back to the original Honeybee Model. Cases
            of duplicate IDs resulting from non-unique names will be resolved
            by adding integers to the ends of the new IDs that are derived from
            the name. (Default: False).
        resource_names: Boolean to note whether a cleaned version of all resource
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Materials,
            Constructions, ConstructionSets, Schedules, Loads, and ProgramTypes.
            It will generally result in more read-able names for the resources
            in the OSM and IDF. Cases of duplicate IDs resulting from non-unique
            names will be resolved by adding integers to the ends of the new IDs
            that are derived from the name. (Default: False).
        output_file: Optional IDF file to output the IDF string of the translation.
            By default this string will be returned from this method.
    """
    # load simulation parameters or generate default ones
    if sim_par_json is not None:
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        sim_par = SimulationParameter.from_dict(data)
    else:
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        sim_par.output.add_hvac_energy_use()
        sim_par.output.add_electricity_generation()
        sim_par.output.reporting_frequency = 'Monthly'

    # re-serialize the Model to Python
    model = Model.from_file(model_file)

    # reset the IDs to be derived from the display_names if requested
    if geometry_names:
        id_map = model.reset_ids()
        model.properties.energy.sync_detailed_hvac_ids(id_map['rooms'])
    if resource_names:
        model.properties.energy.reset_resource_ids()

    # set the schedule directory in case it is needed
    sch_directory = None
    if csv_schedules:
        sch_path = os.path.abspath(model_file) \
            if output_file is not None and 'stdout' in str(output_file) \
            else os.path.abspath(str(output_file))
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

    # create the strings for simulation parameters and model
    ver_str = energyplus_idf_version() if folders.energyplus_version \
        is not None else ''
    sim_par_str = sim_par.to_idf()
    hvac_to_ideal = not hvac_check
    model_str = model.to.idf(
        model, schedule_directory=sch_directory,
        use_ideal_air_equivalent=hvac_to_ideal)
    idf_str = '\n\n'.join([ver_str, sim_par_str, model_str, additional_str])

    # write out the IDF file
    return process_content_to_output(idf_str, output_file)


@translate.command('model-to-gbxml')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw',
              help='Deprecated input that is no longer used.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--default-subfaces/--triangulate-subfaces', ' /-t',
              help='Flag to note whether sub-faces (including Apertures and Doors) '
              'should be triangulated if they have more than 4 sides (True) or whether '
              'they should be left as they are (False). This triangulation is '
              'necessary when exporting directly to EnergyPlus since it cannot accept '
              'sub-faces with more than 4 vertices.', default=True, show_default=True)
@click.option('--triangulate-non-planar/--permit-non-planar', ' /-np',
              help='Flag to note whether any non-planar orphaned geometry in the '
              'model should be triangulated upon export. This can be helpful because '
              'OpenStudio simply raises an error when it encounters non-planar '
              'geometry, which would hinder the ability to save gbXML files that are '
              'to be corrected in other software.', default=True, show_default=True)
@click.option('--minimal/--full-geometry', ' /-fg', help='Flag to note whether space '
              'boundaries and shell geometry should be included in the exported '
              'gbXML vs. just the minimal required non-manifold geometry.',
              default=True, show_default=True)
@click.option('--interior-face-type', '-ift', help='Text string for the type to be '
              'used for all interior floor faces. If unspecified, the interior types '
              'will be left as they are. Choose from: InteriorFloor, Ceiling.',
              type=str, default='', show_default=True)
@click.option('--ground-face-type', '-gft', help='Text string for the type to be '
              'used for all ground-contact floor faces. If unspecified, the ground '
              'types will be left as they are. Choose from: UndergroundSlab, '
              'SlabOnGrade, RaisedFloor.', type=str, default='', show_default=True)
@click.option('--output-file', '-f', help='Optional gbXML file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_gbxml_cli(
        model_file, osw_folder, default_subfaces, triangulate_non_planar, minimal,
        interior_face_type, ground_face_type, output_file):
    """Translate a Honeybee Model (HBJSON) to a gbXML file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        triangulate_subfaces = not default_subfaces
        permit_non_planar = not triangulate_non_planar
        full_geometry = not minimal
        model_to_gbxml(
            model_file, osw_folder, triangulate_subfaces, permit_non_planar,
            full_geometry, interior_face_type, ground_face_type, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_gbxml(
    model_file, osw_folder=None, triangulate_subfaces=False,
    permit_non_planar=False, full_geometry=False,
    interior_face_type='', ground_face_type='', output_file=None,
    default_subfaces=True, triangulate_non_planar=True, minimal=True
):
    """Translate a Honeybee Model file to a gbXML file.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        osw_folder: Deprecated input that is no longer used.
        triangulate_subfaces: Boolean to note whether sub-faces (including
            Apertures and Doors) should be triangulated if they have more
            than 4 sides (True) or whether they should be left as they are (False).
            This triangulation is necessary when exporting directly to EnergyPlus
            since it cannot accept sub-faces with more than 4 vertices. (Default: False).
        permit_non_planar: Boolean to note whether any non-planar orphaned geometry
            in the model should be triangulated upon export. This can be helpful
            because OpenStudio simply raises an error when it encounters non-planar
            geometry, which would hinder the ability to save gbXML files that are
            to be corrected in other software. (Default: False).
        full_geometry: Boolean to note whether space boundaries and shell geometry
            should be included in the exported gbXML vs. just the minimal required
            non-manifold geometry. (Default: False).
        interior_face_type: Text string for the type to be used for all interior
            floor faces. If unspecified, the interior types will be left as they are.
            Choose from: InteriorFloor, Ceiling.
        ground_face_type: Text string for the type to be used for all ground-contact
            floor faces. If unspecified, the ground types will be left as they are.
            Choose from: UndergroundSlab, SlabOnGrade, RaisedFloor.
        output_file: Optional gbXML file to output the string of the translation.
            By default it will be returned from this method.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.writer import model_to_gbxml
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--osw-folder is deprecated and no longer used.')

    # load the model and translate it to a gbXML string
    triangulate_non_planar = not permit_non_planar
    model = Model.from_file(model_file)
    gbxml_str = model_to_gbxml(
        model, triangulate_non_planar_orphaned=triangulate_non_planar,
        triangulate_subfaces=triangulate_subfaces, full_geometry=full_geometry,
        interior_face_type=interior_face_type, ground_face_type=ground_face_type
    )

    # write out the gbXML file
    return process_content_to_output(gbxml_str, output_file)


@translate.command('model-to-trace-gbxml')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--single-window/--detailed-windows', ' /-dw', help='Flag to note '
              'whether all windows within walls should be converted to a single '
              'window with an area that matches the original geometry.',
              default=True, show_default=True)
@click.option('--rect-sub-distance', '-r', help='A number for the resolution at which '
              'non-rectangular Apertures will be subdivided into smaller rectangular '
              'units. This is required as TRACE 3D plus cannot model non-rectangular '
              'geometries. This can include the units of the distance (eg. 0.5ft) or, '
              'if no units are provided, the value will be interpreted in the '
              'honeybee model units.',
              type=str, default='0.15m', show_default=True)
@click.option('--frame-merge-distance', '-m', help='A number for the maximum distance '
              'between non-rectangular Apertures at which point the Apertures will be '
              'merged into a single rectangular geometry. This is often helpful when '
              'there are several triangular Apertures that together make a rectangle '
              'when they are merged across their frames. This can include the units '
              'of the distance (eg. 0.5ft) or, if no units are provided, the value '
              'will be interpreted in the honeybee model units',
              type=str, default='0.2m', show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional gbXML file to output the string '
              'of the translation. By default it printed out to stdout.',
              type=click.File('w'), default='-', show_default=True)
def model_to_trace_gbxml_cli(
        model_file, single_window, rect_sub_distance, frame_merge_distance,
        osw_folder, output_file):
    """Translate a Honeybee Model (HBJSON) to a gbXML file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        detailed_windows = not single_window
        model_to_trace_gbxml(model_file, detailed_windows, rect_sub_distance,
                             frame_merge_distance, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_trace_gbxml(
    model_file, detailed_windows=False, rect_sub_distance='0.15m',
    frame_merge_distance='0.2m', osw_folder=None, output_file=None,
    single_window=True
):
    """Translate a Honeybee Model to a gbXML file that is compatible with TRACE 3D Plus.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        detailed_windows: A boolean for whether all windows within walls should be
            left as they are (True) or converted to a single window with an area
            that matches the original geometry (False). (Default: False).
        rect_sub_distance: A number for the resolution at which non-rectangular
            Apertures will be subdivided into smaller rectangular units. This is
            required as TRACE 3D plus cannot model non-rectangular geometries.
            This can include the units of the distance (eg. 0.5ft) or, if no units
            are provided, the value will be interpreted in the honeybee model
            units. (Default: 0.15m).
        frame_merge_distance: A number for the maximum distance between non-rectangular
            Apertures at which point the Apertures will be merged into a single
            rectangular geometry. This is often helpful when there are several
            triangular Apertures that together make a rectangle when they are
            merged across their frames. This can include the units of the
            distance (eg. 0.5ft) or, if no units are provided, the value will
            be interpreted in the honeybee model units. (Default: 0.2m).
        osw_folder: Deprecated input that is no longer used.
        output_file: Optional gbXML file to output the string of the translation.
            By default it will be returned from this method.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.writer import model_to_gbxml
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--osw-folder is deprecated and no longer used.')

    # load the model and translate it to a gbXML string
    single_window = not detailed_windows
    model = Model.from_file(model_file)
    model = _preprocess_model_for_trace(
        model, single_window=single_window, rect_sub_distance=rect_sub_distance,
        frame_merge_distance=frame_merge_distance)
    gbxml_str = model_to_gbxml(model)

    # write out the gbXML file
    return process_content_to_output(gbxml_str, output_file)


@translate.command('model-to-sdd')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional SDD file to output the string '
              'of the translation. By default it printed out to stdout.', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_to_sdd_cli(model_file, osw_folder, output_file):
    """Translate a Honeybee Model file to a SDD file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        model_to_sdd(model_file, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_sdd(model_file, osw_folder=None, output_file=None):
    """Translate a Honeybee Model file to a SDD file.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        osw_folder: Deprecated input that is no longer used.
        output_file: Optional SDD file to output the string of the translation.
            By default it will be returned from this method.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.openstudio import openstudio
        from honeybee_openstudio.writer import model_to_openstudio
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--folder is deprecated and no longer used.')

    # translate the model to an OpenStudio Model
    model = Model.from_file(model_file)
    os_model = model_to_openstudio(model, use_simple_window_constructions=True)

    # write the SDD
    out_path = None
    if output_file is None or output_file.endswith('-'):
        out_directory = tempfile.gettempdir()
        f_name = os.path.basename(model_file).lower()
        f_name = f_name.replace('.hbjson', '.xml').replace('.json', '.xml')
        out_path = os.path.join(out_directory, f_name)
    sdd = os.path.abspath(output_file) if out_path is None else out_path
    sdd_translator = openstudio.sdd.SddForwardTranslator()
    sdd_translator.modelToSDD(os_model, sdd)

    # return the file contents if requested
    if out_path is not None:
        with open(sdd, 'r') as sdf:
            file_contents = sdf.read()
        if output_file is None:
            return file_contents
        else:
            print(file_contents)


@translate.command('model-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--keep-properties/--reset-properties', ' /-r', help='Flag to note '
              'whether all energy properties should be reset to defaults upon import, '
              'meaning that only the geometry and boundary conditions are imported '
              'from the file.', default=True, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout.',
              type=click.File('w'), default='-', show_default=True)
def model_from_osm_cli(osm_file, keep_properties, osw_folder, output_file):
    """Translate a OpenStudio Model (OSM) to a Honeybee Model (HBJSON).

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        reset_properties = not keep_properties
        model_from_osm(osm_file, reset_properties, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_from_osm(osm_file, reset_properties=False, osw_folder=None, output_file=None,
                   keep_properties=True):
    """Translate a OpenStudio Model (OSM) to a Honeybee Model (HBJSON).

    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
        reset_properties: Boolean to note whether all energy properties should be
            reset to defaults upon import, meaning that only the geometry and boundary
            conditions are imported from the Openstudio Model. (Default: False).
        osw_folder: Deprecated input that is no longer used.
        output_file: Optional HBJSON file to output the string of the translation.
            If None, it will be returned from this method. (Default: None).
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.reader import model_from_osm_file
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--folder is deprecated and no longer used.')
    # translate everything to a honeybee Model
    model = model_from_osm_file(osm_file, reset_properties)
    # write out the file
    return process_content_to_output(json.dumps(model.to_dict()), output_file)


@translate.command('model-from-idf')
@click.argument('idf-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--keep-properties/--reset-properties', ' /-r', help='Flag to note '
              'whether all energy properties should be reset to defaults upon import, '
              'meaning that only the geometry and boundary conditions are imported '
              'from the file.', default=True, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_from_idf_cli(idf_file, keep_properties, osw_folder, output_file):
    """Translate an EnergyPlus Model (IDF) to a Honeybee Model (HBJSON).

    \b
    Args:
        idf_file: Path to an EnergyPlus Model (IDF) file.
    """
    try:
        reset_properties = not keep_properties
        model_from_idf(idf_file, reset_properties, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_from_idf(idf_file, reset_properties=False, osw_folder=None, output_file=None,
                   keep_properties=True):
    """Translate an EnergyPlus Model (IDF) to a Honeybee Model (HBJSON).

    Args:
        idf_file: Path to an EnergyPlus Model (IDF) file.
        reset_properties: Boolean to note whether all energy properties should be
            reset to defaults upon import, meaning that only the geometry and boundary
            conditions are imported from the EnergyPlus Model. (Default: False).
        osw_folder: Deprecated input that is no longer used.
        output_file: Optional HBJSON file to output the string of the translation.
            If None, it will be returned from this method. (Default: None).
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.reader import model_from_idf_file
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--folder is deprecated and no longer used.')
    # translate everything to a honeybee Model
    model = model_from_idf_file(idf_file, reset_properties)
    # write out the file
    return process_content_to_output(json.dumps(model.to_dict()), output_file)


@translate.command('model-from-gbxml')
@click.argument('gbxml-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--keep-properties/--reset-properties', ' /-r', help='Flag to note '
              'whether all energy properties should be reset to defaults upon import, '
              'meaning that only the geometry and boundary conditions are imported '
              'from the file.', default=True, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_from_gbxml_cli(gbxml_file, keep_properties, osw_folder, output_file):
    """Translate a gbXML to a Honeybee Model (HBJSON).

    \b
    Args:
        gbxml_file: Path to a gbXML file.
    """
    try:
        reset_properties = not keep_properties
        model_from_gbxml(gbxml_file, reset_properties, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_from_gbxml(gbxml_file, reset_properties=False, osw_folder=None,
                     output_file=None, keep_properties=True):
    """Translate a gbXML to a Honeybee Model (HBJSON).

    Args:
        gbxml_file: Path to a gbXML file.
        reset_properties: Boolean to note whether all energy properties should be
            reset to defaults upon import, meaning that only the geometry and boundary
            conditions are imported from the gbXML Model. (Default: False).
        osw_folder: Deprecated input that is no longer used.
        output_file: Optional HBJSON file to output the string of the translation.
            If None, it will be returned from this method. (Default: None).
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.reader import model_from_gbxml_file
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
    if osw_folder is not None:
        print('--folder is deprecated and no longer used.')
    # translate everything to a honeybee Model
    model = model_from_gbxml_file(gbxml_file, reset_properties)
    # write out the file
    return process_content_to_output(json.dumps(model.to_dict()), output_file)


@translate.command('constructions-to-idf')
@click.argument('construction-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_to_idf(construction_json, output_file):
    """Translate a Construction JSON file to an IDF using direct-to-idf translators.

    \b
    Args:
        construction_json: Full path to a Construction JSON file. This file should
            either be an array of non-abridged Constructions or a dictionary where
            the values are non-abridged Constructions.
    """
    try:
        # re-serialize the Constructions to Python
        with open(construction_json) as json_file:
            data = json.load(json_file)
        constr_list = data.values() if isinstance(data, dict) else data
        constr_objs = [dict_to_construction(constr) for constr in constr_list]
        mat_objs = set()
        for constr in constr_objs:
            try:
                for mat in constr.materials:
                    mat_objs.add(mat)
                if constr.has_frame:
                    mat_objs.add(constr.frame)
                if constr.has_shade:
                    if constr.is_switchable_glazing:
                        mat_objs.add(constr.switched_glass_material)
            except AttributeError:  # not a construction with materials
                pass

        # create the IDF strings
        idf_str_list = []
        idf_str_list.append('!-   ============== MATERIALS ==============\n')
        idf_str_list.extend([mat.to_idf() for mat in mat_objs])
        idf_str_list.append('!-   ============ CONSTRUCTIONS ============\n')
        idf_str_list.extend([constr.to_idf() for constr in constr_objs])
        idf_str = '\n\n'.join(idf_str_list)

        # write out the IDF file
        output_file.write(idf_str)
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('constructions-from-idf')
@click.argument('construction-idf', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_from_idf(construction_idf, indent, output_file):
    """Translate a Construction IDF file to a honeybee JSON as an array of constructions.

    \b
    Args:
        construction_idf: Full path to a Construction IDF file. Only the constructions
            and materials in this file will be extracted.
    """
    try:
        # re-serialize the Constructions to Python
        opaque_constrs = OpaqueConstruction.extract_all_from_idf_file(construction_idf)
        win_constrs = WindowConstruction.extract_all_from_idf_file(construction_idf)

        # create the honeybee dictionaries
        hb_obj_list = []
        for constr in opaque_constrs[0]:
            hb_obj_list.append(constr.to_dict())
        for constr in win_constrs[0]:
            hb_obj_list.append(constr.to_dict())

        # write out the JSON file
        output_file.write(json.dumps(hb_obj_list, indent=indent))
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('materials-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def materials_from_osm(osm_file, indent, osw_folder, output_file):
    """Translate all Materials in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    materials to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.material import extract_all_materials
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        materials = extract_all_materials(os_model.get())
        out_dict = {mat.identifier: mat.to_dict() for mat in materials.values()}
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Material translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('constructions-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the materials-from-osm command will be used to separately '
              'translate all of the materials from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def constructions_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all Constructions in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    constructions to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.construction import extract_all_constructions
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        constructions = extract_all_constructions(os_model.get())
        abridged = not full
        out_dict = {}
        for con in constructions.values():
            try:
                out_dict[con.identifier] = con.to_dict(abridged=abridged)
            except TypeError:  # no abridged option
                out_dict[con.identifier] = con.to_dict()
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('construction-sets-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the constructions-from-osm command will be used to separately '
              'translate all of the constructions from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_sets_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all ConstructionSets in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    constructions to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.construction import extract_all_constructions
            from honeybee_openstudio.constructionset import construction_set_from_openstudio
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        os_model = os_model.get()
        constructions = extract_all_constructions(os_model)
        abridged = not full
        out_dict = {}
        for os_cons_set in os_model.getDefaultConstructionSets():
            if os_cons_set.nameString() != 'Default Generic Construction Set':
                con_set = construction_set_from_openstudio(os_cons_set, constructions)
                out_dict[con_set.identifier] = con_set.to_dict(abridged=abridged)
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('ConstructionSet translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-to-idf')
@click.argument('schedule-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_to_idf(schedule_json, output_file):
    """Translate a Schedule JSON file to an IDF using direct-to-idf translators.

    \b
    Args:
        schedule_json: Full path to a Schedule JSON file. This file should
            either be an array of non-abridged Schedules or a dictionary where
            the values are non-abridged Schedules.
    """
    try:
        # re-serialize the Schedule to Python
        with open(schedule_json) as json_file:
            data = json.load(json_file)
        sch_list = data.values() if isinstance(data, dict) else data
        sch_objs = [dict_to_schedule(sch) for sch in sch_list]
        type_objs = set()
        for sch in sch_objs:
            type_objs.add(sch.schedule_type_limit)

        # set the schedule directory in case it is needed
        sch_path = os.path.abspath(schedule_json) if 'stdout' in str(output_file) \
            else os.path.abspath(str(output_file))
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

        # create the IDF strings
        sched_strs = []
        used_day_sched_ids = []
        for sched in sch_objs:
            try:  # ScheduleRuleset
                year_schedule, week_schedules = sched.to_idf()
                if week_schedules is None:  # ScheduleConstant
                    sched_strs.append(year_schedule)
                else:  # ScheduleYear
                    # check that day schedules aren't referenced by other schedules
                    day_scheds = []
                    for day in sched.day_schedules:
                        if day.identifier not in used_day_sched_ids:
                            day_scheds.append(day.to_idf(sched.schedule_type_limit))
                            used_day_sched_ids.append(day.identifier)
                    sched_strs.extend([year_schedule] + week_schedules + day_scheds)
            except AttributeError:  # ScheduleFixedInterval
                sched_strs.append(sched.to_idf(sch_directory))
        idf_str_list = []
        idf_str_list.append('!-   ========= SCHEDULE TYPE LIMITS =========\n')
        idf_str_list.extend([type_limit.to_idf() for type_limit in type_objs])
        idf_str_list.append('!-   ============== SCHEDULES ==============\n')
        idf_str_list.extend(sched_strs)
        idf_str = '\n\n'.join(idf_str_list)

        # write out the IDF file
        output_file.write(idf_str)
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-from-idf')
@click.argument('schedule-idf', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_from_idf(schedule_idf, indent, output_file):
    """Translate a schedule IDF file to a honeybee JSON as an array of schedules.

    \b
    Args:
        schedule_idf: Full path to a Schedule IDF file. Only the schedules
            and schedule type limits in this file will be extracted.
    """
    try:
        # re-serialize the schedules to Python
        schedules = ScheduleRuleset.extract_all_from_idf_file(schedule_idf)
        # create the honeybee dictionaries
        hb_obj_list = [sch.to_dict() for sch in schedules]
        # write out the JSON file
        output_file.write(json.dumps(hb_obj_list, indent=indent))
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedule-type-limits-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limits_from_osm(osm_file, indent, osw_folder, output_file):
    """Translate all ScheduleTypeLimits in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    type limits to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.schedule import schedule_type_limits_from_openstudio
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        out_dict = {}
        for os_type_lim in os_model.get().getScheduleTypeLimitss():
            type_lim = schedule_type_limits_from_openstudio(os_type_lim)
            out_dict[type_lim.identifier] = type_lim.to_dict()
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('ScheduleTypeLimit translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the schedule-type-limits-from-osm command will be used to '
              'separately translate all of the type limits from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all Schedules in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    schedules to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.schedule import extract_all_schedules
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        schedules = extract_all_schedules(os_model.get())
        abridged = not full
        out_dict = {}
        for sch in schedules.values():
            out_dict[sch.identifier] = sch.to_dict(abridged=abridged)
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('programs-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the schedules-from-osm command will be used to separately '
              'translate all of the schedules from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Deprecated input that is no longer used.',
              default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def programs_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all ProgramTypes in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    programs to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        try:
            from honeybee_openstudio.openstudio import openstudio
            from honeybee_openstudio.schedule import extract_all_schedules
            from honeybee_openstudio.programtype import program_type_from_openstudio
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))
        ver_translator = openstudio.osversion.VersionTranslator()  # in case OSM is old
        os_model = ver_translator.loadModel(osm_file)
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        os_model = os_model.get()
        schedules = extract_all_schedules(os_model)
        abridged = not full
        out_dict = {}
        for os_space_type in os_model.getSpaceTypes():
            program = program_type_from_openstudio(os_space_type, schedules)
            out_dict[program.identifier] = program.to_dict(abridged=abridged)
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Program translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-occ-schedules')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--threshold', '-t', help='A number between 0 and 1 for the threshold '
              'at and above which a schedule value is considered occupied.',
              type=float, default=0.1, show_default=True)
@click.option('--period', '-p', help='An AnalysisPeriod string to dictate '
              'the start and end of the exported occupancy values '
              '(eg. "6/21 to 9/21 between 0 and 23 @1"). Note that the timestep '
              'of the period will determine the timestep of output values. If '
              'unspecified, the values will be annual.', default=None, type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON of '
              'occupancy values. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_occ_schedules(model_file, threshold, period, output_file):
    """Translate a Model's occupancy schedules into a JSON of 0/1 values.

    \b
    Args:
        model_file: Full path to a Model JSON or Pkl file.
    """
    try:
        # re-serialize the Model
        model = Model.from_file(model_file)

        # loop through the rooms and collect all unique occupancy schedules
        scheds, room_occupancy = [], {}
        for room in model.rooms:
            people = room.properties.energy.people
            if people is not None:
                model.properties.energy._check_and_add_schedule(
                    people.occupancy_schedule, scheds)
                room_occupancy[room.identifier] = people.occupancy_schedule.identifier
            else:
                room_occupancy[room.identifier] = None

        # process the run period if it is supplied
        if period is not None and period != '' and period != 'None':
            a_per = AnalysisPeriod.from_string(period)
        else:
            a_per = AnalysisPeriod()

        # convert occupancy schedules to lists of 0/1 values
        schedules = {}
        for sch in scheds:
            sch_data = sch.data_collection() if isinstance(sch, ScheduleRuleset) \
                else sch.data_collection
            if not a_per.is_annual:
                sch_data = sch_data.filter_by_analysis_period(a_per)
            values = []
            for val in sch_data.values:
                is_occ = 0 if val <= threshold else 1
                values.append(is_occ)
            schedules[sch.identifier] = values

        # write out the JSON file
        occ_dict = {'schedules': schedules, 'room_occupancy': room_occupancy}
        output_file.write(json.dumps(occ_dict))
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-transmittance-schedules')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--period', '-p', help='An AnalysisPeriod string to dictate '
              'the start and end of the exported occupancy values '
              '(eg. "6/21 to 9/21 between 0 and 23 @1"). Note that the timestep '
              'of the period will determine the timestep of output values. If '
              'unspecified, the values will be annual.', default=None, type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON of '
              'occupancy values. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_trans_schedules(model_file, period, output_file):
    """Translate a Model's shade transmittance schedules into a JSON of fractional vals.

    \b
    Args:
        model_file: Full path to a Model JSON or Pkl file.
    """
    try:
        # re-serialize the Model
        model = Model.from_file(model_file)

        # loop through the rooms and collect all unique occupancy schedules
        scheds = []
        for shade in model.shades:
            t_sch = shade.properties.energy.transmittance_schedule
            if t_sch is not None:
                model.properties.energy._check_and_add_schedule(t_sch, scheds)

        # process the run period if it is supplied
        if period is not None and period != '' and period != 'None':
            a_per = AnalysisPeriod.from_string(period)
        else:
            a_per = AnalysisPeriod()

        # convert occupancy schedules to lists of 0/1 values
        schedules = {}
        for sch in scheds:
            sch_data = sch.data_collection() if isinstance(sch, ScheduleRuleset) \
                else sch.data_collection
            if not a_per.is_annual:
                sch_data = sch_data.filter_by_analysis_period(a_per)
            schedules[clean_rad_string(sch.identifier)] = sch_data.values

        # write out the JSON file
        output_file.write(json.dumps(schedules))
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def _run_translation_osw(osw, out_path):
    """Generic function used by all import methods that run OpenStudio CLI."""
    # run the measure to translate the model JSON to an openstudio measure
    _, idf = run_osw(osw, silent=True)
    if idf is not None and os.path.isfile(idf):
        if out_path is not None:  # load the JSON string to stdout
            with open(out_path) as json_file:
                return json_file.read()
    else:
        _parse_os_cli_failure(os.path.dirname(osw))


def _translate_osm_to_hbjson(osm_file, osw_folder):
    """Translate an OSM to a HBJSON for use in resource extraction commands."""
    # come up with a temporary path to write the HBJSON
    out_directory = os.path.join(
        hb_folders.default_simulation_folder, 'temp_translate')
    f_name = os.path.basename(osm_file).lower().replace('.osm', '.hbjson')
    out_path = os.path.join(out_directory, f_name)
    # run the OSW to translate the OSM to HBJSON
    osw = from_osm_osw(osm_file, out_path, osw_folder)
    # load the resulting HBJSON to a dictionary and return it
    _, idf = run_osw(osw, silent=True)
    if idf is not None and os.path.isfile(idf):
        with open(out_path) as json_file:
            return json.load(json_file)
    else:
        _parse_os_cli_failure(os.path.dirname(osw))
