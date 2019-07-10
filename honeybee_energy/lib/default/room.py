"""Collection of construction sets."""
from honeybee_energy.constructionset import ConstructionSet
from honeybee_energy.programtype import ProgramType


generic_costruction_set = ConstructionSet('Default Generic Construction Set')
generic_costruction_set.lock()

plenum_program_type = ProgramType('Plenum')
