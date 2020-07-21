# coding=utf-8
"""Window Construction."""
from __future__ import division

from ._base import _ConstructionBase
from ..material.dictutil import dict_to_material
from ..material._base import _EnergyMaterialWindowBase
from ..material.glazing import _EnergyWindowMaterialGlazingBase, \
    EnergyWindowMaterialGlazing, EnergyWindowMaterialSimpleGlazSys
from ..material.gas import _EnergyWindowMaterialGasBase, EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom
from ..material.shade import EnergyWindowMaterialShade, EnergyWindowMaterialBlind
from ..reader import parse_idf_string

from honeybee._lockable import lockable
from honeybee.typing import clean_rad_string

import re
import os


@lockable
class WindowConstruction(_ConstructionBase):
    """Window energy construction.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        materials: List of materials in the construction (from outside to inside).
            The first and last layer must be a glazing layer. Adjacent glass layers
            be separated by one and only one gas layer. When using a Simple Glazing
            System material, it must be the only material.

    Properties:
        * identifier
        * display_name
        * materials
        * layers
        * unique_materials
        * r_value
        * u_value
        * u_factor
        * r_factor
        * is_symmetric
        * inside_emissivity
        * outside_emissivity
        * solar_transmittance
        * visible_transmittance
        * thickness
        * glazing_count
        * gap_count
    """
    __slots__ = ()

    @property
    def materials(self):
        """Get or set the list of materials in the construction (outside to inside).

        The following rules apply:

            * The first and last layer must be a glazing layer.
            * When using a Simple Glazing System material, it must be the only material.
            * Adjacent glass layers must be separated by one and only one gas layer
            * Shades/blinds are not allowed; WindowConstructionShade must be used
        """
        return self._materials

    @materials.setter
    def materials(self, mats):
        try:
            if not isinstance(mats, tuple):
                mats = tuple(mats)
        except TypeError:
            raise TypeError('Expected list or tuple for construction materials. '
                            'Got {}'.format(type(mats)))
        assert len(mats) > 0, 'Construction must possess at least one material.'
        assert len(mats) <= 8, 'Window construction cannot have more than 8 materials.'
        assert not isinstance(mats[0], _EnergyWindowMaterialGasBase), \
            'Window construction cannot have gas gap layers on the outside layer.'
        assert not isinstance(mats[-1], _EnergyWindowMaterialGasBase), \
            'Window construction cannot have gas gap layers on the inside layer.'
        glazing_layer = False
        for i, mat in enumerate(mats):
            assert isinstance(mat, _EnergyMaterialWindowBase), 'Expected window energy' \
                ' material for construction. Got {}.'.format(type(mat))
            if isinstance(mat, EnergyWindowMaterialSimpleGlazSys):
                assert len(mats) == 1, 'Only one material layer is allowed when using' \
                    ' EnergyWindowMaterialSimpleGlazSys'
            elif isinstance(mat, _EnergyWindowMaterialGasBase):
                assert glazing_layer, 'Gas layer must be adjacent to a glazing layer.'
                glazing_layer = False
            elif isinstance(mat, _EnergyWindowMaterialGlazingBase):
                assert not glazing_layer, 'Two adjacent glazing layers are not allowed.'
                glazing_layer = True
            else:  # it's a shade material
                raise ValueError(
                    'Shades and blinds are not permittend within WindowConstruction.\n'
                    'Use the WindowConstructionShade to add shades and blinds.')
        self._materials = mats

    @property
    def r_factor(self):
        """Construction R-factor [m2-K/W] (including standard resistances for air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        gap_count = self.gap_count
        if gap_count == 0:  # single pane or simple glazing system
            return self.materials[0].r_value + (1 / self.out_h_simple()) + \
                (1 / self.in_h_simple())
        r_vals, emissivities = self._layered_r_value_initial(gap_count)
        r_vals = self._solve_r_values(r_vals, emissivities)
        return sum(r_vals)

    @property
    def r_value(self):
        """R-value of the construction [m2-K/W] (excluding air films).

        Note that shade materials are currently considered impermeable to air within
        the U-value calculation.
        """
        gap_count = self.gap_count
        if gap_count == 0:  # single pane or simple glazing system
            return self.materials[0].r_value
        r_vals, emissivities = self._layered_r_value_initial(gap_count)
        r_vals = self._solve_r_values(r_vals, emissivities)
        return sum(r_vals[1:-1])

    @property
    def inside_emissivity(self):
        """"The emissivity of the inside face of the construction."""
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        try:
            return self.materials[-1].emissivity_back
        except AttributeError:
            return self.materials[-1].emissivity

    @property
    def outside_emissivity(self):
        """"The emissivity of the outside face of the construction."""
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            return 0.84
        return self.materials[0].emissivity

    @property
    def solar_transmittance(self):
        """The solar transmittance of the window at normal incidence."""
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            # E+ interprets ~80% of solar heat gain from direct solar transmission
            return self.materials[0].shgc * 0.8
        trans = 1
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                trans *= mat.solar_transmittance
        return trans

    @property
    def visible_transmittance(self):
        """The visible transmittance of the window at normal incidence."""
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            return self.materials[0].vt
        trans = 1
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                trans *= mat.visible_transmittance
        return trans

    @property
    def thickness(self):
        """Thickness of the construction [m]."""
        thickness = 0
        for mat in self.materials:
            thickness += mat.thickness
        return thickness

    @property
    def glazing_count(self):
        """The number of glazing materials contained within the window construction.

        Note that Simple Glazing System materials do not count.
        """
        count = 0
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                count += 1
        return count

    @property
    def gap_count(self):
        """The number of gas gaps contained within the window construction."""
        count = 0
        for i, mat in enumerate(self.materials):
            if isinstance(mat, _EnergyWindowMaterialGasBase):
                count += 1
        return count

    def temperature_profile(self, outside_temperature=-18, inside_temperature=21,
                            wind_speed=6.7, height=1.0, angle=90.0, pressure=101325):
        """Get a list of temperatures at each material boundary across the construction.

        Args:
            outside_temperature: The temperature on the outside of the construction [C].
                Default is -18, which is consistent with NFRC 100-2010.
            inside_temperature: The temperature on the inside of the construction [C].
                Default is 21, which is consistent with NFRC 100-2010.
            wind_speed: The average outdoor wind speed [m/s]. This affects outdoor
                convective heat transfer coefficient. Default is 6.7 m/s.
            height: An optional height for the surface in meters. Default is 1.0 m.
            angle: An angle in degrees between 0 and 180.
                0 = A horizontal surface with the outside boundary on the bottom.
                90 = A vertical surface
                180 = A horizontal surface with the outside boundary on the top.
            pressure: The average pressure of in Pa.
                Default is 101325 Pa for standard pressure at sea level.

        Returns:
            A tuple with two elements

            -   temperatures: A list of temperature values [C].
                The first value will always be the outside temperature and the
                second will be the exterior surface temperature.
                The last value will always be the inside temperature and the second
                to last will be the interior surface temperature.

            -   r_values: A list of R-values for each of the material layers [m2-K/W].
                The first value will always be the resistance of the exterior air
                and the last value is the resistance of the interior air.
                The sum of this list is the R-factor for this construction given
                the input parameters.
        """
        # reverse the angle if the outside temperature is greater than the inside one
        if angle != 90 and outside_temperature > inside_temperature:
            angle = abs(180 - angle)
        gap_count = self.gap_count

        # single pane or simple glazing system
        if gap_count == 0:
            in_r_init = 1 / self.in_h_simple()
            r_values = [1 / self.out_h(wind_speed, outside_temperature + 273.15),
                        self.materials[0].r_value, in_r_init]
            in_delta_t = (in_r_init / sum(r_values)) * \
                (outside_temperature - inside_temperature)
            r_values[-1] = 1 / self.in_h(inside_temperature - (in_delta_t / 2) + 273.15,
                                         in_delta_t, height, angle, pressure)
            temperatures = self._temperature_profile_from_r_values(
                r_values, outside_temperature, inside_temperature)
            return temperatures, r_values

        # multi-layered window construction
        guess = abs(inside_temperature - outside_temperature) / 2
        guess = 1 if guess < 1 else guess  # prevents zero division with gas conductance
        avg_guess = ((inside_temperature + outside_temperature) / 2) + 273.15
        r_values, emissivities = self._layered_r_value_initial(
            gap_count, guess, avg_guess, wind_speed)
        r_last = 0
        r_next = sum(r_values)
        while abs(r_next - r_last) > 0.001:  # 0.001 is the r-value tolerance
            r_last = sum(r_values)
            temperatures = self._temperature_profile_from_r_values(
                r_values, outside_temperature, inside_temperature)
            r_values = self._layered_r_value(
                temperatures, r_values, emissivities, height, angle, pressure)
            r_next = sum(r_values)
        temperatures = self._temperature_profile_from_r_values(
            r_values, outside_temperature, inside_temperature)
        return temperatures, r_values

    @classmethod
    def from_idf(cls, idf_string, ep_mat_strings):
        """Create an WindowConstruction from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus construction.
            ep_mat_strings: A list of text strings for each of the materials in
                the construction.
        """
        materials_dict = cls._idf_materials_dictionary(ep_mat_strings)
        ep_strs = parse_idf_string(idf_string)
        try:
            materials = [materials_dict[mat.upper()] for mat in ep_strs[1:]]
        except KeyError as e:
            raise ValueError('Failed to find {} in the input ep_mat_strings.'.format(e))
        return cls(ep_strs[0], materials)

    @classmethod
    def from_dict(cls, data):
        """Create a WindowConstruction from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'WindowConstruction',
            "identifier": 'Generic Double Pane U-250 SHGC-035',
            "display_name": 'Double Pane Window',
            "materials": []  # list of material objects
            "layers": [],  # list of material identifiers (from outside to inside)
            }
        """
        assert data['type'] == 'WindowConstruction', \
            'Expected WindowConstruction. Got {}.'.format(data['type'])
        materials = {}
        for mat in data['materials']:
            materials[mat['identifier']] = dict_to_material(mat)
        mat_layers = [materials[mat_id] for mat_id in data['layers']]
        new_obj = cls(data['identifier'], mat_layers)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, materials):
        """Create a WindowConstruction from an abridged dictionary.

        Args:
            data: An WindowConstructionAbridged dictionary with the format below.
            materials: A dictionary with identifiers of materials as keys and
                Python material objects as values.

        .. code-block:: python

            {
            "type": 'WindowConstructionAbridged',
            "identifier": 'Generic Double Pane U-250 SHGC-035',
            "display_name": 'Double Pane Window',
            "layers": [],  # list of material identifiers (from outside to inside)
            }
        """
        assert data['type'] == 'WindowConstructionAbridged', \
            'Expected WindowConstructionAbridged. Got {}.'.format(data['type'])
        mat_layers = [materials[mat_id] for mat_id in data['layers']]
        new_obj = cls(data['identifier'], mat_layers)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        return new_obj

    def to_idf(self):
        """IDF string representation of construction object.

        Note that this method only outputs a single string for the construction and,
        to write the full construction into an IDF, the construction's unique_materials
        must also be written.

        Returns:
            construction_idf -- Text string representation of the construction.
        """
        return self._generate_idf_string('window', self.identifier, self.materials)

    def to_radiance_solar(self):
        """Honeybee Radiance material with the solar transmittance."""
        try:
            from honeybee_radiance.modifier.material import Glass
            from honeybee_radiance.modifier.material import Trans
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        diffusing = False
        trans = 1
        for mat in self.materials:
            if isinstance(mat, EnergyWindowMaterialSimpleGlazSys):
                trans *= mat.shgc * 0.8
            elif isinstance(mat, EnergyWindowMaterialGlazing):
                trans *= mat.solar_transmittance
                diffusing = True if mat.solar_diffusing is True else False
        if not diffusing:
            return Glass.from_single_transmittance(
                clean_rad_string(self.identifier), trans)
        else:
            try:
                ref = self.materials[-1].solar_reflectance_back
            except AttributeError:
                ref = self.materials[-1].solar_reflectance
            return Trans.from_single_reflectance(
                clean_rad_string(self.identifier), rgb_reflectance=ref,
                transmitted_diff=trans, transmitted_spec=0)

    def to_radiance_visible(self):
        """Honeybee Radiance material with the visible transmittance."""
        try:
            from honeybee_radiance.modifier.material import Glass
            from honeybee_radiance.modifier.material import Trans
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_visible() method. {}'.format(e))
        diffusing = False
        trans = 1
        for mat in self.materials:
            if isinstance(mat, EnergyWindowMaterialSimpleGlazSys):
                trans *= mat.vt
            elif isinstance(mat, EnergyWindowMaterialGlazing):
                trans *= mat.visible_transmittance
                diffusing = True if mat.solar_diffusing is True else False
        if not diffusing:
            return Glass.from_single_transmittance(
                clean_rad_string(self.identifier), trans)
        else:
            try:
                ref = self.materials[-1].solar_reflectance_back
            except AttributeError:
                ref = self.materials[-1].solar_reflectance
            return Trans.from_single_reflectance(
                clean_rad_string(self.identifier), rgb_reflectance=ref,
                transmitted_diff=trans, transmitted_spec=0)

    def to_dict(self, abridged=False):
        """Window construction dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of material layers. Default: False.
        """
        base = {'type': 'WindowConstruction'} if not \
            abridged else {'type': 'WindowConstructionAbridged'}
        base['identifier'] = self.identifier
        base['layers'] = self.layers
        if not abridged:
            base['materials'] = [m.to_dict() for m in self.unique_materials]
        if self._display_name is not None:
            base['display_name'] = self.display_name
        return base

    @staticmethod
    def extract_all_from_idf_file(idf_file):
        """Get all WindowConstruction objects in an EnergyPlus IDF file.

        Args:
            idf_file: A path to an IDF file containing objects for window
                constructions and corresponding materials. For example, the
                IDF Report output by LBNL WINDOW.

        Returns:
            A tuple with two elements

            -   constructions: A list of all WindowConstruction objects in the IDF
                file as honeybee_energy WindowConstruction objects.

            -   materials: A list of all window materials in the IDF file as
                honeybee_energy Material objects.
        """
        # check the file
        assert os.path.isfile(idf_file), 'Cannot find an idf file at {}'.format(idf_file)
        with open(idf_file, 'r') as ep_file:
            file_contents = ep_file.read()
        # extract all material objects
        mat_pattern = re.compile(r"(?i)(WindowMaterial:[\s\S]*?;)")
        material_str = mat_pattern.findall(file_contents)
        materials_dict = WindowConstruction._idf_materials_dictionary(material_str)
        materials = list(materials_dict.values())
        # extract all of the construction objects
        constr_pattern = re.compile(r"(?i)(Construction,[\s\S]*?;)")
        constr_props = tuple(parse_idf_string(idf_string) for
                             idf_string in constr_pattern.findall(file_contents))
        constructions = []
        for constr in constr_props:
            try:
                constr_mats = [materials_dict[mat.upper()] for mat in constr[1:]]
                try:
                    constructions.append(WindowConstruction(constr[0], constr_mats))
                except ValueError:
                    pass  # it likely has a blind or a shade and is not serialize-able
            except KeyError:
                pass  # it's an opaque construction or window shaded construction
        return constructions, materials

    @staticmethod
    def _idf_materials_dictionary(ep_mat_strings):
        """Get a dictionary of window EnergyMaterial objects from an IDF string list."""
        materials_dict = {}
        for mat_str in ep_mat_strings:
            mat_str = mat_str.strip()
            mat_obj = None
            if mat_str.startswith('WindowMaterial:SimpleGlazingSystem,'):
                mat_obj = EnergyWindowMaterialSimpleGlazSys.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Glazing,'):
                mat_obj = EnergyWindowMaterialGlazing.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Gas,'):
                try:
                    mat_obj = EnergyWindowMaterialGas.from_idf(mat_str)
                except AssertionError:  # likely a custom gas to serialize differently
                    mat_obj = EnergyWindowMaterialGasCustom.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:GasMixture,'):
                mat_obj = EnergyWindowMaterialGasMixture.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Shade,'):
                mat_obj = EnergyWindowMaterialShade.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Blind,'):
                mat_obj = EnergyWindowMaterialBlind.from_idf(mat_str)
            if mat_obj is not None:
                materials_dict[mat_obj.identifier.upper()] = mat_obj
        return materials_dict

    def _solve_r_values(self, r_vals, emissivities):
        """Iteratively solve for R-values."""
        r_last = 0
        r_next = sum(r_vals)
        while abs(r_next - r_last) > 0.001:  # 0.001 is the r-value tolerance
            r_last = sum(r_vals)
            temperatures = self._temperature_profile_from_r_values(r_vals)
            r_vals = self._layered_r_value(temperatures, r_vals, emissivities)
            r_next = sum(r_vals)
        return r_vals

    def _layered_r_value_initial(self, gap_count, delta_t_guess=15,
                                 avg_t_guess=273.15, wind_speed=6.7):
        """Compute initial r-values of each layer within a layered construction."""
        r_vals = [1 / self.out_h(wind_speed, avg_t_guess - delta_t_guess)]
        emiss = []
        delta_t = delta_t_guess / gap_count
        for i, mat in enumerate(self.materials):
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                r_vals.append(mat.r_value)
                emiss.append(None)
            else:  # gas material
                e_front = self.materials[i + 1].emissivity
                try:
                    e_back = self.materials[i - 1].emissivity_back
                except AttributeError:
                    e_back = self.materials[i - 1].emissivity
                r_vals.append(1 / mat.u_value(
                    delta_t, e_back, e_front, t_kelvin=avg_t_guess))
                emiss.append((e_back, e_front))
        r_vals.append(1 / self.in_h_simple())
        return r_vals, emiss

    def _layered_r_value(self, temperatures, r_values_init, emiss,
                         height=1.0, angle=90.0, pressure=101325):
        """Compute delta_t adjusted r-values of each layer within a construction."""
        r_vals = [r_values_init[0]]
        for i, mat in enumerate(self.materials):
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                r_vals.append(r_values_init[i + 1])
            else:  # gas material
                delta_t = abs(temperatures[i + 1] - temperatures[i + 2])
                avg_temp = ((temperatures[i + 1] + temperatures[i + 2]) / 2) + 273.15
                r_vals.append(1 / mat.u_value_at_angle(
                    delta_t, emiss[i][0], emiss[i][1], height, angle,
                    avg_temp, pressure))
        delta_t = abs(temperatures[-1] - temperatures[-2])
        avg_temp = ((temperatures[-1] + temperatures[-2]) / 2) + 273.15
        r_vals.append(1 / self.in_h(avg_temp, delta_t, height, angle, pressure))
        return r_vals

    def __repr__(self):
        """Represent window energy construction."""
        return self._generate_idf_string('window', self.identifier, self.materials)
