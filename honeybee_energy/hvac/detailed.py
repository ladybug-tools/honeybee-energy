# coding=utf-8
"""Detailed HVAC system object defined using IronBug or OpenStudio .NET bindings."""
from __future__ import division

from honeybee._lockable import lockable

from ._base import _HVACSystem
from .idealair import IdealAirSystem


@lockable
class DetailedHVAC(_HVACSystem):
    """Detailed HVAC system object defined using IronBug or OpenStudio .NET bindings.

    Args:
        identifier: Text string for detailed system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters.
        specification: A JSON-serializable dictionary representing the full
            specification of the detailed system. This can be obtained by calling
            the ToJson() method on any IronBug HVAC system and then serializing
            the resulting JSON string into a Python dictionary using the native
            Python json package. Note that the Rooms that the HVAC is assigned to
            must be specified as ThermalZones under this specification in order
            for the resulting Model this HVAC is a part of to be valid.

    Properties:
        * identifier
        * specification
        * thermal_zones
        * design_type
        * air_loop_count
        * economizer_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * display_name
        * user_data
    """
    NO_AIR_LOOP = 'Ironbug.HVAC.IB_NoAirLoop'
    AIR_LOOP = 'Ironbug.HVAC.IB_AirLoopHVAC'
    BRANCHES = 'Ironbug.HVAC.IB_AirLoopBranches'
    OA_SYSTEM = 'Ironbug.HVAC.IB_OutdoorAirSystem'
    OA_CONTROLLER = 'Ironbug.HVAC.IB_ControllerOutdoorAir'
    HEAT_RECOVERY = 'Ironbug.HVAC.IB_HeatExchangerAirToAirSensibleAndLatent'
    HR_SENSIBLE = (
        'SensibleEffectivenessat75CoolingAirFlow',
        'SensibleEffectivenessat75HeatingAirFlow'
    )
    HR_LATENT = (
        'LatentEffectivenessat75CoolingAirFlow',
        'LatentEffectivenessat75HeatingAirFlow'
    )
    ECONOMIZER_TYPES = ('NoEconomizer', 'DifferentialDryBulb', 'DifferentialEnthalpy',
                        'DifferentialDryBulbAndEnthalpy', 'FixedDryBulb',
                        'FixedEnthalpy', 'ElectronicEnthalpy')

    __slots__ = ('_specification', '_thermal_zones', '_design_type', '_air_loop_count',
                 '_economizer_type', '_sensible_heat_recovery', '_latent_heat_recovery')

    def __init__(self, identifier, specification):
        """Initialize DetailedHVAC."""
        # initialize base HVAC system properties
        _HVACSystem.__init__(self, identifier)
        self.specification = specification

    @property
    def specification(self):
        """Get or set a dictionary for the full specification of this HVAC.

        This can be obtained by calling the SaveAsJson() method on any IronBug HVAC
        system and then serializing the resulting JSON string into a Python dictionary
        using the native Python json package.
        """
        return self._specification

    @specification.setter
    def specification(self, value):
        assert isinstance(value, dict), 'Expected dictionary for DetailedHVAC' \
            'object specification. Got {}.'.format(type(value))
        thermal_zones, design_type, air_loop_count = [], 'HeatCool', 0
        econ_type, sensible_hr, latent_hr = 'NoEconomizer', 0, 0
        try:
            for a_loop in value['AirLoops']:
                if a_loop['$type'].startswith(self.NO_AIR_LOOP):
                    # get all of the zones on the demand side
                    for zone in a_loop['ThermalZones']:
                        for z_attr in zone['CustomAttributes']:
                            if z_attr['Field']['FullName'] == 'Name':
                                thermal_zones.append(z_attr['Value'])
                elif a_loop['$type'].startswith(self.AIR_LOOP):
                    # determine whether it's an AllAir system or DOAS system
                    air_loop_count += 1
                    design_type = 'AllAir'
                    if 'SizingSystem' in a_loop and \
                            'CustomAttributes' in a_loop['SizingSystem']:
                        for sz_attr in a_loop['SizingSystem']['CustomAttributes']:
                            if sz_attr['Field']['FullName'] == 'TypeofLoadtoSizeOn':
                                if sz_attr['Value'] == 'VentilationRequirement':
                                    design_type = 'DOAS'
                    # determine the type of economizer or heat recovery
                    for comp in a_loop['SupplyComponents']:
                        if comp['$type'].startswith(self.OA_SYSTEM):
                            for child in comp['Children']:
                                if child['$type'].startswith(self.OA_CONTROLLER):
                                    if 'CustomAttributes' in child:
                                        for attr in child['CustomAttributes']:
                                            f_name = attr['Field']['FullName']
                                            if f_name == 'EconomizerControlType':
                                                econ_type = self._f_econ(attr['Value'])
                            if 'IBProperties' in comp and \
                                    'OAStreamObjs' in comp['IBProperties']:
                                for oa_comp in comp['IBProperties']['OAStreamObjs']:
                                    if oa_comp['$type'].startswith(self.HEAT_RECOVERY):
                                        if 'CustomAttributes' in oa_comp:
                                            for oa_attr in oa_comp['CustomAttributes']:
                                                f_name = oa_attr['Field']['FullName']
                                                if f_name in self.HR_SENSIBLE:
                                                    sensible_hr = oa_attr['Value']
                                                if f_name in self.HR_LATENT:
                                                    latent_hr = oa_attr['Value']
                    # get all of the zones on the demand side
                    for comp in a_loop['DemandComponents']:
                        if comp['$type'].startswith(self.BRANCHES):
                            for branch in comp['Branches']:
                                for z_attr in branch[0]['CustomAttributes']:
                                    if z_attr['Field']['FullName'] == 'Name':
                                        thermal_zones.append(z_attr['Value'])
                else:
                    raise ValueError('DetailedHVAC specification does not contain '
                                     'any ThermalZones that can be matched to Rooms.')
        except KeyError as e:
            raise ValueError('DetailedHVAC specification is not valid:\n{}'.format(e))
        self._thermal_zones = tuple(thermal_zones)
        self._design_type = design_type
        self._air_loop_count = air_loop_count
        self._economizer_type = econ_type
        self._sensible_heat_recovery = sensible_hr
        self._latent_heat_recovery = latent_hr
        self._specification = value

    @property
    def thermal_zones(self):
        """Get a tuple of strings for the Rooms/Zones to which the HVAC is assigned."""
        return self._thermal_zones

    @property
    def design_type(self):
        """Text for the structure of the system. It will be one of the following.

        * AllAir
        * DOAS
        * HeatCool
        """
        return self._design_type

    @property
    def air_loop_count(self):
        """Get an integer for the number of air loops in the system."""
        return self._air_loop_count

    @property
    def economizer_type(self):
        """Get text to indicate the type of air-side economizer.

        Choose from the following options.

        * NoEconomizer
        * DifferentialDryBulb
        * DifferentialEnthalpy
        * DifferentialDryBulbAndEnthalpy
        * FixedDryBulb
        * FixedEnthalpy
        * ElectronicEnthalpy
        """
        return self._economizer_type

    @property
    def sensible_heat_recovery(self):
        """Get a number for the effectiveness of sensible heat recovery."""
        return self._sensible_heat_recovery

    @property
    def latent_heat_recovery(self):
        """Get a number for the effectiveness of latent heat recovery."""
        return self._latent_heat_recovery

    def sync_room_ids(self, room_map):
        """Sync this DetailedHVAC with Rooms that had their IDs changed.

        This is useful after running the Model.reset_ids() command to ensure that
        the bi-directional Room references between DetailedHVAC and Honeybee Rooms
        is correct.

        Args:
            room_map: A dictionary that relates the original Rooms identifiers (keys)
                to the new identifiers (values) of the Rooms in the Model.
        """
        thermal_zones, air_loop_count = [], 0
        hvac_spec = self._specification
        for a_loop in hvac_spec['AirLoops']:
            if a_loop['$type'].startswith(self.NO_AIR_LOOP):
                for zone in a_loop['ThermalZones']:
                    for z_attr in zone['CustomAttributes']:
                        if z_attr['Field']['FullName'] == 'Name':
                            z_attr['Value'] = room_map[z_attr['Value']]
                            thermal_zones.append(z_attr['Value'])
            elif a_loop['$type'].startswith(self.AIR_LOOP):
                air_loop_count += 1
                for comp in a_loop['DemandComponents']:
                    if comp['$type'].startswith(self.BRANCHES):
                        for branch in comp['Branches']:
                            for z_attr in branch[0]['CustomAttributes']:
                                if z_attr['Field']['FullName'] == 'Name':
                                    z_attr['Value'] = room_map[z_attr['Value']]
                                    thermal_zones.append(z_attr['Value'])
        # unlock object and set attributes
        was_locked = False
        if self._locked:
            was_locked = True
            self.unlock()
        self._air_loop_count = air_loop_count
        self._thermal_zones = tuple(thermal_zones)
        self._specification = hvac_spec
        if was_locked:  # set the object back to being locked
            self.lock()

    def to_ideal_air_equivalent(self):
        """This method is NOT YET IMPLEMENTED."""
        econ_typ = self.economizer_type
        if econ_typ not in self.ECONOMIZER_TYPES[:3]:
            enth_types = ('FixedEnthalpy', 'ElectronicEnthalpy')
            econ_typ = 'DifferentialEnthalpy' if econ_typ in enth_types \
                else 'DifferentialDryBulb'
        i_sys = IdealAirSystem(
            self.identifier, economizer_type=econ_typ,
            sensible_heat_recovery=self.sensible_heat_recovery,
            latent_heat_recovery=self.latent_heat_recovery)
        i_sys._display_name = self._display_name
        return i_sys

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A HVAC dictionary in following the format below.

        .. code-block:: python

            {
            "type": "DetailedHVAC",
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Custom VAV System",  # name for the HVAC
            "specification": {}  # dictionary for the full HVAC specification
            }
        """
        assert data['type'] == 'DetailedHVAC', \
            'Expected {} dictionary. Got {}.'.format('DetailedHVAC', data['type'])
        new_obj = cls(data['identifier'], data['specification'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a HVAC object from an abridged dictionary.

        Args:
            data: An abridged dictionary in following the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values.

        .. code-block:: python

            {
            "type": "DetailedHVAC",
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Custom VAV System",  # name for the HVAC
            "specification": {}  # dictionary for the full HVAC specification
            }
        """
        # this is the same as the from_dict method for as long as there are not schedules
        return cls.from_dict(data)

    def to_dict(self, abridged=False):
        """DetailedHVAC dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this object.
        """
        base = {'type': 'DetailedHVAC'}
        base['identifier'] = self.identifier
        base['specification'] = self.specification
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def _f_econ(self, value):
        clean_input = value.lower()
        for key in self.ECONOMIZER_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'economizer_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.ECONOMIZER_TYPES))
        return value

    def __copy__(self):
        new_obj = self.__class__(self.identifier, self.specification.copy())
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._air_loop_count) + self._thermal_zones

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'DetailedHVAC: {} [air loops: {}] [zones: {}]'.format(
            self.display_name, self.air_loop_count, len(self.thermal_zones))
