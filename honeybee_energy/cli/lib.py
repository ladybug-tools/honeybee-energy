"""honeybee energy standards library commands."""
import click
import sys
import os
import logging
import json
import zipfile
from datetime import datetime

from honeybee_energy.config import folders
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.material.dictutil import dict_to_material, MATERIAL_TYPES

from honeybee_energy.lib.materials import opaque_material_by_identifier, \
    window_material_by_identifier, OPAQUE_MATERIALS, WINDOW_MATERIALS
from honeybee_energy.lib.constructions import opaque_construction_by_identifier, \
    window_construction_by_identifier, shade_construction_by_identifier, \
    OPAQUE_CONSTRUCTIONS, WINDOW_CONSTRUCTIONS, SHADE_CONSTRUCTIONS, \
    lib_dict_abridged_to_construction
from honeybee_energy.lib.constructionsets import construction_set_by_identifier, \
    CONSTRUCTION_SETS, lib_dict_abridged_to_construction_set
from honeybee_energy.lib.scheduletypelimits import schedule_type_limit_by_identifier, \
    SCHEDULE_TYPE_LIMITS
from honeybee_energy.lib.schedules import schedule_by_identifier, SCHEDULES, \
    lib_dict_abridged_to_schedule
from honeybee_energy.lib.programtypes import program_type_by_identifier, PROGRAM_TYPES, \
    lib_dict_abridged_to_program_type

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
        output_file.write(
            json.dumps(opaque_material_by_identifier(material_id).to_dict())
        )
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
        output_file.write(
            json.dumps(window_material_by_identifier(material_id).to_dict())
        )
    except Exception as e:
        _logger.exception(
            'Retrieval from window material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('opaque-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True)
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True)
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
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
    '--standards-folder', '-s', default=None, help='A directory containing sub-folders '
    'of resource objects (constructions, constructionsets, schedules, programtypes) '
    'to be loaded as ModelEnergyProperties. Note that this standards folder MUST '
    'contain these sub-folders. Each sub-folder can contain JSON files of objects '
    'following honeybee schema or IDF files (if appropriate). If unspecified, the '
    'current user honeybee default standards folder will be used.', type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--exclude-abridged/--include-abridged', ' /-a', help='Flag to note whether '
    'fully abridged objects in the user standards library should be included in '
    'the output file. This is useful when some of the sub-objects contained within '
    'the user standards are referenced in another installed standards package that '
    'is not a part of the user personal standards library (eg. honeybee-energy-'
    'standards). When abridged objects are excluded, only objects that contain all '
    'sub-objects within the user library will be in the output-file.',
    default=True, show_default=True
)
@click.option(
    '--output-file', '-f', help='Optional JSON file to output the JSON string of '
    'the translation. By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True
)
def to_model_properties(standards_folder, exclude_abridged, output_file):
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
                if m_con.has_frame:
                    misc_c_mats.append(m_con.frame)
                if m_con.has_shade:
                    if m_con.is_switchable_glazing:
                        misc_c_mats.append(m_con.switched_glass_material)
            except AttributeError:  # not a construction with materials
                pass
        all_mats = set(list(all_m.values()) + misc_m + misc_c_mats)

        # add all object dictionaries into one object
        base = {'type': 'ModelEnergyProperties'}
        base['schedule_type_limits'] = [tl.to_dict() for tl in all_typ_lim]
        base['schedules'] = [sch.to_dict(abridged=True) for sch in all_scheds]
        base['program_types'] = \
            [pro.to_dict(abridged=True) for pro in all_progs.values()]
        base['materials'] = [m.to_dict() for m in all_mats]
        base['constructions'] = []
        for con in all_cons:
            try:
                base['constructions'].append(con.to_dict(abridged=True))
            except TypeError:  # no abridged option
                base['constructions'].append(con.to_dict())
        base['construction_sets'] = \
            [cs.to_dict(abridged=True) for cs in all_con_sets.values()]

        # if set to include abridged, add any of such objects to the dictionary
        if not exclude_abridged:
            _add_abridged_objects(base['schedules'], sch_folder, ('ScheduleTypeLimit',))
            _add_abridged_objects(base['program_types'], prog_folder)
            _add_abridged_objects(base['constructions'], con_folder, MATERIAL_TYPES)
            _add_abridged_objects(base['construction_sets'], con_set_folder)

        # write out the JSON file
        output_file.write(json.dumps(base, indent=4))
    except Exception as e:
        _logger.exception('Loading standards to properties failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def _add_abridged_objects(model_prop_array, lib_folder, ex_types=()):
    """Add abridged resource objects to an existing model properties array.
    
    Args:
        model_prop_array: An array of resource object dictionaries from a
            ModelEnergyProperties dictionary.
        lib_folder: A folder from which abridged objects will be loaded.
        exclude_types: An optional tuple of object types to be excluded
            from the result.
    """
    obj_ids = set(obj['identifier'] for obj in model_prop_array)
    for f in os.listdir(lib_folder):
        f_path = os.path.join(lib_folder, f)
        if os.path.isfile(f_path) and f_path.endswith('.json'):
            with open(f_path) as json_file:
                data = json.load(json_file)
            if 'type' in data:  # single object
                if data['identifier'] not in obj_ids and data['type'] not in ex_types:
                    model_prop_array.append(data)
            else:  # a collection of several objects
                for obj_identifier in data:
                    if obj_identifier not in obj_ids and \
                            data[obj_identifier]['type'] not in ex_types:
                        model_prop_array.append(data[obj_identifier])


@lib.command('purge')
@click.option(
    '--standards-folder', '-s', default=None, help='A directory containing sub-folders '
    'of resource objects (constructions, constructionsets, schedules, programtypes) '
    'to be purged of files. If unspecified, the current user honeybee '
    'default standards folder will be used.', type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--json-only/--all', ' /-a', help='Flag to note whether only JSON files should '
    'be purged from the library or all files should be purged, including IDF files. '
    'Given that all objects added to the library through the `add` command will always '
    'be JSON, only purging the JSONs is useful when one wishes to clear these objects '
    'while preserving objects that originated from other sources.',
    default=True, show_default=True
)
@click.option(
    '--backup/--no-backup', ' /-xb', help='Flag to note whether a backup .zip file '
    'of the user standards library should be made before the purging operation. '
    'This is done by default in case the user ever wants to recover their old '
    'standards but can be turned off if a backup is not desired.',
    default=True, show_default=True
)
@click.option(
    '--log-file', '-log', help='Optional file to output a log of the purging process. '
    'By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True
)
def purge_lib(standards_folder, json_only, backup, log_file):
    """Purge the library of all user energy standards that it contains.

    This is useful when a user's standard library has become filled with duplicated
    objects or the user wishes to start fresh by re-exporting updated objects.
    """
    try:
        # set the folder to the default standards_folder if unspecified
        folder = standards_folder if standards_folder is not None else \
            folders.standards_data_folder
        resources = ('constructions', 'constructionsets', 'schedules', 'programtypes')
        sub_folders = [os.path.join(folder, std) for std in resources]

        # make a backup of the folder if requested
        if backup:
            r_names, s_files, s_paths = [], [], []
            for sf, r_name in zip(sub_folders, resources):
                for s_file in os.listdir(sf):
                    s_path = os.path.join(sf, s_file)
                    if os.path.isfile(s_path):
                        r_names.append(r_name)
                        s_files.append(s_file)
                        s_paths.append(s_path)
            if len(s_paths) != 0:  # there are resources to back up
                backup_name = '.standards_backup_{}.zip'.format(
                    str(datetime.now()).split('.')[0].replace(':', '-'))
                backup_file = os.path.join(os.path.dirname(folder), backup_name)
                with zipfile.ZipFile(backup_file, 'w') as zf:
                    for r_name, s_file, s_path in zip(r_names, s_files, s_paths):
                        zf.write(s_path, os.path.join(r_name, s_file))

        # loop through the sub-folders and delete the files
        rel_files = []
        for sf in sub_folders:
            for s_file in os.listdir(sf):
                s_path = os.path.join(sf, s_file)
                if os.path.isfile(s_path):
                    if json_only:
                        if s_file.lower().endswith('.json'):
                            rel_files.append(s_path)
                    else:
                        rel_files.append(s_path)
        purged_files, fail_files = [], []
        for rf in rel_files:
            try:
                os.remove(rf)
                purged_files.append(rf)
            except Exception:
                fail_files.append(rf)

        # report all of the deleted files in the log file
        if len(rel_files) == 0:
            log_file.write('The standards folder is empty so no files were removed.')
        if len(purged_files) != 0:
            msg = 'The following files were removed in the purging ' \
                'operations:\n{}\n'.format('  \n'.join(purged_files))
            log_file.write(msg)
        if len(fail_files) != 0:
            msg = 'The following files could not be removed in the purging ' \
                'operations:\n{}\n'.format('  \n'.join(fail_files))
            log_file.write(msg)
    except Exception as e:
        _logger.exception('Purging user standards library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@lib.command('add')
@click.argument('properties-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--standards-folder', '-s', default=None, help='A directory containing sub-folders '
    'of resource objects (constructions, constructionsets, schedules, programtypes) '
    'to which the properties-file objects will be added. If unspecified, the current '
    'user honeybee default standards folder will be used.', type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--log-file', '-log', help='Optional file to output a log of the purging process. '
    'By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True
)
def add_to_lib(properties_file, standards_folder, log_file):
    """Add an object or set of objects to the user's standard library.

    \b
    Args:
        properties_file: A JSON file of a ModelEnergyProperties object containing
            the objects to be written into the user standards library. All sub-objects
            within this ModelEnergyProperties object must be Abridged if the sub-object
            has an abridged schema and these abridged schemas are allowed to
            reference either other objects in the ModelEnergyProperties or existing
            objects within the standards library.
    """
    try:
        # set the folder to the default standards_folder if unspecified
        folder = standards_folder if standards_folder is not None else \
            folders.standards_data_folder

        # load up the model energy properties from the JSON
        with open(properties_file) as inf:
            data = json.load(inf)
        assert 'type' in data, 'Properties file lacks required type key.'
        assert data['type'] == 'ModelEnergyProperties', 'Expected ' \
            'ModelEnergyProperties JSON object. Got {}.'.format(data['type'])
        success_objects, dup_id_objects, mis_dep_objects = [], [], []

        # extract, check, and write the schedule type limits
        sch_tl = {}
        if 'schedule_type_limits' in data and data['schedule_type_limits'] is not None:
            for stl_obj in data['schedule_type_limits']:
                msg = _object_message('Schedule Type Limit', stl_obj)
                if stl_obj['identifier'] in _schedule_type_limits:
                    dup_id_objects.append(msg)
                else:
                    try:
                        sch_tl[stl_obj['identifier']] = \
                            ScheduleTypeLimit.from_dict(stl_obj)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if sch_tl:
            sch_tl_dict = {tl.identifier: tl.to_dict() for tl in sch_tl.values()}
            stl_json = os.path.join(folder, 'schedules', 'custom_type_limits.json')
            _update_user_json(sch_tl_dict, stl_json)

        # extract, check, and write the schedules
        scheds = {}
        if 'schedules' in data and data['schedules'] is not None:
            for sch in data['schedules']:
                msg = _object_message('Schedule', sch)
                if sch['identifier'] in SCHEDULES:
                    dup_id_objects.append(msg)
                else:
                    try:
                        scheds[sch['identifier']] = \
                            lib_dict_abridged_to_schedule(sch, sch_tl)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if scheds:
            sch_dict = {s.identifier: s.to_dict(abridged=True) for s in scheds.values()}
            sch_json = os.path.join(folder, 'schedules', 'custom_schedules.json')
            _update_user_json(sch_dict, sch_json)

        # extract, check, and write the program types
        progs = {}
        if 'program_types' in data and data['program_types'] is not None:
            for prog in data['program_types']:
                msg = _object_message('Program', prog)
                if prog['identifier'] in PROGRAM_TYPES:
                    dup_id_objects.append(msg)
                else:
                    try:
                        progs[prog['identifier']] = \
                            lib_dict_abridged_to_program_type(prog, scheds)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if progs:
            prog_dict = {p.identifier: p.to_dict(abridged=True) for p in progs.values()}
            program_json = os.path.join(folder, 'programtypes', 'custom_programs.json')
            _update_user_json(prog_dict, program_json)

        # extract, check, and write the materials
        mats = {}
        if 'materials' in data and data['materials'] is not None and \
                len(data['materials']) != 0:
            all_mats = OPAQUE_MATERIALS + WINDOW_MATERIALS
            for mat_obj in data['materials']:
                msg = _object_message('Material', mat_obj)
                if mat_obj['identifier'] in all_mats:
                    dup_id_objects.append(msg)
                else:
                    try:
                        mats[mat_obj['identifier']] = dict_to_material(mat_obj)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if mats:
            mat_dict = {m.identifier: m.to_dict() for m in mats.values()}
            mat_json = os.path.join(folder, 'constructions', 'custom_materials.json')
            _update_user_json(mat_dict, mat_json)

        # extract, check, and write the constructions
        cons = {}
        if 'constructions' in data and data['constructions'] is not None and \
                len(data['constructions']) != 0:
            all_cons = OPAQUE_CONSTRUCTIONS + WINDOW_CONSTRUCTIONS + SHADE_CONSTRUCTIONS
            for con in data['constructions']:
                msg = _object_message('Construction', con)
                if con['identifier'] in all_cons:
                    dup_id_objects.append(msg)
                else:
                    try:
                        cons[con['identifier']] = \
                            lib_dict_abridged_to_construction(con, mats, scheds)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if cons:
            con_dict = {}
            for c in cons.values():
                try:
                    con_dict[c.identifier] = c.to_dict(abridged=True)
                except TypeError:  # ShadeConstruction
                    con_dict[c.identifier] = c.to_dict()
            con_json = os.path.join(folder, 'constructions', 'custom_constructions.json')
            _update_user_json(con_dict, con_json)

        # extract, check, and write the construction sets
        con_sets = {}
        if 'construction_sets' in data and data['construction_sets'] is not None:
            for cs in data['construction_sets']:
                msg = _object_message('Construction Set', cs)
                if cs['identifier'] in CONSTRUCTION_SETS:
                    dup_id_objects.append(msg)
                else:
                    try:
                        con_sets[cs['identifier']] = \
                            lib_dict_abridged_to_construction_set(cs, cons)
                        success_objects.append(msg)
                    except (ValueError, KeyError, AssertionError):
                        mis_dep_objects.append(msg)
        if con_sets:
            cs_dict = {c.identifier: c.to_dict(abridged=True) for c in con_sets.values()}
            cs_json = os.path.join(folder, 'constructionsets', 'custom_sets.json')
            _update_user_json(cs_dict, cs_json)

        # write a report of the objects that were or were not added
        success_objects, dup_id_objects, mis_dep_objects
        m_start = 'THESE OBJECTS'
        if len(success_objects) != 0:
            msg = '{} WERE SUCCESSFULLY ADDED TO THE STANDARDS LIBRARY:\n{}\n\n'.format(
                m_start, '  \n'.join(success_objects))
            log_file.write(msg)
        if len(dup_id_objects) != 0:
            msg = '{} WERE NOT ADDED SINCE THEY ALREADY EXIST IN THE STANDARDS ' \
                'LIBRARY:\n{}\n\n'.format(m_start, '  \n'.join(dup_id_objects))
            log_file.write(msg)
        if len(mis_dep_objects) != 0:
            msg = '{} WERE NOT ADDED BECAUSE THEY ARE INVALID OR ARE MISSING ' \
                'DEPENDENT OBJECTS:\n{}\n\n'.format(m_start, '  \n'.join(mis_dep_objects))
            log_file.write(msg)
    except Exception as e:
        _logger.exception('Adding to user standards library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def _object_message(obj_type, obj_dict):
    """Get the reporting message of an object to add to the user library."""
    obj_name = obj_dict['display_name'] if 'display_name' in obj_dict and \
        obj_dict['display_name'] is not None else obj_dict['identifier']
    return '{}: {}'.format(obj_type, obj_name)


def _update_user_json(dict_to_add, user_json):
    """Update a JSON file within a user standards folder."""
    if os.path.isfile(user_json):
        with open(user_json) as inf:
            exist_data = json.load(inf)
        dict_to_add.update(exist_data)
    with open(user_json, 'w') as outf:
        json.dump(dict_to_add, outf, indent=4)
