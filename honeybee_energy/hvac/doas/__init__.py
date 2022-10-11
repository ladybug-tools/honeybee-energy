"""Template Dedicated Outdoor Air System (DOAS) HVAC definitions.

DOAS systems separate minimum ventilation supply from the satisfaction of heating
+ cooling demand. Ventilation air tends to be supplied at neutral temperatures
(close to room air temperature) and heating / cooling loads are met with additional
pieces of zone equipment (eg. Fan Coil Units (FCUs)).

Because DOAS systems only have to cool down and re-heat the minimum ventilation air,
they tend to use less energy than all-air systems. They also tend to use less energy
to distribute heating + cooling by pumping around hot/cold water or refrigerant
instead of blowing hot/cold air. However, they do not provide as good of control
over humidity and so they may not be appropriate for rooms with high latent loads
like auditoriums, kitchens, laundromats, etc.

Properties:
    * HVAC_TYPES_DICT: A dictionary containing pointers to the classes of each
        HVAC system. The keys of this dictionary are the names of the HVAC
        classes (eg. 'FCU').
    * EQUIPMENT_TYPES_DICT: A dictionary containing pointers to the classes of
        the HVAC systems. The keys of this dictionary are the names of the HVAC
        systems as they appear in the OpenStudio standards gem and include the
        specific equipment in the system (eg. 'DOAS with fan coil chiller with boiler').
"""
from ._base import _DOASEnumeration

_doas_types = _DOASEnumeration(import_modules=True)
HVAC_TYPES_DICT = _doas_types.types_dict
EQUIPMENT_TYPES_DICT = _doas_types.equipment_types_dict
