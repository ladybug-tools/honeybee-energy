# coding=utf-8
"""Gas materials representing gaps within window constructions.

They can only exist within window constructions bounded by glazing materials
(they cannot be in the interior or exterior layer).
"""
from __future__ import division

from ._base import _EnergyMaterialWindowBase
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee._lockable import lockable
from honeybee.typing import float_positive, float_in_range, tuple_with_length

import math


@lockable
class _EnergyWindowMaterialGasBase(_EnergyMaterialWindowBase):
    """Base for gas gap layer."""
    GASES = ('Air', 'Argon', 'Krypton', 'Xenon')
    CONDUCTIVITYCURVES = {'Air': (0.002873, 0.0000776, 0.0),
                          'Argon': (0.002285, 0.00005149, 0.0),
                          'Krypton': (0.0009443, 0.00002826, 0.0),
                          'Xenon': (0.0004538, 0.00001723, 0.0)}
    VISCOSITYCURVES = {'Air': (0.00000372, 0.00000005, 0.0),
                       'Argon': (0.00000338, 0.00000006, 0.0),
                       'Krypton': (0.00000221, 0.00000008, 0.0),
                       'Xenon': (0.00000107, 0.00000007, 0.0)}
    SPECIFICHEATCURVES = {'Air': (1002.73699951, 0.012324, 0.0),
                          'Argon': (521.92852783, 0.0, 0.0),
                          'Krypton': (248.09069824, 0.0, 0.0),
                          'Xenon': (158.33970642, 0.0, 0.0)}
    MOLECULARWEIGHTS = {'Air': 28.97, 'Argon': 39.948,
                        'Krypton': 83.8, 'Xenon': 131.3}
    __slots__ = ('_thickness',)

    def __init__(self, identifier, thickness=0.0125):
        """Initialize gas base material."""
        _EnergyMaterialWindowBase.__init__(self, identifier)
        self.thickness = thickness

    @property
    def is_gas_material(self):
        """Boolean to note whether the material is a gas gap layer."""
        return True

    @property
    def thickness(self):
        """Get or set the thickess of the gas layer [m]."""
        return self._thickness

    @property
    def molecular_weight(self):
        """Default placeholder gas molecular weight."""
        return self.MOLECULARWEIGHTS['Air']

    @thickness.setter
    def thickness(self, thick):
        self._thickness = float_positive(thick, 'gas gap thickness')

    @property
    def conductivity(self):
        """Conductivity of the gas in the absence of convection at 0C [W/m-K]."""
        return self.conductivity_at_temperature(273.15)

    @property
    def viscosity(self):
        """Viscosity of the gas at 0C [kg/m-s]."""
        return self.viscosity_at_temperature(273.15)

    @property
    def specific_heat(self):
        """Specific heat of the gas at 0C [J/kg-K]."""
        return self.specific_heat_at_temperature(273.15)

    @property
    def density(self):
        """Density of the gas at 0C and sea-level pressure [J/kg-K]."""
        return self.density_at_temperature(273.15)

    @property
    def prandtl(self):
        """Prandtl number of the gas at 0C."""
        return self.prandtl_at_temperature(273.15)

    def density_at_temperature(self, t_kelvin, pressure=101325):
        """Get the density of the gas [kg/m3] at a given temperature and pressure.

        This method uses the ideal gas law to estimate the density.

        Args:
            t_kelvin: The average temperature of the gas cavity in Kelvin.
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return (pressure * self.molecular_weight * 0.001) / (8.314 * t_kelvin)

    def prandtl_at_temperature(self, t_kelvin):
        """Get the Prandtl number of the gas at a given Kelvin temperature."""
        return self.viscosity_at_temperature(t_kelvin) * \
            self.specific_heat_at_temperature(t_kelvin) / \
            self.conductivity_at_temperature(t_kelvin)

    def grashof(self, delta_t=15, t_kelvin=273.15, pressure=101325):
        """Get Grashof number given the temperature difference across the cavity.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return (9.81 * (self.thickness ** 3) * delta_t *
                self.density_at_temperature(t_kelvin, pressure) ** 2) / \
            (t_kelvin * (self.viscosity_at_temperature(t_kelvin) ** 2))

    def rayleigh(self, delta_t=15, t_kelvin=273.15, pressure=101325):
        """Get Rayleigh number given the temperature difference across the cavity.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        _numerator = (self.density_at_temperature(t_kelvin, pressure) ** 2) * \
            (self.thickness ** 3) * 9.81 * self.specific_heat_at_temperature(t_kelvin) \
            * delta_t
        _denominator = t_kelvin * self.viscosity_at_temperature(t_kelvin) * \
            self.conductivity_at_temperature(t_kelvin)
        return _numerator / _denominator

    def nusselt(self, delta_t=15, height=1.0, t_kelvin=273.15, pressure=101325):
        """Get Nusselt number for a vertical cavity given the temp difference and height.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        rayleigh = self.rayleigh(delta_t, t_kelvin, pressure)
        if rayleigh > 50000:
            n_u1 = 0.0673838 * (rayleigh ** (1 / 3))
        elif rayleigh > 10000:
            n_u1 = 0.028154 * (rayleigh ** 0.4134)
        else:
            n_u1 = 1 + 1.7596678e-10 * (rayleigh ** 2.2984755)
        n_u2 = 0.242 * ((rayleigh * (self.thickness / height)) ** 0.272)
        return max(n_u1, n_u2)

    def nusselt_at_angle(self, delta_t=15, height=1.0, angle=90,
                         t_kelvin=273.15, pressure=101325):
        """Get Nusselt number for a cavity at a given angle, temp difference and height.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal cavity with downward heat flow through the layer.
                * 90 = A vertical cavity
                * 180 = A horizontal cavity with upward heat flow through the layer.

            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        def dot_x(x):
            return (x + abs(x)) / 2

        rayleigh = self.rayleigh(delta_t, t_kelvin, pressure)
        if angle < 60:
            cos_a = math.cos(math.radians(angle))
            sin_a_18 = math.sin(1.8 * math.radians(angle))
            term_1 = dot_x(1 - (1708 / (rayleigh * cos_a)))
            term_2 = 1 - ((1708 * (sin_a_18 ** 1.6)) / (rayleigh * cos_a))
            term_3 = dot_x(((rayleigh * cos_a) / 5830) ** (1 / 3) - 1)
            return 1 + (1.44 * term_1 * term_2) + term_3
        elif angle < 90:
            g = 0.5 / ((1 + ((rayleigh / 3160) ** 20.6)) ** 0.1)
            n_u1 = (1 + (((0.0936 * (rayleigh ** 0.314)) / (1 + g)) ** 7)) ** (1 / 7)
            n_u2 = (0.104 + (0.175 / (self.thickness / height))) * (rayleigh ** 0.283)
            n_u_60 = max(n_u1, n_u2)
            n_u_90 = self.nusselt(delta_t, height, t_kelvin, pressure)
            return (n_u_60 + n_u_90) / 2
        elif angle == 90:
            return self.nusselt(delta_t, height, t_kelvin, pressure)
        else:
            n_u_90 = self.nusselt(delta_t, height, t_kelvin, pressure)
            return 1 + ((n_u_90 - 1) * math.sin(math.radians(angle)))

    def convective_conductance(self, delta_t=15, height=1.0,
                               t_kelvin=273.15, pressure=101325):
        """Get convective conductance of the cavity in a vertical position.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return self.nusselt(delta_t, height, t_kelvin, pressure) * \
            (self.conductivity_at_temperature(t_kelvin) / self.thickness)

    def convective_conductance_at_angle(self, delta_t=15, height=1.0, angle=90,
                                        t_kelvin=273.15, pressure=101325):
        """Get convective conductance of the cavity in an angle.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            angle: An angle in degrees between 0 and 180.

                * 0 = A horizontal cavity with downward heat flow through the layer.
                * 90 = A vertical cavity
                * 180 = A horizontal cavity with upward heat flow through the layer.

            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return self.nusselt_at_angle(delta_t, height, angle, t_kelvin, pressure) * \
            (self.conductivity_at_temperature(t_kelvin) / self.thickness)

    def radiative_conductance(self, emissivity_1=0.84, emissivity_2=0.84,
                              t_kelvin=273.15):
        """Get the radiative conductance of the cavity given emissivities on both sides.

        Args:
            emissivity_1: The emissivity of the surface on one side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            emissivity_2: The emissivity of the surface on the other side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
        """
        return (4 * 5.6697e-8) * (((1 / emissivity_1) + (1 / emissivity_2) - 1) ** -1) \
            * (t_kelvin ** 3)

    def u_value(self, delta_t=15, emissivity_1=0.84, emissivity_2=0.84, height=1.0,
                t_kelvin=273.15, pressure=101325):
        """Get the U-value of a vertical gas cavity given temp difference and emissivity.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. This
                influences how strong the convection is within the gas gap. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            emissivity_1: The emissivity of the surface on one side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            emissivity_2: The emissivity of the surface on the other side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return self.convective_conductance(delta_t, height, t_kelvin, pressure) + \
            self.radiative_conductance(emissivity_1, emissivity_2, t_kelvin)

    def u_value_at_angle(self, delta_t=15, emissivity_1=0.84, emissivity_2=0.84,
                         height=1.0, angle=90, t_kelvin=273.15, pressure=101325):
        """Get the U-value of a vertical gas cavity given temp difference and emissivity.

        Args:
            delta_t: The temperature difference across the gas cavity [C]. This
                influences how strong the convection is within the gas gap. Default is
                15C, which is consistent with the NFRC standard for double glazed units.
            emissivity_1: The emissivity of the surface on one side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            emissivity_2: The emissivity of the surface on the other side of the cavity.
                Default is 0.84, which is typical of clear, uncoated glass.
            height: An optional height for the cavity in meters. Default is 1.0,
                which is consistent with NFRC standards.
            angle: An angle in degrees between 0 and 180.
                0 = A horizontal cavity with downward heat flow through the layer.
                90 = A vertical cavity
                180 = A horizontal cavity with upward heat flow through the layer.
            t_kelvin: The average temperature of the gas cavity in Kelvin.
                Default: 273.15 K (0C).
            pressure: The average pressure of the gas cavity in Pa.
                Default is 101325 Pa for standard pressure at sea level.
        """
        return self.convective_conductance_at_angle(
            delta_t, height, angle, t_kelvin, pressure) + \
            self.radiative_conductance(emissivity_1, emissivity_2, t_kelvin)


@lockable
class EnergyWindowMaterialGas(_EnergyWindowMaterialGasBase):
    """Gas gap layer.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the air gap layer [m].
            Default: 0.0125
        gas_type: Text describing the type of gas in the gap.
            Must be one of the following: 'Air', 'Argon', 'Krypton', 'Xenon'.
            Default: 'Air'

    Properties:
        * identifier
        * display_name
        * thickness
        * gas_type
        * conductivity
        * viscosity
        * specific_heat
        * density
        * prandtl
        * user_data
    """
    __slots__ = ('_gas_type',)

    def __init__(self, identifier, thickness=0.0125, gas_type='Air'):
        """Initialize gas energy material."""
        _EnergyWindowMaterialGasBase.__init__(self, identifier, thickness)
        self.gas_type = gas_type

    @property
    def gas_type(self):
        """Get or set the text describing the gas in the gas gap layer."""
        return self._gas_type

    @gas_type.setter
    def gas_type(self, gas):
        assert gas.title() in self.GASES, 'Invalid input "{}" for gas type.' \
            '\nGas type must be one of the following:{}'.format(gas, self.GASES)
        self._gas_type = gas.title()

    @property
    def molecular_weight(self):
        """Get the gas molecular weight."""
        return self.MOLECULARWEIGHTS[self._gas_type]

    def conductivity_at_temperature(self, t_kelvin):
        """Get the conductivity of the gas [W/m-K] at a given Kelvin temperature."""
        return self._coeff_property(self.CONDUCTIVITYCURVES, t_kelvin)

    def viscosity_at_temperature(self, t_kelvin):
        """Get the viscosity of the gas [kg/m-s] at a given Kelvin temperature."""
        return self._coeff_property(self.VISCOSITYCURVES, t_kelvin)

    def specific_heat_at_temperature(self, t_kelvin):
        """Get the specific heat of the gas [J/kg-K] at a given Kelvin temperature."""
        return self._coeff_property(self.SPECIFICHEATCURVES, t_kelvin)

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialGas from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_strs = parse_idf_string(idf_string, 'WindowMaterial:Gas,')
        assert ep_strs[1].title() != 'Custom', \
            'Honeybee EnergyWindowMaterialGas cannot use EnergyPlus Custom gas type.\n' \
            'Use honeybee EnergyWindowMaterialGasCustom instead.'
        return cls(ep_strs[0], ep_strs[2], ep_strs[1])

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialGas from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowMaterialGas',
            "identifier": 'Argon_Gap_0010',
            "display_name": 'Argon Gap',
            "thickness": 0.01,
            "gas_type": 'Argon'
            }
        """
        assert data['type'] == 'EnergyWindowMaterialGas', \
            'Expected EnergyWindowMaterialGas. Got {}.'.format(data['type'])
        thickness = 0.0125 if 'thickness' not in data else data['thickness']
        gas_type = 'Air' if 'gas_type' not in data else data['gas_type']
        new_obj = cls(data['identifier'], thickness, gas_type)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, self.gas_type, self.thickness)
        comments = ('name', 'gas type', 'thickness {m}')
        return generate_idf_string('WindowMaterial:Gas', values, comments)

    def to_dict(self):
        """Energy Material Gas dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialGas',
            'identifier': self.identifier,
            'thickness': self.thickness,
            'gas_type': self.gas_type
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def _coeff_property(self, dictionary, t_kelvin):
        """Get a property given a dictionary of coefficients and kelvin temperature."""
        return dictionary[self._gas_type][0] + \
            dictionary[self._gas_type][1] * t_kelvin + \
            dictionary[self._gas_type][2] * t_kelvin ** 2

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.thickness, self.gas_type)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialGas) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_obj = EnergyWindowMaterialGas(self.identifier, self.thickness, self.gas_type)
        new_obj._display_name = self._display_name
        return new_obj


@lockable
class EnergyWindowMaterialGasMixture(_EnergyWindowMaterialGasBase):
    """Gas gap layer with a mixture of gasses.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the air gap layer [m].
            Default: 0.0125
        gas_types: A list of text describing the types of gas in the gap.
            Text must be one of the following: 'Air', 'Argon', 'Krypton', 'Xenon'.
            Default: ('Argon', 'Air')
        gas_fractions: A list of fractional numbers describing the volumetric
            fractions of gas types in the mixture.  This list must align with
            the gas_types input list and must sum to 1. Default: (0.9, 0.1).

    Properties:
        * identifier
        * display_name
        * thickness
        * gas_types
        * gas_fractions
        * gas_count
        * conductivity
        * viscosity
        * specific_heat
        * density
        * prandtl
    """
    __slots__ = ('_gas_count', '_gas_types', '_gas_fractions')

    def __init__(self, identifier, thickness=0.0125,
                 gas_types=('Argon', 'Air'), gas_fractions=(0.9, 0.1)):
        """Initialize gas mixture energy material."""
        _EnergyWindowMaterialGasBase.__init__(self, identifier, thickness)
        try:  # check the number of gases
            self._gas_count = len(gas_types)
        except (TypeError, ValueError):
            raise TypeError(
                'Expected list for gas_types. Got {}.'.format(type(gas_types)))
        assert 2 <= self._gas_count <= 4, 'Number of gases in gas mixture must be ' \
            'between 2 anf 4. Got {}.'.format(self._gas_count)
        self.gas_types = gas_types
        self.gas_fractions = gas_fractions

    @property
    def gas_types(self):
        """Get or set a tuple of text describing the gases in the gas gap layer."""
        return self._gas_types

    @gas_types.setter
    def gas_types(self, g_types):
        self._gas_types = tuple_with_length(
            g_types, self._gas_count, str, 'gas mixture gas_types')
        self._gas_types = tuple(gas.title() for gas in self._gas_types)
        for gas in self._gas_types:
            assert gas in self.GASES, 'Invalid input "{}" for gas type.' \
                '\nGas type must be one of the following:{}'.format(gas, self.GASES)

    @property
    def gas_fractions(self):
        """Get or set a tuple of numbers the fractions of gases in the gas gap layer."""
        return self._gas_fractions

    @gas_fractions.setter
    def gas_fractions(self, g_fracs):
        self._gas_fractions = tuple_with_length(
            g_fracs, self._gas_count, float, 'gas mixture gas_fractions')
        assert sum(self._gas_fractions) == 1, 'Gas fractions must sum to 1. ' \
            'Got {}.'.format(sum(self._gas_fractions))

    @property
    def molecular_weight(self):
        """Get the gas molecular weight."""
        return sum(tuple(self.MOLECULARWEIGHTS[gas] * frac for gas, frac
                         in zip(self._gas_types, self._gas_fractions)))

    @property
    def gas_count(self):
        """An integer indicating the number of gasses in the mixture."""
        return self._gas_count

    def conductivity_at_temperature(self, t_kelvin):
        """Get the conductivity of the gas [W/m-K] at a given Kelvin temperature."""
        return self._weighted_avg_coeff_property(self.CONDUCTIVITYCURVES, t_kelvin)

    def viscosity_at_temperature(self, t_kelvin):
        """Get the viscosity of the gas [kg/m-s] at a given Kelvin temperature."""
        return self._weighted_avg_coeff_property(self.VISCOSITYCURVES, t_kelvin)

    def specific_heat_at_temperature(self, t_kelvin):
        """Get the specific heat of the gas [J/kg-K] at a given Kelvin temperature."""
        return self._weighted_avg_coeff_property(self.SPECIFICHEATCURVES, t_kelvin)

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialGas from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        prop_types = (str, float, int, str, float, str, float, str, float, str, float)
        ep_strs = parse_idf_string(idf_string, 'WindowMaterial:GasMixture,')
        ep_s = [typ(prop) for typ, prop in zip(prop_types, ep_strs)]
        gas_types = [ep_s[i] for i in range(3, 3 + ep_s[2] * 2, 2)]
        gas_fracs = [ep_s[i] for i in range(4, 4 + ep_s[2] * 2, 2)]
        return cls(ep_s[0], ep_s[1], gas_types, gas_fracs)

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialGasMixture from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            'type': 'EnergyWindowMaterialGasMixture',
            'identifier': 'Argon_Mixture_001_095_005',
            'display_name': 'Argon Mixture',
            'thickness': 0.01,
            'gas_types': ['Argon', 'Air'],
            'gas_fractions': [0.95, 0.05]
            }
        """
        assert data['type'] == 'EnergyWindowMaterialGasMixture', \
            'Expected EnergyWindowMaterialGasMixture. Got {}.'.format(data['type'])
        required_keys = ('identifier', 'gas_types', 'gas_fractions')
        for key in required_keys:
            assert key in data, 'Required key "{}" is missing.'.format(key)
        thickness = 0.0125 if 'thickness' not in data or data['thickness'] is None \
            else data['thickness']
        new_obj = cls(data['identifier'], thickness, data['gas_types'],
                      data['gas_fractions'])
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = [self.identifier, self.thickness, len(self.gas_types)]
        comments = ['name', 'thickness {m}', 'number of gases']
        for i in range(len(self.gas_types)):
            values.append(self.gas_types[i])
            values.append(self.gas_fractions[i])
            comments.append('gas {} type'.format(i))
            comments.append('gas {} fraction'.format(i))
        return generate_idf_string('WindowMaterial:GasMixture', values, comments)

    def to_dict(self):
        """Energy Material Gas Mixture dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialGasMixture',
            'identifier': self.identifier,
            'thickness': self.thickness,
            'gas_types': self.gas_types,
            'gas_fractions': self.gas_fractions
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def _weighted_avg_coeff_property(self, dictionary, t_kelvin):
        """Get a weighted average property given a dictionary of coefficients."""
        property = []
        for gas in self._gas_types:
            property.append(dictionary[gas][0] + dictionary[gas][1] * t_kelvin +
                            dictionary[gas][2] * t_kelvin ** 2)
        return sum(tuple(pr * frac for pr, frac in zip(property, self._gas_fractions)))

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.thickness, self.gas_types, self.gas_fractions)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialGasMixture) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_obj = EnergyWindowMaterialGasMixture(
            self.identifier, self.thickness, self.gas_types, self.gas_fractions)
        new_obj._display_name = self._display_name
        return new_obj


@lockable
class EnergyWindowMaterialGasCustom(_EnergyWindowMaterialGasBase):
    """Custom gas gap layer.

    This object allows you to specify specific values for conductivity,
    viscosity and specific heat through the following formula:

    property = A + (B * T) + (C * T ** 2)

    where:

    * A, B, and C = regression coefficients for the gas
    * T = temperature [K]

    Note that setting properties B and C to 0 will mean the property will be
    equal to the A coefficient.

    Args:
        identifier: Text string for a unique Material ID. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        thickness: Number for the thickness of the air gap layer [m].
            Default: 0.0125
        conductivity_coeff_a: First conductivity coefficient.
            Or conductivity in [W/m-K] if b and c coefficients are 0.
        viscosity_coeff_a: First viscosity coefficient.
            Or viscosity in [kg/m-s] if b and c coefficients are 0.
        specific_heat_coeff_a: First specific heat coefficient.
            Or specific heat in [J/kg-K] if b and c coefficients are 0.
        conductivity_coeff_b: Second conductivity coefficient. Default = 0.
        viscosity_coeff_b: Second viscosity coefficient. Default = 0.
        specific_heat_coeff_b: Second specific heat coefficient. Default = 0.
        conductivity_coeff_c: Third conductivity coefficient. Default = 0.
        viscosity_coeff_c: Third viscosity coefficient. Default = 0.
        specific_heat_coeff_c: Third specific heat coefficient. Default = 0.
        specific_heat_ratio: A number for the the ratio of the specific heat at
            contant pressure, to the specific heat at constant volume.
            Default is 1.0 for Air.
        molecular_weight: Number between 20 and 200 for the mass of 1 mol of
            the substance in grams. Default is 20.0.

    Properties:
        * identifier
        * display_name
        * thickness
        * conductivity_coeff_a
        * viscosity_coeff_a
        * specific_heat_coeff_a
        * conductivity_coeff_b
        * viscosity_coeff_b
        * specific_heat_coeff_b
        * conductivity_coeff_c
        * viscosity_coeff_c
        * specific_heat_coeff_c
        * specific_heat_ratio
        * molecular_weight
        * conductivity
        * viscosity
        * specific_heat
        * density
        * prandtl

    Usage:

    .. code-block:: python

        co2_gap = EnergyWindowMaterialGasCustom('CO2', 0.0125, 0.0146, 0.000014, 827.73)
        co2_gap.specific_heat_ratio = 1.4
        co2_gap.molecular_weight = 44
        print(co2_gap)
    """
    __slots__ = ('_conductivity_coeff_a', '_viscosity_coeff_a', '_specific_heat_coeff_a',
                 '_conductivity_coeff_b', '_viscosity_coeff_b', '_specific_heat_coeff_b',
                 '_conductivity_coeff_c', '_viscosity_coeff_c', '_specific_heat_coeff_c',
                 '_specific_heat_ratio', '_molecular_weight')

    def __init__(self, identifier, thickness,
                 conductivity_coeff_a, viscosity_coeff_a, specific_heat_coeff_a,
                 conductivity_coeff_b=0, viscosity_coeff_b=0, specific_heat_coeff_b=0,
                 conductivity_coeff_c=0, viscosity_coeff_c=0, specific_heat_coeff_c=0,
                 specific_heat_ratio=1.0, molecular_weight=20.0):
        """Initialize custom gas energy material."""
        _EnergyWindowMaterialGasBase.__init__(self, identifier, thickness)
        self.conductivity_coeff_a = conductivity_coeff_a
        self.viscosity_coeff_a = viscosity_coeff_a
        self.specific_heat_coeff_a = specific_heat_coeff_a
        self.conductivity_coeff_b = conductivity_coeff_b
        self.viscosity_coeff_b = viscosity_coeff_b
        self.specific_heat_coeff_b = specific_heat_coeff_b
        self.conductivity_coeff_c = conductivity_coeff_c
        self.viscosity_coeff_c = viscosity_coeff_c
        self.specific_heat_coeff_c = specific_heat_coeff_c
        self.specific_heat_ratio = specific_heat_ratio
        self.molecular_weight = molecular_weight
        self._user_data = None

    @property
    def conductivity_coeff_a(self):
        """Get or set the first conductivity coefficient."""
        return self._conductivity_coeff_a

    @conductivity_coeff_a.setter
    def conductivity_coeff_a(self, coeff):
        self._conductivity_coeff_a = float(coeff)

    @property
    def viscosity_coeff_a(self):
        """Get or set the first viscosity coefficient."""
        return self._viscosity_coeff_a

    @viscosity_coeff_a.setter
    def viscosity_coeff_a(self, coeff):
        self._viscosity_coeff_a = float_positive(coeff)

    @property
    def specific_heat_coeff_a(self):
        """Get or set the first specific heat coefficient."""
        return self._specific_heat_coeff_a

    @specific_heat_coeff_a.setter
    def specific_heat_coeff_a(self, coeff):
        self._specific_heat_coeff_a = float_positive(coeff)

    @property
    def conductivity_coeff_b(self):
        """Get or set the second conductivity coefficient."""
        return self._conductivity_coeff_b

    @conductivity_coeff_b.setter
    def conductivity_coeff_b(self, coeff):
        self._conductivity_coeff_b = float(coeff)

    @property
    def viscosity_coeff_b(self):
        """Get or set the second viscosity coefficient."""
        return self._viscosity_coeff_b

    @viscosity_coeff_b.setter
    def viscosity_coeff_b(self, coeff):
        self._viscosity_coeff_b = float(coeff)

    @property
    def specific_heat_coeff_b(self):
        """Get or set the second specific heat coefficient."""
        return self._specific_heat_coeff_b

    @specific_heat_coeff_b.setter
    def specific_heat_coeff_b(self, coeff):
        self._specific_heat_coeff_b = float(coeff)

    @property
    def conductivity_coeff_c(self):
        """Get or set the third conductivity coefficient."""
        return self._conductivity_coeff_c

    @conductivity_coeff_c.setter
    def conductivity_coeff_c(self, coeff):
        self._conductivity_coeff_c = float(coeff)

    @property
    def viscosity_coeff_c(self):
        """Get or set the third viscosity coefficient."""
        return self._viscosity_coeff_c

    @viscosity_coeff_c.setter
    def viscosity_coeff_c(self, coeff):
        self._viscosity_coeff_c = float(coeff)

    @property
    def specific_heat_coeff_c(self):
        """Get or set the third specific heat coefficient."""
        return self._specific_heat_coeff_c

    @specific_heat_coeff_c.setter
    def specific_heat_coeff_c(self, coeff):
        self._specific_heat_coeff_c = float(coeff)

    @property
    def specific_heat_ratio(self):
        """Get or set the specific heat ratio."""
        return self._specific_heat_ratio

    @specific_heat_ratio.setter
    def specific_heat_ratio(self, number):
        number = float(number)
        assert 1 <= number, 'Input specific_heat_ratio ({}) must be > 1.'.format(number)
        self._specific_heat_ratio = number

    @property
    def molecular_weight(self):
        """Get or set the molecular weight."""
        return self._molecular_weight

    @molecular_weight.setter
    def molecular_weight(self, number):
        self._molecular_weight = float_in_range(
            number, 20.0, 200.0, 'gas material molecular weight')

    def conductivity_at_temperature(self, t_kelvin):
        """Get the conductivity of the gas [W/m-K] at a given Kelvin temperature."""
        return self.conductivity_coeff_a + self.conductivity_coeff_b * t_kelvin + \
            self.conductivity_coeff_c * t_kelvin ** 2

    def viscosity_at_temperature(self, t_kelvin):
        """Get the viscosity of the gas [kg/m-s] at a given Kelvin temperature."""
        return self.viscosity_coeff_a + self.viscosity_coeff_b * t_kelvin + \
            self.viscosity_coeff_c * t_kelvin ** 2

    def specific_heat_at_temperature(self, t_kelvin):
        """Get the specific heat of the gas [J/kg-K] at a given Kelvin temperature."""
        return self.specific_heat_coeff_a + self.specific_heat_coeff_b * t_kelvin + \
            self.specific_heat_coeff_c * t_kelvin ** 2

    @classmethod
    def from_idf(cls, idf_string):
        """Create EnergyWindowMaterialGasCustom from an EnergyPlus text string.

        Args:
            idf_string: A text string fully describing an EnergyPlus material.
        """
        ep_s = parse_idf_string(idf_string, 'WindowMaterial:Gas,')
        assert ep_s[1].title() == 'Custom', 'Exected Custom Gas. Got a specific one.'
        ep_s.pop(1)
        return cls(*ep_s)

    @classmethod
    def from_dict(cls, data):
        """Create a EnergyWindowMaterialGasCustom from a dictionary.

        Args:
            data: A python dictionary in the following format

        .. code-block:: python

            {
            "type": 'EnergyWindowMaterialGasCustom',
            "identifier": 'CO2_0010_00146_0000014_82773_140_44',
            "display_name": 'CO2'
            "thickness": 0.01,
            "conductivity_coeff_a": 0.0146,
            "viscosity_coeff_a": 0.000014,
            "specific_heat_coeff_a": 827.73,
            "specific_heat_ratio": 1.4
            "molecular_weight": 44
            }
        """
        assert data['type'] == 'EnergyWindowMaterialGasCustom', \
            'Expected EnergyWindowMaterialGasCustom. Got {}.'.format(data['type'])
        con_b = 0 if 'conductivity_coeff_b' not in data else data['conductivity_coeff_b']
        vis_b = 0 if 'viscosity_coeff_b' not in data else data['viscosity_coeff_b']
        sph_b = 0 if 'specific_heat_coeff_b' not in data \
            else data['specific_heat_coeff_b']
        con_c = 0 if 'conductivity_coeff_c' not in data else data['conductivity_coeff_c']
        vis_c = 0 if 'viscosity_coeff_c' not in data else data['viscosity_coeff_c']
        sph_c = 0 if 'specific_heat_coeff_c' not in data \
            else data['specific_heat_coeff_c']
        sphr = 1.0 if 'specific_heat_ratio' not in data else data['specific_heat_ratio']
        mw = 20.0 if 'molecular_weight' not in data else data['molecular_weight']
        new_obj = cls(data['identifier'], data['thickness'],
                      data['conductivity_coeff_a'],
                      data['viscosity_coeff_a'],
                      data['specific_heat_coeff_a'],
                      con_b, vis_b, sph_b, con_c, vis_c, sph_c, sphr, mw)
        if 'display_name' in data and data['display_name'] is not None:
            new_obj.display_name = data['display_name']
        if 'user_data' in data and data['user_data'] is not None:
            new_obj.user_data = data['user_data']
        return new_obj

    def to_idf(self):
        """Get an EnergyPlus string representation of the material."""
        values = (self.identifier, 'Custom', self.thickness, self.conductivity_coeff_a,
                  self.conductivity_coeff_b, self.conductivity_coeff_c,
                  self.viscosity_coeff_a, self.viscosity_coeff_b,
                  self.viscosity_coeff_c, self.specific_heat_coeff_a,
                  self.specific_heat_coeff_b, self.specific_heat_coeff_c,
                  self.molecular_weight, self.specific_heat_ratio)
        comments = ('name', 'gas type', 'thickness', 'conductivity coeff a',
                    'conductivity coeff b', 'conductivity coeff c', 'viscosity coeff a',
                    'viscosity coeff b', 'viscosity coeff c', 'specific heat coeff a',
                    'specific heat coeff b', 'specific heat coeff c',
                    'molecular weight', 'specific heat ratio')
        return generate_idf_string('WindowMaterial:Gas', values, comments)

    def to_dict(self):
        """Energy Material Gas Custom dictionary representation."""
        base = {
            'type': 'EnergyWindowMaterialGasCustom',
            'identifier': self.identifier,
            'thickness': self.thickness,
            'conductivity_coeff_a': self.conductivity_coeff_a,
            'viscosity_coeff_a': self.viscosity_coeff_a,
            'specific_heat_coeff_a': self.specific_heat_coeff_a,
            'conductivity_coeff_b': self.conductivity_coeff_b,
            'viscosity_coeff_b': self.viscosity_coeff_b,
            'specific_heat_coeff_b': self.specific_heat_coeff_b,
            'conductivity_coeff_c': self.conductivity_coeff_c,
            'viscosity_coeff_c': self.viscosity_coeff_c,
            'specific_heat_coeff_c': self.specific_heat_coeff_c,
            'specific_heat_ratio': self.specific_heat_ratio,
            'molecular_weight': self.molecular_weight
        }
        if self._display_name is not None:
            base['display_name'] = self.display_name
        if self._user_data is not None:
            base['user_data'] = self.user_data
        return base

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (self.identifier, self.thickness, self.conductivity_coeff_a,
                self.viscosity_coeff_a, self.specific_heat_coeff_a,
                self.conductivity_coeff_b, self.viscosity_coeff_b,
                self.specific_heat_coeff_b, self.conductivity_coeff_c,
                self.viscosity_coeff_c, self.specific_heat_coeff_c,
                self.specific_heat_ratio, self.molecular_weight)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, EnergyWindowMaterialGasCustom) and \
            self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return self.to_idf()

    def __copy__(self):
        new_obj = EnergyWindowMaterialGasCustom(
            self.identifier, self.thickness, self.conductivity_coeff_a,
            self.viscosity_coeff_a, self.specific_heat_coeff_a,
            self.conductivity_coeff_b, self.viscosity_coeff_b,
            self.specific_heat_coeff_b, self.conductivity_coeff_c,
            self.viscosity_coeff_c, self.specific_heat_coeff_c,
            self.specific_heat_ratio, self.molecular_weight)
        new_obj._display_name = self._display_name
        return new_obj
