# coding=utf-8
"""Definitions for global parameters used in the ventilation simulation."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, float_in_range_excl_incl


@lockable
class VentilationSimulationControl(object):
    """Global parameters used in the ventilation simulation.

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
            the surface crack data were obtained. (Default: 20).
        reference_pressure: Reference barometric pressure measurement in
            Pascals under which the surface crack data were obtained. (Default: 101325).
        reference_humidity_ratio: Reference humidity ratio measurement in
            kgWater/kgDryAir under which the surface crack data were obtained.
            (Default: 0).
        building_type: Text indicating relationship between building footprint and
            height used to calculate the wind pressure coefficients for exterior
            surfaces.
            Choose from the following:

            * LowRise
            * HighRise

            LowRise corresponds to rectangular building whose height is less then three
            times the width and length of the footprint. HighRise corresponds to a
            rectangular building whose height is more than three times the width and
            length of the footprint. This parameter is required to automatically
            calculate wind pressure coefficients for the AirflowNetwork simulation.
            If used for complex building geometries that cannot be described as a
            highrise or lowrise rectangular mass, the resulting air flow and pressure
            simulated on the building surfaces may be inaccurate. (Default: 'LowRise').
        long_axis_angle: The clockwise rotation in degrees from true North of the long
            axis of the building. This parameter is required to automatically calculate
            wind pressure coefficients for the AirflowNetwork simulation. If used for
            complex building geometries that cannot be described as a highrise or
            lowrise rectangular mass, the resulting air flow and pressure simulated on
            the building surfaces may be inaccurate. (Default: 0).
        aspect_ratio: Aspect ratio of a rectangular footprint, defined as the ratio of
            length of the short axis divided by the length of the long axis. This
            parameter is required to automatically calculate wind pressure coefficients
            for the AirflowNetwork simulation. If used for complex building geometries
            that cannot be described as a highrise or lowrise rectangular mass, the
            resulting air flow and pressure simulated on the building surfaces may be
            inaccurate. (Default: 1).

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
        """Get or set text indicating type of building type."""
        return self._building_type

    @building_type.setter
    def building_type(self, value):
        assert value in self.BUILDING_TYPES, 'building_type {} is not '\
            'recognized.\nChoose from the following:\n{}'.format(
                value, self.BUILDING_TYPES)
        self._building_type = value

    @property
    def long_axis_angle(self):
        """Get or set angle of the long axis of building."""
        return self._long_axis_angle

    @long_axis_angle.setter
    def long_axis_angle(self, value):
        self._long_axis_angle = float_in_range(value, 0, 180, 'long_axis_angle')

    @property
    def aspect_ratio(self):
        """Get or set the aspect ratio of the building footprint."""
        return self._aspect_ratio

    @aspect_ratio.setter
    def aspect_ratio(self, value):
        self._aspect_ratio = float_in_range_excl_incl(value, 0, 1, 'aspect_ratio')

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
        return 'VentilationSimulationControl,\n vent_control_type: {}\n ' \
            'reference_temperature: {}\n reference_pressure: {}\n ' \
            'reference_humidity_ratio: {}\n building_type: {}\n long_axis_angle: {}\n' \
            'aspect_ratio: {}' .format(
                self.vent_control_type, self.reference_temperature,
                self.reference_pressure, self.reference_humidity_ratio,
                self.building_type, self.long_axis_angle, self.aspect_ratio)
