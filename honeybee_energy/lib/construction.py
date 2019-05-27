"""A collection of default energy constructions.

TODO: Make the decision on how we will be using OpenStudio standards to generate
constructions and materials.
"""
from honeybee_energy.construction import Construction

# TODO(): add materials library and replace the libraries with real materials
generic_wall = Construction('generic_wall', materials=[])
