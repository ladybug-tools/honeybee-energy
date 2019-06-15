"""A collection of default energy constructions.

TODO: Make the decision on how we will be using OpenStudio standards to generate
constructions and materials.
"""
from honeybee_energy.construction import OpaqueConstruction
from honeybee_energy.material.opaque import EnergyMaterial

# TODO(): add materials library and replace the libraries with real materials
concrete = EnergyMaterial('Concrete', 0.15, 2.31, 2322, 832)
insulation = EnergyMaterial('Insulation', 0.05, 0.049, 265, 836)
wall_gap = EnergyMaterial('Wall Air Gap', 0.1, 0.67, 1.2925, 1006.1)
gypsum = EnergyMaterial('Gypsum', 0.0127, 0.16, 784.9, 830)

generic_wall = OpaqueConstruction(
        'Generic Wall', materials=[concrete, insulation, wall_gap, gypsum])
