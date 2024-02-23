# coding=utf-8
"""Parameters with criteria for sizing the heating and cooling system."""
from __future__ import division

from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee.typing import float_positive, valid_ep_string

from ladybug.ddy import DDY
from ladybug.designday import DesignDay
from ladybug.location import Location


class SizingParameter(object):
    """Sizing parameters with criteria for sizing the heating and cooling system.

    Args:
        design_days: An array of Ladybug DesignDay objects that represent the
            criteria for which the HVAC systems will be sized. (Default: None).
        heating_factor: A number that will get multiplied by the peak heating load
            for each zone in the model in order to size the heating system for
            the model. Must be greater than 0. (Default: 1.25).
        cooling_factor: A number that will get multiplied by the peak cooling load
            for each zone in the model in order to size the cooling system for
            the model. Must be greater than 0. (Default: 1.15).
        efficiency_standard: Text to specify the efficiency standard, which will
            automatically set the efficiencies of all HVAC equipment when provided.
            Note that providing a standard here will cause the OpenStudio translation
            process to perform an additional sizing calculation with EnergyPlus,
            which is needed since the default efficiencies of equipment vary depending
            on their size. THIS WILL SIGNIFICANTLY INCREASE TRANSLATION TIME.
            However, it is often worthwhile when the goal is to match the
            HVAC specification with a particular standard. (Default: None).
            Choose from the following.

            * DOE_Ref_Pre_1980
            * DOE_Ref_1980_2004
            * ASHRAE_2004
            * ASHRAE_2007
            * ASHRAE_2010
            * ASHRAE_2013
            * ASHRAE_2016
            * ASHRAE_2019

        climate_zone: Text indicating the ASHRAE climate zone to be used with the
            efficiency_standard. When unspecified, the climate zone will be
            inferred from the design days. This input can be a single
            integer (in which case it is interpreted as A) or it can include the
            A, B, or C qualifier (eg. 3C).
        building_type: Text for the building type to be used in the efficiency_standard.
            If the type is not recognized or is None, it will be assumed that the
            building is a generic NonResidential. The following have meaning
            for the standard.

            * NonResidential
            * Residential
            * MidriseApartment
            * HighriseApartment
            * LargeOffice
            * MediumOffice
            * SmallOffice
            * Retail
            * StripMall
            * PrimarySchool
            * SecondarySchool
            * SmallHotel
            * LargeHotel
            * Hospital
            * Outpatient
            * Warehouse
            * SuperMarket
            * FullServiceRestaurant
            * QuickServiceRestaurant
            * Laboratory
            * Courthouse
        
        bypass_efficiency_sizing: A boolean to indicate whether the efficiency
            standard should trigger an sizing run that sets the efficiencies
            of all HVAC equipment in the Model (False) or the standard should
            only be written into the OSM and the sizing run should be
            bypassed (True). Bypassing the sizing run is useful when you only
            want to check that the overall HVAC system architecture is correct
            and you do not want to wait the extra time that it takes to run the
            sizing calculation. (Default: False).

    Properties:
        * design_days
        * heating_factor
        * cooling_factor
        * efficiency_standard
        * climate_zone
        * building_type
        * bypass_efficiency_sizing
    """
    __slots__ = ('_design_days', '_heating_factor', '_cooling_factor',
                 '_efficiency_standard', '_climate_zone', '_building_type',
                 '_bypass_efficiency_sizing')
    STANDARDS = ('DOE_Ref_Pre_1980', 'DOE_Ref_1980_2004', 'ASHRAE_2004', 'ASHRAE_2007',
                 'ASHRAE_2010', 'ASHRAE_2013', 'ASHRAE_2016', 'ASHRAE_2019')
    CLIMATE_ZONES = (
        '0A', '1A', '2A', '3A', '4A', '5A', '6A',
        '0B', '1B', '2B', '3B', '4B', '5B', '6B',
        '3C', '4C', '5C', '7', '8'
    )

    def __init__(self, design_days=None, heating_factor=1.25, cooling_factor=1.15,
                 efficiency_standard=None, climate_zone=None, building_type=None,
                 bypass_efficiency_sizing=False):
        """Initialize SizingParameter."""
        self.design_days = design_days
        self.heating_factor = heating_factor
        self.cooling_factor = cooling_factor
        self.efficiency_standard = efficiency_standard
        self.climate_zone = climate_zone
        self.building_type = building_type
        self.bypass_efficiency_sizing = bypass_efficiency_sizing

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

    @property
    def efficiency_standard(self):
        """Get or set text for the efficiency standard.

        When specified, this will automatically set the efficiencies of all HVAC
        equipment. Note that setting this variable will cause the OpenStudio
        translation process to perform an additional sizing calculation with EnergyPlus,
        which is needed since the default efficiencies of equipment vary depending
        on their size. So THIS WILL SIGNIFICANTLY INCREASE TRANSLATION TIME.
        However, it is often worthwhile when the goal is to match the
        HVAC specification with a particular standard. Choose from the following.

        * DOE_Ref_Pre_1980
        * DOE_Ref_1980_2004
        * ASHRAE_2004
        * ASHRAE_2007
        * ASHRAE_2010
        * ASHRAE_2013
        * ASHRAE_2016
        * ASHRAE_2019
        """
        return self._efficiency_standard

    @efficiency_standard.setter
    def efficiency_standard(self, value):
        if value:
            clean_input = valid_ep_string(value, 'efficiency_standard').lower()
            for key in self.STANDARDS:
                if key.lower() == clean_input:
                    value = key
                    break
            else:
                raise ValueError(
                    'Efficiency standard "{}" is not recognized.\nChoose from the '
                    'following:\n{}'.format(value, self.STANDARDS))
        else:
            value = None
        self._efficiency_standard = value

    @property
    def climate_zone(self):
        """Get or set text for the climate zone associated with the efficiency standard.

        When unspecified, the climate zone will be inferred from the design days.
        This input can be a single integer (in which case it is interpreted as A)
        or it can include the A, B, or C qualifier (eg. 3C).
        """
        return self._climate_zone

    @climate_zone.setter
    def climate_zone(self, value):
        if value:
            value = valid_ep_string(value, 'climate_zone').upper()
            if len(value) == 1 and value not in ('7', '8'):
                value = '{}A'.format(value)
            if value not in self.CLIMATE_ZONES:
                raise ValueError(
                    'Efficiency climate zone "{}" is not recognized.\nChoose from the '
                    'following:\n{}'.format(value, self.CLIMATE_ZONES))
        else:
            value = None
        self._climate_zone = value

    @property
    def building_type(self):
        """Get or set text for the building type associated with the efficiency standard.

        If the type is not recognized or is None, it will be assumed that the
        building is a generic NonResidential.
        """
        return self._building_type

    @building_type.setter
    def building_type(self, value):
        if value:
            value = valid_ep_string(value, 'building_type')
        else:
            value = None
        self._building_type = value

    @property
    def bypass_efficiency_sizing(self):
        """Get or set a boolean for whether efficiency standard triggers a sizing run."""
        return self._bypass_efficiency_sizing

    @bypass_efficiency_sizing.setter
    def bypass_efficiency_sizing(self, value):
        self._bypass_efficiency_sizing = bool(value)

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
            design_day_index: An integer for the index of the DesignDay to remove.
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
            "cooling_factor": 1.15,
            "efficiency_standard": "ASHRAE_2004",  # standard for HVAC efficiency
            "climate_zone": "5A",  # climate zone for HVAC efficiency
            "building_type": "LargeOffice",  # building type for HVAC efficiency
            "bypass_efficiency_sizing": False  # bypass the efficiency sizing run
            }
        """
        assert data['type'] == 'SizingParameter', \
            'Expected SizingParameter dictionary. Got {}.'.format(data['type'])
        design_days = None
        if 'design_days' in data and data['design_days'] is not None:
            design_days = [DesignDay.from_dict(dday) for dday in data['design_days']]
        heating_factor = data['heating_factor'] if 'heating_factor' in data else 1.25
        cooling_factor = data['cooling_factor'] if 'cooling_factor' in data else 1.15
        es = data['efficiency_standard'] if 'efficiency_standard' in data else None
        cz = data['climate_zone'] if 'climate_zone' in data else None
        bt = data['building_type'] if 'building_type' in data else None
        bes = data['bypass_efficiency_sizing'] \
            if 'bypass_efficiency_sizing' in data else False
        return cls(design_days, heating_factor, cooling_factor, es, cz, bt, bes)

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
        if self.efficiency_standard is not None:
            siz_par['efficiency_standard'] = self.efficiency_standard
        if self.climate_zone is not None:
            siz_par['climate_zone'] = self.climate_zone
        if self.building_type is not None:
            siz_par['building_type'] = self.building_type
        if len(self._design_days) != 0:
            siz_par['design_days'] = [dday.to_dict(False) for dday in self.design_days]
        if self.bypass_efficiency_sizing:
            siz_par['bypass_efficiency_sizing'] = self.bypass_efficiency_sizing
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
        return SizingParameter(
            [dday.duplicate() for dday in self._design_days],
            self.heating_factor, self.cooling_factor, self.efficiency_standard,
            self.climate_zone, self.building_type, self.bypass_efficiency_sizing)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return tuple(hash(dday) for dday in self._design_days) + \
            (self.heating_factor, self.cooling_factor, self.efficiency_standard,
             self.climate_zone, self.building_type, self.bypass_efficiency_sizing)

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
