# coding=utf-8
"""Module for constructing thermal load balances from energy result data collections."""
from __future__ import division

from .match import match_rooms_to_data, match_faces_to_data

from honeybee.model import Model as hb_model
from honeybee.aperture import Aperture
from honeybee.door import Door
from honeybee.facetype import Wall, RoofCeiling, Floor
from honeybee.boundarycondition import Surface, Adiabatic
from honeybee.typing import float_positive

from ladybug.sql import SQLiteResult
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.header import Header
from ladybug.datatype.energyintensity import EnergyIntensity


class LoadBalance(object):
    """Object for constructing thermal load balances from energy results.

    Args:
        rooms: An array of honeybee Rooms, which will be matched to the input
            data collections and used to determine which heat flow values are
            through outdoor surfaces. The length of these Rooms does not have
            to match the data collections and this object will only construct a
            load balance for rooms that are found to be matching.
        cooling_data: Array of data collections for 'Zone Ideal Loads Supply Air Total
            Cooling Energy' that correspond to the input rooms.
        heating_data: Array of data collections for 'Zone Ideal Loads Supply Air Total
            Heating Energy' that correspond to the input rooms.
        lighting_data: Array of data collections for 'Zone Lights Total Heating
            Energy' that correspond to the input rooms.
        electric_equip_data: Array of data collections for 'Zone Electric Equipment
            Total Heating Energy' that correspond to the input rooms.
        gas_equip_data: Array of data collections for 'Zone Gas Equipment Total
            Heating Energy' that correspond to the input rooms.
        process_data: Array of data collections for 'Zone Other Equipment Total
            Heating Energy' that correspond to the input rooms.
        service_hot_water_data: Array of data collections for 'Water Use Equipment
            Zone Heat Gain Energy' that correspond to the input rooms.
        people_data: Array of data collections for 'Zone People Total Heating
            Energy' that correspond to the input rooms.
        solar_data: Array of data collections for 'Zone Windows Total Transmitted
            Solar Radiation Energy' that correspond to the input rooms.
        infiltration_data: The infiltration heat loss (negative) or heat gain (positive),
            which can be obtained by subtracting 'Zone Infiltration Total Heat
            Loss Energy' data collections from 'Zone Infiltration Total Heat
            Gain Energy' data collections.
        mech_ventilation_data: The ventilation heat loss (negative) or heat gain
            (positive) as a result of meeting minimum outdoor air requirements
            with the mechanical system. This can be obtained by first subtracting
            'Zone Ideal Loads Zone Total Energy' from 'Zone Ideal Loads Supply
            Air Total Energy' for both heating and cooling loads. Then the
            resulting heating load (ventilation loss) should be subtracted
            from the cooling load (ventilation gain).
        nat_ventilation_data: The natural ventilation heat loss (negative) or
            heat gain (positive) which can be obtained by subtracting 'Zone
            Ventilation Total Heat Loss Energy' data collections from 'Zone
            Ventilation Total Heat Gain Energy' data collections.
        surface_flow_data: The surface heat loss (negative) or heat gain (positive),
            which can be obtained for opaque surfaces with a 'Surface Average Face
            Conduction Heat Transfer Energy' data collection. For fenestration
            surfaces, it can be obtained by by subtracting 'Surface Window Heat
            Loss Energy' data collections from 'Surface Window Heat Gain Energy'
            data collections.
        units: Text for the units system in which the room geometry exists.
            Choose from the following:

            * Meters
            * Millimeters
            * Feet
            * Inches
            * Centimeters

        use_all_solar: Boolean to note whether all of the solar_data should be used in
            the resulting load balance, regardless of whether it has been matched to
            the rooms. This is useful for the case that air boundaries exist in a model
            and solar data is reported for grouped zones. (Default: False).

    Properties:
        * rooms
        * floor_area
        * cooling
        * heating
        * lighting
        * electric_equip
        * gas_equip
        * process
        * service_hot_water
        * people
        * solar
        * infiltration
        * mech_ventilation
        * nat_ventilation
        * conduction
        * window_conduction
        * opaque_conduction
        * wall_conduction
        * roof_conduction
        * floor_conduction
        * storage
        * units
    """
    __slots__ = \
        ('_rooms', '_floor_area', '_units', '_cooling', '_heating', '_lighting',
         '_electric_equip', '_gas_equip', '_process', '_service_hot_water', '_people',
         '_solar', '_infiltration', '_mech_ventilation', '_nat_ventilation',
         '_conduction', '_window_conduction', '_opaque_conduction',
         '_wall_conduction', '_roof_conduction', '_floor_conduction', '_storage')

    UNITS = hb_model.UNITS

    # List of all EnergyPlus output strings relevant for thermal load balances
    COOLING = (
        'Zone Ideal Loads Supply Air Total Cooling Energy',
        'Zone Ideal Loads Supply Air Sensible Cooling Energy',
        'Zone Ideal Loads Supply Air Latent Cooling Energy')
    HEATING = (
        'Zone Ideal Loads Supply Air Total Heating Energy',
        'Zone Ideal Loads Supply Air Sensible Heating Energy',
        'Zone Ideal Loads Supply Air Latent Heating Energy')
    LIGHTING = (
        'Zone Lights Electricity Energy',
        'Zone Lights Total Heating Energy')
    ELECTRIC_EQUIP = (
        'Zone Electric Equipment Electricity Energy',
        'Zone Electric Equipment Total Heating Energy',
        'Zone Electric Equipment Radiant Heating Energy',
        'Zone Electric Equipment Convective Heating Energy',
        'Zone Electric Equipment Latent Gain Energy')
    GAS_EQUIP = (
        'Zone Gas Equipment NaturalGas Energy',
        'Zone Gas Equipment Total Heating Energy',
        'Zone Gas Equipment Radiant Heating Energy',
        'Zone Gas Equipment Convective Heating Energy',
        'Zone Gas Equipment Latent Gain Energy')
    PROCESS = (
        'Zone Other Equipment Total Heating Energy',
        'Zone Other Equipment Convective Heating Energy',
        'Zone Other Equipment Radiant Heating Energy',
        'Zone Other Equipment Latent Heating Energy')
    HOT_WATER = (
        'Water Use Equipment Zone Sensible Heat Gain Energy',
        'Water Use Equipment Zone Latent Gain Energy')
    PEOPLE_GAIN = (
        'Zone People Total Heating Energy',
        'Zone People Sensible Heating Energy',
        'Zone People Latent Gain Energy')
    SOLAR_GAIN = 'Zone Windows Total Transmitted Solar Radiation Energy'
    INFIL_GAIN = (
        'Zone Infiltration Total Heat Gain Energy',
        'Zone Infiltration Sensible Heat Gain Energy',
        'Zone Infiltration Latent Heat Gain Energy',
        'AFN Zone Infiltration Sensible Heat Gain Energy',
        'AFN Zone Infiltration Latent Heat Gain Energy')
    INFIL_LOSS = (
        'Zone Infiltration Total Heat Loss Energy',
        'Zone Infiltration Sensible Heat Loss Energy',
        'Zone Infiltration Latent Heat Loss Energy',
        'AFN Zone Infiltration Sensible Heat Loss Energy',
        'AFN Zone Infiltration Latent Heat Loss Energy')
    VENT_LOSS = (
        'Zone Ideal Loads Zone Total Heating Energy',
        'Zone Ideal Loads Zone Sensible Heating Energy',
        'Zone Ideal Loads Zone Latent Heating Energy')
    VENT_GAIN = (
        'Zone Ideal Loads Zone Total Cooling Energy',
        'Zone Ideal Loads Zone Sensible Cooling Energy',
        'Zone Ideal Loads Zone Latent Cooling Energy')
    NAT_VENT_GAIN = (
        'Zone Ventilation Total Heat Gain Energy',
        'Zone Ventilation Sensible Heat Gain Energy',
        'Zone Ventilation Latent Heat Gain Energy',
        'AFN Zone Ventilation Sensible Heat Gain Energy',
        'AFN Zone Ventilation Latent Heat Gain Energy')
    NAT_VENT_LOSS = (
        'Zone Ventilation Total Heat Loss Energy',
        'Zone Ventilation Sensible Heat Loss Energy',
        'Zone Ventilation Latent Heat Loss Energy',
        'AFN Zone Ventilation Sensible Heat Loss Energy',
        'AFN Zone Ventilation Latent Heat Loss Energy')
    OPAQUE_ENERGY_FLOW = 'Surface Average Face Conduction Heat Transfer Energy'
    WINDOW_LOSS = 'Surface Window Heat Loss Energy'
    WINDOW_GAIN = 'Surface Window Heat Gain Energy'

    def __init__(self, rooms, cooling_data=None, heating_data=None, lighting_data=None,
                 electric_equip_data=None, gas_equip_data=None, process_data=None,
                 service_hot_water_data=None, people_data=None,
                 solar_data=None, infiltration_data=None, mech_ventilation_data=None,
                 nat_ventilation_data=None, surface_flow_data=None, units='Meters',
                 use_all_solar=False):
        """Initialize LoadBalance."""
        # Set defaults for values that are computed upon request
        self._conduction = None
        self._window_conduction = None
        self._opaque_conduction = None
        self._storage = None
        self.units = units
        self._floor_area = None

        # match all of the room-level inputs
        self._cooling = self._match_room_input(
            cooling_data, rooms, 'Cooling', negate=True)
        self._heating = self._match_room_input(
            heating_data, rooms, 'Heating')
        self._lighting = self._match_room_input(
            lighting_data, rooms, 'Lighting', 'Lights')
        self._electric_equip = self._match_room_input(
            electric_equip_data, rooms, 'Electric Equipment', mult_per_room=True)
        self._gas_equip = self._match_room_input(
            gas_equip_data, rooms, 'Gas Equipment', mult_per_room=True)
        self._process = self._match_room_input(
            process_data, rooms, 'Process Equipment', 'Other Equipment',
            mult_per_room=True)
        self._service_hot_water = self._match_room_input(
            service_hot_water_data, rooms, 'Service Hot Water',
            'Water Use Equipment Zone', mult_per_room=True)
        self._people = self._match_room_input(
            people_data, rooms, 'People')
        self._solar = self._match_room_input(
            solar_data, rooms, 'Solar', use_all=use_all_solar)
        self._infiltration = self._match_room_input(
            infiltration_data, rooms, 'Infiltration')
        self._mech_ventilation = self._match_room_input(
            mech_ventilation_data, rooms, 'Mechanical Ventilation', 'Ventilation')
        self._nat_ventilation = self._match_room_input(
            nat_ventilation_data, rooms, 'Natural Ventilation', 'Ventilation')

        # match the surface-level inputs
        _window_flow, self._wall_conduction, self._roof_conduction, \
            self._floor_conduction = self._match_face_input(surface_flow_data, rooms)
        if _window_flow is not None and self._solar is not None:
            # compute just the conduction loss/gain from the windows
            self._window_conduction = _window_flow - self._solar
            self._window_conduction.header.metadata['type'] = 'Window Conduction'

    @classmethod
    def from_sql_file(cls, model, sql_path):
        """Create a LoadBalance object from an EnergyPlus SQLite result file.

    Args:
        model: A honeybee Model, which will have its rooms matched to the input
            data collections and used to determine which heat flow values are
            through outdoor surfaces.
        sql_path: Full path to an SQLite file that was generated by EnergyPlus.
            this file should have the relevant load balance outputs in the
            ReportData table.
    """
        # create the SQL result parsing object
        sql_obj = SQLiteResult(sql_path)

        # get all of the results relevant for gains and losses
        cooling = sql_obj.data_collections_by_output_name(cls.COOLING)
        heating = sql_obj.data_collections_by_output_name(cls.HEATING)
        lighting = sql_obj.data_collections_by_output_name(cls.LIGHTING)
        people_gain = sql_obj.data_collections_by_output_name(cls.PEOPLE_GAIN)
        solar_gain = sql_obj.data_collections_by_output_name(cls.SOLAR_GAIN)
        infil_gain = sql_obj.data_collections_by_output_name(cls.INFIL_GAIN)
        infil_loss = sql_obj.data_collections_by_output_name(cls.INFIL_LOSS)
        vent_loss = sql_obj.data_collections_by_output_name(cls.VENT_LOSS)
        vent_gain = sql_obj.data_collections_by_output_name(cls.VENT_GAIN)
        nat_vent_gain = sql_obj.data_collections_by_output_name(cls.NAT_VENT_GAIN)
        nat_vent_loss = sql_obj.data_collections_by_output_name(cls.NAT_VENT_LOSS)

        # handle the case that both total elect/gas energy and zone gain are requested
        electric_equip = sql_obj.data_collections_by_output_name(cls.ELECTRIC_EQUIP[1])
        if len(electric_equip) == 0:
            electric_equip = sql_obj.data_collections_by_output_name(cls.ELECTRIC_EQUIP)
        gas_equip = sql_obj.data_collections_by_output_name(cls.GAS_EQUIP[1])
        if len(gas_equip) == 0:
            gas_equip = sql_obj.data_collections_by_output_name(cls.GAS_EQUIP)
        process = sql_obj.data_collections_by_output_name(cls.PROCESS)
        how_water = sql_obj.data_collections_by_output_name(cls.HOT_WATER[1])
        if len(how_water) == 0:
            how_water = sql_obj.data_collections_by_output_name(cls.HOT_WATER)

        # subtract losses from gains
        infiltration = None
        mech_vent = None
        nat_vent = None
        if len(infil_gain) == len(infil_loss):
            infiltration = cls.subtract_loss_from_gain(infil_gain, infil_loss)
        if len(vent_gain) == len(vent_loss) == len(cooling) == len(heating):
            mech_vent = cls.mech_vent_loss_gain(vent_gain, vent_loss, cooling, heating)
        if len(nat_vent_gain) == len(nat_vent_loss):
            nat_vent = cls.subtract_loss_from_gain(nat_vent_gain, nat_vent_loss)

        # get the surface energy flow
        opaque_flow = sql_obj.data_collections_by_output_name(cls.OPAQUE_ENERGY_FLOW)
        window_loss = sql_obj.data_collections_by_output_name(cls.WINDOW_LOSS)
        window_gain = sql_obj.data_collections_by_output_name(cls.WINDOW_GAIN)
        window_flow = []
        if len(window_gain) == len(window_loss):
            window_flow = cls.subtract_loss_from_gain(window_gain, window_loss)
        face_energy_flow = opaque_flow + window_flow

        bal_obj = cls(
            model.rooms, cooling, heating, lighting, electric_equip, gas_equip, process,
            how_water, people_gain, solar_gain, infiltration, mech_vent, nat_vent,
            face_energy_flow, model.units, use_all_solar=True)
        bal_obj.floor_area = bal_obj._area_as_meters_feet(model.floor_area)
        return bal_obj

    @property
    def rooms(self):
        """Get the Rooms that have been successfully matched to the input data."""
        return self._rooms

    @property
    def cooling(self):
        """Get a data collection for the cooling of the load balance."""
        return self._cooling

    @property
    def heating(self):
        """Get a data collection for the heating of the load balance."""
        return self._heating

    @property
    def lighting(self):
        """Get a data collection for the lighting gain of the load balance."""
        return self._lighting

    @property
    def electric_equip(self):
        """Get a data collection for the electric equipment gain of the load balance."""
        return self._electric_equip

    @property
    def gas_equip(self):
        """Get a data collection for the gas equipment gain of the load balance."""
        return self._gas_equip

    @property
    def process(self):
        """Get a data collection for the process load gain of the load balance."""
        return self._process

    @property
    def service_hot_water(self):
        """Get a data collection for the service hot water gain of the load balance."""
        return self._service_hot_water

    @property
    def people(self):
        """Get a data collection for the people gain of the load balance."""
        return self._people

    @property
    def solar(self):
        """Get a data collection for the solar gain of the load balance."""
        return self._solar

    @property
    def infiltration(self):
        """Get a data collection for the infiltration gain/loss of the load balance."""
        return self._infiltration

    @property
    def mech_ventilation(self):
        """Get a data collection for the mechanical ventilation of the load balance."""
        return self._mech_ventilation

    @property
    def nat_ventilation(self):
        """Get a data collection for the natural ventilation of the load balance."""
        return self._nat_ventilation

    @property
    def conduction(self):
        """Get a data collection for all conduction loss/gain of the load balance."""
        if self._conduction is None:
            if self.window_conduction is not None and self.opaque_conduction is not None:
                self._conduction = self.window_conduction + self.opaque_conduction
                self._conduction.header.metadata['type'] = 'Conduction'
        return self._conduction

    @property
    def window_conduction(self):
        """Get a data collection for window conduction loss/gain of the load balance."""
        return self._window_conduction

    @property
    def opaque_conduction(self):
        """Get a data collection for opaque conduction loss/gain of the load balance."""
        if self._opaque_conduction is None:
            if self.wall_conduction is not None and self.roof_conduction is not None \
                    and self.floor_conduction is not None:
                self._opaque_conduction = self.wall_conduction + \
                    self.roof_conduction + self.floor_conduction
                self._opaque_conduction.header.metadata['type'] = 'Opaque Conduction'
        return self._opaque_conduction

    @property
    def wall_conduction(self):
        """Get a data collection for wall conduction loss/gain of the load balance."""
        return self._wall_conduction

    @property
    def roof_conduction(self):
        """Get a data collection for roof conduction loss/gain of the load balance."""
        return self._roof_conduction

    @property
    def floor_conduction(self):
        """Get a data collection for floor conduction loss/gain of the load balance."""
        return self._floor_conduction

    @property
    def storage(self):
        """Get a data collection for the remainder of the load balance."""
        if self._storage is None:
            other_terms = self.load_balance_terms()
            if len(other_terms) != 0:
                _storage = other_terms[0]
                for coll in other_terms[1:]:
                    _storage = _storage + coll
                self._storage = -_storage.duplicate()  # dup to avoid editing header
                self._storage.header.metadata['type'] = 'Storage'
        return self._storage

    @property
    def units(self):
        """Get or set text for the units system in which the room geometry exists."""
        return self._units

    @units.setter
    def units(self, value):
        assert value in self.UNITS, '{} is not supported as a units system. ' \
            'Choose from the following: {}'.format(value, self.units)
        self._units = value

    @property
    def floor_area(self):
        """Get or set a number for the total floor area in square meters or square feet.

        By default, this is the floor area of only the successfully-matched rooms.

        This floor area accounts for Room multipliers and will always be in either
        square meters or square feet depending on whether this object's units are
        either SI or IP.
        """
        if self._floor_area is not None:
            return self._floor_area
        else:
            base_area = sum([room.floor_area * room.multiplier for room in self._rooms])
            return self._area_as_meters_feet(base_area)

    @floor_area.setter
    def floor_area(self, value):
        self._floor_area = float_positive(value)

    def load_balance_terms(self, floor_normalized=False, include_storage=False):
        """Get a list of data collections with one for each term in the load balance.

        Terms of the load balance that are None will be excluded from this list.
        Conduction terms will only appear as opaque and window conduction terms.

        Args:
            floor_normalized: Boolean to note whether all of the output data
                collections should have values that are normaized by the Room
                floor area.
            include_storage: Boolean to note whether the storage term should
                be included in the list.
        """
        all_terms = [self.heating, self.solar, self.service_hot_water, self.gas_equip,
                     self.process, self.electric_equip, self.lighting, self.people,
                     self.infiltration, self.mech_ventilation, self.nat_ventilation,
                     self.opaque_conduction, self.window_conduction, self.cooling]
        bal_terms = [term for term in all_terms if term is not None and term != []]

        if include_storage:
            bal_terms.append(self.storage)

        if floor_normalized:
            flr_area = self.floor_area
            if flr_area == 0:  # rare case but we don't want a ZeroDivision error
                return bal_terms
            is_ip = True if self.units in ('Feet', 'Inches') else False
            bal_terms = [self._normalize_collection(term, flr_area, is_ip)
                         for term in bal_terms]
        return bal_terms

    @staticmethod
    def subtract_loss_from_gain(load_gain, load_loss):
        """Subtract an array of load loss data collections from load gain collections.

        This is what is needed for certain LoadBalance inputs like infiltration
        and natural ventilation.

        Args:
            load_gain: A list of data collections with load gains.
            load_loss: A list of data collections with load losses.
        """
        total_loads = []
        for gain, loss in zip(load_gain, load_loss):
            total_load = gain - loss
            total_load.header.metadata['type'] = \
                total_load.header.metadata['type'].replace('Gain ', '')
            total_loads.append(total_load)
        return total_loads

    @staticmethod
    def mech_vent_loss_gain(zone_cooling, zone_heating, cooling, heating):
        """Compute mechanical ventilation loss/gain from lists of data collections.

        Args:
            zone_cooling: A list of data collections for zone-level cooling.
            zone_heating: A list of data collections for zone-level heating.
            cooling: A list of data collections for supply air cooling.
            heating: A list of data collections for supply air heating.
        """
        mech_vent_loss = LoadBalance.subtract_loss_from_gain(heating, zone_heating)
        mech_vent_gain = LoadBalance.subtract_loss_from_gain(cooling, zone_cooling)
        total_load = LoadBalance.subtract_loss_from_gain(mech_vent_gain, mech_vent_loss)
        mech_vent_load = [data.duplicate() for data in total_load]
        for load in mech_vent_load:
            load.header.metadata['type'] = \
                'Zone Ideal Loads Ventilation Heat Energy'
        return mech_vent_load

    def _match_room_input(self, data_collections, rooms, data_type,
                          type_check_text=None, negate=False, use_all=False,
                          mult_per_room=False):
        """Match a an array of input data collections to input rooms.

        Args:
            data_collections: An array of input data collections.
            rooms: An array of input honeybee Rooms.
            data_type: Text for the name of the data type for the totalled collection.
            type_check_text: Optional text, which will be used to check if the input
                data_collections are of the right type.
            negate: Boolean to note whether the values should be negated.
            use_all: Boolean to note whether all data_collections should be used instead
                of those matched to the rooms.
            mult_per_room: Boolean to note whether there are multiple data collections
                for each room, which should be summed together.
        """
        # don't match anything if there are no collections
        if data_collections is None or len(data_collections) == 0:
            return None

        # match the data collections to the rooms
        if use_all:  # firs try to see if all objects can be matched
            matched_objs = match_rooms_to_data(data_collections, rooms, True)
            if len(matched_objs) != len(rooms):  # take them all
                matched_objs = [(None, data, rm.multiplier)
                                for data, rm in zip(data_collections, rooms)]
        elif mult_per_room:  # group the collections by their type
            coll_dict = {}
            for coll in data_collections:
                try:
                    coll_dict[coll.header.metadata['type']].append(coll)
                except KeyError:
                    coll_dict[coll.header.metadata['type']] = [coll]
            all_match = [match_rooms_to_data(val, rooms, True)
                         for val in coll_dict.values()]
            matched_objs = [list(tup) for tup in all_match[0]]
            for other_tups in all_match[1:]:
                for i, tup in enumerate(other_tups):
                    matched_objs[i][1] += tup[1]
        else:
            matched_objs = match_rooms_to_data(data_collections, rooms, True)
        assert len(matched_objs) != 0, \
            'None of the data collections could be matched to the input rooms.'
        self._rooms = tuple(obj[0] for obj in matched_objs) if not use_all else rooms
        base_data = matched_objs[0][1]

        # check that the data if of the correct type.
        if 'type' in base_data.header.metadata:
            check_text = type_check_text if type_check_text is not None else data_type
            assert check_text in base_data.header.metadata['type'], \
                'Input data collections for {} do not seem to be of the correct type:' \
                '\n{}'.format(data_type, base_data.header.metadata['type'])

        # compute the total values of the load
        values = [0 for val in range(len(base_data))]
        for obj in matched_objs:
            for i, val in enumerate(obj[1].values):
                values[i] += val * obj[2]
        if negate:
            values = [-val for val in values]

        # create the new totalled data collection
        new_header = base_data.header.duplicate()
        if 'Zone' in new_header.metadata:
            del new_header.metadata['Zone']
        elif 'System' in new_header.metadata:
            del new_header.metadata['System']
        new_header.metadata['type'] = data_type
        if isinstance(base_data, HourlyContinuousCollection):
            return HourlyContinuousCollection(new_header, values)
        else:  # it's one of the data collections that needs datetimes
            return base_data.__class__(new_header, values, base_data.datetimes)

    def _match_face_input(self, surface_flow_data, rooms):
        """Match a an array of input data collections to input rooms.

        Args:
            surface_flow_data: An array of input data collections for surface
                energy flow.
            rooms: An array of input honeybee Rooms.
        """
        # match the data collections to the rooms
        if surface_flow_data is None or len(surface_flow_data) == 0:
            return None, None, None, None
        base_data = surface_flow_data[0]
        values = [0 for val in range(len(base_data))]

        # compute the total values of the load
        window_vals, wall_vals, roof_vals, floor_vals = (values[:] for i in range(4))
        for room in rooms:
            mult = room.multiplier
            match_objs = match_faces_to_data(surface_flow_data, room.faces)
            for obj in match_objs:
                if not isinstance(obj[0].boundary_condition, (Surface, Adiabatic)):
                    if isinstance(obj[0], (Aperture, Door)):
                        for i, val in enumerate(obj[1].values):
                            window_vals[i] += val * mult
                    elif isinstance(obj[0].type, Wall):
                        for i, val in enumerate(obj[1].values):
                            wall_vals[i] += val * mult
                    elif isinstance(obj[0].type, RoofCeiling):
                        for i, val in enumerate(obj[1].values):
                            roof_vals[i] += val * mult
                    elif isinstance(obj[0].type, Floor):
                        for i, val in enumerate(obj[1].values):
                            floor_vals[i] += val * mult

        # create the new totalled data collection
        new_header = base_data.header.duplicate()
        if 'Surface' in new_header.metadata:
            del new_header.metadata['Surface']
        window_head, wall_head, roof_head, floor_head = \
            (new_header.duplicate() for i in range(4))
        window_head.metadata['type'] = 'Window Energy Flow'
        wall_head.metadata['type'] = 'Wall Conduction'
        roof_head.metadata['type'] = 'Roof Conduction'
        floor_head.metadata['type'] = 'Floor Conduction'
        all_headers = [window_head, wall_head, roof_head, floor_head]
        all_values = [window_vals, wall_vals, roof_vals, floor_vals]
        all_data = []
        for head, vals in zip(all_headers, all_values):
            if isinstance(base_data, HourlyContinuousCollection):
                all_data.append(HourlyContinuousCollection(head, vals))
            else:  # it's one of the data collections that needs datetimes
                all_data.append(base_data.__class__(head, vals, base_data.datetimes))
        return all_data

    def _area_as_meters_feet(self, base_area):
        """Convert a base area to meters or feet depending on the the assigned units."""
        if self.units in ('Meters', 'Feet'):  # no need to do unit conversions
            return base_area
        elif self.units == 'Millimeters':  # convert to meters
            return base_area / 1000000.0
        elif self.units == 'Inches':  # convert to feet
            return base_area / 144.0
        else:  # assume it's cm; convert to meters
            return base_area / 10000.0

    @staticmethod
    def _normalize_collection(collection, area, is_ip):
        """Normalize a given data collection by floor area.

        Args:
            collection: A data collection to be normalized.
            area: The floor area the the collection is normalize by.
            is_ip: Boolean to note whether the area is in square meters or square feet.
        """
        new_vals = [val / area for val in collection.values]
        head = collection.header
        new_unit = '{}/m2'.format(head.unit) if not is_ip else '{}/ft2'.format(head.unit)
        new_header = Header(
            EnergyIntensity(), new_unit, head.analysis_period, head.metadata)
        if isinstance(collection, HourlyContinuousCollection):
            return HourlyContinuousCollection(new_header, new_vals)
        else:  # it's one of the data collections that needs datetimes
            return collection.__class__(new_header, new_vals, collection.datetimes)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        """Load Balance representation."""
        return 'Load Balance: [{} Rooms]'.format(len(self.rooms))
