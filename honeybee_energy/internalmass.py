# coding=utf-8
"""Room internal mass, including construction and surface area."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, float_positive
from honeybee.units import conversion_factor_to_meters

from .construction.opaque import OpaqueConstruction
from .reader import parse_idf_string
from .writer import generate_idf_string


@lockable
class InternalMass(object):
    """Room internal mass, including construction and surface area.

    Note that internal masses assigned this way cannot "see" solar radiation that
    may potentially hit them and, as such, caution should be taken when using this
    component with internal mass objects that are not always in shade. Masses are
    factored into the the thermal calculations of the Room by undergoing heat
    transfer with the indoor air.

    Args:
        identifier: Text string for a unique InternalMass ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        construction: An OpaqueConstruction object that represents the material
            that the internal thermal mass is composed of.
        area: A number representing the surface area of the internal mass that
            is exposed to the Room air. This value should always be in square
            meters regardless of what units system the parent model is a part of.


    Properties:
        * identifier
        * display_name
        * construction
        * area
        * user_data
    """
    __slots__ = ('_identifier', '_display_name', '_construction', '_area',
                 '_locked', '_user_data')

    def __init__(self, identifier, construction, area):
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.construction = construction
        self.area = area
        self._user_data = None

    @property
    def identifier(self):
        """Get or set the text string for object identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier)

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def construction(self):
        """Get or set a Construction for the material the internal mass is composed of.
        """
        return self._construction

    @construction.setter
    def construction(self, value):
        assert isinstance(value, OpaqueConstruction), \
            'Expected Opaque Construction for face. Got {}'.format(type(value))
        value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def area(self):
        """Get or set a number for the surface area of the mass exposed to the Room air.
        """
        return self._area

    @area.setter
    def area(self, value):
        self._area = float_positive(value, 'internal mass area')

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        if self._user_data is not None:
            return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    @classmethod
    def from_geometry(cls, identifier, construction, geometry, units='Meters'):
        """Create an InternalMass object from a list of geometries.

        Args:
            identifier: Text string for a unique InternalMass ID. Must be < 100
                characters and not contain any EnergyPlus special characters. This
                will be used to identify the object across a model and in the
                exported IDF.
            construction: An OpaqueConstruction object that represents the material
                that the internal thermal mass is composed of.
            geometry: An array of Face3D representing the exposed surface of the
                internal mass. Note that these Face3D are assumed to be one-sided
                so, if they are meant to represent a 2-sided object, the Face3D
                should be duplicated and offset.
            units: Text for the units system of the geometry. Choose from the following:

                * Meters
                * Millimeters
                * Feet
                * Inches
                * Centimeters
        """
        area = sum(geo.area for geo in geometry) * conversion_factor_to_meters(units)
        return cls(identifier, construction, area)

    @classmethod
    def from_idf(cls, idf_string, construction_dict):
        """Create an InternalMass object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus InternalMass
                definition.
            construction_dict: A dictionary with construction identifiers as keys
                and honeybee construction objects as values. This will be used
                to assign the construction to the InternalMass object.

        Returns:
            An InternalMass object loaded from the idf_string.
        """
        ep_strs = parse_idf_string(idf_string, 'InternalMass,')
        obj_id = ep_strs[0].split('..')[0]
        return cls(obj_id, construction_dict[ep_strs[1]], ep_strs[3])

    @classmethod
    def from_dict(cls, data):
        """Create an InternalMass object from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: An InternalMass dictionary in following the format below.

        .. code-block:: python

            {
            "type": 'InternalMass',
            "identifier": 'Kitchen_Table_Wood_050',
            "display_name": 'Kitchen Table',
            "construction": {},  # OpaqueConstruction definition
            "area": 5  # surface area of internal mass in square meters
            }
        """
        assert data['type'] == 'InternalMass', \
            'Expected InternalMass dictionary. Got {}.'.format(data['type'])
        constr = OpaqueConstruction.from_dict(data['construction'])
        new_obj = cls(data['identifier'], constr, data['area'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, construction_dict):
        """Create a InternalMass from an abridged dictionary.

        Args:
            data: An InternalMassAbridged dictionary.
            construction_dict: A dictionary with construction identifiers as keys
                and honeybee construction objects as values. This will be used
                to assign the construction to the InternalMass object.

        .. code-block:: python

            {
            "type": 'InternalMassAbridged',
            "identifier": 'Kitchen_Table_Wood_050',
            "display_name": 'Kitchen Table',
            "construction": 'Hardwood_050'  # OpaqueConstruction identifier
            "area": 5  # surface area of internal mass in square meters
            }
        """
        assert data['type'] == 'InternalMassAbridged', \
            'Expected InternalMassAbridged dictionary. Got {}.'.format(data['type'])
        new_obj = cls(
            data['identifier'], construction_dict[data['construction']], data['area'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of InternalMass object.

        Note that this method only outputs a single string for the InternalMass
        object and, to write everything needed to describe the object into an IDF,
        this object's construction must also be written.

        Args:
            zone_identifier: Text for the zone identifier that the InternalMass
                object is assigned to.
        """
        values = ('{}..{}'.format(self.identifier, zone_identifier),
                  self.construction.identifier, zone_identifier, self.area)
        comments = ('name', 'construction name', 'zone name', 'surface area')
        return generate_idf_string('InternalMass', values, comments)

    def to_dict(self, abridged=False):
        """InternalMass dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version
                (True), which only specifies the identifiers of the
                construction. (Default: False).
        """
        base = {'type': 'InternalMass'} if not abridged \
            else {'type': 'InternalMassAbridged'}
        base['identifier'] = self.identifier
        base['construction'] = self.construction.to_dict() if not \
            abridged else self.construction.identifier
        base['area'] = self.area
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        new_obj = InternalMass(self.identifier, self.construction, self.area)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, hash(self.construction), self.area)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, InternalMass) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'InternalMass: {}'.format(self.display_name)
