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
from honeybee_energy.baseline.result import appendix_g_summary, leed_v4_summary

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
    type=str, default='NonResidential', show_default=True)
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
    type=str, default='NonResidential', show_default=True)
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
    type=str, default='NonResidential', show_default=True)
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
    type=str, default='NonResidential', show_default=True)
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


@baseline.command('appendix-g-summary')
@click.argument('proposed-sql', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('baseline-sqls', nargs=-1, required=True, type=click.Path(
    exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option(
    '--building-type', '-b', help='Text for the building type that the Model represents.'
    ' This is used to determine the baseline window-to-wall ratio and HVAC system. If '
    'the type is not recognized or is "Unknown", it will be assumed that the building is'
    ' a generic NonResidential. The following have meaning per the standard: '
    'Residential, NonResidential, MidriseApartment, HighriseApartment, LargeOffice, '
    'MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, SecondarySchool, '
    'SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, SuperMarket, '
    'FullServiceRestaurant, QuickServiceRestaurant, Laboratory, Courthouse',
    type=str, default='NonResidential', show_default=True)
@click.option(
    '--electricity-cost', '-e', help='A number for the cost per each kWh of electricity.'
    ' This can be in any currency as long as it is coordinated with the costs of '
    'other inputs to this method. (Default: 0.12 for the average 2020 cost of '
    'electricity in the US in $/kWh).', type=float, default=0.12, show_default=True)
@click.option(
    '--natural-gas-cost', '-g', help='A number for the cost per each kWh of natural gas.'
    ' This can be in any currency as long as it is coordinated with the costs of '
    'other inputs to this method. (Default: 0.06 for the average 2020 cost of natural '
    'gas in the US in $/kWh).', type=float, default=0.06, show_default=True)
@click.option(
    '--district-cooling-cost', '-dc', help='A number for the cost per each kWh of '
    'district cooling energy. This can be in any currency as long as it is coordinated '
    'with the costs of other inputs to this method. (Default: 0.04 assuming average '
    '2020 US cost of electricity in $/kWh with a COP 3.5 chiller).',
    type=float, default=0.04, show_default=True)
@click.option(
    '--district-heating-cost', '-dh', help='A number for the cost per each kWh of '
    'district heating energy. This can be in any currency as long as it is coordinated '
    'with the costs of other inputs to this method. (Default: 0.08 assuming average '
    '2020 US cost of natural gas in $/kWh with an efficiency of 0.75 with all burner '
    'and distribution losses).', type=float, default=0.08, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional json file to output the JSON '
    'string of the summary report. By default this will be printed out '
    'to stdout', type=click.File('w'), default='-', show_default=True)
def compute_appendix_g_summary(
        proposed_sql, baseline_sqls, climate_zone, building_type,
        electricity_cost, natural_gas_cost,
        district_cooling_cost, district_heating_cost, output_file):
    """Get a JSON with a summary of ASHRAE-90.1 Appendix G performance.

    This includes Appendix G performance for versions 2016, 2019, and 2022.

    \b
    Args:
        proposed_sql: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        baseline_sqls: The path of a directory with several SQL result files generated
            from an energy simulation of a baseline building (eg. for several
            simulations of different orientations). The baseline performance will
            be computed as the average across all SQL files in the directory.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        # get a dictionary with the Appendix G results
        result_dict = appendix_g_summary(
            proposed_sql, baseline_sqls, climate_zone, building_type,
            electricity_cost, natural_gas_cost,
            district_cooling_cost, district_heating_cost)
        # write everything into the output file
        output_file.write(json.dumps(result_dict, indent=4))
    except Exception as e:
        _logger.exception('Failed to compute Appendix G summary.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('leed-v4-summary')
@click.argument('proposed-sql', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('baseline-sqls', nargs=-1, required=True, type=click.Path(
    exists=True, file_okay=True, dir_okay=True, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option(
    '--building-type', '-b', help='Text for the building type that the Model represents.'
    ' This is used to determine the baseline window-to-wall ratio and HVAC system. If '
    'the type is not recognized or is "Unknown", it will be assumed that the building is'
    ' a generic NonResidential. The following have meaning per the standard: '
    'Residential, NonResidential, MidriseApartment, HighriseApartment, LargeOffice, '
    'MediumOffice, SmallOffice, Retail, StripMall, PrimarySchool, SecondarySchool, '
    'SmallHotel, LargeHotel, Hospital, Outpatient, Warehouse, SuperMarket, '
    'FullServiceRestaurant, QuickServiceRestaurant, Laboratory, Courthouse',
    type=str, default='NonResidential', show_default=True)
@click.option(
    '--electricity-cost', '-e', help='A number for the cost per each kWh of electricity.'
    ' This can be in any currency as long as it is coordinated with the costs of '
    'other inputs to this method. (Default: 0.12 for the average 2020 cost of '
    'electricity in the US in $/kWh).', type=float, default=0.12, show_default=True)
@click.option(
    '--natural-gas-cost', '-g', help='A number for the cost per each kWh of natural gas.'
    ' This can be in any currency as long as it is coordinated with the costs of '
    'other inputs to this method. (Default: 0.06 for the average 2020 cost of natural '
    'gas in the US in $/kWh).', type=float, default=0.06, show_default=True)
@click.option(
    '--district-cooling-cost', '-dc', help='A number for the cost per each kWh of '
    'district cooling energy. This can be in any currency as long as it is coordinated '
    'with the costs of other inputs to this method. (Default: 0.04 assuming average '
    '2020 US cost of electricity in $/kWh with a COP 3 chiller).',
    type=float, default=0.04, show_default=True)
@click.option(
    '--district-heating-cost', '-dh', help='A number for the cost per each kWh of '
    'district heating energy. This can be in any currency as long as it is coordinated '
    'with the costs of other inputs to this method. (Default: 0.08 assuming average '
    '2020 US cost of natural gas in $/kWh with an efficiency of 0.75 with all burner '
    'and distribution losses).', type=float, default=0.08, show_default=True)
@click.option(
    '--electricity-emissions', '-ee', help='A number for the electric grid '
    'carbon emissions in kg CO2 per MWh. For locations in the USA, this can be '
    'obtained from he honeybee_energy.result.emissions future_electricity_emissions '
    'method. For locations outside of the USA where specific data is unavailable, '
    'the following rules of thumb may be used as a guide. (Default: 400).\n'
    '800 kg/MWh - for an inefficient coal or oil-dominated grid\n'
    '400 kg/MWh - for the US (energy mixed) grid around 2020\n'
    '100-200 kg/MWh - for grids with majority renewable/nuclear composition\n'
    '0-100 kg/MWh - for grids with renewables and storage',
    type=float, default=400, show_default=True)
@click.option(
    '--output-file', '-f', help='Optional json file to output the JSON '
    'string of the summary report. By default this will be printed out '
    'to stdout', type=click.File('w'), default='-', show_default=True)
def compute_leed_v4_summary(
        proposed_sql, baseline_sqls, climate_zone, building_type,
        electricity_cost, natural_gas_cost, district_cooling_cost, district_heating_cost,
        electricity_emissions, output_file):
    """Get a JSON with a summary of LEED V4 (and 4.1) performance.

    This includes ASHRAE 90.1-2016 Appendix G performance for both cost and
    carbon (GHG) emissions as well as the estimated number of LEED "Optimize
    Energy Performance" points.

    \b
    Args:
        proposed_sql: The path of the SQL result file that has been generated from an
            energy simulation of a proposed building.
        baseline_sqls: The path of a directory with several SQL result files generated
            from an energy simulation of a baseline building (eg. for several
            simulations of different orientations). The baseline performance will
            be computed as the average across all SQL files in the directory.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        # get a dictionary with the Appendix G results
        result_dict = leed_v4_summary(
            proposed_sql, baseline_sqls, climate_zone, building_type,
            electricity_cost, natural_gas_cost,
            district_cooling_cost, district_heating_cost, electricity_emissions)
        # write everything into the output file
        output_file.write(json.dumps(result_dict, indent=4))
    except Exception as e:
        _logger.exception('Failed to compute Appendix G summary.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
