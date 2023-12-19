# coding=utf-8
"""Definitions for central parameters used in electric generator simulation."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive

from ..writer import generate_idf_string


@lockable
class ElectricLoadCenter(object):
    """Parameters used to specify the properties of the model's electric loads center.

    Args:
        inverter_efficiency: A number between 0 and 1 for the load centers's
            inverter nominal rated DC-to-AC conversion efficiency. An inverter
            converts DC power, such as that output by photovoltaic panels, to
            AC power, such as that distributed by the electrical grid and is available
            from standard electrical outlets. Inverter efficiency is defined
            as the inverter's rated AC power output divided by its rated DC power
            output. (Default: 0.96).
        inverter_dc_to_ac_size_ratio: A positive number (typically greater than 1) for
            the ratio of the inverter's DC rated size to its AC rated size. Typically,
            inverters are not sized to convert the full DC output under standard
            test conditions (STC) as such conditions rarely occur in reality and
            therefore unnecessarily add to the size/cost of the inverter. For a
            system with a high DC to AC size ratio, during times when the 
            DC power output exceeds the inverter's rated DC input size, the inverter
            limits the array's power output by increasing the DC operating voltage,
            which moves the arrays operating point down its current-voltage (I-V)
            curve. The default value of 1.1 is reasonable for most systems. A
            typical range is 1.1 to 1.25, although some large-scale systems have
            ratios of as high as 1.5. The optimal value depends on the system's
            location, array orientation, and module cost. (Default: 1.1).

    Properties:
        * inverter_efficiency
        * inverter_dc_to_ac_size_ratio
    """
    __slots__ = ('_inverter_efficiency', '_inverter_dc_to_ac_size_ratio', '_locked')

    def __init__(self, inverter_efficiency=0.96, inverter_dc_to_ac_size_ratio=1.1):
        """Initialize ElectricLoadCenter."""
        self.inverter_efficiency = inverter_efficiency
        self.inverter_dc_to_ac_size_ratio = inverter_dc_to_ac_size_ratio
        # TODO: Add properties for battery storage to this object

    @property
    def inverter_efficiency(self):
        """Get or set a number for the nominal rated efficiency of the inverter."""
        return self._inverter_efficiency

    @inverter_efficiency.setter
    def inverter_efficiency(self, value):
        self._inverter_efficiency = float_in_range(
            value, 0.0, 1.0, 'inverter rated efficiency')
    
    @property
    def inverter_dc_to_ac_size_ratio(self):
        """Get or set a number for the nominal rated efficiency of the inverter."""
        return self._inverter_dc_to_ac_size_ratio

    @inverter_dc_to_ac_size_ratio.setter
    def inverter_dc_to_ac_size_ratio(self, value):
        self._inverter_dc_to_ac_size_ratio = float_positive(
            value, 'inverter DC to AC size ratio')

    @classmethod
    def from_dict(cls, data):
        """Create a ElectricLoadCenter object from a dictionary.

        Args:
            data: A ElectricLoadCenter dictionary following the format below.

        .. code-block:: python

            {
            "type": "ElectricLoadCenter"
            "inverter_efficiency": 0.95, # rated inverter efficiency
            "inverter_dc_to_ac_size_ratio": 1.2 # ratio between inverter DC and AC size
            }
        """
        assert data['type'] == 'ElectricLoadCenter', 'Expected ' \
            'ElectricLoadCenter dictionary. Got {}.'.format(data['type'])

        eff = data['inverter_efficiency'] if 'inverter_efficiency' in data \
            and data['inverter_efficiency'] is not None else 0.96
        dc_to_ac = data['inverter_dc_to_ac_size_ratio'] \
            if 'inverter_dc_to_ac_size_ratio' in data \
            and data['inverter_dc_to_ac_size_ratio'] is not None else 1.1
        return cls(eff, dc_to_ac)

    def to_dict(self):
        """ElectricLoadCenter dictionary representation."""
        base = {'type': 'ElectricLoadCenter'}
        base['inverter_efficiency'] = self.inverter_efficiency
        base['inverter_dc_to_ac_size_ratio'] = self.inverter_dc_to_ac_size_ratio
        return base

    def to_idf(self, generator_objects):
        """IDF string representation of the electric loads center.

        Note that this method only outputs the ElectricLoadCenter:Generators list,
        the ElectricLoadCenter:Inverter object and the ElectricLoadCenter:Distribution
        specification. However, to write the full set of generation objects into
        an IDF, the individual generators must also be written.

        Args:
            generator_objects: A list of honeybee objects representing electrical
                generators that are included in the system. For example, this can be
                a list of Shade objects with PVProperties assigned to them.

        Returns:
            A tuple with three elements

            -   generators: Text string representation of the ElectricLoadCenter:
                Generators list.

            -   inverter: Text string representation of the ElectricLoadCenter:
                Inverter list.
            
            -   distribution: Text string representation of the ElectricLoadCenter:
                Distribution specification.
        """
        # create the ElectricLoadCenter:Generators list
        generators_vals = ['Model Load Center Generators']
        generators_comments = ['name']
        for i, g_obj in enumerate(generator_objects):
            g_id = '{}..{}'.format(
                g_obj.properties.energy.pv_properties.identifier, g_obj.identifier)
            generators_vals.append(g_id)
            generators_comments.append('generator {} name'.format(i + 1))
            generators_vals.append('Generator:PVWatts')
            generators_comments.append('generator {} object type'.format(i + 1))
            generators_vals.extend(('', '', ''))
            generators_comments.extend(
                ('power output', 'availability', 'thermal to electric'))
        generators = generate_idf_string(
            'ElectricLoadCenter:Generators', generators_vals, generators_comments)
        # create the ElectricLoadCenter:Inverter object
        inverter_values = (
            'Photovoltaic Inverter', self.inverter_dc_to_ac_size_ratio,
            self.inverter_efficiency)
        inverter_comments = (
            'inverter name', 'DC to AC size ratio', 'inverter efficiency')
        inverter = generate_idf_string(
            'ElectricLoadCenter:Inverter:PVWatts', inverter_values, inverter_comments)
        # create the ElectricLoadCenter:Distribution specification
        values = ('Model Load Center Distribution', 'Model Load Center Generators',
                  'Baseload', '', '', '', 'DirectCurrentWithInverter',
                  'Photovoltaic Inverter')
        comments = (
            'distribution name', 'generator list name', 'generator operation type',
            'purchased electric demand limit', 'track schedule', 'track meter',
            'electrical buss type', 'inverter name')
        distribution = generate_idf_string(
            'ElectricLoadCenter:Distribution', values, comments)
        return generators, inverter, distribution

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        return ElectricLoadCenter(
            self.inverter_efficiency, self.inverter_dc_to_ac_size_ratio)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.inverter_efficiency, self.inverter_dc_to_ac_size_ratio)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ElectricLoadCenter) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'ElectricLoadCenter: [inverter efficiency: {}]'.format(
            self.inverter_efficiency)
