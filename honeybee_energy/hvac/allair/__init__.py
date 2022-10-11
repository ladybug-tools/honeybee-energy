"""Template All-air HVAC definitions.

All-air systems provide both ventilation and heating + cooling demand with
the same stream of warm/cool air. As such, they often grant tight control
over zone humidity. However, because such systems often involve the
cooling of air only to reheat it again, they are often more energy intensive
than systems that separate ventilation from the meeting of thermal loads.

Properties:
    * HVAC_TYPES_DICT: A dictionary containing pointers to the classes of each
        HVAC system. The keys of this dictionary are the names of the HVAC
        classes (eg. 'VAV').
    * EQUIPMENT_TYPES_DICT: A dictionary containing pointers to the classes of
        the HVAC systems. The keys of this dictionary are the names of the HVAC
        systems as they appear in the OpenStudio standards gem and include the
        specific equipment in the system (eg. 'VAV chiller with gas boiler reheat').
"""
from ._base import _AllAirEnumeration

_all_air_types = _AllAirEnumeration(import_modules=True)
HVAC_TYPES_DICT = _all_air_types.types_dict
EQUIPMENT_TYPES_DICT = _all_air_types.equipment_types_dict
