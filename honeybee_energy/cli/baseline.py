"""honeybee energy commands for creating baseline buildings conforming to standards."""
import click
import sys
import logging
import os
import json

from honeybee_energy.hvac.allair.vav import VAV
from honeybee_energy.hvac.allair.pvav import PVAV
from honeybee_energy.hvac.allair.psz import PSZ
from honeybee_energy.hvac.allair.ptac import PTAC
from honeybee_energy.material.glazing import EnergyWindowMaterialSimpleGlazSys
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.lib.constructionsets import construction_set_by_identifier
from honeybee_energy.lib.programtypes import program_type_by_identifier

from ladybug.futil import csv_to_matrix
from honeybee.model import Model
from honeybee.boundarycondition import Outdoors
from honeybee.facetype import RoofCeiling

_logger = logging.getLogger(__name__)


@click.group(help='Commands for creating baseline buildings conforming to standards.')
def baseline():
    pass


@baseline.command('geometry-2004')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out to '
              'stdout', type=click.File('w'), default='-', show_default=True)
def geometry_2004(model_json, output_file):
    """Convert a Model's geometry to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes stripping out all attached shades (leaving detached shade as context),
    reducing the vertical glazing ratio to 40% it it's above this value, and
    reducing the skylight ratio to 5% of it's above this value.

    \b
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # re-serialize the Model to Python and get the glazing ratios
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

        # remove all non-context shade
        model.remove_assigned_shades()  # remove all of the child shades
        or_shades = [shd for shd in model.orphaned_shades if shd.is_detached]
        model.remove_shades()
        for shd in or_shades:
            model.add_shade(shd)

        # compute the window and skylight ratios
        w_area = model.exterior_wall_area
        r_area = model.exterior_roof_area
        wr = model.exterior_wall_aperture_area / w_area if w_area != 0 else 0
        sr = model.exterior_skylight_aperture_area / r_area if r_area != 0 else 0

        # if the window or skylight ratio is greater than max permitted, set it to max
        if wr > 0.4:  # set all walls to have 40% ratio
            model.wall_apertures_by_ratio(0.4)
        if sr > 0.05:  # reduce all skylights by the amount needed for 5%
            red_fract = 0.05 / sr  # scale factor for all of the skylights
            for room in model.rooms:
                for face in room.faces:
                    if isinstance(face.boundary_condition, Outdoors) and \
                            isinstance(face.type, RoofCeiling) and \
                            len(face._apertures) > 0:
                        new_ratio = face.aperture_ratio * red_fract
                        face.apertures_by_ratio(new_ratio)

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline geometry creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('constructions-2004')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def constructions_2004(model_json, climate_zone, output_file):
    """Convert a Model's constructions to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes assigning a ConstructionSet that is compliant with Table 5.5 to
    all rooms in the model.

    \b
    Args:
        model_json: Full path to a Model JSON file.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        # re-serialize the Model to Python and get the glazing ratios
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)
        w_area = model.exterior_wall_area
        r_area = model.exterior_roof_area
        wr = model.exterior_wall_aperture_area / w_area if w_area != 0 else 0
        sr = model.exterior_skylight_aperture_area / r_area if r_area != 0 else 0

        # get the base ConstructionSet from the standards library
        clean_cz = str(climate_zone)[0]
        constr_set_id = '2004::ClimateZone{}::SteelFramed'.format(clean_cz)
        base_set = construction_set_by_identifier(constr_set_id)

        # parse the CSV file with exceptions to the base construction set
        ex_file = os.path.join(os.path.dirname(__file__), 'data', 'ashrae_2004.csv')
        ex_data = csv_to_matrix(ex_file)
        ex_cz = clean_cz if climate_zone != '3C' else climate_zone
        ex_ratio = '100'
        for ratio in (40, 30, 20, 10):
            if wr < ratio / 100 + 0.001:
                ex_ratio = str(ratio)
        for row in ex_data:
            if row[0] == ex_cz and row[1] == ex_ratio:
                vert_except = [float(val) for val in row[2:]]
                break

        # change the constructions for fixed and operable windows
        si_ip_u = 5.678263337
        fixed_id = 'U {} SHGC {} Fixed Glz'.format(vert_except[0], vert_except[2])
        fixed_mat = EnergyWindowMaterialSimpleGlazSys(
            fixed_id, vert_except[0] * si_ip_u, vert_except[2])
        fixed_constr = WindowConstruction(fixed_id.replace('Glz', 'Window'), [fixed_mat])
        oper_id = 'U {} SHGC {} Operable Glz'.format(vert_except[1], vert_except[2])
        oper_mat = EnergyWindowMaterialSimpleGlazSys(
            oper_id, vert_except[1] * si_ip_u, vert_except[2])
        oper_constr = WindowConstruction(oper_id.replace('Glz', 'Window'), [oper_mat])
        base_set.aperture_set.window_construction = fixed_constr
        base_set.aperture_set.operable_construction = oper_constr

        # change the construction for skylights if the ratio is greater than 2%
        if sr > 0.021:
            for row in ex_data:
                if row[0] == ex_cz and row[1] == 'sky_5':
                    sky_except = [float(row[2]), float(row[4])]
                    break
            sky_id = 'U {} SHGC {} Skylight Glz'.format(sky_except[0], sky_except[1])
            sky_mat = EnergyWindowMaterialSimpleGlazSys(
                sky_id, sky_except[0] * si_ip_u, sky_except[1])
            sky_constr = WindowConstruction(sky_id.replace('Glz', 'Window'), [sky_mat])
            base_set.aperture_set.skylight_construction = sky_constr

        # remove child constructions ans assign the construction set to all rooms
        model.properties.energy.remove_child_constructions()
        for room in model.rooms:
            room.properties.energy.construction_set = base_set

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline construction creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('lighting-2004')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def lighting_2004(model_json, output_file):
    """Convert a Model's lighting to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes determining whether an ASHRAE 2004 equivalent exists for each
    program type in the model. If none is found, the baseline_watts_per_area on
    the room's program's lighting will be used, which will default to a typical
    office if none has been specified.

    \b
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # re-serialize the Model to Python and get the glazing ratios
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

        # loop through the rooms and try to find equivalent programs in 2004
        for room in model.rooms:
            if room.properties.energy.lighting is None:
                continue
            prog_name = room.properties.energy.program_type.identifier.split('::')
            prog_2004 = None
            if len(prog_name) == 3:
                new_prog_name = '2004::{}::{}'.format(prog_name[1], prog_name[2])
                try:
                    prog_2004 = program_type_by_identifier(new_prog_name)
                except ValueError:  # no equivalent program in ASHRAE 2004
                    pass
            if prog_2004 is not None:  # if program was found, use it to assign the LPD
                if prog_2004.lighting is not None:
                    dup_light = room.properties.energy.lighting.duplicate()
                    dup_light.watts_per_area = prog_2004.lighting.watts_per_area
            elif room.properties.energy.program_type.lighting is not None:
                dup_light = room.properties.energy.program_type.lighting.duplicate()
                dup_light.watts_per_area = dup_light.baseline_watts_per_area
            else:
                dup_light = room.properties.energy.lighting.duplicate()
                dup_light.watts_per_area = dup_light.baseline_watts_per_area
            dup_light.identifier = '{}_Lighting'.format(room.identifier)
            room.properties.energy.lighting = dup_light

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline geometry creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('hvac-2004')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument('climate-zone', type=str)
@click.option('--nonresidential/--residential', ' /-r', help='Flag to note whether '
              'the model represents a residential or nonresidential building.',
              default=True, show_default=True)
@click.option('--fuel/--electric', ' /-e', help='Flag to note whether the available '
              'energy source is fossil fuel based or all-electric.',
              default=True, show_default=True)
@click.option('--floor-area', '-a', help='A number for the floor area of the building'
              ' that the model is a part of in m2. If None, the model floor area '
              'will be used.', type=float, default=0, show_default=True)
@click.option('--story-count', '-s', help='An integer for the number of stories of '
              'the building that the model is a part of. If None, the model stories '
              'will be used.', type=int, default=0, show_default=True)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def hvac_2004(model_json, climate_zone, nonresidential, fuel, floor_area,
              story_count, output_file):
    """Convert a Model's HVAC to be conformant with ASHRAE 90.1-2004 appendix G.

    This includes the selection of the correct Appendix G template HVAC based on
    the inputs and the application of this HVAC to all conditioned spaces in
    the model.

    \b
    Args:
        model_json: Full path to a Model JSON file.
        climate_zone: Text indicating the ASHRAE climate zone. This can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
    """
    try:
        # re-serialize the Model to Python and get the glazing ratios
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

        # determine the HVAC template from the input criteria
        std = 'ASHRAE_2004'
        if len(climate_zone) == 1:
            climate_zone = '{}A'.format(climate_zone)
        if nonresidential:
            # determine the floor area if it is not input
            if floor_area == 0 or floor_area is None:
                floor_area = model.floor_area
                floor_area = floor_area if model.units == 'Meters' else \
                    floor_area * model.conversion_factor_to_meters(model.units)
            # determine the number of stories if it is not input
            if story_count == 0 or story_count is None:
                story_count = len(model.stories)
            # determine the HVAC from the floor area and stories
            hvac_id = 'Baseline 2004 {} HVAC'
            if story_count > 5 or floor_area > 13935.5:  # more than 150,000 ft2
                hvac_id = hvac_id.format('VAV')
                hvac_sys = VAV(hvac_id, std, 'VAV_Chiller_Boiler') \
                    if fuel else VAV(hvac_id, std, 'VAV_Chiller_PFP')
            elif story_count > 3 or floor_area > 6967.7:  # more than 75,000 ft2
                hvac_id = hvac_id.format('PVAV')
                hvac_sys = PVAV(hvac_id, std, 'PVAV_Boiler') \
                    if fuel else PVAV(hvac_id, std, 'PVAV_PFP')
            else:
                hvac_id = hvac_id.format('PSZ')
                hvac_sys = PSZ(hvac_id, std, 'PSZAC_Boiler') \
                    if fuel else PSZ(hvac_id, std, 'PSZHP')
            if climate_zone not in ('1A', '1B', '2A', '3A', '4A'):
                hvac_sys.economizer_type = 'DifferentialDryBulb'
        else:
            hvac_id = 'Baseline 2004 PT Residential HVAC'
            hvac_sys = PTAC(hvac_id, std, 'PTAC_BoilerBaseboard') \
                if fuel else PTAC(hvac_id, std, 'PTHP')

        # apply the HVAC template to all conditioned rooms in the model
        for room in model.rooms:
            if room.properties.energy.is_conditioned:
                room.properties.energy.hvac = hvac_sys

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline geometry creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@baseline.command('remove-ecms')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out '
              'to stdout', type=click.File('w'), default='-', show_default=True)
def remove_ecms(model_json, output_file):
    """Remove energy conservation strategies (ECMs) not associated with baseline models.

    This includes removing the opening behavior of all operable windows, daylight
    controls, etc.

    \b
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # re-serialize the Model to Python and get the glazing ratios
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)

        # loop through the rooms and remove operable windows
        for room in model.rooms:
            room.properties.energy.window_vent_control = None
            room.properties.energy.remove_ventilation_opening()
            for face in room.faces:
                for ap in face.apertures:
                    ap.is_operable = False

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception('Model baseline geometry creation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
