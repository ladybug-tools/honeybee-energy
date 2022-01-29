# coding=utf-8
"""Shade Construction."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, float_in_range, clean_rad_string

from .window import WindowConstruction
from ..material.glazing import EnergyWindowMaterialGlazing
from ..writer import generate_idf_string
from ..properties.extension import ShadeConstructionProperties


@lockable
class ShadeConstruction(object):
    """Construction for Shade objects.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        solar_reflectance: A number between 0 and 1 for the solar reflectance
            of the construction. Default: 0.2.
        visible_reflectance: A number between 0 and 1 for the visible reflectance
            of the construction. Default: 0.2.
        is_specular: A boolean to note whether the reflection off the shade
            should be diffuse (False) or specular (True). Set to True if the
            construction is representing a glass facade or a mirror material.
            Default: False.

    Properties:
        * identifier
        * display_name
        * solar_reflectance
        * visible_reflectance
        * is_specular
        * is_default
        * inside_solar_reflectance
        * inside_visible_reflectance
        * outside_solar_reflectance
        * outside_visible_reflectance
        * user_data
    """

    __slots__ = ('_identifier', '_display_name', '_solar_reflectance',
                 '_visible_reflectance', '_is_specular',
                 '_locked', '_properties', '_user_data')

    def __init__(self, identifier, solar_reflectance=0.2, visible_reflectance=0.2,
                 is_specular=False):
        """Initialize shade construction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.solar_reflectance = solar_reflectance
        self.visible_reflectance = visible_reflectance
        self.is_specular = is_specular
        self._user_data = None
        self._properties = ShadeConstructionProperties(self)

    @property
    def identifier(self):
        """Get or set the text string for construction identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'construction identifier')

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
    def solar_reflectance(self):
        """Get or set the solar reflectance of the shade."""
        return self._solar_reflectance

    @solar_reflectance.setter
    def solar_reflectance(self, value):
        self._solar_reflectance = float_in_range(
            value, 0, 1, 'shade construction solar reflectance')

    @property
    def visible_reflectance(self):
        """Get or set the visible reflectance of the shade."""
        return self._visible_reflectance

    @visible_reflectance.setter
    def visible_reflectance(self, value):
        self._visible_reflectance = float_in_range(
            value, 0, 1, 'shade construction visible reflectance')

    @property
    def is_specular(self):
        """Get or set a boolean to note whether the reflection is diffuse or specular."""
        return self._is_specular

    @is_specular.setter
    def is_specular(self, value):
        try:
            self._is_specular = bool(value)
        except TypeError:
            raise TypeError('Expected boolean for ShadeConstruction.is_specular. '
                            'Got {}.'.format(type(value)))

    @property
    def is_default(self):
        """Get a Boolean for whether all properties follow the EnergyPlus default."""
        return self._solar_reflectance == 0.2 and \
            self._visible_reflectance == 0.2 and not self._is_specular

    @property
    def inside_solar_reflectance(self):
        """Get the solar reflectance of the construction."""
        return self._solar_reflectance

    @property
    def inside_visible_reflectance(self):
        """Get the visible reflectance of the construction."""
        return self._visible_reflectance

    @property
    def outside_solar_reflectance(self):
        """Get the solar reflectance of the construction."""
        return self._solar_reflectance

    @property
    def outside_visible_reflectance(self):
        """Get the visible reflectance of the construction."""
        return self._visible_reflectance

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
                'object _user_data. Got {}.'.format(type(value))
        self._user_data = value

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    def glazing_construction(self):
        """Get a WindowConstruction that EnergyPlus uses for specular reflection.

        Will be None if is_specular is False.
        """
        if not self.is_specular:
            return None
        glz_mat = EnergyWindowMaterialGlazing(
            self.identifier, solar_transmittance=0,
            solar_reflectance=self.solar_reflectance,
            visible_transmittance=0, visible_reflectance=self.visible_reflectance)
        return WindowConstruction(self.identifier, [glz_mat])

    @classmethod
    def from_dict(cls, data):
        """Create a ShadeConstruction from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'ShadeConstruction',
            "identifier": 'Diffuse Overhang Construction 035',
            "display_name": 'Overhang Construction',
            "solar_reflectance": 0.35,
            "visible_reflectance": 0.35,
            "is_specular": False
            }
        """
        assert data['type'] == 'ShadeConstruction', \
            'Expected ShadeConstruction. Got {}.'.format(data['type'])
        s_ref = data['solar_reflectance'] if 'solar_reflectance' in data else 0.2
        v_ref = data['visible_reflectance'] if 'visible_reflectance' in data else 0.2
        spec = data['is_specular'] if 'is_specular' in data else False
        new_obj = cls(data['identifier'], s_ref, v_ref, spec)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_idf(self, host_shade_identifier):
        """IDF string for the ShadingProperty:Reflectance of this construction.

        Note that, if is_specular is True, the glazing_construction() method must
        be used to also write the glazing construction into the IDF.

        Args:
            host_shade_identifier: Text string for the identifier of a Shade object that
                possesses this ShadeConstruction.
        """
        values = [host_shade_identifier, self.solar_reflectance,
                  self.visible_reflectance]
        if self.is_specular:
            values.extend([1, self.identifier])
            comments = ('shading surface name', 'solar reflectance',
                        'visible reflectance',
                        'fraction of shading surface that is glazed',
                        'glazing construction name')
        else:
            comments = ('shading surface name', 'solar reflectance',
                        'visible reflectance')
        return generate_idf_string('ShadingProperty:Reflectance', values, comments)

    def to_radiance_solar(self):
        """Honeybee Radiance material with the solar reflectance."""
        return self._to_radiance(self.solar_reflectance)

    def to_radiance_visible(self):
        """Honeybee Radiance material with the visible reflectance."""
        return self._to_radiance(self.visible_reflectance)

    def to_dict(self):
        """Shade construction dictionary representation."""
        base = {'type': 'ShadeConstruction'}
        base['identifier'] = self.identifier
        base['solar_reflectance'] = self.solar_reflectance
        base['visible_reflectance'] = self.visible_reflectance
        base['is_specular'] = self.is_specular
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def _to_radiance(self, reflectance):
        try:
            from honeybee_radiance.modifier.material import Plastic
            from honeybee_radiance.modifier.material import Mirror
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_* methods. {}'.format(e))
        if not self.is_specular:
            return Plastic.from_single_reflectance(
                clean_rad_string(self.identifier), reflectance, roughness=0.15)
        else:
            return Mirror.from_single_reflectance(
                clean_rad_string(self.identifier), reflectance)

    def __copy__(self):
        new_con = ShadeConstruction(
            self.identifier, self._solar_reflectance, self._visible_reflectance,
            self._is_specular)
        new_con._display_name = self._display_name
        new_con._user_data = None if self._user_data is None else self._user_data.copy()
        new_con._properties._duplicate_extension_attr(self._properties)
        return new_con

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self._solar_reflectance,
                self._visible_reflectance, self._is_specular)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ShadeConstruction) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ShadeConstruction: {} [solar_ref: {}]'.format(
            self.display_name, self.solar_reflectance)
