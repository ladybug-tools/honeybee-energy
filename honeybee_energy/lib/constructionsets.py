"""Collection of construction sets."""
from honeybee_energy.constructionset import ConstructionSet

from ._loadconstructionsets import _json_construction_sets


# establish variables for the default construction sets used across the library
# and auto-generate construction sets if they were not loaded from default.idf
try:
    generic_construction_set = _json_construction_sets['Default Generic Construction Set']
except KeyError:
    generic_construction_set = ConstructionSet('Default Generic Construction Set')
    generic_construction_set.lock()
    _json_construction_sets['Default Generic Construction Set'] = generic_construction_set


# make lists of program types to look up items in the library
CONSTRUCTION_SETS = tuple(_json_construction_sets.keys())


def construction_set_by_name(construction_set_name):
    """Get a construction_set from the library given its name.

    Args:
        construction_set_name: A text string for the name of the ConstructionSet.
    """
    try:
        return _json_construction_sets[construction_set_name]
    except KeyError:
        raise ValueError('"{}" was not found in the construction set library.'.format(
            construction_set_name))
