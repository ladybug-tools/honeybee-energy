# coding=utf-8
"""Photovoltaic properties that can be applied to Shades."""
from __future__ import division

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string, valid_string, float_in_range

from ..reader import parse_idf_string
from ..writer import generate_idf_string


@lockable
class PVProperties(object):
    """Simple Photovoltaic properties that run using PVWatts to estimate electricity.

    Args:
        identifier: Text string for PV properties identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        rated_efficiency: A number between 0 and 1 for the rated nameplate efficiency
            of the photovoltaic solar cells under standard test conditions (STC).
            Standard test conditions are 1,000 Watts per square meter solar
            irradiance, 25 degrees C cell temperature, and ASTM G173-03 standard
            spectrum. Nameplate efficiencies reported by manufacturers are typically
            under STC. Standard poly- or mono-crystalline silicon modules tend to have
            rated efficiencies in the range of 14-17%. Premium high efficiency
            mono-crystalline silicon modules with anti-reflective coatings can have
            efficiencies in the range of 18-20%. Thin film photovoltaic modules
            typically have efficiencies of 11% or less. (Default: 0.15 for standard
            silicon solar cells).
        active_area_fraction: The fraction of the parent Shade geometry that is
            covered in active solar cells. This fraction includes the difference
            between the PV panel (aka. PV module) area and the active cells within
            the panel as well as any losses for how the (typically rectangular) panels
            can be arranged on the Shade geometry. When the parent Shade geometry
            represents just the solar panels, this fraction is typically around 0.9
            given that the metal framing elements of the panel reduce the overall
            active area. (Default: 0.9, assuming parent Shade geometry represents
            only the PV panel geometry).
        module_type: Text to indicate the type of solar module. This is used to
            determine the temperature coefficients used in the simulation of the
            photovoltaic modules. Choose from the three options below. If None,
            the module_type will be inferred from the rated_efficiency of these
            PVProperties using the rated efficiencies listed below. (Default: None).

            * Standard - 12% <= rated_efficiency < 18%
            * Premium - rated_efficiency >= 18%
            * ThinFilm - rated_efficiency < 12%

        mounting_type: Text to indicate the type of mounting and/or tracking used
            for the photovoltaic array. Note that the OneAxis options have an axis
            of rotation that is determined by the azimuth of the parent Shade
            geometry. Also note that, in the case of one or two axis tracking,
            shadows on the (static) parent Shade geometry still reduce the
            electrical output, enabling the simulation to account for large
            context geometry casting shadows on the array. However, the effects
            of smaller detailed shading may be improperly accounted for and self
            shading of the dynamic panel geometry is only accounted for via the
            tracking_ground_coverage_ratio property on this object. Choose from
            the following. (Default: FixedOpenRack).

            * FixedOpenRack - ground or roof mounting where the air flows freely 
            * FixedRoofMounted - mounting flush with the roof with limited air flow
            * OneAxis - a fixed tilt and azimuth, which define an axis of rotation
            * OneAxisBacktracking - same as OneAxis but with controls to reduce self-shade
            * TwoAxis - a dynamic tilt and azimuth that track the sun

        system_loss_fraction: A number between 0 and 1 for the fraction of the
            electricity output lost due to factors other than EPW climate conditions,
            panel efficiency/type, active area, mounting, and inverter conversion from
            DC to AC. Factors that should be accounted for in this input include
            soiling, snow, wiring losses, electrical connection losses, manufacturer
            defects/tolerances/mismatch in cell characteristics, losses from power
            grid availability, and losses due to age or light-induced degradation.
            Losses from these factors tend to be between 10-20% but can vary widely
            depending on the installation, maintenance and the grid to which the
            panels are connected. The loss_fraction_from_components staticmethod
            on this class can be used to estimate this value from the various
            factors that it is intended to account for. (Default: 0.14).
        tracking_ground_coverage_ratio: A number between 0 and 1 that only applies to
            arrays with one-axis tracking mounting_type. The ground coverage ratio (GCR)
            is the ratio of module surface area to the area of the ground beneath
            the array, which is used to account for self shading of single-axis panels
            as they move to track the sun. A GCR of 0.5 means that, when the modules
            are horizontal, half of the surface below the array is occupied by
            the array. An array with wider spacing between rows of modules has a
            lower GCR than one with narrower spacing. A GCR of 1 would be for an
            array with no space between modules, and a GCR of 0 for infinite spacing
            between rows. Typical values range from 0.3 to 0.6. (Default: 0.4).
    """
    __slots__ = (
        '_identifier', '_display_name', '_rated_efficiency', '_active_area_fraction',
        '_module_type', '_mounting_type', '_system_loss_fraction',
        '_tracking_ground_coverage_ratio', '_locked')
    MODULE_TYPES = ('Standard', 'Premium', 'ThinFilm')
    MOUNTING_TYPES = ('FixedOpenRack', 'FixedRoofMounted', 'OneAxis',
                      'OneAxisBacktracking', 'TwoAxis')

    def __init__(self, identifier, rated_efficiency=0.15, active_area_fraction=0.9,
                 module_type=None, mounting_type='FixedOpenRack',
                 system_loss_fraction=0.14, tracking_ground_coverage_ratio=0.4):
        """Initialize PVProperties."""
        # set the identifier and display name
        self.identifier = identifier
        self._display_name = None

        # set the main features of the PV
        self.rated_efficiency = rated_efficiency
        self.active_area_fraction = active_area_fraction
        self.module_type = module_type
        self.mounting_type = mounting_type
        self.system_loss_fraction = system_loss_fraction
        self.tracking_ground_coverage_ratio = tracking_ground_coverage_ratio

    @property
    def identifier(self):
        """Get or set the text string for PV properties system identifier."""
        return self._identifier

    @identifier.setter
    def identifier(self, identifier):
        self._identifier = valid_ep_string(
            identifier, 'photovoltaic properties identifier')

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
    def rated_efficiency(self):
        """Get or set a number for the rated nameplate efficiency of the solar cells.

        Standard poly- or mono-crystalline silicon modules tend to have rated
        efficiencies in the range of 14-17%.

        Premium high efficiency mono-crystalline silicon modules with anti-reflective
        coatings can have efficiencies in the range of 18-20%.

        Thin film photovoltaic modules typically have efficiencies of 11% or less.
        """
        return self._rated_efficiency

    @rated_efficiency.setter
    def rated_efficiency(self, value):
        self._rated_efficiency = float_in_range(
            value, 0.0, 1.0, 'photovoltaic rated efficiency')

    @property
    def module_type(self):
        """Get or set text to indicate the type of photovoltaic module.

        Choose from the following options:

        * Standard
        * Premium
        * ThinFilm
        """
        if self._module_type is None:
            if self.rated_efficiency < 0.12:
                return 'ThinFilm'
            elif self.rated_efficiency < 0.18:
                return 'Standard'
            return 'Premium'
        return self._module_type

    @module_type.setter
    def module_type(self, value):
        if value is not None:
            clean_input = valid_string(value).lower()
            for key in self.MODULE_TYPES:
                if key.lower() == clean_input:
                    value = key
                    break
            else:
                raise ValueError(
                    'PVProperties.module_type {} is not recognized.\nChoose from the '
                    'following:\n{}'.format(value, self.MODULE_TYPES))
        self._module_type = value

    @property
    def mounting_type(self):
        """Get or set text to indicate the way the photovoltaic arrays are mounted.

        Choose from the following options:

        * FixedOpenRack
        * FixedRoofMounted
        * OneAxis
        * OneAxisBacktracking
        * TwoAxis
        """
        return self._mounting_type

    @mounting_type.setter
    def mounting_type(self, value):
        clean_input = valid_string(value).lower()
        for key in self.MOUNTING_TYPES:
            if key.lower() == clean_input:
                value = key
                break
        else:
            raise ValueError(
                'PVProperties.mounting_type {} is not recognized.\nChoose from the '
                'following:\n{}'.format(value, self.MOUNTING_TYPES))
        self._mounting_type = value

    @property
    def system_loss_fraction(self):
        """Get or set a number for the fraction of the output lost due to other factors.
        
        Factors that should be accounted for in this input include soiling, snow,
        wiring losses, electrical connection losses, manufacturer defects/tolerances/
        mismatch in cell characteristics, losses from power grid availability,
        and losses due to age or light-induced degradation.
        """
        return self._system_loss_fraction

    @system_loss_fraction.setter
    def system_loss_fraction(self, value):
        self._system_loss_fraction = float_in_range(
            value, 0.0, 1.0, 'photovoltaic system loss fraction')

    @property
    def tracking_ground_coverage_ratio(self):
        """Get or set a number between 0 and 1 for the ground coverage ratio.
        
        This value only applies to systems using single-axis tracking and is
        used to account for self shading of single-axis panels as they move
        to track the sun.
        """
        return self._tracking_ground_coverage_ratio

    @tracking_ground_coverage_ratio.setter
    def tracking_ground_coverage_ratio(self, value):
        self._tracking_ground_coverage_ratio = float_in_range(
            value, 0.0, 1.0, 'photovoltaic tracking ground coverage ratio')

    @classmethod
    def from_idf(cls, idf_string, shade, active_area_fraction=0.9):
        """Create a PVProperties object from a Generator:PVWatts IDF text string.

        Note that the Generator:PVWatts idf_string must use the 'surface' array
        geometry type in order to be successfully imported.

        Args:
            idf_string: A text string fully describing an EnergyPlus Generator:PVWatts
                definition.
            shade: The Honeybee Shade object to which the PV properties are assigned.
                Note that the geometry of this Shade must be in meters for the
                object to be loaded correctly.
            active_area_fraction: The original active area fraction used to construct
                the PVProperties object. This is needed to correctly derive
                the PV efficiency from the system capacity.

        Returns:
            A PVProperties object from the IDF string.
        """
        # check the inputs
        ep_strs = parse_idf_string(idf_string, 'Generator:PVWatts,')
        # check the inputs
        assert len(ep_strs) >= 9, 'PVProperties must use Surface array geometry ' \
            'type to be loaded from IDF to honeybee.'
        assert ep_strs[9].upper() == shade.identifier.upper(), 'Generator:PVWatts ' \
            'surface "{}" is different from the assigned Shade "{}".'.format(
                ep_strs[9].upper(), shade.identifier.upper())
        # extract the properties from the string
        watts_per_area = float(ep_strs[2]) / shade.area 
        eff = (watts_per_area / active_area_fraction) / 1000
        loss = 0.14
        gcr = 0.4
        try:
            loss = ep_strs[5] if ep_strs[5] != '' else 0.14
            gcr = ep_strs[10] if ep_strs[10] != '' else 0.4
        except IndexError:
            pass  # shorter definition lacking ground coverage ratio

        # return the PV properties object
        obj_id = ep_strs[0].split('..')[0]
        return cls(obj_id, eff, active_area_fraction, ep_strs[3], ep_strs[4], loss, gcr)

    @classmethod
    def from_dict(cls, data):
        """Create a PVProperties object from a dictionary.

        Args:
            data: A PVProperties dictionary in following the format below.

        .. code-block:: python

            {
            "type": "PVProperties",
            "identifier": "Ablytek 270 W Monocrystalline",  # identifier for the PV
            "display_name": "Ablytek Module",  # name for the PV
            "rated_efficiency": 0.18,  # Nameplate rated efficiency
            "active_area_fraction": 0.92,  # Active area fraction
            "module_type": "Standard",  # Type of solar module
            "mounting_type": "FixedOpenRack",  # Type of mounting and tracking
            "system_loss_fraction": 0.16  # Fraction lost to outside factors
            }
        """
        assert data['type'] == 'PVProperties', \
            'Expected PVProperties dictionary. Got {}.'.format(data['type'])

        # extract the key features and properties while setting defaults
        eff = data['rated_efficiency'] if 'rated_efficiency' in data and \
            data['rated_efficiency'] is not None else 0.15
        act = data['active_area_fraction'] if 'active_area_fraction' in data and \
            data['active_area_fraction'] is not None else 0.9
        mod_type = data['module_type'] if 'module_type' in data and \
            data['module_type'] is not None else 'Standard'
        mount = data['mounting_type'] if 'mounting_type' in data and \
            data['mounting_type'] is not None else 'FixedOpenRack'
        loss = data['system_loss_fraction'] if 'system_loss_fraction' in data and \
            data['system_loss_fraction'] is not None else 0.14
        gcr = data['tracking_ground_coverage_ratio'] \
            if 'tracking_ground_coverage_ratio' in data and \
            data['tracking_ground_coverage_ratio'] is not None else 0.4

        new_obj = cls(data['identifier'], eff, act, mod_type, mount, loss, gcr)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self, shade):
        """IDF string representation of PVProperties object.

        Args:
            shade: A Honeybee Shade for which the specific IDF string will
                be generated. Note that the geometry of this shade must be in
                meters in order for the returned IDF string to have correct values.
        """
        # compte the system capacity and other factors from the shade
        idf_id = '{}..{}'.format(self.identifier, shade.identifier)
        rated_watts = self.rated_efficiency * 1000  # 1000W/m2 of solar irradiance
        sys_cap = int(shade.area * self.active_area_fraction * rated_watts)
        # write the IDF string
        values = (idf_id, '', sys_cap, self.module_type, self.mounting_type,
                  self.system_loss_fraction, 'Surface', '', '', shade.identifier,
                  self.tracking_ground_coverage_ratio)
        comments = (
            'PV generator name', 'PVWatts version', 'DC system capacity {W}',
            'module type', 'array type', 'system losses', 'array geometry type',
            'tilt angle {deg}', 'azimuth angle {deg}', 'surface name',
            'ground coverage ratio')
        return generate_idf_string('Generator:PVWatts', values, comments)

    def to_dict(self):
        """PVProperties dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of schedules. (Default: False).
        """
        base = {'type': 'PVProperties'}
        base['identifier'] = self.identifier
        base['rated_efficiency'] = self.rated_efficiency
        base['active_area_fraction'] = self.active_area_fraction
        base['module_type'] = self.module_type
        base['mounting_type'] = self.mounting_type
        base['system_loss_fraction'] = self.system_loss_fraction
        if self.mounting_type in ('OneAxis', 'OneAxisBacktracking') or \
                self.tracking_ground_coverage_ratio != 0.4:
            base['tracking_ground_coverage_ratio'] = self.tracking_ground_coverage_ratio
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.rated_efficiency, self.active_area_fraction,
                self.module_type, self.mounting_type, self.system_loss_fraction,
                self.tracking_ground_coverage_ratio)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, PVProperties) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_obj = PVProperties(
            self.identifier, self._rated_efficiency, self._active_area_fraction,
                self._module_type, self._mounting_type, self._system_loss_fraction,
                self._tracking_ground_coverage_ratio)
        new_obj._display_name = self._display_name
        return new_obj

    def __repr__(self):
        return 'PVProperties: {} [efficiency {}%]'.format(
            self.display_name, round(self.rated_efficiency, 1))
