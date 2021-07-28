# coding=utf-8
"""Aperture Energy Properties."""
from ..construction.dictutil import dict_to_construction
from ..construction.window import WindowConstruction
from ..construction.windowshade import WindowConstructionShade
from ..construction.dynamic import WindowConstructionDynamic
from ..ventcool.opening import VentilationOpening
from ..lib.constructionsets import generic_construction_set


class ApertureEnergyProperties(object):
    """Energy Properties for Honeybee Aperture.

    Args:
        host: A honeybee_core Aperture object that hosts these properties.
        construction: An optional Honeybee WindowConstruction, WindowConstructionShade
            or WindowConstructionDynamic object for the aperture. If None, it will
            be set by the parent Room ConstructionSet or the the Honeybee default
            generic ConstructionSet.
        vent_opening: An optional VentilationOpening to specify the operable
            portion of the Aperture. (Default: None).

    Properties:
        * host
        * construction
        * vent_opening
        * is_construction_set_on_object
    """

    __slots__ = ('_host', '_construction', '_vent_opening')

    def __init__(self, host, construction=None, vent_opening=None):
        """Initialize Aperture energy properties."""
        self._host = host
        self.construction = construction
        self.vent_opening = vent_opening

    @property
    def host(self):
        """Get the Aperture object hosting these properties."""
        return self._host

    @property
    def construction(self):
        """Get or set Aperture Construction.

        If the Construction is not set on the aperture-level, then it will be assigned
        based on the ConstructionSet assigned to the parent Room.  If there is no
        parent Room or the parent Room's ConstructionSet has no construction for
        the aperture, it will be assigned using the honeybee default generic
        construction set.
        """
        if self._construction:  # set by user
            return self._construction
        elif self._host.has_parent and self._host.parent.has_parent:  # set by zone
            constr_set = self._host.parent.parent.properties.energy.construction_set
            return constr_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable,
                self._host.parent.type.name)
        elif self._host.has_parent:  # generic but influenced by parent face
            return generic_construction_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable,
                self._host.parent.type.name)
        else:
            return generic_construction_set.get_aperture_construction(
                self._host.boundary_condition.name, self._host.is_operable, 'Wall')

    @construction.setter
    def construction(self, value):
        if value is not None:
            vw = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)
            assert isinstance(value, vw), 'Expected WindowConstruction, ' \
                'WindowConstructionShade or WindowConstructionDynamic for aperture.' \
                ' Got {}'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def vent_opening(self):
        """Get or set a VentilationOpening object to specify the operable portion."""
        return self._vent_opening

    @vent_opening.setter
    def vent_opening(self, value):
        if value is not None:
            assert isinstance(value, VentilationOpening), 'Expected VentilationOpening ' \
                'for Aperture vent_opening. Got {}'.format(type(value))
            assert self.host.is_operable, 'Aperture must have a "True" is_operable ' \
                'property in order to assign vent_opening energy properties.'
            if value._parent is None:
                value._parent = self.host
            elif value._parent.identifier != self.host.identifier:
                raise ValueError(
                    '{0} objects can be assigned to only one parent.\n{0} cannot be '
                    'assigned to Aperture "{1}" since it is already assigned to "{2}".\n'
                    'Try duplicating the object and then assign it.'.format(
                        'VentilationOpening', self.host.identifier,
                        value._parent.identifier))
        self._vent_opening = value

    @property
    def is_construction_set_on_object(self):
        """Boolean noting if construction is assigned on the level of this Aperture.

        This is opposed to having the construction assigned by a ConstructionSet.
        """
        return self._construction is not None

    def reset_to_default(self):
        """Reset a construction assigned at the level of this Aperture to the default.

        This means the Aperture's construction will be assigned by a ConstructionSet.
        """
        self._construction = None
        self._vent_opening = None

    @classmethod
    def from_dict(cls, data, host):
        """Create ApertureEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of ApertureEnergyProperties in the
                format below.
            host: A Aperture object that hosts these properties.

        .. code-block:: python

            {
            "type": 'ApertureEnergyProperties',
            "construction": {},  # Window Construction dictionary
            "vent_opening": {}  # VentilationOpening dict
            }
        """
        assert data['type'] == 'ApertureEnergyProperties', \
            'Expected ApertureEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction' in data and data['construction'] is not None:
            new_prop.construction = dict_to_construction(data['construction'])
        if 'vent_opening' in data and data['vent_opening'] is not None:
            new_prop.vent_opening = VentilationOpening.from_dict(data['vent_opening'])
        return new_prop

    def apply_properties_from_dict(self, abridged_data, constructions):
        """Apply properties from a ApertureEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A ApertureEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            constructions: A dictionary of constructions with constructions identifiers
                as keys, which will be used to re-assign constructions.
        """
        if 'construction' in abridged_data and abridged_data['construction'] is not None:
            try:
                self.construction = constructions[abridged_data['construction']]
            except KeyError:
                raise ValueError('Aperture construction "{}" was not found in '
                                 'constructions.'.format(abridged_data['construction']))
        if 'vent_opening' in abridged_data and abridged_data['vent_opening'] is not None:
            self.vent_opening = \
                VentilationOpening.from_dict(abridged_data['vent_opening'])

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'ApertureEnergyProperties' if not \
            abridged else 'ApertureEnergyPropertiesAbridged'
        if self._construction is not None:
            base['energy']['construction'] = \
                self._construction.identifier if abridged else self._construction.to_dict()
        if self._vent_opening is not None:
            base['energy']['vent_opening'] = self._vent_opening.to_dict()
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Aperture object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        vo = self._vent_opening.duplicate() if self._vent_opening is not None else None
        return ApertureEnergyProperties(_host, self._construction, vo)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Aperture Energy Properties: [host: {}]'.format(self.host.display_name)
