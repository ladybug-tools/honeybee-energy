# coding=utf-8
"""Parameters with criteria for sizing the heating and cooling system."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee.typing import float_positive

from ladybug.ddy import DDY
from ladybug.designday import DesignDay
from ladybug.location import Location


class SizingParameter(object):
    """Sizing parameters with criteria for sizing the heating and cooling system.

    Args:
        design_days: An array of Ladybug DesignDay objects that represent the
            criteria for which the HVAC systems will be sized. Default: None.
        heating_factor: A number that will get multiplied by the peak heating load
            for each zone in the model in order to size the heating system for
            the model. Must be greater than 0. Default: 1.25.
        cooling_factor: A number that will get multiplied by the peak cooling load
            for each zone in the model in order to size the cooling system for
            the model. Must be greater than 0. Default: 1.15.

    Properties:
        * design_days
        * heating_factor
        * cooling_factor
    """
    __slots__ = ('_design_days', '_heating_factor', '_cooling_factor')

    def __init__(self, design_days=None, heating_factor=1.25, cooling_factor=1.15):
        """Initialize SizingParameter."""
        self.design_days = design_days
        self.heating_factor = heating_factor
        self.cooling_factor = cooling_factor

    @property
    def design_days(self):
        """Get or set an array of Ladybug DesignDay objects for sizing criteria."""
        return tuple(self._design_days)

    @design_days.setter
    def design_days(self, value):
        if value is not None:
            try:
                if not isinstance(value, list):
                    value = list(value)
            except TypeError:
                raise TypeError('Expected list or tuple for SizingParameter '
                                'design_days. Got {}'.format(type(value)))
            for dday in value:
                assert isinstance(dday, DesignDay), 'Expected ladybug DesignDay ' \
                    'for SizingParameter. Got {}.'.format(type(dday))
            self._design_days = value
        else:
            self._design_days = []

    @property
    def heating_factor(self):
        """Get or set a number that will get multiplied by the peak heating loads."""
        return self._heating_factor

    @heating_factor.setter
    def heating_factor(self, value):
        self._heating_factor = float_positive(value, 'sizing parameter heating factor')
        assert self._heating_factor != 0, 'SizingParameter heating factor cannot be 0.'

    @property
    def cooling_factor(self):
        """Get or set a number that will get multiplied by the peak cooling loads."""
        return self._cooling_factor

    @cooling_factor.setter
    def cooling_factor(self, value):
        self._cooling_factor = float_positive(value, 'sizing parameter cooling factor')
        assert self._cooling_factor != 0, 'SizingParameter cooling factor cannot be 0.'

    def add_design_day(self, design_day):
        """Add a ladybug DesignDay to this object's design_days.

        Args:
            design_day: A Ladybug DesignDay object to be added to this object.
        """
        assert isinstance(design_day, DesignDay), 'Expected ladybug DesignDay for' \
            ' SizingParameter. Got {}.'.format(type(design_day))
        self._design_days.append(design_day)

    def add_from_ddy(self, ddy_file):
        """Add all design days within a .ddy file to this object.

        Args:
            ddy_file: The full path to a .ddy file on this machine.
        """
        ddy_obj = DDY.from_ddy_file(ddy_file)
        for dday in ddy_obj:
            self._design_days.append(dday)

    def add_from_ddy_996_004(self, ddy_file):
        """Add the 99.6% and 0.4% design days within a .ddy file to this object.

        99.6% means that this percent of the hours of the year have outside heating
        conditions warmer than this design day. 0.4% means that this percent of the
        hours of the year have outside cooling conditions cooler than this design day.

        Args:
            ddy_file: The full path to a .ddy file on this machine.
        """
        ddy_obj = DDY.from_ddy_file(ddy_file)
        for dday in ddy_obj:
            if '99.6%' in dday.name or '.4%' in dday.name:
                self._design_days.append(dday)

    def add_from_ddy_990_010(self, ddy_file):
        """Add the 99.0% and 1.0% design days within a .ddy file to this object.

        99.0% means that this percent of the hours of the year have outside heating
        conditions warmer than this design day. 1.0% means that this percent of the
        hours of the year have outside cooling conditions cooler than this design day.

        Args:
            ddy_file: The full path to a .ddy file on this machine.
        """
        ddy_obj = DDY.from_ddy_file(ddy_file)
        for dday in ddy_obj:
            if '99%' in dday.name or '1%' in dday.name:
                self._design_days.append(dday)

    def add_from_ddy_keyword(self, ddy_file, keyword):
        """Add DesignDays from a .ddy file using a keyword in the DesignDay name.

        Args:
            ddy_file: The full path to a .ddy file on this machine.
            keyword: String for a keyword, which will be used to select DesignDays
                from the .ddy file to add to this object.
        """
        ddy_obj = DDY.from_ddy_file(ddy_file)
        for dday in ddy_obj:
            if keyword in dday.name:
                self._design_days.append(dday)

    def remove_design_day(self, design_day_index):
        """Remove a single DesignDay from this object using an index.

        Args:
            design_day_index: An interger for the index of the DesignDay to remove.
        """
        del self._design_days[design_day_index]

    def remove_design_day_keyword(self, keyword):
        """Remove DesignDays from this object using a keyword in the DesignDay names.

        Args:
            keyword: String for a keyword, which will be used to select DesignDays
                for deletion from this object.
        """
        design_days = []
        for dday in self._design_days:
            if keyword not in dday.name:
                design_days.append(dday)
        self._design_days = design_days

    def remove_all_design_days(self):
        """Remove all DesignDays from this object."""
        self._design_days = []

    def apply_location(self, location):
        """Apply a Ladybug Location object to all of the DesignDays in this object.

        This is particularly handy after re-serialization from an IDF since the
        IDF does not store the location information in the DesignDay.

        Args:
            location: A Ladybug Location object.
        """
        assert isinstance(location, Location), \
            'Expected Ladybug Location. Got {}.'.format(type(Location))
        for dday in self._design_days:
            dday.location = location

    @classmethod
    def from_idf(cls, design_days=None, sizing_parameter=None, location=None):
        """Create a SizingParameter object from an EnergyPlus IDF text string.

        Args:
            design_days: An array of of IDF SizingPeriod:DesignDay strings that
                represent the criteria for which the HVAC systems will be sized.
                If None, no sizing criteria will be included. Default: None.
            sizing_parameter: A text string for an EnergyPlus Sizing:Parameters
                definition. If None, defaults of 1.25 anf 1.15 will be used.
                Default: None.
            location: An optional Ladybug Location object, which gets assigned
                to the DesignDay objects in order to interpret their SkyConditions.
                This object is not used in the export to IDF. If None, the
                intersection of the equator with the prime meridian will be used.
                Default: None.
        """
        # process the input design_days
        des_day_objs = None
        if design_days is not None:
            location = Location() if location is None else location
            des_day_objs = [DesignDay.from_idf(dday, location) for dday in design_days]

        # process the sizing_parameter
        heating_factor = 1.25
        cooling_factor = 1.15
        if sizing_parameter is not None:
            try:
                ep_strs = parse_idf_string(sizing_parameter, 'Sizing:Parameters,')
                heating_factor = ep_strs[0] if ep_strs[0] != '' else 1.25
                cooling_factor = ep_strs[1] if ep_strs[1] != '' else 1.15
            except IndexError:
                pass  # shorter SizingParameters definition

        return cls(des_day_objs, heating_factor, cooling_factor)

    @classmethod
    def from_dict(cls, data):
        """Create a SizingParameter object from a dictionary.

        Args:
            data: A SizingParameter dictionary in following the format.

        .. code-block:: python

            {
            "type": "SizingParameter",
            "design_days": [],  # Array of Ladybug DesignDay dictionaries
            "heating_factor": 1.25,
            "cooling_factor": 1.15
            }
        """
        assert data['type'] == 'SizingParameter', \
            'Expected SizingParameter dictionary. Got {}.'.format(data['type'])
        design_days = None
        if 'design_days' in data and data['design_days'] is not None:
            design_days = [DesignDay.from_dict(dday) for dday in data['design_days']]
        heating_factor = data['heating_factor'] if 'heating_factor' in data else 1.25
        cooling_factor = data['cooling_factor'] if 'cooling_factor' in data else 1.15
        return cls(design_days, heating_factor, cooling_factor)

    def to_idf(self):
        """Get an EnergyPlus string representation of the SizingParameters.

        Returns:
            A tuple with two elements

            -   design_days: An array of of IDF SizingPeriod:DesignDay strings.

            -   sizing_parameter: A text string for an EnergyPlus Sizing:Parameters
                definition.
        """
        # process the design_days
        design_days = [dday.to_idf() for dday in self.design_days]
        # process the Sizing:Parameters object
        values = (self.heating_factor, self.cooling_factor)
        comments = ('heating factor', 'cooling factor')
        sizing_parameter = generate_idf_string('Sizing:Parameters', values, comments)
        return design_days, sizing_parameter

    def to_dict(self):
        """SizingParameter dictionary representation."""
        siz_par = {
            'type': 'SizingParameter',
            'heating_factor': self.heating_factor,
            'cooling_factor': self.cooling_factor
        }
        if len(self._design_days) != 0:
            siz_par['design_days'] = [dday.to_dict(False) for dday in self.design_days]
        return siz_par

    def to_ddy(self):
        """Get this SizingParameter as a Ladybug DDY object.

        This can be written to a .ddy file if so desired.
        """
        assert len(self._design_days) != 0, \
            'There must be at least one design_day to use SizingParameter.to_ddy.'
        return DDY(self._design_days[0].location, self._design_days)

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SizingParameter([dday.duplicate() for dday in self._design_days],
                               self.heating_factor, self.cooling_factor)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return tuple(hash(dday) for dday in self._design_days) + \
            (self.heating_factor, self.cooling_factor)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SizingParameter) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __len__(self):
        return len(self._design_days)

    def __getitem__(self, key):
        return self._design_days[key]

    def __setitem__(self, key, value):
        assert isinstance(value, DesignDay), \
            'Expected DesignDay type. Got {}'.format(type(value))
        self._design_days[key] = value

    def __iter__(self):
        return iter(self._design_days)

    def __contains__(self, item):
        return item in self._design_days

    def __repr__(self):
        return 'SizingParameter: [{} design days] [heating: {}] [cooling: {}]'.format(
            len(self._design_days), self.heating_factor, self.cooling_factor)
