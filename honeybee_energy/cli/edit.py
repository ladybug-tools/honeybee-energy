"""honeybee energy commands for editing model energy properties."""
import click
import sys
import logging
import json

from honeybee.model import Model

_logger = logging.getLogger(__name__)


@click.group(help='Commands for editing model energy properties.')
def edit():
    pass


@edit.command('modifiers-from-constructions')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--solar/--visible', ' /-v', help='Flag to note whether the assigned '
              'radiance modifiers should follow the solar properties of the '
              'constructions or the visible properties.', default=True)
@click.option('--exterior-offset', '-o', help='A number for the distance at which the '
              'exterior Room faces should be offset in meters. This is used to account '
              'for the fact that the exterior material layer of the construction '
              'usually needs a different modifier from the interior. If set to 0, '
              'no offset will occur and all assigned modifiers will be interior.',
              type=float, default=0, show_default=True)
@click.option('--output-file', '-f', help='Optional hbjson file to output the JSON '
              'string of the converted model. By default this will be printed out to '
              'stdout', type=click.File('w'), default='-', show_default=True)
def modifiers_from_constructions(model_json, solar, exterior_offset, output_file):
    """Assign honeybee Radiance modifiers based on energy construction properties.

    Note that the honeybee-radiance extension must be installed in order for this
    command to be run successfully.

    Also note that setting the --exterior-offset to a non-zero value will add the
    offset faces as orphaned faces and so the model will not be simulate-able in
    EnergyPlus after running this method (it is only intended for Radiance).

    \b
    Args:
        model_json: Full path to a Honeybee Model (HBJSON) file.
    """
    try:
        # re-serialize the Model to Python
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)
        # assign the radiance properties based on the interior energy constructions
        if solar:
            model.properties.energy.assign_radiance_solar_interior()
        else:
            model.properties.energy.assign_radiance_visible_interior()
        # offset the exterior faces and 
        if exterior_offset is not None and exterior_offset > 0:
            exterior_offset = exterior_offset if model.units == 'Meters' else \
                exterior_offset / model.conversion_factor_to_meters(model.units)
            ref_type = 'Solar' if solar else 'Visible'
            model.properties.energy.offset_and_assign_exterior_face_modifiers(
                reflectance_type=ref_type, offset=exterior_offset
            )
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
