"""honeybee-energy library."""
import importlib
import pkgutil
from honeybee.logutil import get_logger


# load all functions that extends honeybee core library
import honeybee_energy._extend_honeybee


logger = get_logger(__name__, filename='honeybee-energy.log')

#  find and import honeybee_energy extensions
#  this is a critical step to add additional functionalities to honeybee_energy library.
extensions = {}
for finder, name, ispkg in pkgutil.iter_modules():
    if not name.startswith('honeybee_energy_') or name.count('_') > 2:
        continue
    try:
        extensions[name] = importlib.import_module(name)
    except Exception:
        logger.exception('Failed to import {0}!'.format(name))
    else:
        logger.info('Successfully imported Honeybee-energy plugin: {}'.format(name))
