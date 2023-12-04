# coding=utf-8
"""Definition of window opening for ventilative cooling."""
from __future__ import division

from .control import VentilationControl
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, valid_string, valid_ep_string


@lockable
class VentilationFan(object):
    """Definition of a fan for ventilative cooling.

    This fan is not connected to any heating or cooling system and is meant to
    represent the intentional circulation of unconditioned outdoor air for the
    purposes of keeping a space cooler, drier or free of indoor pollutants (as in
    the case of kitchen or bathroom exhaust fans).

    Args:
        identifier: Text string for a unique VentilationFan ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        flow_rate: A positive number for the flow rate of the fan in m3/s.
        ventilation_type: Text to indicate the type of type of ventilation. Choose
            from the options below. For either Exhaust or Intake, values for
            fan pressure and efficiency define the fan electric consumption. For Exhaust
            ventilation, the conditions of the air entering the space are assumed
            to be equivalent to outside air conditions. For Intake and Balanced
            ventilation, an appropriate amount of fan heat is added to the
            entering air stream. For Balanced ventilation, both an intake fan
            and an exhaust fan are assumed to co-exist, both having the same
            flow rate and power consumption (using the entered values for fan
            pressure rise and fan total efficiency). Thus, the fan electric
            consumption for Balanced ventilation is twice that for the Exhaust or 
            Intake ventilation types which employ only a single fan. (Default: Balanced).

            * Exhaust
            * Intake
            * Balanced

        pressure_rise: A number for the the pressure rise across the fan in Pascals
            (N/m2). This is often a function of the fan speed and the conditions in
            which the fan is operating since having the fan blow air through filters
            or narrow ducts will increase the pressure rise that is needed to
            deliver the input flow rate. The pressure rise plays an important role in
            determining the amount of energy consumed by the fan. Smaller fans like
            a 0.05 m3/s desk fan tend to have lower pressure rises around 60 Pa.
            Larger fans, such as a 6 m3/s fan used for ventilating a large room tend
            to have higher pressure rises around 400 Pa. The highest pressure rises
            are typically for large fans blowing air through ducts and filters, which
            can have pressure rises as high as 1000 Pa. If this input is None,
            the pressure rise will be estimated from the flow_rate, with higher
            flow rates corresponding to larger pressure rises (up to 400 Pa). These
            estimated pressure rises are generally assumed to have minimal obstructions
            between the fan and the room and they should be increased if the fan is
            blowing air through ducts or filters. (Default: None).
        efficiency: A number between 0 and 1 for the overall efficiency of the fan.
            Specifically, this is the ratio of the power delivered to the fluid
            to the electrical input power. It is the product of the fan motor
            efficiency and the fan impeller efficiency. Fans that have a higher blade
            diameter and operate at lower speeds with smaller pressure rises for
            their size tend to have higher efficiencies. Because motor efficiencies
            are typically between 0.8 and 0.9, the best overall fan efficiencies
            tend to be around 0.7 with most typical fan efficiencies between 0.5 and
            0.7. The lowest efficiencies often happen for small fans in situations
            with high pressure rises for their size, which can result in efficiencies
            as low as 0.15. If None, this input will be estimated from the fan
            flow rate and pressure rise with large fans operating at low pressure
            rises for their size having up to 0.7 efficiency and small fans
            operating at high pressure rises for their size having as low as
            0.15 efficiency. (Default: None).
        control: A VentilationControl object that dictates the conditions under
            which the fan is turned on. If None, a default VentilationControl will
            be generated, which will keep the fan on all of the time. (Default: None).

    Properties:
        * identifier
        * display_name
        * flow_rate
        * ventilation_type
        * pressure_rise
        * efficiency
        * control
    """
    __slots__ = (
        '_identifier', '_display_name', '_flow_rate', '_ventilation_type',
        '_pressure_rise', '_efficiency', '_control', '_locked')
    # types of ventilation
    VENTILATION_TYPES = ('Exhaust', 'Intake', 'Balanced')
    # values relating flow rates to pressure rises
    PRESSURE_RISES = (
        (0.01, 10),
        (0.05, 60),
        (0.25, 120),
        (0.5, 200),
        (2, 300),
        (6, 400)
    )

    def __init__(self, identifier, flow_rate, ventilation_type='Balanced',
                 pressure_rise=None, efficiency=None, control=None):
        """Initialize VentilationControl."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.flow_rate = flow_rate
        self.ventilation_type = ventilation_type
        self.pressure_rise = pressure_rise
        self.efficiency = efficiency
        self.control = control

    @property
    def identifier(self):
        """Get or set the text string for object identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier)

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
        if value is not None:
            try:
                value = str(value)
            except UnicodeEncodeError:  # Python 2 machine lacking the character set
                pass  # keep it as unicode
        self._display_name = value

    @property
    def flow_rate(self):
        """Get or set a number for the fan flow rate in m3/s."""
        return self._flow_rate

    @flow_rate.setter
    def flow_rate(self, value):
        self._flow_rate = float_positive(value, 'fan flow rate')

    @property
    def ventilation_type(self):
        """Get or set text to indicate the type of ventilation.

        Choose from the following options:

        * Exhaust
        * Intake
        * Balanced
        """
        return self._ventilation_type

    @ventilation_type.setter
    def ventilation_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.VENTILATION_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'ventilation_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.VENTILATION_TYPES))
        self._ventilation_type = value

    @property
    def pressure_rise(self):
        """Get or set a number for the fan flow rate in m3/s."""
        if self._pressure_rise is not None:
            return self._pressure_rise
        return self._default_pressure_rise()

    @pressure_rise.setter
    def pressure_rise(self, value):
        if value is not None:
            value = float_positive(value, 'fan pressure rise')
        self._pressure_rise = value

    @property
    def efficiency(self):
        """Get or set a number between 0 and 1 for the fan efficiency."""
        if self._efficiency is not None:
            return self._efficiency
        return self._default_efficiency()

    @efficiency.setter
    def efficiency(self, value):
        if value is not None:
            value = float_in_range(value, 0, 1, 'fan efficiency')
        self._efficiency = value

    @property
    def control(self):
        """Get or set a VentilationControl object to dictate when the fan comes on."""
        return self._control

    @control.setter
    def control(self, value):
        if value is not None:
            assert isinstance(value, VentilationControl), 'Expected VentilationControl' \
                ' object for Fan control. Got {}'.format(type(value))
        else:
            value = VentilationControl()
        self._control = value

    @classmethod
    def from_idf(cls, idf_string, schedule_dict):
        """Create a VentilationFan object from an EnergyPlus IDF text string.

        Note that the ZoneVentilation:DesignFlowRate idf_string must use
        the 'Flow/Zone' method in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus
                ZoneVentilation:DesignFlowRate definition.
            schedule_dict: A dictionary with schedule identifiers as keys and honeybee
                schedule objects as values (either ScheduleRuleset or
                ScheduleFixedInterval). These will be used to assign the schedules to
                the VentilationControl object that governs the control of the fan.

        Returns:
            A tuple with two elements

            -   fan: An VentilationFan object loaded from the idf_string.

            -   zone_id: The identifier of the zone to which the
                VentilationFan object should be assigned.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'ZoneVentilation:DesignFlowRate,')
        # check the inputs
        assert len(ep_strs) >= 9, 'ZoneVentilation:DesignFlowRate does not contain ' \
            'enough information to be loaded to a VentilationFan.'
        assert ep_strs[3].lower() == 'flow/zone', 'ZoneVentilation:DesignFlowRate ' \
            'must use Flow/Zone method to be loaded to a VentilationFan.'
        assert ep_strs[8] != '' and ep_strs[8].lower() != 'natural', \
            'ZoneVentilation:DesignFlowRate cannot use Natural ventilation ' \
            'to be loaded to a VentilationFan.'
        # extract the properties from the string
        sched = None
        flow = 0
        vt = 'Balanced'
        pressure = 0
        eff = 1
        min_in_t = -100
        max_in_t = 100
        delta_t = -100
        min_out_t = -100
        max_out_t = 100
        try:
            sched = ep_strs[2] if ep_strs[2] != '' else None
            flow = ep_strs[4] if ep_strs[4] != '' else 0
            vt = ep_strs[8] if ep_strs[8] != '' else 'Balanced'
            pressure = ep_strs[9] if ep_strs[9] != '' else 0
            eff = ep_strs[10] if ep_strs[10] != '' else 1
            min_in_t = ep_strs[15] if ep_strs[15] != '' else -100
            max_in_t = ep_strs[17] if ep_strs[17] != '' else 100
            delta_t = ep_strs[19] if ep_strs[19] != '' else -100
            min_out_t = ep_strs[21] if ep_strs[21] != '' else -100
            max_out_t = ep_strs[23] if ep_strs[23] != '' else 100
        except IndexError:
            pass  # shorter IDF definition lacking specifications
        # extract the schedules from the string
        try:
            if sched is not None:
                sched = schedule_dict[sched]
        except KeyError as e:
            raise ValueError('Failed to find {} in the schedule_dict.'.format(e))
        control = VentilationControl(
            min_in_t, max_in_t, min_out_t, max_out_t, delta_t, sched)

        # return the fan object and the zone identifier for the fan object
        obj_id = ep_strs[0].split('..')[0]
        zone_id = ep_strs[2]
        fan = cls(obj_id, flow, vt, pressure, eff, control)
        return fan, zone_id

    @classmethod
    def from_dict(cls, data):
        """Create a VentilationFan from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'VentilationFan',
            "flow_rate": 1.0,
            "ventilation_type": "Exhaust",
            "pressure_rise": 200,
            "efficiency": 0.7,
            "control": {}  # dictionary of a VentilationControl
            }
        """
        assert data['type'] == 'VentilationFan', \
            'Expected VentilationFan. Got {}.'.format(data['type'])
        vt, pr, eff = cls._default_dict_values(data)
        ctrl = VentilationControl.from_dict(data['control']) \
            if 'control' in data and data['control'] is not None else None
        new_obj = cls(data['identifier'], data['flow_rate'], vt, pr, eff, ctrl)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        """Create a VentilationFan from an abridged dictionary.

        Args:
            data: A VentilationFanAbridged dictionary with the format below.
            schedule_dict: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values. These will be used to
                assign the schedule to the VentilationControl object.

        .. code-block:: python

            {
            "type": 'VentilationFanAbridged',
            "flow_rate": 1.0,
            "ventilation_type": "Exhaust",
            "pressure_rise": 200,
            "efficiency": 0.7,
            "control": {}  # dictionary of a VentilationControlAbridged
            }
        """
        assert data['type'] == 'VentilationFanAbridged', \
            'Expected VentilationFanAbridged. Got {}.'.format(data['type'])
        vt, pr, eff = cls._default_dict_values(data)
        ctrl = VentilationControl.from_dict_abridged(data['control'], schedule_dict) \
            if 'control' in data and data['control'] is not None else None
        new_obj = cls(data['identifier'], data['flow_rate'], vt, pr, eff, ctrl)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, zone_identifier):
        """IDF string representation of VentilationFan object.

        Note that this method does not return full definitions of the VentilationControl
        schedules and so this objects's schedules must also be translated into
        the final IDF file.

        Args:
            zone_identifier: Text for the zone identifier that the VentilationFan
                object is assigned to.
        """

        # process the properties on this object into IDF format
        cntrl = self.control
        values = (
            '{}..{}'.format(self.identifier, zone_identifier), zone_identifier,
            cntrl.schedule.identifier, 'Flow/Zone', self.flow_rate, '', '', '',
            self.ventilation_type, self.pressure_rise, self.efficiency, '1', '', '', '',
            cntrl.min_indoor_temperature, '', cntrl.max_indoor_temperature, '',
            cntrl.delta_temperature, '',
            cntrl.min_outdoor_temperature, '', cntrl.max_outdoor_temperature, '', 40)
        comments = (
            'name', 'zone name', 'schedule', 'flow calculation method',
            'flow rate {m3/s}', 'flow per floor {m3/s-m2}',
            'flow per person {m3/s-person}' 'flow ach', 'ventilation type',
            'fan pressure rise', 'fan  total efficiency', 'constant term',
            'temperature term', 'velocity term', 'velocity squared term',
            'min indoor temperature {C}', 'min in temp schedule',
            'max indoor temperature {C}', 'max in temp schedule',
            'delta temperature {C}', 'delta temp schedule',
            'min outdoor temperature {C}', 'min out temp schedule',
            'max outdoor temperature {C}', 'max out temp schedule', 'max wind speed')
        return generate_idf_string(
            'ZoneVentilation:DesignFlowRate', values, comments)

    def to_dict(self, abridged=False):
        """Ventilation Fan dictionary representation."""
        base = {'type': 'VentilationFan'} if not \
            abridged else {'type': 'VentilationFanAbridged'}
        base['identifier'] = self.identifier
        base['flow_rate'] = self.flow_rate
        base['ventilation_type'] = self.ventilation_type
        base['pressure_rise'] = self.pressure_rise
        base['efficiency'] = self.efficiency
        base['control'] = self.control.to_dict(abridged)
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def lock(self):
        """The lock() method will also lock the control."""
        self._locked = True
        self._control.lock()

    def unlock(self):
        """The unlock() method will also unlock the control."""
        self._locked = False
        self._control.unlock()

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _default_pressure_rise(self):
        """Calculate the pressure rise from the assigned flow rate."""
        if self._flow_rate < self.PRESSURE_RISES[0][0]:
            return self.PRESSURE_RISES[0][1]
        if self._flow_rate > self.PRESSURE_RISES[-1][0]:
            return self.PRESSURE_RISES[-1][1]
        for i, (flow, pr) in enumerate(self.PRESSURE_RISES):
            if flow <= self._flow_rate <= self.PRESSURE_RISES[i + 1][0]:
                f_num = self._flow_rate - flow
                f_denom = self.PRESSURE_RISES[i + 1][0] - flow
                f_dist = f_num / f_denom
                return pr + (f_dist * (self.PRESSURE_RISES[i + 1][1] - pr))

    def _default_efficiency(self):
        """Calculate the efficiency from the assigned flow rate and pressure rise."""
        pr_rise_ratio = self.pressure_rise / self._default_pressure_rise()
        eff_est = 0.8 - (pr_rise_ratio * 0.1)
        if eff_est > 0.7:
            return 0.7
        if eff_est < 0.15:
            return 0.15
        return eff_est

    @staticmethod
    def _default_dict_values(data):
        """Process dictionary values and include defaults for missing values."""
        vt = data['ventilation_type'] if 'ventilation_type' in data \
            and data['ventilation_type'] is not None else 'Balanced'
        pr = data['pressure_rise'] if 'pressure_rise' in data else None
        eff = data['efficiency'] if 'efficiency' in data else None
        return vt, pr, eff

    def __copy__(self):
        new_obj = VentilationFan(
            self._identifier, self._flow_rate, self._ventilation_type,
            self._pressure_rise, self._efficiency, self._control.duplicate())
        new_obj._display_name = self._display_name
        return new_obj

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.flow_rate, self.ventilation_type,
                self.pressure_rise, self.efficiency, hash(self.control))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, VentilationFan) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'VentilationFan: {}'.format(self.display_name)
