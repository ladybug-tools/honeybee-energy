"""Energy Properties."""
from .boundarycondition import BoundaryConditions


class EnergyProperties(object):
    """Energy Properties for Honeybee geometry."""

    def __init__(self, srf_type):
        self.construction = srf_type.energy_construction
        self.boundary_condition = BoundaryConditions().outdoors

    @property
    def construction(self):
        """Set or get Face construction."""
        return self._construction

    @construction.setter
    def construction(self, value):
        self._construction = value
    
    @property
    def materials(self):
        """List of materials."""
        if not self._construction:
            return []
        return self._construction.materials

    @property
    def boundary_condition(self):
        """Get and set boundary condition."""
        return self._boundary_condition

    @boundary_condition.setter
    def boundary_condition(self, bc):
        self._boundary_condition = bc

    @property
    def to_dict(self):
        """Return energy properties as a dictionary."""
        base = {'energy': {}}
        base['energy'].update(self.boundary_condition.to_dict)
        base['energy']['construction'] = self.construction.to_dict
        return base

    def __repr__(self):
        return 'EnergyProperties:%s' % self.construction.name
