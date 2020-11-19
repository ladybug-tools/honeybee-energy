"""honeybee-energy validation commands."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee_energy.simulation.parameter import SimulationParameter

import sys
import logging
import json

_logger = logging.getLogger(__name__)

try:
    import honeybee_schema.energy.simulation as schema_simulation_parameter
except ImportError:
    _logger.exception(
        'honeybee_schema is not installed. Try `pip install . [cli]` command.'
    )


@click.group(help='Commands for validating Honeybee energy JSON files.')
def validate():
    pass


@validate.command('sim-par')
@click.argument('sim-par-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def validate_sim_par(sim_par_json):
    """Validate all properties of a SimulationParameter JSON against the Honeybee schema.

    \b
    Args:
        sim_par_json: Full path to a SimulationParameter JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        click.echo('Validating SimulationParameter JSON ...')
        schema_simulation_parameter.SimulationParameter.parse_file(sim_par_json)
        click.echo('Pydantic validation passed.')
        # re-serialize the Model to make sure no errors are found in re-serialization
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        SimulationParameter.from_dict(data)
        click.echo('Python re-serialization passed.')
        # if we made it to this point, report that the model is valid
        click.echo('Congratulations! Your SimulationParameter JSON is valid!')
    except Exception as e:
        _logger.exception('SimulationParameter validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
