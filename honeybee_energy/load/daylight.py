# coding=utf-8
"""Room daylight controls, including sensor location and setpoint."""
from __future__ import division
import math

from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee.typing import float_in_range, float_positive

from ..reader import parse_idf_string
from ..writer import generate_idf_string


class DaylightingControl(object):
    """Room daylight controls, including sensor location and setpoint.

    Args:
        sensor_position: A ladybug_geometry Point3D for the position of the daylight
            sensor within the parent Room. This point should lie within the Room
            volume in order for the results to be meaningful. The ladybug_geometry
            Polyface.is_point_inside method can be used to check whether a given
            point is inside the room volume.
        illuminance_setpoint: A number for the illuminance setpoint in lux beyond
            which electric lights are dimmed if there is sufficient daylight.
            Some common setpoints are listed below. (Default: 300 lux).

            * 50 lux - Corridors and hallways.
            * 150 lux - Computer work spaces (screens provide illumination).
            * 300 lux - Paper work spaces (reading from surfaces needing illumination).
            * 500 lux - Retail spaces or museums illuminating merchandise/artifacts.
            * 1000 lux - Operating rooms and workshops where light is needed for safety.

        control_fraction: A number between 0 and 1 that represents the fraction of
            the Room lights that are dimmed when the illuminance at the sensor
            position is at the specified illuminance. 1 indicates that all lights are
            dim-able while 0 indicates that no lights are dim-able. Deeper rooms
            should have lower control fractions to account for the face that the
            lights in the back of the space do not dim in response to suitable
            daylight at the front of the room. (Default: 1).
        min_power_input: A number between 0 and 1 for the the lowest power the
            lighting system can dim down to, expressed as a fraction of maximum
            input power. (Default: 0.3).
        min_light_output: A number between 0 and 1 the lowest lighting output the
            lighting system can dim down to, expressed as a fraction of maximum
            light output. (Default: 0.2).
        off_at_minimum: Boolean to note whether lights should switch off completely
            when they get to the minimum power input. (Default: False).


    Properties:
        * sensor_position
        * illuminance_setpoint
        * control_fraction
        * min_power_input
        * min_light_output
        * off_at_minimum
        * parent
        * has_parent
        * is_sensor_inside_parent
    """
    __slots__ = ('_sensor_position', '_illuminance_setpoint', '_control_fraction',
                 '_min_power_input', '_min_light_output', '_off_at_minimum', '_parent')

    def __init__(self, sensor_position, illuminance_setpoint=300, control_fraction=1,
                 min_power_input=0.3, min_light_output=0.2, off_at_minimum=False):
        self.sensor_position = sensor_position
        self.illuminance_setpoint = illuminance_setpoint
        self.control_fraction = control_fraction
        self.min_power_input = min_power_input
        self.min_light_output = min_light_output
        self.off_at_minimum = off_at_minimum
        self._parent = None  # _parent will be set when the object is added to a Room

    @property
    def sensor_position(self):
        """Get or set a Point3D for the sensor position for the daylight sensor."""
        return self._sensor_position

    @sensor_position.setter
    def sensor_position(self, value):
        assert isinstance(value, Point3D), 'Expected Point3D for DaylightingControl ' \
            'sensor_position. Got {}.'.format(type(value))
        self._sensor_position = value

    @property
    def illuminance_setpoint(self):
        """Get or set a number for the illuminance setpoint in lux."""
        return self._illuminance_setpoint

    @illuminance_setpoint.setter
    def illuminance_setpoint(self, value):
        self._illuminance_setpoint = float_positive(value, 'illuminance setpoint')

    @property
    def control_fraction(self):
        """Get or set the fraction of the Room lights that are dimmed."""
        return self._control_fraction

    @control_fraction.setter
    def control_fraction(self, value):
        if value is not None:
            self._control_fraction = float_in_range(
                value, 0.0, 1.0, 'daylighting control fraction')
        else:
            self._control_fraction = 1

    @property
    def min_power_input(self):
        """Get or set the lowest power the lighting system can dim down to."""
        return self._min_power_input

    @min_power_input.setter
    def min_power_input(self, value):
        if value is not None:
            self._min_power_input = float_in_range(
                value, 0.0, 1.0, 'daylighting control min_power_input')
        else:
            self._min_power_input = 0.3

    @property
    def min_light_output(self):
        """Get or set the lowest lighting output the lighting system can dim down to."""
        return self._min_light_output

    @min_light_output.setter
    def min_light_output(self, value):
        if value is not None:
            self._min_light_output = float_in_range(
                value, 0.0, 1.0, 'daylighting control min_light_output')
        else:
            self._min_light_output = 0.2

    @property
    def off_at_minimum(self):
        """Get or set a boolean to indicate whether the lights switch off completely."""
        return self._off_at_minimum

    @off_at_minimum.setter
    def off_at_minimum(self, value):
        self._off_at_minimum = bool(value)

    @property
    def parent(self):
        """Get the parent Room if assigned. None if not assigned."""
        return self._parent

    @property
    def has_parent(self):
        """Get a boolean noting whether this object has a parent Room."""
        return self._parent is not None

    @property
    def is_sensor_inside_parent(self):
        """Get a boolean for whether the sensor position is inside the parent Room.

        This will always be True if no parent is assigned.
        """
        if self.parent is not None:
            return self.parent.geometry.is_point_inside(self.sensor_position)

    def move(self, moving_vec):
        """Move this object along a vector.

        Args:
            moving_vec: A ladybug_geometry Vector3D with the direction and distance
                to move the sensor.
        """
        self.sensor_position = self.sensor_position.move(moving_vec)

    def rotate(self, angle, axis, origin):
        """Rotate this object by a certain angle around an axis and origin.

        Args:
            angle: An angle for rotation in degrees.
            axis: Rotation axis as a Vector3D.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        rad_angle = math.radians(angle)
        self.sensor_position = self.sensor_position.rotate(axis, rad_angle, origin)

    def rotate_xy(self, angle, origin):
        """Rotate this object counterclockwise in the world XY plane by a certain angle.

        Args:
            angle: An angle in degrees.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        rad_angle = math.radians(angle)
        self.sensor_position = self.sensor_position.rotate_xy(rad_angle, origin)

    def reflect(self, plane):
        """Reflect this object across a plane.

        Args:
            plane: A ladybug_geometry Plane across which the object will
                be reflected.
        """
        self.sensor_position = self.sensor_position.reflect(plane.n, plane.o)

    def scale(self, factor, origin=None):
        """Scale this object by a factor from an origin point.

        Args:
            factor: A number representing how much the object should be scaled.
            origin: A ladybug_geometry Point3D representing the origin from which
                to scale. If None, it will be scaled from the World origin (0, 0, 0).
        """
        self.sensor_position = self.sensor_position.scale(factor, origin)

    @classmethod
    def from_idf(cls, idf_string, idf_point_string):
        """Create a DaylightingControl object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                Daylighting:Controls definition.
            idf_point_string: A text string fully describing an EnergyPlus
                Daylighting:ReferencePoint definition.

        Returns:
            A DaylightingControl object loaded from the idf_string.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'Daylighting:Controls,')
        ep_strs_pt = parse_idf_string(idf_point_string, 'Daylighting:ReferencePoint,')
        assert ep_strs[1] == ep_strs_pt[1], 'Zone names do not match between ' \
            'IDF daylight controls and reference point'

        # extract the properties from the string
        off_at_min = True if ep_strs[4].lower() == 'continuousoff' else False
        min_power = ep_strs[5] if ep_strs[5] != '' else 0.3
        min_output = ep_strs[6] if ep_strs[6] != '' else 0.2
        cntrl_fract = 1
        setpoint = 500
        try:
            cntrl_fract = ep_strs[14] if ep_strs[14] != '' else 1
            setpoint = ep_strs[15] if ep_strs[15] != '' else 500
        except IndexError:
            pass  # shorter daylight controls definition lacking certain fields

        # extract the coordinates of the control point
        ptx, pty = ep_strs_pt[2], ep_strs_pt[3]
        try:
            ptz = ep_strs_pt[4] if ep_strs_pt[4] != '' else 0.8
        except IndexError:
            pass  # shorter definition lacking certain fields

        # return the daylighting object
        return cls(Point3D(ptx, pty, ptz), setpoint, cntrl_fract,
                   min_power, min_output, off_at_min)

    @classmethod
    def from_dict(cls, data):
        """Create a DaylightingControl object from a dictionary.

        Args:
            data: A DaylightingControl dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'DaylightingControl',
            "sensor_position": [5, 5, 0.8]  # array of xyz coordinates for the sensor
            "illuminance_setpoint": 300,  # number for illuminance setpoint in lux
            "control_fraction": 0.5,  # fraction of the lights that are dim-able
            "min_power_input": 0.3,  # minimum fraction of lighting power
            "min_light_output": 0.2,  # minimum fraction of lighting output
            "off_at_minimum": True  # boolean for whether the lights switch off
            }
        """
        assert data['type'] == 'DaylightingControl', \
            'Expected DaylightingControl dictionary. Got {}.'.format(data['type'])
        sensor = Point3D.from_array(data['sensor_position'])
        setpoint = data['illuminance_setpoint'] \
            if 'illuminance_setpoint' in data else 300
        cntrl_fract = data['control_fraction'] if 'control_fraction' in data else 1
        min_pow = data['min_power_input'] if 'min_power_input' in data else 0.3
        min_out = data['min_light_output'] if 'min_light_output' in data else 0.2
        off_min = data['off_at_minimum'] if 'off_at_minimum' in data else False
        return cls(sensor, setpoint, cntrl_fract, min_pow, min_out, off_min)

    def to_idf(self):
        """IDF string representation of DaylightingControl object.

        Returns:
            A tuple with two values.

            -   idf_control -- IDF string for the Daylighting:Controls object.

            -   idf_point -- IDF string for the Daylighting:ReferencePoint object.
        """
        # create the identifiers
        zone_id = self.parent.identifier if self.has_parent else 'Unknown_Room'
        controls_name = '{}_Daylighting'.format(zone_id)
        point_name = '{}_Sensor'.format(zone_id)

        # create the IDF string for the Daylighting:Controls
        cntrl_type = 'ContinuousOff' if self.off_at_minimum else 'Continuous'
        cntrl_values = \
            (controls_name, zone_id, 'SplitFlux', '', cntrl_type, self.min_power_input,
             self.min_light_output, '', '', '', '', '', '', point_name,
             self.control_fraction, self.illuminance_setpoint)
        cntrl_comments = \
            ('name', 'zone name', 'daylight method', 'availability schedule',
             'control type', 'min power input', 'min lighting input',
             'control step count', 'reset probability', 'glare point', 'glare azimuth',
             'max glare index', 'DElight grid res', 'reference point',
             'control fraction', 'illuminance setpoint')
        idf_control = generate_idf_string(
            'Daylighting:Controls', cntrl_values, cntrl_comments)

        # create the IDF string for the Daylighting:ReferencePoint
        sensor = self.sensor_position
        pt_values = (point_name, zone_id, sensor.x, sensor.y, sensor.z)
        pt_comments = ('name', 'zone name', 'X', 'Y', 'Z')
        idf_point = generate_idf_string(
            'Daylighting:ReferencePoint', pt_values, pt_comments)
        return idf_control, idf_point

    def to_dict(self, abridged=False):
        """DaylightingControl dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        return {
            'type': 'DaylightingControl',
            'sensor_position': self.sensor_position.to_array(),
            'illuminance_setpoint': self.illuminance_setpoint,
            'control_fraction': self.control_fraction,
            'min_power_input': self.min_power_input,
            'min_light_output': self.min_light_output,
            'off_at_minimum': self.off_at_minimum
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self.sensor_position), self.illuminance_setpoint,
                self.control_fraction, self.min_power_input, self.min_light_output,
                self.off_at_minimum)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, DaylightingControl) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        return DaylightingControl(
            self.sensor_position, self.illuminance_setpoint, self.control_fraction,
            self.min_power_input, self.min_light_output, self.off_at_minimum)

    def __repr__(self):
        pt = self.sensor_position
        return 'DaylightingControl: [sensor: {}] [{} lux]'.format(
            '(%.2f, %.2f, %.2f)' % (pt.x, pt.y, pt.z), self.illuminance_setpoint)
