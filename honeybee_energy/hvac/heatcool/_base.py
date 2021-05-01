# coding=utf-8
"""Base class for all heating/cooling systems without any ventilation."""
from __future__ import division
import os

from honeybee._lockable import lockable

from .._template import _TemplateSystem, _EnumerationBase


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
    """
    __slots__ = ()


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
