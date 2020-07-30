# coding=utf-8
"""Base class for HVAC systems following a template from the OpenStudio standards gem."""
from __future__ import division

from ._base import _HVACSystem

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string

import os
import importlib


@lockable
class _TemplateSystem(_HVACSystem):
    """Base class for HVAC systems following a standards template.

    Args:
        identifier: Text string for system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        vintage: Text for the vintage of the template system. This will be used
            to set efficiencies for various pieces of equipment within the system.
            Choose from the following.

            * DOE Ref Pre-1980
            * DOE Ref 1980-2004
            * 90.1-2004
            * 90.1-2007
            * 90.1-2010
            * 90.1-2013

        equipment_type: Text for the specific type of the system and equipment.
            For example, 'VAV chiller with gas boiler reheat'.

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * is_single_room
        * schedules
    """
    __slots__ = ('_vintage', '_equipment_type')

    VINTAGES = ('DOE Ref Pre-1980', 'DOE Ref 1980-2004', '90.1-2004', '90.1-2007',
                '90.1-2010', '90.1-2013')
    EQUIPMENT_TYPES = ('Inferred',)

    def __init__(self, identifier, vintage='90.1-2013', equipment_type=None):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _HVACSystem.__init__(self, identifier, is_single_room=False)
        self.vintage = vintage
        self.equipment_type = equipment_type

    @property
    def vintage(self):
        """Get or set text to indicate the vintage of the template system.

        Choose from the following options:

        * DOE Ref Pre-1980
        * DOE Ref 1980-2004
        * 90.1-2004
        * 90.1-2007
        * 90.1-2010
        * 90.1-2013
        """
        return self._vintage

    @vintage.setter
    def vintage(self, value):
        clean_input = valid_ep_string(value).lower()
        for key in self.VINTAGES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'Template HVAC vintage "{}" is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.VINTAGES))
        self._vintage = value

    @property
    def equipment_type(self):
        """Get or set text for the system's equipment specification.

        For example, 'VAV chiller with gas boiler reheat'.
        """
        return self._equipment_type

    @equipment_type.setter
    def equipment_type(self, value):
        if value is not None:
            clean_input = valid_ep_string(value).lower()
            for key in self.EQUIPMENT_TYPES:
                if key.lower() == clean_input:
                    value = key
                    break
            else:
                raise ValueError(
                    'HVAC equipment_type "{}" is not supported for {}.\n'
                    'Choose from the following:\n{}'.format(
                        value, self.__class__.__name__, '\n'.join(self.EQUIPMENT_TYPES)))
            self._equipment_type = value
        else:
            self._equipment_type = self.EQUIPMENT_TYPES[0]

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A HVAC dictionary in following the format below.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "90.1-2013",  # text for the vintage of the template
            "equipment_type": ""  # text for the HVAC equipment type
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a HVAC object from an abridged dictionary.

        Args:
            data: An abridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Setpoint object.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "90.1-2013",  # text for the vintage of the template
            "equipment_type": ""  # text for the HVAC equipment type
            }
        """
        # this is the same as the from_dict method for as long as there are not schedules
        return cls.from_dict(data)

    def to_dict(self, abridged=False):
        """All air system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """
        base = {'type': self.__class__.__name__}
        base['identifier'] = self.identifier
        if self._display_name is not None:
            base['display_name'] = self.display_name
        base['vintage'] = self.vintage
        base['equipment_type'] = self.equipment_type
        return base

    def __copy__(self):
        new_obj = self.__class__(self.identifier, self.vintage, self.equipment_type)
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return '{}: {}\n type: {}\n vintage: {}'.format(
            self.__class__.__name__, self.identifier, self.equipment_type, self.vintage)


class _EnumerationBase(object):
    """Enumerates the systems that inherit from a given template class."""

    def __init__(self):
        pass  # this class is only intended to be used in child objects

    @property
    def types(self):
        """A tuple indicating the currently supported HVAC types."""
        return tuple(sorted(self._HVAC_TYPES.keys()))

    @property
    def equipment_types(self):
        """A tuple indicating the supported equipment types."""
        return tuple(sorted(self._EQUIPMENT_TYPES.keys()))

    @property
    def types_dict(self):
        """A dictionary containing pointers to the classes of each HVAC type.

        The keys of this dictionary are the names of the HVAC classes (eg. 'FCU').
        """
        return self._HVAC_TYPES

    @property
    def equipment_types_dict(self):
        """A dictionary containing pointers to the classes of each equipment type.

        The keys of this dictionary are the names of the HVAC systems as they
        appear in the OpenStudio standards gem and include the specific equipment
        in the system (eg. 'DOAS with fan coil chiller with boiler').
        """
        return self._EQUIPMENT_TYPES

    @staticmethod
    def _import_modules(root_dir, base_package):
        """Import all of the modules in the root_dir.

        Args:
            root_dir: The directory from which modules will be imported.
            base_package: Text for the start of the import statement
                (eg. 'honeybee_energy.hvac.heatcool').
        """
        exclude = ('__init__.py', '_base.py')
        modules = [mod for mod in os.listdir(root_dir)
                   if mod not in exclude]
        modules = [os.path.join(root_dir, mod) for mod in modules]
        importable = ['.{}'.format(os.path.basename(f)[:-3]) for f in modules
                      if os.path.isfile(f) and f.endswith('.py')]
        for mod in importable:
            importlib.import_module(mod, base_package)
