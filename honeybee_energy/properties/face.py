# coding=utf-8
"""Face Energy Properties."""
from ..construction.opaque import OpaqueConstruction
from ..construction.air import AirBoundaryConstruction
from ..lib.constructionsets import generic_construction_set

from honeybee.facetype import AirBoundary


class FaceEnergyProperties(object):
    """Energy Properties for Honeybee Face.

    Args:
        host: A honeybee_core Face object that hosts these properties.
        construction: An optional Honeybee OpaqueConstruction object for
            the face. If None, it will be set by the parent Room ConstructionSet
            or the the Honeybee default generic ConstructionSet.

    Properties:
        * host
        * construction
        * is_construction_set_on_object
    """

    __slots__ = ('_host', '_construction')

    def __init__(self, host, construction=None):
        """Initialize Face energy properties."""
        self._host = host
        self.construction = construction

    @property
    def host(self):
        """Get the Face object hosting these properties."""
        return self._host

    @property
    def construction(self):
        """Get or set Face Construction.

        If the Construction is not set on the face-level, then it will be assigned
        based on the ConstructionSet assigned to the parent Room.  If there is no
        parent Room or the parent Room's ConstructionSet has no construction for
        the Face type and boundary_condition, it will be assigned using the honeybee
        default generic construction set.
        """
        if self._construction:  # set by user
            return self._construction
        elif self._host.has_parent:  # set by parent room
            constr_set = self._host.parent.properties.energy.construction_set
            return constr_set.get_face_construction(
                self._host.type.name, self._host.boundary_condition.name)
        else:
            return generic_construction_set.get_face_construction(
                self._host.type.name, self._host.boundary_condition.name)

    @construction.setter
    def construction(self, value):
        if value is not None:
            if isinstance(self.host.type, AirBoundary):
                assert isinstance(value, AirBoundaryConstruction), 'Expected Air ' \
                    'Boundary Construction for face with AirBoundary type. ' \
                    'Got {}'.format(type(value))
            else:
                assert isinstance(value, OpaqueConstruction), \
                    'Expected Opaque Construction for face. Got {}'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def is_construction_set_on_object(self):
        """Boolean noting if construction is assigned on the level of this Face.

        This is opposed to having the construction assigned by a ConstructionSet.
        """
        return self._construction is not None

    def reset_to_default(self):
        """Reset a construction assigned at the level of this Face to the default.

        This means that the Face's construction will be assigned by a ConstructionSet.
        """
        self._construction = None

    @classmethod
    def from_dict(cls, data, host):
        """Create FaceEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of FaceEnergyProperties with the
                format below.
            host: A Face object that hosts these properties.

        .. code-block:: python

            {
            "type": 'FaceEnergyProperties',
            "construction": {
                "type": 'OpaqueConstruction',
                "identifier": str, # construction identifier
                "layers": [], # list of material identifiers (from outside to inside)
                "materials": []  # list of unique material objects
                }
            }
        """
        assert data['type'] == 'FaceEnergyProperties', \
            'Expected FaceEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction' in data and data['construction'] is not None:
            new_prop.construction = OpaqueConstruction.from_dict(data['construction'])
        return new_prop

    def apply_properties_from_dict(self, abridged_data, constructions):
        """Apply properties from a FaceEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A FaceEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            constructions: A dictionary of constructions with constructions identifiers
                as keys, which will be used to re-assign constructions.
        """
        if 'construction' in abridged_data and abridged_data['construction'] is not None:
            self.construction = constructions[abridged_data['construction']]

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'FaceEnergyProperties' if not \
            abridged else 'FaceEnergyPropertiesAbridged'
        if self._construction is not None:
            base['energy']['construction'] = \
                self._construction.identifier if abridged else \
                self._construction.to_dict()
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Face object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return FaceEnergyProperties(_host, self._construction)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Face Energy Properties:\n host: {}'.format(self.host.identifier)
