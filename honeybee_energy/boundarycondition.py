"""Extra Boundary Condition objects for Energy models.

Note to developers:
    See _extend_honeybee to see where these boundary conditions are added to
    honeybee.boundarycondition module.
"""
from honeybee.boundarycondition import _BoundaryCondition


class Adiabatic(_BoundaryCondition):
    __slots__ = ()
    pass
