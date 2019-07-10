# coding=utf-8
"""Model Energy Properties."""


class ModelEnergyProperties(object):
    """Energy Properties for Honeybee Model.

    Properties:
        materials
        constructions
        construction_sets
        schedules
        program_types
    """

    def __init__(self, host):
        """Initialize Model energy properties.

        Args:
            host: A honeybee_core Model object that hosts these properties.
        """
        self._host = host

    @property
    def host(self):
        """Get the Model object hosting these properties."""
        return self._host

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        abridged: Boolean to note whether the full dictionary describing the
            object should be returned (False) or just an abridged version (True).
            Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'ModelEnergyProperties' if not \
            abridged else 'ModelEnergyPropertiesAbridged'
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Model object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return ModelEnergyProperties(_host)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Model Energy Properties'
