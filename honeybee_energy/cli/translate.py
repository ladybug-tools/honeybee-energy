"""honeybee energy translation commands."""
import click
import sys
import os
import logging
import json
import shutil

from ladybug.futil import preparedir
from ladybug.datatype.fraction import Fraction
from ladybug.dt import Date
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header
from ladybug.datacollection import HourlyContinuousCollection
from honeybee.model import Model
from honeybee.config import folders as hb_folders

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.construction.dictutil import dict_to_construction
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.schedule.dictutil import dict_to_schedule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.run import measure_compatible_model_json, to_openstudio_osw, \
    to_gbxml_osw, run_osw, from_gbxml_osw, from_osm_osw, from_idf_osw, \
    add_gbxml_space_boundaries
from honeybee_energy.writer import energyplus_idf_version
from honeybee_energy.config import folders

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee JSON files to/from OSM/IDF.')
def translate():
    pass


@translate.command('model-to-osm')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for '
              'the simulation. If None default parameters will be generated.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--folder', '-f', help='Folder on this computer, into which the '
              'working files, OSM and IDF files will be written. If None, the '
              'files will be output in the same location as the model_json.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--osm-file', '-osm', help='Optional file where the OSM will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--idf-file', '-idf', help='Optional file where the IDF will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'expored directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths to the '
              'generated OSM and IDF files if they were successfully created. '
              'By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_osm(
        model_json, sim_par_json, folder, osm_file, idf_file, check_model, log_file):
    """Translate a Model JSON file into an OpenStudio Model and corresponding IDF.

    \b
    Args:
        model_json: Full path to a Honeybee Model JSON file (HBJSON).
    """
    try:
        # set the default folder if it's not specified
        if folder is None:
            folder = os.path.dirname(os.path.abspath(model_json))
        preparedir(folder, remove_content=False)

        # generate default simulation parameters
        if sim_par_json is None:
            sim_par = SimulationParameter()
            sim_par.output.add_zone_energy_use()
            sim_par.output.add_hvac_energy_use()
            sim_par_dict = sim_par.to_dict()
            sp_json = os.path.abspath(os.path.join(folder, 'simulation_parameter.json'))
            with open(sp_json, 'w') as fp:
                json.dump(sim_par_dict, fp)

        # run the Model re-serialization and check if specified
        if check_model:
            model_json = measure_compatible_model_json(model_json, folder)

        # Write the osw file to translate the model to osm
        osw = to_openstudio_osw(folder, model_json, sim_par_json)

        # run the measure to translate the model JSON to an openstudio measure
        osm, idf = run_osw(osw)
        # run the resulting idf through EnergyPlus
        if idf is not None and os.path.isfile(idf):
            if osm_file is not None:
                if not osm_file.lower().endswith('.osm'):
                    osm_file = osm_file + '.osm'
                shutil.copyfile(osm, osm_file)
            if idf_file is not None:
                if not idf_file.lower().endswith('.idf'):
                    idf_file = idf_file + '.idf'
                shutil.copyfile(idf, idf_file)
            log_file.write(json.dumps([osm, idf]))
        else:
            raise Exception('Running OpenStudio CLI failed.')
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-to-idf')
@click.argument('model-json', type=click.Path(
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
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_idf(model_json, sim_par_json, additional_str, compact_schedules,
                 hvac_to_ideal_air, output_file):
    """Translate a Model JSON file to a simplified IDF using direct-to-idf translators.

    \b
    Args:
        model_json: Full path to a Honeybee Model JSON file (HBJSON).
    """
    try:
        # load simulation parameters or generate default ones
        if sim_par_json is not None:
            with open(sim_par_json) as json_file:
                data = json.load(json_file)
            sim_par = SimulationParameter.from_dict(data)
        else:
            sim_par = SimulationParameter()
            sim_par.output.add_zone_energy_use()
            sim_par.output.add_hvac_energy_use()

        # re-serialize the Model to Python
        model = Model.from_file(model_json)

        # set the schedule directory in case it is needed
        sch_directory = None
        if not compact_schedules:
            sch_path = os.path.abspath(model_json) if 'stdout' in str(output_file) \
                else os.path.abspath(str(output_file))
            sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

        # create the strings for simulation paramters and model
        ver_str = energyplus_idf_version() if folders.energyplus_version \
            is not None else ''
        sim_par_str = sim_par.to_idf()
        model_str = model.to.idf(
            model, schedule_directory=sch_directory,
            use_ideal_air_equivalent=hvac_to_ideal_air)
        idf_str = '\n\n'.join([ver_str, sim_par_str, model_str, additional_str])

        # write out the IDF file
        output_file.write(idf_str)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-to-gbxml')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'expored directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--minimal/--full-geometry', ' /-fg', help='Flag to note whether space '
              'boundaries and shell geometry should be included in the exported '
              'gbXML vs. just the minimal required non-manifold geometry.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional gbXML file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_to_gbxml(model_json, osw_folder, check_model, minimal, output_file):
    """Translate a Honeybee Model (HBJSON) to a gbXML file.

    \b
    Args:
        model_json: Full path to a Honeybee Model JSON file (HBJSON).
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
        if output_file.endswith('-'):
            f_name = os.path.basename(model_json).lower()
            f_name = f_name.replace('.hbjson', '.xml').replace('.json', '.xml')
            out_path = os.path.join(out_directory, f_name)

        # run the Model re-serialization and check if specified
        if check_model:
            model_json = measure_compatible_model_json(
                model_json, out_directory, simplify_window_cons=True)

        # Write the osw file and translate the model to gbXML
        out_f = out_path if output_file.endswith('-') else output_file
        osw = to_gbxml_osw(model_json, out_f, osw_folder)
        if minimal:
            _run_translation_osw(osw, out_path)
        else:
            _, idf = run_osw(osw, silent=True)
            if idf is not None and os.path.isfile(idf):
                hb_model = Model.from_hbjson(model_json)
                add_gbxml_space_boundaries(out_f, hb_model)
                if out_path is not None:  # load the JSON string to stdout
                    with open(out_path) as json_file:
                        print(json_file.read())
            else:
                raise Exception('Running OpenStudio CLI failed.')
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_osm(osm_file, osw_folder, output_file):
    """Translate a OpenStudio Model (OSM) to a Honeybee Model (HBJSON).

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(osm_file).lower().replace('.osm', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_osm_osw(osm_file, out_f, osw_folder)
        _run_translation_osw(osw, out_path)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-from-idf')
@click.argument('idf-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_idf(idf_file, osw_folder, output_file):
    """Translate an EnergyPlus Model (IDF) to a Honeybee Model (HBJSON).

    \b
    Args:
        idf_file: Path to an EnergyPlus Model (IDF) file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(idf_file).lower().replace('.idf', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_idf_osw(idf_file, out_f, osw_folder)
        _run_translation_osw(osw, out_path)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-from-gbxml')
@click.argument('gbxml-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_gbxml(gbxml_file, osw_folder, output_file):
    """Translate a gbXML to a Honeybee Model (HBJSON).

    \b
    Args:
        gbxml_file: Path to a gbXML file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(gbxml_file).lower()
            f_name = f_name.replace('.gbxml', '.hbjson').replace('.xml', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_gbxml_osw(gbxml_file, out_f, osw_folder)
        _run_translation_osw(osw, out_path)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


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
            for mat in constr.materials:
                mat_objs.add(mat)

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
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_from_idf(construction_idf, output_file):
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
        output_file.write(json.dumps(hb_obj_list))
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
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
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_from_idf(schedule_idf, output_file):
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
        output_file.write(json.dumps(hb_obj_list))
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-occ-schedules')
@click.argument('model-json', type=click.Path(
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
def model_occ_schedules(model_json, threshold, period, output_file):
    """Translate a Model's occupancy schedules into a JSON of 0/1 values.

    \b
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # re-serialize the Model
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

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
            sch_data = sch.data_collection()
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


def _run_translation_osw(osw, out_path):
    """Generic function used by all import methods that run OpenStudio CLI."""
    # run the measure to translate the model JSON to an openstudio measure
    _, idf = run_osw(osw, silent=True)
    if idf is not None and os.path.isfile(idf):
        if out_path is not None:  # load the JSON string to stdout
            with open(out_path) as json_file:
                print(json_file.read())
    else:
        raise Exception('Running OpenStudio CLI failed.')
