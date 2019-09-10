# coding=utf-8
from __future__ import division

from honeybee.typing import valid_ep_string


class ProgramType(object):
    """Program Type object possessing all schedules and loads defining a program.

    Properties:
        name
        people
        lighting
        electric_equipment
        gas_equipment
        infiltration
        ventilation
        cooling_setpoint_schedule
        heating_setpoint_schedule
    """

    def __init__(self, name, people=None, lighting=None, electric_equipment=None,
                 gas_equipment=None, infiltration=None, ventilation=None,
                 cooling_setpoint_schedule=None, heating_setpoint_schedule=None):
        """Initialize energy program type.

        Args:
            name: Text string for construction program type. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
        """
        self.name = name
        self.people = people
        self.lighting = lighting
        self.electric_equipment = electric_equipment
        self.gas_equipment = gas_equipment
        self.infiltration = infiltration
        self.ventilation = ventilation
        self.heating_setpoint_schedule = heating_setpoint_schedule
        self.heating_setpoint_schedule = heating_setpoint_schedule

    @property
    def name(self):
        """Get or set the text string for program type name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'program type name')

    def __repr__(self):
        return 'Program Type: {}'.format(self.name)
