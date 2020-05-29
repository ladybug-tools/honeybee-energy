# coding=utf-8
"""Complete definition of a zone program, including schedules and loads."""
from __future__ import division

from .load.people import People
from .load.lighting import Lighting
from .load.equipment import ElectricEquipment, GasEquipment
from .load.infiltration import Infiltration
from .load.ventilation import Ventilation
from .load.setpoint import Setpoint

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, tuple_with_length


@lockable
class ProgramType(object):
    """Program Type object possessing all schedules and loads defining a program.

    Args:
        identifier: Text string for a unique ProgramType ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        people: A People object to describe the occupancy of the program. If None,
            no occupancy will be assumed for the program. Default: None.
        lighting: A Lighting object to describe the lighting usage of the program.
            If None, no lighting will be assumed for the program. Default: None.
        electric_equipment: An ElectricEquipment object to describe the usage
            of electric equipment within the program. If None, no electric equipment
            will be assumed for the program. Default: None.
        gas_equipment: A GasEquipment object to describe the usage of gas equipment
            within the program. If None, no gas equipment will be assumed for
            the program. Default: None.
        infiltration: An Infiltration object to describe the outdoor air leakage of
            the program. If None, no infiltration will be assumed for the program.
            Default: None.
        ventilation: A Ventilation object to describe the minimum outdoor air
            requirement of the program. If None, no ventilation requirement will
            be assumed for the program. Default: None
        setpoint: A Setpoint object to describe the temperature and humidity
            setpoints of the program.  If None, the ProgramType cannot be assigned
            to a Room that is conditioned. Default: None.

    Properties:
        * identifier
        * display_name
        * people
        * lighting
        * electric_equipment
        * gas_equipment
        * infiltration
        * ventilation
        * setpoint
        * schedules
        * schedules_unique
    """
    __slots__ = ('_identifier', '_display_name', '_people', '_lighting',
                 '_electric_equipment', '_gas_equipment', '_infiltration',
                 '_ventilation', '_setpoint', '_locked')

    def __init__(self, identifier, people=None, lighting=None, electric_equipment=None,
                 gas_equipment=None, infiltration=None, ventilation=None, setpoint=None):
        """Initialize ProgramType"""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.people = people
        self.lighting = lighting
        self.electric_equipment = electric_equipment
        self.gas_equipment = gas_equipment
        self.infiltration = infiltration
        self.ventilation = ventilation
        self.setpoint = setpoint

    @property
    def identifier(self):
        """Get or set the text string for a unique program type identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'program type identifier')

    @property
    def display_name(self):
        """Get or set a string for the object name without any character restrictions.

        If not set, this will be equal to the identifier.
        """
        if self._display_name is None:
            return self._identifier
        return self._display_name

    @display_name.setter
    def display_name(self, value):
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

    @property
    def people(self):
        """Get or set a People object to describe the occupancy of the program."""
        return self._people

    @people.setter
    def people(self, value):
        if value is not None:
            assert isinstance(value, People), 'Expected People object for ' \
                'ProgramType.people. Got {}.'.format(type(value))
        self._people = value

    @property
    def lighting(self):
        """Get or set a Lighting object to describe the lighting usage of the program."""
        return self._lighting

    @lighting.setter
    def lighting(self, value):
        if value is not None:
            assert isinstance(value, Lighting), 'Expected Lighting object for ' \
                'ProgramType.lighting. Got {}.'.format(type(value))
        self._lighting = value

    @property
    def electric_equipment(self):
        """Get or set an ElectricEquipment object to describe the usage of equipment."""
        return self._electric_equipment

    @electric_equipment.setter
    def electric_equipment(self, value):
        if value is not None:
            assert isinstance(value, ElectricEquipment), 'Expected ElectricEquipment ' \
                'object for ProgramType.electric_equipment. Got {}.'.format(type(value))
        self._electric_equipment = value

    @property
    def gas_equipment(self):
        """Get or set a GasEquipment object to describe the usage of equipment."""
        return self._gas_equipment

    @gas_equipment.setter
    def gas_equipment(self, value):
        if value is not None:
            assert isinstance(value, GasEquipment), 'Expected GasEquipment ' \
                'object for ProgramType.gas_equipment. Got {}.'.format(type(value))
        self._gas_equipment = value

    @property
    def infiltration(self):
        """Get or set an Infiltration object to describe the outdoor air leakage."""
        return self._infiltration

    @infiltration.setter
    def infiltration(self, value):
        if value is not None:
            assert isinstance(value, Infiltration), 'Expected Infiltration ' \
                'object for ProgramType.infiltration. Got {}.'.format(type(value))
        self._infiltration = value

    @property
    def ventilation(self):
        """Get or set a Ventilation object to describe the minimum outdoor air flow."""
        return self._ventilation

    @ventilation.setter
    def ventilation(self, value):
        if value is not None:
            assert isinstance(value, Ventilation), 'Expected Ventilation ' \
                'object for ProgramType.ventilation. Got {}.'.format(type(value))
        self._ventilation = value

    @property
    def setpoint(self):
        """Get or set a Setpoint object to describe the temperature setpoints."""
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value):
        if value is not None:
            assert isinstance(value, Setpoint), 'Expected Setpoint ' \
                'object for ProgramType.setpoint. Got {}.'.format(type(value))
        self._setpoint = value

    @property
    def schedules(self):
        """List of all schedules contained within the ProgramType."""
        sched = []
        if self.people is not None:
            sched.append(self.people.occupancy_schedule)
            sched.append(self.people.activity_schedule)
        if self.lighting is not None:
            sched.append(self.lighting.schedule)
        if self.electric_equipment is not None:
            sched.append(self.electric_equipment.schedule)
        if self.gas_equipment is not None:
            sched.append(self.gas_equipment.schedule)
        if self.infiltration is not None:
            sched.append(self.infiltration.schedule)
        if self.ventilation is not None and self.ventilation.schedule is not None:
            sched.append(self.ventilation.schedule)
        if self.setpoint is not None:
            sched.append(self.setpoint.heating_schedule)
            sched.append(self.setpoint.cooling_schedule)
            if self.setpoint.humidifying_schedule is not None:
                sched.append(self.setpoint.humidifying_schedule)
                sched.append(self.setpoint.dehumidifying_schedule)
        return sched

    @property
    def schedules_unique(self):
        """List of all unique schedules contained within the ProgramType."""
        return list(set(self.schedules))

    @classmethod
    def from_dict(cls, data):
        """Create a ProgramType from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: Dictionary describing the ProgramType with the format below.

        .. code-block:: python

            {
            "type": 'ProgramType',
            "identifier": str,  # ProgramType identifier
            "display_name": str,  # ProgramType display name
            'people': {},  # A People dictionary
            'lighting': {},  # A Lighting dictionary
            'electric_equipment': {},  # A ElectricEquipment dictionary
            'gas_equipment': {},  # A GasEquipment dictionary
            'infiltration': {},  # A Infliltration dictionary
            'ventilation': {},  # A Ventilation dictionary
            'setpoint': {}  # A Setpoint dictionary
            }

        """
        assert data['type'] == 'ProgramType', \
            'Expected ProgramType. Got {}.'.format(data['type'])

        # build each of the load objects
        people = People.from_dict(data['people']) if 'people' in data and \
            data['people'] is not None else None
        lighting = Lighting.from_dict(data['lighting']) if 'lighting' in data and \
            data['lighting'] is not None else None
        electric_equipment = ElectricEquipment.from_dict(data['electric_equipment']) \
            if 'electric_equipment' in data and \
            data['electric_equipment'] is not None else None
        gas_equipment = GasEquipment.from_dict(data['gas_equipment']) \
            if 'gas_equipment' in data and \
            data['gas_equipment'] is not None else None
        infiltration = Infiltration.from_dict(data['infiltration']) if 'infiltration' \
            in data and data['infiltration'] is not None else None
        ventilation = Ventilation.from_dict(data['ventilation']) if 'ventilation' \
            in data and data['ventilation'] is not None else None
        setpoint = Setpoint.from_dict(data['setpoint']) if 'setpoint' in data and \
            data['setpoint'] is not None else None

        new_obj = cls(data['identifier'], people, lighting, electric_equipment,
                      gas_equipment, infiltration, ventilation, setpoint)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a ProgramType object from an abridged dictionary.

        Args:
            data: A ProgramTypeAbridged dictionary.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the ProgramType object.

        .. code-block:: python

            {
            "type": 'ProgramTypeAbridged',
            "identifier": str,  # ProgramType identifier
            "display_name": str,  # ProgramType display name
            'people': {},  # A PeopleAbridged dictionary
            'lighting': {},  # A LightingAbridged dictionary
            'electric_equipment': {},  # A ElectricEquipmentAbridged dictionary
            'gas_equipment': {},  # A GasEquipmentAbridged dictionary
            'infiltration': {},  # A InfliltrationAbridged dictionary
            'ventilation': {},  # A VentilationAbridged dictionary
            'setpoint': {}  # A SetpointAbridged dictionary
            }
        """
        assert data['type'] == 'ProgramTypeAbridged', \
            'Expected ProgramTypeAbridged dictionary. Got {}.'.format(data['type'])

        # build each of the load objects
        people, lighting, electric_equipment, gas_equipment, infiltration, \
            ventilation, setpoint = cls._get_loads_from_abridged(data, schedule_dict)
        new_obj = cls(data['identifier'], people, lighting, electric_equipment,
                      gas_equipment, infiltration, ventilation, setpoint)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_dict(self, abridged=False):
        """Get ProgramType as a dictionary.

        Args:
            abridged: Boolean noting whether detailed schedule objects should be
                written into the ProgramType (False) or just an abridged version (True)
                that references the schedules by identifier. Default: False.
        """
        base = {'type': 'ProgramType'} if not \
            abridged else {'type': 'ProgramTypeAbridged'}
        base['identifier'] = self.identifier
        if self.people is not None:
            base['people'] = self.people.to_dict(abridged)
        if self.lighting is not None:
            base['lighting'] = self.lighting.to_dict(abridged)
        if self.electric_equipment is not None:
            base['electric_equipment'] = self.electric_equipment.to_dict(abridged)
        if self.gas_equipment is not None:
            base['gas_equipment'] = self.gas_equipment.to_dict(abridged)
        if self.infiltration is not None:
            base['infiltration'] = self.infiltration.to_dict(abridged)
        if self.ventilation is not None:
            base['ventilation'] = self.ventilation.to_dict(abridged)
        if self.setpoint is not None:
            base['setpoint'] = self.setpoint.to_dict(abridged)

        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    @staticmethod
    def average(identifier, program_types, weights=None, timestep_resolution=1):
        """Get a ProgramType object that's a weighted average between other objects.

        Args:
            identifier: A unique ID text string for the new averaged ProgramType.
                Must be < 100 characters and not contain any EnergyPlus special
                characters. This will be used to identify the object across a model
                and in the exported IDF.
            program_types: A list of ProgramType objects that will be averaged
                together to make a new ProgramType.
            weights: An optional list of fractional numbers with the same length
                as the input program_types that sum to 1. These will be used to weight
                each of the ProgramType objects in the resulting average. If None, the
                individual objects will be weighted equally. Default: None.
            timestep_resolution: An optional integer for the timestep resolution
                at which the schedules will be averaged. Any schedule details
                smaller than this timestep will be lost in the averaging process.
                Default: 1.
        """
        # check the weights input
        if weights is None:
            weights = [1 / len(program_types)] * len(program_types) if \
                len(program_types) > 0 else []
        else:
            weights = tuple_with_length(weights, len(program_types), float,
                                        'average ProgramType weights')
        assert abs(sum(weights) - 1.0) <= 1e-9, 'Average ProgramType weights ' \
            'must be equal to 1. Got {}.'.format(sum(weights))

        # gather all of the load objects across all of the programs
        people_mtx = [[pr.people, w] for pr, w in zip(program_types, weights)
                      if pr.people is not None]
        lighting_mtx = [[pr.lighting, w] for pr, w in zip(program_types, weights)
                        if pr.lighting is not None]
        e_equip_mtx = [[pr.electric_equipment, w] for pr, w in zip(program_types, weights)
                       if pr.electric_equipment is not None]
        g_equip_mtx = [[pr.gas_equipment, w] for pr, w in zip(program_types, weights)
                       if pr.gas_equipment is not None]
        inf_mtx = [[pr.infiltration, w] for pr, w in zip(program_types, weights)
                   if pr.infiltration is not None]
        vent_mtx = [[pr.ventilation, w] for pr, w in zip(program_types, weights)
                    if pr.ventilation is not None]
        setp_mtx = [[pr.setpoint, w] for pr, w in zip(program_types, weights)
                    if pr.setpoint is not None]

        # compute the average loads
        people = None
        if len(people_mtx) != 0:
            t_people_mtx = tuple(zip(*people_mtx))
            people = People.average('{}_People'.format(identifier), t_people_mtx[0],
                                    t_people_mtx[1], timestep_resolution)
        lighting = None
        if len(lighting_mtx) != 0:
            t_lighting_mtx = tuple(zip(*lighting_mtx))
            lighting = Lighting.average('{}_Lighting'.format(identifier), t_lighting_mtx[0],
                                        t_lighting_mtx[1], timestep_resolution)
        electric_equipment = None
        if len(e_equip_mtx) != 0:
            t_e_equip_mtx = tuple(zip(*e_equip_mtx))
            electric_equipment = ElectricEquipment.average(
                '{}_Electric Equipment'.format(identifier), t_e_equip_mtx[0],
                t_e_equip_mtx[1], timestep_resolution)
        gas_equipment = None
        if len(g_equip_mtx) != 0:
            t_g_equip_mtx = tuple(zip(*g_equip_mtx))
            gas_equipment = GasEquipment.average(
                '{}_Gas Equipment'.format(identifier), t_g_equip_mtx[0],
                t_g_equip_mtx[1], timestep_resolution)
        infiltration = None
        if len(inf_mtx) != 0:
            t_inf_mtx = tuple(zip(*inf_mtx))
            infiltration = Infiltration.average(
                '{}_Infiltration'.format(identifier), t_inf_mtx[0],
                t_inf_mtx[1], timestep_resolution)
        ventilation = None
        if len(vent_mtx) != 0:
            t_vent_mtx = tuple(zip(*vent_mtx))
            ventilation = Ventilation.average(
                '{}_Ventilation'.format(identifier), t_vent_mtx[0],
                t_vent_mtx[1], timestep_resolution)
        setpoint = None
        if len(setp_mtx) != 0:
            t_setp_mtx = tuple(zip(*setp_mtx))
            setpoint = Setpoint.average('{}_Setpoint'.format(identifier), t_setp_mtx[0],
                                        t_setp_mtx[1], timestep_resolution)

        # return the averaged object
        return ProgramType(identifier, people, lighting, electric_equipment, gas_equipment,
                           infiltration, ventilation, setpoint)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def lock(self):
        """The lock() method to will also lock the loads."""
        self._locked = True
        if self.people is not None:
            self.people.lock()
        if self.lighting is not None:
            self.lighting.lock()
        if self.electric_equipment is not None:
            self.electric_equipment.lock()
        if self.gas_equipment is not None:
            self.gas_equipment.lock()
        if self.infiltration is not None:
            self.infiltration.lock()
        if self.ventilation is not None:
            self.ventilation.lock()
        if self.setpoint is not None:
            self.setpoint.lock()

    def unlock(self):
        """The unlock() method will also unlock the loads."""
        self._locked = False
        if self.people is not None:
            self.people.unlock()
        if self.lighting is not None:
            self.lighting.unlock()
        if self.electric_equipment is not None:
            self.electric_equipment.unlock()
        if self.gas_equipment is not None:
            self.gas_equipment.unlock()
        if self.infiltration is not None:
            self.infiltration.unlock()
        if self.ventilation is not None:
            self.ventilation.unlock()
        if self.setpoint is not None:
            self.setpoint.unlock()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    @staticmethod
    def _get_loads_from_abridged(data, schedule_dict):
        """Get re-built load objects from abridged dictionaries."""
        people = None
        lighting = None
        electric_equipment = None
        gas_equipment = None
        infiltration = None
        ventilation = None
        setpoint = None
        if 'people' in data and data['people'] is not None:
            people = People.from_dict_abridged(data['people'], schedule_dict)
        if 'lighting' in data and data['lighting'] is not None:
            lighting = Lighting.from_dict_abridged(data['lighting'], schedule_dict)
        if 'electric_equipment' in data and data['electric_equipment'] is not None:
            electric_equipment = ElectricEquipment.from_dict_abridged(
                data['electric_equipment'], schedule_dict)
        if 'gas_equipment' in data and data['gas_equipment'] is not None:
            gas_equipment = GasEquipment.from_dict_abridged(
                data['gas_equipment'], schedule_dict)
        if 'infiltration' in data and data['infiltration'] is not None:
            infiltration = Infiltration.from_dict_abridged(
                data['infiltration'], schedule_dict)
        if 'ventilation' in data and data['ventilation'] is not None:
            ventilation = Ventilation.from_dict_abridged(
                data['ventilation'], schedule_dict)
        if 'setpoint' in data and data['setpoint'] is not None:
            setpoint = Setpoint.from_dict_abridged(data['setpoint'], schedule_dict)
        return people, lighting, electric_equipment, gas_equipment, infiltration, \
            ventilation, setpoint

    @staticmethod
    def _instance_in_array(object_instance, object_array):
        """Check if a specific object instance is already in an array.

        This can be much faster than  `if object_instance in object_array`
        when you expect to be testing a lot of the same instance of an object for
        inclusion in an array since the builtin method uses an == operator to
        test inclusion.
        """
        for val in object_array:
            if val is object_instance:
                return True
        return False

    def __copy__(self):
        people = self.people.duplicate() if self.people is not None else None
        lighting = self.lighting.duplicate() if self.lighting is not None else None
        electric_equipment = self.electric_equipment.duplicate() if \
            self.electric_equipment is not None else None
        gas_equipment = self.gas_equipment.duplicate() if \
            self.gas_equipment is not None else None
        infiltration = self.infiltration.duplicate() if \
            self.infiltration is not None else None
        ventilation = self.ventilation.duplicate() if \
            self.ventilation is not None else None
        setpoint = self.setpoint.duplicate() if self.setpoint is not None else None
        new_obj = ProgramType(self.identifier, people, lighting, electric_equipment,
                              gas_equipment, infiltration, ventilation, setpoint)
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, hash(self.people), hash(self.lighting),
                hash(self.electric_equipment), hash(self.gas_equipment),
                hash(self.infiltration), hash(self.ventilation), hash(self.setpoint))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, ProgramType) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Program Type: {}'.format(self.identifier)
