# coding=utf-8
"""Glazing materials representing panes of glass within window constructions.

They can exist anywhere within a window construction as long as they are not adjacent
to other glazing materials.
The one exception to this is the EnergyWindowMaterialSimpleGlazSys, which is meant to
represent an entire window assembly (including glazing, gaps, and frame), and
therefore must be the only material in its parent construction.
"""
from __future__ import division

from ._base import _EnergyMaterialWindowBase
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive


@lockable
class _EnergyWindowMaterialGlazingBase(_EnergyMaterialWindowBase):
    """Base for all glazing layers."""
    __slots__ = ()

    @property
    def is_glazing_material(self):
        """Boolean to note whether the material is a glazing layer."""
        return True


@lockable
class EnergyWindowMaterialGlazing(_EnergyWindowMaterialGlazingBase):
    """A single glass pane corresponding to a layer in a window construction.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the glass layer [m].
            Default: 0.003 meters (3 mm).
        solar_transmittance: Number between 0 and 1 for the transmittance of solar
            radiation through the glass at normal incidence.
            Default: 0.85 for clear glass.
        solar_reflectance: Number between 0 and 1 for the reflectance of solar
            radiation off of the front side of the glass at normal incidence,
            averaged over the solar spectrum. Default: 0.075.
        visible_transmittance: Number between 0 and 1 for the transmittance of
            visible light through the glass at normal incidence.
            Default: 0.9 for clear glass.
        visible_reflectance: Number between 0 and 1 for the reflectance of
            visible light off of the front side of the glass at normal incidence.
            Default: 0.075.
        infrared_transmittance: Long-wave transmittance of the glass at normal
            incidence. Default: 0.
        emissivity: Number between 0 and 1 for the infrared hemispherical
            emissivity of the front side of the glass.  Default: 0.84, which
            is typical of clear glass.
        emissivity_back: Number between 0 and 1 for the infrared hemispherical
            emissivity of the back side of the glass.  Default: 0.84, which
            is typical of clear glass.
        conductivity: Number for the thermal conductivity of the glass [W/m-K].
            Default: 0.9.

    Properties:
        * identifier
        * display_name
        * thickness
        * solar_transmittance
        * solar_reflectance
        * solar_reflectance_back
        * visible_transmittance
        * visible_reflectance
        * visible_reflectance_back
        * infrared_transmittance
        * emissivity
        * emissivity_back
        * conductivity
        * dirt_correction
        * solar_diffusing
        * resistivity
        * u_value
        * r_value
    """
    __slots__ = ('_thickness', '_solar_transmittance', '_solar_reflectance',
                 '_solar_reflectance_back', '_visible_transmittance',
                 '_visible_reflectance', '_visible_reflectance_back',
                 '_infrared_transmittance', '_emissivity', '_emissivity_back',
                 '_conductivity', '_dirt_correction', '_dirt_correction',
                 '_solar_diffusing')

    def __init__(self, identifier, thickness=0.003, solar_transmittance=0.85,
                 solar_reflectance=0.075, visible_transmittance=0.9,
                 visible_reflectance=0.075, infrared_transmittance=0,
                 emissivity=0.84, emissivity_back=0.84, conductivity=0.9):
        """Initialize energy window material glazing."""
        _EnergyWindowMaterialGlazingBase.__init__(self, identifier)

        # default for checking transmittance + reflectance < 1
        self._solar_reflectance = 0
        self._solar_reflectance_back = None
        self._visible_reflectance = 0
        self._visible_reflectance_back = None

        self.thickness = thickness
        self.solar_transmittance = solar_transmittance
        self.solar_reflectance = solar_reflectance
        self.visible_transmittance = visible_transmittance
        self.visible_reflectance = visible_reflectance
        self.infrared_transmittance = infrared_transmittance
        self.emissivity = emissivity
        self.emissivity_back = emissivity_back
        self.conductivity = conductivity
        self.dirt_correction = 1.0
        self.solar_diffusing = False

    @property
    def thickness(self):
        """Get or set the thickess of the glass material layer [m]."""
        return self._thickness

    @thickness.setter
    def thickness(self, thick):
        self._thickness = float_positive(thick, 'glazing material thickness')

    @property
    def solar_transmittance(self):
        """Get or set the solar transmittance of the glass at normal incidence."""
        return self._solar_transmittance

    @solar_transmittance.setter
    def solar_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'glazing material solar transmittance')
        assert s_tr + self._solar_reflectance <= 1, 'Sum of window transmittance and ' \
            'reflectance ({}) is greater than 1.'.format(s_tr + self._solar_reflectance)
        if self._solar_reflectance_back is not None:
            assert s_tr + self._solar_reflectance_back <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_tr + self._solar_reflectance_back)
        self._solar_transmittance = s_tr

    @property
    def solar_reflectance(self):
        """Get or set the front solar reflectance of the glass at normal incidence."""
        return self._solar_reflectance

    @solar_reflectance.setter
    def solar_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'glazing material solar reflectance')
        assert s_ref + self._solar_transmittance <= 1, 'Sum of window transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                s_ref + self._solar_transmittance)
        self._solar_reflectance = s_ref

    @property
    def solar_reflectance_back(self):
        """Get or set the back solar reflectance of the glass at normal incidence."""
        return self._solar_reflectance_back if self._solar_reflectance_back is not None \
            else self._solar_reflectance

    @solar_reflectance_back.setter
    def solar_reflectance_back(self, s_ref):
        if s_ref is not None:
            s_ref = float_in_range(s_ref, 0.0, 1.0, 'glazing material solar reflectance')
            assert s_ref + self._solar_transmittance <= 1, 'Sum of window transmittance ' \
                'and reflectance ({}) is greater than 1.'.format(
                    s_ref + self._solar_transmittance)
        self._solar_reflectance_back = s_ref

    @property
    def visible_transmittance(self):
        """Get or set the visible transmittance of the glass at normal incidence."""
        return self._visible_transmittance

    @visible_transmittance.setter
    def visible_transmittance(self, v_tr):
        v_tr = float_in_range(v_tr, 0.0, 1.0, 'glazing material visible transmittance')
        assert v_tr + self._visible_reflectance <= 1, 'Sum of window transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                v_tr + self._visible_reflectance)
        if self._visible_reflectance_back is not None:
            assert v_tr + self._visible_reflectance_back <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    v_tr + self._visible_reflectance_back)
        self._visible_transmittance = v_tr

    @property
    def visible_reflectance(self):
        """Get or set the front visible reflectance of the glass at normal incidence."""
        return self._visible_reflectance

    @visible_reflectance.setter
    def visible_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'glazing material visible reflectance')
        assert v_ref + self._visible_transmittance <= 1, 'Sum of window transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                v_ref + self._visible_transmittance)
        self._visible_reflectance = v_ref

    @property
    def visible_reflectance_back(self):
        """Get or set the back visible reflectance of the glass at normal incidence."""
        return self._visible_reflectance_back if self._visible_reflectance_back \
            is not None else self._visible_reflectance

    @visible_reflectance_back.setter
    def visible_reflectance_back(self, v_ref):
        if v_ref is not None:
            v_ref = float_in_range(v_ref, 0.0, 1.0,
                                   'glazing material visible reflectance')
            assert v_ref + self._visible_transmittance <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    v_ref + self._visible_transmittance)
        self._visible_reflectance_back = v_ref

    @property
    def infrared_transmittance(self):
        """Get or set the infrared transmittance of the glass at normal incidence."""
        return self._infrared_transmittance

    @infrared_transmittance.setter
    def infrared_transmittance(self, ir_tr):
        self._infrared_transmittance = float_in_range(
            ir_tr, 0.0, 1.0, 'glazing material infrared transmittance')

    @property
    def emissivity(self):
        """Get or set the hemispherical emissivity of the front side of the glass."""
        return self._emissivity

    @emissivity.setter
    def emissivity(self, ir_e):
        ir_e = float_in_range(ir_e, 0.0, 1.0, 'glazing material emissivity')
        self._emissivity = ir_e

    @property
    def emissivity_back(self):
        """Get or set the hemispherical emissivity of the back side of the glass."""
        return self._emissivity_back if self._emissivity_back is not None \
            else self._emissivity

    @emissivity_back.setter
    def emissivity_back(self, ir_e):
        if ir_e is not None:
            ir_e = float_in_range(ir_e, 0.0, 1.0, 'glazing material emissivity')
        self._emissivity_back = ir_e

    @property
    def conductivity(self):
        """Get or set the conductivity of the glazing layer [W/m-K]."""
        return self._conductivity

    @conductivity.setter
    def conductivity(self, cond):
        self._conductivity = float_positive(cond, 'glazing material conductivity')

    @property
    def dirt_correction(self):
        """Get or set the hemispherical emissivity of the back side of the glass."""
        return self._dirt_correction

    @dirt_correction.setter
    def dirt_correction(self, dirt):
        self._dirt_correction = float_in_range(
            dirt, 0.0, 1.0, 'glazing material dirt correction')

    @property
    def solar_diffusing(self):
        """Get or set the solar diffusing property of the glass."""
        return self._solar_diffusing

    @solar_diffusing.setter
    def solar_diffusing(self, s_diff):
        self._solar_diffusing = bool(s_diff)

    @property
    def resistivity(self):
        """Get or set the resistivity of the glazing layer [m-K/W]."""
        return 1 / self._conductivity

    @resistivity.setter
    def resistivity(self, resis):
        self._conductivity = 1 / float_positive(resis, 'glazing material resistivity')

    @property
    def u_value(self):
        """Get or set the U-value of the material layer [W/m2-K] (excluding air films).

        Note that, when setting the R-value, the thickness of the material will
        remain fixed and only the conductivity will be adjusted.
        """
        return self.conductivity / self.thickness

    @u_value.setter
    def u_value(self, u_val):
        self.r_value = 1 / float_positive(u_val, 'glazing material u-value')

    @property
    def r_value(self):
        """Get or set the R-value of the material [m2-K/W] (excluding air films).

        Note that, when setting the R-value, the thickness of the material will
        remain fixed and only the conductivity will be adjusted.
        """
        return self.thickness / self.conductivity

    @r_value.setter
    def r_value(self, r_val):
        self._conductivity = self.thickness / \
            float_positive(r_val, 'glazing material r-value')

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialGlazing from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_s = parse_idf_string(idf_string, 'WindowMaterial:Glazing,')
        idf_defaults = {10: 0, 11: 0.84, 12: 0.84, 13: 0.9, 14: 1.0, 15: 'No'}
        for i, ep_str in enumerate(ep_s):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_s[i] = idf_defaults[i]

        assert ep_s[1] == 'SpectralAverage', \
            'Expected SpectralAverage glazing type. Got {}.'.format(ep_s[1])
        new_mat = cls(ep_s[0], ep_s[3], ep_s[4], ep_s[5], ep_s[7], ep_s[8],
                      ep_s[10], ep_s[11], ep_s[12], ep_s[13])
        new_mat.solar_reflectance_back = ep_s[6]
        new_mat.visible_reflectance_back = ep_s[9]
        new_mat.dirt_correction = ep_s[14] if len(ep_s) > 14 else 1.0
        if len(ep_s) > 15:
            new_mat.solar_diffusing = False if ep_s[15] == 'No' else True
        return new_mat

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialGlazing from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowMaterialGlazing',
            "identifier": 'Lowe_Glazing_00030_045_090',
            "display_name": 'Low-e Glazing',
            "thickness": 0.003,
            "solar_transmittance": 0.45,
            "solar_reflectance": 0.36,
            "visible_transmittance": 0.714,
            "visible_reflectance": 0.207,
            "infrared_transmittance": 0,
            "emissivity": 0.84,
            "emissivity_back": 0.0466,
            "conductivity": 0.9
            }
        """
        assert data['type'] == 'EnergyWindowMaterialGlazing', \
            'Expected EnergyWindowMaterialGlazing. Got {}.'.format(data['type'])

        thick = data['thickness'] if 'thickness' in data and data['thickness'] \
            is not None else 0.003
        t_sol = data['solar_transmittance'] if 'solar_transmittance' in data and \
            data['solar_transmittance'] is not None else 0.85
        r_sol = data['solar_reflectance'] if 'solar_reflectance' in data and \
            data['solar_reflectance'] is not None else 0.075
        r_sol_b = data['solar_reflectance_back'] if 'solar_reflectance_back' \
            in data else None
        t_vis = data['visible_transmittance'] if 'visible_transmittance' in data and \
            data['visible_transmittance'] is not None else 0.9
        r_vis = data['visible_reflectance'] if 'visible_reflectance' in data and \
            data['visible_reflectance'] is not None else 0.075
        r_vis_b = data['visible_reflectance_back'] if 'visible_reflectance_back' \
            in data else None
        t_inf = data['infrared_transmittance'] if 'infrared_transmittance' in data and \
            data['infrared_transmittance'] is not None else 0.0
        emis = data['emissivity'] if 'emissivity' in data and \
            data['emissivity'] is not None else 0.84
        emis_b = data['emissivity_back'] if 'emissivity_back' in data and \
            data['emissivity_back'] is not None else 0.84
        cond = data['conductivity'] if 'conductivity' in data and \
            data['conductivity'] is not None else 0.9
        dirt = data['dirt_correction'] if 'dirt_correction' in data and \
            data['dirt_correction'] is not None else 1.0
        sol_diff = data['solar_diffusing'] if 'solar_diffusing' in data and \
            data['solar_diffusing'] is not None else False

        new_mat = cls(data['identifier'], thick, t_sol, r_sol, t_vis, r_vis,
                      t_inf, emis, emis_b, cond)
        new_mat.solar_reflectance_back = r_sol_b
        new_mat.visible_reflectance_back = r_vis_b
        new_mat.dirt_correction = dirt
        new_mat.solar_diffusing = sol_diff
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        solar_diffusing = 'Yes' if self.solar_diffusing is True else 'No'
        values = (self.identifier, 'SpectralAverage', '',
                  self.thickness, self.solar_transmittance,
                  self.solar_reflectance, self.solar_reflectance_back,
                  self.visible_transmittance, self.visible_reflectance,
                  self.visible_reflectance_back, self.infrared_transmittance,
                  self.emissivity, self.emissivity_back, self.conductivity,
                  self.dirt_correction, solar_diffusing)
        comments = ('name', 'optical data type', 'spectral data set name',
                    'thickness {m}', 'solar transmittance', 'solar reflectance front',
                    'solar reflectance back', 'visible transmittance',
                    'visible reflectance front', 'visible reflectance back',
                    'infrared_transmittance', 'emissivity front', 'emissivity back',
                    'conductivity {W/m-K}', 'dirt correction factor',
                    'solar diffusing')
        return generate_idf_string('WindowMaterial:Glazing', values, comments)

    def to_dict(self):
        """Energy Window Material Glazing dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialGlazing',
            'identifier': self.identifier,
            'thickness': self.thickness,
            'solar_transmittance': self.solar_transmittance,
            'solar_reflectance': self.solar_reflectance,
            'solar_reflectance_back': self.solar_reflectance_back,
            'visible_transmittance': self.visible_transmittance,
            'visible_reflectance': self.visible_reflectance,
            'visible_reflectance_back': self.visible_reflectance_back,
            'infrared_transmittance': self.infrared_transmittance,
            'emissivity': self.emissivity,
            'emissivity_back': self.emissivity_back,
            'conductivity': self.conductivity,
            'dirt_correction': self.dirt_correction,
            'solar_diffusing': self.solar_diffusing
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.thickness, self.solar_transmittance,
                self.solar_reflectance, self.solar_reflectance_back,
                self.visible_transmittance, self.visible_reflectance,
                self.visible_reflectance_back, self.infrared_transmittance,
                self.emissivity, self.emissivity_back, self.conductivity,
                self.dirt_correction, self.solar_diffusing)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialGlazing) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = EnergyWindowMaterialGlazing(
            self.identifier, self.thickness, self.solar_transmittance,
            self.solar_reflectance, self.visible_transmittance, self.visible_reflectance,
            self.infrared_transmittance, self.emissivity, self._emissivity_back,
            self.conductivity)
        new_material._solar_reflectance_back = self._solar_reflectance_back
        new_material._visible_reflectance_back = self._visible_reflectance_back
        new_material._dirt_correction = self._dirt_correction
        new_material._solar_diffusing = self._solar_diffusing
        new_material._display_name = self._display_name
        return new_material


@lockable
class EnergyWindowMaterialSimpleGlazSys(_EnergyWindowMaterialGlazingBase):
    """A material to describe an entire glazing system, including glass, gaps, and frame.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        u_factor: A number for the U-factor of the glazing system [W/m2-K]
            including standard air gap resistances on either side of the system.
        shgc: A number between 0 and 1 for the solar heat gain coefficient
            of the glazing system. This includes both directly transmitted solar
            heat as well as solar heat that is absorbed by the glazing system and
            conducts towards the interior.
        vt: A number between 0 and 1 for the visible transmittance of the
            glazing system. Default: 0.6.

    Properties:
        * identifier
        * display_name
        * u_factor
        * shgc
        * vt
        * r_factor
        * u_value
        * r_value
    """
    __slots__ = ('_u_factor', '_shgc', '_vt')
    _film_resistance = (1 / 23) + (1 / 8)  # interior + exterior films resistance

    def __init__(self, identifier, u_factor, shgc, vt=0.6):
        """Initialize energy window material simple glazing system."""
        _EnergyWindowMaterialGlazingBase.__init__(self, identifier)
        self.u_factor = u_factor
        self.shgc = shgc
        self.vt = vt

    @property
    def u_factor(self):
        """Get or set the glazing system U-factor (including air film resistance)."""
        return self._u_factor

    @u_factor.setter
    def u_factor(self, u_fac):
        # NOTE: u-values above 5.8 are not usually realistic but 12 is used as a hard limit
        self._u_factor = float_in_range(u_fac, 0.0, 12, 'glazing material u-factor')

    @property
    def r_factor(self):
        """Get or set the glazing system R-factor (including air film resistance)."""
        return 1 / self._u_factor

    @r_factor.setter
    def r_factor(self, r_fac):
        self._u_factor = 1 / float_positive(r_fac, 'glazing material r-factor')

    @property
    def shgc(self):
        """Get or set the glazing system solar heat gain coefficient (SHGC)."""
        return self._shgc

    @shgc.setter
    def shgc(self, sc):
        self._shgc = float_in_range(sc, 0.0, 1.0, 'glazing material shgc')

    @property
    def vt(self):
        """Get or set the visible transmittance."""
        return self._vt

    @vt.setter
    def vt(self, vt):
        self._vt = float_in_range(vt, 0.0, 1.0, 'glazing material visible transmittance')

    @property
    def u_value(self):
        """U-value of the material layer [W/m2-K] (excluding air film resistance)."""
        return 1 / self.r_value

    @property
    def r_value(self):
        """R-value of the material layer [m2-K/W] (excluding air film resistance)."""
        return (1 / self.u_factor) - self._film_resistance

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialSimpleGlazSys from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'WindowMaterial:SimpleGlazingSystem,')
        idf_defaults = {3: 0.6}
        for i, ep_str in enumerate(ep_strs):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_strs[i] = idf_defaults[i]
        return cls(*ep_strs)

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialSimpleGlazSys from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowMaterialSimpleGlazSys',
            "identifier": 'Double_Lowe_Glazing_200_040_060',
            "display_name": 'Double Low-e Glazing System',
            "u_factor": 2.0,
            "shgc": 0.4,
            "vt": 0.6
            }
        """
        assert data['type'] == 'EnergyWindowMaterialSimpleGlazSys', \
            'Expected EnergyWindowMaterialSimpleGlazSys. Got {}.'.format(data['type'])
        vt = 0.6 if 'vt' not in data else data['vt']
        new_obj = cls(data['identifier'], data['u_factor'], data['shgc'], vt)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.u_factor, self.shgc, self.vt)
        comments = ('name', 'u-factor {W/m2-K}', 'shgc', 'vt')
        return generate_idf_string(
            'WindowMaterial:SimpleGlazingSystem', values, comments)

    def to_dict(self):
        """Energy Window Material Simple Glazing System dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialSimpleGlazSys',
            'identifier': self.identifier,
            'u_factor': self.u_factor,
            'shgc': self.shgc,
            'vt': self.vt
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.u_factor, self.shgc, self.vt)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialSimpleGlazSys) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = EnergyWindowMaterialSimpleGlazSys(
            self.identifier, self.u_factor, self.shgc, self.vt)
        new_material._display_name = self._display_name
        return new_material
