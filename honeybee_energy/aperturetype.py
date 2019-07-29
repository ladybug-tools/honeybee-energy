# coding=utf-8
"""Aperture Types."""
from honeybee.aperturetype import _ApertureType
from honeybee.typing import float_in_range


class OperableWindow(_ApertureType):
    __slots__ = ('_fraction_operable',)

    """Type for operable apertures that can be opened for natrual ventilation."""

    def __init__(self, fraction_operable=0.5):
        """Initialize operable ApertureType.

        Args:
            fraction_operable: A number between 0 and 1 for the fraction of the
                Aperture area that is operable. Default: 0.5.
        """
        self._fraction_operable = float_in_range(
            fraction_operable, 0.0, 1.0, 'aperture fraction operabe')

    @classmethod
    def from_dict(cls, data):
        """Initialize ApertureType from a dictionary.

        Args:
            data: A dictionary representaion of the aperture type.
        """
        return cls(data['fraction_operable'])

    @property
    def fraction_operable(self):
        """Get or set the fraction of the aperture area that is operable."""
        return self._fraction_operable

    def to_dict(self):
        """ApertureType as a dictionary."""
        ap_type_dict = {
            'type': 'OperableWindow',
            'fraction_operable': self.fraction_operable}
        return ap_type_dict

    def __eq__(self, other):
        return self.__class__ == other.__class__ and \
            self._fraction_operable == other._fraction_operable


class GlassDoor(_ApertureType):
    """Type for glass doors."""
    __slots__ = ()
    pass
