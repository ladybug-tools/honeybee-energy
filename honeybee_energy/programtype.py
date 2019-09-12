# coding=utf-8
from __future__ import division

from honeybee.typing import valid_ep_string


class ProgramType(object):
    """Program Type object possessing all schedules and loads defining a program.

    Properties:
        * name
        * people
        * lighting
        * electric_equipment
        * gas_equipment
        * infiltration
        * ventilation
        * setpoint
    """

    def __init__(self, name, people=None, lighting=None, electric_equipment=None,
                 gas_equipment=None, infiltration=None, ventilation=None, setpoint=None):
        """Initialize ProgramType.

        Args:
            name: Text string for ProgramType. Must be <= 100 characters.
                Can include spaces but special characters will be stripped out.
            people: A People object to describe the occupancy of the program. If None,
                no occupancy will be assumed for the program. Default: None.
            lighting: A Lighting object to describe the lighting usage of the program.
                If None, no lighting will be assumed for the program. Default: None.
            electric_equipment: An ElectricEquipment object to describe the usage
                of electric equipment within the program. If None, no electric equipment
                will be assumed for the program. Default: None.
            gas_equipment: A GasEquipment object to describe the usage of gas equipment
                within the program. If None, no gas equipment will be assumed for
                the program. Default: None.
            infiltration: An Infiltration object to describe the outdoor air leakage of
                the program. If None, no infiltration will be assumed for the program.
                Default: None.
            ventilation: A Ventilation object to describe the minimum outdoor air
                requirement of the program. If None, no ventilation requirement will
                be assumed for the program. Default: None
            setpoint: A Setpoint object to describe the temperature and humidity
                setpoints of the program.  If None, the ProgramType cannot be assigned
                to a Room that is conditioned. Default: None.
        """
        self.name = name
        self.people = people
        self.lighting = lighting
        self.electric_equipment = electric_equipment
        self.gas_equipment = gas_equipment
        self.infiltration = infiltration
        self.ventilation = ventilation
        self.setpoint = setpoint

    @property
    def name(self):
        """Get or set the text string for program type name."""
        return self._name

    @name.setter
    def name(self, name):
        self._name = valid_ep_string(name, 'program type name')

    def __repr__(self):
        return 'Program Type: {}'.format(self.name)
