# coding=utf-8
"""Shade Energy Properties."""
from honeybee.typing import float_in_range


class ShadeEnergyProperties(object):
    """Energy Properties for Honeybee Shade.

    Properties:
        diffuse_reflectance
        specular_reflectance
        transmittance
        transmittance_schedule
    """

    __slots__ = ('_host', '_diffuse_reflectance', '_specular_reflectance',
                 '_transmittance', '_transmittance_schedule')

    def __init__(self, host_shade, diffuse_reflectance=0.2,
                 specular_reflectance=0, transmittance=0,
                 transmittance_schedule=None):
        """Initialize Shade energy properties.

        Args:
            host_shade: A honeybee_core Shade object that hosts these properties.
            diffuse_reflectance: A float between 0 and 1 for the diffuse
                reflectance of the shade (in the absence of transmittance or
                a transmittance schedule). Default: 0.2.
            specular_reflectance: A float between 0 and 1 for the specular
                reflectance of the shade (in the absence of transmittance or
                a transmittance schedule). Default: 0.
            transmittance: A float between 0 and 1 for the transmittance of
                the shade. Note that this property is not set-able when a
                transmittance_schedule is assigned.
            transmittance_schedule: An optional schedule to replace the
                assigned transmittance, which will vary transmittance
                throughout the year.
        """
        self._host = host_shade
        self._diffuse_reflectance = float_in_range(
            diffuse_reflectance, 0, 1, 'shade diffuse reflectance')
        self.specular_reflectance = specular_reflectance

        self._transmittance_schedule = None
        self.transmittance = transmittance
        self.transmittance_schedule = transmittance_schedule

    @property
    def host(self):
        """Get the Shade object hosting these properties."""
        return self._host

    @property
    def diffuse_reflectance(self):
        """Get or set the diffuse reflectance of the shade."""
        return self._diffuse_reflectance

    @diffuse_reflectance.setter
    def diffuse_reflectance(self, value):
        self._diffuse_reflectance = float_in_range(
            value, 0, 1, 'shade diffuse reflectance')
        assert self._diffuse_reflectance + self._specular_reflectance <= 1, \
            'Sum of diffuse and specular reflectance is greater than 1. Got ' \
            '{}'.format(self._diffuse_reflectance + self._specular_reflectance)

    @property
    def specular_reflectance(self):
        """Get or set the specular reflectance of the shade."""
        return self._specular_reflectance

    @specular_reflectance.setter
    def specular_reflectance(self, value):
        self._specular_reflectance = float_in_range(
            value, 0, 1, 'shade specular reflectance')
        assert self._diffuse_reflectance + self._specular_reflectance <= 1, \
            'Sum of diffuse and specular reflectance is greater than 1. Got ' \
            '{}'.format(self._diffuse_reflectance + self._specular_reflectance)

    @property
    def transmittance(self):
        """Get or set the transmittance of the shade."""
        return self._transmittance

    @transmittance.setter
    def transmittance(self, value):
        assert self._transmittance_schedule is None, \
            'Shade transmittance cannot be be set while a transmittance ' \
            'schedule is assigned.'
        self._transmittance = float_in_range(value, 0, 1, 'shade transmittance')

    @property
    def transmittance_schedule(self):
        """Get or set the transmittance schedule of the shade."""
        return self._transmittance_schedule

    @transmittance_schedule.setter
    def transmittance_schedule(self, value):
        if value is not None:
            # TODO: Un-comment this check once schedules are implemented
            #assert isinstance(self.transmittance_schedule, _ScheduleBase), \
            #    'Expected schedule for shade transmittance schedule. ' \
            #    'Got {}.'.format(type(value))
            self._transmittance = 'Set by Schedule'
        self._transmittance_schedule = value

    def apply_properties_from_dict(self, abridged_data):
        """Apply properties from a ShadeEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A ShadeEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
        """
        if 'diffuse_reflectance' in abridged_data and \
                abridged_data['diffuse_reflectance'] is not None:
            self.diffuse_reflectance = abridged_data['diffuse_reflectance']

        if 'specular_reflectance' in abridged_data and \
                abridged_data['specular_reflectance'] is not None:
            self.specular_reflectance = abridged_data['specular_reflectance']

        if 'transmittance' in abridged_data and \
                abridged_data['transmittance'] is not None:
            self.transmittance = abridged_data['transmittance']

        # TODO: Un-comment this check once schedules are implemented
        #if 'transmittance_schedule' in abridged_data and \
        #        abridged_data['transmittance_schedule'] is not None:
        #    self.transmittance_schedule = \
        #        schedules[abridged_data['transmittance_schedule']]

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
        if self.diffuse_reflectance != 0.2:
            base['energy']['diffuse_reflectance'] = self.diffuse_reflectance
        if self.specular_reflectance != 0:
            base['energy']['specular_reflectance'] = self.specular_reflectance
        if self.transmittance_schedule is not None:
            base['energy']['transmittance_schedule'] = \
                self.transmittance_schedule.name if abridged else \
                self.transmittance_schedule.to_dict()
        elif self.transmittance != 0:
            base['energy']['transmittance'] = self.transmittance
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Shade object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        _transm = self.transmittance if self.transmittance != 'Set by Schedule' else 0.0
        return ShadeEnergyProperties(
            _host, self._diffuse_reflectance, self._specular_reflectance,
            _transm, self._transmittance_schedule)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Shade Energy Properties:\n Reflectance:{}'.format(
            self.diffuse_reflectance + self.specular_reflectance)
