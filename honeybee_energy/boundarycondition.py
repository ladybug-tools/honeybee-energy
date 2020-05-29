"""Extra Boundary Condition objects for Energy models.

Note to developers:
    See _extend_honeybee to see where these boundary conditions are added to
    honeybee.boundarycondition module.
"""
from honeybee.boundarycondition import _BoundaryCondition


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
