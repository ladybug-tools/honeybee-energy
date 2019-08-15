# coding=utf-8
"""Base energy material."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


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
