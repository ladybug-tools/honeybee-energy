# coding=utf-8
"""Detailed HVAC system object defined using IronBug or OpenStudio .NET bindings."""
from __future__ import division

from honeybee._lockable import lockable

from ._base import _HVACSystem


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
        * air_loop_count
        * thermal_zones
        * display_name
        * user_data
    """
    __slots__ = ('_specification', '_air_loop_count', '_thermal_zones')

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
        thermal_zones, air_loop_count = [], 0
        try:
            for a_loop in value['AirLoops']:
                if a_loop['$type'].startswith('Ironbug.HVAC.IB_NoAirLoop'):
                    for zone in a_loop['ThermalZones']:
                        for z_attr in zone['CustomAttributes']:
                            if z_attr['Field']['FullName'] == 'Name':
                                thermal_zones.append(z_attr['Value'])
                elif a_loop['$type'].startswith('Ironbug.HVAC.IB_AirLoopHVAC'):
                    air_loop_count += 1
                    for comp in a_loop['DemandComponents']:
                        if comp['$type'].startswith('Ironbug.HVAC.IB_AirLoopBranches'):
                            for branch in comp['Branches']:
                                for z_attr in branch[0]['CustomAttributes']:
                                    if z_attr['Field']['FullName'] == 'Name':
                                        thermal_zones.append(z_attr['Value'])
                else:
                    raise ValueError('DetailedHVAC specification does not contain '
                                     'any ThermalZones that can be matched to Rooms.')
        except KeyError as e:
            raise ValueError('DetailedHVAC specification is not valid:\n{}'.format(e))
        self._air_loop_count = air_loop_count
        self._thermal_zones = tuple(thermal_zones)
        self._specification = value

    @property
    def air_loop_count(self):
        """Get an integer for the number of air loops in the system."""
        return self._air_loop_count

    @property
    def thermal_zones(self):
        """Get a tuple of strings for the Rooms/Zones to which the HVAC is assigned."""
        return self._thermal_zones

    def to_ideal_air_equivalent(self):
        """This method is NOT YET IMPLEMENTED."""
        # TODO: Consider supporting this method by analyzing the air loop
        # sensing economizers, DCV, and heat recovery seems doable
        # but sensing heating-only and cooling-only systems seems more challenging
        msg = 'DetailedHVAC "{}" cannot be translated to an ideal air ' \
            'equivalent.'.format(self.display_name)
        raise NotImplementedError(msg)

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
