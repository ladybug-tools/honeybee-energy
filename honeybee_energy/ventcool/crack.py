# coding=utf-8
"""Definition of surface crack for multizone airflow."""
from __future__ import division

from honeybee._lockable import lockable


@lockable
class AFNCrack(object):
    """Definition of surface crack for multizone airflow.

    Args:
        air_mass_flow_coefficient_reference: A number in kg/s-m at 1 Pa per meter of
            crack length at the conditions defined in the ReferenceCrack condition;
            required to run an AirflowNetwork simulation. Some common values for this
            coefficient from the DesignBuilder Cracks template include the following:

                * 0.00001 - Tight low-leakage external wall
                * 0.001 - Tight, low-leakage internal wall
                * 0.0004 - Poor, high-leakage external wall
                * 0.019 - Poor, high-leakage internal wall

        air_mass_flow_exponent: An optional dimensionless number between 0.5 and 1 used
            to calculate the crack mass flow rate; required to run an AirflowNetwork
            simulation. This value represents the leak geometry impact on airflow, with
            0.5 generally corresponding to turbulent orifice flow and 1 generally
            corresponding to laminar flow. The default of 0.65 is representative of many
            cases of wall and window leakage, used when the exponent cannot be measured.
            (Default: 0.65).
        crack_factor: A number indicating multiplier for air mass flow through a crack.
            (Default: 1).

    Properties:
        * air_mass_flow_coefficient_reference
        * air_mass_flow_exponent
        * crack_factor
        * parent
        * has_parent
    """
    __slots__ = ('_air_mass_flow_coefficient_reference', '_air_mass_flow_exponent',
                 '_crack_factor', '_parent', '_locked')

    def __init__(self, air_mass_flow_coefficient_reference, air_mass_flow_exponent=0.65,
                 crack_factor=1):
        """Initialize AFNCrack."""
        self.air_mass_flow_coefficient_reference = air_mass_flow_coefficient_reference
        self.air_mass_flow_exponent = air_mass_flow_exponent
        self.crack_factor = crack_factor
        self._parent = None  # this will be set when assigned to an aperture

    @property
    def air_mass_flow_coefficient_reference(self):
        """Get or set the air mass flow coefficient defined at the reference crack."""
        return self._air_mass_flow_coefficient_reference

    @air_mass_flow_coefficient_reference.setter
    def air_mass_flow_coefficient_reference(self, value):
        assert value > 0, 'The air_mass_flow_coefficient_reference must be greater ' \
            'than 0. Got: {}.'.format(value)
        self._air_mass_flow_coefficient_reference = value

    @property
    def air_mass_flow_exponent(self):
        """Get or set the air mass flow exponent for the surface crack."""
        return self._air_mass_flow_exponent

    @air_mass_flow_exponent.setter
    def air_mass_flow_exponent(self, value):
        assert 1 >= value >= 0.5, 'The air_mass_flow_exponent must be greater ' \
            'than or equal to 0.5 and less than or equal to 1. Got: {}.'.format(value)
        self._air_mass_flow_exponent = value

    @property
    def crack_factor(self):
        """Get or set the multiplier for air mass flow through a crack."""
        return self._crack_factor

    @crack_factor.setter
    def crack_factor(self, value):
        assert 0 < value <= 1, 'The crack_factor must be greater ' \
            'than 0 and less than or equal to 1. Got: {}.'.format(value)
        self._crack_factor = value

    @property
    def parent(self):
        """Get the parent of this object if it exists."""
        return self._parent

    @property
    def has_parent(self):
        """Get a boolean noting whether this AFNCrack has a parent object."""
        return self._parent is not None

    @classmethod
    def from_dict(cls, data):
        """Create a AFNCrack object from a dictionary.

        Args:
            data: A AFNCrack dictionary following the format below.

        .. code-block:: python

            {
            "type": "AFNCrack",
            "air_mass_flow_coefficient_reference": 0.01 # coefficient at reference crack
            "air_mass_flow_exponent": 0.65 # exponent for the surface crack
            "crack_factor" 0.5 # multiplier for air mass flow through a crack
            }
        """
        assert data['type'] == 'AFNCrack', \
            'Expected AFNCrack dictionary. Got {}.'.format(data['type'])

        assert 'air_mass_flow_coefficient_reference' in data, 'The ' \
            'air_mass_flow_coefficient_reference must be defined to create a ' \
            'AFNCrack object.'

        air_coeff = data['air_mass_flow_coefficient_reference']
        air_exp = data['air_mass_flow_exponent'] if 'air_mass_flow_exponent' in data \
            and data['air_mass_flow_exponent'] is not None else 0.65
        crack_fac = data['crack_factor'] if 'crack_factor' in data \
            and data['crack_factor'] is not None else 1

        return cls(air_coeff, air_exp, crack_fac)

    def to_dict(self):
        """AFNCrack dictionary representation."""
        base = {'type': 'AFNCrack'}
        base['air_mass_flow_coefficient_reference'] = \
            self.air_mass_flow_coefficient_reference
        base['air_mass_flow_exponent'] = self.air_mass_flow_exponent
        base['crack_factor'] = self.crack_factor
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def __copy__(self):
        return AFNCrack(
            self.air_mass_flow_coefficient_reference, self.air_mass_flow_exponent,
            self.crack_factor)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.air_mass_flow_coefficient_reference, self.air_mass_flow_exponent,
                self.crack_factor)

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
        return 'AFNCrack,\n air_mass_flow_coefficient_reference: {}\n ' \
            'air_mass_flow_exponent: {}\n crack_factor: {}'.format(
                self.air_mass_flow_coefficient_reference, self.air_mass_flow_exponent,
                self.crack_factor)