# coding=utf-8
"""Low temperature radiant system."""
from __future__ import division

from ._base import _HeatCoolBase

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, valid_string


@lockable
class Radiant(_HeatCoolBase):
    """Low temperature radiant HVAC system.

    By default, this HVAC template will swap out all floor and ceiling constructions
    of the Rooms that it is applied to (according to the radiant_face_type property).
    If the Rooms that the system is assigned to have constructions with internal
    source material layers, no floor or ceiling constructions will be changed
    and these existing constructions with internal sources will dictate the thermally
    active surfaces.

    Note that radiant systems are particularly limited in cooling capacity
    and using them may result in many unmet hours. To reduce unmet hours, use
    an expanded comfort range, remove carpet, reduce internal loads, reduce
    solar and envelope gains during peak times, and add thermal mass.

    Args:
        identifier: Text string for system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        vintage: Text for the vintage of the template system. This will be used
            to set efficiencies for various pieces of equipment within the system.
            Choose from the following.

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013
            * ASHRAE_2016
            * ASHRAE_2019

        equipment_type: Text for the specific type of the system and equipment. (Default:
            the first option below) Choose from.

            * Radiant_Chiller_Boiler
            * Radiant_Chiller_ASHP
            * Radiant_Chiller_DHW
            * Radiant_ACChiller_Boiler
            * Radiant_ACChiller_ASHP
            * Radiant_ACChiller_DHW
            * Radiant_DCW_Boiler
            * Radiant_DCW_ASHP
            * Radiant_DCW_DHW

        proportional_gain: A fractional number for the proportional gain constant.
            Recommended values are 0.3 or less. (Default: 0.3).
        minimum_operation_time: A number for the minimum number of hours of operation
            for the radiant system before it shuts off. (Default: 1).
        switch_over_time: A number for the minimum number of hours for when the system
            can switch between heating and cooling. (Default: 24).
        radiant_face_type: Text to indicate which faces are thermally active by default.
            Note that this property has no effect when the rooms to which the HVAC
            system is assigned have constructions with internal source materials.
            In this case, those constructions will dictate the thermally active
            surfaces. Choose from the following. (Default: Floor).

            * Floor
            * Ceiling
            * FloorWithCarpet

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * proportional_gain
        * minimum_operation_time
        * switch_over_time
        * radiant_face_type
        * schedules
    """
    __slots__ = ('_proportional_gain', '_minimum_operation_time',
                 '_switch_over_time', '_radiant_face_type')

    EQUIPMENT_TYPES = (
        'Radiant_Chiller_Boiler',
        'Radiant_Chiller_ASHP',
        'Radiant_Chiller_DHW',
        'Radiant_ACChiller_Boiler',
        'Radiant_ACChiller_ASHP',
        'Radiant_ACChiller_DHW',
        'Radiant_DCW_Boiler',
        'Radiant_DCW_ASHP',
        'Radiant_DCW_DHW'
    )

    RADIANT_FACE_TYPES = ('Floor', 'Ceiling', 'FloorWithCarpet')

    def __init__(self, identifier, vintage='ASHRAE_2019', equipment_type=None,
                 proportional_gain=0.3, minimum_operation_time=1,
                 switch_over_time=24, radiant_face_type='Floor'):
        """Initialize HVACSystem."""
        # initialize base HVAC system properties
        _HeatCoolBase.__init__(self, identifier, vintage, equipment_type)

        # set the main features of the HVAC system
        self.proportional_gain = proportional_gain
        self.minimum_operation_time = minimum_operation_time
        self.switch_over_time = switch_over_time
        self.radiant_face_type = radiant_face_type

    @property
    def proportional_gain(self):
        """Get or set a fractional number for the proportional gain constant."""
        return self._proportional_gain

    @proportional_gain.setter
    def proportional_gain(self, value):
        self._proportional_gain = \
            float_in_range(value, 0.0, 1.0, 'hvac proportional gain')

    @property
    def minimum_operation_time(self):
        """Get or set a the minimum hours of operation before the system shuts off."""
        return self._minimum_operation_time

    @minimum_operation_time.setter
    def minimum_operation_time(self, value):
        self._minimum_operation_time = \
            float_positive(value, 'hvac minimum operation time')

    @property
    def switch_over_time(self):
        """Get or set the minimum hours the system can switch between heating/cooling."""
        return self._switch_over_time

    @switch_over_time.setter
    def switch_over_time(self, value):
        self._switch_over_time = float_positive(value, 'hvac switch over time')

    @property
    def radiant_face_type(self):
        """Get or set text to indicate the type of default radiant face.

        Choose from the following options.

        * Floor
        * Ceiling
        * FloorWithCarpet
        """
        return self._radiant_face_type

    @radiant_face_type.setter
    def radiant_face_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.RADIANT_FACE_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'radiant_face_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.RADIANT_FACE_TYPES))
        self._radiant_face_type = value

    @classmethod
    def from_dict(cls, data):
        """Create a HVAC object from a dictionary.

        Args:
            data: A dictionary in following the format below.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "proportional_gain": 0.3,
            "minimum_operation_time": 1,
            "switch_over_time": 24,
            "radiant_face_type": "Ceiling"
            }
        """
        assert data['type'] == cls.__name__, \
            'Expected {} dictionary. Got {}.'.format(cls.__name__, data['type'])
        # extract the key features and properties of the HVAC
        pro_g, mot, sot, f_type = cls._radiant_properties_from_dict(data)
        new_obj = cls(data['identifier'], data['vintage'], data['equipment_type'],
                      pro_g, mot, sot, f_type)
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
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules
                to the Setpoint object.

        .. code-block:: python

            {
            "type": "",  # text for the class name of the HVAC
            "identifier": "Classroom1_System",  # identifier for the HVAC
            "display_name": "Standard System",  # name for the HVAC
            "vintage": "ASHRAE_2019",  # text for the vintage of the template
            "equipment_type": "",  # text for the HVAC equipment type
            "proportional_gain": 0.3,
            "minimum_operation_time": 1,
            "switch_over_time": 24,
            "radiant_face_type": "Ceiling"
            }
        """
        # this is the same as the from_dict method for as long as there are not schedules
        return cls.from_dict(data)

    def to_dict(self, abridged=False):
        """Radiant system dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True).
                This input currently has no effect but may eventually have one if
                schedule-type properties are exposed on this template.
        """
        base = {'type': self.__class__.__name__}
        base['identifier'] = self.identifier
        base['vintage'] = self.vintage
        base['equipment_type'] = self.equipment_type
        base['proportional_gain'] = self.proportional_gain
        base['minimum_operation_time'] = self.minimum_operation_time
        base['switch_over_time'] = self.switch_over_time
        base['radiant_face_type'] = self.radiant_face_type
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    @staticmethod
    def _radiant_properties_from_dict(data):
        """Extract basic radiant properties from a dictionary and assign defaults."""
        pro_g = data['proportional_gain'] if 'proportional_gain' in data else 0.3
        mot = data['minimum_operation_time'] if 'minimum_operation_time' in data else 1
        sot = data['switch_over_time'] if 'switch_over_time' in data else 24
        econ = data['radiant_face_type'] if 'radiant_face_type' in data and \
            data['radiant_face_type'] is not None else 'Floor'
        return pro_g, mot, sot, econ

    def __copy__(self):
        new_obj = self.__class__(
            self._identifier, self._vintage, self._equipment_type,
            self._proportional_gain, self._minimum_operation_time,
            self._switch_over_time, self._radiant_face_type)
        new_obj._display_name = self._display_name
        new_obj._user_data = None if self._user_data is None else self._user_data.copy()
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, self._vintage, self._equipment_type,
                self._proportional_gain, self._minimum_operation_time,
                self._switch_over_time, self._radiant_face_type)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, self.__class__) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)
