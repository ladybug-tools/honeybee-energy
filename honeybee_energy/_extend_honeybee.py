from honeybee.properties import Properties
import honeybee.writer as writer
from .properties import EnergyProperties
from .writer import face_to_idf

# add energy properties to Properties class
Properties.energy =  property(lambda self: EnergyProperties(self.face_type))

# add energy writer to idf
setattr(writer, 'energy', face_to_idf)
