# coding=utf-8
"""Window Construction with shades/blinds or a dynamically-controlled glass pane."""
from __future__ import division

from .window import WindowConstruction
from ..material.dictutil import dict_to_material
from ..material.glazing import EnergyWindowMaterialGlazing, \
    EnergyWindowMaterialSimpleGlazSys
from ..material.shade import _EnergyWindowMaterialShadeBase, EnergyWindowMaterialBlind
from ..schedule.dictutil import dict_to_schedule
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.fixedinterval import ScheduleFixedInterval
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string


@lockable
class WindowConstructionShade(object):
    """Window Construction with shades/blinds or a dynamically-controlled glass pane.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        window_construction: A WindowConstruction object that serves as the
            "switched off" version of the construction (aka. the "bare construction").
            The shade_material and shade_location will be used to modify this
            starting construction.
        shade_material: An EnergyWindowMaterialShade or an EnergyWindowMaterialBlind
            that serves as the shading layer for this construction. This can also
            be an EnergyWindowMaterialGlazing, which will indicate that the
            WindowConstruction has a dynamically-controlled glass pane like an
            electrochromic window assembly.
        shade_location: Text to indicate where in the window assembly the shade_material
            is located. (Default: "Interior"). Choose from the following 3 options:

                * Interior
                * Between
                * Exterior

            Note that the WindowConstruction must have at least one gas gap to use
            the "Between" option. Also note that, for a WindowConstruction with more
            than one gas gap, the "Between" option defalts to using the inner gap
            as this is the only option that EnergyPlus supports.
        control_type: Text to indicate how the shading device is controlled, which
             determines when the shading is “on” or “off.” (Default: "AlwaysOn").
             Choose from the options below (units for the values of the corresponding
             setpoint are noted in parentheses next to each option):

                * AlwaysOn
                * OnIfHighSolarOnWindow (W/m2)
                * OnIfHighHorizontalSolar (W/m2)
                * OnIfHighOutdoorAirTemperature (C)
                * OnIfHighZoneAirTemperature (C)
                * OnIfHighZoneCooling (W)
                * OnNightIfLowOutdoorTempAndOffDay (C)
                * OnNightIfLowInsideTempAndOffDay (C)
                * OnNightIfHeatingAndOffDay (W)

        setpoint: A number that corresponds to the specified control_type. This can
            be a value in (W/m2), (C) or (W) depending upon the control type.
        schedule: An optional ScheduleRuleset or ScheduleFixedInterval to be applied
            on top of the control_type. If None, the control_type will govern all
            behavior of the construction.

    Properties:
        * identifier
        * display_name
        * window_construction
        * shade_material
        * shade_location
        * control_type
        * setpoint
        * schedule
        * materials
        * layers
        * unique_materials
        * r_value
        * u_value
        * u_factor
        * r_factor
        * is_symmetric
        * is_switchable_glazing
        * has_shade
        * inside_emissivity
        * outside_emissivity
        * thickness
        * glazing_count
        * gap_count
        * user_data
    """

    __slots__ = ('_identifier', '_display_name', '_window_construction',
                 '_shade_material', '_shade_location', '_control_type',
                 '_setpoint', '_schedule', '_between_gap', '_locked', '_user_data')
    SHADE_LOCATIONS = ('Interior', 'Between', 'Exterior')
    CONTROL_TYPES = (
        'AlwaysOn', 'OnIfHighSolarOnWindow', 'OnIfHighHorizontalSolar',
        'OnIfHighOutdoorAirTemperature', 'OnIfHighZoneAirTemperature',
        'OnIfHighZoneCooling', 'OnNightIfLowOutdoorTempAndOffDay',
        'OnNightIfLowInsideTempAndOffDay', 'OnNightIfHeatingAndOffDay')

    def __init__(self, identifier, window_construction, shade_material,
                 shade_location='Interior', control_type='AlwaysOn',
                 setpoint=None, schedule=None):
        """Initialize shaded window construction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self._between_gap = None  # will be used if 'Between' option is used
        self._user_data = None
        # check that the window construction, shade, and shade location are compatible
        assert isinstance(window_construction, WindowConstruction), \
            'Expected WindowConstruction for WindowConstructionShade. ' \
            'Got {}.'.format(type(window_construction))
        shade_types = (_EnergyWindowMaterialShadeBase, EnergyWindowMaterialGlazing)
        assert isinstance(shade_material, shade_types), \
            'Expected Shade/Blind or Glazing material for WindowConstructionShade. ' \
            'Got {}.'.format(type(shade_material))
        assert shade_location in self.SHADE_LOCATIONS, \
            'Invalid input "{}" for shade location.  Must be one ' \
            'of the following:\n{}'.format(shade_location, self.SHADE_LOCATIONS)
        if isinstance(shade_material, EnergyWindowMaterialGlazing):
            ext_pane = window_construction[0]
            assert not isinstance(ext_pane, EnergyWindowMaterialSimpleGlazSys), \
                'WindowConstruction cannot be a SimpleGlazSys when shading material ' \
                'is a glass pane.'
        elif shade_location == 'Between':  # it's a shade/blind between glass panes
            assert window_construction.gap_count >= 1, 'WindowConstruction must have ' \
                'at least one gap in order to use "Between" shade_location.'
            # calculate the thickness of the gaps on either side of the shade
            int_gap = window_construction[-2]
            if isinstance(shade_material, EnergyWindowMaterialBlind):
                assert shade_material.slat_width < int_gap.thickness, \
                    'Blind slat_width must be less than the width of the gap in which ' \
                    'it sits. {} > {}.'.format(
                        shade_material.slat_width, int_gap.thickness)
            shd_thick = 0 if isinstance(shade_material, EnergyWindowMaterialBlind) \
                else shade_material.thickness
            gap_thick = (int_gap.thickness - shd_thick) / 2
            assert gap_thick > 0, \
                'Shade thickness is greater than the gap in which it sits.'
            # create the split gap material to be used on either side of the shade
            between_int_gap = int_gap.duplicate()
            between_int_gap.identifier = \
                '{}_Split{}'.format(int_gap.identifier, round(gap_thick, 4))
            between_int_gap.thickness = gap_thick
            self._between_gap = between_int_gap
        window_construction.lock()  # lock to avoid illegal shade/material combinations
        self._window_construction = window_construction
        self._shade_material = shade_material
        self._shade_location = shade_location

        # assign the control type, setpoint and schedule
        assert control_type in self.CONTROL_TYPES, \
            'Invalid input "{}" for shading control type.' \
            ' Must be one of the following:\n{}'.format(control_type, self.CONTROL_TYPES)
        self._control_type = control_type
        self.setpoint = setpoint
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
    def window_construction(self):
        """Get the WindowConstruction serving as the "switched off" version."""
        return self._window_construction

    @property
    def shade_material(self):
        """Get the material that serves as the shading layer for this construction."""
        return self._shade_material

    @property
    def shade_location(self):
        """Get text to indicate where in the construction the shade_material is located.

        This will be either "Interior", "Between" or "Exterior". Note that, for a
        WindowConstruction with more than one gas gap, the "Between" option defalts
        to using the inner gap as this is the only option that EnergyPlus supports.
        """
        return self._shade_location

    @property
    def control_type(self):
        """Get or set the text indicating how the shading device is controlled.

        Choose from the options below:

        * AlwaysOn
        * OnIfHighSolarOnWindow
        * OnIfHighHorizontalSolar
        * OnIfHighOutdoorAirTemperature
        * OnIfHighZoneAirTemperature
        * OnIfHighZoneCooling
        * OnNightIfLowOutdoorTempAndOffDay
        * OnNightIfLowInsideTempAndOffDay
        * OnNightIfHeatingAndOffDay
        """
        return self._control_type

    @control_type.setter
    def control_type(self, value):
        assert value in self.CONTROL_TYPES, \
            'Invalid input "{}" for shading control type.' \
            ' Must be one of the following:\n{}'.format(value, self.CONTROL_TYPES)
        if value != 'AlwaysOn':
            assert self._setpoint is not None, 'Control setpoint must not ' \
                'be None to use "{}" control type.'.format(value)
        self._control_type = value

    @property
    def setpoint(self):
        """A number for the setpoint that corresponds to the specified control_type.

        This can be a value in (W/m2), (C) or (W) depending upon the control type.
        """
        return self._setpoint

    @setpoint.setter
    def setpoint(self, value):
        if value is not None:
            try:
                value = float(value)
            except (ValueError, TypeError):
                raise TypeError('Input setpoint must be a number. Got '
                                '{}: {}.'.format(type(value), value))
        else:
            assert self._control_type == 'AlwaysOn', 'Control setpoint cannot ' \
                'be None for control type "{}"'.format(self._control_type)
        self._setpoint = value

    @property
    def schedule(self):
        """Get or set a fractional schedule to be applied on top of the control_type.

        If None, the control_type will govern all behavior of the construction.
        """
        return self._schedule

    @schedule.setter
    def schedule(self, value):
        if value is not None:
            assert isinstance(value, (ScheduleRuleset, ScheduleFixedInterval)), \
                'Expected schedule for window construction shaded schedule. ' \
                'Got {}.'.format(type(value))
            if value.schedule_type_limit is not None:
                assert value.schedule_type_limit.unit == 'fraction', 'Window ' \
                    'construction schedule should be fractional. Got a schedule ' \
                    'of unit_type [{}].'.format(value.schedule_type_limit.unit_type)
            value.lock()  # lock editing in case schedule has multiple references
        self._schedule = value

    @property
    def materials(self):
        """Get the list of materials in the construction (outside to inside).

        This will include the shade material layer in its correct position.
        """
        base_mats = list(self._window_construction.materials)
        if self.is_switchable_glazing:
            if self._shade_location == 'Interior':
                base_mats[-1] = self._shade_material
            elif self._shade_location == 'Exterior' or \
                    self._window_construction.gap_count == 0:
                base_mats[0] = self._shade_material
            else:  # middle glass pane
                base_mats[-3] = self._shade_material
        else:
            if self._shade_location == 'Interior':
                base_mats.append(self._shade_material)
            elif self._shade_location == 'Exterior':
                base_mats.insert(0, self._shade_material)
            else:  # between glass shade/blind
                base_mats[-2] = self._between_gap
                base_mats.insert(-1, self._shade_material)
                base_mats.insert(-1, self._between_gap)
        return base_mats

    @property
    def layers(self):
        """Get a list of material identifiers in the construction (outside to inside).

        This will include the shade material layer in its correct position.
        """
        return [mat.identifier for mat in self.materials]

    @property
    def unique_materials(self):
        """Get a list of only unique material objects in the construction.

        This will include the shade material layer. It will include both types of glass
        layers if the consruction is a switchable glazing.
        """
        if self.is_switchable_glazing:
            return list(set(
                self._window_construction.materials + (self.shade_material,)))
        return list(set(self.materials))

    @property
    def r_value(self):
        """R-value of the bare window construction [m2-K/W] (excluding air films).

        Note that this excludes all effects of the shade layer.
        """
        return self._window_construction.r_value

    @property
    def u_value(self):
        """U-value of the bare window construction [W/m2-K] (excluding air films).

        Note that this excludes all effects of the shade layer.
        """
        return self._window_construction.u_value

    @property
    def r_factor(self):
        """Bare window construction R-factor [m2-K/W] (with standard air film resistances).

        Note that this excludes all effects of the shade layer.
        Formulas for film coefficients come from EN673 / ISO10292.
        """
        return self._window_construction.r_factor

    @property
    def u_factor(self):
        """Bare window construction U-factor [W/m2-K] (with standard air film resistances).

        Note that this excludes all effects of the shade layer.
        Formulas for film coefficients come from EN673 / ISO10292.
        """
        return self._window_construction.u_factor

    @property
    def solar_transmittance(self):
        """The solar transmittance of the bare window construction at normal incidence.

        Note that this excludes all effects of the shade layer.
        """
        return self._window_construction.solar_transmittance

    @property
    def visible_transmittance(self):
        """The visible transmittance of the bare window construction at normal incidence.

        Note that this excludes all effects of the shade layer.
        """
        return self._window_construction.visible_transmittance

    @property
    def shgc(self):
        """The solar heat gain coefficient (SHGC) of the bare window construction.

        Note that this excludes all effects of the shade layer.
        """
        return self._window_construction.shgc

    @property
    def is_symmetric(self):
        """Get a boolean for whether the construction layers are symmetric.

        Symmetric means that the materials in reversed order are equal to those
        in the current order (eg. 'Glass', 'Air Gap', 'Glass'). This is particularly
        helpful for interior constructions, which need to have matching materials
        in reversed order between adjacent Faces.
        """
        mats = self.materials
        half_mat = int(len(mats) / 2)
        for i in range(half_mat):
            if mats[i] != mats[-(i + 1)]:
                return False
        return True

    @property
    def has_shade(self):
        """Get a boolean noting whether dynamic materials are in the construction.

        This should always be True for this class.
        """
        return True

    @property
    def is_switchable_glazing(self):
        """Get a boolean to note whether the construction is switchable glazing.

        The construction is a switchable glazing if the shade material is a
        glass material.
        """
        return isinstance(self.shade_material, EnergyWindowMaterialGlazing)

    @property
    def switched_glass_material(self):
        """Get material replaced by shade glass when construction is switchable glazing.

        This can be used to comapre the properties of the glass layer replaced by
        the shade glass. Will be None if the construction is not a switchable glazing.
        """
        if not self.is_switchable_glazing:
            return None
        base_mats = self._window_construction.materials
        if self._shade_location == 'Interior':
            return self.base_mats[-1]
        elif self._shade_location == 'Exterior' or \
                self._window_construction.gap_count == 0:
            return base_mats[0]
        else:  # middle glass pane
            return base_mats[-3]

    @property
    def inside_emissivity(self):
        """"The emissivity of the inside face of the construction.

        This will use the emissivity of the shade layer if it is interior.
        """
        mats = self.materials
        if isinstance(mats[-1], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        try:
            return mats[-1].emissivity_back
        except AttributeError:
            return mats[-1].emissivity

    @property
    def outside_emissivity(self):
        """"The emissivity of the outside face of the construction.

        This will use the emissivity of the shade layer if it is interior.
        """
        mats = self.materials
        if isinstance(mats[0], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        return mats[0].emissivity

    @property
    def thickness(self):
        """Thickness of the construction [m], excluding the shade layer.

        This is effectively the thickness that EnergyPlus assumes.
        """
        return self._window_construction.thickness

    @property
    def glazing_count(self):
        """The number of glazing materials contained within the construction.

        Note that Simple Glazing System materials do not count.
        """
        return self._window_construction.glazing_count

    @property
    def gap_count(self):
        """The number of gas gaps contained within the construction."""
        count = self._window_construction.gap_count
        if self.shade_location == 'Between' and not self.is_switchable_glazing:
            count += 1
        return count

    @property
    def _ep_shading_type(self):
        """Text for the Shading Type field that EnergyPlus wants in the IDF."""
        if self.is_switchable_glazing:
            return 'SwitchableGlazing'
        elif isinstance(self.shade_material, EnergyWindowMaterialBlind):
            return 'BetweenGlassBlind' if self.shade_location == 'Between' \
                else '{}Blind'.format(self.shade_location)
        else:
            return 'BetweenGlassShade' if self.shade_location == 'Between' \
                else '{}Shade'.format(self.shade_location)

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
        """Create a WindowConstructionShade from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'WindowConstructionShade',
            "identifier": 'Double Pane U-250 IntBlind-0025',
            "display_name": 'Double Pane with Interior Blind',
            "window_construction": {}  # a WindowConstruction dictionary representation
            "shade_material": {}  # a shade/blind/glass dictionary representation
            "shade_location": 'Interior',  # text for shade layer location
            "control_type": 'OnIfHighSolarOnWindow',  # text for shade control type
            "setpoint": 200,  # number for control setpoint
            "schedule": {}  # optional ScheduleRuleset or ScheduleFixedInterval dict
            }
        """
        # check the type
        assert data['type'] == 'WindowConstructionShade', \
            'Expected WindowConstructionShade. Got {}.'.format(data['type'])

        # re-serialize required inputs
        window_constr = WindowConstruction.from_dict(data['window_construction'])
        shade_material = dict_to_material(data['shade_material'])

        # re-serialize optional inputs
        shade_location, control_type, setpoint = cls._from_dict_defaults(data)
        schedule = dict_to_schedule(data['schedule']) if 'schedule' in data and \
            data['schedule'] is not None else None

        new_obj = cls(data['identifier'], window_constr, shade_material, shade_location,
                      control_type, setpoint, schedule)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, materials, schedules):
        """Create a WindowConstructionShade from an abridged dictionary.

        Args:
            data: An WindowConstructionShade dictionary with the format below.
            materials: A dictionary with identifiers of materials as keys and
                Python material objects as values.
            schedules: A dictionary with schedule identifiers as keys and
                honeybee schedule objects as values.

        .. code-block:: python

            {
            "type": 'WindowConstructionShadeAbridged',
            "identifier": 'Double Pane U-250 IntBlind-0025',
            "display_name": 'Double Pane with Interior Blind',
            "window_construction": {}  # a WindowConstructionAbridged dictionary
            "shade_material": 'Blind-0025'  # a shade/blind/glass identifier
            "shade_location": 'Interior',  # text for shade layer location
            "control_type": 'OnIfHighSolarOnWindow',  # text for shade control type
            "setpoint": 200,  # number for control setpoint
            "schedule": 'DayNight_Schedule'  # optional schedule identifier
            }
        """
        # check the type
        assert data['type'] == 'WindowConstructionShadeAbridged', \
            'Expected WindowConstructionShadeAbridged. Got {}.'.format(data['type'])

        # re-serialize required inputs
        window_constr = WindowConstruction.from_dict_abridged(
            data['window_construction'], materials)
        shade_material = materials[data['shade_material']]

        # re-serialize optional inputs
        shade_location, control_type, setpoint = cls._from_dict_defaults(data)
        schedule = schedules[data['schedule']] if 'schedule' in data and \
            data['schedule'] is not None else None

        new_obj = cls(data['identifier'], window_constr, shade_material, shade_location,
                      control_type, setpoint, schedule)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """IDF string representation of construction object.

        Note that this method only outputs a single string for the bare window
        construction and, to write the full construction into an IDF, the
        construction's unique_materials must also be written along with the
        output of to_idf_shaded, which contains the shaded construction.
        Also, for each Aperture to which this construction is assigned, a
        ShadingControl object must also be written, which can be obtained from
        the to_idf_shading_control.

        Returns:
            Text string representation of the bare (unshaded) construction.
        """
        return self._window_construction.to_idf()

    def to_shaded_idf(self):
        """IDF string representation of construction in its shaded state.

        Returns:
            Text string representation of the shaded construction.
        """
        materials = self.materials
        values = (self.identifier,) + tuple(mat.identifier for mat in materials)
        comments = ('name',) + tuple('layer %s' % (i + 1) for i in range(len(materials)))
        return generate_idf_string('Construction', values, comments)

    def to_shading_control_idf(self, aperture_identifier, room_identifier):
        """IDF string representation of a WindowShadingControl object.

        This has to be written for every Aperture to which this construction is
        assigned in order for EnergyPlus to simulate it correctly.

        Args:
            aperture_identifier: The identifier of the honeybee Aperture to
                which this construction is assigned.
            room_identifier: The identifier of the honeybee Room to which the
                aperture belongs.

        Returns:
            Text string representation of the WindowShadingControl.
        """
        control_name = '{}_ShdControl'.format(aperture_identifier)
        control_type = 'OnIfScheduleAllows' if self.schedule is not None and \
            self.control_type == 'AlwaysOn' else self.control_type
        sch = self.schedule.identifier if self.schedule is not None else ''
        sch_bool = 'Yes' if self.schedule is not None else 'No'
        setpt = self.setpoint if self.setpoint is not None else ''
        values = (control_name, room_identifier, 1, self._ep_shading_type,
                  self.identifier, control_type, sch, setpt, sch_bool,
                  '', '', '', '', '', '', '', aperture_identifier)
        comments = \
            ('name', 'zone name', 'sequence number', 'shading type',
             'construction with shade', 'control type', 'schedule', 'setpoint',
             'is scheduled', 'is glare controlled', 'shade material', 'slat control',
             'slat schedule', 'setpoint 2', 'daylight object', 'multiple control type',
             'fenestration surface')
        return generate_idf_string('WindowShadingControl', values, comments)

    def to_radiance_solar(self):
        """Honeybee Radiance material for the bare (unshaded) construction."""
        # TODO: add method that represents blinds with BSDF + shades with Trans
        return self._window_construction.to_radiance_solar()

    def to_radiance_visible(self):
        """Honeybee Radiance material for the bare (unshaded) construction."""
        # TODO: add method that represents blinds with BSDF + shades with Trans
        return self._window_construction.to_radiance_visible()

    def to_dict(self, abridged=False):
        """Window construction dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of material layers and
                schedules. (Default: False).
        """
        base = {'type': 'WindowConstructionShade'} if not \
            abridged else {'type': 'WindowConstructionShadeAbridged'}
        base['identifier'] = self.identifier
        base['window_construction'] = self.window_construction.to_dict(abridged)
        base['shade_material'] = self.shade_material.identifier if abridged \
            else self.shade_material.to_dict()
        base['shade_location'] = self.shade_location
        base['control_type'] = self.control_type
        if self.control_type != 'AlwaysOn':
            base['setpoint'] = self.setpoint
        if self.schedule is not None:
            base['schedule'] = self.schedule.identifier if abridged \
                else self.schedule.to_dict()
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def lock(self):
        """The lock() method will also lock the shade_material."""
        self._locked = True
        self.shade_material.lock()

    def unlock(self):
        """The unlock() method will also unlock the shade_material."""
        self._locked = False
        self.shade_material.unlock()

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    @staticmethod
    def _from_dict_defaults(data):
        "Re-serialize default values from a dictionary."
        shade_location = data['shade_location'] if 'shade_location' in data and \
            data['shade_location'] is not None else 'Interior'
        control_type = data['control_type'] if 'control_type' in data and \
            data['control_type'] is not None else 'AlwaysOn'
        setpoint = data['setpoint'] if 'setpoint' in data \
            else None
        return shade_location, control_type, setpoint

    def __copy__(self):
        new_con = WindowConstructionShade(
            self.identifier, self.window_construction, self.shade_material,
            self.shade_location, self.control_type, self.setpoint,
            self.schedule)
        new_con._between_gap = self._between_gap
        new_con._display_name = self._display_name
        new_con._user_data = None if self._user_data is None else self._user_data.copy()
        return new_con

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        sch = hash(self.schedule) if self.schedule is not None else None
        return (self._identifier, hash(self.window_construction),
                hash(self.shade_material), self.shade_location, self.control_type,
                self.setpoint, sch)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, WindowConstructionShade) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return self.to_shaded_idf()
