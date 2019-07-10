# coding=utf-8
"""Room Energy Properties."""
from ..programtype import ProgramType
from ..constructionset import ConstructionSet
from ..lib.default.room import generic_costruction_set, plenum_program_type


class RoomEnergyProperties(object):
    """Energy Properties for Honeybee Room.

    Properties:
        program_type
        construction_set
        people
        lighting
        electric_equipment
        gas_equipment
        infiltration
        ventilation
    """

    __slots__ = ('_host', '_program_type', '_construction_set',
                 '_people', '_lighting', '_electric_equipment',
                 '_gas_equipment', '_infiltration', '_ventilation')

    def __init__(self, host, program_type=None, construction_set=None,
                 people=None, lighting=None, electric_equipment=None,
                 gas_equipment=None, infiltration=None, ventilation=None):
        """Initialize Room energy properties.

        Args:
            host: A honeybee_core Room object that hosts these properties.
            program_type: A honeybee ProgramType object to specify all default
                schedules and loads for the Room.
            construction_set: A honeybee ConstructionSet object to specify all
                default constructions for the Faces of the Room.
            people
            lighting
            electric_equipment
            gas_equipment
            infiltration
            ventilation
        """
        self._host = host
        self.program_type = program_type
        self.construction_set = construction_set
        self._people = people
        self._lighting = lighting
        self._electric_equipment = electric_equipment
        self._gas_equipment = gas_equipment
        self._infiltration = infiltration
        self._ventilation = ventilation

    @property
    def host(self):
        """Get the Room object hosting these properties."""
        return self._host

    @property
    def program_type(self):
        """Get or set the ProgramType object for the Room.

        If not set, it will default to a plenum ProgramType (with no loads assigned).
        """
        if self._program_type is not None:  # set by the user
            return self._program_type
        else:
            return plenum_program_type

    @program_type.setter
    def program_type(self, value):
        if value is not None:
            assert isinstance(value, ProgramType), \
                'Expected ProgramType. Got {}'.format(type(value))
        self._program_type = value

    @property
    def construction_set(self):
        """Get or set the Room ConstructionSet object.

        If not set, it will be the Honeybee default generic ConstructionSet.
        """
        if self._construction_set is not None:  # set by the user
            return self._construction_set
        else:
            return generic_costruction_set

    @construction_set.setter
    def construction_set(self, value):
        if value is not None:
            assert isinstance(value, ConstructionSet), \
                'Expected ConstructionSet. Got {}'.format(type(value))
            value.lock()   # lock editing in case constructionset has multiple references
        self._construction_set = value

    def to_dict(self, abridged=False):
        """Return energy properties as a dictionary.

        Args:
            abridged: Boolean for whether the full dictionary of the Room should
                be written (False) or just the name of the the individual
                properties (True). Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'RoomEnergyProperties' if not \
            abridged else 'RoomEnergyPropertiesAbridged'
        if self._program_type is not None:
            base['energy']['program_type'] = \
                self._program_type.name if abridged else self._program_type.to_dict()
        else:
            base['energy']['program_type'] = None
        if self._construction_set is not None:
            base['energy']['construction_set'] = \
                self._construction_set.name if abridged else \
                self._construction_set.to_dict()
        else:
            base['energy']['construction_set'] = None
        base['energy']['people'] = self._people.to_dict(abridged) if \
            self._people is not None else None
        base['energy']['lighting'] = self._lighting.to_dict(abridged) if \
            self._lighting is not None else None
        base['energy']['electric_equipment'] = \
            self._electric_equipment.to_dict(abridged) if \
            self._electric_equipment is not None else None
        base['energy']['gas_equipment'] = self._gas_equipment.to_dict(abridged) if \
            self._gas_equipment is not None else None
        base['energy']['infiltration'] = self._infiltration.to_dict(abridged) if \
            self._infiltration is not None else None
        base['energy']['ventilation'] = self._ventilation.to_dict(abridged) if \
            self._ventilation is not None else None
        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        new_host: A new Room object that hosts these properties.
            If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return RoomEnergyProperties(
            _host, self._program_type, self._construction_set,
            self._people, self._lighting, self._electric_equipment,
            self._gas_equipment, self._infiltration, self._ventilation)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Room Energy Properties:\n Program Type:{}\n Construction Set:' \
            '{}'.format(self.program_type.name, self.construction_set.name)
