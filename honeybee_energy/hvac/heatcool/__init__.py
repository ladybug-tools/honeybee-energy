"""Template HVAC definitions that only supply heating + cooling (no ventilation).

These systems are only designed to satisfy heating + cooling demand and they
cannot meet any minimum ventilation requirements.

As such, these systems tend to be used in residential or storage settings where
meeting minimum ventilation requirements may not be required or the density
of occupancy is so low that infiltration is enough to meet fresh air demand.

Properties:
    * HVAC_TYPES_DICT: A dictionary containing pointers to the classes of each
        HVAC system. The keys of this dictionary are the names of the HVAC
        classes (eg. 'Baseboard').
    * EQUIPMENT_TYPES_DICT: A dictionary containing pointers to the classes of
        the HVAC systems. The keys of this dictionary are the names of the HVAC
        systems as they appear in the OpenStudio standards gem and include the
        specific equipment in the system (eg. 'Baseboard gas boiler').
"""
from ._base import _HeatCoolEnumeration

_heat_cool_types = _HeatCoolEnumeration(import_modules=True)
HVAC_TYPES_DICT = _heat_cool_types.types_dict
EQUIPMENT_TYPES_DICT = _heat_cool_types.equipment_types_dict
