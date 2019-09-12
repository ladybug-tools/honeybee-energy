# coding=utf-8
"""Room Energy Properties."""
from ..programtype import ProgramType
from ..constructionset import ConstructionSet
from ..lib.constructionsets import generic_costruction_set
from ..lib.programtypes import plenum_program_type


class RoomEnergyProperties(object):
    """Energy Properties for Honeybee Room.

    Properties:
        * program_type
        * construction_set
        * hvac
        * people
        * lighting
        * electric_equipment
        * gas_equipment
        * infiltration
        * ventilation
        * setpoint
        * is_conditioned
    """

    __slots__ = ('_host', '_program_type', '_construction_set', '_hvac',
                 '_people', '_lighting', '_electric_equipment', '_gas_equipment',
                 '_infiltration', '_ventilation', '_setpoint')

    def __init__(self, host, program_type=None, construction_set=None, hvac=None):
        """Initialize Room energy properties.

        Args:
            host: A honeybee_core Room object that hosts these properties.
            program_type: A honeybee ProgramType object to specify all default
                schedules and loads for the Room. If None, the Room will have a Plenum
                program (with no loads or setpoints). Default: None.
            construction_set: A honeybee ConstructionSet object to specify all
                default constructions for the Faces of the Room. If None, the Room
                will use the honeybee default construction set, which is not
                representative of a particular building code or climate zone.
                Default: None.
            hvac: A honeybee HVAC object (such as an IdealAirSystem) that specifies
                how the Room is conditioned. If None, it will be assumed that the
                space is not conditioned. Default: None.
        """
        self._host = host
        self.program_type = program_type
        self.construction_set = construction_set
        self._hvac = hvac

        # set the Room's overriding properties to None by default
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None

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

    @classmethod
    def from_dict(cls, data, host):
        """Create RoomEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of RoomEnergyProperties.
            host: A Room object that hosts these properties.
        """
        assert data['type'] == 'RoomEnergyProperties', \
            'Expected RoomEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction_set' in data and data['construction_set'] is not None:
            new_prop.construction_set = \
                ConstructionSet.from_dict(data['construction_set'])
        # TODO: Add re-serializing of loads and program type once they are implemented
        return new_prop

    def apply_properties_from_dict(self, abridged_data, construction_sets):
        """Apply properties from a RoomEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A RoomEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            construction_sets: A dictionary of ConstructionSets with names of the sets
                as keys, which will be used to re-assign construction_sets.
        """
        if 'construction_set' in abridged_data and \
                abridged_data['construction_set'] is not None:
            self.construction_set = construction_sets[abridged_data['construction_set']]
        # TODO: Add re-assigning of loads and program type once they are implemented

    def to_dict(self, abridged=False):
        """Return Room energy properties as a dictionary.

        Args:
            abridged: Boolean for whether the full dictionary of the Room should
                be written (False) or just the name of the the individual
                properties (True). Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'RoomEnergyProperties' if not \
            abridged else 'RoomEnergyPropertiesAbridged'

        # write the ProgramType into the dictionary
        if self._program_type is not None:
            base['energy']['program_type'] = \
                self._program_type.name if abridged else self._program_type.to_dict()
        else:
            base['energy']['program_type'] = None

        # write the ConstructionSet into the dictionary
        if self._construction_set is not None:
            base['energy']['construction_set'] = \
                self._construction_set.name if abridged else \
                self._construction_set.to_dict()
        else:
            base['energy']['construction_set'] = None

        # write any room-specific overriding properties into the dictionary
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
        new_room = RoomEnergyProperties(_host, self._program_type,
                                        self._construction_set, None)
        new_room._people = self._people
        new_room._lighting = self._lighting
        new_room._electric_equipment = self._electric_equipment
        new_room._gas_equipment = self._gas_equipment
        new_room._infiltration = self._infiltration
        new_room._ventilation = self._ventilation
        new_room._setpoint = self._setpoint
        return new_room

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Room Energy Properties:\n host: {}'.format(self.host.name)
