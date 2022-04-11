# coding=utf-8
"""Base class for all heating/cooling systems without any ventilation."""
from __future__ import division
import os

from honeybee._lockable import lockable

from .._template import _TemplateSystem, _EnumerationBase
from ..idealair import IdealAirSystem
from ...properties.extension import HeatCoolSystemProperties


@lockable
class _HeatCoolBase(_TemplateSystem):
    """Base class for all heating/cooling systems without any ventilation.

    Args:
        identifier: Text string for system identifier. Must be < 100 characters
            and not contain any EnergyPlus special characters. This will be used to
            identify the object across a model and in the exported IDF.
        vintage: Text for the vintage of the template system. This will be used
            to set efficiencies for various pieces of equipment within the system.
            Choose from the following.

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013
            * ASHRAE_2016
            * ASHRAE_2019

        equipment_type: Text for the specific type of the system and equipment.
            For example, 'Baseboard gas boiler'.

    Properties:
        * identifier
        * display_name
        * vintage
        * equipment_type
        * sensible_heat_recovery
        * latent_heat_recovery
        * schedules
        * properties
    """
    __slots__ = ('_properties')
    COOL_ONLY_TYPES = (
            'EvapCoolers', 'FCU_Chiller', 'FCU_ACChiller', 'FCU_DCW',
            'ResidentialAC', 'WindowAC'
        )
    HEAT_ONLY_TYPES = (
            'ElectricBaseboard', 'BoilerBaseboard', 'ASHPBaseboard',
            'DHWBaseboard', 'GasHeaters', 'ResidentialHPNoCool', 'ResidentialFurnace'
        )

    def __init__(self, identifier, vintage='ASHRAE_2019', equipment_type=None):
        # initialize base HVAC system properties
        super(_HeatCoolBase, self).__init__(identifier, vintage, equipment_type)
        self._properties = HeatCoolSystemProperties(self)

    def to_ideal_air_equivalent(self):
        """Get a version of this HVAC as an IdealAirSystem."""
        i_sys = IdealAirSystem(self.identifier)
        if self.equipment_type in self.COOL_ONLY_TYPES:
            i_sys.heating_limit = 0
        if self.equipment_type in self.HEAT_ONLY_TYPES:
            i_sys.cooling_limit = 0
        i_sys.economizer_type = 'NoEconomizer'
        i_sys._display_name = self._display_name
        return i_sys

    @property
    def properties(self):
        """Get properties for extensions."""
        return self._properties

    @classmethod
    def from_dict(cls, data):
        new_obj = super(_HeatCoolBase, cls).from_dict(data)
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    @classmethod
    def from_dict_abridged(cls, data, schedule_dict):
        new_obj = super(_HeatCoolBase, cls).from_dict_abridged(data, schedule_dict)
        if 'properties' in data and data['properties'] is not None:
            new_obj.properties._load_extension_attr_from_dict(data['properties'])
        return new_obj

    def to_dict(self, abridged=False):
        base = super(_HeatCoolBase, self).to_dict(abridged)
        prop_dict = self.properties.to_dict()
        if prop_dict is not None:
            base['properties'] = prop_dict
        return base

    def __copy__(self):
        new_obj = super(_HeatCoolBase, self).__copy__()
        new_obj._properties._duplicate_extension_attr(self._properties)
        return new_obj

class _HeatCoolEnumeration(_EnumerationBase):
    """Enumerates the systems that inherit from _HeatCoolBase."""

    def __init__(self, import_modules=True):
        if import_modules:
            self._import_modules(
                os.path.dirname(__file__), 'honeybee_energy.hvac.heatcool')

        self._HVAC_TYPES = {}
        self._EQUIPMENT_TYPES = {}
        for clss in _HeatCoolBase.__subclasses__():
            self._HVAC_TYPES[clss.__name__] = clss
            for equip_type in clss.EQUIPMENT_TYPES:
                self._EQUIPMENT_TYPES[equip_type] = clss
