from honeybee.properties import Properties
import honeybee.writer as writer
import honeybee.boundarycondition as hbc

from .properties import EnergyProperties
from .writer import face_to_idf
from .boundarycondition import Adiabatic

# add energy properties to Properties class
Properties.energy =  \
    property(lambda self: EnergyProperties(self.face_type, self.boundary_condition))

# add energy writer to idf
setattr(writer, 'energy', face_to_idf)

# extend boundary conditions
setattr(hbc, 'Adiabatic', Adiabatic)
hbc._BoundaryConditions._adiabatic = Adiabatic()
hbc._BoundaryConditions.adiabatic = property(lambda self: self._adiabatic)
