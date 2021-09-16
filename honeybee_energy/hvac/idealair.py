# coding=utf-8
"""Simple ideal air system object used to condition zones."""
from __future__ import division

from ._base import _HVACSystem
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_string, float_positive, float_in_range
from honeybee.altnumber import autosize, no_limit


@lockable
class IdealAirSystem(_HVACSystem):
    """Simple ideal air system object used to condition zones.

    Args:
        identifier: Text string for ideal air system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        economizer_type: Text to indicate the type of air-side economizer used on
            the ideal air system. Economizers will mix in a greater amount of
            outdoor air to cool the zone (rather than running the cooling system)
            when the zone needs cooling and the outdoor air is cooler than the zone.
            Choose from the options below. (Default: DifferentialDryBulb).

            * NoEconomizer
            * DifferentialDryBulb
            * DifferentialEnthalpy

        demand_controlled_ventilation: Boolean to note whether demand controlled
            ventilation should be used on the system, which will vary the amount
            of ventilation air according to the occupancy schedule of the
            Room. (Default: False).
        sensible_heat_recovery: A number between 0 and 1 for the effectiveness
            of sensible heat recovery within the system. (Default: 0).
        latent_heat_recovery: A number between 0 and 1 for the effectiveness
            of latent heat recovery within the system. (Default: 0).
        heating_air_temperature: A number for the maximum heating supply air
            temperature [C]. (Default: 50, which is typical for many air-based
            HVAC systems).
        cooling_air_temperature: A number for the minimum cooling supply air
            temperature [C]. (Default: 13, which is typical for many air-based
            HVAC systems).
        heating_limit: A number for the maximum heating capacity in Watts. This
            can also be an Autosize object to indicate that the capacity should
            be determined during the EnergyPlus sizing calculation. This can also
            be a NoLimit object to indicate no upper limit to the heating
            capacity. (Default: autosize).
        cooling_limit: A number for the maximum cooling capacity in Watts. This
            can also be an Autosize object to indicate that the capacity should
            be determined during the EnergyPlus sizing calculation. This can also
            be a NoLimit object to indicate no upper limit to the cooling
            capacity. (Default: autosize).
        heating_availability: An optional on/off schedule to set the availability of
            heating over the course of the simulation. (Default: None).
        cooling_availability: An optional on/off schedule to set the availability of
            cooling over the course of the simulation. (Default: None).

    Properties:
        * identifier
        * display_name
        * economizer_type
        * demand_controlled_ventilation
        * sensible_heat_recovery
        * latent_heat_recovery
        * heating_air_temperature
        * cooling_air_temperature
        * heating_limit
        * cooling_limit
        * heating_availability
        * cooling_availability
        * schedules
    """
    __slots__ = ('_economizer_type', '_demand_controlled_ventilation',
                 '_sensible_heat_recovery', '_latent_heat_recovery',
                 '_heating_air_temperature', '_cooling_air_temperature',
                 '_heating_limit', '_cooling_limit', '_heating_availability',
                 '_cooling_availability')
    ECONOMIZER_TYPES = ('NoEconomizer', 'DifferentialDryBulb', 'DifferentialEnthalpy')

    def __init__(self, identifier, economizer_type='DifferentialDryBulb',
                 demand_controlled_ventilation=False,
                 sensible_heat_recovery=0, latent_heat_recovery=0,
                 heating_air_temperature=50, cooling_air_temperature=13,
                 heating_limit=autosize, cooling_limit=autosize,
                 heating_availability=None, cooling_availability=None):
        """Initialize IdealAirSystem."""
        # initialize base HVAC system properties
        _HVACSystem.__init__(self, identifier)

        # set the main features of the HVAC system
        self.economizer_type = economizer_type
        self.demand_controlled_ventilation = demand_controlled_ventilation
        self.sensible_heat_recovery = sensible_heat_recovery
        self.latent_heat_recovery = latent_heat_recovery

        # set the options affecting heating and cooling
        # set heating_air_temperature without the setter to ensure > cooling check works
        self._heating_air_temperature = \
            float_positive(heating_air_temperature, 'ideal air heating air temperature')
        self.cooling_air_temperature = cooling_air_temperature
        self.heating_limit = heating_limit
        self.cooling_limit = cooling_limit
        self.heating_availability = heating_availability
        self.cooling_availability = cooling_availability

    @property
    def economizer_type(self):
        """Get or set text to indicate the type of air-side economizer.

        Choose from the following options:

        * NoEconomizer
        * DifferentialDryBulb
        * DifferentialEnthalpy
        """
        return self._economizer_type

    @economizer_type.setter
    def economizer_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.ECONOMIZER_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'economizer_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.ECONOMIZER_TYPES))
        self._economizer_type = value

    @property
    def demand_controlled_ventilation(self):
        """Get or set a boolean for whether demand controlled ventilation is present."""
        return self._demand_controlled_ventilation

    @demand_controlled_ventilation.setter
    def demand_controlled_ventilation(self, value):
        self._demand_controlled_ventilation = bool(value)

    @property
    def sensible_heat_recovery(self):
        """Get or set a number for the effectiveness of sensible heat recovery."""
        return self._sensible_heat_recovery

    @sensible_heat_recovery.setter
    def sensible_heat_recovery(self, value):
        self._sensible_heat_recovery = float_in_range(
            value, 0.0, 1.0, 'ideal air sensible heat recovery')

    @property
    def latent_heat_recovery(self):
        """Get or set a number for the effectiveness of latent heat recovery."""
        return self._latent_heat_recovery

    @latent_heat_recovery.setter
    def latent_heat_recovery(self, value):
        self._latent_heat_recovery = float_in_range(
            value, 0.0, 1.0, 'ideal air latent heat recovery')

    @property
    def heating_air_temperature(self):
        """Get or set a number for the maximum heating supply air temperature."""
        return self._heating_air_temperature

    @heating_air_temperature.setter
    def heating_air_temperature(self, value):
        self._heating_air_temperature = float_in_range(
            value, 0, 100, 'ideal air heating air temperature')
        self._air_temperature_check()

    @property
    def cooling_air_temperature(self):
        """Get or set a number for the minimum cooling supply air temperature."""
        return self._cooling_air_temperature

    @cooling_air_temperature.setter
    def cooling_air_temperature(self, value):
        self._cooling_air_temperature = float_in_range(
            value, -100, 50, 'ideal air cooling air temperature')
        self._air_temperature_check()

    @property
    def heating_limit(self):
        """Get or set a number for the maximum heating capacity in Watts."""
        return self._heating_limit

    @heating_limit.setter
    def heating_limit(self, value):
        if value == autosize or value is None:
            self._heating_limit = autosize
        elif value == no_limit:
            self._heating_limit = no_limit
        else:
            self._heating_limit = float_positive(value, 'ideal air heating limit')

    @property
    def cooling_limit(self):
        """Get or set a number for the maximum cooling capacity in Watts."""
        return self._cooling_limit

    @cooling_limit.setter
    def cooling_limit(self, value):
        if value == autosize or value is None:
            self._cooling_limit = autosize
        elif value == no_limit:
            assert self.economizer_type == 'NoEconomizer', 'Ideal air system ' \
                'economizer_type must be "NoEconomizer" to have no cooling limit.'
            self._cooling_limit = no_limit
        else:
            self._cooling_limit = float_positive(value, 'ideal air cooling limit')

    @property
    def heating_availability(self):
        """Get or set a ScheduleRuleset/ScheduleFixedInterval for heating availability.
        """
        return self._heating_availability

    @heating_availability.setter
    def heating_availability(self, value):
        if value is not None:
            self._check_schedule(value, 'heating_availability')
            value.lock()   # lock editing in case schedule has multiple references
        self._heating_availability = value

    @property
    def cooling_availability(self):
        """Get or set a ScheduleRuleset/ScheduleFixedInterval for cooling availability.
        """
        return self._cooling_availability

    @cooling_availability.setter
    def cooling_availability(self, value):
        if value is not None:
            self._check_schedule(value, 'cooling_availability')
            value.lock()   # lock editing in case schedule has multiple references
        self._cooling_availability = value

    @property
    def schedules(self):
        """Get an array of all the schedules associated with the HVAC system."""
        schedules = []
        if self._heating_availability is not None:
            schedules.append(self._heating_availability)
        if self._cooling_availability is not None:
            schedules.append(self._cooling_availability)
        return schedules

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create an IdealAirSystem object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                HVACTemplate:Zone:IdealLoadsAirSystem definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the IdealAirSystem object.

        Returns:
            A tuple with two elements

            -   ideal_air_system: An IdealAirSystem object loaded from the idf_string.

            -   zone_identifier: The identifier of the zone to which the IdealAirSystem
                object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'HVACTemplate:Zone:IdealLoadsAirSystem,')

        # set defaults for anything not included
        identifier = '{} Ideal Loads Air System'.format(ep_strs[0])
        econ = 'DifferentialDryBulb'
        dcv = False
        sensible = 0
        latent = 0
        heat_temp = 50
        cool_temp = 13
        heat_limit = autosize
        cool_limit = autosize
        heat_sch = None
        cool_sch = None

        # extract the properties from the string
        try:
            heat_temp = ep_strs[3] if ep_strs[3] != '' else heat_temp
            cool_temp = ep_strs[4] if ep_strs[4] != '' else cool_temp
            if ep_strs[7].lower() == 'limitcapacity' or \
                    ep_strs[7].lower() == 'limitflowrateandcapacity':
                heat_limit = autosize if ep_strs[9] == '' or \
                    ep_strs[9].lower() == 'autosize' else ep_strs[9]
            else:
                heat_limit = no_limit
            if ep_strs[10].lower() == 'limitcapacity' or \
                    ep_strs[10].lower() == 'limitflowrateandcapacity':
                cool_limit = autosize if ep_strs[12] == '' or \
                    ep_strs[12].lower() == 'autosize' else ep_strs[12]
            else:
                cool_limit = no_limit
            if ep_strs[13] != '':
                heat_sch = schedule_dict[ep_strs[13]]
            if ep_strs[14] != '':
                cool_sch = schedule_dict[ep_strs[14]]
            if ep_strs[25].lower() == 'occupancyschedule':
                dcv = True
            if ep_strs[26].lower() != 'differentialdrybulb':
                econ = ep_strs[26]
            if ep_strs[27].lower() == 'sensible':
                sensible = ep_strs[28] if ep_strs[28] != '' else 0.7
            elif ep_strs[27].lower() == 'enthalpy':
                sensible = ep_strs[28] if ep_strs[28] != '' else 0.7
                latent = ep_strs[29] if ep_strs[29] != '' else 0.65
        except IndexError:
            pass  # shorter Ideal air loads definition

        # return the object and the zone identifier for the object
        ideal_air_system = cls(
            identifier, econ, dcv, sensible, latent, heat_temp, cool_temp,
            heat_limit, cool_limit, heat_sch, cool_sch)
        zone_identifier = ep_strs[0]
        return ideal_air_system, zone_identifier

    @classmethod
    def from_dict(cls, data):
        """Create a IdealAirSystem object from a dictionary.

        Args:
            data: A IdealAirSystem dictionary in following the format below.

        .. code-block:: python

            {
            "type": "IdealAirSystem",
            "identifier": "Classroom1 Ideal Loads Air System",  # identifier for the HVAC
            "display_name": "Standard IdealAir",  # name for the HVAC
            "economizer_type": 'DifferentialDryBulb',  # Economizer type
            "demand_controlled_ventilation": True,  # Demand controlled ventilation
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            "heating_air_temperature": 50,  # Heating supply air temperature
            "cooling_air_temperature": 13,  # Cooling supply air temperature
            "heating_limit": {'type': 'Autosize'},  # Max size of the heating system
            "cooling_limit": {'type': 'Autosize'},  # Max size of the cooling system
            "heating_availability": {},  # Schedule for availability of heat or None
            "cooling_availability": {}  # Schedule for availability of cooling or None
            }
        """
        assert data['type'] == 'IdealAirSystem', \
            'Expected IdealAirSystem dictionary. Got {}.'.format(data['type'])

        # extract the key features and properties of the HVAC
        econ, dcv, sensible, latent, heat_temp, cool_temp, heat_limit, cool_limit = \
            cls._properties_from_dict(data)

        # extract the schedules
        heat_avail = cls._get_schedule_from_dict(data['heating_availability']) if \
            'heating_availability' in data and data['heating_availability'] is not None \
            else None
        cool_avail = cls._get_schedule_from_dict(data['cooling_availability']) if \
            'cooling_availability' in data and data['cooling_availability'] is not None \
            else None

        new_obj = cls(data['identifier'], econ, dcv, sensible, latent, heat_temp,
                      cool_temp, heat_limit, cool_limit, heat_avail, cool_avail)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a IdealAirSystem object from an abridged dictionary.

        Args:
            data: A IdealAirSystemAbridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Setpoint object.

        .. code-block:: python

            {
            "type": 'IdealAirSystemAbridged',
            "identifier": 'Warehouse1 Ideal Loads Air System',  # identifier for the HVAC
            "economizer_type": 'DifferentialDryBulb',  # Economizer type
            "demand_controlled_ventilation": True,  # Demand controlled ventilation
            "sensible_heat_recovery": 0.75,  # Sensible heat recovery effectiveness
            "latent_heat_recovery": 0.7,  # Latent heat recovery effectiveness
            "heating_air_temperature": 40,  # Heating supply air temperature
            "cooling_air_temperature": 15,  # Cooling supply air temperature
            "heating_limit": 'autosize',  # Max size of the heating system in Watts
            "cooling_limit": 'autosize',  # Max size of the cooling system in Watts
            "heating_availability": "Warehouse Heating Control",  # identifier of schedule
            "cooling_availability": "Warehouse Cooling Control",  # identifier of schedule
            }
        """
        assert data['type'] == 'IdealAirSystemAbridged', \
            'Expected IdealAirSystemAbridged dictionary. Got {}.'.format(data['type'])

        # extract the key features and properties of the HVAC
        econ, dcv, sensible, latent, heat_temp, cool_temp, heat_limit, cool_limit = \
            cls._properties_from_dict(data)

        # extract the schedules
        heat_avail = None
        cool_avail = None
        if 'heating_availability' in data and data['heating_availability'] is not None:
            try:
                heat_avail = schedule_dict[data['heating_availability']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        if 'cooling_availability' in data and data['cooling_availability'] is not None:
            try:
                cool_avail = schedule_dict[data['cooling_availability']]
            except KeyError as e:
                raise ValueError('Failed to find {} in the schedule_dict.'.format(e))

        new_obj = cls(data['identifier'], econ, dcv, sensible, latent, heat_temp,
                      cool_temp, heat_limit, cool_limit, heat_avail, cool_avail)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self, room):
        """IDF string representation of IdealAirSystem object.

        Note that this method does not return full definitions of heating/cooling
        availability schedules and so this objects's schedules must also be translated
        into the final IDF file.

        Args:
            room: A Honeybee Room for which the specific IDF string will be generated.
                This Room must have a Setpoint object for this method to work
                correctly since all setpoints (and any ventilation requirements)
                are pulled from this Room.
        """
        # check that a setpoint object is assigned
        assert room.properties.energy.setpoint is not None, \
            'IdealAirSystem must be assigned to a Room ' \
            'with a setpoint object to use IdealAirSystem.to_idf.'

        # extract all of the fields from this object and its room
        # heating limit
        if self.heating_limit != no_limit:
            h_lim_type = 'LimitCapacity'
            heat_limit = str(self.heating_limit)  # stringify Autosize
        else:
            h_lim_type = 'NoLimit'
            heat_limit = ''
        # cooling limit
        if self.cooling_limit != no_limit:
            c_lim_type = 'LimitFlowRateAndCapacity'
            air_limit = 'Autosize'
            cool_limit = str(self.cooling_limit)  # stringify Autosize
        else:
            c_lim_type = 'NoLimit'
            air_limit = cool_limit = ''
        # availability schedules
        heat_avail = self.heating_availability.identifier if \
            self.heating_availability is not None else ''
        cool_avail = self.cooling_availability.identifier if \
            self.cooling_availability is not None else ''
        # humidifying setpoint
        if room.properties.energy.setpoint.humidifying_setpoint is not None:
            humid_type = 'Humidistat'
            humid_setpt = room.properties.energy.setpoint.humidifying_setpoint
        else:
            humid_type = 'None'
            humid_setpt = ''
        # dehumidifying setpoint
        if room.properties.energy.setpoint.dehumidifying_setpoint is not None:
            dehumid_type = 'Humidistat'
            dehumid_setpt = room.properties.energy.setpoint.dehumidifying_setpoint
        else:
            dehumid_type = 'None'
            dehumid_setpt = ''
        # ventilation requirements
        if room.properties.energy.ventilation is not None:
            oa_method = 'DetailedSpecification'
            oa_id = '{}..{}'.format(room.properties.energy.ventilation.identifier,
                                    room.identifier)
        else:
            oa_method = 'None'
            oa_id = ''
        # demand controlled ventilation
        dcv = 'OccupancySchedule' if self.demand_controlled_ventilation else 'None'
        # heat recovery
        if self.sensible_heat_recovery == 0 and self.latent_heat_recovery == 0:
            heat_recovery = 'None'
        elif self.latent_heat_recovery != 0:
            heat_recovery = 'Enthalpy'
        else:
            heat_recovery = 'Sensible'

        # return a full IDF string
        thermostat = '{}..{}'.format(room.properties.energy.setpoint.identifier,
                                     room.identifier)
        values = (room.identifier, thermostat,
                  '', self.heating_air_temperature, self.cooling_air_temperature,
                  '', '', h_lim_type, '', heat_limit, c_lim_type, air_limit, cool_limit,
                  heat_avail, cool_avail, dehumid_type, '', dehumid_setpt,
                  humid_type, humid_setpt, oa_method, '', '', '', oa_id, dcv,
                  self.economizer_type, heat_recovery, self.sensible_heat_recovery,
                  self.latent_heat_recovery)
        comments = (
            'zone name', 'template thermostat name', 'availability schedule',
            'heating supply air temp {C}', 'cooling supply air temp {C}',
            'max heating supply air hr {kg-H2O/kg-air}',
            'min cooling supply air hr {kg-H2O/kg-air}',
            'heating limit', 'max heating fow rate {m3/s}', 'max sensible heat capacity',
            'cooling limit', 'max cooling fow rate {m3/s}', 'max total cooling capacity',
            'heating availability schedule', 'cooling availability schedule',
            'dehumidification type', 'cooling shr', 'dehumidification setpoint',
            'humidification type', 'humidification setpoint', 'outdoor air method',
            'oa per person', 'oa per area', 'oa per zone', 'outdoor air object name',
            'demand controlled vent type', 'economizer type', 'heat recovery type',
            'sensible heat recovery effectiveness', 'latent heat recovery effectiveness')
        return generate_idf_string(
            'HVACTemplate:Zone:IdealLoadsAirSystem', values, comments)

    def to_dict(self, abridged=False):
        """IdealAirSystem dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. Default: False.
        """
        base = {'type': 'IdealAirSystem'} if not \
            abridged else {'type': 'IdealAirSystemAbridged'}
        base['identifier'] = self.identifier
        base['economizer_type'] = self.economizer_type
        base['demand_controlled_ventilation'] = self.demand_controlled_ventilation
        base['sensible_heat_recovery'] = self.sensible_heat_recovery
        base['latent_heat_recovery'] = self.latent_heat_recovery
        base['heating_air_temperature'] = self.heating_air_temperature
        base['cooling_air_temperature'] = self.cooling_air_temperature
        base['heating_limit'] = self.heating_limit if \
            isinstance(self.heating_limit, float) else self.heating_limit.to_dict()
        base['cooling_limit'] = self.cooling_limit if \
            isinstance(self.cooling_limit, float) else self.cooling_limit.to_dict()
        if self.heating_availability is not None:
            base['heating_availability'] = self.heating_availability.identifier if \
                abridged else self.heating_availability.to_dict()
        if self.cooling_availability is not None:
            base['cooling_availability'] = self.cooling_availability.identifier if \
                abridged else self.cooling_availability.to_dict()
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def _air_temperature_check(self):
        """Check that heating_air_temperature is greater than cooling_air_temperature."""
        assert self._heating_air_temperature > self._cooling_air_temperature, \
            'Ideal air heating_air_temperature must be greater than ' \
            'cooling_air_temperature.'

    @staticmethod
    def _properties_from_dict(data):
        """Extract basic properties from a dictionary and assign defaults."""
        # extract the key features of the HVAC
        econ = data['economizer_type'] if 'economizer_type' in data and \
            data['economizer_type'] is not None else 'DifferentialDryBulb'
        dcv = data['demand_controlled_ventilation'] if \
            'demand_controlled_ventilation' in data else False
        sensible = data['sensible_heat_recovery'] if \
            'sensible_heat_recovery' in data else 0
        latent = data['latent_heat_recovery'] if \
            'latent_heat_recovery' in data else 0

        # extract the heating and cooling temperature
        heat_temp = data['heating_air_temperature'] if \
            'heating_air_temperature' in data else 50
        cool_temp = data['cooling_air_temperature'] if \
            'cooling_air_temperature' in data else 13

        # extract the heating and cooling limits
        if 'heating_limit' not in data or data['heating_limit'] == autosize.to_dict():
            heat_limit = autosize
        else:
            heat_limit = no_limit if data['heating_limit'] == no_limit.to_dict() \
                else data['heating_limit']
        if 'cooling_limit' not in data or data['cooling_limit'] == autosize.to_dict():
            cool_limit = autosize
        else:
            cool_limit = no_limit if data['cooling_limit'] == no_limit.to_dict() \
                else data['cooling_limit']

        return econ, dcv, sensible, latent, heat_temp, cool_temp, heat_limit, cool_limit

    def __copy__(self):
        new_obj = IdealAirSystem(
            self._identifier, self._economizer_type, self._demand_controlled_ventilation,
            self._sensible_heat_recovery, self._latent_heat_recovery,
            self._heating_air_temperature, self._cooling_air_temperature,
            self._heating_limit, self._cooling_limit, self._heating_availability,
            self._cooling_availability)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (
            self._identifier, self._economizer_type, self._demand_controlled_ventilation,
            self._sensible_heat_recovery, self._latent_heat_recovery,
            self._heating_air_temperature, self._cooling_air_temperature,
            str(self._heating_limit), str(self._cooling_limit),
            hash(self._heating_availability), hash(self._cooling_availability))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, IdealAirSystem) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'IdealAirSystem: {}'.format(self.display_name)
