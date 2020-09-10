"""honeybee energy commands for creating baseline buildings conforming to standards."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee.model import Model
from honeybee.boundarycondition import Outdoors
from honeybee.facetype import RoofCeiling

import sys
import logging
import json

_logger = logging.getLogger(__name__)


@click.group(help='Commands for creating baseline buildings conforming to standards.')
def baseline():
    pass


@baseline.command('geometry-2004')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', help='Optional hbjson file to output the JSON string '
              'of the converted model. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def geometry_2004(model_json, output_file):
    """Convert a Model's geometry to be conformant with ASHRAE 90.1-2004 appendix G.
    \n
    This includes stripping out all child shades (leaving orphaned shade), reducing
    the vertical glazing ratio to 40% it it's above this value, and reducing the
    skylight ratio to 5% of it's above this value.
    \n
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # re-serialize the Model to Python
        with open(model_json) as json_file:
            data = json.load(json_file)
        model = Model.from_dict(data)
        model.remove_assigned_shades()  # remove all of the child shades
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
