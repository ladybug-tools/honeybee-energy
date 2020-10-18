"""honeybee energy translation commands."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from ladybug.futil import preparedir
from honeybee.model import Model

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.construction.dictutil import dict_to_construction
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.schedule.dictutil import dict_to_schedule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.run import measure_compatible_model_json, to_openstudio_osw, \
    run_osw
from honeybee_energy.writer import energyplus_idf_version
from honeybee_energy.config import folders

import sys
import os
import logging
import json

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
              type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--folder', '-f', help='Folder on this computer, into which the OSM '
              'and IDF files will be written. If None, the files will be output in the'
              'same location as the model_json.', default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'expored directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths to the '
              'generated OSM and IDF files if they were successfully created. '
              'By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_osm(model_json, sim_par_json, folder, check_model, log_file):
    """Translate a Model JSON file into an OpenStudio Model and corresponding IDF.

    \b
    Args:
        model_json: Full path to a Model JSON file.
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
        if osw is not None and os.path.isfile(osw):
            osm, idf = run_osw(osw)
            # run the resulting idf through EnergyPlus
            if idf is not None and os.path.isfile(idf):
                log_file.write(json.dumps([osm, idf]))
            else:
                raise Exception('Running OpenStudio CLI failed.')
        else:
            raise Exception('Writing OSW file failed.')
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
              type=click.Path(exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--additional-str', '-a', help='Text string for additional lines that '
              'should be added to the IDF.', type=str, default='', show_default=True)
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string of the '
              'translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_idf(model_json, sim_par_json, additional_str, output_file):
    """Translate a Model JSON file to an IDF using direct-to-idf translators.

    If the model contains a feature that is not translate-able through direct-to-idf
    translators, an exception will be raised.

    \b
    Args:
        model_json: Full path to a Model JSON file.
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
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

        # set the schedule directory in case it is needed
        sch_path = os.path.abspath(model_json) if 'stdout' in str(output_file) \
            else os.path.abspath(str(output_file))
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

        # create the strings for simulation paramters and model
        ver_str = energyplus_idf_version() if folders.energyplus_version \
            is not None else ''
        sim_par_str = sim_par.to_idf()
        model_str = model.to.idf(model, schedule_directory=sch_directory)
        idf_str = '\n\n'.join([ver_str, sim_par_str, model_str, additional_str])

        # write out the IDF file
        output_file.write(idf_str)
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
