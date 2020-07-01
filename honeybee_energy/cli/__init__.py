"""honeybee-energy commands which will be added to honeybee command line interface."""

try:
    import click
except ImportError:
    raise ImportError(
        'click is not installed. Try `pip install . [cli]` command.'
    )

from honeybee.cli import main
from .lib import lib
from .translate import translate
from .settings import settings
from .simulate import simulate
from .result import result

# command group for all energy extension commands.
@click.group(help='honeybee energy commands.')
def energy():
    pass


# add sub-commands to energy
energy.add_command(lib)
energy.add_command(translate)
energy.add_command(settings)
energy.add_command(simulate)
energy.add_command(result)

# add energy sub-commands to honeybee CLI
main.add_command(energy)
