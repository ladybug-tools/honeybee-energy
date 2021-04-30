# coding=utf-8
"""Room Energy Properties."""
# import honeybee-core and ladybug-geometry modules
from ladybug_geometry.geometry2d.pointvector import Vector2D
from ladybug_geometry.geometry3d.pointvector import Point3D
from honeybee.boundarycondition import Outdoors, Surface, boundary_conditions
from honeybee.facetype import Wall, RoofCeiling, Floor, AirBoundary
from honeybee.aperture import Aperture

# import the main types of assignable objects
from ..programtype import ProgramType
from ..constructionset import ConstructionSet
from ..load.people import People
from ..load.lighting import Lighting
from ..load.equipment import ElectricEquipment, GasEquipment
from ..load.hotwater import ServiceHotWater
from ..load.infiltration import Infiltration
from ..load.ventilation import Ventilation
from ..load.setpoint import Setpoint
from ..load.daylight import DaylightingControl
from ..ventcool.control import VentilationControl
from ..ventcool.crack import AFNCrack
from ..ventcool.opening import VentilationOpening
from ..construction.opaque import OpaqueConstruction

# import all hvac modules to ensure they are all re-serialize-able in Room.from_dict
from ..hvac import HVAC_TYPES_DICT
from ..hvac._base import _HVACSystem
from ..hvac.idealair import IdealAirSystem

# import the libraries of constructionsets and programs
from ..lib.constructionsets import generic_construction_set
from ..lib.schedules import always_on
from ..lib.programtypes import plenum_program


class RoomEnergyProperties(object):
    """Energy Properties for Honeybee Room.

    Args:
        host: A honeybee_core Room object that hosts these properties.
        program_type: A honeybee ProgramType object to specify all default
            schedules and loads for the Room. If None, the Room will have a Plenum
            program (with no loads or setpoints). Default: None.
        construction_set: A honeybee ConstructionSet object to specify all
            default constructions for the Faces of the Room. If None, the Room
            will use the honeybee default construction set, which is not
            representative of a particular building code or climate zone.
            Default: None.
        hvac: A honeybee HVAC object (such as an IdealAirSystem) that specifies
            how the Room is conditioned. If None, it will be assumed that the
            Room is not conditioned. Default: None.

    Properties:
        * host
        * program_type
        * construction_set
        * hvac
        * people
        * lighting
        * electric_equipment
        * gas_equipment
        * service_hot_water
        * infiltration
        * ventilation
        * setpoint
        * window_vent_control
        * is_conditioned
    """

    __slots__ = ('_host', '_program_type', '_construction_set', '_hvac',
                 '_people', '_lighting', '_electric_equipment', '_gas_equipment',
                 '_service_hot_water', '_infiltration', '_ventilation', '_setpoint',
                 '_daylighting_control', '_window_vent_control')

    def __init__(self, host, program_type=None, construction_set=None, hvac=None):
        """Initialize Room energy properties."""
        # set the main properties of the Room
        self._host = host
        self.program_type = program_type
        self.construction_set = construction_set
        self.hvac = hvac

        # set the Room's specific properties that override the program_type to None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._service_hot_water = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None
        self._daylighting_control = None
        self._window_vent_control = None

    @property
    def host(self):
        """Get the Room object hosting these properties."""
        return self._host

    @property
    def program_type(self):
        """Get or set the ProgramType object for the Room.

        If not set, it will default to a plenum ProgramType (with no loads assigned).
        """
        if self._program_type is not None:  # set by the user
            return self._program_type
        else:
            return plenum_program

    @program_type.setter
    def program_type(self, value):
        if value is not None:
            assert isinstance(value, ProgramType), \
                'Expected ProgramType for Room program_type. Got {}'.format(type(value))
            value.lock()   # lock in case program type has multiple references
        self._program_type = value

    @property
    def construction_set(self):
        """Get or set the Room ConstructionSet object.

        If not set, it will be the Honeybee default generic ConstructionSet.
        """
        if self._construction_set is not None:  # set by the user
            return self._construction_set
        else:
            return generic_construction_set

    @construction_set.setter
    def construction_set(self, value):
        if value is not None:
            assert isinstance(value, ConstructionSet), \
                'Expected ConstructionSet. Got {}'.format(type(value))
            value.lock()   # lock in case construction set has multiple references
        self._construction_set = value

    @property
    def hvac(self):
        """Get or set the HVAC object for the Room.

        If None, it will be assumed that the Room is not conditioned.
        """
        return self._hvac

    @hvac.setter
    def hvac(self, value):
        if value is not None:
            assert isinstance(value, _HVACSystem), \
                'Expected HVACSystem for Room hvac. Got {}'.format(type(value))
            value.lock()   # lock in case hvac has multiple references
        self._hvac = value

    @property
    def people(self):
        """Get or set a People object to describe the occupancy of the Room."""
        if self._people is not None:  # set by the user
            return self._people
        else:
            return self.program_type.people

    @people.setter
    def people(self, value):
        if value is not None:
            assert isinstance(value, People), \
                'Expected People for Room people. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._people = value

    @property
    def lighting(self):
        """Get or set a Lighting object to describe the lighting usage of the Room."""
        if self._lighting is not None:  # set by the user
            return self._lighting
        else:
            return self.program_type.lighting

    @lighting.setter
    def lighting(self, value):
        if value is not None:
            assert isinstance(value, Lighting), \
                'Expected Lighting for Room lighting. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._lighting = value

    @property
    def electric_equipment(self):
        """Get or set an ElectricEquipment object to describe the equipment usage."""
        if self._electric_equipment is not None:  # set by the user
            return self._electric_equipment
        else:
            return self.program_type.electric_equipment

    @electric_equipment.setter
    def electric_equipment(self, value):
        if value is not None:
            assert isinstance(value, ElectricEquipment), 'Expected ElectricEquipment ' \
                'for Room electric_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._electric_equipment = value

    @property
    def gas_equipment(self):
        """Get or set a GasEquipment object to describe the equipment usage."""
        if self._gas_equipment is not None:  # set by the user
            return self._gas_equipment
        else:
            return self.program_type.gas_equipment

    @gas_equipment.setter
    def gas_equipment(self, value):
        if value is not None:
            assert isinstance(value, GasEquipment), 'Expected GasEquipment ' \
                'for Room gas_equipment. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._gas_equipment = value

    @property
    def service_hot_water(self):
        """Get or set a ServiceHotWater object to describe the hot water usage."""
        if self._service_hot_water is not None:  # set by the user
            return self._service_hot_water
        else:
            return self.program_type.service_hot_water

    @service_hot_water.setter
    def service_hot_water(self, value):
        if value is not None:
            assert isinstance(value, ServiceHotWater), 'Expected ServiceHotWater ' \
                'for Room service_hot_water. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._service_hot_water = value

    @property
    def infiltration(self):
        """Get or set a Infiltration object to to describe the outdoor air leakage."""
        if self._infiltration is not None:  # set by the user
            return self._infiltration
        else:
            return self.program_type.infiltration

    @infiltration.setter
    def infiltration(self, value):
        if value is not None:
            assert isinstance(value, Infiltration), 'Expected Infiltration ' \
                'for Room infiltration. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._infiltration = value

    @property
    def ventilation(self):
        """Get or set a Ventilation object for the minimum outdoor air requirement."""
        if self._ventilation is not None:  # set by the user
            return self._ventilation
        else:
            return self.program_type.ventilation

    @ventilation.setter
    def ventilation(self, value):
        if value is not None:
            assert isinstance(value, Ventilation), 'Expected Ventilation ' \
                'for Room ventilation. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._ventilation = value

    @property
    def setpoint(self):
        """Get or set a Setpoint object for the temperature setpoints of the Room."""
        if self._setpoint is not None:  # set by the user
            return self._setpoint
        else:
            return self.program_type.setpoint

    @setpoint.setter
    def setpoint(self, value):
        if value is not None:
            assert isinstance(value, Setpoint), 'Expected Setpoint ' \
                'for Room setpoint. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._setpoint = value

    @property
    def daylighting_control(self):
        """Get or set a DaylightingControl object to dictate the dimming of lights.

        If None, the lighting will respond only to the schedule and not the
        daylight conditions within the room.
        """
        return self._daylighting_control

    @daylighting_control.setter
    def daylighting_control(self, value):
        if value is not None:
            assert isinstance(value, DaylightingControl), 'Expected DaylightingControl' \
                ' object for Room daylighting_control. Got {}'.format(type(value))
            value._parent = self.host
        self._daylighting_control = value

    @property
    def window_vent_control(self):
        """Get or set a VentilationControl object to dictate the opening of windows.

        If None, the windows will never open.
        """
        return self._window_vent_control

    @window_vent_control.setter
    def window_vent_control(self, value):
        if value is not None:
            assert isinstance(value, VentilationControl), 'Expected VentilationControl' \
                ' object for Room window_vent_control. Got {}'.format(type(value))
            value.lock()   # lock because we don't duplicate the object
        self._window_vent_control = value

    @property
    def is_conditioned(self):
        """Boolean to note whether the Room is conditioned."""
        return self._hvac is not None

    def abolute_people(self, person_count, conversion=1):
        """Set the abolute number of people in the Room.

        This overwrites the RoomEnergyProperties's people per area but preserves
        all schedules and other people properties. If the Room has no people definition,
        a new one with an Always On schedule will be created. Note that, if the
        host Room has no floors, the people load will be zero.

        Args:
            person_count: Number for the maximum quantity of people in the room.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        people = self._dup_load('people', People)
        self._absolute_by_floor(people, 'people_per_area', person_count, conversion)
        self.people = people

    def abolute_lighting(self, watts, conversion=1):
        """Set the abolute wattage of lighting in the Room.

        This overwrites the RoomEnergyProperties's lighting per area but preserves all
        schedules and other lighting properties. If the Room has no lighting definition,
        a new one with an Always On schedule will be created. Note that, if the
        host Room has no floors, the lighting load will be zero.

        Args:
            watts: Number for the installed wattage of lighting in the room.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        lighting = self._dup_load('lighting', Lighting)
        self._absolute_by_floor(lighting, 'watts_per_area', watts, conversion)
        self.lighting = lighting

    def abolute_electric_equipment(self, watts, conversion=1):
        """Set the abolute wattage of electric equipment in the Room.

        This overwrites the RoomEnergyProperties's electric equipment per area but
        preserves all schedules and other properties. If the Room has no electric
        equipment definition, a new one with an Always On schedule will be created.
        Note that, if the host Room has no floors, the electric equipment load
        will be zero.

        Args:
            watts: Number for the installed wattage of electric equipment in the room.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        elect_equip = self._dup_load('electric_equipment', ElectricEquipment)
        self._absolute_by_floor(elect_equip, 'watts_per_area', watts, conversion)
        self.electric_equipment = elect_equip

    def abolute_gas_equipment(self, watts, conversion=1):
        """Set the abolute wattage of gas equipment in the Room.

        This overwrites the RoomEnergyProperties's gas equipment per area but
        preserves all schedules and other properties. If the Room has no gas
        equipment definition, a new one with an Always On schedule will be created.
        Note that, if the host Room has no floors, the gas equipment load
        will be zero.

        Args:
            watts: Number for the installed wattage of gas equipment in the room.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        gas_equipment = self._dup_load('gas_equipment', GasEquipment)
        self._absolute_by_floor(gas_equipment, 'watts_per_area', watts, conversion)
        self.gas_equipment = gas_equipment

    def abolute_service_hot_water(self, flow, conversion=1):
        """Set the abolute flow rate of service hot water use in the Room.

        This overwrites the RoomEnergyProperties's hot water flow per area but
        preserves all schedules and other properties. If the Room has no service
        hot water definition, a new one with an Always On schedule will be created.
        Note that, if the host Room has no floors, the service hot water flow
        will be zero.

        Args:
            flow: Number for the peak flow rate of service hot water in the room.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        shw = self._dup_load('service_hot_water', ServiceHotWater)
        self._absolute_by_floor(shw, 'flow_per_area', flow, conversion)
        self.service_hot_water = shw

    def abolute_infiltration(self, flow_rate, conversion=1):
        """Set the abolute flow rate of infiltration for the Room in m3/s.

        This overwrites the RoomEnergyProperties's infiltration flow per exterior area
        but preserves all schedules and other properties. If the Room has no
        infiltration definition, a new one with an Always On schedule will be created.
        Note that, if the host Room has no exterior faces, the infiltration load
        will be zero.

        Args:
            flow_rate: Number for the infiltration flow rate in m3/s.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        infiltration = self._dup_load('infiltration', Infiltration)
        try:
            ext_area = self.host.exposed_area * conversion ** 2
            infiltration.flow_per_exterior_area = flow_rate / ext_area
        except ZeroDivisionError:
            pass  # no exposed area; just leave the load level as is
        self.infiltration = infiltration

    def abolute_infiltration_ach(self, air_changes_per_hour, conversion=1):
        """Set the abolute flow rate of infiltration for the Room in ACH.

        This overwrites the RoomEnergyProperties's infiltration flow per exterior area
        but preserves all schedules and other properties. If the Room has no
        infiltration definition, a new one with an Always On schedule will be created.
        Note that, if the host Room has no exterior faces, the infiltration load
        will be zero.

        Args:
            air_changes_per_hour: Number for the infiltration flow rate in ACH.
            conversion: Factor to account for the case where host Room geometry is
                not in meters. This will be multiplied by the floor area so it should
                be 0.001 for millimeters, 0.305 for feet, etc. (Default: 1).
        """
        room_vol = self.host.volume * conversion ** 3
        self.abolute_infiltration((air_changes_per_hour * room_vol) / 3600., conversion)

    def remove_child_constructions(self):
        """Remove constructions assigned to the Room's Faces, Apertures, Doors and Shades.

        This means that all constructions of the Room will be assigned by the Room's
        construction_set (or the Honeybee default ConstructionSet if the Room has
        no construction set).
        """
        for shade in self.host.shades:
            shade.properties.energy.construction = None
        for face in self.host.faces:
            face.properties.energy.construction = None
            for shade in face.shades:
                shade.properties.energy.construction = None
            for ap in face._apertures:
                ap.properties.energy.construction = None
                for shade in ap.shades:
                    shade.properties.energy.construction = None
            for dr in face._doors:
                dr.properties.energy.construction = None
                for shade in dr.shades:
                    shade.properties.energy.construction = None

    def window_construction_by_orientation(
            self, construction, orientation=0, offset=45, north_vector=Vector2D(0, 1)):
        """Set the construction of exterior Apertures in Walls facing a given orientation.

        This is useful for testing orientation-specific energy conservation
        strategies or creating AHSRAE baseline buildings.

        Args:
            construction: A WindowConstruction that will be assigned to all of the
                room's Apertures in Walls that are facing a certain orientation.
            orientation: A number between 0 and 360 that represents the orientation
                in degrees to which the construction will be assigned. 0 = North,
                90 = East, 180 = South, 270 = West. (Default: 0 for North).
            offset: A number between 0 and 180 that represents the offset from the
                orientation in degrees for which the construction will be assigned.
                For example, a value of 45 indicates that any Apertures falling
                in the 90 degree range around the orientation will get the input
                construction. (Default: 45).
            north_vector: A ladybug_geometry Vector3D for the north direction.
                Default is the Y-axis (0, 1).
        """
        # determine the min and max values for orientation
        ori_min = orientation - offset
        ori_max = orientation + offset
        ori_min = ori_min + 360 if ori_min < 0 else ori_min
        ori_max = ori_max - 360 if ori_max > 360 else ori_max
        rev_vars = True if ori_min > ori_max else False

        # loop through the faces an determine if they meet the criteria
        for face in self.host.faces:
            if isinstance(face.boundary_condition, Outdoors) and \
                    isinstance(face.type, Wall) and len(face._apertures) > 0:
                if rev_vars:
                    if face.horizontal_orientation(north_vector) > ori_min \
                            or face.horizontal_orientation(north_vector) < ori_max:
                        for ap in face._apertures:
                            ap.properties.energy.construction = construction
                else:
                    if ori_min < face.horizontal_orientation(north_vector) < ori_max:
                        for ap in face._apertures:
                            ap.properties.energy.construction = construction

    def add_default_ideal_air(self):
        """Add a default IdealAirSystem to this Room.

        The identifier of this system will be derived from the room identifier
        and will align with the naming convention that EnergyPlus uses for
        templates Ideal Air systems.
        """
        hvac_id = '{} Ideal Loads Air System'.format(self.host.identifier)
        self.hvac = IdealAirSystem(hvac_id)

    def add_daylight_control_to_center(
            self, distance_from_floor, illuminance_setpoint=300, control_fraction=1,
            min_power_input=0.3, min_light_output=0.2, off_at_minimum=False):
        """Try to assign a DaylightingControl object to the center of the Room.

        If the Room is too concave and the center point does not lie within the
        Room volume, this method wil return None and no daylighting control will
        be assigned.

        Args:
            distance_from_floor: A number for the distance that the daylight sensor
                is from the floor. Typical values are around 0.8 meters.
            illuminance_setpoint: A number for the illuminance setpoint in lux
                beyond which electric lights are dimmed if there is sufficient
                daylight. (Default: 300 lux).
            control_fraction: A number between 0 and 1 that represents the fraction of
                the Room lights that are dimmed when the illuminance at the sensor
                position is at the specified illuminance. 1 indicates that all lights are
                dim-able while 0 indicates that no lights are dim-able. Deeper rooms
                should have lower control fractions to account for the face that the
                lights in the back of the space do not dim in response to suitable
                daylight at the front of the room. (Default: 1).
            min_power_input: A number between 0 and 1 for the the lowest power the
                lighting system can dim down to, expressed as a fraction of maximum
                input power. (Default: 0.3).
            min_light_output: A number between 0 and 1 the lowest lighting output the
                lighting system can dim down to, expressed as a fraction of maximum
                light output. (Default: 0.2).
            off_at_minimum: Boolean to note whether lights should switch off completely
                when they get to the minimum power input. (Default: False).

        Returns:
            A DaylightingControl object if the sensor was successfully assigned
            to the center of the Room. Will be None if the zone was so concave
            that a sensor would not be assigned.
        """
        cen_pt, min_pt = self.host.geometry.center, self.host.geometry.min
        sensor_pt = Point3D(cen_pt.x, cen_pt.y, min_pt.z + distance_from_floor)
        if self.host.geometry.is_point_inside(sensor_pt):
            dl_control = DaylightingControl(
                sensor_pt, illuminance_setpoint, control_fraction,
                min_power_input, min_light_output, off_at_minimum)
            self.daylighting_control = dl_control
            return dl_control

    def assign_ventilation_opening(self, vent_opening):
        """Assign a VentilationOpening object to all operable Apertures on this Room.

        This method will handle the duplication of the VentilationOpening object to
        ensure that each aperture gets a unique object that can export the correct
        area and height properties of its parent.

        Args:
            vent_opening: A VentilationOpening object to be duplicated and assigned
                to all of the operable apertures of the Room.

        Returns:
            A list of Apertures for which ventilation opening properties were set.
            This can be used to perform additional operations on the apertures, such
            as changing their construction.
        """
        operable_aps = []
        for face in self.host.faces:
            for ap in face.apertures:
                if ap.is_operable:
                    ap.properties.energy.vent_opening = vent_opening.duplicate()
                    operable_aps.append(ap)
        return operable_aps

    def remove_ventilation_opening(self):
        """Remove all VentilationOpening objects assigned to the Room's Apertures."""
        for face in self.host.faces:
            for ap in face.apertures:
                ap.properties.energy.vent_opening = None

    def exterior_afn_from_infiltration_load(self, exterior_face_groups,
                                            air_density=1.2041, delta_pressure=4):
        """Assign AirflowNetwork parameters using the room's infiltration rate.

        This will assign air leakage parameters to the Room's exterior Faces that
        produce a total air flow rate equivalent to the room infiltration rate at
        an envelope pressure difference of 4 Pa. However, the individual flow air
        leakage parameters are not meant to be representative of real values, since the
        infiltration flow rate is an average of the actual, variable surface flow
        dynamics.

        VentilationOpening objects will be added to Aperture and Door objects if not
        already defined, with the fraction_area_operable set to 0. If VentilationOpening
        objects are already defined, only the parameters defining leakage when the
        openings are closed will be overwritten. AFNCrack objects will be added
        to all external and internal Face objects, and any existing AFNCrack
        objects will be overwritten.

        Args:
            exterior_face_groups: A tuple with five types of the exterior room envelope

                -   ext_walls - A list of exterior Wall type Face objects.

                -   ext_roofs - A list of exterior RoofCeiling type Face objects.

                -   ext_floors - A list of exterior Floor type Face objects, like you
                    would find in a cantilevered Room.

                -   ext_apertures - A list of exterior Aperture Face objects.

                -   ext_doors - A list of exterior Door Face objects.

            air_density: Air density in kg/m3. (Default: 1.2041 represents
                air density at a temperature of 20 C and 101325 Pa).
            delta_pressure: Reference air pressure difference across the building
                envelope orifice in Pascals used to calculate infiltration crack flow
                coefficients. The resulting average simulated air pressure difference
                will roughly equal this delta_pressure times the nth root of the ratio
                between the simulated and target room infiltration rates::

                    dP_sim = (Q_sim / Q_target)^(1/n) * dP_ref

                    where:
                        dP: delta_pressure, the reference air pressure difference [Pa]
                        dP_sim: Simulated air pressure difference [Pa]
                        Q_sim: Simulated volumetric air flow rate per area [m3/s/m2]
                        Q_target: Target volumetric air flow rate per area [m3/s/m2]
                        n: Air mass flow exponent [-]

                If attempting to replicate the room infiltration rate per exterior area,
                delta_pressure should be set to an approximation of the simulated air
                pressure difference described in the above formula. Default 4 represents
                typical building pressures.
        """
        # simplify parameters
        ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors = exterior_face_groups
        ext_faces = ext_walls + ext_roofs + ext_floors
        ext_openings = ext_apertures + ext_doors
        infil_flow = self.infiltration.flow_per_exterior_area

        # derive normalized flow coefficient
        flow_cof_per_area = self.solve_norm_area_flow_coefficient(
            infil_flow, air_density=air_density, delta_pressure=delta_pressure)

        # add exterior crack leakage components
        for ext_face in ext_faces:
            # Note: this calculation includes opening areas to be consistent with
            # assumption behind the Infiltration Flow per Exterior Area measure.
            flow_cof = flow_cof_per_area * ext_face.area
            ext_face.properties.energy.vent_crack = AFNCrack(flow_cof)

        # add exterior opening leakage components
        for ext_opening in ext_openings:
            if ext_opening.properties.energy.vent_opening is None:
                if isinstance(ext_opening, Aperture):
                    ext_opening.is_operable = True
                ext_opening.properties.energy.vent_opening = \
                    VentilationOpening(fraction_area_operable=0.0)
            vent_opening = ext_opening.properties.energy.vent_opening
            # Note: can be calculated with solve_norm_perimeter_flow_coefficient
            # but it adds an additional degree of freedom when attempting to calculate
            # reference delta pressure from simulated delta pressure and infiltration
            # data. Setting to zero simplifies assumptions by constraining infiltration
            # to just area-based method.
            vent_opening.flow_coefficient_closed = 0.0
            vent_opening.flow_exponent_closed = 0.5

    def envelope_components_by_type(self):
        """Get groups for room envelope components by boundary condition and type.

        The groups created by this function correspond to the structure of the
        crack template data used to generate the AirflowNetwork but can be
        useful for other purposes. However, any parts of the envelope with a
        boundary condition other than Outdoors and Surface will be excluded
        (eg. Ground or Adiabatic).

        Return:
            A tuple with five groups of exterior envelope types

            -   ext_walls - A list of exterior Wall type Face objects.

            -   ext_roofs - A list of exterior RoofCeiling type Face objects.

            -   ext_floors - A list of exterior Floor type Face objects, like you
                would find in a cantilevered Room.

            -   ext_apertures - A list of exterior Aperture Face objects.

            -   ext_doors - A list of exterior Door Face objects.

            A tuple with four groups of interior faces types

            - int_walls: List of interior Wall type Face objects.

            - int_floorceilings: List of interior RoofCeiling and Floor type Face
              objects.

            - int_apertures: List of interior Aperture Face objects.

            - int_doors: List of interior Door Face objects.

            - int_air: List of interior Faces with AirBoundary face type.
        """
        ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors = \
            [], [], [], [], []
        int_walls, int_floorceilings, int_apertures, int_doors, int_air = \
            [], [], [], [], []

        for face in self.host.faces:
            if isinstance(face.boundary_condition, Outdoors):
                if isinstance(face.type, Wall):
                    ext_walls.append(face)
                    ext_apertures.extend(face.apertures)
                    ext_doors.extend(face.doors)
                elif isinstance(face.type, RoofCeiling):
                    ext_roofs.append(face)
                    ext_apertures.extend(face.apertures)  # exterior skylights
                elif isinstance(face.type, Floor):
                    ext_floors.append(face)
            elif isinstance(face.boundary_condition, Surface):
                if isinstance(face.type, Wall):
                    int_walls.append(face)
                    int_apertures.extend(face.apertures)
                    int_doors.extend(face.doors)
                elif isinstance(face.type, RoofCeiling) or isinstance(face.type, Floor):
                    int_floorceilings.append(face)
                    int_apertures.extend(face.apertures)  # interior skylights
                elif isinstance(face.type, AirBoundary):
                    int_air.append(face)

        ext_faces = (ext_walls, ext_roofs, ext_floors,
                     ext_apertures, ext_doors)
        int_faces = (int_walls, int_floorceilings,
                     int_apertures, int_doors, int_air)

        return ext_faces, int_faces

    def move(self, moving_vec):
        """Move this object along a vector.

        Args:
            moving_vec: A ladybug_geometry Vector3D with the direction and distance
                to move the object.
        """
        if self.daylighting_control is not None:
            self.daylighting_control.move(moving_vec)

    def rotate(self, angle, axis, origin):
        """Rotate this object by a certain angle around an axis and origin.

        Args:
            angle: An angle for rotation in degrees.
            axis: Rotation axis as a Vector3D.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        if self.daylighting_control is not None:
            self.daylighting_control.rotate(angle, axis, origin)

    def rotate_xy(self, angle, origin):
        """Rotate this object counterclockwise in the world XY plane by a certain angle.

        Args:
            angle: An angle in degrees.
            origin: A ladybug_geometry Point3D for the origin around which the
                object will be rotated.
        """
        if self.daylighting_control is not None:
            self.daylighting_control.rotate_xy(angle, origin)

    def reflect(self, plane):
        """Reflect this object across a plane.

        Args:
            plane: A ladybug_geometry Plane across which the object will
                be reflected.
        """
        if self.daylighting_control is not None:
            self.daylighting_control.reflect(plane)

    def scale(self, factor, origin=None):
        """Scale this object by a factor from an origin point.

        Args:
            factor: A number representing how much the object should be scaled.
            origin: A ladybug_geometry Point3D representing the origin from which
                to scale. If None, it will be scaled from the World origin (0, 0, 0).
        """
        if self.daylighting_control is not None:
            self.daylighting_control.scale(factor, origin)

    def make_plenum(self, conditioned=False, remove_infiltration=False):
        """Turn the host Room into a plenum with no internal loads.

        This includes removing all people, lighting, equipment, hot water, and
        mechanical ventilation. By
        default, the heating/cooling system and setpoints will also be removed but they
        can optionally be kept. Infiltration is kept by default but can optionally be
        removed as well.

        This is useful to appropriately assign properties for closets, underfloor spaces,
        and drop ceilings.

        Args:
            conditioned: Boolean to indicate whether the plenum is conditioned with a
                heating/cooling system. If True, the setpoints of the Room will also
                be kept in addition to the heating/cooling system (Default: False).
            remove_infiltration: Boolean to indicate whether infiltration should be
                removed from the Rooms. (Default: False).
        """
        # remove or add the HVAC system as needed
        if conditioned and not self.is_conditioned:
            self.add_default_ideal_air()
        elif not conditioned:
            self.hvac = None

        # remove the loads and reapply infiltration/setpoints as needed
        infiltration = None if remove_infiltration else self.infiltration
        setpt = self.setpoint if conditioned else None
        self._program_type = None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._service_hot_water = None
        self._ventilation = None
        self._infiltration = infiltration
        self._setpoint = setpt

    def make_ground(self, soil_construction):
        """Change the properties of the host Room to reflect those of a ground surface.

        This is particularly useful for setting up outdoor thermal comfort maps
        to account for the surface temperature of the ground. Modeling the ground
        as a room this way will ensure that shadows other objects cast upon it
        are accounted for along with the storage of heat in the ground surface.

        The turning of a Room into a ground entails:

        * Setting all constructions to be indicative of a certain soil type.
        * Setting all Faces except the roof to have a Ground boundary condition.
        * Removing all loads and schedules assigned to the Room.

        Args:
            soil_construction: An OpaqueConstruction that reflects the soil type of
                the ground. If a multi-layered construction is input, the multiple
                layers will only be used for the roof Face of the Room and all other
                Faces will get a construction with the inner-most layer assigned.
        """
        # process the input soil_construction
        assert isinstance(soil_construction, OpaqueConstruction), 'Expected ' \
            'OpaqueConstruction for soil_construction. Got {}.'.format(
                type(soil_construction))
        int_soil = soil_construction if len(soil_construction.materials) == 1 else \
            OpaqueConstruction('{}_BelowGrade'.format(soil_construction.identifier),
                               (soil_construction.materials[-1],))

        # reset all of the properties of the room to reflect the ground
        self.reset_to_default()
        for face in self.host.faces:
            face.remove_sub_faces()
            if isinstance(face.type, RoofCeiling):
                face.boundary_condition = boundary_conditions.outdoors
                face.properties.energy.construction = soil_construction
            else:
                face.boundary_condition = boundary_conditions.ground
                face.properties.energy.construction = int_soil

    def reset_to_default(self):
        """Reset all of the properties assigned at the level of this Room to the default.
        """
        self._program_type = None
        self._construction_set = None
        self._hvac = None
        self._people = None
        self._lighting = None
        self._electric_equipment = None
        self._gas_equipment = None
        self._service_hot_water = None
        self._infiltration = None
        self._ventilation = None
        self._setpoint = None
        self._daylighting_control = None
        self._window_vent_control = None

    @classmethod
    def from_dict(cls, data, host):
        """Create RoomEnergyProperties from a dictionary.

        Note that the dictionary must be a non-abridged version for this
        classmethod to work.

        Args:
            data: A dictionary representation of RoomEnergyProperties with the
                format below.
            host: A Room object that hosts these properties.

        .. code-block:: python

            {
            "type": 'RoomEnergyProperties',
            "construction_set": {},  # A ConstructionSet dictionary
            "program_type": {},  # A ProgramType dictionary
            "hvac": {}, # A HVACSystem dictionary
            "people":{},  # A People dictionary
            "lighting": {},  # A Lighting dictionary
            "electric_equipment": {},  # A ElectricEquipment dictionary
            "gas_equipment": {},  # A GasEquipment dictionary
            "service_hot_water": {},  # A ServiceHotWater dictionary
            "infiltration": {},  # A Infiltration dictionary
            "ventilation": {},  # A Ventilation dictionary
            "setpoint": {},  # A Setpoint dictionary
            "daylighting_control": {},  # A DaylightingControl dictionary
            "window_vent_control": {}  # A VentilationControl dictionary
            }
        """
        assert data['type'] == 'RoomEnergyProperties', \
            'Expected RoomEnergyProperties. Got {}.'.format(data['type'])

        new_prop = cls(host)
        if 'construction_set' in data and data['construction_set'] is not None:
            new_prop.construction_set = \
                ConstructionSet.from_dict(data['construction_set'])
        if 'program_type' in data and data['program_type'] is not None:
            new_prop.program_type = ProgramType.from_dict(data['program_type'])
        if 'hvac' in data and data['hvac'] is not None:
            hvac_class = HVAC_TYPES_DICT[data['hvac']['type']]
            new_prop.hvac = hvac_class.from_dict(data['hvac'])

        if 'people' in data and data['people'] is not None:
            new_prop.people = People.from_dict(data['people'])
        if 'lighting' in data and data['lighting'] is not None:
            new_prop.lighting = Lighting.from_dict(data['lighting'])
        if 'electric_equipment' in data and data['electric_equipment'] is not None:
            new_prop.electric_equipment = \
                ElectricEquipment.from_dict(data['electric_equipment'])
        if 'gas_equipment' in data and data['gas_equipment'] is not None:
            new_prop.gas_equipment = GasEquipment.from_dict(data['gas_equipment'])
        if 'service_hot_water' in data and data['service_hot_water'] is not None:
            new_prop.service_hot_water = \
                ServiceHotWater.from_dict(data['service_hot_water'])
        if 'infiltration' in data and data['infiltration'] is not None:
            new_prop.infiltration = Infiltration.from_dict(data['infiltration'])
        if 'ventilation' in data and data['ventilation'] is not None:
            new_prop.ventilation = Ventilation.from_dict(data['ventilation'])
        if 'setpoint' in data and data['setpoint'] is not None:
            new_prop.setpoint = Setpoint.from_dict(data['setpoint'])
        if 'daylighting_control' in data and data['daylighting_control'] is not None:
            new_prop.daylighting_control = \
                DaylightingControl.from_dict(data['daylighting_control'])
        if 'window_vent_control' in data and data['window_vent_control'] is not None:
            new_prop.window_vent_control = \
                VentilationControl.from_dict(data['window_vent_control'])

        return new_prop

    def apply_properties_from_dict(self, abridged_data, construction_sets,
                                   program_types, hvacs, schedules):
        """Apply properties from a RoomEnergyPropertiesAbridged dictionary.

        Args:
            abridged_data: A RoomEnergyPropertiesAbridged dictionary (typically
                coming from a Model).
            construction_sets: A dictionary of ConstructionSets with identifiers
                of the sets as keys, which will be used to re-assign construction_sets.
            program_types: A dictionary of ProgramTypes with identifiers of the types as
                keys, which will be used to re-assign program_types.
            hvacs: A dictionary of HVACSystems with the identifiers of the systems as
                keys, which will be used to re-assign hvac to the Room.
            schedules: A dictionary of Schedules with identifiers of the schedules ask
                keys, which will be used to re-assign schedules.
        """
        base_e = 'Room {0} "{1}" was not found in {0}s.'
        if 'construction_set' in abridged_data and \
                abridged_data['construction_set'] is not None:
            try:
                self.construction_set = \
                    construction_sets[abridged_data['construction_set']]
            except KeyError:
                raise ValueError(
                    base_e.format(abridged_data['construction_set'], 'construction_set'))
        if 'program_type' in abridged_data and abridged_data['program_type'] is not None:
            try:
                self.program_type = program_types[abridged_data['program_type']]
            except KeyError:
                raise ValueError(
                    base_e.format(abridged_data['program_type'], 'program_type'))
        if 'hvac' in abridged_data and abridged_data['hvac'] is not None:
            try:
                self.hvac = hvacs[abridged_data['hvac']]
            except KeyError:
                raise ValueError(base_e.format(abridged_data['hvac'], 'hvac'))

        if 'people' in abridged_data and abridged_data['people'] is not None:
            self.people = People.from_dict_abridged(
                abridged_data['people'], schedules)
        if 'lighting' in abridged_data and abridged_data['lighting'] is not None:
            self.lighting = Lighting.from_dict_abridged(
                abridged_data['lighting'], schedules)
        if 'electric_equipment' in abridged_data and \
                abridged_data['electric_equipment'] is not None:
            self.electric_equipment = ElectricEquipment.from_dict_abridged(
                abridged_data['electric_equipment'], schedules)
        if 'gas_equipment' in abridged_data and \
                abridged_data['gas_equipment'] is not None:
            self.gas_equipment = GasEquipment.from_dict_abridged(
                abridged_data['gas_equipment'], schedules)
        if 'service_hot_water' in abridged_data and \
                abridged_data['service_hot_water'] is not None:
            self.service_hot_water = ServiceHotWater.from_dict_abridged(
                abridged_data['service_hot_water'], schedules)
        if 'infiltration' in abridged_data and abridged_data['infiltration'] is not None:
            self.infiltration = Infiltration.from_dict_abridged(
                abridged_data['infiltration'], schedules)
        if 'ventilation' in abridged_data and abridged_data['ventilation'] is not None:
            self.ventilation = Ventilation.from_dict_abridged(
                abridged_data['ventilation'], schedules)
        if 'setpoint' in abridged_data and abridged_data['setpoint'] is not None:
            self.setpoint = Setpoint.from_dict_abridged(
                abridged_data['setpoint'], schedules)
        if 'daylighting_control' in abridged_data and \
                abridged_data['daylighting_control'] is not None:
            self.daylighting_control = DaylightingControl.from_dict(
                abridged_data['daylighting_control'])
        if 'window_vent_control' in abridged_data and \
                abridged_data['window_vent_control'] is not None:
            self.window_vent_control = VentilationControl.from_dict_abridged(
                abridged_data['window_vent_control'], schedules)

    def to_dict(self, abridged=False):
        """Return Room energy properties as a dictionary.

        Args:
            abridged: Boolean for whether the full dictionary of the Room should
                be written (False) or just the identifier of the the individual
                properties (True). Default: False.
        """
        base = {'energy': {}}
        base['energy']['type'] = 'RoomEnergyProperties' if not \
            abridged else 'RoomEnergyPropertiesAbridged'

        # write the ProgramType into the dictionary
        if self._program_type is not None:
            base['energy']['program_type'] = \
                self._program_type.identifier if abridged else \
                self._program_type.to_dict()

        # write the ConstructionSet into the dictionary
        if self._construction_set is not None:
            base['energy']['construction_set'] = \
                self._construction_set.identifier if abridged else \
                self._construction_set.to_dict()

        # write the hvac into the dictionary
        if self._hvac is not None:
            base['energy']['hvac'] = \
                self._hvac.identifier if abridged else self._hvac.to_dict()

        # write any room-specific overriding properties into the dictionary
        if self._people is not None:
            base['energy']['people'] = self._people.to_dict(abridged)
        if self._lighting is not None:
            base['energy']['lighting'] = self._lighting.to_dict(abridged)
        if self._electric_equipment is not None:
            base['energy']['electric_equipment'] = \
                self._electric_equipment.to_dict(abridged)
        if self._gas_equipment is not None:
            base['energy']['gas_equipment'] = self._gas_equipment.to_dict(abridged)
        if self._service_hot_water is not None:
            base['energy']['service_hot_water'] = \
                self._service_hot_water.to_dict(abridged)
        if self._infiltration is not None:
            base['energy']['infiltration'] = self._infiltration.to_dict(abridged)
        if self._ventilation is not None:
            base['energy']['ventilation'] = self._ventilation.to_dict(abridged)
        if self._setpoint is not None:
            base['energy']['setpoint'] = self._setpoint.to_dict(abridged)
        if self._daylighting_control is not None:
            base['energy']['daylighting_control'] = self._daylighting_control.to_dict()
        if self._window_vent_control is not None:
            base['energy']['window_vent_control'] = \
                self._window_vent_control.to_dict(abridged)

        return base

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Room object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        new_room = RoomEnergyProperties(
            _host, self._program_type, self._construction_set, self._hvac)
        new_room._people = self._people
        new_room._lighting = self._lighting
        new_room._electric_equipment = self._electric_equipment
        new_room._gas_equipment = self._gas_equipment
        new_room._service_hot_water = self._service_hot_water
        new_room._infiltration = self._infiltration
        new_room._ventilation = self._ventilation
        new_room._setpoint = self._setpoint
        new_room._daylighting_control = self._daylighting_control
        new_room._window_vent_control = self._window_vent_control
        return new_room

    @staticmethod
    def solve_norm_area_flow_coefficient(flow_per_exterior_area, flow_exponent=0.65,
                                         air_density=1.2041, delta_pressure=4):
        """Get normalized mass flow coefficient [kg/(m2 s P^n)] from infiltration per area.

        The normalized area air mass flow coefficient is derived from a zone's
        infiltration flow rate using the power law relationship between pressure
        and air flow::

            Qva * d = Cqa * dP^n

            where:
                Cqa: Air mass flow coefficient per unit meter at 1 Pa [kg/m2/s/P^n]
                Qva: Volumetric air flow rate per area [m3/s/m2]
                d: Air density [kg/m3]
                dP: Change in pressure across building envelope orifice [Pa]
                n: Air mass flow exponent [-]

        Rearranged to solve for ``Cqa`` ::

            Cqa = (Qva * d) / dP^n

        The resulting value has units of kg/(m2-s-P^n) @ <delta_pressure> Pa, while the
        EnergyPlus AirflowNetwork requires this value to be in kg/(s-Pa) @ 1 Pa. Thus
        this value needs to be multiplied by its corresponding exposed surface area.
        Since the actual ratio between mass infiltration and pressure difference (raised
        by n) is constant, we assume solving for the flow coefficient at the
        delta_pressure value is equivalent to solving it at the required 1 Pa.

        Args:
            flow_per_exterior_area: A numerical value for the intensity of infiltration
                in m3/s per square meter of exterior surface area.
            air_density: Air density in kg/m3. (Default: 1.2041 represents
                air density at a temperature of 20 C and 101325 Pa).
            flow_exponent: A numerical value for the air mass flow exponent.
                (Default: 0.65).
            delta_pressure: Reference air pressure difference across building envelope
                orifice in Pascals. Default 4 represents typical building pressures.

        Returns:
            Air mass flow coefficient per unit meter at 1 Pa [kg/m2/s/P^n]
        """
        qva = flow_per_exterior_area
        n = flow_exponent
        d = air_density
        dp = delta_pressure
        # group similar magnitude terms to preserve precision
        return (qva * d) / (dp ** n)

    @staticmethod
    def solve_norm_perimeter_flow_coefficient(norm_area_flow_coefficient, face_area,
                                              face_perimeter):
        """Get mass flow coefficient [kg/(s m P^n)] from a normalied one and geometry.

        This parameter is used to derive air flow for the four cracks around the
        perimeter of a closed window or door: one along the bottom, one along the top,
        and one on each side. Since this value is derived from the infiltration flow
        rate per exterior area, which represents an average over many types of air
        leakage rates, this value is not intended to be representative of actual opening
        edges flow coefficients. The normalized perimeter air mass flow coefficient is
        derived from its infiltration flow rate using the following formula::

            Qva * d * A = Cql * L * dP^n

            where:
                Cql: Air mass flow coefficient per unit length at 1 Pa [kg/m/s/P^n]
                Qva: Volumetric air flow rate per length [m3/s/m]
                d: Air density [kg/m3]
                A: Surface area of opening [m2]
                L: Surface perimeter of opening [m]
                dP: Change in pressure across building envelope [Pa]
                n: Air mass flow exponent [-]

        Since ``(Qva * d) / dP^n`` equals ``Cqa`` the normalized area flow coefficient,
        this can be simplified and rearranged to solve for ``Cql`` with the following
        formula::

            (Cqa * dP^n) * A = Cql * L * dP^n
            Cql = ((Cqa * dP^n) * A) / (L * dP^n)
                = Cqa * A / L


        The resulting value has units of kg/(m-s-P^n) @ <delta_pressure> Pa, while the
        EnergyPlus AirflowNetwork requires this value to be in kg/(s-Pa) @ 1 Pa. Thus
        unlike the surface area flow_coefficient, this coefficient is normalized per
        unit length. Since the actual ratio between mass infiltration and pressure
        difference (raised by n) is constant, we assume solving for the flow coefficient
        at the delta_pressure value is equivalent to solving it at the required 1 Pa.

        Args:
            norm_area_flow_coefficient: Air mass flow coefficient per unit meter at
                1 Pa [kg/m2/s/P^n]
            face_area: A numerical value for the total exterior area in m2.
            face_perimeter: A numerical value for the total exterior perimeter in meters.

        Returns:
            Air mass flow coefficient per unit length at 1 Pa [kg/m/s/P^n]
        """
        cqa = norm_area_flow_coefficient
        a = face_area
        ln = face_perimeter
        # group similar magnitude terms to preserve precision
        return cqa * (a / ln)

    def _dup_load(self, load_name, load_class):
        """Duplicate a load object assigned to this Room or get a new one if none exists.

        Args:
            load_name: Text for the name of the property as it appears on this object.
                This is used both to retrive the load and to man an identifier
                for it. (eg. "people", "lighting").
            load_class: The class of the load object (eg. People).
        """
        load_obj = getattr(self, load_name)
        load_id = '{}_{}'.format(self.host.identifier, load_name)
        try:  # duplicate the Room's current load object and give it a unique ID
            dup_load = load_obj.duplicate()
            dup_load.identifier = load_id
            return dup_load
        except AttributeError:  # currently no load object; create a new one
            return load_class(load_id, 0, always_on)

    def _absolute_by_floor(self, load_obj, property_name, value, conversion):
        """Set a floor-normalized load object to have an abolute value for a property."""
        try:
            floor_area = self.host.floor_area * conversion ** 2
            setattr(load_obj, property_name, value / floor_area)
        except ZeroDivisionError:
            pass  # no floor area; just leave the load level as is

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Room Energy Properties: [host: {}]'.format(self.host.display_name)
