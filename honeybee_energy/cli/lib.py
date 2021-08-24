"""honeybee energy standards library commands."""
import click
import sys
import os
import logging
import json

from honeybee_energy.config import folders
from honeybee_energy.lib.materials import opaque_material_by_identifier, \
    window_material_by_identifier, OPAQUE_MATERIALS, WINDOW_MATERIALS
from honeybee_energy.lib.constructions import opaque_construction_by_identifier, \
    window_construction_by_identifier, shade_construction_by_identifier, \
    OPAQUE_CONSTRUCTIONS, WINDOW_CONSTRUCTIONS, SHADE_CONSTRUCTIONS
from honeybee_energy.lib.constructionsets import construction_set_by_identifier, \
    CONSTRUCTION_SETS
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier, \
    SCHEDULE_TYPE_LIMITS
from honeybee_energy.lib.schedules import schedule_by_identifier, SCHEDULES
from honeybee_energy.lib.programtypes import program_type_by_identifier, PROGRAM_TYPES

from honeybee_energy.lib._loadtypelimits import load_type_limits_from_folder, \
    _schedule_type_limits
from honeybee_energy.lib._loadschedules import load_schedules_from_folder
from honeybee_energy.lib._loadprogramtypes import load_programtypes_from_folder
from honeybee_energy.lib._loadmaterials import load_materials_from_folder
from honeybee_energy.lib._loadconstructions import load_constructions_from_folder
from honeybee_energy.lib._loadconstructionsets import load_constructionsets_from_folder

_logger = logging.getLogger(__name__)


@click.group(help='Commands for retrieving objects from the standards library.')
def lib():
    pass


@lib.command('opaque-materials')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_materials(output_file):
    """Get a list of all opaque materials in the standards library."""
    try:
        output_file.write(json.dumps(OPAQUE_MATERIALS))
    except Exception as e:
        _logger.exception('Failed to load opaque materials.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('window-materials')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_materials(output_file):
    """Get a list of all window materials in the standards library."""
    try:
        output_file.write(json.dumps(WINDOW_MATERIALS))
    except Exception as e:
        _logger.exception('Failed to load window materials.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('opaque-constructions')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_constructions(output_file):
    """Get a list of all opaque constructions in the standards library."""
    try:
        output_file.write(json.dumps(OPAQUE_CONSTRUCTIONS))
    except Exception as e:
        _logger.exception('Failed to load opaque constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('window-constructions')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_constructions(output_file):
    """Get a list of all window constructions in the standards library."""
    try:
        output_file.write(json.dumps(WINDOW_CONSTRUCTIONS))
    except Exception as e:
        _logger.exception('Failed to load window constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('shade-constructions')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def shade_constructions(output_file):
    """Get a list of all shade constructions in the standards library."""
    try:
        output_file.write(json.dumps(SHADE_CONSTRUCTIONS))
    except Exception as e:
        _logger.exception('Failed to load shade constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('construction-sets')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_sets(output_file):
    """Get a list of all construction sets in the standards library."""
    try:
        output_file.write(json.dumps(CONSTRUCTION_SETS))
    except Exception as e:
        _logger.exception('Failed to load construction sets.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedule-type-limits')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limits(output_file):
    """Get a list of all schedule type limits in the standards library."""
    try:
        output_file.write(json.dumps(SCHEDULE_TYPE_LIMITS))
    except Exception as e:
        _logger.exception('Failed to load schedule type limits.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedules')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules(output_file):
    """Get a list of all schedules in the standards library."""
    try:
        output_file.write(json.dumps(SCHEDULES))
    except Exception as e:
        _logger.exception('Failed to load schedules.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('program-types')
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def program_types(output_file):
    """Get a list of all program_types in the standards library."""
    try:
        output_file.write(json.dumps(PROGRAM_TYPES))
    except Exception as e:
        _logger.exception('Failed to load program types.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('opaque-material-by-id')
@click.argument('material-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_material_by_id(material_id, output_file):
    """Get an opaque material definition from the standards lib with its identifier.

    \b
    Args:
        material_id: The identifier of an opaque material in the library.
    """
    try:
        output_file.write(json.dumps(opaque_material_by_identifier(material_id).to_dict()))
    except Exception as e:
        _logger.exception(
            'Retrieval from opaque material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('window-material-by-id')
@click.argument('material-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_material_by_id(material_id, output_file):
    """Get a window material definition from the standards lib with its identifier.

    \b
    Args:
        material_id: The identifier of an window material in the library.
    """
    try:
        output_file.write(json.dumps(window_material_by_identifier(material_id).to_dict()))
    except Exception as e:
        _logger.exception(
            'Retrieval from window material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('opaque-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'defintion should be returned.', default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_construction_by_id(construction_id, complete, output_file):
    """Get an opaque construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of an opaque construction in the library.
    """
    try:
        abridged = not complete
        output_file.write(json.dumps(opaque_construction_by_identifier(
            construction_id).to_dict(abridged=abridged)))
    except Exception as e:
        _logger.exception(
            'Retrieval from opaque construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('window-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'defintion should be returned.', default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_construction_by_id(construction_id, complete, output_file):
    """Get a window construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of a window construction in the library.
    """
    try:
        abridged = not complete
        output_file.write(json.dumps(window_construction_by_identifier(
            construction_id).to_dict(abridged=abridged)))
    except Exception as e:
        _logger.exception(
            'Retrieval from window construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('shade-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def shade_construction_by_id(construction_id, output_file):
    """Get a shade construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of a shade construction in the library.
    """
    try:
        output_file.write(json.dumps(shade_construction_by_identifier(
            construction_id).to_dict()))
    except Exception as e:
        _logger.exception(
            'Retrieval from shade construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('construction-set-by-id')
@click.argument('construction-set-id', type=str)
@click.option('--none-defaults/--include-defaults', ' /-d', help='Flag to note whether '
              'default constructions in the set should be included in or should be '
              'None.', default=True, show_default=True)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_set_by_id(construction_set_id, none_defaults, complete, output_file):
    """Get a construction set definition from the standards lib with its identifier.

    \b
    Args:
        construction_set_id: The identifier of a construction set in the library.
    """
    try:
        abridged = not complete
        c_set = construction_set_by_identifier(construction_set_id)
        output_file.write(json.dumps(c_set.to_dict(
            none_for_defaults=none_defaults, abridged=abridged)))
    except Exception as e:
        _logger.exception(
            'Retrieval from construction set library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedule-type-limit-by-id')
@click.argument('schedule-type-limit-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limit_by_id(schedule_type_limit_id, output_file):
    """Get a schedule type limit definition from the standards lib with its identifier.

    \b
    Args:
        schedule_type_limit_id: The identifier of a schedule type limit in the library.
    """
    try:
        output_file.write(json.dumps(schedule_type_limit_by_identifier(
            schedule_type_limit_id).to_dict()))
    except Exception as e:
        _logger.exception(
            'Retrieval from schedule type limit library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedule-by-id')
@click.argument('schedule-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_by_id(schedule_id, complete, output_file):
    """Get a schedule definition from the standards lib with its identifier.

    \b
    Args:
        schedule_id: The identifier of a schedule in the library.
    """
    try:
        abridged = not complete
        output_file.write(json.dumps(schedule_by_identifier(
            schedule_id).to_dict(abridged=abridged)))
    except Exception as e:
        _logger.exception('Retrieval from schedule library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('program-type-by-id')
@click.argument('program-type-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def program_type_by_id(program_type_id, complete, output_file):
    """Get a program type definition from the standards lib with its identifier.

    \b
    Args:
        program_type_id: The identifier of a program type in the library.
    """
    try:
        abridged = not complete
        output_file.write(json.dumps(program_type_by_identifier(
            program_type_id).to_dict(abridged=abridged)))
    except Exception as e:
        _logger.exception('Retrieval from program type library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('materials-by-id')
@click.argument('material-ids', nargs=-1)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def materials_by_id(material_ids, output_file):
    """Get several material definitions from the standards lib at once.

    \b
    Args:
        material_ids: Any number of material identifiers to be retrieved from
            the library.
    """
    try:
        mats = []
        for mat_id in material_ids:
            try:
                mats.append(opaque_material_by_identifier(mat_id))
            except ValueError:
                mats.append(window_material_by_identifier(mat_id))
        output_file.write(json.dumps([mat.to_dict() for mat in mats]))
    except Exception as e:
        _logger.exception(
            'Retrieval from material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('constructions-by-id')
@click.argument('construction-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def constructions_by_id(construction_ids, complete, output_file):
    """Get several construction definitions from the standards lib at once.

    \b
    Args:
        construction_ids: Any number of construction identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        cons = []
        for con_id in construction_ids:
            try:
                cons.append(opaque_construction_by_identifier(
                    con_id).to_dict(abridged=abridged))
            except ValueError:
                try:
                    cons.append(window_construction_by_identifier(
                        con_id).to_dict(abridged=abridged))
                except ValueError:
                    cons.append(shade_construction_by_identifier(con_id).to_dict())
        output_file.write(json.dumps(cons))
    except Exception as e:
        _logger.exception(
            'Retrieval from construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('construction-sets-by-id')
@click.argument('construction-set-ids', nargs=-1)
@click.option('--none-defaults/--include-defaults', ' /-d', help='Flag to note whether '
              'default constructions in the set should be included in detail or should '
              'be None.', default=True, show_default=True)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_sets_by_id(construction_set_ids, none_defaults, complete, output_file):
    """Get several construction set definitions from the standards lib at once.

    \b
    Args:
        construction_set_ids: Any number of construction set identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        cons = []
        for con_id in construction_set_ids:
            cons.append(construction_set_by_identifier(con_id))
        output_file.write(json.dumps([con.to_dict(
            none_for_defaults=none_defaults, abridged=abridged) for con in cons]))
    except Exception as e:
        _logger.exception(
            'Retrieval from construction set library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedule-type-limits-by-id')
@click.argument('schedule-type-limit-ids', nargs=-1)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limits_by_id(schedule_type_limit_ids, output_file):
    """Get several schedule type limit definitions from the standards lib at once.

    \b
    Args:
        schedule_type_limit_ids: Any number of schedule type limit identifiers to be
            retrieved from the library.
    """
    try:
        stls = []
        for stl_id in schedule_type_limit_ids:
            stls.append(schedule_type_limit_by_identifier(stl_id))
        output_file.write(json.dumps([stl.to_dict() for stl in stls]))
    except Exception as e:
        _logger.exception(
            'Retrieval from schedule type limit library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('schedules-by-id')
@click.argument('schedule-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules_by_id(schedule_ids, complete, output_file):
    """Get several schedule definitions from the standards lib at once.

    \b
    Args:
        schedule_ids: Any number of schedule identifiers to be retrieved from
            the library.
    """
    try:
        abridged = not complete
        schs = []
        for sch_id in schedule_ids:
            schs.append(schedule_by_identifier(sch_id))
        output_file.write(json.dumps([sch.to_dict(abridged=abridged) for sch in schs]))
    except Exception as e:
        _logger.exception('Retrieval from schedule library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('program-types-by-id')
@click.argument('program-type-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note wether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def program_types_by_id(program_type_ids, complete, output_file):
    """Get several program type definitions from the standards lib at once.

    \b
    Args:
        program_type_ids: Any number of program type identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        prgs = []
        for prg_id in program_type_ids:
            prgs.append(program_type_by_identifier(prg_id))
        output_file.write(json.dumps([prg.to_dict(abridged=abridged) for prg in prgs]))
    except Exception as e:
        _logger.exception('Retrieval from program type library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('to-model-properties')
@click.option(
    '--standards-folder', '-s', default=None, help='A directory containing subfolders '
    'of resource objects (constructions, constructionsets, schedules, programtypes) '
    'to be loaded as ModelEnergyProperties. Note that this standards folder MUST '
    'contain these subfolders. Each sub-folder can contain JSON files of objects '
    'following honeybee schema or IDF files (if appropriate). If None, the honeybee '
    'default standards folder will be used.',type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--output-file', '-f', help='Optional JSON file to output the JSON string of '
    'the translation. By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True
)
def to_model_properties(standards_folder, output_file):
    """Translate a lib folder of standards to a JSON of honeybee ModelEnergyProperties.

    This is useful in workflows where one must import everything within a user's
    standards folder and requires all objects to be in a consistent format.
    All objects in the resulting ModelEnergyProperties will be abridged and
    duplicated objects in the folder will be removed such that there
    is only one of each object.
    """
    try:
        # set the folder to the default standards_folder if unspecified
        folder = standards_folder if standards_folder is not None else \
            folders.standards_data_folder

        # load schedules from the standards folder
        sch_folder = os.path.join(folder, 'schedules')
        type_lim = load_type_limits_from_folder(sch_folder)
        tl_with_default = type_lim.copy()
        tl_with_default.update(_schedule_type_limits)
        scheds = load_schedules_from_folder(sch_folder, tl_with_default)

        # load program types from the standards folder
        prog_folder = os.path.join(folder, 'programtypes')
        all_progs, misc_p_scheds = load_programtypes_from_folder(prog_folder, scheds)

        # load constructions from the standards folder
        con_folder = os.path.join(folder, 'constructions')
        opaque_m, window_m = load_materials_from_folder(con_folder)
        all_m = opaque_m.copy()
        all_m.update(window_m)
        opaque_c, window_c, shade_c, opaque_mc, window_mc, misc_m, misc_c_scheds = \
            load_constructions_from_folder(con_folder, all_m, scheds)
        all_m.update(opaque_mc)
        all_m.update(window_mc)
        all_c = opaque_c.copy()
        all_c.update(window_c)
        all_c.update(shade_c)

        # load construction sets from the standards folder
        con_set_folder = os.path.join(folder, 'constructionsets')
        all_con_sets, misc_c = load_constructionsets_from_folder(con_set_folder, all_c)

        # get sets of unique objects
        all_scheds = set(list(scheds.values()) + misc_p_scheds + misc_c_scheds)
        sched_tl = [sch.schedule_type_limit for sch in all_scheds
                    if sch.schedule_type_limit is not None]
        all_typ_lim = set(list(type_lim.values()) + sched_tl)
        all_cons = set(list(all_c.values()) + misc_c)
        misc_c_mats = []
        for m_con in misc_c:
            try:
                misc_c_mats.extend(m_con.materials)
            except AttributeError:  # not a construction with materials
                pass
        all_mats = set(list(all_m.values()) + misc_m + misc_c_mats)

        # add all object dictionaries into one object
        base = {'type': 'ModelEnergyProperties'}
        base['schedule_type_limits'] = [tl.to_dict() for tl in all_typ_lim]
        base['schedules'] = [sch.to_dict(abridged=True) for sch in all_scheds]
        base['programtypes'] = [pro.to_dict(abridged=True) for pro in all_progs.values()]
        base['materials'] = [m.to_dict() for m in all_mats]
        base['constructions'] = []
        for con in all_cons:
            try:
                base['constructions'].append(con.to_dict(abridged=True))
            except TypeError:  # no abridged option
                base['constructions'].append(con.to_dict())
        base['construction_sets'] = \
            [cs.to_dict(abridged=True) for cs in all_con_sets.values()]

        # write out the JSON file
        output_file.write(json.dumps(base))
    except Exception as e:
        _logger.exception('Loading standards to properties failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
