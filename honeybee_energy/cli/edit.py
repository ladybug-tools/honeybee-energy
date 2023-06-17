"""honeybee energy commands for editing model energy properties."""
import click
import sys
import logging
import os
import json

from honeybee.model import Model
from honeybee.typing import clean_rad_string

from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.lib.scheduletypelimits import fractional
from honeybee_energy.properties.model import ModelEnergyProperties

_logger = logging.getLogger(__name__)


@click.group(help='Commands for editing model energy properties.')
def edit():
    pass


@edit.command('reset-resource-ids')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--by-name/--by-name-and-uuid', ' /-uuid', help='Flag to note whether '
    'newly-generated resource object IDs should be derived only from a '
    'cleaned display_name or whether this new ID should also have a unique '
    'set of 8 characters appended to it to guarantee uniqueness.', default=True
)
@click.option(
    '--reset-materials/--keep-materials', ' /-m', help='Flag to note whether '
    'the IDs of all materials in the model should be reset.',
    default=True, show_default=True
)
@click.option(
    '--reset-constructions/--keep-constructions', ' /-c', help='Flag to note whether '
    'the IDs of all constructions in the model should be reset.',
    default=True, show_default=True
)
@click.option(
    '--reset-construction-sets/--keep-construction-sets', ' /-cs', help='Flag to '
    'note whether the IDs of all construction sets in the model should be reset.',
    default=True, show_default=True
)
@click.option(
    '--reset-schedules/--keep-schedules', ' /-s', help='Flag to note whether '
    'the IDs of all schedules in the model should be reset.',
    default=True, show_default=True
)
@click.option(
    '--reset-programs/--keep-programs', ' /-p', help='Flag to note whether '
    'the IDs of all programs in the model should be reset. This will also include '
    'resetting the IDs of all load objects in the program.',
    default=True, show_default=True
)
@click.option(
    '--output-file', '-f', help='Optional hbjson file to output the JSON '
    'string of the converted model. By default this will be printed out to '
    'stdout', type=click.File('w'), default='-', show_default=True
)
def reset_resource_ids(
    model_file, by_name,
    reset_materials, reset_constructions, reset_construction_sets,
    reset_schedules, reset_programs, output_file
):
    """Reset the identifiers of resource objects in a Model file.

    This is useful when human-readable names are needed when the model is
    exported to other formats like IDF and OSM and the uniqueness of the
    identifiers is less of a concern.

    \b
    Args:
        model_file: Full path to a Honeybee Model (HBJSON) file.
    """
    try:
        # load the model file and separately load up the resource objects
        if sys.version_info < (3, 0):
            with open(model_file) as inf:
                data = json.load(inf)
        else:
            with open(model_file, encoding='utf-8') as inf:
                data = json.load(inf)
        # reset the identifiers of resources in the dictionary
        add_uuid = not by_name
        model_dict = ModelEnergyProperties.reset_resource_ids_in_dict(
            data, add_uuid, reset_materials, reset_constructions,
            reset_construction_sets, reset_schedules, reset_programs)
        # write the dictionary into a JSON
        output_file.write(json.dumps(model_dict))
    except Exception as e:
        _logger.exception('Resetting resource identifiers failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@edit.command('modifiers-from-constructions')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--solar/--visible', ' /-v', help='Flag to note whether the assigned '
              'radiance modifiers should follow the solar properties of the '
              'constructions or the visible properties.', default=True)
@click.option('--dynamic-groups/--static-groups', ' /-sg', help='Flag to note whether '
              'dynamic window constructions and shaded window constructions should '
              'be translated to dynamic aperture groups or just the static (bare) '
              'construction should be used.', default=True)
@click.option('--dynamic-shade/--static-shade', ' /-ss', help='Flag to note whether '
              'dynamic shade transmittance schedules should be translated to dynamic '
              'shade groups or just a static, fully-opaque construction should '
              'be used.', default=True)
@click.option('--exterior-offset', '-o', help='A number for the distance at which the '
              'exterior Room faces should be offset in meters. This is used to account '
              'for the fact that the exterior material layer of the construction '
              'usually needs a different modifier from the interior. If set to 0, '
              'no offset will occur and all assigned modifiers will be interior.',
              type=float, default=0, show_default=True)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out to '
              'stdout', type=click.File('w'), default='-', show_default=True)
def modifiers_from_constructions(
    model_file, solar, dynamic_groups, dynamic_shade, exterior_offset, output_file
):
    """Assign honeybee Radiance modifiers based on energy construction properties.

    Note that the honeybee-radiance extension must be installed in order for this
    command to be run successfully.

    Also note that setting the --exterior-offset to a non-zero value will add the
    offset faces as orphaned faces, which changes how the model simulates in EnergyPlus.

    \b
    Args:
        model_file: Full path to a Honeybee Model (HBJSON or HBpkl) file.
    """
    try:
        # import dependencies and set up reused variables
        try:
            from honeybee_radiance.lib.modifiers import air_boundary
            from honeybee_radiance.dynamic.state import RadianceShadeState
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'modifiers-from-constructions method. {}'.format(e))
        # re-serialize the Model to Python
        model = Model.from_file(model_file)
        # assign the radiance properties based on the interior energy constructions
        if solar:
            model.properties.energy.assign_radiance_solar_interior()
        else:
            model.properties.energy.assign_radiance_visible_interior()
        # offset the exterior faces and give them modifiers for the exterior
        if exterior_offset is not None and exterior_offset > 0:
            exterior_offset = exterior_offset if model.units == 'Meters' else \
                exterior_offset / model.conversion_factor_to_meters(model.units)
            ref_type = 'Solar' if solar else 'Visible'
            model.properties.energy.offset_and_assign_exterior_face_modifiers(
                reflectance_type=ref_type, offset=exterior_offset
            )
        # assign trans modifiers for any shades with constant transmittance schedules
        tr_sch_dict = {}
        for shade in model.shades:
            t_sch = shade.properties.energy.transmittance_schedule
            if t_sch is not None:
                if t_sch.is_constant:  # just use a trans modifier
                    if solar:
                        shade.properties.radiance.modifier = \
                            shade.properties.energy.radiance_modifier_solar()
                    else:
                        shade.properties.radiance.modifier = \
                            shade.properties.energy.radiance_modifier_visible()
                else:  # represent the shade as a dynamic group
                    try:
                        tr_sch_dict[t_sch.identifier].append(shade)
                    except KeyError:
                        tr_sch_dict[t_sch.identifier] = [shade]
        # assign dynamic shade groups if requested
        if dynamic_shade:
            for grp_name, group in tr_sch_dict.items():
                grp_name = clean_rad_string(grp_name)
                for shd in group:
                    shd.properties.radiance.dynamic_group_identifier = grp_name
                    on_state = RadianceShadeState(shd.properties.radiance.modifier)
                    off_state = RadianceShadeState(air_boundary)
                    shd.properties.radiance.states = [on_state, off_state]
        # assign dynamic aperture groups if requested
        if dynamic_groups:
            model.properties.energy.assign_dynamic_aperture_groups()
        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception(
            'Assignment of model radiance modifiers from energy construction '
            'failed.\n{}'.format(e)
        )
        sys.exit(1)
    else:
        sys.exit(0)


@edit.command('lighting-from-daylight')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.argument(
    'daylight-folder',
    type=click.Path(exists=True, file_okay=False, dir_okay=True, resolve_path=True)
)
@click.option(
    '--ill-setpoint', '-i', help='A number for the illuminance setpoint in lux beyond '
    'which electric lights are dimmed if there is sufficient daylight.',
    default=300, type=int, show_default=True
)
@click.option(
    '--min-power-in', '-p',
    help='A number between 0 and 1 for the the lowest power the lighting system can '
    'dim down to, expressed as a fraction of maximum input power.', default=0.3,
    type=float, show_default=True
)
@click.option(
    '--min-light-out', '-l',
    help='A number between 0 and 1 the lowest lighting output the lighting system can '
    'dim down to, expressed as a fraction of maximum light output. Note that setting '
    'this to 1 means lights are not dimmed at all until the illuminance setpoint is '
    'reached. This can be used to approximate manual light-switching behavior when '
    'used in conjunction with the off_at_min_ output below.', default=0.2,
    type=float, show_default=True
)
@click.option(
    '--on-at-min/--off-at-min', ' /-oam', help='Flag to note whether lights should '
    'switch off completely when they get to the minimum power input.',
    default=True, show_default=True
)
@click.option(
    '--output-file', '-f', help='Optional hbjson file to output the JSON '
    'string of the converted model. By default this will be printed out to '
    'stdout', type=click.File('w'), default='-', show_default=True
)
def lighting_from_daylight(
    model_file, daylight_folder, ill_setpoint, min_power_in, min_light_out,
    on_at_min, output_file
):
    """Assign HB-energy lighting schedules using Radiance annual-daylight results.

    Note that the honeybee-radiance extension must be installed in order for this
    command to be run successfully.

    Also note that the Honeybee model must have sensor grids with room_identifiers
    assigned to them for them to affect the HB-Energy lighting schedules. If such
    grids are found, the lighting schedules of the Rooms will be adjusted according
    to whether the illuminance values at the sensor locations are at a target
    illuminance setpoint.

    Each grid should have sensors at the locations in space where daylight dimming
    sensors are located. Grids with two or more sensors can be used to model setups
    where fractions of each room are controlled by different sensors. If the sensor
    grids are distributed over the entire floor of the rooms, the resulting schedules
    will be idealized, where light dimming has been optimized to supply the minimum
    illuminance setpoint everywhere in the room.

    \b
    Args:
        model_file: Full path to a Honeybee Model (HBJSON or HBpkl) file.
        daylight_folder: Path to an annual-daylight results folder. This folder is
            an output folder of the annual daylight recipe. The folder should
            include grids_info.json and sun-up-hours.txt. The command uses the
            list in grids_info.json to find the result files for each sensor grid.
    """
    try:
        # load up relevant honeybee-radiance dependencies
        try:
            from honeybee_radiance.postprocess.annualdaylight import \
                _process_input_folder
            from honeybee_radiance.postprocess.electriclight import \
                _file_to_dimming_fraction
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'lighting-from-daylight. {}'.format(e))

        # re-serialize the Model to Python and get a map from grids to room IDs
        model = Model.from_file(model_file)
        room_map = {}
        for grid in model.properties.radiance.sensor_grids:
            room_map[grid.room_identifier] = grid.full_identifier

        # get the dimming fractions for each sensor grid from the .ill files
        grids, sun_up_hours = _process_input_folder(daylight_folder, '*')
        sun_up_hours = [int(h) for h in sun_up_hours]
        off_at_min = not on_at_min
        dim_fracts = {}
        for grid_info in grids:
            ill_file = os.path.join(daylight_folder, '%s.ill' % grid_info['full_id'])
            fract_list = _file_to_dimming_fraction(
                ill_file, sun_up_hours, ill_setpoint, min_power_in,
                min_light_out, off_at_min
            )
            dim_fracts[grid_info['full_id']] = fract_list

        # loop through the rooms of the model and assign the lighting dimming
        for room in model.rooms:
            light = room.properties.energy.lighting
            if light is not None:
                base_schedule = light.schedule.values_at_timestep(1) \
                    if isinstance(light.schedule, ScheduleFixedInterval) \
                    else light.schedule.values(1)
                try:
                    dim_fract = dim_fracts[room_map[room.identifier]]
                    sch_vals = [b_val * d_val for b_val, d_val in
                                zip(base_schedule, dim_fract)]
                    sch_id = '{} Daylight Control'.format(room.identifier)
                    new_sch = ScheduleFixedInterval(sch_id, sch_vals, fractional)
                    new_light = light.duplicate()
                    new_light.schedule = new_sch
                    room.properties.energy.lighting = new_light
                except KeyError:
                    pass  # no grid is associated with the room

        # write the Model JSON string
        output_file.write(json.dumps(model.to_dict()))
    except Exception as e:
        _logger.exception(
            'Assignment of model lighting schedules from annual-daylight results '
            'failed.\n{}'.format(e)
        )
        sys.exit(1)
    else:
        sys.exit(0)
