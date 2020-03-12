# coding=utf-8
"""Module for coloring Model geometry with energy simulation results."""
from __future__ import division

from honeybee.typing import int_in_range
from honeybee.room import Room
from honeybee.facetype import Floor


from ladybug.datatype.energyintensity import EnergyIntensity
from ladybug.datatype.energyflux import EnergyFlux

from ladybug.dt import Date, DateTime
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.datacollection import MonthlyCollection, DailyCollection, \
    MonthlyPerHourCollection, HourlyContinuousCollection, HourlyDiscontinuousCollection
from ladybug.graphic import GraphicContainer
from ladybug.legend import LegendParameters

from ladybug_geometry.geometry3d.pointvector import Point3D


class ColorRoom(object):
    """Object for visualization zone-level simulation results on Honeybee Room geometry.

    Args:
        data_collections: An array of HourlyContinuousCollections of the same data type,
            which will be used to color Rooms with simulation results. Data collections
            can be of any class (eg. MonthlyCollection, DailyCollection) but they
            should all have headers with metadata dictionaries with 'Zone' or
            'System' keys. These keys will be used to match the data in the collections
            to the input rooms.
        rooms: An array of honeybee Rooms, which will be matched to the data_collections.
            The length of these Rooms does not have to match the data_collections
            and this object will only create visualizations for rooms that are
            found to be matching.
        legend_parameters: An optional LegendParameter object to change the display
            of the ColorRooms (Default: None).
        simulation_step: An optional integer (greater than or equal to 0) to select
            a specific step of the data collections for which result values will be
            generated. If None, the geometry will be colored with the total of
            resutls in the data_collections if the data type is cumulative or with
            the average of results if the data type is not cumulative. Default: None.
        normalize_by_floor: Boolean to note whether results should be normalized
            by the floor area of the Room if the data type of the data_colections
            supports it. If False, values will be generated using sum total of
            the data collection values. Note that this input has no effect if
            the data type of the data_collections is not cumulative since data
            collection values will always be averaged for this case. Default: True.
        geo_unit: Optional text to note the units that the Room geometry is in.
            This will be used to ensure the legend units display correctly when
            data is floor-normalized. Examples include 'm', 'mm', 'ft'.
            (Default: 'm' for meters).

    Properties:
        * data_collections
        * rooms
        * legend_parameters
        * simulation_step
        * normalize_by_floor
        * geo_unit
        * matched_rooms
        * matched_values
        * matched_floor_faces
        * matched_floor_areas
        * graphic_container
        * title_text
        * data_type_text
        * data_type
        * unit
        * analysis_period
        * min_point
        * max_point
    """
    __slots__ = ('_data_collections', '_rooms', '_legend_parameters', '_geo_unit',
                 '_simulation_step', '_normalize_by_floor', '_matched_objects',
                 '_base_collection', '_base_type', '_base_unit',
                 '_min_point', '_max_point')

    def __init__(self, data_collections, rooms, legend_parameters=None,
                 simulation_step=None, normalize_by_floor=True, geo_unit='m'):
        """Initialize ColorRoom."""
        # check the input collections
        acceptable_colls = (MonthlyCollection, DailyCollection, MonthlyPerHourCollection,
                            HourlyContinuousCollection, HourlyDiscontinuousCollection)
        try:
            data_collections = list(data_collections)
        except TypeError:
            raise TypeError('Input data_collections must be an array. Got {}.'.format(
                type(data_collections)))
        assert len(data_collections) > 0, \
            'ColorRooms must have at least one data_collection.'
        for i, coll in enumerate(data_collections):
            assert isinstance(coll, acceptable_colls), 'Expected data collection for ' \
                'ColorRoom data_collections. Got {}.'.format(type(coll))
            assert 'Zone' in coll.header.metadata or 'System' in coll.header.metadata, \
                'ColorRoom data collection does not have metadata associated with Zones.'
            if not coll.validated_a_period:
                data_collections[i] = coll.validate_analysis_period()
        self._base_collection = data_collections[0]
        self._base_type = self._base_collection.header.data_type
        self._base_unit = self._base_collection.header.unit
        for coll in data_collections[1:]:
            assert coll.header.unit == self._base_unit, 'ColorRoom data_collections must all' \
                ' have matching units. {} != {}.'.format(coll.header.unit. self._unit)
            assert len(coll.values) == len(self._base_collection.values), \
                'ColorRoom data_collections must all be aligned with one another.' \
                '{} != {}'.format(len(coll.values), len(self._base_collection.values))
        self._data_collections = data_collections

        try:  # check the input rooms
            rooms = tuple(rooms)
        except TypeError:
            raise TypeError('Input rooms must be an array. Got {}.'.format(type(rooms)))
        assert len(rooms) > 0, 'ColorRooms must have at least one room.'
        for room in rooms:
            assert isinstance(room, Room), 'Expected honeybee Room for ' \
                'ColorRoom rooms. Got {}.'.format(type(room))
        self._rooms = rooms
        self._calculate_min_max()

        # match the rooms with the data collections
        self._match_rooms_to_data()
        if len(self._matched_objects) == 0:
            raise ValueError('None of the ColorRoom data collections could be '
                             'matched to the input rooms')

        # assign the other properties of this object
        self.legend_parameters = legend_parameters
        self.simulation_step = simulation_step
        self.normalize_by_floor = normalize_by_floor
        self.geo_unit = geo_unit

    @property
    def data_collections(self):
        """Get a tuple of data collections assigned to this object."""
        return tuple(self._data_collections)

    @property
    def rooms(self):
        """Get a tuple of honeybee Rooms assigned to this object."""
        return self._rooms

    @property
    def legend_parameters(self):
        """Get or set the legend parameters."""
        return self._legend_parameters

    @legend_parameters.setter
    def legend_parameters(self, value):
        if value is not None:
            assert isinstance(value, LegendParameters), \
                'Expected LegendParameters. Got {}.'.format(type(value))
            self._legend_parameters = legend_parameters.duplicate()
        else:
            self._legend_parameters = LegendParameters()

    @property
    def simulation_step(self):
        """Get or set an integer to select a specific step of the data collections."""
        return self._simulation_step

    @simulation_step.setter
    def simulation_step(self, value):
        if value is not None:
            value = int_in_range(
                value, 0, len(self._base_collection) - 1, 'simulation_step')
        self._simulation_step = value

    @property
    def normalize_by_floor(self):
        """Get or set a boolean for whether results should be normalized by floor area.
        """
        return self._normalize_by_floor

    @normalize_by_floor.setter
    def normalize_by_floor(self, value):
        self._normalize_by_floor = bool(value)

    @property
    def geo_unit(self):
        """Text to note the units that the Room geometry is in.

        This will be used to ensure the legend units display correctly when
        data is floor-normalized. Examples include 'm', 'mm', 'ft'.
        """
        return self._geo_unit

    @geo_unit.setter
    def geo_unit(self, value):
        self._geo_unit = str(value)

    @property
    def matched_rooms(self):
        """Get a tuple of honeybee Rooms that have been matched to the data."""
        return tuple(obj[0] for obj in self._matched_objects)

    @property
    def matched_values(self):
        """Get an array of numbers that correspond to the matched_rooms.

        These values are derived from the data_collections but they will be
        averaged/totaled and normalized by Room floor area depending on the
        other inputs to this object.
        """
        if self._simulation_step is not None:  # specific index from all collections
            if self._base_type.normalized_type is None or not self._normalize_by_floor:
                return tuple(obj[1][self._simulation_step] for obj in
                             self._matched_objects)
            else:  # normalize the data by the floor area
                vals = []
                for obj, f_area in zip(self._matched_objects, self.matched_floor_areas):
                    try:
                        vals.append(obj[1][self._simulation_step] / (f_area * obj[2]))
                    except ZeroDivisionError:  # no floor faces in the Room
                        vals.append(0)
                return vals
        else:  # average or total the data based on data type
            if self._base_type.normalized_type is None or not self._normalize_by_floor:
                if self._base_type.cumulative:
                    return tuple(obj[1].total for obj in self._matched_objects)
                else:
                    return tuple(obj[1].average for obj in self._matched_objects)
            else:  # normalize the data by floor area
                vals = []
                if self._base_type.cumulative:  # divide total values by floor area
                    for obj, f_area in zip(self._matched_objects, self.matched_floor_areas):
                        try:
                            vals.append(obj[1].total / (f_area * obj[2]))
                        except ZeroDivisionError:  # no floor faces in the Room
                            vals.append(0)
                else:  # divide average values by floor area
                    for obj, f_area in zip(self._matched_objects, self.matched_floor_areas):
                        try:
                            vals.append(obj[1].average / f_area)
                        except ZeroDivisionError:  # no floor faces in the Room
                            vals.append(0)
                return vals

    @property
    def matched_floor_faces(self):
        """Get a nested array with each sub-array having all floor Face3Ds of each room.
        """
        flr_faces = []
        for room in self.matched_rooms:
            flr_faces.append(
                [face.geometry for face in room.faces if isinstance(face.type, Floor)])
        return flr_faces

    @property
    def matched_floor_areas(self):
        """Get a list for all of the room floor faces."""
        return [room.floor_area for room in self.matched_rooms]

    @property
    def graphic_container(self):
        """Get a ladybug GraphicContainer that relates to this object.

        The GraphicContainer possesses almost all things needed to visualize the
        ColorRooms object including the legend, value_colors, lower_title_location,
        upper_title_location, etc.
        """
        return GraphicContainer(
            self.matched_values, self.min_point, self._max_point,
            self.legend_parameters, self.data_type, str(self.unit))

    @property
    def title_text(self):
        """Text string for the title of the color zones."""
        d_type_text = self.data_type_text
        if self._simulation_step is not None:  # specific index from all collections
            time_text = self.time_interval_text(self.simulation_step)
            if self._base_type.normalized_type is not None and self._normalize_by_floor:
                d_type_text = '{} {}'.format(d_type_text, 'Intensity')
        else:  # average or total the data
            time_text = str(self.analysis_period).split('@')[0]
            if self._base_type.normalized_type is None or not self._normalize_by_floor:
                if not self._base_type.cumulative:
                    d_type_text = '{} {}'.format('Average', d_type_text)
                else:
                    d_type_text = '{} {}'.format('Total', d_type_text)
            else:
                if not self._base_type.cumulative:
                    d_type_text = '{} {} {}'.format('Average', d_type_text, 'Intensity')
                else:
                    d_type_text = '{} {} {}'.format('Total', d_type_text, 'Intensity')
        return '{}\n{}'.format('{} ({})'.format(d_type_text, self.unit), time_text)

    @property
    def data_type_text(self):
        """Text for the data type.

        This will be the full name of the EnergyPlus ouput if the DataCollection
        header meatadata contains a 'type' key. Otherwise, this will be the name
        of the data_type object.
        """
        m_data = self._base_collection.header.metadata
        return m_data['type'] if 'type' in m_data else str(self.data_type)

    @property
    def data_type(self):
        """The data type of this object's data collections."""
        if self._base_type.normalized_type is None or not self._normalize_by_floor:
            return self._base_type
        else:
            return self._base_type.normalized_type()

    @property
    def unit(self):
        """The unit of this object's data collections."""
        if self._base_type.normalized_type is not None and self._normalize_by_floor:
            return '{}/{}2'.format(self._base_unit, self._geo_unit) if '/' not in \
                self._base_unit else '{}-{}2'.format(self._base_unit, self._geo_unit)
        else:
            return self._base_unit

    @property
    def analysis_period(self):
        """The analysis_period of this object's data collections."""
        return self._base_collection.header.analysis_period

    @property
    def min_point(self):
        """Get a Point3D for the minimum of the box around the rooms."""
        return self._min_point

    @property
    def max_point(self):
        """Get a Point3D for the maximum of the box around the rooms."""
        return self._max_point

    def time_interval_text(self, simulation_step):
        """Get text for a specific time simulation_step of the data collections.

        Args:
            simulation_step: An integer for the step of simulation for which
                text should be generated.
        """
        hourly_colls = (HourlyContinuousCollection, HourlyDiscontinuousCollection)
        if isinstance(self._base_collection, hourly_colls):
            return str(self._base_collection.datetimes[simulation_step])
        elif isinstance(self._base_collection, MonthlyCollection):
            month_names = AnalysisPeriod.MONTHNAMES
            return month_names[self._base_collection.datetimes[simulation_step]]
        elif isinstance(self._base_collection, DailyCollection):
            return str(Date.from_doy(self._base_collection.datetimes[simulation_step]))
        elif isinstance(self._base_collection, MonthlyPerHourCollection):
            dt_tuple = self._base_collection.datetimes[simulation_step]
            date_time = DateTime(month=dt_tuple[0], hour=dt_tuple[1])
            return date_time.strftime('%b %H:%M')

    def _calculate_min_max(self):
        """Calculate maximum and minimum Point3D for a set of rooms."""
        st_rm_min, st_rm_max = self._rooms[0].geometry.min, self._rooms[0].geometry.max
        min_pt = [st_rm_min.x, st_rm_min.y, st_rm_min.z]
        max_pt = [st_rm_max.x, st_rm_max.y, st_rm_max.z]

        for room in self._rooms[1:]:
            rm_min, rm_max = room.geometry.min, room.geometry.max
            if rm_min.x < min_pt[0]:
                min_pt[0] = rm_min.x
            if rm_min.y < min_pt[1]:
                min_pt[1] = rm_min.y
            if rm_min.z < min_pt[2]:
                min_pt[2] = rm_min.z
            if rm_max.x > max_pt[0]:
                max_pt[0] = rm_max.x
            if rm_max.y > max_pt[1]:
                max_pt[1] = rm_max.y
            if rm_max.z > max_pt[2]:
                max_pt[2] = rm_max.z

        self._min_point = Point3D(min_pt[0], min_pt[1], min_pt[2])
        self._max_point = Point3D(max_pt[0], max_pt[1], max_pt[2])

    def _match_rooms_to_data(self):
        """Match the object's rooms to the data_collections."""
        self._matched_objects = []  # list of matched rooms and data collections

        # extract the zone name from each of the data collections
        zone_names = []
        use_mult = False
        for data in self._data_collections:
            if 'Zone' in data.header.metadata:
                zone_names.append(data.header.metadata['Zone'])
            else:  # it's HVAC system data and we need to see if it's matchable
                hvac_name = data.header.metadata['System']
                use_mult = True
                if '_IDEALAIR' in hvac_name:
                    zone_names.append(hvac_name.split('_IDEALAIR')[0])
                elif ' IDEAL LOADS AIR SYSTEM' in hvac_name:
                    zone_names.append(hvac_name.split(' IDEAL LOADS AIR SYSTEM')[0])
                else:
                    zone_names.append(hvac_name)

        # loop through the rooms and match the data to them
        for room in self._rooms:
            rm_name = room.name.upper()
            for i, data_name in enumerate(zone_names):
                if data_name == rm_name:
                    mult = 1 if not use_mult else room.multiplier
                    self._matched_objects.append((room, self._data_collections[i], mult))
                    break

    def __repr__(self):
        """Color Room representation."""
        return 'Color Room:\n{} Rooms\n{}'.format(
            len(self.rooms), self._base_collection.header)
