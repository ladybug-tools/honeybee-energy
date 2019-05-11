"""Energy Properties."""


class EnergyProperties(object):
    """Energy Properties for Honeybee geometry."""

    def __init__(self, srf_type):
        # set default construction based on srf_type
        self.construction = srf_type.energy_construction

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
    def to_dict(self):
        """Return energy properties as a dictionary."""
        return {
            'properties': {
                'energy': {
                    'construction': self.construction.to_dict
                }
            }
        }

    def __repr__(self):
        return 'EnergyProperties:%s' % self.construction.name
