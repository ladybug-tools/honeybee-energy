# coding=utf-8
"""Door Energy Properties."""
from ..construction.opaque import OpaqueConstruction
from ..construction.window import WindowConstruction
from ..lib.constructionsets import generic_construction_set


class DoorEnergyProperties(object):
    """Energy Properties for Honeybee Door.

    Args:
        host_door: A honeybee_core Door object that hosts these properties.
        construction: An optional Honeybee OpaqueConstruction or WindowConstruction
            object for the door. Note that the host Door must have the is_glass
            property set to True to assign a WindowConstruction. If None, it will
            be set by the parent Room ConstructionSet or the the Honeybee default
            generic ConstructionSet.

    Properties:
        * host
        * construction
        * is_construction_set_on_object
    """

    __slots__ = ('_host', '_construction')

    def __init__(self, host, construction=None):
        """Initialize Door energy properties."""
        self._host = host
        self.construction = construction

    @property
    def host(self):
        """Get the Door object hosting these properties."""
        return self._host

    @property
    def construction(self):
        """Get or set Door Construction.

        If the Construction is not set on the door-level, then it will be assigned
        based on the ConstructionSet assigned to the parent Room.  If there is no
        parent Room or the parent Room's ConstructionSet has no construction for
        this type of door, it will be assigned using the honeybee default
        generic construction set.
        """
        if self._construction:  # set by user
            return self._construction
        elif self._host.has_parent and self._host.parent.has_parent:  # set by room
            constr_set = self._host.parent.parent.properties.energy.construction_set
            return constr_set.get_door_construction(
                self._host.boundary_condition.name, self._host.is_glass,
                self._host.parent.type.name)
        elif self._host.has_parent:  # generic but influenced by parent face
            return generic_construction_set.get_door_construction(
                self._host.boundary_condition.name, self._host.is_glass,
                self._host.parent.type.name)
        else:
            return generic_construction_set.get_door_construction(
                self._host.boundary_condition.name, self._host.is_glass, 'Wall')

    @construction.setter
    def construction(self, value):
        if value is not None:
            if not self.host.is_glass:
                assert isinstance(value, OpaqueConstruction), 'Expected ' \
                    'OpaqueConstruction for door. Got {}'.format(type(value))
            else:
                assert isinstance(value, WindowConstruction), 'Expected ' \
                    'WindowConstruction for glass door. Got {}'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def is_construction_set_on_object(self):
        """Boolean noting if construction is assigned on the level of this Door.

        This is opposed to having the construction assigned by a ConstructionSet.
        """
        return self._construction is not None

    def reset_to_default(self):
        """Reset a construction assigned at the level of this Door to the default.

        This means that the Door's construction will be assigned by a ConstructionSet.
        """
        self._construction = None

    @classmethod
    def from_dict(cls, data, host):
        """Create DoorEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of DoorEnergyProperties in the
                format below.
            host: A Door object that hosts these properties.

        .. code-block:: python

            {
            "type": 'DoorEnergyProperties',
            "construction": {
                "type": 'OpaqueConstruction',
                "identifier": str,  # construction identifier
                "layers": [],  # list of material identifiers (from outside to inside)
                "materials": []  # list of unique material objects
                }
            }
        """
        assert data['type'] == 'DoorEnergyProperties', \
            'Expected DoorEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction' in data and data['construction'] is not None:
            if not host.is_glass:
                new_prop.construction = OpaqueConstruction.from_dict(
                    data['construction'])
            else:
                new_prop.construction = WindowConstruction.from_dict(
                    data['construction'])
        return new_prop

    def apply_properties_from_dict(self, abridged_data, constructions):
        """Apply properties from a DoorEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A DoorEnergyPropertiesAbridged dictionary (typically
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
        base['energy']['type'] = 'DoorEnergyProperties' if not \
            abridged else 'DoorEnergyPropertiesAbridged'
        if self._construction is not None:
            base['energy']['construction'] = \
                self._construction.identifier if abridged else \
                self._construction.to_dict()
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Door object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return DoorEnergyProperties(_host, self._construction)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Door Energy Properties:\n host: {}'.format(self.host.identifier)
