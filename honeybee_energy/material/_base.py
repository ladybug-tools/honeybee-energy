# coding=utf-8
"""Base energy material."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string

import re


@lockable
class _EnergyMaterialBase(object):
    """Base energy material.

    Properties:
        name
    """
    __slots__ = ('_name', '_locked')

    def __init__(self, name):
        """Initialize energy material base.

        Args:
            name: Text string for material name. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
        """
        self._locked = False
        self.name = name

    @property
    def name(self):
        """Get or set the text string for material name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'material name')

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    @staticmethod
    def _parse_ep_string(ep_string, expected_type=None):
        """Parse an EnergyPlus material string into a tuple of values.

        Args:
            ep_string: An IDF string for a single EnergyPlus object.
            expected_type: Text representing the expected start of the IDF object.
                (ie. WindowMaterial:Glazing). If None, no type check will be performed.
        """
        ep_string = ep_string.strip()
        if expected_type is not None:
            assert ep_string.startswith(expected_type), 'Expected EnergyPlus {} ' \
                'but received a differet object: {}'.format(expected_type, ep_string)
        ep_strings = ep_string.split(';')
        assert len(ep_strings) == 2, 'Received more than one object in ep_string.'
        ep_string = re.sub(r'!.*\n', '', ep_strings[0])
        ep_strs = [e_str.strip() for e_str in ep_string.split(',')]
        ep_strs.pop(0)  # remove the EnergyPlus object name
        return ep_strs

    @staticmethod
    def _generate_ep_string(object_type, values, comments=None):
        """Get an IDF string representation of an EnergyPlus object.

        Args:
            object_type: Text representing the expected start of the IDF object.
                (ie. WindowMaterial:Glazing).
            values: A list of values associated with the EnergyPlus object in the
                order that they are supposed to be written to IDF format.
            comments: A list of text comments with the same length as the values.
                If None, no comments will be written into the object.
        """
        if comments is not None:
            space_count = tuple((25 - len(str(n))) for n in values)
            spaces = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
            ep_str = object_type + ',\n ' + '\n '.join(
                '{},{}!- {}'.format(val, space, com) for val, space, com in
                zip(values[:-1], spaces[:-1], comments[:-1]))
            ep_str = ep_str + '\n {};{}!- {}'.format(
                values[-1], spaces[-1], comments[-1])
        else:
            ep_str = object_type + ',\n ' + '\n '.join(
                '{},'.format(val) for val in values[:-1])
            ep_str = ep_str + '\n {};'.format(values[-1])
        return ep_str

    def __copy__(self):
        return self.__class__(self.name)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Base Energy Material:\n{}'.format(self.name)


@lockable
class _EnergyMaterialOpaqueBase(_EnergyMaterialBase):
    """Base energy material for all opaque material types."""
    ROUGHTYPES = ('VeryRough', 'Rough', 'MediumRough',
                  'MediumSmooth', 'Smooth', 'VerySmooth')
    RADIANCEROUGHTYPES = {'VeryRough': 0.3, 'Rough': 0.2, 'MediumRough': 0.15,
                          'MediumSmooth': 0.1, 'Smooth': 0.05, 'VerySmooth': 0}
    __slots__ = ()

    @property
    def is_window_material(self):
        """Boolean to note whether the material can be used for window surfaces."""
        return False

    def __repr__(self):
        return 'Base Opaque Energy Material:\n{}'.format(self.name)


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
        return 'Base Window Energy Material:\n{}'.format(self.name)
