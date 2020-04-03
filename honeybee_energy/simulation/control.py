# coding=utf-8
"""Simulation controls for which types of calculations to run."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string


class SimulationControl(object):
    """Simulation controls for which types of calculations to run.

    Args:
        do_zone_sizing: Boolean for whether the zone sizing calculation
            should be run. Default: True.
        do_system_sizing: Boolean for whether the system sizing calculation
            should be run. Default: True.
        do_plant_sizing: Boolean for whether the plant sizing calculation
            should be run. Default: True.
        run_for_sizing_periods: Boolean for whether the simulation should
            be run for the sizing periods. Default: False.
        run_for_run_periods: Boolean for whether the simulation should
            be run for the run periods. Default: True.

    Properties:
        * do_zone_sizing
        * do_system_sizing
        * do_plant_sizing
        * run_for_sizing_periods
        * run_for_run_periods
    """
    __slots__ = ('_do_zone_sizing', '_do_system_sizing', '_do_plant_sizing',
                 '_run_for_sizing_periods', '_run_for_run_periods')

    def __init__(self, do_zone_sizing=True, do_system_sizing=True,
                 do_plant_sizing=True, run_for_sizing_periods=False,
                 run_for_run_periods=True):
        """Initialize SimulationControl."""
        self.do_zone_sizing = do_zone_sizing
        self.do_system_sizing = do_system_sizing
        self.do_plant_sizing = do_plant_sizing
        self.run_for_sizing_periods = run_for_sizing_periods
        self.run_for_run_periods = run_for_run_periods

    @property
    def do_zone_sizing(self):
        """Get or set a boolean for whether the zone sizing calculation is run."""
        return self._do_zone_sizing

    @do_zone_sizing.setter
    def do_zone_sizing(self, value):
        self._do_zone_sizing = bool(value)

    @property
    def do_system_sizing(self):
        """Get or set a boolean for whether the system sizing calculation is run."""
        return self._do_system_sizing

    @do_system_sizing.setter
    def do_system_sizing(self, value):
        self._do_system_sizing = bool(value)

    @property
    def do_plant_sizing(self):
        """Get or set a boolean for whether the plant sizing calculation is run."""
        return self._do_plant_sizing

    @do_plant_sizing.setter
    def do_plant_sizing(self, value):
        self._do_plant_sizing = bool(value)

    @property
    def run_for_sizing_periods(self):
        """Get or set a boolean for whether the simulation is run for sizing periods."""
        return self._run_for_sizing_periods

    @run_for_sizing_periods.setter
    def run_for_sizing_periods(self, value):
        self._run_for_sizing_periods = bool(value)

    @property
    def run_for_run_periods(self):
        """Get or set a boolean for whether the simulation is run for run periods."""
        return self._run_for_run_periods

    @run_for_run_periods.setter
    def run_for_run_periods(self, value):
        self._run_for_run_periods = bool(value)

    @classmethod
    def from_idf(cls, idf_string):
        """Create a SimulationControl object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                SimulationControl definition.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'SimulationControl,')

        # extract the properties from the string
        do_zone_sizing = False
        do_system_sizing = False
        do_plant_sizing = False
        run_for_sizing_periods = True
        run_for_run_periods = True
        try:
            do_zone_sizing = True if ep_strs[0].lower() == 'yes' else False
            do_system_sizing = True if ep_strs[1].lower() == 'yes' else False
            do_plant_sizing = True if ep_strs[2].lower() == 'yes' else False
            run_for_sizing_periods = False if ep_strs[3].lower() == 'no' else True
            run_for_run_periods = False if ep_strs[4].lower() == 'no' else True
        except IndexError:
            pass  # shorter SimulationControl definition

        return cls(do_zone_sizing, do_system_sizing, do_plant_sizing,
                   run_for_sizing_periods, run_for_run_periods)

    @classmethod
    def from_dict(cls, data):
        """Create a SimulationControl object from a dictionary.

        Args:
            data: A SimulationControl dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SimulationControl",
            "do_zone_sizing": True,
            "do_system_sizing": True,
            "do_plant_sizing": True,
            "run_for_sizing_periods": False,
            "run_for_run_periods": True
            }
        """
        assert data['type'] == 'SimulationControl', \
            'Expected SimulationControl dictionary. Got {}.'.format(data['type'])
        do_zone_sizing = data['do_zone_sizing'] if \
            'do_zone_sizing' in data else True
        do_system_sizing = data['do_system_sizing'] if \
            'do_system_sizing' in data else True
        do_plant_sizing = data['do_plant_sizing'] if \
            'do_plant_sizing' in data else True
        run_for_sizing_periods = data['run_for_sizing_periods'] if \
            'run_for_sizing_periods' in data else False
        run_for_run_periods = data['run_for_run_periods'] if \
            'run_for_run_periods' in data else False
        return cls(do_zone_sizing, do_system_sizing, do_plant_sizing,
                   run_for_sizing_periods, run_for_run_periods)

    def to_idf(self):
        """Get an EnergyPlus string representation of the SimulationControl."""
        do_zone_sizing = 'Yes' if self.do_zone_sizing else 'No'
        do_system_sizing = 'Yes' if self.do_system_sizing else 'No'
        do_plant_sizing = 'Yes' if self.do_plant_sizing else 'No'
        run_for_sizing_periods = 'Yes' if self.run_for_sizing_periods else 'No'
        run_for_run_periods = 'Yes' if self.run_for_run_periods else 'No'
        values = (do_zone_sizing, do_system_sizing, do_plant_sizing,
                  run_for_sizing_periods, run_for_run_periods)
        comments = ('do zone sizing', 'do system sizing', 'do plant sizing',
                    'run for sizing periods', 'run for run periods')
        return generate_idf_string('SimulationControl', values, comments)

    def to_dict(self):
        """SimulationControl dictionary representation."""
        return {
            'type': 'SimulationControl',
            'do_zone_sizing': self.do_zone_sizing,
            'do_system_sizing': self.do_system_sizing,
            'do_plant_sizing': self.do_plant_sizing,
            'run_for_sizing_periods': self.run_for_sizing_periods,
            'run_for_run_periods': self.run_for_run_periods
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SimulationControl(
            self.do_zone_sizing, self.do_system_sizing,
            self.do_plant_sizing, self.run_for_sizing_periods,
            self.run_for_run_periods)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.do_zone_sizing, self.do_system_sizing, self.do_plant_sizing,
                self.run_for_sizing_periods, self.run_for_run_periods)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SimulationControl) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()
