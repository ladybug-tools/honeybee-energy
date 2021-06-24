"""honeybee-energy validation commands."""
import click
import sys
import logging
import json

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.programtype import ProgramType
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.constructionset import ConstructionSet

from honeybee.model import Model

_logger = logging.getLogger(__name__)

try:
    import honeybee_schema.model as schema_model
    import honeybee_schema.energy.simulation as schema_simulation_parameter
    import honeybee_schema.energy.programtype as schema_programtype
    import honeybee_schema.energy.schedule as schema_schedule
    import honeybee_schema.energy.constructionset as schema_constructionset
except ImportError:
    _logger.exception(
        'honeybee_schema is not installed and validation commands are unavailable.\n'
        'You must use Python 3.7 or above to run validation commands.'
    )


@click.group(help='Commands for validating Honeybee energy JSON files.')
def validate():
    pass


@validate.command('model-properties')
@click.argument('model-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option(
    '--output-file', '-f', help='Optional file to output the full report '
    'of any errors detected. By default it will be printed out to stdout',
    type=click.File('w'), default='-')
def validate_model_properties(model_json, output_file):
    """Validate the energy properties of a Model JSON against the Honeybee schema.

    This includes basic re-serialization, which accounts for missing objects,
    and unique identifier checks.

    \b
    Args:
        model_json: Full path to a Model JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        click.echo('Validating Model JSON ...')
        schema_model.Model.parse_file(model_json)
        click.echo('Pydantic validation passed.')
        # re-serialize the Model to make sure no errors are found in re-serialization
        parsed_model = Model.from_hbjson(model_json)
        click.echo('Python re-serialization passed.')
        # perform several other checks for key honeybee model schema rules
        report = parsed_model.properties.energy.check_all(raise_exception=False)
        # check the report and write the summary of errors
        if report == '':
            output_file.write(
                'Congratulations! The energy properties of your Model JSON are valid!')
        else:
            error_msg = '\nYour Model is invalid for the following reasons:'
            output_file.write('\n'.join([error_msg, report]))
    except Exception as e:
        _logger.exception('Model validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


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
        # re-serialize to make sure no errors are found in re-serialization
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        SimulationParameter.from_dict(data)
        click.echo('Python re-serialization passed.')
        # if we made it to this point, report that the object is valid
        click.echo('Congratulations! Your SimulationParameter JSON is valid!')
    except Exception as e:
        _logger.exception('SimulationParameter validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@validate.command('program-type')
@click.argument('program-type-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def validate_program_type(program_type_json):
    """Validate all properties of a ProgramType or ProgramTypeAbridged JSON.

    \b
    Args:
        program_type_json: Full path to a ProgramType or ProgramTypeAbridged JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        with open(program_type_json) as json_file:
            data = json.load(json_file)
        if data['type'] == 'ProgramType':
            click.echo('Validating ProgramType JSON ...')
            schema_programtype.ProgramType.parse_file(program_type_json)
            click.echo('Pydantic validation passed.')
            ProgramType.from_dict(data)
            click.echo('Python re-serialization passed.')
        else:  # assume it's a ProgramTypeAbridged schema
            click.echo('Validating ProgramTypeAbridged JSON ...')
            schema_programtype.ProgramTypeAbridged.parse_file(program_type_json)
            click.echo('Pydantic validation passed.')
        # if we made it to this point, report that the object is valid
        click.echo('Congratulations! Your Program JSON is valid!')
    except Exception as e:
        _logger.exception('ProgramType validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@validate.command('schedule')
@click.argument('schedule-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def validate_schedule(schedule_json):
    """Validate all properties of a schedule or abridged schedule JSON.

    \b
    Args:
        schedule_json: Full path to a either ScheduleRuleset, ScheduleRulesetAbridged
            ScheduleFixedInterval, or ScheduleFixedIntervalAbridged JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        with open(schedule_json) as json_file:
            data = json.load(json_file)
        if data['type'] == 'ScheduleRuleset':
            click.echo('Validating ScheduleRuleset JSON ...')
            schema_schedule.ScheduleRuleset.parse_file(schedule_json)
            click.echo('Pydantic validation passed.')
            ScheduleRuleset.from_dict(data)
            click.echo('Python re-serialization passed.')
        elif data['type'] == 'ScheduleFixedInterval':
            click.echo('Validating ScheduleFixedInterval JSON ...')
            schema_schedule.ScheduleFixedInterval.parse_file(schedule_json)
            click.echo('Pydantic validation passed.')
            ScheduleFixedInterval.from_dict(data)
            click.echo('Python re-serialization passed.')
        elif data['type'] == 'ScheduleRulesetAbridged':
            click.echo('Validating ScheduleRulesetAbridged JSON ...')
            schema_schedule.ScheduleRulesetAbridged.parse_file(schedule_json)
            click.echo('Pydantic validation passed.')
        else:  # assume it's a ScheduleFixedIntervalAbridged schema
            click.echo('Validating ScheduleFixedIntervalAbridged JSON ...')
            schema_schedule.ScheduleFixedIntervalAbridged.parse_file(schedule_json)
            click.echo('Pydantic validation passed.')
        # if we made it to this point, report that the object is valid
        click.echo('Congratulations! Your Schedule JSON is valid!')
    except Exception as e:
        _logger.exception('Schedule validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@validate.command('schedule-type-limit')
@click.argument('schedule-type-limit-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def validate_schedule_type_limit(schedule_type_limit_json):
    """Validate all properties of a ScheduleTypeLimit JSON against the Honeybee schema.

    \b
    Args:
        schedule_type_limit_json: Full path to a ScheduleTypeLimit JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        click.echo('Validating ScheduleTypeLimit JSON ...')
        schema_schedule.ScheduleTypeLimit.parse_file(schedule_type_limit_json)
        click.echo('Pydantic validation passed.')
        # re-serialize to make sure no errors are found in re-serialization
        with open(schedule_type_limit_json) as json_file:
            data = json.load(json_file)
        ScheduleTypeLimit.from_dict(data)
        click.echo('Python re-serialization passed.')
        # if we made it to this point, report that the object is valid
        click.echo('Congratulations! Your ScheduleTypeLimit JSON is valid!')
    except Exception as e:
        _logger.exception('ScheduleTypeLimit validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@validate.command('construction-set')
@click.argument('construction-set-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
def validate_construction_set(construction_set_json):
    """Validate all properties of a ConstructionSet or ConstructionSetAbridged JSON.

    \b
    Args:
        construction_set_json: Full path to a ConstructionSet or ConstructionSetAbridged
            JSON file.
    """
    try:
        # first check the JSON against the OpenAPI specification
        with open(construction_set_json) as json_file:
            data = json.load(json_file)
        if data['type'] == 'ConstructionSet':
            click.echo('Validating ConstructionSet JSON ...')
            schema_constructionset.ConstructionSet.parse_file(construction_set_json)
            click.echo('Pydantic validation passed.')
            ConstructionSet.from_dict(data)
            click.echo('Python re-serialization passed.')
        else:  # assume it's a ConstructionSetAbridged schema
            click.echo('Validating ConstructionSetAbridged JSON ...')
            schema_constructionset.ConstructionSetAbridged.parse_file(
                construction_set_json)
            click.echo('Pydantic validation passed.')
        # if we made it to this point, report that the object is valid
        click.echo('Congratulations! Your Program JSON is valid!')
    except Exception as e:
        _logger.exception('ConstructionSet validation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)
