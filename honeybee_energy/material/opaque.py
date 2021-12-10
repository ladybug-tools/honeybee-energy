# coding=utf-8
"""Opaque energy materials.

The materials here are the only ones that can be used in opaque constructions.
"""
from __future__ import division

from ._base import _EnergyMaterialOpaqueBase
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_in_range, float_positive, clean_rad_string


@lockable
class EnergyMaterial(_EnergyMaterialOpaqueBase):
    """Typical opaque energy material.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the material layer [m].
        conductivity: Number for the thermal conductivity of the material [W/m-K].
        density: Number for the density of the material [kg/m3].
        specific_heat: Number for the specific heat of the material [J/kg-K].
        roughness: Text describing the relative roughness of the material.
            Must be one of the following: 'VeryRough', 'Rough', 'MediumRough',
            'MediumSmooth', 'Smooth', 'VerySmooth'. Default is 'MediumRough'.
        thermal_absorptance: A number between 0 and 1 for the fraction of
            incident long wavelength radiation that is absorbed by the material.
            Default value is 0.9.
        solar_absorptance: A number between 0 and 1 for the fraction of incident
            solar radiation absorbed by the material. Default value is 0.7.
        visible_absorptance: A number between 0 and 1 for the fraction of incident
            visible wavelength radiation absorbed by the material.
            Default is None, which will yield the same value as solar_absorptance.

    Properties:
        * identifier
        * display_name
        * roughness
        * thickness
        * conductivity
        * density
        * specific_heat
        * thermal_absorptance
        * solar_absorptance
        * visible_absorptance
        * solar_reflectance
        * visible_reflectance
        * resistivity
        * u_value
        * r_value
        * mass_area_density
        * area_heat_capacity
        * user_data
    """
    __slots__ = ('_roughness', '_thickness', '_conductivity',
                 '_density', '_specific_heat', '_thermal_absorptance',
                 '_solar_absorptance', '_visible_absorptance')

    def __init__(self, identifier, thickness, conductivity, density, specific_heat,
                 roughness='MediumRough', thermal_absorptance=0.9,
                 solar_absorptance=0.7, visible_absorptance=None):
        """Initialize energy material."""
        _EnergyMaterialOpaqueBase.__init__(self, identifier)
        self.thickness = thickness
        self.conductivity = conductivity
        self.density = density
        self.specific_heat = specific_heat
        self.roughness = roughness
        self.thermal_absorptance = thermal_absorptance
        self.solar_absorptance = solar_absorptance
        self.visible_absorptance = visible_absorptance
        self._locked = False

    @property
    def roughness(self):
        """Get or set the text describing the roughness of the material layer."""
        return self._roughness

    @roughness.setter
    def roughness(self, rough):
        assert rough in self.ROUGHTYPES, 'Invalid input "{}" for material roughness.' \
            ' Roughness must be one of the following:\n'.format(
                rough, self.ROUGHTYPES)
        self._roughness = rough

    @property
    def thickness(self):
        """Get or set the thickess of the material layer [m]."""
        return self._thickness

    @thickness.setter
    def thickness(self, thick):
        self._thickness = float_positive(thick, 'material thickness')
        self._compare_thickness_conductivity()

    @property
    def conductivity(self):
        """Get or set the conductivity of the material layer [W/m-K]."""
        return self._conductivity

    @conductivity.setter
    def conductivity(self, cond):
        self._conductivity = float_positive(cond, 'material conductivity')
        self._compare_thickness_conductivity()

    @property
    def density(self):
        """Get or set the density of the material layer [kg/m3]."""
        return self._density

    @density.setter
    def density(self, dens):
        self._density = float_positive(dens, 'material density')

    @property
    def specific_heat(self):
        """Get or set the specific heat of the material layer [J/kg-K]."""
        return self._specific_heat

    @specific_heat.setter
    def specific_heat(self, sp_ht):
        self._specific_heat = float_in_range(
            sp_ht, 100.0, input_name='material specific heat')

    @property
    def thermal_absorptance(self):
        """Get or set the thermal absorptance of the material layer."""
        return self._thermal_absorptance

    @thermal_absorptance.setter
    def thermal_absorptance(self, t_abs):
        self._thermal_absorptance = float_in_range(
            t_abs, 0.0, 1.0, 'material thermal absorptance')

    @property
    def solar_absorptance(self):
        """Get or set the solar absorptance of the material layer."""
        return self._solar_absorptance

    @solar_absorptance.setter
    def solar_absorptance(self, s_abs):
        self._solar_absorptance = float_in_range(
            s_abs, 0.0, 1.0, 'material solar absorptance')

    @property
    def visible_absorptance(self):
        """Get or set the visible absorptance of the material layer."""
        return self._visible_absorptance if self._visible_absorptance is not None \
            else self._solar_absorptance

    @visible_absorptance.setter
    def visible_absorptance(self, v_abs):
        self._visible_absorptance = float_in_range(
            v_abs, 0.0, 1.0, 'material visible absorptance') if v_abs is not None \
            else None

    @property
    def solar_reflectance(self):
        """Get or set the front solar reflectance of the material layer."""
        return 1 - self.solar_absorptance

    @solar_reflectance.setter
    def solar_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'material solar reflectance')
        self.solar_absorptance = 1 - v_ref

    @property
    def visible_reflectance(self):
        """Get or set the front visible reflectance of the material layer."""
        return 1 - self.visible_absorptance

    @visible_reflectance.setter
    def visible_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'material visible reflectance')
        self.visible_absorptance = 1 - v_ref

    @property
    def resistivity(self):
        """Get or set the resistivity of the material layer [m-K/W]."""
        return 1 / self._conductivity

    @resistivity.setter
    def resistivity(self, resis):
        self._conductivity = 1 / float_positive(resis, 'material resistivity')

    @property
    def r_value(self):
        """Get or set the R-value of the material in [m2-K/W] (excluding air films).

        Note that, when setting the R-value, the thickness of the material will
        remain fixed and only the conductivity will be adjusted.
        """
        return self.thickness / self.conductivity

    @r_value.setter
    def r_value(self, r_val):
        _new_conductivity = self.thickness / \
            float_positive(r_val, 'material r-value')
        self._conductivity = _new_conductivity

    @property
    def u_value(self):
        """Get or set the  U-value of the material [W/m2-K] (excluding air films).

        Note that, when setting the R-value, the thickness of the material will
        remain fixed and only the conductivity will be adjusted.
        """
        return self.conductivity / self.thickness

    @u_value.setter
    def u_value(self, u_val):
        self.r_value = 1 / float_positive(u_val, 'material u-value')

    @property
    def mass_area_density(self):
        """The area density of the material [kg/m2]."""
        return self.thickness * self.density

    @property
    def area_heat_capacity(self):
        """The heat capacity per unit area of the material [kg/K-m2]."""
        return self.mass_area_density * self.specific_heat

    @classmethod
    def from_idf(cls, idf_string):
        """Create an EnergyMaterial from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'Material,')
        idf_defaults = {6: 0.9, 7: 0.7, 8: 0.7}
        for i, ep_str in enumerate(ep_strs):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_strs[i] = idf_defaults[i]
        ep_strs.insert(5, ep_strs.pop(1))  # move roughness to correct place
        return cls(*ep_strs)

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyMaterial from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyMaterial',
            "identifier": 'Concrete_020_231_2322_832',
            "display_name": 'Concrete Slab',
            "roughness": 'MediumRough',
            "thickness": 0.2,
            "conductivity": 2.31,
            "density": 2322,
            "specific_heat": 832,
            "thermal_absorptance": 0.9,
            "solar_absorptance": 0.7,
            "visible_absorptance": 0.7
            }
        """
        assert data['type'] == 'EnergyMaterial', \
            'Expected EnergyMaterial. Got {}.'.format(data['type'])

        rough = data['roughness'] if 'roughness' in data and \
            data['roughness'] is not None else 'MediumRough'
        t_abs = data['thermal_absorptance'] if 'thermal_absorptance' in data and \
            data['thermal_absorptance'] is not None else 0.9
        s_abs = data['solar_absorptance'] if 'solar_absorptance' in data and \
            data['solar_absorptance'] is not None else 0.7
        v_abs = data['visible_absorptance'] if 'visible_absorptance' in data else None

        new_mat = cls(data['identifier'], data['thickness'], data['conductivity'],
                      data['density'], data['specific_heat'], rough, t_abs, s_abs, v_abs)
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']

        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.roughness, self.thickness, self.conductivity,
                  self.density, self.specific_heat, self.thermal_absorptance,
                  self.solar_absorptance, self.visible_absorptance)
        comments = ('name', 'roughness', 'thickness {m}', 'conductivity {W/m-K}',
                    'density {kg/m3}', 'specific heat {J/kg-K}', 'thermal absorptance',
                    'solar absorptance', 'visible absorptance')
        return generate_idf_string('Material', values, comments)

    def to_radiance_solar(self, specularity=0.0):
        """Honeybee Radiance material from the solar reflectance of this material."""
        try:
            from honeybee_radiance.modifier.material import Plastic
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        return Plastic.from_single_reflectance(
            clean_rad_string(self.identifier), 1 -
            self.solar_absorptance, specularity,
            self.RADIANCEROUGHTYPES[self.roughness])

    def to_radiance_visible(self, specularity=0.0):
        """Honeybee Radiance material from the visible reflectance of this material."""
        try:
            from honeybee_radiance.modifier.material import Plastic
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        return Plastic.from_single_reflectance(
            clean_rad_string(self.identifier), 1 -
            self.visible_absorptance, specularity,
            self.RADIANCEROUGHTYPES[self.roughness])

    def to_dict(self):
        """Energy Material dictionary representation."""
        base = {
            'type': 'EnergyMaterial',
            'identifier': self.identifier,
            'roughness': self.roughness,
            'thickness': self.thickness,
            'conductivity': self.conductivity,
            'density': self.density,
            'specific_heat': self.specific_heat,
            'thermal_absorptance': self.thermal_absorptance,
            'solar_absorptance': self.solar_absorptance,
            'visible_absorptance': self.visible_absorptance
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.roughness, self.thickness, self.conductivity,
                self.density, self.specific_heat, self.thermal_absorptance,
                self.solar_absorptance, self.visible_absorptance)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyMaterial) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = self.__class__(
            self.identifier, self.thickness, self.conductivity, self.density,
            self.specific_heat, self.roughness, self.thermal_absorptance,
            self.solar_absorptance, self._visible_absorptance)
        new_material._display_name = self._display_name
        return new_material


@lockable
class EnergyMaterialNoMass(_EnergyMaterialOpaqueBase):
    """Typical no mass opaque energy material.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        r_value: Number for the R-value of the material [m2-K/W].
        roughness: Text describing the relative roughness of the material.
            Must be one of the following: 'VeryRough', 'Rough', 'MediumRough',
            'MediumSmooth', 'Smooth', 'VerySmooth'. Default: 'MediumRough'.
        thermal_absorptance: A number between 0 and 1 for the fraction of
            incident long wavelength radiation that is absorbed by the material.
            Default: 0.9.
        solar_absorptance: A number between 0 and 1 for the fraction of incident
            solar radiation absorbed by the material. Default: 0.7.
        visible_absorptance: A number between 0 and 1 for the fraction of incident
            visible wavelength radiation absorbed by the material.
            Default value is None, which will use the same value as the
            solar_absorptance.

    Properties:
        * identifier
        * display_name
        * r_value
        * u_value
        * roughness
        * thermal_absorptance
        * solar_absorptance
        * visible_absorptance
        * solar_reflectance
        * visible_reflectance
        * mass_area_density
        * area_heat_capacity
    """
    __slots__ = ('_r_value', '_roughness', '_thermal_absorptance',
                 '_solar_absorptance', '_visible_absorptance')

    def __init__(self, identifier, r_value, roughness='MediumRough',
                 thermal_absorptance=0.9, solar_absorptance=0.7,
                 visible_absorptance=None):
        """Initialize energy material."""
        _EnergyMaterialOpaqueBase.__init__(self, identifier)
        self.r_value = r_value
        self.roughness = roughness
        self.thermal_absorptance = thermal_absorptance
        self.solar_absorptance = solar_absorptance
        self.visible_absorptance = visible_absorptance

    @property
    def r_value(self):
        """Get or set the r_value of the material layer [m2-K/W] (excluding air films).
        """
        return self._r_value

    @r_value.setter
    def r_value(self, r_val):
        self._r_value = float_positive(r_val, 'material r-value')

    @property
    def u_value(self):
        """U-value of the material layer [W/m2-K] (excluding air films)."""
        return 1 / self.r_value

    @u_value.setter
    def u_value(self, u_val):
        self._r_value = 1 / float_positive(u_val, 'material u-value')

    @property
    def roughness(self):
        """Get or set the text describing the roughness of the material layer."""
        return self._roughness

    @roughness.setter
    def roughness(self, rough):
        assert rough in self.ROUGHTYPES, 'Invalid input "{}" for material roughness.' \
            ' Roughness must be one of the following:\n'.format(
                rough, self.ROUGHTYPES)
        self._roughness = rough

    @property
    def thermal_absorptance(self):
        """Get or set the thermal absorptance of the material layer."""
        return self._thermal_absorptance

    @thermal_absorptance.setter
    def thermal_absorptance(self, t_abs):
        self._thermal_absorptance = float_in_range(
            t_abs, 0.0, 1.0, 'material thermal absorptance')

    @property
    def solar_absorptance(self):
        """Get or set the solar absorptance of the material layer."""
        return self._solar_absorptance

    @solar_absorptance.setter
    def solar_absorptance(self, s_abs):
        self._solar_absorptance = float_in_range(
            s_abs, 0.0, 1.0, 'material solar absorptance')

    @property
    def visible_absorptance(self):
        """Get or set the visible absorptance of the material layer."""
        return self._visible_absorptance if self._visible_absorptance is not None \
            else self._solar_absorptance

    @visible_absorptance.setter
    def visible_absorptance(self, v_abs):
        self._visible_absorptance = float_in_range(
            v_abs, 0.0, 1.0, 'material visible absorptance') if v_abs is not None \
            else None

    @property
    def solar_reflectance(self):
        """Get or set the front solar reflectance of the material layer."""
        return 1 - self.solar_absorptance

    @solar_reflectance.setter
    def solar_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'material solar reflectance')
        self.solar_absorptance = 1 - v_ref

    @property
    def visible_reflectance(self):
        """Get or set the front visible reflectance of the material layer."""
        return 1 - self.visible_absorptance

    @visible_reflectance.setter
    def visible_reflectance(self, v_ref):
        v_ref = float_in_range(v_ref, 0.0, 1.0, 'material visible reflectance')
        self.visible_absorptance = 1 - v_ref

    @property
    def mass_area_density(self):
        """Returns 0 for the area density of a no mass material."""
        return 0

    @property
    def area_heat_capacity(self):
        """Returns 0 for the heat capacity of a no mass material."""
        return 0

    @classmethod
    def from_idf(cls, idf_string):
        """Create an EnergyMaterialNoMass from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'Material:NoMass,')
        idf_defaults = {3: 0.9, 4: 0.7, 5: 0.7}
        for i, ep_str in enumerate(ep_strs):  # fill in any default values
            if ep_str == '' and i in idf_defaults:
                ep_strs[i] = idf_defaults[i]
        ep_strs.insert(2, ep_strs.pop(1))  # move roughness to correct place
        return cls(*ep_strs)

    @classmethod
    def from_idf_air_gap(cls, idf_string):
        """Create an EnergyMaterialNoMass from an EnergyPlus string of an AirGap.

        Args:
            idf_string: A text string fully describing an EnergyPlus Material:AirGap.
        """
        ep_strs = parse_idf_string(idf_string, 'Material:AirGap,')
        return cls(*ep_strs)

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyMaterialNoMass from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyMaterialNoMass',
            "identifier": 'Insulation_R20_MediumRough_090_070_070',
            "display_name": 'Insulation R2',
            "r_value": 2.0,
            "roughness": 'MediumRough',
            "thermal_absorptance": 0.9,
            "solar_absorptance": 0.7,
            "visible_absorptance": 0.7
            }
        """
        assert data['type'] == 'EnergyMaterialNoMass', \
            'Expected EnergyMaterialNoMass. Got {}.'.format(data['type'])

        rough = data['roughness'] if 'roughness' in data and \
            data['roughness'] is not None else 'MediumRough'
        t_abs = data['thermal_absorptance'] if 'thermal_absorptance' in data and \
            data['thermal_absorptance'] is not None else 0.9
        s_abs = data['solar_absorptance'] if 'solar_absorptance' in data and \
            data['solar_absorptance'] is not None else 0.7
        v_abs = data['visible_absorptance'] if 'visible_absorptance' in data else None

        new_mat = cls(data['identifier'], data['r_value'],
                      rough, t_abs, s_abs, v_abs)
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']
        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (
            self.identifier, self.roughness, self.r_value, self.thermal_absorptance,
            self.solar_absorptance, self.visible_absorptance
        )
        comments = ('name', 'roughness', 'r-value {m2-K/W}', 'thermal absorptance',
                    'solar absorptance', 'visible absorptance')
        return generate_idf_string('Material:NoMass', values, comments)

    def to_radiance_solar(self, specularity=0.0):
        """Honeybee Radiance material from the solar reflectance of this material."""
        try:
            from honeybee_radiance.modifier.material import Plastic
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        return Plastic.from_single_reflectance(
            clean_rad_string(self.identifier), 1 -
            self.solar_absorptance, specularity,
            self.RADIANCEROUGHTYPES[self.roughness])

    def to_radiance_visible(self, specularity=0.0):
        """Honeybee Radiance material from the visible reflectance of this material."""
        try:
            from honeybee_radiance.modifier.material import Plastic
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        return Plastic.from_single_reflectance(
            clean_rad_string(self.identifier), 1 -
            self.visible_absorptance, specularity,
            self.RADIANCEROUGHTYPES[self.roughness])

    def to_dict(self):
        """Energy Material No Mass dictionary representation."""
        base = {
            'type': 'EnergyMaterialNoMass',
            'identifier': self.identifier,
            'r_value': self.r_value,
            'roughness': self.roughness,
            'thermal_absorptance': self.thermal_absorptance,
            'solar_absorptance': self.solar_absorptance,
            'visible_absorptance': self.visible_absorptance
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        return (self.identifier, self.r_value, self.roughness, self.thermal_absorptance,
                self.solar_absorptance, self.visible_absorptance)

    def __hash__(self):
        """A small tuple based on the object properties, useful for hashing."""
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyMaterialNoMass) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_material = self.__class__(
            self.identifier, self.r_value, self.roughness, self.thermal_absorptance,
            self.solar_absorptance, self._visible_absorptance)
        new_material._display_name = self._display_name
        return new_material


@lockable
class EnergyMaterialGreenRoof(_EnergyMaterialOpaqueBase):
    """Green Roof Material
    https://bigladdersoftware.com/epx/docs/9-5/input-output-reference/group-surface-construction-elements.html#materialroofvegetation"""
    __slots__ = ('_plant_height', '_leaf_area_ind', '_leaf_reflectivity',
                 '_leaf_emissivity', '_min_stomatal_res', '_soil_layer_name',
                 '_roughness', '_thickness', '_conductivity', '_density',
                 '_specific_heat', '_thermal_absorptance', '_solar_absorptance', '_visible_absorptance',
                 '_sat_vol_moist_cont', '_res_vol_moist_cont', '_init_vol_moist_cont',
                 '_moist_dif_calc')

    def __init__(self, identifier, thickness=0.1, conductivity=0.35, density=1100, specific_heat=800,
                 roughness='MediumRough', thermal_absorptance=0.9,
                 solar_absorptance=0.7, visible_absorptance=None, plant_height=0.2,
                 leaf_area_ind=1.0, leaf_reflectivity=0.22, leaf_emissivity=0.95,
                 min_stomatal_res=180, soil_layer_name='GreenRoofSoil',
                 sat_vol_moist_cont=0.3, res_vol_moist_cont=0.01, init_vol_moist_cont=0.1,
                 moist_dif_calc='Simple'):
        self.thickness = thickness
        self.conductivity = conductivity
        self.density = density
        self.specific_heat = specific_heat
        self.roughness = roughness
        self.thermal_absorptance = thermal_absorptance
        self.solar_absorptance = solar_absorptance
        self.visible_absorptance = visible_absorptance
        self.plant_height = plant_height
        self.leaf_area_ind = leaf_area_ind
        self.leaf_reflectivity = leaf_reflectivity
        self.leaf_emissivity = leaf_emissivity
        self.min_stomatal_res = min_stomatal_res
        self.soil_layer_name = soil_layer_name
        self.sat_vol_moist_cont = sat_vol_moist_cont
        self.res_vol_moist_cont = res_vol_moist_cont
        self.init_vol_moist_cont = init_vol_moist_cont
        self.moist_dif_calc = moist_dif_calc

    @property
    def roughness(self):
        """Get or set the text describing the roughness of the material layer."""
        return self._roughness

    @roughness.setter
    def roughness(self, rough):
        assert rough in self.ROUGHTYPES, 'Invalid input "{}" for material roughness.' \
            ' Roughness must be one of the following:\n'.format(
                rough, self.ROUGHTYPES)
        self._roughness = rough

    @property
    def thickness(self):
        """Get or set the thickess of the material layer [m]."""
        return self._thickness

    @thickness.setter
    def thickness(self, thick):
        self._thickness = float_positive(thick, 'material thickness')
        self._compare_thickness_conductivity()

    @property
    def conductivity(self):
        """Get or set the conductivity of the material layer [W/m-K]."""
        return self._conductivity

    @conductivity.setter
    def conductivity(self, cond):
        self._conductivity = float_positive(cond, 'material conductivity')
        self._compare_thickness_conductivity()

    @property
    def density(self):
        """Get or set the density of the material layer [kg/m3]."""
        return self._density

    @density.setter
    def density(self, dens):
        self._density = float_positive(dens, 'material density')

    @property
    def specific_heat(self):
        """Get or set the specific heat of the material layer [J/kg-K]."""
        return self._specific_heat

    @specific_heat.setter
    def specific_heat(self, sp_ht):
        self._specific_heat = float_in_range(
            sp_ht, 100.0, input_name='material specific heat')

    @property
    def thermal_absorptance(self):
        """Get or set the thermal absorptance of the material layer."""
        return self._thermal_absorptance

    @thermal_absorptance.setter
    def thermal_absorptance(self, t_abs):
        self._thermal_absorptance = float_in_range(
            t_abs, 0.0, 1.0, 'material thermal absorptance')

    @property
    def solar_absorptance(self):
        """Get or set the solar absorptance of the material layer."""
        return self._solar_absorptance

    @solar_absorptance.setter
    def solar_absorptance(self, s_abs):
        self._solar_absorptance = float_in_range(
            s_abs, 0.0, 1.0, 'material solar absorptance')

    @property
    def visible_absorptance(self):
        """Get or set the visible absorptance of the material layer."""
        return self._visible_absorptance if self._visible_absorptance is not None \
            else self._solar_absorptance

    @visible_absorptance.setter
    def visible_absorptance(self, v_abs):
        self._visible_absorptance = float_in_range(
            v_abs, 0.0, 1.0, 'material visible absorptance') if v_abs is not None \
            else None

    @property
    def plant_height(self):
        return(self._plant_height)

    @plant_height.setter
    def plant_height(self, p_h):
        self._plant_height = float_in_range(
            p_h, 0.005, 1.000, 'plant height') if p_h is not None \
            else None

    @property
    def leaf_area_ind(self):
        return(self._leaf_area_ind)

    @leaf_area_ind.setter
    def leaf_area_ind(self, lai):
        self._leaf_area_ind = float_in_range(
            lai, 0.001, 5.00, 'leaf area index') if lai is not None \
            else None

    @property
    def leaf_reflectivity(self):
        return(self._leaf_reflectivity)

    @leaf_reflectivity.setter
    def leaf_reflectivity(self, l_r):
        self._leaf_reflectivity = float_in_range(
            l_r, 0.05, 0.50, 'leaf reflectivity') if l_r is not None \
            else None

    @property
    def leaf_emissivity(self):
        return(self._leaf_emissivity)

    @leaf_emissivity.setter
    def leaf_emissivity(self, l_e):
        self._leaf_emissivity = float_in_range(
            l_e, 0.8, 1.0) if l_e is not None \
            else None

    @property
    def min_stomatal_res(self):
        return(self._min_stomatal_res)

    @min_stomatal_res.setter
    def min_stomatal_res(self, msr):
        self._min_stomatal_res = float_in_range(
            msr, 50.0, 300.0, 'minimum stomatal resistance') if msr is not None \
            else None

    @property
    def soil_layer_name(self):
        return(self._soil_layer_name)

    @soil_layer_name.setter
    def soil_layer_name(self, sln):
        self._soil_layer_name = sln if sln is not None \
            else None

    @property
    def sat_vol_moist_cont(self):
        return(self._sat_vol_moist_cont)

    @sat_vol_moist_cont.setter
    def sat_vol_moist_cont(self, svmc):
        self._sat_vol_moist_cont = float_in_range(
            svmc, 0.1, 0.5, 'saturation volumetric moisture content of soil layer') \
            if svmc is not None \
            else None

    @property
    def res_vol_moist_cont(self):
        return(self._res_vol_moist_cont)

    @res_vol_moist_cont.setter
    def res_vol_moist_cont(self, rvmc):
        self._res_vol_moist_cont = float_in_range(
            rvmc, 0.01, 0.1) if rvmc is not None \
            else None

    @property
    def init_vol_moist_cont(self):
        return(self._init_vol_moist_cont)

    @init_vol_moist_cont.setter
    def init_vol_moist_cont(self, ivmc):
        self._init_vol_moist_cont = float_in_range(
            ivmc, 0.05, 0.50) if ivmc is not None \
            else None

    @property
    def moist_dif_calc(self):
        return(self._moist_dif_calc)

    @moist_dif_calc.setter
    def moist_dif_calc(self, mdc):
        if mdc == 'Simple':
            self._moist_dif_calc = mdc
        else:
            self._moist_dif_calc = 'Simple'

    @classmethod
    def from_idf(cls, idf_string):
        """Create an EnergyMaterial from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'Material:RoofVegetation,')
        return cls(*ep_strs)

    @classmethod
    def from_dict(cls, data):
        """Create an EnergyMaterialGreenRoof from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyMaterialGreenRoof',
            "identifier": 'My_New_Green_Roof_040_110_5834_654',
            "display_name": 'My green roof',
            "thickness"

            }

        """
        assert data['type'] == 'EnergyMaterialGreenRoof', \
            'Expectend EnergyMaterialGreenRoof. Got {}'.format(data['type'])
        # Use .setter arg_names
        # For setting default values from dict to obj:
        rough = data['roughness'] if 'roughness' in data and \
            data['roughness'] is not None else 'MediumRough'
        thick = data['thickness'] if 'thickness' in data and \
            data['thickness'] is not None else 0.1
        t_abs = data['thermal_absorptance'] if 'thermal_absorptance' in data and \
            data['thermal_absorptance'] is not None else 0.9
        s_abs = data['solar_absorptance'] if 'solar_absorptance' in data and \
            data['solar_absorptance'] is not None else 0.7
        v_abs = data['visible_absorptance'] if 'visible_absorptance' in data else None
        cond = data['conductivity'] if 'conductivity' in data and \
            data['conductivity'] is not None else 0.35
        dens = data['density'] if 'density' in data and \
            data['density'] is not None else 1100
        sp_ht = data['specific_heat'] if 'specific_heat' in data and \
            data['specific_heat'] is not None else 800
        p_h = data['plant_height'] if 'plant_height' in data and \
            data['plant_height'] is not None else 0.2
        lai = data['leaf_area_index'] if 'leaf_area_index' in data and \
            data['leaf_area_index'] is not None else 1.0
        l_r = data['leaf_reflectivity'] if 'leaf_reflectivity' in data and \
            data['leaf_reflectivity'] is not None else 0.22
        l_e = data['leaf_emissivity'] if 'leaf_emissivity' in data and \
            data['leaf_emissivity'] is not None else 0.95
        msr = data['min_stomatal_res'] if 'min_stomatal_res' in data and \
            data['min_stomatal_res'] is not None else 180
        sln = data['soil_layer_name'] if 'soil_layer_name' in data and \
            data['soil_layer_name'] is not None else 'GreenRoofSoil'
        svmc = data['sat_vol_moist_cont'] if 'sat_vol_moist_cont' \
            in data and data['sat_vol_moist_cont'] is not None else 0.3
        rvmc = data['res_vol_moist_cont'] if 'res_vol_moist_cont' \
            in data and data['res_vol_moist_cont'] is not None else 0.01
        ivmc = data['init_vol_moist_cont'] if 'init_vol_moist_cont' \
            in data and data['init_vol_moist_cont'] is not None else 0.1
        mdc = data['moist_dif_calc'] if 'moist_dif_calc' in data and \
            data['moist_dif_calc'] is not None else 'Simple'

        new_mat = cls(rough, thick, t_abs, s_abs, v_abs, dense, sp_ht, p_h, lai,
                      l_r, l_e, msr, sln, svmc, rvmc, ivmc, mdc)
        if 'display_name' in data and data['display_name'] is not None:
            new_mat.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_mat.user_data = data['user_data']

        return new_mat

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.plant_height, self.leaf_area_ind,
                  self.leaf_reflectivity, self.leaf_emissivity, self.min_stomatal_res,
                  self.soil_layer_name, self.roughness, self.thickness, self.conductivity,
                  self.density, self.specific_heat, self.thermal_absorptance,
                  self.solar_absorptance, self.visible_absorptance,
                  self.sat_vol_moist_cont, self.res_vol_moist_cont, self.init_vol_moist_cont,
                  self.moist_dif_calc)
        comments = ('name', 'height of plants', 'leaf area index', 'leaf reflectivity',
                    'leaf emissivity', 'minimum stomatal resistance', 'soil layer name',
                    'roughness', 'thickness', 'conductivity of dry soil', 'density of dry soil',
                    'specific heat of dry soil', 'thermal absorptance', 'solar absorptance',
                    'visible absorptance', 'saturation volumetric moisture content of the soil layer',
                    'residual volumetric moisture content of the soil layer',
                    'initial volumetric moisture content of the soil layer',
                    'moisture diffusion calculation method')
        return generate_idf_string('Material:RoofVegetation', values, comments)

    def to_dict(self):
        base = {
            'type': 'EnergyMaterialGreenRoof',
            'identifier': self.identifier,
            'plant_height': self.plant_height,
            'leaf_area_ind': self.leaf_area_ind,
            'leaf_reflectivity': self.leaf_reflectivity,
            'leaf_emissivity': self.leaf_emissivity,
            'min_stomatal_res': self.min_stomatal_res,
            'soil_layer_name': self.soil_layer_name,
            'roughness': self.roughness,
            'thickness': self.thickness,
            'conductivity': self.conductivity,
            'density': self.density,
            'specific_heat': self.specific_heat,
            'thermal_absorptance': self.thermal_absorptance,
            'solar_absorptance': self.solar_absorptance,
            'visible_absorptance': self.visible_absorptance,
            'sat_vol_moist_cont': self.sat_vol_moist_cont,
            'res_vol_moist_cont': self.res_vol_moist_cont,
            'init_vol_moist_cont': self.init_vol_moist_cont,
            'moist_dif_calc': self.moist_dif_calc
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.plant_height, self.leaf_area_ind,
                self.leaf_reflectivity, self.leaf_emissivity, self.min_stomatal_res,
                self.soil_layer_name, self.roughness, self.thickness, self.conductivity,
                self.density, self.specific_heat, self.thermal_absorptance,
                self.solar_absorptance, self.visible_absorptance,
                self.sat_vol_moist_cont, self.res_vol_moist_cont, self.init_vol_moist_cont,
                self.moist_dif_calc)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyMaterialGreenRoof) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __copy__(self):
        new_material = self.__class__(self.identifier, self.plant_height, self.leaf_area_ind,
                                      self.leaf_reflectivity, self.leaf_emissivity, self.min_stomatal_res,
                                      self.soil_layer_name, self.roughness, self.thickness, self.conductivity,
                                      self.density, self.specific_heat, self.thermal_absorptance,
                                      self.solar_absorptance, self.visible_absorptance,
                                      self.sat_vol_moist_cont, self.res_vol_moist_cont, self.init_vol_moist_cont,
                                      self.moist_dif_calc)
        new_material._display_name = self._display_name
        return new_material
