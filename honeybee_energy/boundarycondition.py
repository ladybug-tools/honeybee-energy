"""Extra Boundary Condition objects for Energy models.

Note to developers:
    See _extend_honeybee to see where these boundary conditions are added to
    honeybee.boundarycondition module.
"""
from honeybee.boundarycondition import _BoundaryCondition
from honeybee.typing import float_in_range, float_positive
from honeybee.altnumber import autocalculate


class Adiabatic(_BoundaryCondition):
    __slots__ = ()

    @classmethod
    def from_dict(cls, data):
        """Initialize Adiabatic BoundaryCondition from a dictionary.

        Args:
            data: A dictionary representation of the boundary condition.
        """
        assert data['type'] == 'Adiabatic', 'Expected dictionary for Adiabatic ' \
            'boundary condition. Got {}.'.format(data['type'])
        return cls()


class OtherSideTemperature(_BoundaryCondition):
    """Custom temperature or heat transfer coefficient on the other side of a surface.

    Args:
        temperature: A temperature value in Celsius to note the temperature on the
            other side of the object. This input can also be an Autocalculate object
            to signify that the temperature is equal to the outdoor air
            temperature. (Default: autocalculate).
        heat_transfer_coefficient: A value in W/m2-K to indicate the combined
            convective/radiative film coefficient. If equal to 0, then the
            specified temperature above is equal to the exterior surface
            temperature. Otherwise, the temperature above is considered the
            outside air temperature and this coefficient is used to determine the
            difference between this outside air temperature and the exterior surface
            temperature. (Default: 0).
    """

    __slots__ = ('_temperature', '_heat_transfer_coefficient')

    def __init__(self, temperature=autocalculate, heat_transfer_coefficient=0):
        """Initialize OtherSideTemperature boundary condition."""
        if temperature == autocalculate:
            self._temperature = autocalculate
        else:
            self._temperature = float_in_range(
                temperature, input_name='other side temperature')
        self._heat_transfer_coefficient = float_positive(
            heat_transfer_coefficient, input_name='other side heat transfer coefficient')

    @classmethod
    def from_dict(cls, data):
        """Initialize OtherSideTemperature BoundaryCondition from a dictionary.

        Args:
            data: A dictionary representation of the boundary condition.
        """
        assert data['type'] == 'OtherSideTemperature', 'Expected dictionary for ' \
            'OtherSideTemperature boundary condition. Got {}.'.format(data['type'])
        temperature = autocalculate if 'temperature' not in data or \
            data['temperature'] == autocalculate.to_dict() else data['temperature']
        htc = 0 if 'heat_transfer_coefficient' not in data \
            else data['heat_transfer_coefficient']
        return cls(temperature, htc)

    @property
    def temperature(self):
        """Get a value in Celsius for temperature on the other side of the object.

        Autocalculate signifies that the outdoor air temperature is used.
        """
        return self._temperature

    @property
    def heat_transfer_coefficient(self):
        """Get a value in W/m2-K for the combined convective/radiative film coefficient.
        """
        return self._heat_transfer_coefficient

    def to_dict(self):
        """Get the boundary condition as a dictionary."""
        bc_dict = {'type': self.name}
        bc_dict['temperature'] = autocalculate.to_dict() if \
            self.temperature == autocalculate else self.temperature
        bc_dict['heat_transfer_coefficient'] = self.heat_transfer_coefficient
        return bc_dict

    def to_idf(self, identifier):
        """Get the boundary condition as an IDF string.

        Args:
            identifier: Text for unique identifier to be given to the boundary condition.
        """
        comments = (
            'name', 'heat transfer coefficient', 'temperature',
            'temperature factor', 'outdoor temperature factor')
        values = [identifier, self.heat_transfer_coefficient]
        if self.temperature == autocalculate:
            values.extend([0, 0, 1])
        else:
            values.extend([self.temperature, 1, 0])

        space_count = tuple((25 - len(str(n))) for n in values)
        spaces = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
        body_str = '\n '.join('{},{}!- {}'.format(val, spc, com) for val, spc, com in
                              zip(values[:-1], spaces[:-1], comments[:-1]))
        ep_str = 'SurfaceProperty:OtherSideCoefficients,\n {}'.format(body_str)
        end_str = '\n {};{}!- {}'.format(values[-1], spaces[-1], comments[-1]) \
            if comments[-1] != '' else '\n {};'.format(values[-1])
        return ''.join((ep_str, end_str))
