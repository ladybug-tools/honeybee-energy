"""Extra AltNumber objects for Energy models.

Note to developers:
    See _extend_honeybee to see where these alternate numbers are added to
    honeybee.altnumber module.
"""
from honeybee.altnumber import _AltNumber


class Autosize(_AltNumber):
    """Object for a numerical value is determined from a sizing calculation.

    This object is specifically for values determined during the EnergyPlus sizing
    calculation and is therefore disctinct from numerical values that are
    generically Autocalculated.
    """
    __slots__ = ()
    pass


autosize = Autosize()
