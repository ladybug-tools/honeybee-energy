# coding=utf-8
# extend the honeybee.altnumber module first since other modules rely on it
import honeybee.altnumber as haltn
from .altnumber import Autosize
setattr(haltn, 'Autosize', Autosize)
setattr(haltn, 'autosize', Autosize())

# import all of the other modules
from honeybee.properties import ModelProperties, RoomProperties, FaceProperties, \
    ShadeProperties, ApertureProperties, DoorProperties
import honeybee.writer.door as door_writer
import honeybee.writer.aperture as aperture_writer
import honeybee.writer.shade as shade_writer
import honeybee.writer.face as face_writer
import honeybee.writer.room as room_writer
import honeybee.writer.model as model_writer
import honeybee.boundarycondition as hbc

from .properties.model import ModelEnergyProperties
from .properties.room import RoomEnergyProperties
from .properties.face import FaceEnergyProperties
from .properties.shade import ShadeEnergyProperties
from .properties.aperture import ApertureEnergyProperties
from .properties.door import DoorEnergyProperties
from .writer import model_to_idf, room_to_idf, face_to_idf, shade_to_idf, \
    aperture_to_idf, door_to_idf
from .boundarycondition import Adiabatic

# set a hidden energy attribute on each core geometry Property class to None
# define methods to produce energy property instances on each Property instance
ModelProperties._energy = None
RoomProperties._energy = None
FaceProperties._energy = None
ShadeProperties._energy = None
ApertureProperties._energy = None
DoorProperties._energy = None


def model_energy_properties(self):
    if self._energy is None:
        self._energy = ModelEnergyProperties(self.host)
    return self._energy


def room_energy_properties(self):
    if self._energy is None:
        self._energy = RoomEnergyProperties(self.host)
    return self._energy


def face_energy_properties(self):
    if self._energy is None:
        self._energy = FaceEnergyProperties(self.host)
    return self._energy


def shade_energy_properties(self):
    if self._energy is None:
        self._energy = ShadeEnergyProperties(self.host)
    return self._energy


def aperture_energy_properties(self):
    if self._energy is None:
        self._energy = ApertureEnergyProperties(self.host)
    return self._energy


def door_energy_properties(self):
    if self._energy is None:
        self._energy = DoorEnergyProperties(self.host)
    return self._energy


# add energy property methods to the Properties classes
ModelProperties.energy = property(model_energy_properties)
RoomProperties.energy = property(room_energy_properties)
FaceProperties.energy = property(face_energy_properties)
ShadeProperties.energy = property(shade_energy_properties)
ApertureProperties.energy = property(aperture_energy_properties)
DoorProperties.energy = property(door_energy_properties)

# add energy writer to idf
model_writer.idf = model_to_idf
room_writer.idf = room_to_idf
face_writer.idf = face_to_idf
shade_writer.idf = shade_to_idf
aperture_writer.idf = aperture_to_idf
door_writer.idf = door_to_idf


# extend boundary conditions
setattr(hbc, 'Adiabatic', Adiabatic)
hbc._BoundaryConditions._adiabatic = Adiabatic()
hbc._BoundaryConditions.adiabatic = property(lambda self: self._adiabatic)
