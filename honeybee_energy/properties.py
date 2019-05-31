"""Energy Properties."""
from .construction import Construction


class EnergyProperties(object):
    """Energy Properties for Honeybee geometry."""

    __slots__ = ('_face_type', '_boundary_condition',
                 '_construction', '_constructionset')

    def __init__(self, face_type, boundary_condition, construction=None):
        # private properties to set construction from construction-set.
        self._face_type = face_type
        self._boundary_condition = boundary_condition
        # construction set by user
        self.construction = construction
        # Constructionset can only be be set from the parent zone
        self._constructionset = None

    @property
    def construction(self):
        """Set or get Face construction.

        If construction is not set by user then it will be assigned based on parent zone
        construction-set when the face is added to a zone. For a free floating face the
        construction will be None unless it is set by user.
        """
        if self._construction:
            # set by user
            return self._construction
        elif self._constructionset:
            # set by parent zone
            return self._constructionset(self._face_type, self._boundary_condition)
        else:
            return None

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

    def to_dict(self):
        """Return energy properties as a dictionary."""
        base = {'energy': {}}
        construction = self.construction
        base['energy']['construction'] = construction.to_dict(
        ) if construction else None
        base['energy']['construction_set'] = \
            self._constructionset.name if self._constructionset else None
        return base

    def __repr__(self):
        return 'EnergyProperties:%s' % self.construction.name if self.construction else ''
