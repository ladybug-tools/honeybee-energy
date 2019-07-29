# coding=utf-8
from honeybee.properties import ModelProperties, RoomProperties, FaceProperties, \
    ShadeProperties, ApertureProperties, DoorProperties
import honeybee.writer as writer
import honeybee.boundarycondition as hbc
import honeybee.aperturetype as hat

from .properties.model import ModelEnergyProperties
from .properties.room import RoomEnergyProperties
from .properties.face import FaceEnergyProperties
from .properties.shade import ShadeEnergyProperties
from .properties.aperture import ApertureEnergyProperties
from .properties.door import DoorEnergyProperties
from .writer import face_to_idf
from .boundarycondition import Adiabatic
from .aperturetype import OperableWindow, GlassDoor

# set a hidden energy attribute on each core geometry Property class to None
# define methods to produce energy property instances on each Proprety instance
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
setattr(writer, 'idf', face_to_idf)

# extend boundary conditions
setattr(hbc, 'Adiabatic', Adiabatic)
hbc._BoundaryConditions._adiabatic = Adiabatic()
hbc._BoundaryConditions.adiabatic = property(lambda self: self._adiabatic)

# extend aperture types
setattr(hat, 'GlassDoor', GlassDoor)
hat._Types._glass_door = GlassDoor()
hat._Types.glass_door = property(lambda self: self._glass_door)


def operable_window(self, fraction_operable=0.5):
    return OperableWindow(fraction_operable)


setattr(hat, 'OperableWindow', OperableWindow)
hat._Types.operable_window = operable_window
