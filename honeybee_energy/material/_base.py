# coding=utf-8
"""Base energy material."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class _EnergyMaterialBase(object):
    """Base energy material.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.

    Properties:
        * identifier
        * display_name
        * user_data
        * properties
    """
    __slots__ = ('_identifier', '_display_name', '_locked', '_user_data', '_properties')

    def __init__(self, identifier):
        """Initialize energy material base."""
        self._locked = False
        self.identifier = identifier
        self._display_name = None
        self._user_data = None
        self._properties = None

    @property
    def identifier(self):
        """Get or set the text string for material identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'material identifier')

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
        if value is not None:
            try:
                value = str(value)
            except UnicodeEncodeError:  # Python 2 machine lacking the character set
                pass  # keep it as unicode
        self._display_name = value

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

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def _compare_thickness_conductivity(self):
        """Compare the thickness and conductivity to avoid CTF errors from EnergyPlus."""
        try:
            assert self._conductivity / self._thickness <= 200000, \
                'Material layer "{}" does not have sufficient thermal resistance.\n'\
                'Either increase the thickness or remove it from the ' \
                'construction.'.format(self.identifier)
        except ZeroDivisionError:
            raise ValueError(
                'Material layer "{}" cannot have zero thickness.'.format(self.identifier)
            )
        except AttributeError:
            pass  # conductivity or thickness has not yet been set

    def __copy__(self):
        new_obj = self.__class__(self.identifier)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Base Energy Material:\n{}'.format(self.display_name)


@lockable
class _EnergyMaterialOpaqueBase(_EnergyMaterialBase):
    """Base energy material for all opaque material types."""
    ROUGHTYPES = ('VeryRough', 'Rough', 'MediumRough',
                  'MediumSmooth', 'Smooth', 'VerySmooth')
    RADIANCEROUGHTYPES = {'VeryRough': 0.2, 'Rough': 0.2, 'MediumRough': 0.15,
                          'MediumSmooth': 0.1, 'Smooth': 0.05, 'VerySmooth': 0}
    __slots__ = ()

    @property
    def is_window_material(self):
        """Boolean to note whether the material can be used for window surfaces."""
        return False

    def __repr__(self):
        return 'Base Opaque Energy Material:\n{}'.format(self.display_name)


@lockable
class _EnergyMaterialWindowBase(_EnergyMaterialBase):
    """Base energy material for all window material types."""
    __slots__ = ()

    @property
    def is_window_material(self):
        """Boolean to note whether the material can be used for window surfaces."""
        return True

    @property
    def is_glazing_material(self):
        """Boolean to note whether the material is a glazing layer."""
        return False

    @property
    def is_gas_material(self):
        """Boolean to note whether the material is a gas gap layer."""
        return False

    @property
    def is_shade_material(self):
        """Boolean to note whether the material is a shade layer."""
        return False

    def __repr__(self):
        return 'Base Window Energy Material:\n{}'.format(self.display_name)
