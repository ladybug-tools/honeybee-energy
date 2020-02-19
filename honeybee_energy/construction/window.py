# coding=utf-8
"""Window Construction."""
from __future__ import division

from ._base import _ConstructionBase
from ..material._base import _EnergyMaterialWindowBase
from ..material.glazing import _EnergyWindowMaterialGlazingBase, \
    EnergyWindowMaterialGlazing, EnergyWindowMaterialSimpleGlazSys
from ..material.gas import _EnergyWindowMaterialGasBase, EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom
from ..material.shade import _EnergyWindowMaterialShadeBase, EnergyWindowMaterialShade, \
    EnergyWindowMaterialBlind
from ..reader import parse_idf_string

from honeybee._lockable import lockable

import re
import os


@lockable
class WindowConstruction(_ConstructionBase):
    """Window energy construction.

    Properties:
        * name
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
        * unshaded_solar_transmittance
        * unshaded_visible_transmittance
        * glazing_count
        * gap_count
        * has_shade
        * shade_location
    """
    __slots__ = ('_has_shade',)

    @property
    def materials(self):
        """Get or set a list of materials in the construction (outside to inside)."""
        return self._materials

    @materials.setter
    def materials(self, mats):
        """For multi-layer window constructions the following rules apply in E+:

        * The first and last layer must be a solid layer (glass or shade/screen/blind)
        * Adjacent glass layers must be separated by one and only one gas layer
        * Adjacent layers must not be of the same type
        * Only one shade/screen/blind layer is allowed
        * An exterior shade/screen/blind must be the first layer
        * An interior shade/blind must be the last layer
        * Shades/screens should always be adjacent to glass layers and should never
          be adjacent to gas layers (honeybee takes care of adding the additional gas
          gaps needed by EnergyPlus using the material's distance_to_shade property
          to set the gap thickness).
        * For triple glazing the between-glass shade/blind must be between the two
          inner glass layers. (currently no check)
        * The slat width of a between-glass blind must be less than 2 times the
          blind's distance_to_glass.(currently no check).
        """
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
        has_shade = False
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
            else:  # must be a shade material
                if i != 0:
                    assert glazing_layer, \
                        'Shade layer must be adjacent to a glazing layer.'
                assert not has_shade, 'Constructions can only possess one shade.'
                glazing_layer = False
                has_shade = True
        self._has_shade = has_shade
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
    def unshaded_solar_transmittance(self):
        """The unshaded solar transmittance of the window at normal incidence.

        Note that 'unshaded' means that all shade materials in the construction
        are ignored.
        """
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            # E+ interprets ~80% of solar heat gain from direct solar transmission
            return self.materials[0].shgc * 0.8
        trans = 1
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                trans *= mat.solar_transmittance
        return trans

    @property
    def unshaded_visible_transmittance(self):
        """The unshaded visible transmittance of the window at normal incidence.

        Note that 'unshaded' means that all shade materials in the construction
        are ignored.
        """
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
            if isinstance(mat, (EnergyWindowMaterialGlazing, EnergyWindowMaterialShade,
                                _EnergyWindowMaterialGasBase)):
                thickness += mat.thickness
            elif isinstance(mat, EnergyWindowMaterialBlind):
                thickness += mat.slat_width
        return thickness

    @property
    def glazing_count(self):
        """The number of glazing materials contained within the window construction."""
        count = 0
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGlazingBase):
                count += 1
        return count

    @property
    def gap_count(self):
        """The number of gas gaps contained within the window construction.

        Note that this property will count the distance between shades and glass
        as a gap in addition to any gas layers.
        """
        count = 0
        for i, mat in enumerate(self.materials):
            if isinstance(mat, _EnergyWindowMaterialGasBase):
                count += 1
            elif isinstance(mat, _EnergyWindowMaterialShadeBase):
                if i == 0 or count == len(self.materials) - 1:
                    count += 1
                else:
                    count += 2
        return count

    @property
    def has_shade(self):
        """Boolean noting whether there is a shade or blind in the construction."""
        return self._has_shade

    @property
    def shade_location(self):
        """Text noting the location of shade in the construction.

        This will be one of the following: ('Interior', 'Exterior', 'Between', None).
        None indicates that there is no shade within the construction.
        """
        if isinstance(self.materials[0], _EnergyWindowMaterialShadeBase):
            return 'Exterior'
        elif isinstance(self.materials[-1], _EnergyWindowMaterialShadeBase):
            return 'Interior'
        elif self.has_shade:
            return 'Between'
        else:
            return None

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
        if angle != 90 and outside_temperature > inside_temperature:
            angle = abs(180 - angle)
        gap_count = self.gap_count
        if gap_count == 0:  # single pane or simple glazing system
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
            materials = [materials_dict[mat] for mat in ep_strs[1:]]
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
            "name": 'Generic Double Pane Window',
            "materials": []  # list of material objects
            "layers": [],  # list of material names (from outside to inside)
            }
        """
        assert data['type'] == 'WindowConstruction', \
            'Expected WindowConstruction. Got {}.'.format(data['type'])
        materials = {}
        for mat in data['materials']:
            if mat['type'] == 'EnergyWindowMaterialSimpleGlazSys':
                materials[mat['name']] = EnergyWindowMaterialSimpleGlazSys.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGlazing':
                materials[mat['name']] = EnergyWindowMaterialGlazing.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGas':
                materials[mat['name']] = EnergyWindowMaterialGas.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGasMixture':
                materials[mat['name']] = EnergyWindowMaterialGasMixture.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialGasCustom':
                materials[mat['name']] = EnergyWindowMaterialGasCustom.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialShade':
                materials[mat['name']] = EnergyWindowMaterialShade.from_dict(mat)
            elif mat['type'] == 'EnergyWindowMaterialBlind':
                materials[mat['name']] = EnergyWindowMaterialBlind.from_dict(mat)
            else:
                raise NotImplementedError(
                    'Material {} is not supported.'.format(mat['type']))
        mat_layers = [materials[mat_name] for mat_name in data['layers']]
        return cls(data['name'], mat_layers)

    @classmethod
    def from_dict_abridged(cls, data, materials):
        """Create a WindowConstruction from an abridged dictionary.

        Args:
            data: An WindowConstructionAbridged dictionary with the format below.
            materials: A dictionary with names of materials as keys and Python
                material objects as values.

        .. code-block:: python

            {
            "type": 'WindowConstructionAbridged',
            "name": 'Generic Double Pane Window',
            "layers": [],  # list of material names (from outside to inside)
            }
        """
        assert data['type'] == 'WindowConstructionAbridged', \
            'Expected WindowConstructionAbridged. Got {}.'.format(data['type'])
        mat_layers = [materials[mat_name] for mat_name in data['layers']]
        return cls(data['name'], mat_layers)

    def to_idf(self):
        """IDF string representation of construction object.

        Note that this method only outputs a single string for the construction and,
        to write the full construction into an IDF, the construction's unique_materials
        must also be written.

        Returns:
            construction_idf -- Text string representation of the construction.
        """
        construction_idf = self._generate_idf_string('window', self.name, self.materials)
        return construction_idf

    def to_radiance_solar(self):
        """Honeybee Radiance material with the solar transmittance."""
        try:
            from honeybee_radiance.primitive.material.glass import Glass
            from honeybee_radiance.primitive.material.trans import Trans
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
            elif isinstance(mat, EnergyWindowMaterialShade):
                trans *= mat.solar_transmittance
                diffusing = True
            elif isinstance(mat, EnergyWindowMaterialBlind):
                raise NotImplementedError('to_radiance_solar() is not supported for '
                                          'window constructions with blind materials.')
        if diffusing is False:
            return Glass.from_single_transmittance(self.name, trans)
        else:
            try:
                ref = self.materials[-1].solar_reflectance_back
            except AttributeError:
                ref = self.materials[-1].solar_reflectance
            return Trans.from_single_reflectance(
                self.name, rgb_reflectance=ref,
                transmitted_diff=trans, transmitted_spec=0)

    def to_radiance_visible(self, specularity=0.0):
        """Honeybee Radiance material with the visible transmittance."""
        try:
            from honeybee_radiance.primitive.material.glass import Glass
            from honeybee_radiance.primitive.material.trans import Trans
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
            elif isinstance(mat, EnergyWindowMaterialShade):
                trans *= mat.visible_transmittance
                diffusing = True
            elif isinstance(mat, EnergyWindowMaterialBlind):
                raise NotImplementedError('to_radiance_visible() is not supported for '
                                          'window constructions with blind materials.')
        if diffusing is False:
            return Glass.from_single_transmittance(self.name, trans)
        else:
            try:
                ref = self.materials[-1].solar_reflectance_back
            except AttributeError:
                ref = self.materials[-1].solar_reflectance
            return Trans.from_single_reflectance(
                self.name, rgb_reflectance=ref,
                transmitted_diff=trans, transmitted_spec=0)

    def to_dict(self, abridged=False):
        """Window construction dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the names of material layers. Default: False.
        """
        base = {'type': 'WindowConstruction'} if not \
            abridged else {'type': 'WindowConstructionAbridged'}
        base['name'] = self.name
        base['layers'] = self.layers
        if not abridged:
            base['materials'] = [m.to_dict() for m in self.unique_materials]
        return base

    @staticmethod
    def extract_all_from_idf_file(idf_file):
        """Get all WindowConstruction objects in an EnergyPlus IDF file.

        Args:
            idf_file: A path to an IDF file containing objects for window
                constructions and corresponding materials. For example, the
                IDF Report output by LBNL WINDOW.
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
                constr_mats = [materials_dict[mat] for mat in constr[1:]]
                constructions.append(WindowConstruction(constr[0], constr_mats))
            except KeyError:
                pass  # the construction is an opaque construction
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
                mat_obj = EnergyWindowMaterialGas.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:GasMixture,'):
                mat_obj = EnergyWindowMaterialGasMixture.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Shade,'):
                mat_obj = EnergyWindowMaterialShade.from_idf(mat_str)
            elif mat_str.startswith('WindowMaterial:Blind,'):
                mat_obj = EnergyWindowMaterialBlind.from_idf(mat_str)
            if mat_obj is not None:
                materials_dict[mat_obj.name] = mat_obj
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
            elif isinstance(mat, _EnergyWindowMaterialGasBase):
                e_front = self.materials[i + 1].emissivity
                try:
                    e_back = self.materials[i - 1].emissivity_back
                except AttributeError:
                    e_back = self.materials[i - 1].emissivity
                r_vals.append(1 / mat.u_value(
                    delta_t, e_back, e_front, t_kelvin=avg_t_guess))
                emiss.append((e_back, e_front))
            else:  # shade material
                if i == 0:
                    e_back = self.materials[i + 1].emissivity
                    r_vals.append(mat.r_value_exterior(
                        delta_t, e_back, t_kelvin=avg_t_guess))
                    emiss.append(e_back)
                elif i == len(self.materials) - 1:
                    e_front = self.materials[i - 1].emissivity_back
                    r_vals.append(mat.r_value_interior(
                        delta_t, e_front, t_kelvin=avg_t_guess))
                    emiss.append(e_front)
                else:
                    e_back = self.materials[i + 1].emissivity
                    e_front = self.materials[i - 1].emissivity_back
                    r_vals.append(mat.r_value_between(
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
            elif isinstance(mat, _EnergyWindowMaterialGasBase):
                delta_t = abs(temperatures[i + 1] - temperatures[i + 2])
                avg_temp = ((temperatures[i + 1] + temperatures[i + 2]) / 2) + 273.15
                r_vals.append(1 / mat.u_value_at_angle(
                    delta_t, emiss[i][0], emiss[i][1], height, angle,
                    avg_temp, pressure))
            else:  # shade material
                delta_t = abs(temperatures[i + 1] - temperatures[i + 2])
                avg_temp = ((temperatures[i + 1] + temperatures[i + 2]) / 2) + 273.15
                if i == 0:
                    r_vals.append(mat.r_value_exterior(
                        delta_t, emiss[i], height, angle, avg_temp, pressure))
                elif i == len(self.materials) - 1:
                    r_vals.append(mat.r_value_interior(
                        delta_t, emiss[i], height, angle, avg_temp, pressure))
                else:
                    r_vals.append(mat.r_value_between(
                        delta_t, emiss[i][0], emiss[i][1],
                        height, angle, avg_temp, pressure))
        delta_t = abs(temperatures[-1] - temperatures[-2])
        avg_temp = ((temperatures[-1] + temperatures[-2]) / 2) + 273.15
        r_vals.append(1 / self.in_h(avg_temp, delta_t, height, angle, pressure))
        return r_vals

    def __repr__(self):
        """Represent window energy construction."""
        return self._generate_idf_string('window', self.name, self.materials)
