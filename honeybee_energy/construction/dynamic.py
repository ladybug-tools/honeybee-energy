# coding=utf-8
"""Window Construction with any number of dynamic states."""
from __future__ import division

import re

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string

from .window import WindowConstruction
from ..material.glazing import EnergyWindowMaterialSimpleGlazSys
from ..schedule.dictutil import dict_to_schedule
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..writer import generate_idf_string


@lockable
class WindowConstructionDynamic(object):
    """Window Construction with any number of dynamic states.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        constructions: A list of WindowConstruction objects that define the various
            states that the dynamic window can assume.
        schedule: A ScheduleRuleset or ScheduleFixedInterval composed of integers
            that correspond to the indices of the constructions that are active
            at given times throughout the simulation.

    Properties:
        * identifier
        * display_name
        * constructions
        * schedule
        * materials
        * layers
        * unique_materials
        * frame
        * r_value
        * u_value
        * u_factor
        * r_factor
        * is_symmetric
        * has_frame
        * has_shade
        * is_dynamic
        * inside_emissivity
        * outside_emissivity
        * solar_transmittance
        * visible_transmittance
        * shgc
        * thickness
        * glazing_count
        * gap_count
        * user_data
    """

    __slots__ = ('_identifier', '_display_name', '_constructions', '_schedule',
                 '_locked', '_user_data')

    def __init__(self, identifier, constructions, schedule):
        """Initialize dynamic window construction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.constructions = constructions
        self.schedule = schedule
        self._user_data = None

    @property
    def identifier(self):
        """Get or set the text string for construction identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(identifier, 'construction identifier')

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
    def constructions(self):
        """Get or set a list of WindowConstructions that define the dynamic states."""
        return self._constructions

    @constructions.setter
    def constructions(self, cons):
        try:
            if not isinstance(cons, tuple):
                cons = tuple(cons)
        except TypeError:
            raise TypeError('Expected list or tuple for WindowConstructionDynamic '
                            'constructions. Got {}'.format(type(cons)))
        for construct in cons:
            assert isinstance(construct, WindowConstruction), \
                'Expected WindowConstruction for WindowConstructionDynamic. ' \
                'Got {}.'.format(type(construct))
        assert len(cons) > 1, 'There must be at least two constructions ' \
            'for a WindowConstructionDynamic.'
        self._constructions = cons

    @property
    def schedule(self):
        """Get or set a control schedule for the constructions active at given time.

        The values of the schedule should be integers and range from 0 to one
        less then the number of constructions. Zero indicates that the first
        construction is active, one indicates that the second on is active, etc.
        The schedule type limits of this schedule should be "Discrete" and the unit
        type should be "Mode," "Control," or some other fractional unit.
        """
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
            'Expected schedule for window construction shaded schedule. ' \
            'Got {}.'.format(type(value))
        if value.schedule_type_limit is not None:
            assert value.schedule_type_limit.numeric_type == 'Discrete', 'Dynamic ' \
                'window construction schedule should have a Discrete type limit. ' \
                'Got a schedule of numeric_type [{}].'.format(
                    value.schedule_type_limit.numeric_type)
            assert value.schedule_type_limit.unit == 'fraction', 'Dynamic window ' \
                'construction schedule should have Mode or Control unit types. ' \
                'Got a schedule of unit_type [{}].'.format(
                    value.schedule_type_limit.unit_type)
        value.lock()  # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def materials(self):
        """Get a list of materials for the constituent constructions.

        Materials will be listed from outside to inside and will move from the first
        construction to the last.
        """
        return [m for con in self._constructions for m in con.materials]

    @property
    def layers(self):
        """Get a list of material identifiers for the constituent constructions.

        Materials will be listed from outside to inside and will move from the first
        construction to the last.
        """
        return [mat.identifier for mat in self.materials]

    @property
    def unique_materials(self):
        """A list of only unique material objects in the construction.

        This will include the materials across all dynamic states of the construction.
        """
        return list(set([m for con in self._constructions for m in con.materials]))

    @property
    def frame(self):
        """Get a window frame for the frame material surrounding the construction."""
        return self._constructions[0].frame

    @property
    def r_value(self):
        """R-value of the first window construction [m2-K/W] (excluding air films)."""
        return self._constructions[0].r_value

    @property
    def u_value(self):
        """U-value of the first window construction [W/m2-K] (excluding air films)."""
        return self._constructions[0].u_value

    @property
    def r_factor(self):
        """First window construction R-factor [m2-K/W] (with standard air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        return self._constructions[0].r_factor

    @property
    def u_factor(self):
        """First window construction U-factor [W/m2-K] (with standard air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        return self._constructions[0].u_factor

    @property
    def solar_transmittance(self):
        """The solar transmittance of the first window construction at normal incidence.
        """
        return self._constructions[0].solar_transmittance

    @property
    def visible_transmittance(self):
        """Visible transmittance of the first window construction at normal incidence.
        """
        return self._constructions[0].visible_transmittance

    @property
    def shgc(self):
        """The solar heat gain coefficient (SHGC) of the first window construction."""
        return self._constructions[0].shgc

    @property
    def is_symmetric(self):
        """Get a boolean for whether all of the construction layers are symmetric.

        Symmetric means that the materials in reversed order are equal to those
        in the current order (eg. 'Glass', 'Air Gap', 'Glass'). This is particularly
        helpful for interior constructions, which need to have matching materials
        in reversed order between adjacent Faces.
        """
        for con in self._constructions:
            mats = con.materials
            half_mat = int(len(mats) / 2)
            for i in range(half_mat):
                if mats[i] != mats[-(i + 1)]:
                    return False
        return True

    @property
    def has_frame(self):
        """Get a boolean noting whether the construction has a frame assigned to it."""
        return self._constructions[0].has_frame

    @property
    def has_shade(self):
        """Get a boolean noting whether dynamic shade materials are in the construction.
        """
        # This is False for all construction types except WindowConstructionShade.
        return False

    @property
    def is_dynamic(self):
        """Get a boolean noting whether the construction is dynamic.

        This will always be True for this class.
        """
        return True

    @property
    def inside_emissivity(self):
        """"The emissivity of the inside face of the first construction."""
        mats = self._constructions[0].materials
        if isinstance(mats[-1], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        try:
            return mats[-1].emissivity_back
        except AttributeError:
            return mats[-1].emissivity

    @property
    def outside_emissivity(self):
        """"The emissivity of the outside face of the first construction."""
        mats = self._constructions[0].materials
        if isinstance(mats[0], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        return mats[0].emissivity

    @property
    def thickness(self):
        """Thickness of the first construction [m]."""
        return self._constructions[0].thickness

    @property
    def glazing_count(self):
        """The number of glazing materials contained within the first construction."""
        return self._constructions[0].glazing_count

    @property
    def gap_count(self):
        """The number of gas gaps contained within the first construction."""
        return self._constructions[0].gap_count

    @property
    def inside_material(self):
        """The the inside material layer of the first construction.

        Useful for checking that an asymmetric construction is correctly assigned.
        """
        mats = self._constructions[0].materials
        return mats[-1]

    @property
    def outside_material(self):
        """The the outside material layer of the first construction.

        Useful for checking that an asymmetric construction is correctly assigned.
        """
        mats = self._constructions[0].materials
        return mats[0]

    @property
    def user_data(self):
        """Get or set an optional dictionary for additional meta data for this object.

        This will be None until it has been set. All keys and values of this
        dictionary should be of a standard Python type to ensure correct
        serialization of the object to/from JSON (eg. str, float, int, list, dict)
        """
        if self._user_data is not None:
            return self._user_data

    @user_data.setter
    def user_data(self, value):
        if value is not None:
            assert isinstance(value, dict), 'Expected dictionary for honeybee_energy' \
                'object user_data. Got {}.'.format(type(value))
        self._user_data = value

    @classmethod
    def from_dict(cls, data):
        """Create a WindowConstructionDynamic from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'WindowConstructionDynamic',
            "identifier": 'Double Pane Electrochromic 0.4-0.12',
            "display_name": 'Electrochromic Window',
            "constructions": [],  # a list of WindowConstruction dictionaries
            "schedule": {}  # a ScheduleRuleset or ScheduleFixedInterval dictionary
            }
        """
        # check the type
        assert data['type'] == 'WindowConstructionDynamic', \
            'Expected WindowConstructionDynamic. Got {}.'.format(data['type'])
        # re-serialize the inputs
        constrs = [WindowConstruction.from_dict(c_dict)
                   for c_dict in data['constructions']]
        schedule = dict_to_schedule(data['schedule'])
        # create the object
        new_obj = cls(data['identifier'], constrs, schedule)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, materials, schedules):
        """Create a WindowConstructionDynamic from an abridged dictionary.

        Args:
            data: An WindowConstructionDynamic dictionary with the format below.
            materials: A dictionary with identifiers of materials as keys and
                Python material objects as values.
            schedules: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values.

        .. code-block:: python

            {
            "type": 'WindowConstructionDynamicAbridged',
            "identifier": 'Double Pane Electrochromic 0.4-0.12',
            "display_name": 'Electrochromic Window',
            "constructions": [],  # a list of WindowConstructionAbridged dictionaries
            "schedule": 'DayNight_Schedule'  # a schedule identifier
            }
        """
        # check the type
        assert data['type'] == 'WindowConstructionDynamicAbridged', \
            'Expected WindowConstructionDynamicAbridged. Got {}.'.format(data['type'])
        # re-serialize the inputs
        constrs = [WindowConstruction.from_dict_abridged(c_dict, materials)
                   for c_dict in data['constructions']]
        schedule = schedules[data['schedule']]
        # create the object
        new_obj = cls(data['identifier'], constrs, schedule)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """Get an IDF string representation of this construction object.

        Note that writing this string is not enough to add everything needed for
        the construction to the IDF. The construction's materials also have to
        be added as well as the schedule. The to_program_idf method must also
        be called in order to add the EMS program that controls the constructions.

        Returns:
            Text string that includes the following EnergyPlus objects.

            -   Construction definitions for each state

            -   The EMS Construction Index Variable object for each state

            -   The EMS Sensor linked to the schedule

        """
        idf_strs = []
        # add all of the construction definitions and EMS states
        state_com = ('name', 'construction name')
        for i, con in enumerate(self.constructions):
            con_dup = con.duplicate()
            con_dup.identifier = '{}State{}'.format(con.identifier, i)
            idf_strs.append(con_dup.to_idf())
            state_id = 'State{}{}'.format(i, re.sub('[^A-Za-z0-9]', '', con.identifier))
            vals = [state_id, con_dup.identifier]
            state_str = generate_idf_string(
                'EnergyManagementSystem:ConstructionIndexVariable', vals, state_com)
            idf_strs.append(state_str)

        # add the EMS Sensor definition
        sensor_com = ('name', 'variable key name', 'variable name')
        sensor_id = 'Sensor{}'.format(re.sub('[^A-Za-z0-9]', '', self.identifier))
        sen_vals = [sensor_id, self.schedule.identifier, 'Schedule Value']
        sensor = generate_idf_string(
            'EnergyManagementSystem:Sensor', sen_vals, sensor_com)
        idf_strs.append(sensor)
        return '\n\n'.join(idf_strs)

    def to_program_idf(self, aperture_identifiers):
        """Get an IDF string representation of the EMS program.

        Args:
            aperture_identifiers: A list of Aperture identifiers to
                which this construction is assigned.

        Returns:
            Text string that includes the following EnergyPlus objects.

            -   The EMS Actuators linked to the apertures

            -   The EMS Program definition

        """
        idf_strs = []
        # add all of the actuators linked to the apertures
        act_com = ('name', 'component name', 'component type', 'component control')
        actuator_ids = []
        for i, ap_id in enumerate(aperture_identifiers):
            act_id = 'Actuator{}{}'.format(i, re.sub('[^A-Za-z0-9]', '', ap_id))
            act_vals = [act_id, ap_id, 'Surface', 'Construction State']
            actuator = generate_idf_string(
                'EnergyManagementSystem:Actuator', act_vals, act_com)
            actuator_ids.append(act_id)
            idf_strs.append(actuator)

        # add each construction state to the program
        pid = 'StateChange{}'.format(re.sub('[^A-Za-z0-9]', '', self.identifier))
        ems_program = [pid]
        sensor_id = 'Sensor{}'.format(re.sub('[^A-Za-z0-9]', '', self.identifier))
        max_state_count = len(self.constructions) - 1
        for i, con in enumerate(self.constructions):
            # determine which conditional operator to use
            cond_op = 'IF' if i == 0 else 'ELSEIF'
            # add the conditional statement
            state_count = i + 1
            if i == max_state_count:
                cond_stmt = 'ELSE'
            else:
                cond_stmt = '{} ({} < {})'.format(cond_op, sensor_id, state_count)
            ems_program.append(cond_stmt)
            # loop through the actuators and set the appropriate window state
            state_id = 'State{}{}'.format(i, re.sub('[^A-Za-z0-9]', '', con.identifier))
            for act_name in actuator_ids:
                ems_program.append('SET {} = {}'.format(act_name, state_id))
        ems_program.append('ENDIF')
        ems_prog_str = generate_idf_string('EnergyManagementSystem:Program', ems_program)
        idf_strs.append(ems_prog_str)
        return '\n\n'.join(idf_strs)

    @staticmethod
    def idf_program_manager(constructions):
        """Get an IDF string representation of the EMS program calling manager.

        Args:
            constructions: A list of WindowConstructionDynamic objects to be written
                into a program manager.
        """
        man_com = ['name', 'calling point']
        man_vals = ['Dynamic_Window_Constructions', 'BeginTimestepBeforePredictor']
        for i, con in enumerate(constructions):
            pid = 'StateChange{}'.format(re.sub('[^A-Za-z0-9]', '', con.identifier))
            man_vals.append(pid)
            man_com.append('program name{}'.format(i))
        manager = generate_idf_string(
            'EnergyManagementSystem:ProgramCallingManager', man_vals, man_com)
        return manager

    def to_radiance_solar(self):
        """Honeybee Radiance material for the first construction."""
        # TODO: add methods that can represent the dynamic window behavior
        return self._constructions[0].to_radiance_solar()

    def to_radiance_visible(self):
        """Honeybee Radiance material for the first construction."""
        # TODO: add methods that can represent the dynamic window behavior
        return self._constructions[0].to_radiance_visible()

    def to_dict(self, abridged=False):
        """Window construction dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of material layers and
                schedules. (Default: False).
        """
        base = {'type': 'WindowConstructionDynamic'} if not \
            abridged else {'type': 'WindowConstructionDynamicAbridged'}
        base['identifier'] = self.identifier
        base['constructions'] = [con.to_dict(abridged) for con in self.constructions]
        base['schedule'] = self.schedule.identifier if abridged \
            else self.schedule.to_dict()
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def lock(self):
        """The lock() method will also lock the constructions."""
        self._locked = True
        for mat in self.constructions:
            mat.lock()

    def unlock(self):
        """The unlock() method will also unlock the constructions."""
        self._locked = False
        for mat in self.constructions:
            mat.unlock()

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def __copy__(self):
        new_con = WindowConstructionDynamic(
            self.identifier, self.constructions, self.schedule)
        new_con._display_name = self._display_name
        new_con.user_data = None if self._user_data is None else self._user_data.copy()
        return new_con

    def __len__(self):
        return len(self._constructions)

    def __getitem__(self, key):
        return self._constructions[key]

    def __iter__(self):
        return iter(self._constructions)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self._identifier, hash(self.schedule)) + \
            tuple(hash(con) for con in self.constructions)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, WindowConstructionDynamic) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'WindowConstructionDynamic: [{} states]'.format(len(self.constructions))
