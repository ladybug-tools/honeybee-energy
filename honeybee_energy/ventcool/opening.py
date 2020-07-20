# coding=utf-8
"""Definition of window opening for ventilative cooling."""
from __future__ import division

from .control import VentilationControl
from ..writer import generate_idf_string

from honeybee.typing import float_in_range


class VentilationOpening(object):
    """Definition of window opening for ventilative cooling.

    Args:
        fraction_area_operable: A number between 0.0 and 1.0 for the fraction of the
            window area that is operable. (Default: 0.5, typical of sliding windows).
        fraction_height_operable: A number between 0.0 and 1.0 for the fraction
            of the distance from the bottom of the window to the top that is
            operable. (Default: 1.0, typical of windows that slide horizontally).
        discharge_coefficient: A number between 0.0 and 1.0 that will be multipled
            by the area of the window in the stack (buoyancy-driven) part of the
            equation to account for additional friction from window geometry,
            insect screens, etc. (Default: 0.17, for unobstructed windows with
            insect screens). This value should be lowered if windows are of an
            awning or casement type and not allowed to fully open. Some common
            values for this coefficient include the following.

                * 0.0 - Completely discount stack ventilation from the calculation.
                * 0.17 - For unobstructed windows with an insect screen.
                * 0.25 - For unobstructed windows with NO insect screen.

        wind_cross_vent: Boolean to indicate if there is an opening of roughly
            equal area on the opposite side of the Room such that wind-driven
            cross ventilation will be induced. If False, the assumption is that
            the operable area is primarily on one side of the Room and there is
            no wind-driven ventilation. (Default: False)

    Properties:
        * fraction_area_operable
        * fraction_height_operable
        * discharge_coefficient
        * wind_cross_vent
        * parent
        * has_parent
    """
    __slots__ = ('_fraction_area_operable', '_fraction_height_operable',
                 '_discharge_coefficient', '_wind_cross_vent', '_parent')

    def __init__(self, fraction_area_operable=0.5, fraction_height_operable=1.0,
                 discharge_coefficient=0.17, wind_cross_vent=False):
        """Initialize VentilationOpening."""
        self.fraction_area_operable = fraction_area_operable
        self.fraction_height_operable = fraction_height_operable
        self.discharge_coefficient = discharge_coefficient
        self.wind_cross_vent = wind_cross_vent
        self._parent = None  # this will be set when assigned to an aperture

    @property
    def fraction_area_operable(self):
        """Get or set a number for the fraction of the window area that is operable."""
        return self._fraction_area_operable

    @fraction_area_operable.setter
    def fraction_area_operable(self, value):
        self._fraction_area_operable = \
            float_in_range(value, 0.0, 1.0, 'fraction area operable')

    @property
    def fraction_height_operable(self):
        """Get or set a number for the fraction of the window height that is operable."""
        return self._fraction_height_operable

    @fraction_height_operable.setter
    def fraction_height_operable(self, value):
        self._fraction_height_operable = \
            float_in_range(value, 0.0, 1.0, 'fraction height operable')

    @property
    def discharge_coefficient(self):
        """Get or set a number for the discharge coefficient."""
        return self._discharge_coefficient

    @discharge_coefficient.setter
    def discharge_coefficient(self, value):
        self._discharge_coefficient = \
            float_in_range(value, 0.0, 1.0, 'discharge coefficient')

    @property
    def wind_cross_vent(self):
        """Get or set a boolean for whether there is cross ventilation from the window.

        Note that this property only has significance for simulations with simple
        ZoneVentilation objects and has no bearing on simulations with the
        Airflow Network.

        This should be True if there is an opening of roughly equal area on the
        opposite side of the Room such that wind-driven cross ventilation will
        be induced. If False, the assumption is that the operable area is primarily
        on one side of the Room and there is no wind-driven ventilation.
        """
        return self._wind_cross_vent

    @wind_cross_vent.setter
    def wind_cross_vent(self, value):
        self._wind_cross_vent = bool(value)

    @property
    def parent(self):
        """Get the parent of this object if it exists."""
        return self._parent

    @property
    def has_parent(self):
        """Get a boolean noting whether this VentilationOpening has a parent object."""
        return self._parent is not None

    @classmethod
    def from_dict(cls, data):
        """Create a VentilationOpening object from a dictionary.

        Args:
            data: A VentilationOpening dictionary in following the format below.

        .. code-block:: python

            {
            "type": "VentilationOpening",
            "fraction_area_operable": 0.5,  # Fractional number for area operable
            "fraction_height_operable": 0.5,  # Fractional number for height operable
            "discharge_coefficient": 0.17,  # Fractional number for discharge coefficient
            "wind_cross_vent": True  # Wind-driven cross ventilation
            }
        """
        assert data['type'] == 'VentilationOpening', \
            'Expected VentilationOpening dictionary. Got {}.'.format(data['type'])

        area_op = data['fraction_area_operable'] if 'fraction_area_operable' in data \
            and data['fraction_area_operable'] is not None else 0.5
        height_op = data['fraction_height_operable'] if 'fraction_height_operable' in data \
            and data['fraction_height_operable'] is not None else 1.0
        discharge = data['discharge_coefficient'] if 'discharge_coefficient' in data \
            and data['discharge_coefficient'] is not None else 0.17
        cross_vent = data['wind_cross_vent'] if 'wind_cross_vent' in data \
            and data['wind_cross_vent'] is not None else False

        return cls(area_op, height_op, discharge, cross_vent)

    def to_idf(self):
        """IDF string representation of VentilationOpening object.

        Note that this ventilation opening must be assigned to a honeybee Aperture
        or Door for this method to run. This parent Aperture or Door must also have
        a parent Room. It is also recommended that this Room have a VentilationControl
        object under its energy properties. Otherwise, the default control sequence
        will be used, which will likely result in the window never opening.

        Also note that the parent's geometry should be in meters whenever calling
        this method and that this method does not return full definitions of
        ventilation control schedules. So these schedules must also be translated
        into the final IDF file.
        """
        # check that a parent is assigned
        assert self.parent is not None, \
            'VentilationOpening must be assigned to an Aperture or Door to use to_idf().'

        # get the VentilationControl object from the room
        cntrl = None
        room = None
        if self.parent.has_parent:
            if self.parent.parent.has_parent:
                room = self.parent.parent.parent
                if room.properties.energy.window_vent_control is not None:
                    cntrl = room.properties.energy.window_vent_control
        if cntrl is None:  # use default ventilation control
            cntrl = VentilationControl()
        assert room is not None, \
            'VentilationOpening must have a parent Room to use to_idf().'

        # process the properties on this object into IDF format
        sch = '' if cntrl.schedule is None else cntrl.schedule.identifier
        wind = 'autocalculate' if self.wind_cross_vent else 0
        angle = self.parent.horizontal_orientation() if self.parent.normal.z != 1 else 0
        height = (self.parent.geometry.max.z - self.parent.geometry.min.z) * \
            self.fraction_height_operable

        # create the final IDF string
        values = (
            '{}_Opening'.format(self.parent.identifier), room.identifier,
            self.parent.area * self.fraction_area_operable, sch, wind, angle,
            height, self.discharge_coefficient, cntrl.min_indoor_temperature, '',
            cntrl.max_indoor_temperature, '', cntrl.delta_temperature, '',
            cntrl.min_outdoor_temperature, '', cntrl.max_outdoor_temperature, '', 40)
        comments = (
            'name', 'zone name', 'opening area', 'opening schedule',
            'opening effectiveness {m2}', 'horizontal orientation angle',
            'height difference {m}', 'discharge coefficient',
            'min indoor temperature {C}', 'min in temp schedule',
            'max indoor temperature {C}', 'max in temp schedule',
            'delta temperature {C}', 'delta temp schedule',
            'min outdoor temperature {C}', 'min out temp schedule',
            'max outdoor temperature {C}', 'max out temp schedule', 'max wind speed')
        return generate_idf_string(
            'ZoneVentilation:WindandStackOpenArea', values, comments)

    def to_dict(self):
        """Ventilation Opening dictionary representation."""
        base = {'type': 'VentilationOpening'}
        base['fraction_area_operable'] = self.fraction_area_operable
        base['fraction_height_operable'] = self.fraction_height_operable
        base['discharge_coefficient'] = self.discharge_coefficient
        base['wind_cross_vent'] = self.wind_cross_vent
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        return VentilationOpening(
            self.fraction_area_operable, self.fraction_height_operable,
            self.discharge_coefficient, self.wind_cross_vent)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.fraction_area_operable, self.fraction_height_operable,
                self.discharge_coefficient, self.wind_cross_vent)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, VentilationOpening) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'VentilationOpening,\n fraction area: {}\n ' \
            'fration height: {}\n discharge coeff: {}'.format(
                self.fraction_area_operable, self.fraction_height_operable,
                self.discharge_coefficient)
