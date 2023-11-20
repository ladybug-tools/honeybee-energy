# coding=utf-8
# extend the honeybee.altnumber module first since other modules rely on it
import honeybee.altnumber as haltn
from .altnumber import Autosize
setattr(haltn, 'Autosize', Autosize)
setattr(haltn, 'autosize', Autosize())

# import all of the other modules
from honeybee.properties import ModelProperties, RoomProperties, FaceProperties, \
    ShadeProperties, ApertureProperties, DoorProperties, ShadeMeshProperties
import honeybee.writer.shademesh as shade_mesh_writer
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
from .properties.shademesh import ShadeMeshEnergyProperties
from .writer import model_to_idf, room_to_idf, face_to_idf, shade_to_idf, \
    aperture_to_idf, door_to_idf, shade_mesh_to_idf, \
    orphaned_face_to_idf, orphaned_aperture_to_idf, orphaned_door_to_idf
from .boundarycondition import Adiabatic, OtherSideTemperature

# set a hidden energy attribute on each core geometry Property class to None
# define methods to produce energy property instances on each Property instance
ModelProperties._energy = None
RoomProperties._energy = None
FaceProperties._energy = None
ShadeProperties._energy = None
ApertureProperties._energy = None
DoorProperties._energy = None
ShadeMeshProperties._energy = None


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


def shade_mesh_energy_properties(self):
    if self._energy is None:
        self._energy = ShadeMeshEnergyProperties(self.host)
    return self._energy


# add energy property methods to the Properties classes
ModelProperties.energy = property(model_energy_properties)
RoomProperties.energy = property(room_energy_properties)
FaceProperties.energy = property(face_energy_properties)
ShadeProperties.energy = property(shade_energy_properties)
ApertureProperties.energy = property(aperture_energy_properties)
DoorProperties.energy = property(door_energy_properties)
ShadeMeshProperties.energy = property(shade_mesh_energy_properties)

# add energy writer to idf
model_writer.idf = model_to_idf
room_writer.idf = room_to_idf
face_writer.idf = face_to_idf
shade_writer.idf = shade_to_idf
aperture_writer.idf = aperture_to_idf
door_writer.idf = door_to_idf
face_writer.idf_shade = orphaned_face_to_idf
aperture_writer.idf_shade = orphaned_aperture_to_idf
door_writer.idf_shade = orphaned_door_to_idf
shade_mesh_writer.idf = shade_mesh_to_idf

# extend boundary conditions
setattr(hbc, 'Adiabatic', Adiabatic)
hbc._BoundaryConditions._adiabatic = Adiabatic()
hbc._BoundaryConditions.adiabatic = property(lambda self: self._adiabatic)


def other_side_temperature(
        self, temperature=haltn.autocalculate, heat_transfer_coefficient=0):
    """Get a boundary condition for a custom temperature or heat transfer coefficient.

    Args:
        temperature: A temperature value in Celsius to note the temperature on the
            other side of the object. This input can also be an Autocalculate object
            to signify that the temperature is equal to the outdoor air
            temperature. (Default: autocalculate).
        heat_transfer_coefficient: A value in W/m2-K to indicate the combined
            convective/radiative film coefficient. If equal to 0, then the
            specified temperature above is equal to the exterior surface
            temperature. Otherwise, the temperature above is considered the
            outside air temperature and this coefficient is used to determine the
            difference between this outside air temperature and the exterior surface
            temperature. (Default: 0).
    """
    return OtherSideTemperature(temperature, heat_transfer_coefficient)


setattr(hbc, 'OtherSideTemperature', OtherSideTemperature)
hbc._BoundaryConditions.other_side_temperature = other_side_temperature
