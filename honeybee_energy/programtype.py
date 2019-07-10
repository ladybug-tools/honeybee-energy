# coding=utf-8
from __future__ import division

from honeybee.typing import valid_ep_string


class ProgramType(object):
    """Energy Program Type.

    Properties:
        name
        people_load
        lighting_load
        electric_equipment_load
        gas_equipment_load
        infiltration_load
        ventilation_load
    """

    def __init__(self, name, people_load=None, lighting_load=None,
                 electric_equipment_load=None, gas_equipment_load=None,
                 infiltration_load=None, ventilation_load=None):
        """Initialize energy program type.

        Args:
            name: Text string for construction program type. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
        """
        self.name = name
        self.people_load = people_load
        self.lighting_load = lighting_load
        self.electric_equipment_load = electric_equipment_load
        self.gas_equipment_load = gas_equipment_load
        self.infiltration_load = infiltration_load
        self.ventilation_load = ventilation_load

    @property
    def name(self):
        """Get or set the text string for program type name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'program type name')

    def __repr__(self):
        return 'Program Type: {}'.format(self.name)
