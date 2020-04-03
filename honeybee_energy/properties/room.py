# coding=utf-8
"""Room Energy Properties."""
# import the main types of assignable objects
from ..programtype import ProgramType
from ..constructionset import ConstructionSet
from ..load.people import People
from ..load.lighting import Lighting
from ..load.equipment import ElectricEquipment, GasEquipment
from ..load.infiltration import Infiltration
from ..load.ventilation import Ventilation
from ..load.setpoint import Setpoint

# import all hvac modules to ensure they are all re-serializable in Room.from_dict
from ..hvac import HVAC_TYPES_DICT
from ..hvac._base import _HVACSystem
from ..hvac.idealair import IdealAirSystem

# import the libraries of constructionsets and programs
from ..lib.constructionsets import generic_construction_set
from ..lib.programtypes import plenum_program


class RoomEnergyProperties(object):
    """Energy Properties for Honeybee Room.

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
            Room is not conditioned. Default: None.

    Properties:
        * host
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
        """Initialize Room energy properties."""
        # set the main properties of the Room
        self._host = host
        self.program_type = program_type
        self.construction_set = construction_set
        self.hvac = hvac

        # set the Room's specific properties that override the program_type to None
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
            return plenum_program

    @program_type.setter
    def program_type(self, value):
        if value is not None:
            assert isinstance(value, ProgramType), \
                'Expected ProgramType for Room program_type. Got {}'.format(type(value))
            value.lock()   # lock in case program type has multiple references
        self._program_type = value

    @property
    def construction_set(self):
        """Get or set the Room ConstructionSet object.

        If not set, it will be the Honeybee default generic ConstructionSet.
        """
        if self._construction_set is not None:  # set by the user
            return self._construction_set
        else:
            return generic_construction_set

    @construction_set.setter
    def construction_set(self, value):
        if value is not None:
            assert isinstance(value, ConstructionSet), \
                'Expected ConstructionSet. Got {}'.format(type(value))
            value.lock()   # lock in case construction set has multiple references
        self._construction_set = value

    @property
    def hvac(self):
        """Get or set the HVAC object for the Room.

        If None, it will be assumed that the Room is not conditioned.
        """
        return self._hvac

    @hvac.setter
    def hvac(self, value):
        if value is not None:
            assert isinstance(value, _HVACSystem), \
                'Expected HVACSystem for Room hvac. Got {}'.format(type(value))
            if value.is_single_room:
                if value._parent is None:
                    value._parent = self.host
                elif value._parent.identifier != self.host.identifier:
                    raise ValueError(
                        '{0} objects can be assigned to a only one Room.\n'
                        '{0} "{1}" cannot be assigned to Room "{2}" since it is '
                        'already assigned to "{3}".\nTry duplicating the {0}, '
                        'and then assigning it to this Room.'.format(
                            value.__class__.__name__, value.identifier,
                            self.host.identifier, value._parent.identifier))
            value.lock()   # lock in case hvac has multiple references
        self._hvac = value

    @property
    def people(self):
        """Get or set a People object to describe the occupancy of the Room."""
        if self._people is not None:  # set by the user
            return self._people
        else:
            return self.program_type.people

    @people.setter
    def people(self, value):
        if value is not None:
            assert isinstance(value, People), \
                'Expected People for Room people. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._people = value

    @property
    def lighting(self):
        """Get or set a Lighting object to describe the lighting usage of the Room."""
        if self._lighting is not None:  # set by the user
            return self._lighting
        else:
            return self.program_type.lighting

    @lighting.setter
    def lighting(self, value):
        if value is not None:
            assert isinstance(value, Lighting), \
                'Expected Lighting for Room lighting. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._lighting = value

    @property
    def electric_equipment(self):
        """Get or set an ElectricEquipment object to describe the equipment usage."""
        if self._electric_equipment is not None:  # set by the user
            return self._electric_equipment
        else:
            return self.program_type.electric_equipment

    @electric_equipment.setter
    def electric_equipment(self, value):
        if value is not None:
            assert isinstance(value, ElectricEquipment), 'Expected ElectricEquipment ' \
                'for Room electric_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._electric_equipment = value

    @property
    def gas_equipment(self):
        """Get or set a GasEquipment object to describe the equipment usage."""
        if self._gas_equipment is not None:  # set by the user
            return self._gas_equipment
        else:
            return self.program_type.gas_equipment

    @gas_equipment.setter
    def gas_equipment(self, value):
        if value is not None:
            assert isinstance(value, GasEquipment), 'Expected GasEquipment ' \
                'for Room gas_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._gas_equipment = value

    @property
    def infiltration(self):
        """Get or set a Infiltration object to to describe the outdoor air leakage."""
        if self._infiltration is not None:  # set by the user
            return self._infiltration
        else:
            return self.program_type.infiltration

    @infiltration.setter
    def infiltration(self, value):
        if value is not None:
            assert isinstance(value, Infiltration), 'Expected Infiltration ' \
                'for Room infiltration. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._infiltration = value

    @property
    def ventilation(self):
        """Get or set a Ventilation object for the minimum outdoor air requirement."""
        if self._ventilation is not None:  # set by the user
            return self._ventilation
        else:
            return self.program_type.ventilation

    @ventilation.setter
    def ventilation(self, value):
        if value is not None:
            assert isinstance(value, Ventilation), 'Expected Ventilation ' \
                'for Room ventilation. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._ventilation = value

    @property
    def setpoint(self):
        """Get or set a Setpoint object for the temperature setpoints of the Room."""
        if self._setpoint is not None:  # set by the user
            return self._setpoint
        else:
            return self.program_type.setpoint

    @setpoint.setter
    def setpoint(self, value):
        if value is not None:
            assert isinstance(value, Setpoint), 'Expected Setpoint ' \
                'for Room setpoint. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._setpoint = value

    @property
    def is_conditioned(self):
        """Boolean to note whether the Room is conditioned."""
        return self._hvac is not None

    def add_default_ideal_air(self):
        """Add a default IdealAirSystem to this Room.

        The identifier of this system will be derived from the room identifier.
        """
        self.hvac = IdealAirSystem('{}_IdealAir'.format(self.host.identifier))

    def add_prefix(self, prefix):
        """Change the identifier attributes unique to this object by adding a prefix.

        Notably, this method only adds the prefix to extension attributes that must
        be unique to the Room (eg. single-room HVAC systems) and does not add the
        prefix to attributes that are shared across several Rooms (eg. ConstructionSets).

        Args:
            prefix: Text that will be inserted at the start of extension
                attribute identifiers.
        """
        if self._hvac is not None and self._hvac.is_single_room:
            new_hvac = self._hvac.duplicate()
            new_hvac.identifier = '{}_{}'.format(prefix, self._hvac.identifier)
            self.hvac = new_hvac

    def reset_to_default(self):
        """Reset all of the properties assigned at the level of this Room to the default.
        """
        self._program_type = None
        self._construction_set = None
        self._hvac = None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None

    @classmethod
    def from_dict(cls, data, host):
        """Create RoomEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of RoomEnergyProperties with the
                format below.
            host: A Room object that hosts these properties.

        .. code-block:: python

            {
            "type": 'RoomEnergyProperties',
            "construction_set": {},  # A ConstructionSet dictionary
            "program_type": {},  # A ProgramType dictionary
            "hvac": {}, # A HVACSystem dictionary
            "people":{},  # A People dictionary
            "lighting": {},  # A Lighting dictionary
            "electric_equipment": {},  # A ElectricEquipment dictionary
            "gas_equipment": {},  # A GasEquipment dictionary
            "infiltration": {},  # A Infiltration dictionary
            "ventilation": {},  # A Ventilation dictionary
            "setpoint": {}  # A Setpoint dictionary
            }
        """
        assert data['type'] == 'RoomEnergyProperties', \
            'Expected RoomEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction_set' in data and data['construction_set'] is not None:
            new_prop.construction_set = \
                ConstructionSet.from_dict(data['construction_set'])
        if 'program_type' in data and data['program_type'] is not None:
            new_prop.program_type = ProgramType.from_dict(data['program_type'])
        if 'hvac' in data and data['hvac'] is not None:
            hvac_class = HVAC_TYPES_DICT[data['hvac']['type']]
            new_prop.hvac = hvac_class.from_dict(data['hvac'])

        if 'people' in data and data['people'] is not None:
            new_prop.people = People.from_dict(data['people'])
        if 'lighting' in data and data['lighting'] is not None:
            new_prop.lighting = Lighting.from_dict(data['lighting'])
        if 'electric_equipment' in data and data['electric_equipment'] is not None:
            new_prop.electric_equipment = \
                ElectricEquipment.from_dict(data['electric_equipment'])
        if 'gas_equipment' in data and data['gas_equipment'] is not None:
            new_prop.gas_equipment = GasEquipment.from_dict(data['gas_equipment'])
        if 'infiltration' in data and data['infiltration'] is not None:
            new_prop.infiltration = Infiltration.from_dict(data['infiltration'])
        if 'ventilation' in data and data['ventilation'] is not None:
            new_prop.ventilation = Ventilation.from_dict(data['ventilation'])
        if 'setpoint' in data and data['setpoint'] is not None:
            new_prop.setpoint = Setpoint.from_dict(data['setpoint'])

        return new_prop

    def apply_properties_from_dict(self, abridged_data, construction_sets,
                                   program_types, hvacs, schedules):
        """Apply properties from a RoomEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A RoomEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            construction_sets: A dictionary of ConstructionSets with identifiers
                of the sets as keys, which will be used to re-assign construction_sets.
            program_types: A dictionary of ProgramTypes with identifiers of the types as
                keys, which will be used to re-assign program_types.
            hvacs: A dictionary of HVACSystems with the identifiers of the systems as
                keys, which will be used to re-assign hvac to the Room.
            schedules: A dictionary of Schedules with identifiers of the schedules ask
                keys, which will be used to re-assign schedules.
        """
        if 'construction_set' in abridged_data and \
                abridged_data['construction_set'] is not None:
            self.construction_set = construction_sets[abridged_data['construction_set']]
        if 'program_type' in abridged_data and abridged_data['program_type'] is not None:
            self.program_type = program_types[abridged_data['program_type']]
        if 'hvac' in abridged_data and abridged_data['hvac'] is not None:
            self.hvac = hvacs[abridged_data['hvac']]

        if 'people' in abridged_data and abridged_data['people'] is not None:
            self.people = People.from_dict_abridged(
                abridged_data['people'], schedules)
        if 'lighting' in abridged_data and abridged_data['lighting'] is not None:
            self.lighting = Lighting.from_dict_abridged(
                abridged_data['lighting'], schedules)
        if 'electric_equipment' in abridged_data and \
                abridged_data['electric_equipment'] is not None:
            self.electric_equipment = ElectricEquipment.from_dict_abridged(
                abridged_data['electric_equipment'], schedules)
        if 'gas_equipment' in abridged_data and \
                abridged_data['gas_equipment'] is not None:
            self.gas_equipment = GasEquipment.from_dict_abridged(
                abridged_data['gas_equipment'], schedules)
        if 'infiltration' in abridged_data and abridged_data['infiltration'] is not None:
            self.infiltration = Infiltration.from_dict_abridged(
                abridged_data['infiltration'], schedules)
        if 'ventilation' in abridged_data and abridged_data['ventilation'] is not None:
            self.ventilation = Ventilation.from_dict_abridged(
                abridged_data['ventilation'], schedules)
        if 'setpoint' in abridged_data and abridged_data['setpoint'] is not None:
            self.setpoint = Setpoint.from_dict_abridged(
                abridged_data['setpoint'], schedules)

    def to_dict(self, abridged=False):
        """Return Room energy properties as a dictionary.

        Args:
            abridged: Boolean for whether the full dictionary of the Room should
                be written (False) or just the identifier of the the individual
                properties (True). Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'RoomEnergyProperties' if not \
            abridged else 'RoomEnergyPropertiesAbridged'

        # write the ProgramType into the dictionary
        if self._program_type is not None:
            base['energy']['program_type'] = \
                self._program_type.identifier if abridged else \
                self._program_type.to_dict()

        # write the ConstructionSet into the dictionary
        if self._construction_set is not None:
            base['energy']['construction_set'] = \
                self._construction_set.identifier if abridged else \
                self._construction_set.to_dict()

        # write the hvac into the dictionary
        if self._hvac is not None:
            base['energy']['hvac'] = \
                self._hvac.identifier if abridged else self._hvac.to_dict()

        # write any room-specific overriding properties into the dictionary
        if self._people is not None:
            base['energy']['people'] = self._people.to_dict(abridged)
        if self._lighting is not None:
            base['energy']['lighting'] = self._lighting.to_dict(abridged)
        if self._electric_equipment is not None:
            base['energy']['electric_equipment'] = \
                self._electric_equipment.to_dict(abridged)
        if self._gas_equipment is not None:
            base['energy']['gas_equipment'] = self._gas_equipment.to_dict(abridged)
        if self._infiltration is not None:
            base['energy']['infiltration'] = self._infiltration.to_dict(abridged)
        if self._ventilation is not None:
            base['energy']['ventilation'] = self._ventilation.to_dict(abridged)
        if self._setpoint is not None:
            base['energy']['setpoint'] = self._setpoint.to_dict(abridged)

        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Room object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        new_room = RoomEnergyProperties(
            _host, self._program_type, self._construction_set, self._hvac)
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
        return 'Room Energy Properties:\n host: {}'.format(self.host.identifier)
