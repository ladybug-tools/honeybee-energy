# coding=utf-8
"""Global sizing parameters dictating scaling factors for all zone peak loads."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee.typing import float_positive


class SizingParameter(object):
    """Global sizing parameters dictating scaling factors for all zone peak loads.

    Properties:
        * heating_factor
        * cooling_factor
    """
    __slots__ = ('_heating_factor', '_cooling_factor')

    def __init__(self, heating_factor=1.25, cooling_factor=1.15):
        """Initialize SizingParameter.

        Args:
            heating_factor: A number that will get multiplied by the peak heating load
                for each zone in the model in order to size the heating system for
                the model. Must be greater than 0. Default: 1.25.
            cooling_factor: A number that will get multiplied by the peak cooling load
                for each zone in the model in order to size the cooling system for
                the model. Must be greater than 0. Default: 1.15.
        """
        self.heating_factor = heating_factor
        self.cooling_factor = cooling_factor

    @property
    def heating_factor(self):
        """Get or set a number that will get multiplied by the peak heating loads."""
        return self._heating_factor

    @heating_factor.setter
    def heating_factor(self, value):
        self._heating_factor = float_positive(value, 'sizing parameter heating factor')
        assert self._heating_factor != 0, 'SizingParameter heating factor cannot be 0.'

    @property
    def cooling_factor(self):
        """Get or set a number that will get multiplied by the peak cooling loads."""
        return self._cooling_factor

    @cooling_factor.setter
    def cooling_factor(self, value):
        self._cooling_factor = float_positive(value, 'sizing parameter cooling factor')
        assert self._cooling_factor != 0, 'SizingParameter cooling factor cannot be 0.'

    @classmethod
    def from_idf(cls, idf_string):
        """Create a SizingParameter object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                SizingParameters definition.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'SizingParameters,')

        # extract the properties from the string
        heating_factor = 1.25
        cooling_factor = 1.15
        try:
            heating_factor = ep_strs[0] if ep_strs[0] != '' else 1.25
            cooling_factor = ep_strs[1] if ep_strs[1] != '' else 1.15
        except IndexError:
            pass  # shorter SizingParameters definition

        # return the object and the zone name for the object
        return cls(heating_factor, cooling_factor)

    @classmethod
    def from_dict(cls, data):
        """Create a SizingParameter object from a dictionary.

        Args:
            data: A SizingParameter dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SizingParameter",
            "heating_factor": 1.25,
            "cooling_factor": 1.15
            }
        """
        assert data['type'] == 'SizingParameter', \
            'Expected SizingParameter dictionary. Got {}.'.format(data['type'])
        heating_factor = data['heating_factor'] if 'heating_factor' in data else 1.25
        cooling_factor = data['cooling_factor'] if 'cooling_factor' in data else 1.15
        return cls(heating_factor, cooling_factor)

    def to_idf(self):
        """Get an EnergyPlus string representation of the SizingParameters."""
        values = (self.heating_factor, self.cooling_factor)
        comments = ('heating factor', 'cooling factor')
        return generate_idf_string('SizingParameters', values, comments)

    def to_dict(self):
        """SizingParameter dictionary representation."""
        return {
            'type': 'SizingParameter',
            'heating_factor': self.heating_factor,
            'cooling_factor': self.cooling_factor
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SizingParameter(self.heating_factor, self.cooling_factor)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.heating_factor, self.cooling_factor)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SizingParameter) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()
