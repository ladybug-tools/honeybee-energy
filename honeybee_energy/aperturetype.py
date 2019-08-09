# coding=utf-8
"""Aperture Types."""
from honeybee.aperturetype import _ApertureType


class OperableWindow(_ApertureType):
    """Type for windows that can be opened for natural ventilation."""
    __slots__ = ()
    pass


class GlassDoor(_ApertureType):
    """Type for glass doors."""
    __slots__ = ()
    pass
