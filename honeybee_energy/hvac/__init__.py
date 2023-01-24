"""honeybee-energy HVAC definitions.

To extend this sub-package with a new HVAC system template, add a module that contains
a single class inheriting from _HVACSystem in hvac._base. Then, add the class to the
HVAC_TYPES_DICT using the name of the class as the key.

Properties:
    * HVAC_TYPES_DICT: A dictionary containing pointers to the classes of each
        HVAC system. The keys of this dictionary are the names of the HVAC classes.
"""
from .idealair import IdealAirSystem
from .allair import HVAC_TYPES_DICT as allair_types
from .doas import HVAC_TYPES_DICT as doas_types
from .heatcool import HVAC_TYPES_DICT as heatcool_types
from .detailed import DetailedHVAC

HVAC_TYPES_DICT = {'IdealAirSystem': IdealAirSystem}
HVAC_TYPES_DICT.update(allair_types)
HVAC_TYPES_DICT.update(doas_types)
HVAC_TYPES_DICT.update(heatcool_types)
HVAC_TYPES_DICT['DetailedHVAC'] = DetailedHVAC
