# coding=utf-8
"""Shade materials representing shades, blinds, or screens in a window construction.

They can exist in only one of three possible locations in a window construction:

1) On the innermost material layer.
2) On the outermost material layer.
3) In between two glazing materials. In the case of window constructions with
   multiple glazing surfaces, the shade material must be between the two
   inner glass layers.

Note that shade materials should never be bounded by gas gap layers in honeybee-energy.
"""
from __future__ import division

from ._base import _EnergyMaterialWindowBase
from .gas import EnergyWindowMaterialGas
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive


@lockable
class _EnergyWindowMaterialShadeBase(_EnergyMaterialWindowBase):
    """Base for all shade material layers."""
    __slots__ = ('_infrared_transmittance', '_emissivity', '_distance_to_glass',
                 '_top_opening_multiplier', '_bottom_opening_multiplier',
                 '_left_opening_multiplier', '_right_opening_multiplier')

    def __init__(self, identifier, infrared_transmittance=0, emissivity=0.9,
                 distance_to_glass=0.05, opening_multiplier=0.5):
        """Initialize base shade energy material."""
        _EnergyMaterialWindowBase.__init__(self, identifier)
        self.infrared_transmittance = infrared_transmittance
        self.emissivity = emissivity
        self.distance_to_glass = distance_to_glass
        self.set_all_opening_multipliers(opening_multiplier)
        

    @property
    def is_shade_material(self):
        """Boolean to note whether the material is a shade layer."""
        return True

    @property
    def infrared_transmittance(self):
        """Get or set the infrared transmittance of the shade."""
        return self._infrared_transmittance

    @infrared_transmittance.setter
    def infrared_transmittance(self, ir_tr):
        self._infrared_transmittance = float_in_range(
            ir_tr, 0.0, 1.0, 'shade material infrared transmittance')

    @property
    def emissivity(self):
        """Get or set the hemispherical emissivity of the shade."""
        return self._emissivity

    @emissivity.setter
    def emissivity(self, ir_e):
        ir_e = float_in_range(ir_e, 0.0, 1.0, 'shade material emissivity')
        self._emissivity = ir_e

    @property
    def distance_to_glass(self):
        """Get or set the shade distance to the glass [m]."""
        return self._distance_to_glass

    @distance_to_glass.setter
    def distance_to_glass(self, dist):
        self._distance_to_glass = float_in_range(
            dist, 0.001, 1.0, 'shade material distance to glass')

    @property
    def top_opening_multiplier(self):
        """Get or set the top opening multiplier."""
        return self._top_opening_multiplier

    @top_opening_multiplier.setter
    def top_opening_multiplier(self, multiplier):
        self._top_opening_multiplier = float_in_range(
            multiplier, 0.0, 1.0, 'shade material opening multiplier')

    @property
    def bottom_opening_multiplier(self):
        """Get or set the bottom opening multiplier."""
        return self._bottom_opening_multiplier

    @bottom_opening_multiplier.setter
    def bottom_opening_multiplier(self, multiplier):
        self._bottom_opening_multiplier = float_in_range(
            multiplier, 0.0, 1.0, 'shade material opening multiplier')

    @property
    def left_opening_multiplier(self):
        """Get or set the left opening multiplier."""
        return self._left_opening_multiplier

    @left_opening_multiplier.setter
    def left_opening_multiplier(self, multiplier):
        self._left_opening_multiplier = float_in_range(
            multiplier, 0.0, 1.0, 'shade material opening multiplier')

    @property
    def right_opening_multiplier(self):
        """Get or set the right opening multiplier."""
        return self._right_opening_multiplier

    @right_opening_multiplier.setter
    def right_opening_multiplier(self, multiplier):
        self._right_opening_multiplier = float_in_range(
            multiplier, 0.0, 1.0, 'shade material opening multiplier')

    @property
    def r_value(self):
        """R-value of the material layer [m2-K/W] (excluding air film resistance)."""
        return 0

    def set_all_opening_multipliers(self, multiplier):
        """Set all opening multipliers to the same value at once."""
        self.top_opening_multiplier = multiplier
        self.bottom_opening_multiplier = multiplier
        self.left_opening_multiplier = multiplier
        self.right_opening_multiplier = multiplier

    def r_value_exterior(self, delta_t=7.5, emissivity=0.84, height=1.0, angle=90,
                         t_kelvin=273.15, pressure=101325):
        """Get an estimate of the R-value of the shade + air gap when it is exterior.

        Args:
            delta_t: The temperature difference across the air gap [C]. This
                influences how strong the convection is within the air gap. Default is
                7.5C, which is consistent with the NFRC standard for double glazed units.
            emissivity: The emissivity of the glazing surface adjacent to the shade.
                Default is 0.84, which is typical of clear, uncoated glass.
            height: An optional height for the cavity between the shade and the
                glass in meters. Default is 1.0.
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal surface with downward heat flow through the layer.
                * 90 = A vertical surface
                * 180 = A horizontal surface with upward heat flow through the layer.

            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average air pressure in Pa. Default is 101325 Pa for sea level.
        """
        # TODO: Account for air permeability and side openings in gap u-value.
        # https://bigladdersoftware.com/epx/docs/9-0/engineering-reference/
        # window-heat-balance-calculation.html#solving-for-gap-airflow-and-temperature
        _gap = EnergyWindowMaterialGas(
            identifier='Generic Shade Gap', thickness=self.distance_to_glass,
            gas_type='Air')
        try:
            _shade_e = self.emissivity_back
        except AttributeError:
            _shade_e = self.emissivity
        _r_gap = 1 / _gap.u_value_at_angle(delta_t, _shade_e, emissivity,
                                           height, angle, t_kelvin, pressure)
        return self.r_value + _r_gap

    def r_value_interior(self, delta_t=7.5, emissivity=0.84, height=1.0, angle=90,
                         t_kelvin=273.15, pressure=101325):
        """Get an estimate of the R-value of the shade + air gap when it is interior.

        Args:
            delta_t: The temperature difference across the air gap [C]. This
                influences how strong the convection is within the air gap. Default is
                7.5C, which is consistent with the NFRC standard for double glazed units.
            emissivity: The emissivity of the glazing surface adjacent to the shade.
                Default is 0.84, which is typical of clear, uncoated glass.
            height: An optional height for the cavity between the shade and the
                glass in meters. Default is 1.0.
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal surface with downward heat flow through the layer.
                * 90 = A vertical surface
                * 180 = A horizontal surface with upward heat flow through the layer.

            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average air pressure in Pa. Default is 101325 Pa for sea level.
        """
        # TODO: Account for air permeability and side openings in gap u-value.
        # https://bigladdersoftware.com/epx/docs/9-0/engineering-reference/
        # window-heat-balance-calculation.html#solving-for-gap-airflow-and-temperature
        _gap = EnergyWindowMaterialGas(
            identifier='Generic Shade Gap', thickness=self.distance_to_glass,
            gas_type='Air')
        _shade_e = self.emissivity
        _r_gap = 1 / _gap.u_value_at_angle(delta_t, _shade_e, emissivity,
                                           height, angle, t_kelvin, pressure)
        return self.r_value + _r_gap

    def r_value_between(self, delta_t=7.5, emissivity_1=0.84, emissivity_2=0.84,
                        height=1.0, angle=90, t_kelvin=273.15, pressure=101325):
        """Get an estimate of the R-value of the shade + air gap when it is interior.

        Args:
            delta_t: The temperature difference across the air gap [C]. This
                influences how strong the convection is within the air gap. Default is
                7.5C, which is consistent with the NFRC standard for double glazed units.
            emissivity_1: The emissivity of the glazing surface on one side of the shade.
                Default is 0.84, which is typical of clear, uncoated glass.
            emissivity_2: The emissivity of the glazing surface on the other side of
                the shade. Default is 0.84, which is typical of clear, uncoated glass.
            height: An optional height for the cavity between the shade and the
                glass in meters. Default is 1.0.
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal surface with downward heat flow through the layer.
                * 90 = A vertical surface
                * 180 = A horizontal surface with upward heat flow through the layer.

            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average air pressure in Pa. Default is 101325 Pa for sea level.
        """
        _gap = EnergyWindowMaterialGas(
            identifier='Generic Shade Gap', thickness=self.distance_to_glass,
            gas_type='Air')
        _shade_e = self.emissivity
        _r_gap_1 = 1 / _gap.u_value_at_angle(delta_t, _shade_e, emissivity_1,
                                             height, angle, t_kelvin, pressure)
        _r_gap_2 = 1 / _gap.u_value_at_angle(delta_t, _shade_e, emissivity_2,
                                             height, angle, t_kelvin, pressure)
        return self.r_value + _r_gap_1 + _r_gap_2


@lockable
class EnergyWindowMaterialShade(_EnergyWindowMaterialShadeBase):
    """A material for a shade layer in a window construction.

    Reflectance and emissivity properties are assumed to be the same on both sides of
    the shade. Shades are considered to be perfect diffusers.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the shade layer [m].
            Default: 0.005 meters (5 mm).
        solar_transmittance: Number between 0 and 1 for the transmittance
            of solar radiation through the shade.
            Default: 0.4, which is typical of a white diffusing shade.
        solar_reflectance: Number between 0 and 1 for the reflectance of solar
            radiation off of the shade, averaged over the solar spectrum.
            Default: 0.5, which is typical of a white diffusing shade.
        visible_transmittance: Number between 0 and 1 for the transmittance
            of visible light through the shade.
            Default: 0.4, which is typical of a white diffusing shade.
        visible_reflectance: Number between 0 and 1 for the reflectance of
            visible light off of the shade.
            Default: 0.4, which is typical of a white diffusing shade.
        infrared_transmittance: Long-wave hemispherical transmittance of the shade.
            Default: 0, which is typical of diffusing shades.
        emissivity: Number between 0 and 1 for the infrared hemispherical
            emissivity of the front side of the shade.  Default: 0.9, which
            is typical of most diffusing shade materials.
        conductivity: Number for the thermal conductivity of the shade [W/m-K].
            Default: 0.05, typical of cotton shades.
        distance_to_glass: A number between 0.001 and 1.0 for the distance
            between the shade and neighboring glass layers [m]. Default: 0.05 (50 mm).
        opening_multiplier: Factor between 0 and 1 that is multiplied by the
            area at the top, bottom and sides of the shade for air flow
            calculations. Default: 0.5.
        airflow_permeability: The fraction of the shade surface that is open to
            air flow. Must be between 0 and 0.8. Default: 0 for no permeability.

    Properties:
        * identifier
        * display_name
        * thickness
        * solar_transmittance
        * solar_reflectance
        * visible_transmittance
        * visible_reflectance
        * infrared_transmittance
        * emissivity
        * conductivity
        * distance_to_glass
        * top_opening_multiplier
        * bottom_opening_multiplier
        * left_opening_multiplier
        * right_opening_multiplier
        * airflow_permeability
        * resistivity
        * u_value
        * r_value
        * user_data
    """
    __slots__ = ('_thickness', '_solar_transmittance', '_solar_reflectance',
                 '_visible_transmittance', '_visible_reflectance',
                 '_conductivity', '_airflow_permeability')

    def __init__(self, identifier, thickness=0.005, solar_transmittance=0.4,
                 solar_reflectance=0.5,
                 visible_transmittance=0.4, visible_reflectance=0.4,
                 infrared_transmittance=0, emissivity=0.9,
                 conductivity=0.05, distance_to_glass=0.05,
                 opening_multiplier=0.5, airflow_permeability=0.0):
        """Initialize energy window material shade."""
        _EnergyWindowMaterialShadeBase.__init__(
            self, identifier, infrared_transmittance, emissivity,
            distance_to_glass, opening_multiplier)

        # default for checking transmittance + reflectance < 1
        self._solar_reflectance = 0
        self._visible_reflectance = 0

        self.thickness = thickness
        self.solar_transmittance = solar_transmittance
        self.solar_reflectance = solar_reflectance
        self.visible_transmittance = visible_transmittance
        self.visible_reflectance = visible_reflectance
        self.infrared_transmittance = infrared_transmittance
        self.conductivity = conductivity
        self.airflow_permeability = airflow_permeability

    @property
    def thickness(self):
        """Get or set the thickess of the shade material layer [m]."""
        return self._thickness

    @thickness.setter
    def thickness(self, thick):
        self._thickness = float_positive(thick, 'shade material thickness')

    @property
    def solar_transmittance(self):
        """Get or set the solar transmittance of the shade."""
        return self._solar_transmittance

    @solar_transmittance.setter
    def solar_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'shade material solar transmittance')
        assert s_tr + self._solar_reflectance <= 1, 'Sum of shade transmittance and ' \
            'reflectance ({}) is greater than 1.'.format(s_tr + self._solar_reflectance)
        self._solar_transmittance = s_tr

    @property
    def solar_reflectance(self):
        """Get or set the front solar reflectance of the shade."""
        return self._solar_reflectance

    @solar_reflectance.setter
    def solar_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
        assert s_ref + self._solar_transmittance <= 1, 'Sum of shade transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                s_ref + self._solar_transmittance)
        self._solar_reflectance = s_ref

    @property
    def visible_transmittance(self):
        """Get or set the visible transmittance of the shade."""
        return self._visible_transmittance

    @visible_transmittance.setter
    def visible_transmittance(self, v_tr):
        v_tr = float_in_range(v_tr, 0.0, 1.0, 'shade material visible transmittance')
        assert v_tr + self._visible_reflectance <= 1, 'Sum of shade transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                v_tr + self._visible_reflectance)
        self._visible_transmittance = v_tr

    @property
    def visible_reflectance(self):
        """Get or set the front visible reflectance of the shade."""
        return self._visible_reflectance

    @visible_reflectance.setter
    def visible_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'shade material visible reflectance')
        assert v_ref + self._visible_transmittance <= 1, 'Sum of shade transmittance ' \
            'and reflectance ({}) is greater than 1.'.format(
                v_ref + self._visible_transmittance)
        self._visible_reflectance = v_ref

    @property
    def conductivity(self):
        """Get or set the conductivity of the shade layer [W/m-K]."""
        return self._conductivity

    @conductivity.setter
    def conductivity(self, cond):
        self._conductivity = float_positive(cond, 'shade material conductivity')

    @property
    def airflow_permeability(self):
        """Get or set the fraction of the shade surface open to air flow."""
        return self._airflow_permeability

    @airflow_permeability.setter
    def airflow_permeability(self, perm):
        self._airflow_permeability = float_in_range(
            perm, 0.0, 0.8, 'shade material permeability')

    @property
    def resistivity(self):
        """Get or set the resistivity of the shade layer [m-K/W]."""
        return 1 / self._conductivity

    @resistivity.setter
    def resistivity(self, resis):
        self._conductivity = 1 / float_positive(resis, 'shade material resistivity')

    @property
    def u_value(self):
        """U-value of the material layer [W/m2-K] (excluding air film resistance)."""
        return self.conductivity / self.thickness

    @u_value.setter
    def u_value(self, u_val):
        self.r_value = 1 / float_positive(u_val, 'shade material u-value')

    @property
    def r_value(self):
        """R-value of the material layer [m2-K/W] (excluding air film resistance)."""
        return self.thickness / self.conductivity

    @r_value.setter
    def r_value(self, r_val):
        self._conductivity = self.thickness / \
            float_positive(r_val, 'shade material r-value')

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialShade from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_s = parse_idf_string(idf_string, 'WindowMaterial:Shade,')
        idf_defaults = {9: 0.05, 10: 0.5, 11: 0.5, 12: 0.5, 13: 0.5, 14: 0.0}
        for i, ep_str in enumerate(ep_s):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_s[i] = idf_defaults[i]

        new_mat = cls(ep_s[0], ep_s[7], ep_s[1], ep_s[2], ep_s[3], ep_s[4],
                      ep_s[6], ep_s[5], ep_s[8], ep_s[9], ep_s[10], ep_s[14])
        new_mat.bottom_opening_multiplier = ep_s[11]
        new_mat.left_opening_multiplier = ep_s[12]
        new_mat.right_opening_multiplier = ep_s[13]
        return new_mat

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialShade from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

                {
                "type": 'EnergyWindowMaterialShade',
                "identifier": 'Insulating_Shade_0020_005_020_010',
                "identifier": 'Dark Insulating Shade',
                "thickness": 0.02,
                "solar_transmittance": 0.05,
                "solar_reflectance": 0.2,
                "visible_transmittance": 0.05,
                "visible_reflectance": 0.15,
                "emissivity": 0.9,
                "infrared_transmittance": 0,
                "conductivity": 0.1
                }
        """
        assert data['type'] == 'EnergyWindowMaterialShade', \
            'Expected EnergyWindowMaterialShade. Got {}.'.format(data['type'])

        thick = data['thickness'] if 'thickness' in data and data['thickness'] \
            is not None else 0.005
        t_sol = data['solar_transmittance'] if 'solar_transmittance' in data and \
            data['solar_transmittance'] is not None else 0.4
        r_sol = data['solar_reflectance'] if 'solar_reflectance' in data and \
            data['solar_reflectance'] is not None else 0.5
        t_vis = data['visible_transmittance'] if 'visible_transmittance' in data and \
            data['visible_transmittance'] is not None else 0.4
        r_vis = data['visible_reflectance'] if 'visible_reflectance' in data and \
            data['visible_reflectance'] is not None else 0.5
        t_inf = data['infrared_transmittance'] if 'infrared_transmittance' in data and \
            data['infrared_transmittance'] is not None else 0.0
        emis = data['emissivity'] if 'emissivity' in data and \
            data['emissivity'] is not None else 0.9
        cond = data['conductivity'] if 'conductivity' in data and \
            data['conductivity'] is not None else 0.9
        dist = data['distance_to_glass'] if 'distance_to_glass' in data and \
            data['distance_to_glass'] is not None else 0.05
        top = data['top_opening_multiplier'] if 'top_opening_multiplier' in data \
            and data['top_opening_multiplier'] is not None else 0.5
        bot = data['bottom_opening_multiplier'] if 'bottom_opening_multiplier' in data \
            and data['bottom_opening_multiplier'] is not None else 0.5
        left = data['left_opening_multiplier'] if 'left_opening_multiplier' in data \
            and data['left_opening_multiplier'] is not None else 0.5
        right = data['right_opening_multiplier'] if 'right_opening_multiplier' in data \
            and data['right_opening_multiplier'] is not None else 0.5
        air = data['airflow_permeability'] if 'airflow_permeability' in data \
            and data['airflow_permeability'] is not None else 0

        new_mat = cls(data['identifier'], thick, t_sol, r_sol, t_vis, r_vis,
                      t_inf, emis, cond, dist, top, air)
        new_mat.bottom_opening_multiplier = bot
        new_mat.left_opening_multiplier = left
        new_mat.right_opening_multiplier = right
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']
        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.solar_transmittance, self.solar_reflectance,
                  self.visible_transmittance, self.visible_reflectance,
                  self.emissivity, self.infrared_transmittance, self.thickness,
                  self.conductivity, self.top_opening_multiplier,
                  self.bottom_opening_multiplier, self.left_opening_multiplier,
                  self.right_opening_multiplier, self.airflow_permeability)
        comments = ('name', 'solar transmittance', 'solar reflectance',
                    'visible transmittance', 'visible reflectance', 'emissivity',
                    'infrared transmittance', 'thickness {m}', 'conductivity {W/m-K}',
                    'distance to glass {m}', 'top opening multiplier',
                    'bottom opening multiplier', 'left opening multiplier',
                    'right opening multiplier', 'airflow permeability')
        return generate_idf_string('WindowMaterial:Shade', values, comments)

    def to_dict(self):
        """Energy Window Material Shade dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialShade',
            'identifier': self.identifier,
            'thickness': self.thickness,
            'solar_transmittance': self.solar_transmittance,
            'solar_reflectance': self.solar_reflectance,
            'visible_transmittance': self.visible_transmittance,
            'visible_reflectance': self.visible_reflectance,
            'infrared_transmittance': self.infrared_transmittance,
            'emissivity': self.emissivity,
            'conductivity': self.conductivity,
            'distance_to_glass': self.distance_to_glass,
            'top_opening_multiplier': self.top_opening_multiplier,
            'bottom_opening_multiplier': self.bottom_opening_multiplier,
            'left_opening_multiplier': self.left_opening_multiplier,
            'right_opening_multiplier': self.right_opening_multiplier,
            'airflow_permeability': self.airflow_permeability
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.thickness, self.solar_transmittance,
                self.solar_reflectance, self.visible_transmittance,
                self.visible_reflectance, self.infrared_transmittance,
                self.emissivity, self.conductivity, self.distance_to_glass,
                self.top_opening_multiplier, self.bottom_opening_multiplier,
                self.left_opening_multiplier, self.right_opening_multiplier,
                self.airflow_permeability)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialShade) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = EnergyWindowMaterialShade(
            self.identifier, self.thickness, self.solar_transmittance,
            self.solar_reflectance, self.visible_transmittance, self.visible_reflectance,
            self.infrared_transmittance, self.emissivity,
            self.conductivity, self.distance_to_glass,
            self.top_opening_multiplier, self.airflow_permeability)
        new_material._top_opening_multiplier = self._top_opening_multiplier
        new_material._bottom_opening_multiplier = self._bottom_opening_multiplier
        new_material._left_opening_multiplier = self._left_opening_multiplier
        new_material._right_opening_multiplier = self._right_opening_multiplier
        new_material._display_name = self._display_name
        return new_material


@lockable
class EnergyWindowMaterialBlind(_EnergyWindowMaterialShadeBase):
    """A material for a blind layer in a window construction.

    Window blind properties consist of flat, equally-spaced slats.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        slat_orientation: Text describing the orientation of the slats.
            Only the following two options are acceptable:
            "Horizontal", "Vertical". Default: "Horizontal"
        slat_width: The width of slat measured from edge to edge [m].
            Default: 0.025 m (25 mm).
        slat_separation: The distance between each of the slats [m].
            Default: 0.01875 m (18.75 mm).
        slat_thickness: A number between 0 and 0.1 for the thickness of the slat [m].
            Default: 0.001 m (1 mm).
        slat_angle: A number between 0 and 180 for the angle between the slats
            and the glazing normal in degrees. 90 signifies slats that are
            perpendicular to the glass. Default: 45.
        slat_conductivity: The thermal conductivity of the blind material [W/m-K].
            Default is 221, which is characteristic of metal blinds.
        solar_transmittance: Number between 0 and 1 for the transmittance
            of solar radiation through the blind material. Default: 0.
        solar_reflectance: Number between 0 and 1 for the front reflectance
            of solar radiation off of the blind, averaged over the solar
            spectrum. Default: 0.5.
        visible_transmittance: Number between 0 and 1 for the transmittance
            of visible light through the blind material. Default : 0.
        visible_reflectance: Number between 0 and 1 for the reflectance of
            visible light off of the blind. Default: 0.5.
        infrared_transmittance: Long-wave hemispherical transmittance of the blind.
            Default value is 0.
        emissivity: Number between 0 and 1 for the infrared hemispherical
            emissivity of the blind.  Default is 0.9.
        distance_to_glass: A number between 0.001 and 1.0 for the distance from
            the mid-plane of the blind to the adjacent glass layers [m].
            Default is 0.05 (50 mm).
        opening_multiplier: Factor between 0 and 1 that is multiplied by the
            area at the top, bottom and sides of the shade for air flow
            calculations. Default: 0.5.

    Properties:
        * identifier
        * display_name
        * slat_orientation
        * slat_width
        * slat_separation
        * slat_thickness
        * slat_angle
        * slat_conductivity
        * beam_solar_transmittance
        * beam_solar_reflectance
        * beam_solar_reflectance_back
        * diffuse_solar_transmittance
        * diffuse_solar_reflectance
        * diffuse_solar_reflectance_back
        * beam_visible_transmittance
        * beam_visible_reflectance
        * beam_visible_reflectance_back
        * diffuse_visible_transmittance
        * diffuse_visible_reflectance
        * diffuse_visible_reflectance_back
        * infrared_transmittance
        * emissivity
        * emissivity_back
        * distance_to_glass
        * top_opening_multiplier
        * bottom_opening_multiplier
        * left_opening_multiplier
        * right_opening_multiplier
        * slat_resistivity
        * u_value
        * r_value
        * user_data
    """
    ORIENTATIONS = ('Horizontal', 'Vertical')
    __slots__ = ('_slat_orientation', '_slat_width', '_slat_separation',
                 '_slat_thickness', '_slat_angle', '_slat_conductivity',
                 '_beam_solar_transmittance', '_beam_solar_reflectance',
                 '_beam_solar_reflectance_back', '_diffuse_solar_transmittance',
                 '_diffuse_solar_reflectance', '_diffuse_solar_reflectance_back',
                 '_beam_visible_transmittance', '_beam_visible_reflectance',
                 '_beam_visible_reflectance_back', '_diffuse_visible_transmittance',
                 '_diffuse_visible_reflectance', '_diffuse_visible_reflectance_back',
                 '_emissivity_back')

    def __init__(self, identifier, slat_orientation='Horizontal', slat_width=0.025,
                 slat_separation=0.01875, slat_thickness=0.001, slat_angle=45,
                 slat_conductivity=221, solar_transmittance=0, solar_reflectance=0.5,
                 visible_transmittance=0, visible_reflectance=0.5,
                 infrared_transmittance=0, emissivity=0.9,
                 distance_to_glass=0.05, opening_multiplier=0.5):
        """Initialize energy window material blind."""
        _EnergyWindowMaterialShadeBase.__init__(
            self, identifier, infrared_transmittance, emissivity,
            distance_to_glass, opening_multiplier)

        # default for checking transmittance + reflectance < 1
        self._beam_solar_reflectance = 0
        self._beam_solar_reflectance_back = None
        self._diffuse_solar_reflectance = 0
        self._diffuse_solar_reflectance_back = None
        self._beam_visible_reflectance = 0
        self._beam_visible_reflectance_back = None
        self._diffuse_visible_reflectance = 0
        self._diffuse_visible_reflectance_back = None

        self.slat_orientation = slat_orientation
        self.slat_width = slat_width
        self.slat_separation = slat_separation
        self.slat_thickness = slat_thickness
        self.slat_angle = slat_angle
        self.slat_conductivity = slat_conductivity
        self.set_all_solar_transmittance(solar_transmittance)
        self.set_all_solar_reflectance(solar_reflectance)
        self.set_all_visible_transmittance(visible_transmittance)
        self.set_all_visible_reflectance(visible_reflectance)
        self.infrared_transmittance = infrared_transmittance
        self.emissivity_back = None

    @property
    def slat_orientation(self):
        """Get or set text describing the slat orientation.

        Must be one of the following: ["Horizontal", "Vertical"].
        """
        return self._slat_orientation

    @slat_orientation.setter
    def slat_orientation(self, orient):
        assert orient in self.ORIENTATIONS, 'Invalid input "{}" for slat ' \
            'orientation.\nMust be one of the following:{}'.format(
                orient, self.ORIENTATIONS)
        self._slat_orientation = orient

    @property
    def slat_width(self):
        """Get or set the width of slat measured from edge to edge [m]"""
        return self._slat_width

    @slat_width.setter
    def slat_width(self, width):
        self._slat_width = float_in_range(width, 0.0, 1.0, 'shade material slat width')

    @property
    def slat_separation(self):
        """Get or set the distance between each of the slats [m]"""
        return self._slat_separation

    @slat_separation.setter
    def slat_separation(self, separ):
        self._slat_separation = float_in_range(
            separ, 0.0, 1.0, 'shade material slat separation')

    @property
    def slat_thickness(self):
        """Get or set the thickness of the slat [m]."""
        return self._slat_thickness

    @slat_thickness.setter
    def slat_thickness(self, thick):
        self._slat_thickness = float_in_range(
            thick, 0.0, 0.1, 'shade material slat thickness')

    @property
    def slat_angle(self):
        """Get or set the angle between the slats and the glazing normal."""
        return self._slat_angle

    @slat_angle.setter
    def slat_angle(self, angle):
        self._slat_angle = float_in_range(angle, 0, 180, 'shade material slat angle')

    @property
    def slat_conductivity(self):
        """Get or set the conductivity of the blind material [W/m-K]."""
        return self._slat_conductivity

    @slat_conductivity.setter
    def slat_conductivity(self, cond):
        self._slat_conductivity = float_positive(cond, 'shade material conductivity')

    @property
    def beam_solar_transmittance(self):
        """Get or set the beam solar transmittance of the blind material."""
        return self._beam_solar_transmittance

    @beam_solar_transmittance.setter
    def beam_solar_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'shade material solar transmittance')
        assert s_tr + self._beam_solar_reflectance <= 1, 'Sum of blind ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_tr + self._beam_solar_reflectance)
        if self._beam_solar_reflectance_back is not None:
            assert s_tr + self._beam_solar_reflectance_back <= 1, 'Sum of blind ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_tr + self._beam_solar_reflectance_back)
        self._beam_solar_transmittance = s_tr

    @property
    def beam_solar_reflectance(self):
        """Get or set the front beam solar reflectance of the blind."""
        return self._beam_solar_reflectance

    @beam_solar_reflectance.setter
    def beam_solar_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
        assert s_ref + self._beam_solar_transmittance <= 1, 'Sum of window ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_ref + self._beam_solar_transmittance)
        self._beam_solar_reflectance = s_ref

    @property
    def beam_solar_reflectance_back(self):
        """Get or set the back beam solar reflectance of the blind."""
        return self._beam_solar_reflectance_back if \
            self._beam_solar_reflectance_back is not None \
            else self._beam_solar_reflectance

    @beam_solar_reflectance_back.setter
    def beam_solar_reflectance_back(self, s_ref):
        if s_ref is not None:
            s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
            assert s_ref + self._beam_solar_transmittance <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_ref + self._beam_solar_transmittance)
        self._beam_solar_reflectance_back = s_ref

    @property
    def diffuse_solar_transmittance(self):
        """Get or set the diffuse solar transmittance of the blind material."""
        return self._diffuse_solar_transmittance

    @diffuse_solar_transmittance.setter
    def diffuse_solar_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'shade material solar transmittance')
        assert s_tr + self._diffuse_solar_reflectance <= 1, 'Sum of blind ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_tr + self._diffuse_solar_reflectance)
        if self._diffuse_solar_reflectance_back is not None:
            assert s_tr + self._diffuse_solar_reflectance_back <= 1, 'Sum of blind' \
                ' transmittance and reflectance ({}) is greater than 1.'.format(
                    s_tr + self._diffuse_solar_reflectance_back)
        self._diffuse_solar_transmittance = s_tr

    @property
    def diffuse_solar_reflectance(self):
        """Get or set the front diffuse solar reflectance of the blind."""
        return self._diffuse_solar_reflectance

    @diffuse_solar_reflectance.setter
    def diffuse_solar_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
        assert s_ref + self._diffuse_solar_transmittance <= 1, 'Sum of window ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_ref + self._diffuse_solar_transmittance)
        self._diffuse_solar_reflectance = s_ref

    @property
    def diffuse_solar_reflectance_back(self):
        """Get or set the back diffuse solar reflectance of the blind."""
        return self._diffuse_solar_reflectance_back if \
            self._diffuse_solar_reflectance_back is not None \
            else self._diffuse_solar_reflectance

    @diffuse_solar_reflectance_back.setter
    def diffuse_solar_reflectance_back(self, s_ref):
        if s_ref is not None:
            s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
            assert s_ref + self._diffuse_solar_transmittance <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_ref + self._diffuse_solar_transmittance)
        self._diffuse_solar_reflectance_back = s_ref

    @property
    def beam_visible_transmittance(self):
        """Get or set the beam visible transmittance of the blind material."""
        return self._beam_visible_transmittance

    @beam_visible_transmittance.setter
    def beam_visible_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'shade material solar transmittance')
        assert s_tr + self._beam_visible_reflectance <= 1, 'Sum of blind ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_tr + self._beam_visible_reflectance)
        if self._beam_visible_reflectance_back is not None:
            assert s_tr + self._beam_visible_reflectance_back <= 1, 'Sum of blind ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_tr + self._beam_visible_reflectance_back)
        self._beam_visible_transmittance = s_tr

    @property
    def beam_visible_reflectance(self):
        """Get or set the front beam visible reflectance of the blind."""
        return self._beam_visible_reflectance

    @beam_visible_reflectance.setter
    def beam_visible_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
        assert s_ref + self._beam_visible_transmittance <= 1, 'Sum of window ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_ref + self._beam_visible_transmittance)
        self._beam_visible_reflectance = s_ref

    @property
    def beam_visible_reflectance_back(self):
        """Get or set the back beam visible reflectance of the blind."""
        return self._beam_visible_reflectance_back if \
            self._beam_visible_reflectance_back is not None \
            else self._beam_visible_reflectance

    @beam_visible_reflectance_back.setter
    def beam_visible_reflectance_back(self, s_ref):
        if s_ref is not None:
            s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
            assert s_ref + self._beam_visible_transmittance <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_ref + self._beam_visible_transmittance)
        self._beam_visible_reflectance_back = s_ref

    @property
    def diffuse_visible_transmittance(self):
        """Get or set the diffuse visible transmittance of the blind material."""
        return self._diffuse_visible_transmittance

    @diffuse_visible_transmittance.setter
    def diffuse_visible_transmittance(self, s_tr):
        s_tr = float_in_range(s_tr, 0.0, 1.0, 'shade material solar transmittance')
        assert s_tr + self._diffuse_visible_reflectance <= 1, 'Sum of blind ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_tr + self._diffuse_visible_reflectance)
        if self._diffuse_visible_reflectance_back is not None:
            assert s_tr + self._diffuse_visible_reflectance_back <= 1, 'Sum of blind' \
                ' transmittance and reflectance ({}) is greater than 1.'.format(
                    s_tr + self._diffuse_visible_reflectance_back)
        self._diffuse_visible_transmittance = s_tr

    @property
    def diffuse_visible_reflectance(self):
        """Get or set the front diffuse visible reflectance of the blind."""
        return self._diffuse_visible_reflectance

    @diffuse_visible_reflectance.setter
    def diffuse_visible_reflectance(self, s_ref):
        s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
        assert s_ref + self._diffuse_visible_transmittance <= 1, 'Sum of window ' \
            'transmittance and reflectance ({}) is greater than 1.'.format(
                s_ref + self._diffuse_visible_transmittance)
        self._diffuse_visible_reflectance = s_ref

    @property
    def diffuse_visible_reflectance_back(self):
        """Get or set the back diffuse visible reflectance of the blind."""
        return self._diffuse_visible_reflectance_back if \
            self._diffuse_visible_reflectance_back is not None \
            else self._diffuse_visible_reflectance

    @diffuse_visible_reflectance_back.setter
    def diffuse_visible_reflectance_back(self, s_ref):
        if s_ref is not None:
            s_ref = float_in_range(s_ref, 0.0, 1.0, 'shade material solar reflectance')
            assert s_ref + self._diffuse_visible_transmittance <= 1, 'Sum of window ' \
                'transmittance and reflectance ({}) is greater than 1.'.format(
                    s_ref + self._diffuse_visible_transmittance)
        self._diffuse_visible_reflectance_back = s_ref

    @property
    def emissivity_back(self):
        """Get or set the hemispherical emissivity of the back side of the glass."""
        return self._emissivity_back if self._emissivity_back is not None \
            else self._emissivity

    @emissivity_back.setter
    def emissivity_back(self, ir_e):
        if ir_e is not None:
            ir_e = float_in_range(ir_e, 0.0, 1.0, 'shade material emissivity')
        self._emissivity_back = ir_e

    @property
    def slat_resistivity(self):
        """Get or set the resistivity of the blind layer [m-K/W]."""
        return 1 / self._slat_conductivity

    @slat_resistivity.setter
    def slat_resistivity(self, resis):
        self._slat_conductivity = 1 / float_positive(resis, 'shade material resistivity')

    @property
    def u_value(self):
        """U-value of the blind slats [W/m2-K] (excluding air film resistance).

        Note that this value assumes that blinds are completely closed (at 0 degrees).
        """
        return self.slat_conductivity / self.slat_thickness

    @u_value.setter
    def u_value(self, u_val):
        self.r_value = 1 / float_positive(u_val, 'shade material u-value')

    @property
    def r_value(self):
        """R-value of the blind slats [m2-K/W] (excluding air film resistance).

        Note that this value assumes that blinds are completely closed (at 0 degrees).
        """
        return self.slat_thickness / self.slat_conductivity

    @r_value.setter
    def r_value(self, r_val):
        self._slat_conductivity = self.slat_thickness / \
            float_positive(r_val, 'shade material r-value')

    def set_all_solar_transmittance(self, transmittance):
        """Set all solar transmittance to the same value at once."""
        self.beam_solar_transmittance = transmittance
        self.diffuse_solar_transmittance = transmittance

    def set_all_solar_reflectance(self, reflectance):
        """Set all solar reflectance to the same value at once."""
        self.beam_solar_reflectance = reflectance
        self.beam_solar_reflectance_back = None
        self.diffuse_solar_reflectance = reflectance
        self.diffuse_solar_reflectance_back = None

    def set_all_visible_transmittance(self, transmittance):
        """Set all solar transmittance to the same value at once."""
        self.beam_visible_transmittance = transmittance
        self.diffuse_visible_transmittance = transmittance

    def set_all_visible_reflectance(self, reflectance):
        """Set all visible reflectance to the same value at once."""
        self.beam_visible_reflectance = reflectance
        self.beam_visible_reflectance_back = None
        self.diffuse_visible_reflectance = reflectance
        self.diffuse_visible_reflectance_back = None

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialBlind from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_s = parse_idf_string(idf_string, 'WindowMaterial:Blind,')
        idf_defaults = {1: 'Horizontal', 4: 0.00025, 5: 45, 6: 221.0, 7: 0.0,
                        10: 0.0, 14: 0.0, 15: 0.0, 16: 0.0, 17: 0.0, 18: 0.0,
                        19: 0.0, 20: 0.9, 21: 0.9, 22: 0.05, 23: 0.5, 24: 0.0,
                        25: 0.5, 26: 0.5}
        for i, ep_str in enumerate(ep_s):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_s[i] = idf_defaults[i]

        new_mat = cls(ep_s[0], ep_s[1], ep_s[2], ep_s[3], ep_s[4], ep_s[5],
                      ep_s[6], ep_s[7], ep_s[8], ep_s[13], ep_s[14], ep_s[19],
                      ep_s[20], ep_s[22], ep_s[23])
        new_mat.beam_solar_reflectance_back = ep_s[9]
        new_mat.diffuse_solar_transmittance = ep_s[10]
        new_mat.diffuse_solar_reflectance = ep_s[11]
        new_mat.diffuse_solar_reflectance_back = ep_s[12]
        new_mat.beam_visible_reflectance_back = ep_s[15]
        new_mat.diffuse_visible_transmittance = ep_s[16]
        new_mat.diffuse_visible_reflectance = ep_s[17]
        new_mat.diffuse_visible_reflectance_back = ep_s[18]
        new_mat.emissivity_back = ep_s[21]
        new_mat.bottom_opening_multiplier = ep_s[24]
        new_mat.left_opening_multiplier = ep_s[25]
        new_mat.right_opening_multiplier = ep_s[26]
        return new_mat

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialBlind from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowMaterialBlind',
            "identifier": 'Plastic_Blind_Horiz_0040_0030_0002_90',
            "display_name": 'Plastic Blind',
            "slat_orientation": 'Horizontal',
            "slat_width": 0.04,
            "slat_separation": 0.03,
            "slat_thickness": 0.002,
            "slat_angle": 90,
            "slat_conductivity": 0.2
            }
        """
        assert data['type'] == 'EnergyWindowMaterialBlind', \
            'Expected EnergyWindowMaterialBlind. Got {}.'.format(data['type'])

        orient = data['slat_orientation'] if 'slat_orientation' in data and \
            data['slat_orientation'] is not None else 'Horizontal'
        width = data['slat_width'] if 'slat_width' in data and \
            data['slat_width'] is not None else 0.025
        sep = data['slat_separation'] if 'slat_separation' in data and \
            data['slat_separation'] is not None else 0.01875
        thick = data['slat_thickness'] if 'slat_thickness' in data and \
            data['slat_thickness'] is not None else 0.001
        angle = data['slat_angle'] if 'slat_angle' in data and \
            data['slat_angle'] is not None else 45
        cond = data['slat_conductivity'] if 'slat_conductivity' in data and \
            data['slat_conductivity'] is not None else 221
        t_sol = data['beam_solar_transmittance'] if 'beam_solar_transmittance' in data \
            and data['beam_solar_transmittance'] is not None else 0.0
        r_sol = data['beam_solar_reflectance'] if 'beam_solar_reflectance' in data and \
            data['beam_solar_reflectance'] is not None else 0.5
        r_sol_b = data['beam_solar_reflectance_back'] if 'beam_solar_reflectance_back' \
            in data else None
        td_sol = data['diffuse_solar_transmittance'] if 'diffuse_solar_transmittance' \
            in data and data['diffuse_solar_transmittance'] is not None else 0.0
        rd_sol = data['diffuse_solar_reflectance'] if 'diffuse_solar_reflectance' in \
            data and data['diffuse_solar_reflectance'] is not None else 0.5
        rd_sol_b = data['diffuse_solar_reflectance_back'] if \
            'diffuse_solar_reflectance_back' in data else None

        t_vis = data['beam_visible_transmittance'] if 'beam_visible_transmittance' in \
            data and data['beam_visible_transmittance'] is not None else 0.0
        r_vis = data['beam_visible_reflectance'] if 'beam_visible_reflectance' in data and \
            data['beam_visible_reflectance'] is not None else 0.5
        r_vis_b = data['beam_visible_reflectance_back'] if 'beam_visible_reflectance_back' \
            in data else None
        td_vis = data['diffuse_visible_transmittance'] if 'diffuse_visible_transmittance' \
            in data and data['diffuse_visible_transmittance'] is not None else 0.0
        rd_vis = data['diffuse_visible_reflectance'] if 'diffuse_visible_reflectance' \
            in data and data['diffuse_visible_reflectance'] is not None else 0.5
        rd_vis_b = data['diffuse_visible_reflectance_back'] if \
            'diffuse_visible_reflectance_back' in data else None

        t_inf = data['infrared_transmittance'] if 'infrared_transmittance' in data and \
            data['infrared_transmittance'] is not None else 0.0
        emis = data['emissivity'] if 'emissivity' in data and \
            data['emissivity'] is not None else 0.9
        emis_b = data['emissivity_back'] if 'emissivity_back' in data else None
        dist = data['distance_to_glass'] if 'distance_to_glass' in data and \
            data['distance_to_glass'] is not None else 0.05
        top = data['top_opening_multiplier'] if 'top_opening_multiplier' in data \
            and data['top_opening_multiplier'] is not None else 0.5
        bot = data['bottom_opening_multiplier'] if 'bottom_opening_multiplier' in data \
            and data['bottom_opening_multiplier'] is not None else 0.5
        left = data['left_opening_multiplier'] if 'left_opening_multiplier' in data \
            and data['left_opening_multiplier'] is not None else 0.5
        right = data['right_opening_multiplier'] if 'right_opening_multiplier' in data \
            and data['right_opening_multiplier'] is not None else 0.5

        new_mat = cls(
            data['identifier'], orient, width, sep, thick, angle, cond, t_sol, r_sol,
            t_vis, r_vis, t_inf, emis, dist, top)

        new_mat.beam_solar_reflectance_back = r_sol_b
        new_mat.diffuse_solar_transmittance = td_sol
        new_mat.diffuse_solar_reflectance = rd_sol
        new_mat.diffuse_solar_reflectance_back = rd_sol_b
        new_mat.beam_visible_reflectance_back = r_vis_b
        new_mat.diffuse_visible_transmittance = td_vis
        new_mat.diffuse_visible_reflectance = rd_vis
        new_mat.diffuse_visible_reflectance_back = rd_vis_b
        new_mat.emissivity_back = emis_b
        new_mat.bottom_opening_multiplier = bot
        new_mat.left_opening_multiplier = left
        new_mat.right_opening_multiplier = right
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']
        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.slat_orientation, self.slat_width,
                  self.slat_separation, self.slat_thickness, self.slat_angle,
                  self.slat_conductivity, self.beam_solar_transmittance,
                  self.beam_solar_reflectance, self.beam_solar_reflectance_back,
                  self.diffuse_solar_transmittance, self.diffuse_solar_reflectance,
                  self.diffuse_solar_reflectance_back, self.beam_visible_transmittance,
                  self.beam_visible_reflectance, self.beam_visible_reflectance_back,
                  self.diffuse_visible_transmittance, self.diffuse_visible_reflectance,
                  self.diffuse_visible_reflectance_back, self.infrared_transmittance,
                  self.emissivity, self.emissivity_back, self.distance_to_glass,
                  self.top_opening_multiplier, self.bottom_opening_multiplier,
                  self.left_opening_multiplier, self.right_opening_multiplier, 0, 180)
        comments = (
            'name', 'slat orientation', 'slat width {m}', 'slat separation {m}',
            'slat thickness {m}', 'slat angle {deg}',
            'slat conductivity {W/m-K}', 'beam solar transmittance',
            'beam solar reflectance front', 'beam solar reflectance back',
            'diffuse solar transmittance', 'diffuse solar reflectance front',
            'diffuse solar reflectance back', 'beam visible transmittance',
            'beam visible reflectance front', 'beam visible reflectance back',
            'diffuse visible transmittance', 'diffuse visible reflectance front',
            'diffuse visible reflectance back', 'infrared transmittance',
            'emissivity front', 'emissivity back', 'distance to glass {m}',
            'top opening multiplier', 'bottom opening multiplier',
            'left opening multiplier', 'right opening multiplier',
            'minimum slat angle {deg}', 'maximum slat angle {deg}')
        return generate_idf_string('WindowMaterial:Blind', values, comments)

    def to_dict(self):
        """Energy Window Material Blind dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialBlind',
            'identifier': self.identifier,
            'slat_orientation': self.slat_orientation,
            'slat_width': self.slat_width,
            'slat_separation': self.slat_separation,
            'slat_thickness': self.slat_thickness,
            'slat_angle': self.slat_angle,
            'slat_conductivity': self.slat_conductivity,
            'beam_solar_transmittance': self.beam_solar_transmittance,
            'beam_solar_reflectance': self.beam_solar_reflectance,
            'beam_solar_reflectance_back': self.beam_solar_reflectance_back,
            'diffuse_solar_transmittance': self.diffuse_solar_transmittance,
            'diffuse_solar_reflectance': self.diffuse_solar_reflectance,
            'diffuse_solar_reflectance_back': self.diffuse_solar_reflectance_back,
            'beam_visible_transmittance': self.beam_visible_transmittance,
            'beam_visible_reflectance': self.beam_visible_reflectance,
            'beam_visible_reflectance_back': self.beam_visible_reflectance_back,
            'diffuse_visible_transmittance': self.diffuse_visible_transmittance,
            'diffuse_visible_reflectance': self.diffuse_visible_reflectance,
            'diffuse_visible_reflectance_back': self.diffuse_visible_reflectance_back,
            'infrared_transmittance': self.infrared_transmittance,
            'emissivity': self.emissivity,
            'emissivity_back': self.emissivity_back,
            'distance_to_glass': self.distance_to_glass,
            'top_opening_multiplier': self.top_opening_multiplier,
            'bottom_opening_multiplier': self.bottom_opening_multiplier,
            'left_opening_multiplier': self.left_opening_multiplier,
            'right_opening_multiplier': self.right_opening_multiplier
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.slat_orientation, self.slat_width,
                self.slat_separation, self.slat_thickness, self.slat_angle,
                self.slat_conductivity, self.beam_solar_transmittance,
                self.beam_solar_reflectance, self.beam_solar_reflectance_back,
                self.diffuse_solar_transmittance, self.diffuse_solar_reflectance,
                self.diffuse_solar_reflectance_back, self.beam_visible_transmittance,
                self.beam_visible_reflectance, self.beam_visible_reflectance_back,
                self.diffuse_visible_transmittance, self.diffuse_visible_reflectance,
                self.diffuse_visible_reflectance_back, self.infrared_transmittance,
                self.emissivity, self.emissivity_back, self.distance_to_glass,
                self.top_opening_multiplier, self.bottom_opening_multiplier,
                self.left_opening_multiplier, self.right_opening_multiplier)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialBlind) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_m = EnergyWindowMaterialBlind(
            self.identifier, self.slat_orientation, self.slat_width, self.slat_separation,
            self.slat_thickness, self.slat_angle, self.slat_conductivity,
            self.beam_solar_transmittance, self.beam_solar_reflectance,
            self.beam_visible_transmittance, self.beam_visible_reflectance,
            self.infrared_transmittance, self.emissivity, self.distance_to_glass,
            self.top_opening_multiplier)
        new_m._diffuse_solar_transmittance = self._diffuse_solar_transmittance
        new_m._beam_solar_reflectance_back = self._beam_solar_reflectance_back
        new_m._diffuse_solar_reflectance = self._diffuse_solar_reflectance
        new_m._diffuse_solar_reflectance_back = self._diffuse_solar_reflectance_back
        new_m._diffuse_visible_transmittance = self._diffuse_visible_transmittance
        new_m._beam_visible_reflectance_back = self._beam_visible_reflectance_back
        new_m._diffuse_visible_reflectance = self._diffuse_visible_reflectance
        new_m._diffuse_visible_reflectance_back = self._diffuse_visible_reflectance_back
        new_m._top_opening_multiplier = self._top_opening_multiplier
        new_m._bottom_opening_multiplier = self._bottom_opening_multiplier
        new_m._left_opening_multiplier = self._left_opening_multiplier
        new_m._right_opening_multiplier = self._right_opening_multiplier
        new_m._display_name = self._display_name
        return new_m
