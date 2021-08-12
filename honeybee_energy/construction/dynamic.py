# coding=utf-8
"""Window Construction with any number of dynamic states."""
from __future__ import division

from .window import WindowConstruction
from ..material.glazing import EnergyWindowMaterialSimpleGlazSys
from ..schedule.dictutil import dict_to_schedule
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class WindowConstructionDynamic(object):
    """Window Construction with any number of dynamic states.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        constructions: A list of WindowConstruction objects that define the various
            states that the dynamic window can assume.
        schedule: A ScheduleRuleset or ScheduleFixedInterval composed of integers that
            corredpond to the indices of the constructions that are active at given
            times throughout the simulation.

    Properties:
        * identifier
        * display_name
        * constructions
        * schedule
        * materials
        * layers
        * unique_materials
        * r_value
        * u_value
        * u_factor
        * r_factor
        * is_symmetric
        * has_shade
        * inside_emissivity
        * outside_emissivity
        * thickness
        * glazing_count
        * gap_count
    """

    __slots__ = ('_identifier', '_display_name', '_constructions', '_schedule',
                 '_locked')

    def __init__(self, identifier, constructions, schedule):
        """Initialize dynamic window construction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.constructions = constructions
        self.schedule = schedule

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
        try:
            self._display_name = str(value)
        except UnicodeEncodeError:  # Python 2 machine lacking the character set
            self._display_name = value  # keep it as unicode

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

        The values of the schedule should be intergers and range from 0 to one
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
    def has_shade(self):
        """Get a boolean noting whether dynamic shade materials are in the construction.
        """
        # This is False for all construction types except WindowConstructionShade.
        return False

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
        return new_obj

    def to_idf(self):
        """IDF string representation of construction object.

        This is a placeholder and has not been implemented yet.
        """
        raise NotImplementedError(
            'WindowConstructionDynamic to_idf has not yet been implemented.')

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
