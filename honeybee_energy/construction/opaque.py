# coding=utf-8
"""Opaque Construction."""
from __future__ import division

from ._base import _ConstructionBase
from ..material.dictutil import dict_to_material
from ..material._base import _EnergyMaterialOpaqueBase
from ..material.opaque import EnergyMaterial, EnergyMaterialNoMass
from ..reader import parse_idf_string, clean_idf_file_contents

from honeybee._lockable import lockable

import re
import os


@lockable
class OpaqueConstruction(_ConstructionBase):
    """Opaque energy construction.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        materials: List of materials in the construction (from outside to inside).
            All materials must be opaque and a maximum of 10 materials are allowed.

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
        * inside_solar_reflectance
        * inside_visible_reflectance
        * outside_emissivity
        * outside_solar_reflectance
        * outside_visible_reflectance
        * mass_area_density
        * area_heat_capacity
        * user_data
    """
    __slots__ = ()

    @property
    def materials(self):
        """Get or set the list of materials in the construction (outside to inside).

        All materials must be opaque and a maximum of 10 materials are allowed.
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
        for mat in mats:
            assert isinstance(mat, _EnergyMaterialOpaqueBase), 'Expected opaque energy' \
                ' material for construction. Got {}.'.format(type(mat))
        assert len(mats) > 0, 'Construction must possess at least one material.'
        assert len(mats) <= 10, 'Opaque Construction cannot have more than 10 materials.'
        self._materials = mats

    @property
    def inside_solar_reflectance(self):
        """The solar reflectance of the inside face of the construction."""
        return 1 - self.materials[-1].solar_absorptance

    @property
    def inside_visible_reflectance(self):
        """The visible reflectance of the inside face of the construction."""
        return 1 - self.materials[-1].visible_absorptance

    @property
    def outside_solar_reflectance(self):
        """The solar reflectance of the outside face of the construction."""
        return 1 - self.materials[0].solar_absorptance

    @property
    def outside_visible_reflectance(self):
        """The visible reflectance of the outside face of the construction."""
        return 1 - self.materials[0].visible_absorptance

    @property
    def mass_area_density(self):
        """The area density of the construction [kg/m2]."""
        return sum(tuple(mat.mass_area_density for mat in self.materials))

    @property
    def area_heat_capacity(self):
        """The heat capacity per unit area of the construction [kg/K-m2]."""
        return sum(tuple(mat.area_heat_capacity for mat in self.materials))

    @property
    def thickness(self):
        """Thickness of the construction [m]."""
        thickness = 0
        for mat in self.materials:
            if isinstance(mat, EnergyMaterial):
                thickness += mat.thickness
        return thickness

    def temperature_profile(self, outside_temperature=-18, inside_temperature=21,
                            outside_wind_speed=6.7, solar_irradiance=0,
                            height=1.0, angle=90.0, pressure=101325):
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
        # reverse the angle if the outside temperature is greater than the inside one
        if angle != 90 and outside_temperature > inside_temperature:
            angle = abs(180 - angle)

        # compute delta temperature from solar irradiance if applicable
        heat_gen = None
        if solar_irradiance != 0:
            heat_gen = self.materials[0].solar_absorptance * solar_irradiance

        # use the r-values to get the temperature profile
        in_r_init = 1 / self.in_h_simple()
        r_values = [1 / self.out_h(outside_wind_speed, outside_temperature + 273.15)] + \
            [mat.r_value for mat in self.materials] + [in_r_init]
        in_delta_t = (in_r_init / sum(r_values)) * \
            (outside_temperature - inside_temperature)
        r_values[-1] = 1 / self.in_h(inside_temperature - (in_delta_t / 2) + 273.15,
                                     in_delta_t, height, angle, pressure)
        temperatures = self._temperature_profile_from_r_values(
            r_values, outside_temperature, inside_temperature, heat_gen)
        return temperatures, r_values

    @classmethod
    def from_idf(cls, idf_string, ep_mat_strings):
        """Create an OpaqueConstruction from an EnergyPlus IDF text string.

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
        """Create a OpaqueConstruction from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'OpaqueConstruction',
            "identifier": 'Generic Brick Wall R-10',
            "display_name": 'Brick Wall',
            "materials": []  # list of unique material objects (from outside to inside)
            }
        """
        assert data['type'] == 'OpaqueConstruction', \
            'Expected OpaqueConstruction. Got {}.'.format(data['type'])
        mat_layers = cls._old_schema_materials(data) if 'layers' in data else \
            [dict_to_material(mat) for mat in data['materials']]
        new_obj = cls(data['identifier'], mat_layers)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, materials):
        """Create a OpaqueConstruction from an abridged dictionary.

        Args:
            data: An OpaqueConstructionAbridged dictionary.
            materials: A dictionary with identifiers of materials as keys and Python
                material objects as values.

        .. code-block:: python

            {
            "type": 'OpaqueConstructionAbridged',
            "identifier": 'Generic Brick Wall R-10',
            "display_name": 'Brick Wall',
            "materials": [],  # list of material identifiers (from outside to inside)
            }
        """
        assert data['type'] == 'OpaqueConstructionAbridged', \
            'Expected OpaqueConstructionAbridged. Got {}.'.format(data['type'])
        # handle old schema definition before May 2021 (used layers instead of materials)
        mat_key = 'layers' if 'layers' in data else 'materials'
        try:
            mat_layers = [materials[mat_id] for mat_id in data[mat_key]]
        except KeyError as e:
            raise ValueError('Failed to find {} in materials.'.format(e))
        new_obj = cls(data['identifier'], mat_layers)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """IDF string representation of construction object.

        Note that this method only outputs a single string for the construction and,
        to write the full construction into an IDF, the construction's unique_materials
        must also be written.

        Returns:
            construction_idf -- Text string representation of the construction.
        """
        return self._generate_idf_string('opaque', self.identifier, self.materials)

    def to_radiance_solar_interior(self, specularity=0.0):
        """Honeybee Radiance modifier with the interior solar reflectance."""
        return self.materials[-1].to_radiance_solar(specularity)

    def to_radiance_visible_interior(self, specularity=0.0):
        """Honeybee Radiance modifier with the interior visible reflectance."""
        return self.materials[-1].to_radiance_visible(specularity)

    def to_radiance_solar_exterior(self, specularity=0.0):
        """Honeybee Radiance modifier with the exterior solar reflectance."""
        return self.materials[0].to_radiance_solar(specularity)

    def to_radiance_visible_exterior(self, specularity=0.0):
        """Honeybee Radiance modifier with the exterior visible reflectance."""
        return self.materials[0].to_radiance_visible(specularity)

    def to_dict(self, abridged=False):
        """Opaque construction dictionary representation.

        Args:
            abridged: Boolean to note whether the full dictionary describing the
                object should be returned (False) or just an abridged version (True),
                which only specifies the identifiers of material layers. Default: False.
        """
        base = {'type': 'OpaqueConstruction'} if not \
            abridged else {'type': 'OpaqueConstructionAbridged'}
        base['identifier'] = self.identifier
        base['materials'] = self.layers if abridged else \
            [m.to_dict() for m in self.materials]
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    @staticmethod
    def extract_all_from_idf_file(idf_file):
        """Extract all OpaqueConstruction objects from an EnergyPlus IDF file.

        Args:
            idf_file: A path to an IDF file containing objects for opaque
                constructions and corresponding materials.

        Returns:
            A tuple with two elements

            -   constructions: A list of all OpaqueConstruction objects in the IDF
                file as honeybee_energy OpaqueConstruction objects.

            -   materials: A list of all opaque materials in the IDF file as
                honeybee_energy EnergyMaterial objects.
        """
        # read the file and remove lines of comments
        file_contents = clean_idf_file_contents(idf_file)
        # extract all of the opaque material objects
        mat_pattern1 = re.compile(r"(?i)(Material,[\s\S]*?;)")
        mat_pattern2 = re.compile(r"(?i)(Material:NoMass,[\s\S]*?;)")
        mat_pattern3 = re.compile(r"(?i)(Material:AirGap,[\s\S]*?;)")
        material_str = mat_pattern1.findall(file_contents) + \
            mat_pattern2.findall(file_contents) + mat_pattern3.findall(file_contents)
        materials_dict = OpaqueConstruction._idf_materials_dictionary(material_str)
        materials = list(materials_dict.values())
        # extract all of the construction objects
        constr_pattern = re.compile(r"(?i)(Construction,[\s\S]*?;)")
        constr_props = tuple(parse_idf_string(idf_string) for
                             idf_string in constr_pattern.findall(file_contents))
        constructions = []
        for constr in constr_props:
            try:
                constr_mats = [materials_dict[mat.upper()] for mat in constr[1:]]
                constructions.append(OpaqueConstruction(constr[0], constr_mats))
            except (KeyError, AssertionError):
                pass  # the construction is probably a window construction
        return constructions, materials

    @staticmethod
    def _idf_materials_dictionary(ep_mat_strings):
        """Get a dictionary of opaque EnergyMaterial objects from an IDF string list."""
        materials_dict = {}
        for mat_str in ep_mat_strings:
            mat_str = mat_str.strip()
            if mat_str.startswith('Material,'):
                mat_obj = EnergyMaterial.from_idf(mat_str)
                materials_dict[mat_obj.identifier.upper()] = mat_obj
            elif mat_str.startswith('Material:NoMass,'):
                mat_obj = EnergyMaterialNoMass.from_idf(mat_str)
                materials_dict[mat_obj.identifier.upper()] = mat_obj
            elif mat_str.startswith('Material:AirGap,'):
                mat_obj = EnergyMaterialNoMass.from_idf_air_gap(mat_str)
                materials_dict[mat_obj.identifier.upper()] = mat_obj
        return materials_dict

    @staticmethod
    def _old_schema_materials(data):
        """Get material objects from an old schema definition of OpaqueConstruction.

        The schema is from before May 2021 and this method should eventually be removed.
        """
        materials = {}
        for mat in data['materials']:
            materials[mat['identifier']] = dict_to_material(mat)
        try:
            mat_layers = [materials[mat_id] for mat_id in data['layers']]
        except KeyError as e:
            raise ValueError(
                'Failed to find {} in opaque construction materials.'.format(e))
        return mat_layers

    def __repr__(self):
        """Represent opaque energy construction."""
        return self._generate_idf_string('opaque', self.identifier, self.materials)
