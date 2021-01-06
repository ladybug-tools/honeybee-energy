# coding=utf-8
"""Definitions for global parameters used in the ventilation simulation."""
from __future__ import division
import math

from ladybug_geometry.bounding import bounding_box_extents

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, float_in_range_excl_incl


@lockable
class VentilationSimulationControl(object):
    """Global parameters used to specify the simulation of air flow.

    Args:
        vent_control_type: Text indicating type of ventilation control.
            Choose from the following:

            * SingleZone
            * MultiZoneWithDistribution
            * MultiZoneWithoutDistribution

            The MultiZone options will model air flow with the AirflowNetwork model,
            which is generally more accurate then the SingleZone option, but will take
            considerably longer to simulate, and requires defining more ventilation
            parameters to explicitly account for weather and building-induced pressure
            differences, and the leakage geometry corresponding to specific windows,
            doors, and surface cracks (Default: 'SingleZone').
        reference_temperature: Reference temperature measurement in Celsius under which
            the surface crack data were obtained. This is only used for AFN simulations,
            when vent_control_type is NOT SingleZone. (Default: 20).
        reference_pressure: Reference barometric pressure measurement in Pascals
            under which the surface crack data were obtained. This is only used for AFN
            simulations, when vent_control_type is NOT SingleZone.(Default: 101325).
        reference_humidity_ratio: Reference humidity ratio measurement in
            kgWater/kgDryAir under which the surface crack data were obtained.
            This is only used for AFN simulations, when vent_control_type is
            NOT SingleZone. (Default: 0).
        building_type: Text indicating relationship between building footprint and
            height. Choose from the following:

            * LowRise
            * HighRise

            LowRise corresponds to a building where the height is less then three
            times the width AND length of the footprint. HighRise corresponds to a
            building where height is more than three times the width OR length of
            the footprint. This parameter is used to estimate building-wide wind
            pressure coefficients for the AFN by approximating the building geometry
            as an extruded rectangle. This property can be auto-calculated from
            Honeybee Room geometry with the geometry_properties_from_rooms
            method. (Default: 'LowRise').
        long_axis_angle: A number between 0 and 180 for the clockwise angle difference
            in degrees that the long axis of the building is from true North. This
            parameter is used to estimate building-wide wind pressure coefficients
            for the AFN by approximating the building geometry as an extruded
            rectangle. 0 indicates a North-South long axis while 90 indicates an
            East-West long axis. (Default: 0).
        aspect_ratio: A number between 0 and 1 for the aspect ratio of the building's
            footprint, defined as the ratio of length of the short axis divided
            by the length of the long axis. This parameter is used to estimate
            building-wide wind pressure coefficients for the AFN by approximating
            the building geometry as an extruded rectangle (Default: 1).

    Properties:
        * vent_control_type
        * reference_temperature
        * reference_pressure
        * reference_humidity_ratio
        * building_type
        * long_axis_angle
        * aspect_ratio
    """
    __slots__ = ('_vent_control_type', '_reference_temperature',
                 '_reference_pressure', '_reference_humidity_ratio',
                 '_building_type', '_long_axis_angle', '_aspect_ratio', '_locked')
    VENT_CONTROL_TYPES = ('SingleZone', 'MultiZoneWithDistribution',
                          'MultiZoneWithoutDistribution')
    BUILDING_TYPES = ('LowRise', 'HighRise')

    def __init__(self, vent_control_type='SingleZone', reference_temperature=20,
                 reference_pressure=101325, reference_humidity_ratio=0,
                 building_type='LowRise', long_axis_angle=0, aspect_ratio=1):
        """Initialize VentilationSimulationControl."""
        self.vent_control_type = vent_control_type
        self.reference_temperature = reference_temperature
        self.reference_pressure = reference_pressure
        self.reference_humidity_ratio = reference_humidity_ratio
        self.building_type = building_type
        self.long_axis_angle = long_axis_angle
        self.aspect_ratio = aspect_ratio

    @property
    def vent_control_type(self):
        """Get or set text indicating type of ventilation control type."""
        return self._vent_control_type

    @vent_control_type.setter
    def vent_control_type(self, value):
        assert value in self.VENT_CONTROL_TYPES, 'vent_control_type {} is not '\
            'recognized.\nChoose from the following:\n{}'.format(
                value, self.VENT_CONTROL_TYPES)
        self._vent_control_type = value

    @property
    def reference_temperature(self):
        """Get or set the temperature for the reference crack."""
        return self._reference_temperature

    @reference_temperature.setter
    def reference_temperature(self, value):
        self._reference_temperature = \
            float_in_range(value, mi=-273.15, input_name='reference_temperature')

    @property
    def reference_pressure(self):
        """Get or set the barometric pressure for the reference crack."""
        return self._reference_pressure

    @reference_pressure.setter
    def reference_pressure(self, value):
        self._reference_pressure = \
            float_in_range(value, 31000, 120000, 'reference_pressure')

    @property
    def reference_humidity_ratio(self):
        """Get or set the humidity ratio for the reference crack."""
        return self._reference_humidity_ratio

    @reference_humidity_ratio.setter
    def reference_humidity_ratio(self, value):
        self._reference_humidity_ratio = \
            float_positive(value, 'reference_humidity_ratio')

    @property
    def building_type(self):
        """Get or set text indicating whether the building is high or low rise."""
        return self._building_type

    @building_type.setter
    def building_type(self, value):
        assert value in self.BUILDING_TYPES, 'building_type {} is not '\
            'recognized.\nChoose from the following:\n{}'.format(
                value, self.BUILDING_TYPES)
        self._building_type = value

    @property
    def long_axis_angle(self):
        """Get or set a number between 0 and 180 for the building long axis angle.

        The value represents the clockwise difference between the long axis and
        true North. 0 indicates a North-South long axis while 90 indicates an
        East-West long axis.
        """
        return self._long_axis_angle

    @long_axis_angle.setter
    def long_axis_angle(self, value):
        self._long_axis_angle = float_in_range(value, 0, 180, 'long_axis_angle')

    @property
    def aspect_ratio(self):
        """Get or set a number between 0 and 1 for the building footprint aspect ratio.
        """
        return self._aspect_ratio

    @aspect_ratio.setter
    def aspect_ratio(self, value):
        self._aspect_ratio = float_in_range_excl_incl(value, 0, 1, 'aspect_ratio')

    def assign_geometry_properties_from_rooms(self, rooms):
        """Assign the geometry properties of this object using an array of Honeybee Rooms.

        The building_type (HighRise or LowRise) will be determined by analyzing
        the bounding box around the Rooms (assessing whether the box is taller than
        it is wide + long).

        This object's long_axis_angle will be used to orient the bounding box and
        compute the aspect ratio of the footprint. If the length of what should
        be the short axis ends up being longer than the other axis, this object's
        long_axis_angle will be rotated 90 degrees in order to keep the aspect
        ratio from being greater than 1.

        Args:
            rooms: An array of Honeybee Rooms, which will have their geometry
                collectively analyzed in order to set the geometry properties
                of this object. Typically, this should be all of the Rooms of
                a Honeybee Model.
        """
        l_axis = self.long_axis_angle
        bldg_type, aspect_r = self.geometry_properties_from_rooms(rooms, l_axis)
        self.building_type = bldg_type
        if aspect_r > 1:  # rotate the long axis 90 degrees
            aspect_r = 1 / aspect_r
            self.long_axis_angle = l_axis + 90 if l_axis < 90 else l_axis - 90
        self.aspect_ratio = aspect_r

    @classmethod
    def from_dict(cls, data):
        """Create a VentilationSimulationControl object from a dictionary.

        Args:
            data: A VentilationSimulationControl dictionary following the format below.

        .. code-block:: python

            {
            "type": "VentilationSimulationControl"
            "vent_control_type": SingleZone # type of ventilation control
            "reference_temperature": 20 # reference crack temperature
            "reference_pressure": 101320 # reference crack barometric pressure
            "reference_humidity_ratio": 0.5 # reference crack humidity ratio
            "building_type": 'LowRise' # building type text
            "long_axis_angle": 0 # angle of building low axis
            "aspect_ratio": 1 # aspect ratio of building footprint
            }
        """
        assert data['type'] == 'VentilationSimulationControl', 'Expected ' \
            'VentilationSimulationControl dictionary. Got {}.'.format(data['type'])

        vent_control_type = data['vent_control_type'] if 'vent_control_type' in data \
            and data['vent_control_type'] is not None else 'SingleZone'
        ref_temp = data['reference_temperature'] if 'reference_temperature' in data \
            and data['reference_temperature'] is not None else 20
        ref_pres = data['reference_pressure'] if \
            'reference_pressure' in data and \
            data['reference_pressure'] is not None else 101320
        ref_hum = data['reference_humidity_ratio'] if 'reference_humidity_ratio' in \
            data and data['reference_humidity_ratio'] is not None else 0
        bld_type = data['building_type'] if 'building_type' in data and \
            data['building_type'] is not None else 'LowRise'
        axis = data['long_axis_angle'] if 'long_axis_angle' in data and \
            data['long_axis_angle'] is not None else 0
        ratio = data['aspect_ratio'] if 'aspect_ratio' in data and data['aspect_ratio'] \
            is not None else 1
        return cls(vent_control_type, ref_temp, ref_pres, ref_hum, bld_type, axis, ratio)

    def to_dict(self):
        """VentilationSimulationControl dictionary representation."""
        base = {'type': 'VentilationSimulationControl'}
        base['vent_control_type'] = self.vent_control_type
        base['reference_temperature'] = self.reference_temperature
        base['reference_pressure'] = self.reference_pressure
        base['reference_humidity_ratio'] = self.reference_humidity_ratio
        base['building_type'] = self.building_type
        base['long_axis_angle'] = self.long_axis_angle
        base['aspect_ratio'] = self.aspect_ratio
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    @staticmethod
    def geometry_properties_from_rooms(rooms, axis_angle=0):
        """Get AFN building geometry properties from an array of Honeybee Rooms.

        Args:
            rooms: An array of Honeybee Rooms, which will have their geometry
                collectively analyzed.
            axis_angle: The clockwise rotation angle in degrees in the XY plane
                to represent the orientation of the bounding box. (Default: 0).

        Returns:
            A tuple with 2 values for geometry properties.

            1) Text indicating the building_type (either Highrise or LowRise)
            2) A number for the aspect ratio of the axis_angle-oriented bounding box.

            Note that the aspect ratio may be greater than 1 if the axis_angle
            isn't aligned to the long axis of the geometry.
        """
        # process the inputs to be suitable for ladybug_geometry
        if axis_angle != 0:  # convert to counter-clockwise radians for ladybug_geometry
            axis_angle = -math.radians(axis_angle)
        geo = [room.geometry for room in rooms]  # get ladybug_geometry polyfaces

        # get the bounding box and return the properties
        xx, yy, zz = bounding_box_extents(geo)
        bldg_type = 'LowRise' if zz <= 3 * max(xx, yy) else 'HighRise'
        return bldg_type, xx / yy

    def __copy__(self):
        return VentilationSimulationControl(
            self.vent_control_type, self.reference_temperature,
            self.reference_pressure, self.reference_humidity_ratio,
            self.building_type, self.long_axis_angle, self.aspect_ratio)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.vent_control_type, self.reference_temperature,
                self.reference_pressure, self.reference_humidity_ratio,
                self.building_type, self.long_axis_angle, self.aspect_ratio)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, VentilationSimulationControl) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'VentilationSimulationControl: [control type: {}] ' \
            '[building_type: {}] [long axis: {}] [aspect_ratio: {}]' .format(
                self.vent_control_type, self.building_type,
                round(self.long_axis_angle), round(self.aspect_ratio, 2))
