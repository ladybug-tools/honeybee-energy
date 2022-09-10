# coding=utf-8
"""Base Construction."""
from __future__ import division

from ..material.gas import EnergyWindowMaterialGas
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import valid_ep_string

import math


@lockable
class _ConstructionBase(object):
    """Energy construction.

    Args:
        identifier: Text string for a unique Construction ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        materials: List of materials in the construction (from outside to inside).

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
        * has_frame
        * has_shade
        * is_dynamic
        * user_data
    """
    # generic air material used to compute indoor film coefficients.
    _air = EnergyWindowMaterialGas('generic air', gas_type='Air')

    __slots__ = ('_identifier', '_display_name', '_materials', '_locked',
                 '_properties', '_user_data')

    def __init__(self, identifier, materials):
        """Initialize energy construction."""
        self._locked = False  # unlocked by default
        self.identifier = identifier
        self._display_name = None
        self.materials = materials
        self._user_data = None
        self._properties = None

    @property
    def identifier(self):
        """Get or set the text string for unique construction identifier."""
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
        if value is not None:
            try:
                value = str(value)
            except UnicodeEncodeError:  # Python 2 machine lacking the character set
                pass  # keep it as unicode
        self._display_name = value

    @property
    def materials(self):
        """Get or set the list of materials in the construction (outside to inside)."""
        return self._materials

    @materials.setter
    def materials(self, mats):
        self._materials = mats

    @property
    def layers(self):
        """A list of material identifiers in the construction (outside to inside)."""
        return [mat.identifier for mat in self._materials]

    @property
    def unique_materials(self):
        """A set of only unique material objects in the construction.

        This is useful when constructions reuse material layers.
        """
        return list(set(self._materials))

    @property
    def inside_emissivity(self):
        """"The emissivity of the inside face of the construction."""
        return self.materials[-1].thermal_absorptance

    @property
    def outside_emissivity(self):
        """"The emissivity of the outside face of the construction."""
        return self.materials[0].thermal_absorptance

    @property
    def r_value(self):
        """R-value of the construction [m2-K/W] (excluding air films)."""
        return sum(tuple(mat.r_value for mat in self.materials))

    @property
    def u_value(self):
        """U-value of the construction [W/m2-K] (excluding air films)."""
        return 1 / self.r_value

    @property
    def r_factor(self):
        """Construction R-factor [m2-K/W] (including standard resistances for air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        _ext_r = 1 / self.out_h_simple()  # exterior heat transfer coefficient in m2-K/W
        _int_r = 1 / self.in_h_simple()  # interior film
        return self.r_value + _ext_r + _int_r

    @property
    def u_factor(self):
        """Construction U-factor [W/m2-K] (including standard resistances for air films).

        Formulas for film coefficients come from EN673 / ISO10292.
        """
        return 1 / self.r_factor

    @property
    def is_symmetric(self):
        """Get a boolean to note whether the construction layers are symmetric.

        Symmetric means that the materials in reversed order are equal to those
        in the current order (eg. 'Gypsum', 'Air Gap', 'Gypsum'). This is particularly
        helpful for interior constructions, which need to have matching materials
        in reversed order between adjacent Faces.
        """
        half_mat = int(len(self._materials) / 2)
        for i in range(half_mat):
            if self._materials[i] != self._materials[-(i + 1)]:
                return False
        return True

    @property
    def has_shade(self):
        """Get a boolean noting whether dynamic shade materials are in the construction.
        """
        # This is False for all construction types except WindowConstructionShade.
        return False

    @property
    def has_frame(self):
        """Get a boolean noting whether the construction has a frame assigned to it."""
        return False

    @property
    def is_dynamic(self):
        """Get a boolean noting whether the construction is dynamic.

        This will always be False for this class.
        """
        return False

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

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    def duplicate(self):
        """Get a copy of this construction."""
        return self.__copy__()

    def out_h_simple(self):
        """Get the simple outdoor heat transfer coefficient according to ISO 10292.

        This is used for all opaque R-factor calculations.
        """
        return 23

    def in_h_simple(self):
        """Get the simple indoor heat transfer coefficient according to ISO 10292.

        This is used for all opaque R-factor calculations.
        """
        return (3.6 + (4.4 * self.inside_emissivity / 0.84))

    def out_h(self, wind_speed=6.7, t_kelvin=273.15):
        """Get the detailed outdoor heat transfer coefficient according to ISO 15099.

        This is used for window U-factor calculations and all of the
        temperature_profile calculations.

        Args:
            wind_speed: The average outdoor wind speed [m/s]. This affects the
                convective heat transfer coefficient. Default is 6.7 m/s.
            t_kelvin: The average between the outdoor temperature and the
                exterior surface temperature. This can affect the radiative heat
                transfer. Default is 273.15K (0C).
        """
        _conv_h = 4 + (4 * wind_speed)
        _rad_h = 4 * 5.6697e-8 * self.outside_emissivity * (t_kelvin ** 3)
        return _conv_h + _rad_h

    def in_h(self, t_kelvin=293.15, delta_t=15, height=1.0, angle=90, pressure=101325):
        """Get the detailed indoor heat transfer coefficient according to ISO 15099.

        This is used for window U-factor calculations and all of the
        temperature_profile calculations.

        Args:
            t_kelvin: The average between the indoor temperature and the
                interior surface temperature. Default is 293.15K (20C).
            delta_t: The temperature difference between the indoor temperature and the
                interior surface temperature [C]. Default is 15C.
            height: An optional height for the surface in meters. Default is 1.0 m,
                which is consistent with NFRC standards.
            angle: An angle in degrees between 0 and 180.
                0 = A horizontal surface with downward heat flow through the layer.
                90 = A vertical surface
                180 = A horizontal surface with upward heat flow through the layer.
            pressure: The average pressure in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        _ray_numerator = (self._air.density_at_temperature(t_kelvin, pressure) ** 2) * \
            (height ** 3) * 9.81 * self._air.specific_heat_at_temperature(t_kelvin) \
            * delta_t
        _ray_denominator = t_kelvin * self._air.viscosity_at_temperature(t_kelvin) * \
            self._air.conductivity_at_temperature(t_kelvin)
        _rayleigh_h = abs(_ray_numerator / _ray_denominator)
        if angle < 15:
            nusselt = 0.13 * (_rayleigh_h ** (1 / 3))
        elif angle <= 90:
            _sin_a = math.sin(math.radians(angle))
            _rayleigh_c = 2.5e5 * ((math.exp(0.72 * angle) / _sin_a) ** (1 / 5))
            if _rayleigh_h < _rayleigh_c:
                nusselt = 0.56 * ((_rayleigh_h * _sin_a) ** (1 / 4))
            else:
                nu_1 = 0.56 * ((_rayleigh_c * _sin_a) ** (1 / 4))
                nu_2 = 0.13 * ((_rayleigh_h ** (1 / 3)) - (_rayleigh_c ** (1 / 3)))
                nusselt = nu_1 + nu_2
        elif angle <= 179:
            _sin_a = math.sin(math.radians(angle))
            nusselt = 0.56 * ((_rayleigh_h * _sin_a) ** (1 / 4))
        else:
            nusselt = 0.58 * (_rayleigh_h ** (1 / 5))
        a_cond = self._air.conductivity_at_temperature(t_kelvin)
        try:
            _conv_h = nusselt * (a_cond / height)
        except ZeroDivisionError:  # completely horizontal face
            _conv_h = nusselt * a_cond
        _rad_h = 4 * 5.6697e-8 * self.inside_emissivity * (t_kelvin ** 3)
        return _conv_h + _rad_h

    def lock(self):
        """The lock() method will also lock the materials."""
        self._locked = True
        for mat in self.materials:
            mat.lock()

    def unlock(self):
        """The unlock() method will also unlock the materials."""
        self._locked = False
        for mat in self.materials:
            mat.unlock()

    def _temperature_profile_from_r_values(
            self, r_values, outside_temperature=-18, inside_temperature=21,
            heat_generation=None):
        """Get a list of temperatures at each material boundary between R-values."""
        r_factor = sum(r_values)
        delta_t = inside_temperature - outside_temperature
        temperatures = [outside_temperature]
        for i, r_val in enumerate(r_values):
            temperatures.append(temperatures[i] + (delta_t * (r_val / r_factor)))
        # account for heat_generation in material layers if specified
        if isinstance(heat_generation, float):  # single heat incident on the exterior
            r_prev, r_follow = r_values[0], r_values[1:]
            q_prev = heat_generation * (1 - (r_prev / r_factor))
            q_follow = heat_generation * (1 - (sum(r_follow) / r_factor))
            temperatures[1] += q_prev * r_prev  # heat going to exterior
            # add the heat transferred to the interior
            for j in range(len(r_follow)):
                temperatures[2 + j] += q_follow * sum(r_follow[j + 1:])
        elif isinstance(heat_generation, list):  # a list of heat generated inside layers
            for i, heat_g in enumerate(heat_generation):
                if heat_g == 0:
                    continue
                r_prev, r_follow = r_values[:i], r_values[i + 1:]
                q_prev = heat_g * (1 - (sum(r_prev) / r_factor))
                q_follow = heat_g * (1 - (sum(r_follow) / r_factor))
                # add the heat transferred to the interior
                for j in range(len(r_follow)):
                    temperatures[i + 1 + j] += q_follow * sum(r_follow[j:])
                # add the heat transferred to the exterior
                for k in range(len(r_prev), 0, -1):
                    temperatures[k] += q_prev * sum(r_prev[:k])
        return temperatures

    @staticmethod
    def _generate_idf_string(constr_type, identifier, materials):
        """Get an EnergyPlus string representation from values and comments."""
        values = (identifier,) + tuple(mat.identifier for mat in materials)
        comments = ('name',) + tuple('layer %s' % (i + 1) for i in range(len(materials)))
        return generate_idf_string('Construction', values, comments)

    def __copy__(self):
        new_con = self.__class__(
            self.identifier, [mat.duplicate() for mat in self.materials])
        new_con._display_name = self._display_name
        new_con._user_data = None if self._user_data is None else self._user_data.copy()
        new_con._properties._duplicate_extension_attr(self._properties)
        return new_con

    def __len__(self):
        return len(self._materials)

    def __getitem__(self, key):
        return self._materials[key]

    def __iter__(self):
        return iter(self._materials)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier,) + tuple(hash(mat) for mat in self.materials)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, _ConstructionBase) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'Construction: {}, [{} materials]'.format(
            self.display_name, len(self.materials))
