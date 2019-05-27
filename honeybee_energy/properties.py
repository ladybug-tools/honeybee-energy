"""Energy Properties."""
from .boundarycondition import boundary_conditions
from .construction import Construction
from .lib.constructionset import generic as generic_constructionset


class EnergyProperties(object):
    """Energy Properties for Honeybee geometry."""

    def __init__(self, face_type):
        self.face_type = face_type
        self.boundary_condition = boundary_conditions.outdoors
        # this will be set by user
        self._construction = None
        # this will be set by parent zone
        self._constructionset = None

    @property
    def construction(self):
        """Set or get Face construction.

        If construction is not set by user then it will be assigned based on parent zone
        construction-set when the face is added to a zone. For a free floating face the
        construction will be set to a generic construction based on face type and face
        boundary condition.
        """
        if self._construction:
            # set by user
            return self._construction
        elif self._constructionset:
            # set by parent zone
            return self._constructionset(self.face_type, self.boundary_condition)
        else:
            # not set yet - use generic construction set
            return generic_constructionset(self.face_type, self.boundary_condition)

    @construction.setter
    def construction(self, value):
        if value:
            assert isinstance(value, Construction), \
                'Expected Construction not {}'.format(type(value))
        self._construction = value

    @property
    def is_construction_set_by_user(self):
        """Check if construction is set by user."""
        return self._construction is not None

    @property
    def is_construction_set_by_zone(self):
        """Check if construction is set by user."""
        return not self.is_construction_set_by_user \
            and self._constructionset is not None

    @property
    def materials(self):
        """List of materials."""
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
