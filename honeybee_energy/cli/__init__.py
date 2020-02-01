"""honeybee-energy commands which will be added to honeybee command line interface."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee.cli import main
from .simulate import simulate
from .translate import translate

# command group for all energy extension commands.
@click.group(help='honeybee energy commands.')
def energy():
    pass

# add sub-commands to energy
energy.add_command(simulate)
energy.add_command(translate)

# add energy sub-commands to honeybee CLI
main.add_command(energy)
