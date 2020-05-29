# coding=utf-8
"""Settings for the EnergyPlus Shadow Calculation."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee.typing import valid_string, int_in_range


class ShadowCalculation(object):
    """Settings for the EnergyPlus Shadow Calculation.


    Args:
        solar_distribution: Text desribing how EnergyPlus should treat beam solar
            radiation and reflectances from surfaces that strike the building
            surfaces. (Default: FullExteriorWithReflections). Choose from the following:

            * MinimalShadowing
            * FullExterior
            * FullInteriorAndExterior
            * FullExteriorWithReflections
            * FullInteriorAndExteriorWithReflections

        calculation_method: Text noting whether CPU-based polygon clipping method or
            GPU-based pixel counting method should be used. For low numbers of shading
            surfaces (less than ~200), PolygonClipping requires less runtime than
            PixelCounting. However, PixelCounting runtime scales significantly
            better at higher numbers of shading surfaces. PixelCounting also has
            no limitations related to zone concavity when used with any
            “FullInterior” solar distribution options. (Default: PolygonClipping).
            Choose from the following:

            * PolygonClipping
            * PixelCounting

        calculation_update_method: Text describing how often the solar and shading
            calculations are updated with respect to the flow of time in the
            simulation. (Default: Periodic). Choose from the following:

            * Periodic
            * Timestep

        calculation_frequency: Integer for the number of days in each period for
            which a unique shadow calculation will be performed. This field is only
            used if the Periodic method is used in the previous field. (Default: 30).
        maximum_figures: Integer for the number of figures used in shadow overlaps.
            (Default: 15000).

    Properties:
        * solar_distribution
        * calculation_method
        * calculation_update_method
        * calculation_frequency
        * maximum_figures
    """
    __slots__ = (
        '_solar_distribution', '_calculation_method', '_calculation_update_method',
        '_calculation_frequency', '_maximum_figures')
    SOLAR_DISTRIBUTIONS = (
        'MinimalShadowing', 'FullExterior', 'FullInteriorAndExterior',
        'FullExteriorWithReflections', 'FullInteriorAndExteriorWithReflections')
    CALCULATION_METHODS = ('PolygonClipping', 'PixelCounting')
    CALCULATION_UPDATE_METHODS = ('Periodic', 'Timestep')

    def __init__(self, solar_distribution='FullExteriorWithReflections',
                 calculation_method='PolygonClipping',
                 calculation_update_method='Periodic',
                 calculation_frequency=30, maximum_figures=15000):
        """Initialize ShadowCalculation."""
        self.solar_distribution = solar_distribution
        self.calculation_method = calculation_method
        self.calculation_update_method = calculation_update_method
        self.calculation_frequency = calculation_frequency
        self.maximum_figures = maximum_figures

    @property
    def solar_distribution(self):
        """Get or set text for how solar reflectances from surfaces should be treated.

        Choose from the options below:

        * MinimalShadowing
        * FullExterior
        * FullInteriorAndExterior
        * FullExteriorWithReflections
        * FullInteriorAndExteriorWithReflections
        """
        return self._solar_distribution

    @solar_distribution.setter
    def solar_distribution(self, value):
        clean_input = valid_string(value).lower()
        for key in self.SOLAR_DISTRIBUTIONS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'solar_distribution {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.SOLAR_DISTRIBUTIONS))
        self._solar_distribution = value

    @property
    def calculation_method(self):
        """Get or set text for whether CPU-based or GPU-based methods should be used.

        Choose from the options below:

        * PolygonClipping
        * PixelCounting
        """
        return self._calculation_method

    @calculation_method.setter
    def calculation_method(self, value):
        clean_input = valid_string(value).lower()
        for key in self.CALCULATION_METHODS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'calculation_method "{}" is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.CALCULATION_METHODS))
        self._calculation_method = value

    @property
    def calculation_update_method(self):
        """Get or set text for how often the solar and shading calculations are updated.

        Choose from the options below:

        * Periodic
        * Timestep
        """
        return self._calculation_update_method

    @calculation_update_method.setter
    def calculation_update_method(self, value):
        clean_input = valid_string(value).lower()
        for key in self.CALCULATION_UPDATE_METHODS:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'calculation_update_method "{}" is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.CALCULATION_UPDATE_METHODS))
        self._calculation_update_method = value

    @property
    def calculation_frequency(self):
        """Get or set a integer for the number of days with unique shadow calculations."""
        return self._calculation_frequency

    @calculation_frequency.setter
    def calculation_frequency(self, value):
        self._calculation_frequency = int_in_range(
            value, 1, input_name='shadow calculation calculation frequency')

    @property
    def maximum_figures(self):
        """Get or set a integer for the number of figures used in shadow overlaps."""
        return self._maximum_figures

    @maximum_figures.setter
    def maximum_figures(self, value):
        self._maximum_figures = int_in_range(
            value, 200, input_name='shadow calculation maximum figures')

    @classmethod
    def from_idf(cls, idf_string, solar_distribution='FullExteriorWithReflections'):
        """Create a ShadowCalculation object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                ShadowCalculation definition.
            solar_distribution: Text desribing how EnergyPlus should treat beam solar
                radiation and reflectances from surfaces that strike the building surfaces.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'ShadowCalculation,')

        # extract the properties from the string
        calc_method = 'PolygonClipping'
        update_method = 'Periodic'
        calculation_frequency = 20
        maximum_figures = 15000
        try:
            calc_method = ep_strs[0] if ep_strs[0] != '' else update_method
            update_method = ep_strs[1] if ep_strs[1] != '' else update_method
            calculation_frequency = ep_strs[2] if ep_strs[2] != '' else 20
            maximum_figures = ep_strs[3] if ep_strs[3] != '' else 15000
        except IndexError:
            pass  # shorter ShadowCalculation definition

        return cls(solar_distribution, calc_method, update_method,
                   calculation_frequency, maximum_figures)

    @classmethod
    def from_dict(cls, data):
        """Create a ShadowCalculation object from a dictionary.

        Args:
            data: A ShadowCalculation dictionary in following the format below.

        .. code-block:: python

            {
            "type": "ShadowCalculation",
            "solar_distribution": 'FullInteriorAndExteriorWithReflections',
            "calculation_method": 'PolygonClipping',
            "calculation_update_method": 'Periodic',
            "calculation_frequency": 30,
            "maximum_figures": 15000
            }
        """
        assert data['type'] == 'ShadowCalculation', \
            'Expected ShadowCalculation dictionary. Got {}.'.format(data['type'])
        solar_distribution = data['solar_distribution'] if \
            'solar_distribution' in data else 'FullExteriorWithReflections'
        calculation_method = data['calculation_method'] if \
            'calculation_method' in data else 'PolygonClipping'
        update_method = data['calculation_update_method'] if \
            'calculation_update_method' in data else 'Periodic'
        calculation_frequency = data['calculation_frequency'] if \
            'calculation_frequency' in data else 30
        maximum_figures = data['maximum_figures'] if \
            'maximum_figures' in data else 15000
        return cls(solar_distribution, calculation_method, update_method,
                   calculation_frequency, maximum_figures)

    def to_idf(self):
        """Get an EnergyPlus string representation of the ShadowCalculation."""
        values = (self.calculation_method, self.calculation_update_method,
                  self.calculation_frequency, self.maximum_figures)
        comments = ('calculation method', 'calculation update method',
                    'calculation frequency', 'maximum figures')
        return generate_idf_string('ShadowCalculation', values, comments)

    def to_dict(self):
        """ShadowCalculation dictionary representation."""
        return {
            'type': 'ShadowCalculation',
            'solar_distribution': self.solar_distribution,
            'calculation_method': self.calculation_method,
            'calculation_update_method': self.calculation_update_method,
            'calculation_frequency': self.calculation_frequency,
            'maximum_figures': self.maximum_figures
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return ShadowCalculation(
            self.solar_distribution, self.calculation_method,
            self.calculation_update_method, self.calculation_frequency,
            self.maximum_figures)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.solar_distribution, self.calculation_method,
                self.calculation_update_method, self.calculation_frequency,
                self.maximum_figures)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ShadowCalculation) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()
