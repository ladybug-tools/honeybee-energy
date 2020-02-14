"""honeybee-energy HVAC definitions.

To extend this sub-package with a new HVAC system template, add a module that contains
a single class inheriting from _HVACSystem in hvac._base. Then, add the class to the
HVAC_TYPES_DICT using the name of the class as the key.

Properties:
    * HVAC_TYPES_DICT: A dictionary containing pointers to the classes of each HVAC system.
      The keys of this dictionary are the names of the HVAC classes.
"""
from .idealair import IdealAirSystem


HVAC_TYPES_DICT = {'IdealAirSystem': IdealAirSystem}
