"""honeybee energy standards library commands."""
import click
import sys
import os
import logging
import json
import zipfile
from datetime import datetime

from ladybug.commandutil import process_content_to_output
from honeybee.search import filter_array_by_keywords

from honeybee_energy.config import folders
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.material.dictutil import dict_to_material, MATERIAL_TYPES
from honeybee_energy.run import HB_OS_MSG

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
    STANDARDS_REGISTRY, lib_dict_abridged_to_program_type

from honeybee_energy.lib._loadtypelimits import load_type_limits_from_folder, \
    _schedule_type_limits
from honeybee_energy.lib._loadschedules import load_schedules_from_folder, \
    _default_schedules
from honeybee_energy.lib._loadprogramtypes import load_programtypes_from_folder, \
    _default_programs
from honeybee_energy.lib._loadmaterials import load_materials_from_folder, \
    _default_mats
from honeybee_energy.lib._loadconstructions import load_constructions_from_folder, \
    _default_constrs
from honeybee_energy.lib._loadconstructionsets import \
    load_constructionsets_from_folder, _default_sets

_logger = logging.getLogger(__name__)


@click.group(help='Commands for retrieving objects from the standards library.')
def lib():
    pass


@lib.command('opaque-materials')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available materials will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Concrete" -k "Heavyweight"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def opaque_materials_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all opaque materials in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        opaque_materials(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load opaque materials.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def opaque_materials(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all opaque materials in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            materials. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available materials
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the material
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        mat_ids = sorted(filter_array_by_keywords(OPAQUE_MATERIALS, kwd, split_words))
    else:
        mat_ids = OPAQUE_MATERIALS
    # output a list of identifiers or objects
    if json_objects:
        mat_objs = [opaque_material_by_identifier(m) for m in mat_ids]
        out_str = json.dumps([m.to_dict() for m in mat_objs])
    else:
        out_str = '\n'.join(mat_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('window-materials')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available materials will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Generic" -k "Gap"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def window_materials_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all window materials in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        window_materials(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load window materials.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def window_materials(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all window materials in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            materials. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available materials
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the material
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        mat_ids = sorted(filter_array_by_keywords(WINDOW_MATERIALS, kwd, split_words))
    else:
        mat_ids = WINDOW_MATERIALS
    # output a list of identifiers or objects
    if json_objects:
        mat_objs = [window_material_by_identifier(m) for m in mat_ids]
        out_str = json.dumps([m.to_dict() for m in mat_objs])
    else:
        out_str = '\n'.join(mat_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('opaque-constructions')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available constructions will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Generic" -k "Underground"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def opaque_constructions_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all opaque constructions in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        opaque_constructions(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load opaque constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def opaque_constructions(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all opaque constructions in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            constructions. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available constructions
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the construction
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        con_ids = sorted(filter_array_by_keywords(OPAQUE_CONSTRUCTIONS, kwd, split_words))
    else:
        con_ids = OPAQUE_CONSTRUCTIONS
    # output a list of identifiers or objects
    if json_objects:
        con_objs = [opaque_construction_by_identifier(c) for c in con_ids]
        out_str = json.dumps([c.to_dict() for c in con_objs])
    else:
        out_str = '\n'.join(con_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('window-constructions')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available constructions will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Generic" -k "Double"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def window_constructions_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all window constructions in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        window_constructions(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load window constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def window_constructions(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all window constructions in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            constructions. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available constructions
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the construction
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        con_ids = sorted(filter_array_by_keywords(WINDOW_CONSTRUCTIONS, kwd, split_words))
    else:
        con_ids = WINDOW_CONSTRUCTIONS
    # output a list of identifiers or objects
    if json_objects:
        con_objs = [window_construction_by_identifier(c) for c in con_ids]
        out_str = json.dumps([c.to_dict() for c in con_objs])
    else:
        out_str = '\n'.join(con_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('shade-constructions')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available constructions will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Generic" -k "Context"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def shade_constructions_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all shade constructions in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        shade_constructions(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load shade constructions.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def shade_constructions(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all shade constructions in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            constructions. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available constructions
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the construction
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        con_ids = sorted(filter_array_by_keywords(SHADE_CONSTRUCTIONS, kwd, split_words))
    else:
        con_ids = SHADE_CONSTRUCTIONS
    # output a list of identifiers or objects
    if json_objects:
        con_objs = [shade_construction_by_identifier(c) for c in con_ids]
        out_str = json.dumps([c.to_dict() for c in con_objs])
    else:
        out_str = '\n'.join(con_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('construction-sets')
@click.option(
    '--climate-zone', '-z', help='An optional integer between 0 and 8 for the '
    'ASHRAE climate zone for which construction sets will be filtered. This can '
    'include the letter associated with the zone (eg. 5A).', type=str, default=None)
@click.option(
    '--vintage', '-v', help='Optional text for the building vintage to filter the '
    'sets. Choose from: "2019", "2016", "2013", "2010", "2007", "2004", '
    '"1980_2004", "pre_1980". Note that vintages are often called "templates" '
    'within the OpenStudio standards gem and this property effectively maps to '
    'the standards gem "template".', type=str, default=None)
@click.option(
    '--construction-type', '-t', help='Optional text for the construction type '
    'to filter the sets. Choose from: "SteelFramed", "WoodFramed", "Mass", '
    '"Metal Building".', type=str, default=None)
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter the '
    'output. If nothing is input here, all available construction sets will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Generic" -k "Context"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'material identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def construction_sets_cli(
    climate_zone, vintage, construction_type, keyword, split_words,
    identifiers, output_file
):
    """Get a list of all construction sets in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        construction_sets(climate_zone, vintage, construction_type,
                          keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load construction sets.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def construction_sets(
    climate_zone=None, vintage=None, construction_type=None,
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all construction sets in the standards library.

    Args:
        climate_zone: An optional integer between 0 and 8 for the ASHRAE climate
            zone for which construction sets will be filtered. This can include
            the letter associated with the zone (eg. 5A).
        vintage: Optional text for the building vintage to filter the sets.
            Choose from: "2019", "2016", "2013", "2010", "2007", "2004",
            "1980_2004", "pre_1980".
        construction_type: Optional text for the construction type to filter
            the sets. Choose from: "SteelFramed", "WoodFramed", "Mass", "Metal Building".
        keyword: An optional keyword to be used to filter the output list of
            construction sets. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available construction sets
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the construction
            set identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # process the specific types of filters
    base_str = ''
    if vintage is not None:
        assert vintage in STANDARDS_REGISTRY.keys(), \
            'Input vintage "{}" is not valid. Choose from:\n' \
            '{}'.format(vintage, '\n'.join(STANDARDS_REGISTRY.keys()))
        base_str = '{}::'.format(vintage)
    if climate_zone is not None:
        c_zone = (climate_zone)[0]  # strip out any qualifiers like A, b, or C
        assert 0 <= int(c_zone) <= 8, 'Input climate_zone "{}" is not valid. ' \
            'Climate zone must be between 0 and 8.'.format(climate_zone)
        base_str = '{}ClimateZone{}::'.format(base_str, c_zone)
    if construction_type is not None:
        CONSTRUCTION_TYPES = ('SteelFramed', 'WoodFramed', 'Mass', 'Metal Building')
        assert construction_type in CONSTRUCTION_TYPES, \
            'Input construction_type "{}" is not valid. Choose from:\n' \
            '{}'.format(construction_type, '\n'.join(CONSTRUCTION_TYPES))
        base_str = '{}{}'.format(base_str, construction_type)
    if base_str:
        con_ids = sorted(filter_array_by_keywords(CONSTRUCTION_SETS, [base_str]))
    else:
        con_ids = CONSTRUCTION_SETS
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        con_ids = sorted(filter_array_by_keywords(con_ids, kwd, split_words))
    # output a list of identifiers or objects
    if json_objects:
        con_objs = [construction_set_by_identifier(c) for c in con_ids]
        out_str = json.dumps([c.to_dict() for c in con_objs])
    else:
        out_str = '\n'.join(con_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('schedule-type-limits')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available limits will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Concrete" -k "Heavyweight"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'schedule type limit identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def schedule_type_limits_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all schedule type limits in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        schedule_type_limits(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load schedule type limits.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedule_type_limits(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all schedule type limits in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            limits. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available limits
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the limit
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        stl_ids = sorted(filter_array_by_keywords(SCHEDULE_TYPE_LIMITS, kwd, split_words))
    else:
        stl_ids = SCHEDULE_TYPE_LIMITS
    # output a list of identifiers or objects
    if json_objects:
        stl_objs = [schedule_type_limit_by_identifier(t) for t in stl_ids]
        out_str = json.dumps([t.to_dict() for t in stl_objs])
    else:
        out_str = '\n'.join(stl_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('schedules')
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter '
    'the output. If nothing is input here, all available schedules will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Concrete" -k "Heavyweight"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'schedule identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def schedules_cli(keyword, split_words, identifiers, output_file):
    """Get a list of all schedules in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        schedules(keyword, join_words, json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load schedules.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedules(
    keyword=None, join_words=False, json_objects=False, output_file=None,
    split_words=True, identifiers=True
):
    """Get a list of all schedules in the standards library.

    Args:
        keyword: An optional keyword to be used to filter the output list of
            schedules. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available limits
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the schedule
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        sch_ids = sorted(filter_array_by_keywords(SCHEDULES, kwd, split_words))
    else:
        sch_ids = SCHEDULES
    # output a list of identifiers or objects
    if json_objects:
        sch_objs = [schedule_by_identifier(t) for t in sch_ids]
        out_str = json.dumps([t.to_dict() for t in sch_objs])
    else:
        out_str = '\n'.join(sch_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('program-types')
@click.option(
    '--building-type', '-b', help='Optional text to filter the programs by '
    'building type (eg. "LargeOffice", "MidriseApartment", etc.).',
    type=str, default=None)
@click.option(
    '--vintage', '-v', help='Optional text for the building vintage to filter the '
    'programs. Choose from: "2019", "2016", "2013", "2010", "2007", "2004", '
    '"1980_2004", "pre_1980". Note that vintages are often called "templates" '
    'within the OpenStudio standards gem and this property effectively maps to '
    'the standards gem "template".', type=str, default=None)
@click.option(
    '--keyword', '-k', help='Text for an optional keyword to be used to filter the '
    'output. If nothing is input here, all available programs will be output. '
    'Multiple keywords can be requested by using multiple -k options. For example\n'
    ' -k "Hospital" -k "ICU"', type=str, default=None, multiple=True)
@click.option(
    '--split-words/--join-words', ' /-w', help='Flag to note whether strings '
    'of multiple keywords (separated by spaces) are split into separate '
    'keywords for searching. This results in a greater likelihood of finding '
    'an item in the search but it is not be desirable when searching for a '
    'specific word sequence.', default=True, show_default=True)
@click.option(
    '--identifiers/--json-objects', ' /-j', help='Flag to note whether to format the '
    'output as an array of JSON objects instead of a plain text list of the '
    'program identifiers.', default=True, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional file to output the result. By default, it '
    'is printed out to stdout', type=click.File('w'), default='-', show_default=True)
def program_types_cli(
    building_type, vintage, keyword, split_words, identifiers, output_file
):
    """Get a list of all program_types in the standards library."""
    try:
        join_words = not split_words
        json_objects = not identifiers
        program_types(building_type, vintage, keyword, join_words,
                      json_objects, output_file)
    except Exception as e:
        _logger.exception('Failed to load program types.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def program_types(
    building_type=None, vintage=None, keyword=None, join_words=False,
    json_objects=False, output_file=None, split_words=True, identifiers=True
):
    """Get a list of all construction sets in the standards library.

    Args:
        building_type: Optional text to filter the programs by building
            type (eg. "LargeOffice", "MidriseApartment", etc.).
        vintage: Optional text for the building vintage to filter the programs.
            Choose from: "2019", "2016", "2013", "2010", "2007", "2004",
            "1980_2004", "pre_1980".
        keyword: An optional keyword to be used to filter the output list of
            programs. This can also be a list of keywords which will collectively
            be used to filter the results. If None, all available programs
            will be output. (Default: None).
        join_words: Boolean to note whether strings of multiple keywords (separated
            by spaces) are joined together or will be split into separate keywords
            for searching. This results in a greater likelihood of finding an item but is
            not desirable when searching for a specific word sequence. (Default: False).
        json_objects: Boolean to note whether the output should be formatted as
            an array of JSON objects instead of a plain text list of the program
            identifiers currently in the library. (Default: False).
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    # process the specific types of filters
    base_str = ''
    if vintage is not None:
        assert vintage in STANDARDS_REGISTRY.keys(), \
            'Input vintage "{}" is not valid. Choose from:\n' \
            '{}'.format(vintage, '\n'.join(STANDARDS_REGISTRY.keys()))
        base_str = '{}::'.format(vintage)
    if building_type is not None:
        if building_type not in ('Residential', 'NonResidential'):
            assert building_type in STANDARDS_REGISTRY['2019'], \
                'Input building_type "{}" is not valid. Choose from:\n' \
                '{}'.format(building_type, '\n'.join(STANDARDS_REGISTRY['2019']))
            base_str = '{}{}'.format(base_str, building_type)
    if base_str:
        prog_ids = sorted(filter_array_by_keywords(PROGRAM_TYPES, [base_str]))
    else:
        prog_ids = PROGRAM_TYPES
    if building_type == 'Residential':
        filter_prog_ids = []
        for prog_id in prog_ids:
            if '::MidriseApartment::' in prog_id or '::HighriseApartment::' in prog_id:
                filter_prog_ids.append(prog_id)
        prog_ids = filter_prog_ids
    elif building_type == 'NonResidential':
        filter_prog_ids = []
        for prog_id in prog_ids:
            if '::MidriseApartment::' not in prog_id and \
                    '::HighriseApartment::' not in prog_id:
                filter_prog_ids.append(prog_id)
        prog_ids = filter_prog_ids
    # filter the objects by keywords
    if keyword:
        split_words = not join_words
        kwd = [keyword] if isinstance(keyword, str) else keyword
        prog_ids = sorted(filter_array_by_keywords(prog_ids, kwd, split_words))
    # output a list of identifiers or objects
    if json_objects:
        con_objs = [program_type_by_identifier(p) for p in prog_ids]
        out_str = json.dumps([p.to_dict() for p in con_objs])
    else:
        out_str = '\n'.join(prog_ids)
    return process_content_to_output(out_str, output_file)


@lib.command('opaque-material-by-id')
@click.argument('material-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_material_by_id_cli(material_id, output_file):
    """Get an opaque material definition from the standards lib with its identifier.

    \b
    Args:
        material_id: The identifier of an opaque material in the library.
    """
    try:
        opaque_material_by_id(material_id, output_file)
    except Exception as e:
        _logger.exception('Retrieval from opaque material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def opaque_material_by_id(material_id, output_file=None):
    """Get an opaque material definition from the standards lib with its identifier.

    Args:
        material_id: The identifier of an opaque material in the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_str = json.dumps(opaque_material_by_identifier(material_id).to_dict())
    return process_content_to_output(out_str, output_file)


@lib.command('window-material-by-id')
@click.argument('material-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_material_by_id_cli(material_id, output_file):
    """Get a window material definition from the standards lib with its identifier.

    \b
    Args:
        material_id: The identifier of an window material in the library.
    """
    try:
        window_material_by_id(material_id, output_file)
    except Exception as e:
        _logger.exception('Retrieval from window material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def window_material_by_id(material_id, output_file=None):
    """Get a window material definition from the standards lib with its identifier.

    Args:
        material_id: The identifier of an window material in the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_str = json.dumps(window_material_by_identifier(material_id).to_dict())
    return process_content_to_output(out_str, output_file)


@lib.command('opaque-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def opaque_construction_by_id_cli(construction_id, complete, output_file):
    """Get an opaque construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of an opaque construction in the library.
    """
    try:
        abridged = not complete
        opaque_construction_by_id(construction_id, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from opaque construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def opaque_construction_by_id(
    construction_id, abridged=False, output_file=None, complete=True
):
    """Get an opaque construction definition from the standards lib with its identifier.

    Args:
        construction_id: The identifier of an opaque construction in the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_dict = opaque_construction_by_identifier(construction_id).to_dict(abridged=abridged)
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('window-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def window_construction_by_id_cli(construction_id, complete, output_file):
    """Get a window construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of a window construction in the library.
    """
    try:
        abridged = not complete
        window_construction_by_id(construction_id, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from window construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def window_construction_by_id(
    construction_id, abridged=False, output_file=None, complete=True
):
    """Get a window construction definition from the standards lib with its identifier.

    Args:
        construction_id: The identifier of a window construction in the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_dict = window_construction_by_identifier(construction_id).to_dict(abridged=abridged)
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('shade-construction-by-id')
@click.argument('construction-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def shade_construction_by_id_cli(construction_id, output_file):
    """Get a shade construction definition from the standards lib with its identifier.

    \b
    Args:
        construction_id: The identifier of a shade construction in the library.
    """
    try:
        shade_construction_by_id(construction_id, output_file)
    except Exception as e:
        _logger.exception('Retrieval from shade construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def shade_construction_by_id(construction_id, output_file=None):
    """Get a shade construction definition from the standards lib with its identifier.

    Args:
        construction_id: The identifier of a shade construction in the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_str = json.dumps(shade_construction_by_identifier(construction_id).to_dict())
    return process_content_to_output(out_str, output_file)


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
def construction_set_by_id_cli(construction_set_id, none_defaults, complete, output_file):
    """Get a construction set definition from the standards lib with its identifier.

    \b
    Args:
        construction_set_id: The identifier of a construction set in the library.
    """
    try:
        abridged = not complete
        include_defaults = not none_defaults
        construction_set_by_id(construction_set_id, include_defaults, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from construction set library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def construction_set_by_id(
    construction_set_id, include_defaults=False, abridged=False, output_file=None,
    complete=True, none_defaults=True
):
    """Get a construction set definition from the standards lib with its identifier.

    Args:
        construction_set_id: The identifier of a construction set in the library.
        include_defaults: Boolean to note whether default constructions in the set
            should be included in or should be None.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    none_defaults = not include_defaults
    c_set = construction_set_by_identifier(construction_set_id)
    out_dict = c_set.to_dict(none_for_defaults=none_defaults, abridged=abridged)
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('schedule-type-limit-by-id')
@click.argument('schedule-type-limit-id', type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limit_by_id_cli(schedule_type_limit_id, output_file):
    """Get a schedule type limit definition from the standards lib with its identifier.

    \b
    Args:
        schedule_type_limit_id: The identifier of a schedule type limit in the library.
    """
    try:
        schedule_type_limit_by_id(schedule_type_limit_id, output_file)
    except Exception as e:
        _logger.exception(
            'Retrieval from schedule type limit library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedule_type_limit_by_id(schedule_type_limit_id, output_file=None):
    """Get a schedule type limit definition from the standards lib with its identifier.

    Args:
        schedule_type_limit_id: The identifier of a schedule type limit in the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_str = json.dumps(schedule_type_limit_by_identifier(schedule_type_limit_id).to_dict())
    return process_content_to_output(out_str, output_file)


@lib.command('schedule-by-id')
@click.argument('schedule-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_by_id_cli(schedule_id, complete, output_file):
    """Get a schedule definition from the standards lib with its identifier.

    \b
    Args:
        schedule_id: The identifier of a schedule in the library.
    """
    try:
        abridged = not complete
        schedule_by_id(schedule_id, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from schedule library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedule_by_id(schedule_id, abridged=False, output_file=None, complete=True):
    """Get a schedule definition from the standards lib with its identifier.

    Args:
        schedule_id: The identifier of a schedule in the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_dict = schedule_by_identifier(schedule_id).to_dict(abridged=abridged)
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('program-type-by-id')
@click.argument('program-type-id', type=str)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON string of '
              'the object. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def program_type_by_id_cli(program_type_id, complete, output_file):
    """Get a program type definition from the standards lib with its identifier.

    \b
    Args:
        program_type_id: The identifier of a program type in the library.
    """
    try:
        abridged = not complete
        program_type_by_id(program_type_id, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from program type library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def program_type_by_id(program_type_id, abridged=False, output_file=None, complete=True):
    """Get a program type definition from the standards lib with its identifier.

    Args:
        program_type_id: The identifier of a program type in the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    out_dict = program_type_by_identifier(program_type_id).to_dict(abridged=abridged)
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('materials-by-id')
@click.argument('material-ids', nargs=-1)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def materials_by_id_cli(material_ids, output_file):
    """Get several material definitions from the standards lib at once.

    \b
    Args:
        material_ids: Any number of material identifiers to be retrieved from
            the library.
    """
    try:
        materials_by_id(material_ids, output_file)
    except Exception as e:
        _logger.exception('Retrieval from material library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def materials_by_id(material_ids, output_file=None):
    """Get several material definitions from the standards lib at once.

    Args:
        material_ids: A list of identifiers for materials in the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    mats = []
    for mat_id in material_ids:
        try:
            mats.append(opaque_material_by_identifier(mat_id))
        except ValueError:
            mats.append(window_material_by_identifier(mat_id))
    out_str = json.dumps([mat.to_dict() for mat in mats])
    return process_content_to_output(out_str, output_file)


@lib.command('constructions-by-id')
@click.argument('construction-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def constructions_by_id_cli(construction_ids, complete, output_file):
    """Get several construction definitions from the standards lib at once.

    \b
    Args:
        construction_ids: Any number of construction identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        constructions_by_id(construction_ids, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from construction library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def constructions_by_id(
    construction_ids, abridged=False, output_file=None, complete=True
):
    """Get several construction definitions from the standards lib at once.

    Args:
        construction_ids: Any number of construction identifiers to be retrieved
            from the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    cons = []
    for con_id in construction_ids:
        try:
            con = opaque_construction_by_identifier(con_id)
            cons.append(con.to_dict(abridged=abridged))
        except ValueError:
            try:
                con = window_construction_by_identifier(con_id)
                cons.append(con.to_dict(abridged=abridged))
            except ValueError:
                cons.append(shade_construction_by_identifier(con_id).to_dict())
    return process_content_to_output(json.dumps(cons), output_file)


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
def construction_sets_by_id_cli(construction_set_ids, none_defaults, complete, output_file):
    """Get several construction set definitions from the standards lib at once.

    \b
    Args:
        construction_set_ids: Any number of construction set identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        include_defaults = not none_defaults
        construction_sets_by_id(
            construction_set_ids, include_defaults, abridged, output_file
        )
    except Exception as e:
        _logger.exception('Retrieval from construction set library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def construction_sets_by_id(
    construction_set_ids, include_defaults=False, abridged=False, output_file=None,
    complete=True, none_defaults=True
):
    """Get several construction set definitions from the standards lib at once.

    Args:
        construction_set_ids: Any number of construction set identifiers to be
            retrieved from the library.
        include_defaults: Boolean to note whether default constructions in the set
            should be included in or should be None.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    none_defaults = not include_defaults
    cons = []
    for con_id in construction_set_ids:
        cons.append(construction_set_by_identifier(con_id))
    out_dict = [con.to_dict(none_for_defaults=none_defaults, abridged=abridged)
                for con in cons]
    return process_content_to_output(json.dumps(out_dict), output_file)


@lib.command('schedule-type-limits-by-id')
@click.argument('schedule-type-limit-ids', nargs=-1)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limits_by_id_cli(schedule_type_limit_ids, output_file):
    """Get several schedule type limit definitions from the standards lib at once.

    \b
    Args:
        schedule_type_limit_ids: Any number of schedule type limit identifiers to be
            retrieved from the library.
    """
    try:
        schedule_type_limits_by_id(schedule_type_limit_ids, output_file)
    except Exception as e:
        _logger.exception('Retrieval from schedule type limit library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedule_type_limits_by_id(schedule_type_limit_ids, output_file=None):
    """Get several schedule type limit definitions from the standards lib at once.

    Args:
        schedule_type_limit_ids: Any number of schedule type limit identifiers to be
            retrieved from the library.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    stls = []
    for stl_id in schedule_type_limit_ids:
        stls.append(schedule_type_limit_by_identifier(stl_id))
    out_str = json.dumps([stl.to_dict() for stl in stls])
    return process_content_to_output(out_str, output_file)


@lib.command('schedules-by-id')
@click.argument('schedule-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules_by_id_cli(schedule_ids, complete, output_file):
    """Get several schedule definitions from the standards lib at once.

    \b
    Args:
        schedule_ids: Any number of schedule identifiers to be retrieved from
            the library.
    """
    try:
        abridged = not complete
        schedules_by_id(schedule_ids, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from schedule library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def schedules_by_id(schedule_ids, abridged=False, output_file=None, complete=True):
    """Get a schedule definition from the standards lib with its identifier.

    Args:
        schedule_ids: Any number of schedule identifiers to be retrieved from
            the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    schs = []
    for sch_id in schedule_ids:
        schs.append(schedule_by_identifier(sch_id))
    out_str = json.dumps([sch.to_dict(abridged=abridged) for sch in schs])
    return process_content_to_output(out_str, output_file)


@lib.command('program-types-by-id')
@click.argument('program-type-ids', nargs=-1)
@click.option('--complete/--abridged', ' /-a', help='Flag to note whether an abridged '
              'definition should be returned.', default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional file to output the JSON strings of '
              'the objects. By default, it will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def program_types_by_id_cli(program_type_ids, complete, output_file):
    """Get several program type definitions from the standards lib at once.

    \b
    Args:
        program_type_ids: Any number of program type identifiers to be retrieved
            from the library.
    """
    try:
        abridged = not complete
        program_types_by_id(program_type_ids, abridged, output_file)
    except Exception as e:
        _logger.exception('Retrieval from program type library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def program_types_by_id(program_type_ids, abridged=False, output_file=None, complete=True):
    """Get a program type definition from the standards lib with its identifier.

    Args:
        program_type_ids: Any number of program type identifiers to be retrieved
            from the library.
        abridged: Boolean to note whether an abridged definition should be returned.
        output_file: Optional file to output the result. If None, the string
            will be returned from this method.
    """
    prgs = []
    for prg_id in program_type_ids:
        prgs.append(program_type_by_identifier(prg_id))
    out_str = json.dumps([prg.to_dict(abridged=abridged) for prg in prgs])
    return process_content_to_output(out_str, output_file)


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


def _update_user_json(dict_to_add, user_json, indent=4):
    """Update a JSON file within a user standards folder."""
    if os.path.isfile(user_json):
        with open(user_json) as inf:
            exist_data = json.load(inf)
        dict_to_add.update(exist_data)
    with open(user_json, 'w') as outf:
        json.dump(dict_to_add, outf, indent=indent)


@lib.command('add-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--standards-folder', '-s', default=None, help='A directory containing sub-folders '
    'of resource objects (constructions, constructionsets, schedules, programtypes) '
    'to which the properties-file objects will be added. If unspecified, the current '
    'user honeybee default standards folder will be used.', type=click.Path(
        exists=True, file_okay=False, dir_okay=True, resolve_path=True))
@click.option(
    '--indent', '-i', help='Optional integer to specify the indentation in '
    'the output JSON file. Specifying an value here can produce more read-able'
    ' JSONs.', type=int, default=None, show_default=True)
@click.option(
    '--osw-folder', '-osw', help='Folder on this computer, into which the '
    'working files will be written. If None, it will be written into the a '
    'temp folder in the default simulation folder.', default=None,
    type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option(
    '--log-file', '-log', help='Optional file to output a log of the addition process. '
    'By default this will be printed out to stdout',
    type=click.File('w'), default='-', show_default=True)
def add_osm_to_lib(osm_file, standards_folder, indent, osw_folder, log_file):
    """Add all objects within an OSM file to the user's standard library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # check that honeybee-openstudio is installed
        try:
            from honeybee_openstudio.openstudio import openstudio, os_path
            from honeybee_openstudio.schedule import extract_all_schedules, \
                schedule_type_limits_from_openstudio
            from honeybee_openstudio.material import extract_all_materials
            from honeybee_openstudio.construction import extract_all_constructions
            from honeybee_openstudio.constructionset import construction_set_from_openstudio
            from honeybee_openstudio.programtype import program_type_from_openstudio
        except ImportError as e:  # honeybee-openstudio is not installed
            raise ImportError('{}\n{}'.format(HB_OS_MSG, e))

        # set the folder to the default standards_folder if unspecified
        folder = standards_folder if standards_folder is not None else \
            folders.standards_data_folder
        base_name = os.path.basename(osm_file).lower().replace('.osm', '')

        # get the version translator
        assert os.path.isfile(osm_file), 'No file was found at: {}.'.format(osm_file)
        if (sys.version_info < (3, 0)):
            ver_translator = openstudio.VersionTranslator()
        else:
            ver_translator = openstudio.osversion.VersionTranslator()
        os_model = ver_translator.loadModel(os_path(osm_file))
        # print errors and warnings from the translation process
        if not os_model.is_initialized():
            errors = '\n'.join(str(err.logMessage()) for err in ver_translator.errors())
            raise ValueError('Failed to load model from OSM.\n{}'.format(errors))
        os_model = os_model.get()

        # translate the OSM to a Honeybee objects
        type_limits = {}
        for os_type_lim in os_model.getScheduleTypeLimitss():
            type_lim = schedule_type_limits_from_openstudio(os_type_lim)
            type_limits[type_lim.identifier] = type_lim
        schedules = extract_all_schedules(os_model)
        materials = extract_all_materials(os_model)
        constructions = extract_all_constructions(os_model, schedules)
        construction_sets = {}
        for os_cons_set in os_model.getDefaultConstructionSets():
            if os_cons_set.nameString() != 'Default Generic Construction Set':
                con_set = construction_set_from_openstudio(os_cons_set, constructions)
                construction_sets[con_set.identifier] = con_set
        program_types = {}
        for os_space_type in os_model.getSpaceTypes():
            program = program_type_from_openstudio(os_space_type, schedules)
            program_types[program.identifier] = program

        # write each of the objects from the dictionary into the standards folder
        added_objs = []
        # write the materials
        con_folder = os.path.join(folder, 'constructions')
        mat_json = os.path.join(con_folder, '{}_materials.json'.format(base_name))
        mat_dict = {}
        for mat in materials.values():
            if mat.identifier not in _default_mats:
                added_objs.append(mat.identifier)
                mat_dict[mat.identifier] = mat.to_dict()
        _update_user_json(mat_dict, mat_json, indent)
        # write the constructions
        con_json = os.path.join(con_folder, '{}_constructions.json'.format(base_name))
        con_dict = {}
        for con in constructions.values():
            if con.identifier not in _default_constrs:
                added_objs.append(con.identifier)
                try:
                    con_dict[con.identifier] = con.to_dict(abridged=True)
                except TypeError:  # no abridged option
                    con_dict[con.identifier] = con.to_dict()
        _update_user_json(con_dict, con_json, indent)
        # write the construction sets
        c_set_folder = os.path.join(folder, 'constructionsets')
        c_set_json = os.path.join(c_set_folder, '{}.json'.format(base_name))
        c_set_dict = {}
        for c_set in construction_sets.values():
            if c_set.identifier not in _default_sets:
                added_objs.append(c_set.identifier)
                c_set_dict[c_set.identifier] = c_set.to_dict(abridged=True)
        _update_user_json(c_set_dict, c_set_json, indent)
        # write the type limits
        sched_folder = os.path.join(folder, 'schedules')
        stl_json = os.path.join(sched_folder, '{}_type_limits.json'.format(base_name))
        sch_tl_dict = {}
        for stl in type_limits.values():
            if stl.identifier not in _schedule_type_limits:
                added_objs.append(stl.identifier)
                sch_tl_dict[stl.identifier] = stl.to_dict()
        _update_user_json(sch_tl_dict, stl_json, indent)
        # write the schedules
        sch_json = os.path.join(sched_folder, '{}_schedules.json'.format(base_name))
        sch_dict = {}
        for sch in schedules.values():
            if sch.identifier not in _default_schedules:
                added_objs.append(sch.identifier)
                sch_dict[sch.identifier] = sch.to_dict(abridged=True)
        _update_user_json(sch_dict, sch_json, indent)
        # write the programs
        prog_folder = os.path.join(folder, 'programtypes')
        prog_json = os.path.join(prog_folder, '{}.json'.format(base_name))
        prog_dict = {}
        for prog in program_types.values():
            if prog.identifier not in _default_programs:
                added_objs.append(prog.identifier)
                prog_dict[prog.identifier] = prog.to_dict(abridged=True)
        _update_user_json(prog_dict, prog_json, indent)

        # write a message into the log file
        msg = 'The following objects were successfully added:\n{}'.format(
            '\n'.join(added_objs))
        log_file.write(msg)
    except Exception as e:
        _logger.exception('Adding to user standards library failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
