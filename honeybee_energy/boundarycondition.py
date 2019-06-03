"""Extra Boundary Condition for Energy models.

Note to developers:
    See _extend_honeybee to see how to add these boundary conditions to
    honeybee.boundarycondition module.
"""
from honeybee.boundarycondition import _BoundaryCondition, Surface


class Adiabatic(_BoundaryCondition):
    __slots__ = ()
    pass
