# coding=utf-8
"""Shade Energy Properties."""
from honeybee.typing import clean_rad_string
from honeybee.checkdup import is_equivalent

from ..construction.shade import ShadeConstruction
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..generator.pv import PVProperties

from ..lib.constructions import generic_context
from ..lib.constructionsets import generic_construction_set


class ShadeEnergyProperties(object):
    """Energy Properties for Honeybee Shade.

    Args:
        host: A honeybee_core Shade object that hosts these properties.
        construction: An optional ShadeConstruction object to set the reflectance
            and specularity of the Shade. The default is set by a ConstructionSet
            if the shade is the parent to an object. Otherwise, if it is an
            orphaned shade, the default is a completely diffuse construction
            with 0.2 visible and solar reflectance.
        transmittance_schedule: An optional schedule to set the transmittance
            of the shade, which can vary throughout the day or year. Default
            is None for a completely opaque object.
        pv_properties: An optional PVProperties object to specify photovoltaic
            behavior of the Shade. If None, the Shade will have no Photovoltaic
            properties. Note that the normal of the Shade is important in
            determining the performance of the shade as a PV geometry.

    Properties:
        * host
        * construction
        * transmittance_schedule
        * pv_properties
        * is_construction_set_on_object
    """

    __slots__ = ('_host', '_construction', '_transmittance_schedule', '_pv_properties')

    def __init__(self, host, construction=None, transmittance_schedule=None,
                 pv_properties=None):
        """Initialize Shade energy properties."""
        self._host = host
        self.construction = construction
        self.transmittance_schedule = transmittance_schedule
        self.pv_properties = pv_properties

    @property
    def host(self):
        """Get the Shade object hosting these properties."""
        return self._host

    @property
    def construction(self):
        """Get or set a ShadeConstruction for the shade.

        If the construction is not set on the shade-level, then it will be assigned
        based on the ConstructionSet assigned to the parent Room.  If the parent Room's
        ConstructionSet has no construction for the Shade type, it will be assigned
        using the honeybee default generic ConstructionSet. If there is no parent
        Room, it will be the generic context construction.
        """
        if self._construction:  # set by user
            return self._construction
        elif not self._host.has_parent:
            return generic_context if self._host.is_detached else \
                generic_construction_set.shade_construction
        else:
            c_set = self._parent_construction_set(self._host.parent)
            if c_set is None:
                c_set = generic_construction_set
        return c_set.shade_construction

    @construction.setter
    def construction(self, value):
        if value is not None:
            assert isinstance(value, ShadeConstruction), \
                'Expected ShadeConstruction. Got {}.'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._construction = value

    @property
    def transmittance_schedule(self):
        """Get or set the transmittance schedule of the shade."""
        return self._transmittance_schedule

    @transmittance_schedule.setter
    def transmittance_schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected schedule for shade transmittance schedule. ' \
                'Got {}.'.format(type(value))
            if value.schedule_type_limit is not None:
                assert value.schedule_type_limit.unit == 'fraction', 'Transmittance ' \
                    'schedule should be fractional [Dimensionless]. Got a schedule ' \
                    'of unit_type [{}].'.format(value.schedule_type_limit.unit_type)
            value.lock()  # lock editing in case schedule has multiple references
        self._transmittance_schedule = value

    @property
    def pv_properties(self):
        """Get or set a PVProperties object for photovoltaic behavior of the Shade."""
        return self._pv_properties

    @pv_properties.setter
    def pv_properties(self, value):
        if value is not None:
            assert isinstance(value, PVProperties), \
                'Expected PVProperties. Got {}.'.format(type(value))
            value.lock()  # lock editing in case construction has multiple references
        self._pv_properties = value

    @property
    def is_construction_set_on_object(self):
        """Boolean noting if construction is assigned on the level of this Shade.

        This is opposed to having the construction assigned by a ConstructionSet.
        """
        return self._construction is not None

    def reset_construction_to_set(self):
        """Reset the construction and transmittance schedule of this Shade to default.

        This means that the Shade's construction will be assigned by a ConstructionSet.
        """
        self._construction = None
        self._transmittance_schedule = None

    def radiance_modifier_solar(self):
        """Get a Radiance modifier that combines the construction and transmittance.

        Note that only the first value from the transmittance schedule will be used
        to create the Trans modifier and so this method is really only intended for
        cases of constant transmittance schedules. If there is no transmittance
        schedule, a plastic material will be returned.
        """
        return self._radiance_modifier(self.construction.solar_reflectance)

    def radiance_modifier_visible(self):
        """Get a Radiance modifier that combines the construction and transmittance.

        Note that only the first value from the transmittance schedule will be used
        to create the Trans modifier and so this method is really only intended for
        cases of constant transmittance schedules. If there is no transmittance
        schedule, a plastic material will be returned.
        """
        return self._radiance_modifier(self.construction.visible_reflectance)

    @classmethod
    def from_dict(cls, data, host):
        """Create ShadeEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of ShadeEnergyProperties with the
                format below.
            host: A Shade object that hosts these properties.

        .. code-block:: python

            {
            "type": 'ShadeEnergyProperties',
            "construction": {},  # A ShadeConstruction dictionary
            "transmittance_schedule": {},  # A transmittance schedule dictionary
            "pv_properties": {}  # A PVProperties dictionary
            }
        """
        assert data['type'] == 'ShadeEnergyProperties', \
            'Expected ShadeEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction' in data and data['construction'] is not None:
            new_prop.construction = ShadeConstruction.from_dict(data['construction'])
        if 'transmittance_schedule' in data and \
                data['transmittance_schedule'] is not None:
            sch_dict = data['transmittance_schedule']
            if sch_dict['type'] == 'ScheduleRuleset':
                new_prop.transmittance_schedule = \
                    ScheduleRuleset.from_dict(data['transmittance_schedule'])
            elif sch_dict['type'] == 'ScheduleFixedInterval':
                new_prop.transmittance_schedule = \
                    ScheduleFixedInterval.from_dict(data['transmittance_schedule'])
            else:
                raise ValueError(
                    'Expected non-abridged Schedule dictionary for Shade '
                    'transmittance_schedule. Got {}.'.format(sch_dict['type']))
        if 'pv_properties' in data and data['pv_properties'] is not None:
            new_prop.pv_properties = PVProperties.from_dict(data['pv_properties'])
        return new_prop

    def apply_properties_from_dict(self, abridged_data, constructions, schedules):
        """Apply properties from a ShadeEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A ShadeEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            constructions: A dictionary of constructions with constructions identifiers
                as keys, which will be used to re-assign constructions.
            schedules: A dictionary of schedules with schedule identifiers as keys,
                which will be used to re-assign schedules.
        """
        if 'construction' in abridged_data and abridged_data['construction'] is not None:
            try:
                self.construction = constructions[abridged_data['construction']]
            except KeyError:
                raise ValueError('Shade construction "{}" was not found in '
                                 'constructions.'.format(abridged_data['construction']))
        if 'transmittance_schedule' in abridged_data and \
                abridged_data['transmittance_schedule'] is not None:
            self.transmittance_schedule = \
                schedules[abridged_data['transmittance_schedule']]
        if 'pv_properties' in abridged_data and \
                abridged_data['pv_properties'] is not None:
            self.pv_properties = PVProperties.from_dict(abridged_data['pv_properties'])

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'ShadeEnergyProperties' if not \
            abridged else 'ShadeEnergyPropertiesAbridged'
        if self._construction is not None:
            base['energy']['construction'] = \
                self._construction.identifier if abridged else \
                self._construction.to_dict()
        if self.transmittance_schedule is not None:
            base['energy']['transmittance_schedule'] = \
                self.transmittance_schedule.identifier if abridged else \
                self.transmittance_schedule.to_dict()
        if self.pv_properties is not None:
            base['energy']['pv_properties'] = self.pv_properties.to_dict()
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Shade object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return ShadeEnergyProperties(
            _host, self._construction, self._transmittance_schedule, self._pv_properties)

    def is_equivalent(self, other):
        """Check to see if these energy properties are equivalent to another object.

        This will only be True if all properties match (except for the host) and
        will otherwise be False.
        """
        if not is_equivalent(self._construction, other._construction):
            return False
        if not is_equivalent(
                self._transmittance_schedule, other._transmittance_schedule):
            return False
        if not is_equivalent(self._pv_properties, other._pv_properties):
            return False
        return True

    def _radiance_modifier(self, ref):
        """Get a Radiance modifier that respects the transmittance schedule.

        Args:
            ref: The reflectance to be used in the modifier.
        """
        # check to be sure that the honeybee-radiance installed
        try:
            from honeybee_radiance.modifier.material import Trans
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'Shade radiance_modifier methods. {}'.format(e))

        # create the modifier from the properties
        if self.transmittance_schedule is None:
            return self.construction._to_radiance(ref)
        else:
            mod_id = '{}_mod'.format(clean_rad_string(self.host.identifier))
            if isinstance(self.transmittance_schedule, ScheduleRuleset):
                trans = self.transmittance_schedule.default_day_schedule.values[0]
            else:
                trans = self.transmittance_schedule.values[0]
            avg_ref = (1 - trans) * ref
            return Trans.from_average_properties(
                mod_id, average_reflectance=avg_ref, average_transmittance=trans,
                is_specular=self.construction.is_specular, is_diffusing=False)

    @staticmethod
    def _parent_construction_set(host_parent):
        """Recursively search through host parents to find a ConstructionSet."""
        if hasattr(host_parent.properties.energy, 'construction_set'):
            # we found the room with the construction set
            return host_parent.properties.energy.construction_set
        elif host_parent.has_parent:
            # we found an aperture or face that could have a room with a construction set
            return ShadeEnergyProperties._parent_construction_set(host_parent.parent)
        else:
            # there is no parent room
            return None

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Shade Energy Properties: [host: {}]'.format(self.host.display_name)
