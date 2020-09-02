# coding=utf-8
"""Definition of surface crack for multizone airflow."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive


@lockable
class AFNCrack(object):
    """Airflow leakage through surface due to cracks or porous surface material.

    Note that this whole class only has bearing on the simulation when the Model
    that the AFNCrack is a part of has its ventilation_simulation_control set for
    MultiZone air flow, thereby triggering the use of the AirflowNetwork.

    Args:
        flow_coefficient: A number in kg/s-m at 1 Pa per meter of
            crack length at the conditions defined in the ReferenceCrack condition;
            required to run an AirflowNetwork simulation. Some common values for this
            coefficient from the DesignBuilder Cracks template include the following:

            * 0.00001 - Tight low-leakage external wall
            * 0.001 - Tight, low-leakage internal wall
            * 0.0004 - Poor, high-leakage external wall
            * 0.019 - Poor, high-leakage internal wall

        flow_exponent: An optional dimensionless number between 0.5 and 1 used
            to calculate the crack mass flow rate; required to run an AirflowNetwork
            simulation. This value represents the leak geometry impact on airflow, with
            0.5 generally corresponding to turbulent orifice flow and 1 generally
            corresponding to laminar flow. The default of 0.65 is representative of many
            cases of wall and window leakage, used when the exponent cannot be measured.
            (Default: 0.65).

    Properties:
        * flow_coefficient
        * flow_exponent
    """
    __slots__ = ('_flow_coefficient', '_flow_exponent', '_locked')

    def __init__(self, flow_coefficient, flow_exponent=0.65):
        """Initialize AFNCrack."""
        self.flow_coefficient = flow_coefficient
        self.flow_exponent = flow_exponent

    @property
    def flow_coefficient(self):
        """Get or set the air mass flow coefficient defined at the reference crack."""
        return self._flow_coefficient

    @flow_coefficient.setter
    def flow_coefficient(self, value):
        self._flow_coefficient = float_positive(value, 'flow_coefficient')

    @property
    def flow_exponent(self):
        """Get or set the air mass flow exponent for the surface crack."""
        return self._flow_exponent

    @flow_exponent.setter
    def flow_exponent(self, value):
        self._flow_exponent = float_in_range(value, 0.5, 1.0, 'flow_exponent')

    @classmethod
    def from_dict(cls, data):
        """Create a AFNCrack object from a dictionary.

        Args:
            data: A AFNCrack dictionary following the format below.

        .. code-block:: python

            {
            "type": "AFNCrack",
            "flow_coefficient": 0.01 # coefficient at reference crack
            "flow_exponent": 0.65 # exponent for the surface crack
            }
        """
        assert data['type'] == 'AFNCrack', \
            'Expected AFNCrack dictionary. Got {}.'.format(data['type'])

        assert 'flow_coefficient' in data, 'The flow_coefficient must be defined to ' \
            'create a AFNCrack object.'

        air_coeff = data['flow_coefficient']
        air_exp = data['flow_exponent'] if 'flow_exponent' in data \
            and data['flow_exponent'] is not None else 0.65

        return cls(air_coeff, air_exp)

    def to_dict(self):
        """AFNCrack dictionary representation."""
        base = {'type': 'AFNCrack'}
        base['flow_coefficient'] = self.flow_coefficient
        base['flow_exponent'] = self.flow_exponent
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        return AFNCrack(
            self.flow_coefficient, self.flow_exponent)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.flow_coefficient, self.flow_exponent)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, AFNCrack) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'AFNCrack,\n flow_coefficient: {}\n ' \
            'flow_exponent: {}'.format(self.flow_coefficient, self.flow_exponent)
