"""honeybee energy commands for creating baseline buildings conforming to standards."""
import click
import sys
import logging
import json

from honeybee.model import Model

from honeybee_energy.baseline.create import model_to_baseline, \
    model_geometry_to_baseline, model_constructions_to_baseline, \
    model_lighting_to_baseline, model_hvac_to_baseline, model_shw_to_baseline, \
    model_remove_ecms

_logger = logging.getLogger(__name__)


@click.group(help='Commands for creating baseline buildings conforming to standards.')
def baseline():
    pass


@baseline.command('create')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option(
    '--building-type', '-b', help='Text for the building type that the Model represents.'
    ' This is used to determine the baseline window-to-wall ratio and HVAC system. If '
    'the type is not recognized or is "Unknown", it will be assumed that the building is'
    ' a generic NonResidential. The following have specified systems per the standard: '
    'Residential, NonResidential, MidriseApartment, HighriseApartment, LargeOffice, '
    'MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, SecondarySchool, '
    'SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, SuperMarket, '
    'FullServiceRestaurant, QuickServiceRestaurant, Laboratory',
    type=str, default='Unknown', show_default=True)
@click.option(
    '--floor-area', '-a', help='A number for the floor area of the building'
    ' that the model is a part of in m2. If None or 0, the model floor area '
    'will be used.', type=float, default=0, show_default=True)
@click.option(
    '--story-count', '-s', help='An integer for the number of stories of '
    'the building that the model is a part of. If None or 0, the model stories '
    'will be used.', type=int, default=0, show_default=True)
@click.option(
    '--lighting-by-space/--lighting-by-building', ' /-lb', help='Flag to note whether '
    'the building-type should be used to assign the baseline lighting power density, '
    'which will use the same value for all Rooms in the model, or a space-by-space '
    'method should be used. To use the space-by-space method, the model should '
    'either be built with the programs that ship with Ladybug Tools in '
    'honeybee-energy-standards or the baseline_watts_per_area should be correctly '
    'assigned for all Rooms.', default=True)
@click.option(
    '--output-file', '-f', help='Optional hbjson file to output the JSON '
    'string of the converted model. By default this will be printed out '
    'to stdout', type=click.File('w'), default='-', show_default=True)
def create_baseline(model_file, climate_zone, building_type, floor_area,
                    story_count, lighting_by_space, output_file):
    """Convert a Model to be conformant with ASHRAE 90.1 appendix G.

    This includes running all other functions contained within this group to adjust
    the geometry, constructions, lighting, HVAC, SHW, and remove any clearly-defined
    energy conservation measures like daylight controls. Note that all schedules
    are essentially unchanged, meaning that additional post-processing of setpoints
    may be necessary to account for energy conservation strategies like expanded
    comfort ranges, ceiling fans, and personal thermal comfort devices. It may
    also be necessary to adjust electric equipment loads in cases where such
    equipment qualifies as an energy conservation strategy or hot water loads in
    cases where low-flow fixtures are implemented.

    Note that not all versions of ASHRAE 90.1 use this exact definition of a
    baseline model but version 2016 and onward conform to it. It is essentially
    an adjusted version of the 90.1-2004 methods.

    \b
    Args:
        model_file: Full path to a Honeybee Model file.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        lighting_by_building = not lighting_by_space
        model = Model.from_file(model_file)
        model_to_baseline(
            model, climate_zone, building_type, floor_area, story_count,
            lighting_by_building)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline HVAC creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('geometry')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--building-type', '-b', help='Text for the building type that the '
    'Model represents. This is used to set the maximum window ratio for the '
    'model. If the type is not recognized or is "Unknown", a maximum of 0.4 '
    'shall be used. The following have specified ratios per the standard: '
    'LargeOffice, MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, '
    'SecondarySchool, SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, '
    'SuperMarket, FullServiceRestaurant, QuickServiceRestaurant',
    type=str, default='Unknown', show_default=True)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out to '
              'stdout', type=click.File('w'), default='-', show_default=True)
def baseline_geometry(model_file, building_type, output_file):
    """Convert a Model's geometry to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes stripping out all attached shades (leaving detached shade as context),
    reducing the vertical glazing ratio to 40% it it's above this value, and
    reducing the skylight ratio to 5% if it's above this value.

    \b
    Args:
        model_file: Path to a Honeybee Model file.
    """
    try:
        model = Model.from_file(model_file)
        model_geometry_to_baseline(model, building_type)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline geometry creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('constructions')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def baseline_constructions(model_file, climate_zone, output_file):
    """Convert a Model's constructions to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes assigning a ConstructionSet that is compliant with Table 5.5 to
    all rooms in the model.

    \b
    Args:
        model_file: Full path to a Honeybee Model file.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        model = Model.from_file(model_file)
        model_constructions_to_baseline(model, climate_zone)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline construction assignment failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('lighting')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def baseline_lighting(model_file, output_file):
    """Convert a Model's lighting to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes determining whether an ASHRAE 2004 equivalent exists for each
    program type in the model. If none is found, the baseline_watts_per_area on
    the room's program's lighting will be used, which will default to a typical
    office if none has been specified.

    \b
    Args:
        model_file: Full path to a Honeybee Model file.
    """
    try:
        model = Model.from_file(model_file)
        model_lighting_to_baseline(model)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline lighting assignment failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('hvac')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option(
    '--building-type', '-b', help='Text for the building type that the '
    'Model represents. This is used to determine the baseline system. If the type '
    'is not recognized or is "Unknown", it will be assumed that the building is '
    'a generic NonResidential. The following have specified systems per the standard: '
    'Residential, NonResidential, MidriseApartment, HighriseApartment, LargeOffice, '
    'MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, SecondarySchool, '
    'SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, SuperMarket, '
    'FullServiceRestaurant, QuickServiceRestaurant, Laboratory',
    type=str, default='Unknown', show_default=True)
@click.option(
    '--floor-area', '-a', help='A number for the floor area of the building'
    ' that the model is a part of in m2. If None or 0, the model floor area '
    'will be used.', type=float, default=0, show_default=True)
@click.option(
    '--story-count', '-s', help='An integer for the number of stories of '
    'the building that the model is a part of. If None or 0, the model stories '
    'will be used.', type=int, default=0, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional hbjson file to output the JSON '
    'string of the converted model. By default this will be printed out '
    'to stdout', type=click.File('w'), default='-', show_default=True)
def baseline_hvac(model_file, climate_zone, building_type, floor_area,
                  story_count, output_file):
    """Convert a Model's HVAC to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes the selection of the correct Appendix G template HVAC based on
    the inputs and the application of this HVAC to all conditioned spaces in
    the model.

    \b
    Args:
        model_file: Full path to a Honeybee Model file.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        model = Model.from_file(model_file)
        model_hvac_to_baseline(
            model, climate_zone, building_type, floor_area, story_count)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline HVAC creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('shw')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--building-type', '-b', help='Text for the building type that the '
    'Model represents. This is used to determine the baseline system. If the type '
    'is not recognized or is "Unknown", it will be assumed that the building is '
    'a generic NonResidential. The following have specified systems per the standard: '
    'Residential, NonResidential, MidriseApartment, HighriseApartment, LargeOffice, '
    'MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, SecondarySchool, '
    'SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, SuperMarket, '
    'FullServiceRestaurant, QuickServiceRestaurant, Laboratory',
    type=str, default='Unknown', show_default=True)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out to '
              'stdout', type=click.File('w'), default='-', show_default=True)
def baseline_shw(model_file, building_type, output_file):
    """Convert a Model's geometry to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes stripping out all attached shades (leaving detached shade as context),
    reducing the vertical glazing ratio to 40% it it's above this value, and
    reducing the skylight ratio to 5% if it's above this value.

    \b
    Args:
        model_file: Path to a Honeybee Model file.
    """
    try:
        model = Model.from_file(model_file)
        model_shw_to_baseline(model, building_type)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline SHW creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('remove-ecms')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def remove_ecms(model_file, output_file):
    """Remove energy conservation strategies (ECMs) not associated with baseline models.

    This includes removing the opening behavior of all operable windows, daylight
    controls, etc.

    \b
    Args:
        model_file: Full path to a Honeybee Model file.
    """
    try:
        model = Model.from_file(model_file)
        model_remove_ecms(model)
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model remove ECMs failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
