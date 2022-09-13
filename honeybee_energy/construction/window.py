# coding=utf-8
"""Window Construction."""
from __future__ import division

import re

from honeybee._lockable import lockable
from honeybee.typing import clean_rad_string

from ._base import _ConstructionBase
from ..material.dictutil import dict_to_material
from ..material._base import _EnergyMaterialWindowBase
from ..material.glazing import _EnergyWindowMaterialGlazingBase, \
    EnergyWindowMaterialGlazing, EnergyWindowMaterialSimpleGlazSys
from ..material.gas import _EnergyWindowMaterialGasBase, EnergyWindowMaterialGas, \
    EnergyWindowMaterialGasMixture, EnergyWindowMaterialGasCustom
from ..material.shade import EnergyWindowMaterialShade, EnergyWindowMaterialBlind
from ..material.frame import EnergyWindowFrame
from ..reader import parse_idf_string, clean_idf_file_contents
from ..properties.extension import WindowConstructionProperties


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
        frame: An optional window frame material to denote the frame that surrounds
            the window construction. (Default: None).

    Properties:
        * identifier
        * display_name
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
        * solar_reflectance
        * solar_absorptance
        * visible_transmittance
        * visible_reflectance
        * visible_absorptance
        * shgc
        * thickness
        * glazing_count
        * gap_count
        * glazing_materials
        * user_data
    """
    __slots__ = ('_frame',)

    COG_AREA = 0.76
    EDGE_AREA = 0.24

    def __init__(self, identifier, materials, frame=None):
        """Initialize window construction."""
        _ConstructionBase.__init__(self, identifier, materials)
        self.frame = frame
        self._properties = WindowConstructionProperties(self)

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
                    'Shades and blinds are not permitted within WindowConstruction.\n'
                    'Use the WindowConstructionShade to add shades and blinds.')
        self._materials = mats

    @property
    def frame(self):
        """Get or set a window frame for the frame material surrounding the construction.
        """
        return self._frame

    @frame.setter
    def frame(self, value):
        if value is not None:
            assert isinstance(value, EnergyWindowFrame), 'Expected EnergyWindowFrame ' \
                'for WindowConstruction frame. Got {}.'.format(type(value))
        self._frame = value

    @property
    def r_factor(self):
        """Construction R-factor [m2-K/W] (including standard resistances for air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        # figure out the center-of-glass R-value
        gap_count = self.gap_count
        if gap_count == 0:  # single pane or simple glazing system
            cog_r = self.materials[0].r_value + (1 / self.out_h_simple()) + \
                (1 / self.in_h_simple())
        else:
            r_vals, emissivities = self._layered_r_value_initial(gap_count)
            r_vals = self._solve_r_values(r_vals, emissivities)
            cog_r = sum(r_vals)
        if self.frame is None:
            return cog_r
        # if there is a frame, account for it in the final R-value
        glass_u = (1 / cog_r)
        if self.frame.edge_to_center_ratio != 1 and not \
                isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            edge_u = self.frame.edge_to_center_ratio * glass_u
            glass_u = (glass_u * self.COG_AREA) + (edge_u * self.EDGE_AREA)
        frame_r = self.frame.r_value + (1 / self.out_h_simple()) + \
            (1 / self.in_h_simple())
        frame_u = 1 / frame_r
        frame_area = ((1 + self.frame.width) ** 2) - 1
        total_u = (glass_u + (frame_u * frame_area)) / (1 + frame_area)
        return 1 / total_u

    @property
    def r_value(self):
        """R-value of the construction [m2-K/W] (excluding air films).

        Note that shade materials are currently considered impermeable to air within
        the U-value calculation.
        """
        # figure out the center-of-glass R-value
        gap_count = self.gap_count
        if gap_count == 0:  # single pane or simple glazing system
            cog_r = self.materials[0].r_value
        else:
            r_vals, emissivities = self._layered_r_value_initial(gap_count)
            r_vals = self._solve_r_values(r_vals, emissivities)
            cog_r = sum(r_vals[1:-1])
        if self.frame is None:
            return cog_r
        # if there is a frame, account for it in the final R-value
        glass_u = (1 / cog_r)
        if self.frame.edge_to_center_ratio != 1 and not \
                isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            edge_u = self.frame.edge_to_center_ratio * glass_u
            glass_u = (glass_u * self.COG_AREA) + (edge_u * self.EDGE_AREA)
        frame_area = ((1 + self.frame.width) ** 2) - 1
        total_u = (glass_u + (self.frame.u_value * frame_area)) / (1 + frame_area)
        return 1 / total_u

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
        return self.solar_optical_properties()[0]

    @property
    def solar_reflectance(self):
        """The solar reflectance of the window at normal incidence (to the exterior).
        """
        return self.solar_optical_properties()[1]

    @property
    def solar_absorptance(self):
        """Get the combined solar absorptance of all window panes at normal incidence.
        """
        return sum(self.solar_optical_properties()[2])

    @property
    def visible_transmittance(self):
        """The visible transmittance of the window at normal incidence."""
        return self.visible_optical_properties()[0]

    @property
    def visible_reflectance(self):
        """The visible reflectance of the window at normal incidence (to the exterior).
        """
        return self.visible_optical_properties()[1]

    @property
    def visible_absorptance(self):
        """Get the combined visible absorptance of all window panes at normal incidence.
        """
        return sum(self.visible_optical_properties()[2])

    @property
    def shgc(self):
        """Get the solar heat gain coefficient (SHGC) of the construction.

        If this construction is not a simple glazing system, this value is computed
        by summing the transmitted and conducted portions of solar irradiance under
        the NFRC summer conditions of 32C outdoor temperature, 24C indoor temperature,
        and 783 W/m2 of incident solar flux.
        """
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            if self.frame is None:
                return self.materials[0].shgc
        t_out, t_in, sol_irr = 32, 24, 783  # NFRC 2010 summer conditions
        _, r_values = self.temperature_profile(t_out, t_in, solar_irradiance=sol_irr)
        heat_gen, transmitted = self._heat_gen_from_solar(sol_irr)
        conducted = 0
        r_factor = sum(r_values)
        for i, heat_g in enumerate(heat_gen):
            if heat_g != 0:
                conducted += heat_g * (1 - (sum(r_values[i + 1:]) / r_factor))
        if self.frame is None:
            return (transmitted + conducted) / sol_irr
        else:  # account for the frame conduction
            _, r_values = self.temperature_profile_frame(
                t_out, t_in, solar_irradiance=sol_irr)
            heat_gen = [0, sol_irr * self.frame.solar_absorptance, 0]
            frame_conducted = 0
            r_factor = sum(r_values)
            for i, heat_g in enumerate(heat_gen):
                if heat_g != 0:
                    frame_conducted += heat_g * (1 - (sum(r_values[i + 1:]) / r_factor))
            frame_area = ((1 + self.frame.width) ** 2) - 1
            frame_conduct = frame_conducted * frame_area
            frame_sol_irr = sol_irr * frame_area
            return (transmitted + conducted + frame_conduct) / (sol_irr + frame_sol_irr)

    @property
    def thickness(self):
        """Thickness of the construction [m]."""
        thickness = 0
        for mat in self.materials:
            thickness += mat.thickness
        return thickness

    @property
    def inside_solar_reflectance(self):
        """The solar reflectance of the inside face of the construction."""
        return self.materials[-1].solar_reflectance_back

    @property
    def inside_visible_reflectance(self):
        """The visible reflectance of the inside face of the construction."""
        return self.materials[-1].visible_reflectance_back

    @property
    def outside_solar_reflectance(self):
        """The solar reflectance of the outside face of the construction."""
        return self.materials[0].solar_reflectance

    @property
    def outside_visible_reflectance(self):
        """The visible reflectance of the outside face of the construction."""
        return self.materials[0].visible_reflectance

    @property
    def has_frame(self):
        """Get a boolean noting whether the construction has a frame assigned to it."""
        return self.frame is not None

    @property
    def glazing_count(self):
        """The number of glazing materials contained within the window construction.
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
        for mat in self.materials:
            if isinstance(mat, _EnergyWindowMaterialGasBase):
                count += 1
        return count

    @property
    def glazing_materials(self):
        """The only the glazing materials contained within the window construction.
        """
        return [mat for mat in self.materials
                if isinstance(mat, _EnergyWindowMaterialGlazingBase)]

    def solar_optical_properties(self):
        """Get solar transmittance + reflectance, and absorptances for each glass pane.

        Returns:
            A tuple of three values.

            -   transmittance: A transmittance value through all glass panes.

            -   reflectance: A reflectance value from the front of all glass panes.

            -   absorptances: A list of absorptance values through each pane
                of glass. The values in this list correspond to the glass panes
                in the construction.
        """
        # first check whether the construction is a simple glazing system
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            transmittance = self.materials[0].solar_transmittance
            reflectance = self.materials[0].solar_reflectance
            absorptances = [1 - transmittance - reflectance]
            return transmittance, reflectance, absorptances

        # if it's multi-layered, then compute the optical properties across each gap
        glz_mats = self.glazing_materials
        forward_ref, backward_ref, backward_abs = \
            self._solar_optical_properties_by_gap(glz_mats)
        # set initial properties based on the first pane
        trans = glz_mats[0].solar_transmittance  # will decrease with each pane
        reflect = glz_mats[0].solar_reflectance  # will increase with each pane
        absorb = [1 - trans - reflect]  # will increase and get new value with each pane
        # loop through the panes of glass and update the initial properties
        for i in range(len(glz_mats) - 1):
            # get the two panes across the gap and their optical properties
            mat = glz_mats[i + 1]
            fw_ref, back_ref, back_abs = forward_ref[i], backward_ref[i], backward_abs[i]
            # get the incident solar on the pane, including back reflection
            incident = (trans + trans * fw_ref)
            absorb[i] += back_abs * trans
            back_out = back_ref * trans
            for p in range(i, 0, -1):
                prev_mat, p_prev_mat = glz_mats[p], glz_mats[p - 1]
                prev_incident = back_out * p_prev_mat.solar_reflectance_back
                incident += prev_incident * prev_mat.solar_transmittance
                absorb[p] += prev_incident * prev_mat.solar_absorptance
                absorb[p - 1] += back_out * p_prev_mat.solar_absorptance
                back_out = back_out * p_prev_mat.solar_transmittance
            reflect += back_out
            # pass the incident solar through the glass pane
            absorb.append(incident * mat.solar_absorptance)
            trans = incident * mat.solar_transmittance
        return trans, reflect, absorb

    def visible_optical_properties(self):
        """Get visible transmittance + reflectance, and absorptances for each glass pane.

        Returns:
            A tuple of three values.

            -   transmittance: A transmittance value through all glass panes.

            -   reflectance: A reflectance value from the front of all glass panes.

            -   absorptances: A list of absorptance values through each pane
                of glass. The values in this list correspond to the glass panes
                in the construction.
        """
        # first check whether the construction is a simple glazing system
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            transmittance = self.materials[0].vt
            reflectance = self.materials[0].visible_reflectance
            absorptances = [1 - transmittance - reflectance]
            return transmittance, reflectance, absorptances

        # if it's multi-layered, then compute the optical properties across each gap
        glz_mats = self.glazing_materials
        forward_ref, backward_ref, backward_abs = \
            self._visible_optical_properties_by_gap(glz_mats)
        # set initial properties based on the first pane
        trans = glz_mats[0].visible_transmittance  # will decrease with each pane
        reflect = glz_mats[0].visible_reflectance  # will increase with each pane
        absorb = [1 - trans - reflect]  # will increase and get new value with each pane
        # loop through the panes of glass and update the initial properties
        for i in range(len(glz_mats) - 1):
            # get the two panes across the gap and their optical properties
            mat = glz_mats[i + 1]
            fw_ref, back_ref, back_abs = forward_ref[i], backward_ref[i], backward_abs[i]
            # get the incident visible on the pane, including back reflection
            incident = (trans + trans * fw_ref)
            absorb[i] += back_abs * trans
            back_out = back_ref * trans
            for p in range(i, 0, -1):
                prev_mat, p_prev_mat = glz_mats[p], glz_mats[p - 1]
                prev_incident = back_out * p_prev_mat.visible_reflectance_back
                incident += prev_incident * prev_mat.visible_transmittance
                absorb[p] += prev_incident * prev_mat.visible_absorptance
                absorb[p - 1] += back_out * p_prev_mat.visible_absorptance
                back_out = back_out * p_prev_mat.visible_transmittance
            reflect += back_out
            # pass the incident visible through the glass pane
            absorb.append(incident * mat.visible_absorptance)
            trans = incident * mat.visible_transmittance
        return trans, reflect, absorb

    def temperature_profile(
        self, outside_temperature=-18, inside_temperature=21,
        wind_speed=6.7, solar_irradiance=0,
        height=1.0, angle=90.0, pressure=101325
    ):
        """Get a list of temperatures at each material boundary across the construction.

        Args:
            outside_temperature: The temperature on the outside of the
                construction [C]. (Default: -18, consistent with NFRC 100-2010).
            inside_temperature: The temperature on the inside of the
                construction [C]. (Default: 21, consistent with NFRC 100-2010).
            wind_speed: The average outdoor wind speed [m/s]. This affects outdoor
                convective heat transfer coefficient. (Default: 6.7 m/s).
            solar_irradiance: An optional value for solar irradiance that is incident
                on the front (exterior) of the construction [W/m2]. (Default: 0 W/m2).
            height: An optional height for the surface in meters. (Default: 1.0 m).
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal surface with the outside boundary on the top.
                * 90 = A vertical surface
                * 180 = A horizontal surface with the outside boundary on the bottom.

            pressure: The average pressure of in Pa. (Default: 101325 Pa for
                standard pressure at sea level).

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

        # compute delta temperature from solar irradiance if applicable
        heat_gen = None
        if solar_irradiance != 0:
            heat_gen, _ = self._heat_gen_from_solar(solar_irradiance)

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
                r_values, outside_temperature, inside_temperature, heat_gen)
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
                r_values, outside_temperature, inside_temperature, heat_gen)
            r_values = self._layered_r_value(
                temperatures, r_values, emissivities, height, angle, pressure)
            r_next = sum(r_values)
        temperatures = self._temperature_profile_from_r_values(
            r_values, outside_temperature, inside_temperature, heat_gen)
        return temperatures, r_values

    def temperature_profile_frame(
        self, outside_temperature=-18, inside_temperature=21,
        outside_wind_speed=6.7, solar_irradiance=0,
        height=1.0, angle=90.0, pressure=101325
    ):
        """Get a list of temperatures across the frame of the construction.

        Note that this method will return None if no frame is assigned to
        the construction.

        Args:
            outside_temperature: The temperature on the outside of the
                construction [C]. (Default: -18, consistent with NFRC 100-2010).
            inside_temperature: The temperature on the inside of the
                construction [C]. (Default: 21, consistent with NFRC 100-2010).
            wind_speed: The average outdoor wind speed [m/s]. This affects outdoor
                convective heat transfer coefficient. (Default: 6.7 m/s).
            solar_irradiance: An optional value for solar irradiance that is incident
                on the front (exterior) of the construction [W/m2]. (Default: 0 W/m2).
            height: An optional height for the surface in meters. (Default: 1.0 m).
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal surface with the outside boundary on the bottom.
                * 90 = A vertical surface
                * 180 = A horizontal surface with the outside boundary on the top.

            pressure: The average pressure of in Pa. (Default: 101325 Pa for
                standard pressure at sea level).

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
        # first check to e sure that the construction has a frame
        if self.frame is None:
            return None

        # reverse the angle if the outside temperature is greater than the inside one
        if angle != 90 and outside_temperature > inside_temperature:
            angle = abs(180 - angle)

        # compute delta temperature from solar irradiance if applicable
        heat_gen = None
        if solar_irradiance != 0:
            heat_gen = self.frame.solar_absorptance * solar_irradiance

        # use the r-values to get the temperature profile
        in_r_init = 1 / self.in_h_simple()
        r_values = [1 / self.out_h(outside_wind_speed, outside_temperature + 273.15),
                    self.frame.r_value, in_r_init]
        in_delta_t = (in_r_init / sum(r_values)) * \
            (outside_temperature - inside_temperature)
        r_values[-1] = 1 / self.in_h(inside_temperature - (in_delta_t / 2) + 273.15,
                                     in_delta_t, height, angle, pressure)
        temperatures = self._temperature_profile_from_r_values(
            r_values, outside_temperature, inside_temperature, heat_gen)
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
            "materials": [],  # list of material objects (from outside to inside)
            "frame": {}  # an optional frame object for the construction
            }
        """
        assert data['type'] == 'WindowConstruction', \
            'Expected WindowConstruction. Got {}.'.format(data['type'])
        mat_layers = cls._old_schema_materials(data) if 'layers' in data else \
            [dict_to_material(mat) for mat in data['materials']]
        new_obj = cls(data['identifier'], mat_layers)
        if 'frame' in data and data['frame'] is not None:
            new_obj.frame = EnergyWindowFrame.from_dict(data['frame'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
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
            "materials": [],  # list of material identifiers (from outside to inside)
            "frame": 'AL with thermal break'  # identifier of frame material
            }
        """
        assert data['type'] == 'WindowConstructionAbridged', \
            'Expected WindowConstructionAbridged. Got {}.'.format(data['type'])
        mat_key = 'layers' if 'layers' in data else 'materials'
        try:
            mat_layers = [materials[mat_id] for mat_id in data[mat_key]]
        except KeyError as e:
            raise ValueError('Failed to find {} in materials.'.format(e))
        new_obj = cls(data['identifier'], mat_layers)
        if 'frame' in data and data['frame'] is not None:
            new_obj.frame = materials[data['frame']]
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_idf(self):
        """IDF string representation of construction object.

        Note that this method only outputs a single string for the construction and,
        to write the full construction into an IDF, the construction's unique_materials
        must also be written. If the construction has a frame, the frame definition
        must also be written.

        Returns:
            construction_idf -- Text string representation of the construction.
        """
        return self._generate_idf_string('window', self.identifier, self.materials)

    def to_radiance_solar(self):
        """Honeybee Radiance modifier with the solar transmittance."""
        try:
            from honeybee_radiance.modifier.material import Glass
            from honeybee_radiance.modifier.material import Trans
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_solar() method. {}'.format(e))
        diffusing = False
        for mat in self.materials:
            if isinstance(mat, EnergyWindowMaterialGlazing) and mat.solar_diffusing:
                diffusing = True
        if not diffusing:
            return Glass.from_single_transmittance(
                clean_rad_string(self.identifier), self.solar_transmittance)
        else:
            _, ref, absorb = self.solar_optical_properties()
            rgb_ref = 1 - (sum(absorb) / (1 - ref))
            return Trans.from_single_reflectance(
                clean_rad_string(self.identifier), rgb_reflectance=rgb_ref,
                specularity=ref, transmitted_diff=1, transmitted_spec=0)

    def to_radiance_visible(self):
        """Honeybee Radiance modifier with the visible transmittance."""
        try:
            from honeybee_radiance.modifier.material import Glass
            from honeybee_radiance.modifier.material import Trans
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'to_radiance_visible() method. {}'.format(e))
        diffusing = False
        for mat in self.materials:
            if isinstance(mat, EnergyWindowMaterialGlazing) and mat.solar_diffusing:
                diffusing = True
        if not diffusing:
            return Glass.from_single_transmittance(
                clean_rad_string(self.identifier), self.visible_transmittance)
        else:
            _, ref, absorb = self.visible_optical_properties()
            rgb_ref = 1 - (sum(absorb) / (1 - ref))
            return Trans.from_single_reflectance(
                clean_rad_string(self.identifier), rgb_reflectance=rgb_ref,
                specularity=ref, transmitted_diff=1, transmitted_spec=0)

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
        base['materials'] = self.layers if abridged else \
            [m.to_dict() for m in self.materials]
        if self.frame is not None:
            base['frame'] = self.frame.identifier if abridged else self.frame.to_dict()
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    def to_simple_construction(self):
        """Get a version of this construction that uses a SimpleGlazSys material.

        This is useful when translating to gbXML and other formats that do not
        support layered window constructions.
        """
        if isinstance(self.materials[0], EnergyWindowMaterialSimpleGlazSys):
            return self
        simple_mat = EnergyWindowMaterialSimpleGlazSys(
            '{}_SimpleGlazSys'.format(self.identifier),
            self.u_factor, self.shgc, self.visible_transmittance
        )
        new_con = WindowConstruction(self.identifier, [simple_mat])
        if self._display_name is not None:
            new_con._display_name = self._display_name
        return new_con

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
        # read the file and remove lines of comments
        file_contents = clean_idf_file_contents(idf_file)
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
                except (ValueError, AssertionError):
                    pass  # it likely has a blind or a shade and is not serialize-able
            except KeyError:
                pass  # it's an opaque construction or window shaded construction
        # extract all of the frame objects
        frame_pattern = re.compile(r"(?i)(WindowProperty:FrameAndDivider,[\s\S]*?;)")
        frame_strings = frame_pattern.findall(file_contents)
        frame_materials = []
        for fr_str in frame_strings:
            frame_obj = EnergyWindowFrame.from_idf(fr_str.strip())
            frame_materials.append(frame_obj)
        # if there's only one frame in the file, assume it applies to all constructions
        # this is the convention used by LBNL WINDOW
        if len(frame_materials) == 1:
            for construct in constructions:
                construct.frame = frame_materials[0]
        return constructions, materials + frame_materials

    def lock(self):
        """The lock() method will also lock the materials."""
        self._locked = True
        for mat in self.materials:
            mat.lock()
        if self.has_frame:
            self.frame.lock()

    def unlock(self):
        """The unlock() method will also unlock the materials."""
        self._locked = False
        for mat in self.materials:
            mat.unlock()
        if self.has_frame:
            self.frame.unlock()

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

    def _heat_gen_from_solar(self, solar_irradiance):
        """Get heat generated in each material layer given incident irradiance.

        Args:
            solar_irradiance: The solar irradiance incident on the exterior
                of the window construction in W/m2.

        Returns:
            A tuple with two values

            -   heat_gen: A list of heat absorbed in each material and air film layer.

            -   transmitted: The solar irradiance directly transmitted through
                the construction.
        """
        # get the amount of solar absorbed by each glass pane
        transmittance, _, absorb = self.solar_optical_properties()
        transmitted = solar_irradiance * transmittance
        # turn the absorbed solar into delta temperatures
        heat_gen = [0]
        for m_abs in absorb:
            heat_gen.append(solar_irradiance * m_abs)  # heat absorbed in glass
            heat_gen.append(0)  # heat not absorbed by the following gap
        return heat_gen, transmitted

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

    @staticmethod
    def _solar_optical_properties_by_gap(glazing_materials):
        """Get forward_reflectance, back_reflectance, and back_absorptance across gaps.
        """
        forward_reflectance = []
        backward_reflectance = []
        backward_absorptance = []
        for i, mat in enumerate(glazing_materials[1:]):
            # compute the fraction of inter-reflected solar off previous panes
            prev_pane = glazing_materials[i]
            back_ref = mat.solar_reflectance * prev_pane.solar_transmittance
            back_abs = mat.solar_reflectance * prev_pane.solar_absorptance
            fwrd_ref = mat.solar_reflectance * prev_pane.solar_reflectance_back
            b_ref_i, b_abs_i, f_ref_i = back_ref, fwrd_ref, back_abs
            for r in range(3):  # simulate 3 bounces back and forth
                f_ref_i = f_ref_i ** 2
                b_ref_i = f_ref_i * prev_pane.solar_transmittance
                b_abs_i = f_ref_i * prev_pane.solar_absorptance
                fwrd_ref += f_ref_i
                back_ref += b_ref_i
                back_abs += b_abs_i
            forward_reflectance.append(fwrd_ref)
            backward_reflectance.append(back_ref)
            backward_absorptance.append(back_abs)
        return forward_reflectance, backward_reflectance, backward_absorptance

    @staticmethod
    def _visible_optical_properties_by_gap(glazing_materials):
        """Get forward_reflectance, back_reflectance, and back_absorptance across gaps.
        """
        forward_reflectance = []
        backward_reflectance = []
        backward_absorptance = []
        for i, mat in enumerate(glazing_materials[1:]):
            # compute the fraction of inter-reflected visible off previous panes
            prev_pane = glazing_materials[i]
            back_ref = mat.visible_reflectance * prev_pane.visible_transmittance
            back_abs = mat.visible_reflectance * prev_pane.visible_absorptance
            fwrd_ref = mat.visible_reflectance * prev_pane.visible_reflectance_back
            b_ref_i, b_abs_i, f_ref_i = back_ref, fwrd_ref, back_abs
            for r in range(3):  # simulate 3 bounces back and forth
                f_ref_i = f_ref_i ** 2
                b_ref_i = f_ref_i * prev_pane.visible_transmittance
                b_abs_i = f_ref_i * prev_pane.visible_absorptance
                fwrd_ref += f_ref_i
                back_ref += b_ref_i
                back_abs += b_abs_i
            forward_reflectance.append(fwrd_ref)
            backward_reflectance.append(back_ref)
            backward_absorptance.append(back_abs)
        return forward_reflectance, backward_reflectance, backward_absorptance

    @staticmethod
    def _old_schema_materials(data):
        """Get material objects from an old schema definition of WindowConstruction.

        The schema is from before May 2021 and this method should eventually be removed.
        """
        materials = {}
        for mat in data['materials']:
            materials[mat['identifier']] = dict_to_material(mat)
        try:
            mat_layers = [materials[mat_id] for mat_id in data['layers']]
        except KeyError as e:
            raise ValueError(
                'Failed to find {} in window construction materials.'.format(e))
        return mat_layers

    def __copy__(self):
        new_con = self.__class__(
            self.identifier, [mat.duplicate() for mat in self.materials])
        if self.has_frame:
            new_con._frame = self.frame.duplicate()
        new_con._display_name = self._display_name
        new_con._user_data = None if self._user_data is None else self._user_data.copy()
        new_con._properties._duplicate_extension_attr(self._properties)
        return new_con

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier,) + tuple(hash(mat) for mat in self.materials) + \
            (self.frame,)

    def __repr__(self):
        """Represent window energy construction."""
        return self._generate_idf_string('window', self.identifier, self.materials)
