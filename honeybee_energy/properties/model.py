# coding=utf-8
"""Model Energy Properties."""
try:
    from itertools import izip as zip  # python 2
except ImportError:
    pass   # python 3

from ladybug_geometry.geometry2d import Vector2D
from ladybug_geometry.geometry3d import Point3D
from honeybee.boundarycondition import Outdoors, Surface, boundary_conditions
from honeybee.facetype import AirBoundary, face_types
from honeybee.extensionutil import model_extension_dicts
from honeybee.checkdup import check_duplicate_identifiers
from honeybee.units import conversion_factor_to_meters
from honeybee.typing import invalid_dict_error, clean_ep_string, \
    clean_and_id_ep_string, clean_and_number_ep_string
from honeybee.face import Face
from honeybee.room import Room
from honeybee.model import Model

from ..material.dictutil import dict_to_material
from ..construction.dictutil import CONSTRUCTION_TYPES, dict_to_construction, \
    dict_abridged_to_construction
from ..construction.opaque import OpaqueConstruction
from ..construction.window import WindowConstruction
from ..construction.windowshade import WindowConstructionShade
from ..construction.dynamic import WindowConstructionDynamic
from ..construction.air import AirBoundaryConstruction
from ..constructionset import ConstructionSet
from ..material.opaque import EnergyMaterialVegetation
from ..schedule.typelimit import ScheduleTypeLimit
from ..schedule.ruleset import ScheduleRuleset
from ..schedule.dictutil import SCHEDULE_TYPES, dict_to_schedule, \
    dict_abridged_to_schedule
from ..programtype import ProgramType
from ..hvac.detailed import DetailedHVAC
from ..hvac import HVAC_TYPES_DICT
from ..shw import SHWSystem
from ..ventcool.simulation import VentilationSimulationControl
from ..generator.loadcenter import ElectricLoadCenter

from ..config import folders
from ..lib.constructions import generic_context
from ..lib.constructionsets import generic_construction_set
from ..lib.schedules import always_on
from ..lib.scheduletypelimits import fractional


class ModelEnergyProperties(object):
    """Energy Properties for Honeybee Model.

    Args:
        host: A honeybee_core Model object that hosts these properties.
        ventilation_simulation_control: A VentilationSimulationControl object that
            defines global parameters for ventilation simulation.
        electric_load_center: A ElectricLoadCenter object that defines the properties
            of the model's electric loads center.

    Properties:
        * host
        * materials
        * constructions
        * room_constructions
        * face_constructions
        * shade_constructions
        * construction_sets
        * global_construction_set
        * schedule_type_limits
        * schedules
        * shade_schedules
        * room_schedules
        * program_type_schedules
        * hvac_schedules
        * orphaned_trans_schedules
        * program_types
        * hvacs
        * shws
        * ventilation_simulation_control
        * electric_load_center
    """

    def __init__(
            self, host, ventilation_simulation_control=None, electric_load_center=None):
        """Initialize Model energy properties."""
        self._host = host
        self.ventilation_simulation_control = ventilation_simulation_control
        self.electric_load_center = electric_load_center

    @property
    def host(self):
        """Get the Model object hosting these properties."""
        return self._host

    @property
    def materials(self):
        """Get a list of all unique materials contained within the model.

        This includes materials across all Faces, Apertures, Doors and Room
        ConstructionSets but it does NOT include the Honeybee generic default
        construction set.
        """
        materials = []
        for constr in self.constructions:
            try:
                materials.extend(constr.materials)
                if constr.has_frame:
                    materials.append(constr.frame)
                if isinstance(constr, WindowConstructionShade):
                    if constr.is_switchable_glazing:
                        materials.append(constr.switched_glass_material)
                    if constr.shade_location == 'Between':
                        materials.append(constr.window_construction.materials[-2])
            except AttributeError:
                pass  # ShadeConstruction or AirBoundaryConstruction
        return list(set(materials))

    @property
    def constructions(self):
        """Get a list of all unique constructions in the model.

        This includes constructions across all Faces, Apertures, Doors, Shades,
        and Room ConstructionSets but it does NOT include the Honeybee generic
        default construction set.
        """
        all_constrs = self.room_constructions + self.face_constructions + \
            self.shade_constructions
        return list(set(all_constrs))

    @property
    def room_constructions(self):
        """Get a list of all unique constructions assigned to Room ConstructionSets.

        This also includes the constructions assigned to Room InternalMasses.
        """
        room_constrs = []
        for cnstr_set in self.construction_sets:
            room_constrs.extend(cnstr_set.modified_constructions_unique)
        for room in self.host.rooms:
            for int_mass in room.properties.energy._internal_masses:
                constr = int_mass.construction
                if not self._instance_in_array(constr, room_constrs):
                    room_constrs.append(constr)
        return list(set(room_constrs))

    @property
    def face_constructions(self):
        """Get a list of all unique constructions assigned to Faces, Apertures and Doors.
        """
        constructions = []
        for face in self.host.faces:
            self._check_and_add_obj_construction(face, constructions)
            for ap in face.apertures:
                self._check_and_add_obj_construction(ap, constructions)
            for dr in face.doors:
                self._check_and_add_obj_construction(dr, constructions)
        for ap in self.host.orphaned_apertures:
            self._check_and_add_obj_construction(ap, constructions)
        for dr in self.host.orphaned_doors:
            self._check_and_add_obj_construction(dr, constructions)
        return list(set(constructions))

    @property
    def shade_constructions(self):
        """Get a list of all unique constructions assigned to Shades in the model."""
        constructions = []
        for shade in self.host.shades:
            self._check_and_add_obj_construction(shade, constructions)
        for sm in self.host.shade_meshes:  # check all ShadeMesh modifiers
            self._check_and_add_obj_construction(sm, constructions)
        return list(set(constructions))

    @property
    def construction_sets(self):
        """Get a list of all unique Room-Assigned ConstructionSets in the Model."""
        construction_sets = []
        for room in self.host.rooms:
            if room.properties.energy._construction_set is not None:
                if not self._instance_in_array(room.properties.energy._construction_set,
                                               construction_sets):
                    construction_sets.append(room.properties.energy._construction_set)
        return list(set(construction_sets))  # catch equivalent construction sets

    @property
    def global_construction_set(self):
        """The global energy construction set.

        This is what is used whenever no construction has been assigned to a given
        Face/Aperture/Door/Shade and there is no construction_set assigned to the
        parent Room.
        """
        return generic_construction_set

    @property
    def schedule_type_limits(self):
        """Get a list of all unique schedule type limits contained within the model.

        This includes schedules across all Shades and Rooms.
        """
        type_limits = []
        for sched in self.schedules:
            t_lim = sched.schedule_type_limit
            if t_lim is not None and not self._instance_in_array(t_lim, type_limits):
                type_limits.append(t_lim)
        return list(set(type_limits))

    @property
    def schedules(self):
        """Get a list of all unique schedules directly assigned to objects in the model.

        This includes schedules across all ProgramTypes, HVACs, Rooms and Shades.
        However, it does not include any of the orphaned_trans_schedules as these
        are not directly assigned to objects but rather generated from their
        constructions.
        """
        all_scheds = self.program_type_schedules + self.hvac_schedules + \
            self.room_schedules + self.shade_schedules + self.construction_schedules
        return list(set(all_scheds))

    @property
    def construction_schedules(self):
        """Get a list of all unique schedules assigned to constructions in the model.

        This includes schedules on al AirBoundaryConstructions.
        """
        schedules = []
        for constr in self.constructions:
            if isinstance(constr, AirBoundaryConstruction):
                self._check_and_add_schedule(constr.air_mixing_schedule, schedules)
            elif isinstance(constr, WindowConstructionShade):
                if constr.schedule is not None:
                    self._check_and_add_schedule(constr.schedule, schedules)
            elif isinstance(constr, WindowConstructionDynamic):
                self._check_and_add_schedule(constr.schedule, schedules)
        return list(set(schedules))

    @property
    def shade_schedules(self):
        """Get a list of unique transmittance schedules assigned to Shades in the model.
        """
        schedules = []
        for shade in self.host.orphaned_shades:
            self._check_and_add_shade_schedule(shade, schedules)
        for room in self.host.rooms:  # check all Room Shade schedules
            for shade in room.shades:
                self._check_and_add_shade_schedule(shade, schedules)
            for face in room.faces:  # check all Face Shade schedules
                for shade in face.shades:
                    self._check_and_add_shade_schedule(shade, schedules)
                for ap in face.apertures:  # check all Aperture Shade schedules
                    for shade in ap.shades:
                        self._check_and_add_shade_schedule(shade, schedules)
                for dr in face.doors:  # check all Door Shade schedules
                    for shade in dr.shades:
                        self._check_and_add_shade_schedule(shade, schedules)
        for sm in self.host.shade_meshes:
            self._check_and_add_shade_schedule(sm, schedules)
        return list(set(schedules))

    @property
    def room_schedules(self):
        """Get a list of all unique schedules assigned directly to Rooms in the model.

        Note that this does not include schedules from ProgramTypes assigned to the
        rooms. For this, use the program_type_schedules property.
        """
        scheds = []
        for room in self.host.rooms:
            people = room.properties.energy._people
            lighting = room.properties.energy._lighting
            electric_equipment = room.properties.energy._electric_equipment
            gas_equipment = room.properties.energy._gas_equipment
            shw = room.properties.energy._service_hot_water
            infiltration = room.properties.energy._infiltration
            ventilation = room.properties.energy._ventilation
            setpoint = room.properties.energy._setpoint
            window_vent = room.properties.energy._window_vent_control
            processes = room.properties.energy._process_loads
            fans = room.properties.energy._fans
            if people is not None:
                self._check_and_add_schedule(people.occupancy_schedule, scheds)
                self._check_and_add_schedule(people.activity_schedule, scheds)
            if lighting is not None:
                self._check_and_add_schedule(lighting.schedule, scheds)
            if electric_equipment is not None:
                self._check_and_add_schedule(electric_equipment.schedule, scheds)
            if gas_equipment is not None:
                self._check_and_add_schedule(gas_equipment.schedule, scheds)
            if shw is not None:
                self._check_and_add_schedule(shw.schedule, scheds)
            if infiltration is not None:
                self._check_and_add_schedule(infiltration.schedule, scheds)
            if ventilation is not None and ventilation.schedule is not None:
                self._check_and_add_schedule(ventilation.schedule, scheds)
            if setpoint is not None:
                self._check_and_add_schedule(setpoint.heating_schedule, scheds)
                self._check_and_add_schedule(setpoint.cooling_schedule, scheds)
                if setpoint.humidifying_schedule is not None:
                    self._check_and_add_schedule(
                        setpoint.humidifying_schedule, scheds)
                    self._check_and_add_schedule(
                        setpoint.dehumidifying_schedule, scheds)
            if window_vent is not None:
                self._check_and_add_schedule(window_vent.schedule, scheds)
            if len(processes) != 0:
                for process in processes:
                    self._check_and_add_schedule(process.schedule, scheds)
            if len(fans) != 0:
                for fan in fans:
                    self._check_and_add_schedule(fan.control.schedule, scheds)
        return list(set(scheds))

    @property
    def program_type_schedules(self):
        """Get a list of all unique schedules assigned to ProgramTypes in the model."""
        schedules = []
        for p_type in self.program_types:
            for sched in p_type.schedules:
                self._check_and_add_schedule(sched, schedules)
        return list(set(schedules))

    @property
    def hvac_schedules(self):
        """Get a list of all unique HVAC-assigned schedules in the model."""
        schedules = []
        for hvac in self.hvacs:
            for sched in hvac.schedules:
                self._check_and_add_schedule(sched, schedules)
        return list(set(schedules))

    @property
    def orphaned_trans_schedules(self):
        """Get a list of constant transmittance schedules for transparent orphaned objs.

        These schedules are not directly assigned to any honeybee objects but
        they are automatically generated from the constructions of orphaned objects.
        They are intended to be assigned to shade representations of the orphaned
        objects in the simulation in order to account for their transparency.
        """
        # collect all unique transmittances
        transmittances = set()
        for face in self.host.orphaned_faces:
            for ap in face.apertures:
                self._check_and_add_obj_transmit(ap, transmittances)
            for dr in face.doors:
                self._check_and_add_obj_transmit(dr, transmittances)
        for ap in self.host.orphaned_apertures:
            self._check_and_add_obj_transmit(ap, transmittances)
        for dr in self.host.orphaned_doors:
            if dr.is_glass:
                self._check_and_add_obj_transmit(dr, transmittances)
        # create the schedules from the transmittances
        schedules = []
        for trans in transmittances:
            sch_name = 'Constant %.3f Transmittance' % trans
            sch = ScheduleRuleset.from_constant_value(sch_name, trans, fractional)
            schedules.append(sch)
        return schedules

    @property
    def program_types(self):
        """Get a list of all unique ProgramTypes in the Model."""
        program_types = []
        for room in self.host.rooms:
            if room.properties.energy._program_type is not None:
                if not self._instance_in_array(room.properties.energy._program_type,
                                               program_types):
                    program_types.append(room.properties.energy._program_type)
        return list(set(program_types))  # catch equivalent program types

    @property
    def hvacs(self):
        """Get a list of all unique HVAC systems in the Model."""
        hvacs = []
        for room in self.host.rooms:
            if room.properties.energy._hvac is not None:
                if not self._instance_in_array(room.properties.energy._hvac, hvacs):
                    hvacs.append(room.properties.energy._hvac)
        return hvacs

    @property
    def shws(self):
        """Get a list of all unique SHW systems in the Model."""
        shws = []
        for room in self.host.rooms:
            if room.properties.energy._shw is not None:
                if not self._instance_in_array(room.properties.energy._shw, shws):
                    shws.append(room.properties.energy._shw)
        return shws

    @property
    def electric_load_center(self):
        """Get or set global parameters for ventilation cooling simulation."""
        return self._electric_load_center

    @electric_load_center.setter
    def electric_load_center(self, value):
        if value is None:
            value = ElectricLoadCenter()
        else:
            assert isinstance(value, ElectricLoadCenter), \
                'electric_load_center must be a ' \
                'ElectricLoadCenter object. Got: {}.'.format(value)
        self._electric_load_center = value

    @property
    def ventilation_simulation_control(self):
        """Get or set global parameters for ventilation cooling simulation."""
        return self._ventilation_simulation_control

    @ventilation_simulation_control.setter
    def ventilation_simulation_control(self, value):
        if value is None:
            value = VentilationSimulationControl()
        else:
            assert isinstance(value, VentilationSimulationControl), \
                'ventilation_simulation_control must be a ' \
                'VentilationSimulationControl object. Got: {}.'.format(value)
        self._ventilation_simulation_control = value

    def aperture_constructions(self, room_assigned_only=True):
        """Get only the constructions assigned to Apertures in the Model.

        Args:
            room_assigned_only: Boolean to note whether only the constructions that
                are a part of Room-assigned Apertures should be returned (True) or
                constructions assigned to all Apertures should be included (False).
        """
        if room_assigned_only:
            aps_to_search = []
            for room in self.host.rooms:
                for face in room.faces:
                    aps_to_search.extend(face.apertures)
        else:
            aps_to_search = self.host.apertures
        constructions = []
        for ap in aps_to_search:
            self._check_and_add_obj_construction_inc_parent(ap, constructions)
        return list(set(constructions))

    def door_constructions(self, room_assigned_only=True):
        """Get only the constructions assigned to Doors in the Model.

        Args:
            room_assigned_only: Boolean to note whether only the constructions that
                are a part of Room-assigned Doors should be returned (True) or
                constructions assigned to all Doors should be included (False).
        """
        if room_assigned_only:
            doors_to_search = []
            for room in self.host.rooms:
                for face in room.faces:
                    doors_to_search.extend(face.doors)
        else:
            doors_to_search = self.host.doors
        constructions = []
        for dr in doors_to_search:
            self._check_and_add_obj_construction_inc_parent(dr, constructions)
        return list(set(constructions))

    def autocalculate_ventilation_simulation_control(self):
        """Set geometry properties of ventilation_simulation_control with Model's rooms.

        The room geometry of the host Model will be used to assign the aspect_ratio,
        long_axis_angle, and the building_type. Note that these properties are only
        meaningful for simulations using the AirflowNetwork.
        """
        self.ventilation_simulation_control.assign_geometry_properties_from_rooms(
            self.host.rooms)

    def remove_child_constructions(self):
        """Remove constructions assigned to Faces, Apertures, Doors and Shades.

        This means that all constructions of the Mode's rooms will be assigned
        by the Rooms' construction_set (or the Honeybee default ConstructionSet
        if Rooms have no construction set).
        """
        for room in self._host.rooms:
            room.properties.energy.remove_child_constructions()

    def window_construction_by_orientation(
            self, construction, orientation=0, offset=45, north_vector=Vector2D(0, 1)):
        """Set the construction of exterior Apertures facing a given orientation.

        This is useful for testing orientation-specific energy conservation
        strategies or creating ASHRAE baseline buildings.

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
        for room in self._host.rooms:
            room.properties.energy.window_construction_by_orientation(
                construction, orientation, offset, north_vector)

    def remove_hvac_from_no_setpoints(self):
        """Remove any HVAC systems assigned to Rooms that have no thermostat setpoints.

        This will ensure that EnergyPlus does not fail when it tries to simulate
        a HVAC for which there are no criteria to meet.

        Returns:
            A list of text strings for each room that had an HVAC removed because
            of a lack of setpoints. This can be printed to logs or registered as
            a warning in the interface.
        """
        removed_msgs = []
        for room in self._host.rooms:
            if room.properties.energy.hvac is not None \
                    and room.properties.energy.setpoint is None:
                hvac_name = room.properties.energy.hvac.display_name
                room.properties.energy.hvac = None
                msg = 'Room "{}" has an HVAC assigned to it but does not have any ' \
                    'thermostat setpoints.\nThe HVAC "{}" will not be translated ' \
                    'for this room.'.format(room.display_name, hvac_name)
                removed_msgs.append(msg)
        return removed_msgs

    def missing_adjacencies_to_adiabatic(self):
        """Set any Faces with missing adjacencies in the model to adiabatic.

        If any of the Faces with missing adjacencies have sub-faces, these will be
        removed in order to accommodate the adiabatic condition. Similarly, if the
        Face is an AirBoundary, the type will be set to a Wall.

        Note that this method assumes all of the Surface boundary conditions
        are set up correctly with the last boundary_condition_object being
        the adjacent room.
        """
        room_ids = set()
        for room in self.host._rooms:
            room_ids.add(room.identifier)
        for room in self.host._rooms:
            for face in room._faces:
                if isinstance(face.boundary_condition, Surface):
                    bc_room = face.boundary_condition.boundary_condition_objects[-1]
                    if bc_room not in room_ids:
                        face.remove_sub_faces()
                        if isinstance(face.type, AirBoundary):
                            face.type = face_types.wall
                        face.boundary_condition = boundary_conditions.adiabatic
                elif isinstance(face.type, AirBoundary):  # assume it's Surface
                    face.type = face_types.wall
                    face.boundary_condition = boundary_conditions.adiabatic

    def assign_radiance_solar_interior(self):
        """Assign honeybee Radiance modifiers based on interior solar properties."""
        mod_sets = {}
        for constr_set in self.construction_sets + [generic_construction_set]:
            mod_sets[constr_set.identifier] = constr_set.to_radiance_solar_interior()
        self._assign_room_modifier_sets(mod_sets)
        mods = {}
        for con in self.face_constructions + self.shade_constructions:
            mods[con.identifier] = con.to_radiance_solar_interior() \
                if isinstance(con, OpaqueConstruction) else con.to_radiance_solar()
        self._assign_face_modifiers(mods)

    def assign_radiance_visible_interior(self):
        """Assign honeybee Radiance modifiers based on interior visible properties."""
        mod_sets = {}
        for constr_set in self.construction_sets + [generic_construction_set]:
            mod_sets[constr_set.identifier] = constr_set.to_radiance_visible_interior()
        self._assign_room_modifier_sets(mod_sets)
        mods = {}
        for con in self.face_constructions + self.shade_constructions:
            mods[con.identifier] = con.to_radiance_visible_interior() \
                if isinstance(con, OpaqueConstruction) else con.to_radiance_visible()
        self._assign_face_modifiers(mods)

    def assign_radiance_solar_exterior(self):
        """Assign honeybee Radiance modifiers based on exterior solar properties."""
        mod_sets = {}
        for constr_set in self.construction_sets + [generic_construction_set]:
            mod_sets[constr_set.identifier] = constr_set.to_radiance_solar_exterior()
        self._assign_room_modifier_sets(mod_sets)
        mods = {}
        for con in self.face_constructions + self.shade_constructions:
            mods[con.identifier] = con.to_radiance_solar_exterior() \
                if isinstance(con, OpaqueConstruction) else con.to_radiance_solar()
        self._assign_face_modifiers(mods)

    def assign_radiance_visible_exterior(self):
        """Assign honeybee Radiance modifiers based on exterior visible properties."""
        mod_sets = {}
        for constr_set in self.construction_sets + [generic_construction_set]:
            mod_sets[constr_set.identifier] = constr_set.to_radiance_visible_exterior()
        self._assign_room_modifier_sets(mod_sets)
        mods = {}
        for con in self.face_constructions + self.shade_constructions:
            mods[con.identifier] = con.to_radiance_visible_exterior() \
                if isinstance(con, OpaqueConstruction) else con.to_radiance_visible()
        self._assign_face_modifiers(mods)

    def offset_and_assign_exterior_face_modifiers(
            self, reflectance_type='Solar', offset=0.02):
        """Offset all exterior Faces and assign them a modifier based on exterior layer.

        This is often useful in conjunction with the assign_radiance_solar_interior
        or the assign_radiance_visible_interior to make a radiance model that
        accounts for both the interior and exterior material layers.

        Note that this method will add the offset faces as orphaned faces and so the
        model will not be simulate-able in EnergyPlus after running this method
        (it is only intended to be simulated within Radiance).

        Args:
            reflectance_type: Text for the type of reflectance to be used in the
                assigned modifier. Must be either Solar or Visible. (Default: Solar).
            offset: A number for the distance at which the exterior Faces should
                be offset. (Default: 0.02, suitable for models in meters).
        """
        # collect all of the unique exterior face constructions
        constructions = []
        for room in self.host.rooms:
            for face in room.faces:  # check all Face constructions
                if isinstance(face.boundary_condition, Outdoors):
                    constr = face.properties.energy.construction
                    if not self._instance_in_array(constr, constructions):
                        constructions.append(constr)
        constructions = set(constructions)
        # convert constructions into modifiers
        mods = {}
        for con in constructions:
            mods[con.identifier] = con.to_radiance_visible_exterior() \
                if reflectance_type == 'Visible' else con.to_radiance_solar_exterior()
        # loop through the faces and create new offset exterior ones
        new_faces = []
        for room in self._host.rooms:
            for face in room.faces:
                if isinstance(face.boundary_condition, Outdoors):
                    new_geo = face.punched_geometry.move(face.normal * offset)
                    new_id = '{}_ext'.format(face.identifier)
                    new_face = Face(
                        new_id, new_geo, face.type, face.boundary_condition)
                    new_face.properties.radiance.modifier = \
                        mods[face.properties.energy.construction.identifier]
                    new_faces.append(new_face)
        # add the new faces to the host model
        for face in new_faces:
            self._host.add_face(face)

    def assign_dynamic_aperture_groups(self):
        """Assign aperture groups to all Apertures with dynamic and shaded constructions.

        Note that this method will only add two groups for each dynamic aperture.
        The first group will be completely transparent while the second group
        will be a 100% transmittance perfectly diffusing modifier. This is done
        with the assumption that EnergyPlus transmittance results will be used to
        appropriately account for the transmittance of states in the results.
        """
        # import dependencies and set up reused variables
        try:
            from honeybee_radiance.modifier.material import Trans
            from honeybee_radiance.dynamic.state import RadianceSubFaceState
        except ImportError as e:
            raise ImportError('honeybee_radiance library must be installed to use '
                              'assign_dynamic_aperture_groups() method. {}'.format(e))
        all_spec = Trans('complete_spec', 1, 1, 1, 0, 0, 1, 1)
        all_diff = Trans('complete_diff', 1, 1, 1, 0, 0, 1, 0)

        # establish groups based on similar constructions, orientations and controls
        group_dict = {}
        for room in self.host.rooms:
            for face in room.faces:
                for ap in face.apertures:
                    u_id = None
                    con = ap.properties.energy.construction
                    if isinstance(con, WindowConstructionDynamic):
                        orient = '{}_{}'.format(int(ap.azimuth), int(ap.altitude))
                        u_id = '{}_{}'.format(con.identifier, orient)
                    elif isinstance(con, WindowConstructionShade):
                        orient = '{}_{}'.format(int(ap.azimuth), int(ap.altitude))
                        if con.is_groupable:
                            u_id = '{}_{}'.format(con.identifier, orient)
                        elif con.is_room_groupable:
                            u_id = '{}_{}_{}'.format(
                                con.identifier, room.identifier, orient)
                        else:
                            u_id = ap.identifier
                    if u_id is not None:
                        try:
                            group_dict[u_id].append(ap)
                        except KeyError:
                            group_dict[u_id] = [ap]

        # create the actual aperture groups and assign states
        for group in group_dict.values():
            grp_name = group[0].identifier
            for ap in group:
                ap.properties.radiance.dynamic_group_identifier = grp_name
                spec_state = RadianceSubFaceState(all_spec)
                diff_state = RadianceSubFaceState(all_diff)
                ap.properties.radiance.states = [spec_state, diff_state]

    def generate_ground_room(self, soil_construction):
        """Generate and add a Room to the Model that represents the ground.

        The Room will be added such that it exists below all of the other geometry
        of the model and covers the full XY extents of the model.

        This is useful when it is desirable to track the ground surface temperature
        or when the model needs a simple Room to be able to simulate in EnergyPlus.

        Args:
            soil_construction: An OpaqueConstruction that reflects the soil type of
                the ground. If a multi-layered construction is input, the multiple
                layers will only be used for the roof Face of the Room and all other
                Faces will get a construction with the inner-most layer assigned.
                If the outer-most material is an EnergyMaterialVegetation and there
                are no other layers in the construction, the vegetation's soil
                material will be used for all other Faces.
        """
        # create the room geometry from the min and max points
        min_pt, max_pt = self.host.min, self.host.max
        room_height = 1 / conversion_factor_to_meters(self.host.units)
        rm_origin = Point3D(min_pt.x, min_pt.y, min_pt.z - room_height)
        ground = Room.from_box(
            'Ground_Room', max_pt.x - min_pt.x, max_pt.y - min_pt.y, room_height,
            origin=rm_origin)
        # turn the room into a ground with an appropriate construction
        ground.properties.energy.make_ground(soil_construction)
        self.host.add_room(ground)
        return ground

    def check_all(self, raise_exception=True, detailed=False):
        """Check all of the aspects of the Model energy properties.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if any errors are found. If False, this method will simply
                return a text string with all errors that were found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A text string with all errors that were found or a list if detailed is True.
            This string (or list) will be empty if no errors were found.
        """
        # set up defaults to ensure the method runs correctly
        detailed = False if raise_exception else detailed
        msgs = []
        # perform checks for duplicate identifiers
        msgs.append(self.check_duplicate_material_identifiers(False, detailed))
        msgs.append(self.check_duplicate_construction_identifiers(False, detailed))
        msgs.append(self.check_duplicate_construction_set_identifiers(False, detailed))
        msgs.append(
            self.check_duplicate_schedule_type_limit_identifiers(False, detailed))
        msgs.append(self.check_duplicate_schedule_identifiers(False, detailed))
        msgs.append(self.check_duplicate_program_type_identifiers(False, detailed))
        msgs.append(self.check_duplicate_hvac_identifiers(False, detailed))
        msgs.append(self.check_duplicate_shw_identifiers(False, detailed))
        # perform checks for specific energy simulation rules
        msgs.append(self.check_detailed_hvac_rooms(False, detailed))
        msgs.append(self.check_shw_rooms_in_model(False, detailed))
        msgs.append(self.check_all_air_boundaries_with_window(False, detailed))
        msgs.append(self.check_one_vegetation_material(False, detailed))
        msgs.append(self.check_interior_constructions_reversed(False, detailed))
        # output a final report of errors or raise an exception
        full_msgs = [msg for msg in msgs if msg]
        if detailed:
            return [m for msg in full_msgs for m in msg]
        full_msg = '\n'.join(full_msgs)
        if raise_exception and len(full_msgs) != 0:
            raise ValueError(full_msg)
        return full_msg

    def check_duplicate_material_identifiers(self, raise_exception=True, detailed=False):
        """Check that there are no duplicate Material identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.materials, raise_exception, 'Material',
            detailed, '020001', 'Energy', error_type='Duplicate Material Identifier')

    def check_duplicate_construction_identifiers(
            self, raise_exception=True, detailed=False):
        """Check that there are no duplicate Construction identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.constructions, raise_exception, 'Construction',
            detailed, '020002', 'Energy', error_type='Duplicate Construction Identifier')

    def check_duplicate_construction_set_identifiers(
            self, raise_exception=True, detailed=False):
        """Check that there are no duplicate ConstructionSet identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.construction_sets, raise_exception, 'ConstructionSet',
            detailed, '020003', 'Energy',
            error_type='Duplicate ConstructionSet Identifier')

    def check_duplicate_schedule_type_limit_identifiers(
            self, raise_exception=True, detailed=False):
        """Check that there are no duplicate ScheduleTypeLimit identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.schedule_type_limits, raise_exception, 'ScheduleTypeLimit',
            detailed, '020004', 'Energy',
            error_type='Duplicate ScheduleTypeLimit Identifier')

    def check_duplicate_schedule_identifiers(self, raise_exception=True, detailed=False):
        """Check that there are no duplicate Schedule identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.schedules, raise_exception, 'Schedule', detailed, '020005', 'Energy',
            error_type='Duplicate Schedule Identifier')

    def check_duplicate_program_type_identifiers(
            self, raise_exception=True, detailed=False):
        """Check that there are no duplicate ProgramType identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.program_types, raise_exception, 'ProgramType',
            detailed, '020006', 'Energy', error_type='Duplicate ProgramType Identifier')

    def check_duplicate_hvac_identifiers(self, raise_exception=True, detailed=False):
        """Check that there are no duplicate HVAC identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.hvacs, raise_exception, 'HVAC', detailed, '020007', 'Energy',
            error_type='Duplicate HVAC Identifier')

    def check_duplicate_shw_identifiers(self, raise_exception=True, detailed=False):
        """Check that there are no duplicate SHW identifiers in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if duplicate identifiers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        return check_duplicate_identifiers(
            self.shws, raise_exception, 'SHW', detailed, '020008', 'Energy',
            error_type='Duplicate SHW Identifier')

    def check_shw_rooms_in_model(self, raise_exception=True, detailed=False):
        """Check that the room_identifiers of SHWSystems are in the model.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised if
                SHWSystems reference Rooms that are not in the Model. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        detailed = False if raise_exception else detailed
        # gather a list of all the missing rooms
        shw_ids = [(shw_sys, shw_sys.ambient_condition) for shw_sys in self.shws
                   if isinstance(shw_sys.ambient_condition, str)]
        room_ids = set(room.identifier for room in self.host.rooms)
        missing_rooms = [] if detailed else set()
        for shw_sys in shw_ids:
            if shw_sys[1] not in room_ids:
                if detailed:
                    missing_rooms.append(shw_sys[0])
                else:
                    missing_rooms.add(shw_sys[1])
        # if missing rooms were found, then report the issue
        if len(missing_rooms) != 0:
            if detailed:
                all_err = []
                for shw_sys in missing_rooms:
                    msg = 'SHWSystem "{}" has a ambient_condition referencing ' \
                        'a Room that is not in the ' \
                        'Model: "{}"'.format(shw_sys.identifier, shw_sys.room_identifier)
                    error_dict = {
                        'type': 'ValidationError',
                        'code': '020009',
                        'error_type': 'SHWSystem Room Not In Model',
                        'extension_type': 'Energy',
                        'element_type': 'SHW',
                        'element_id': [shw_sys.identifier],
                        'element_name': [shw_sys.display_name],
                        'message': msg
                    }
                    all_err.append(error_dict)
                return all_err
            else:
                msg = 'The model has the following missing rooms referenced by SHW ' \
                    'Systems:\n{}'.format('\n'.join(missing_rooms))
                if raise_exception:
                    raise ValueError(msg)
                return msg
        return [] if detailed else ''

    def check_one_vegetation_material(self, raise_exception=True, detailed=False):
        """Check that there no more than one EnergyMaterialVegetation in the model.

        It is a limitation of EnergyPlus that it can only simulate a single
        eco roof per model. This should probably be addressed at some point
        so that we don't always have to check for it.

        Args:
            raise_exception: Boolean for whether a ValueError should be raised if there's
                more than one EnergyMaterialVegetation in the Model. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        # first see if there's more than one vegetation material
        all_constrs = self.room_constructions + self.face_constructions
        materials = []
        for constr in all_constrs:
            try:
                materials.extend(constr.materials)
            except AttributeError:
                pass  # ShadeConstruction
        all_mats = list(set(materials))
        veg_mats = [m for m in all_mats if isinstance(m, EnergyMaterialVegetation)]

        # if more than one vegetation material was found, then report the issue
        if len(veg_mats) > 1:
            if detailed:
                all_err = []
                for v_mat in veg_mats:
                    msg = 'EnergyMaterialVegetation "{}" is one of several vegetation ' \
                        'materials in the model.\nThis is not allowed by ' \
                        'EnergyPlus.'.format(v_mat.identifier)
                    error_dict = {
                        'type': 'ValidationError',
                        'code': '020010',
                        'error_type': 'Multiple Vegetation Materials',
                        'extension_type': 'Energy',
                        'element_type': 'Material',
                        'element_id': [v_mat.identifier],
                        'element_name': [v_mat.display_name],
                        'message': msg
                    }
                    all_err.append(error_dict)
                return all_err
            else:
                veg_mats_ids = [v_mat.identifier for v_mat in veg_mats]
                msg = 'The model has multiple vegetation materials. This is not ' \
                    'allowed by EnergyPlus:\n{}'.format('\n'.join(veg_mats_ids))
                if raise_exception:
                    raise ValueError(msg)
                return msg
        return [] if detailed else ''

    def check_all_air_boundaries_with_window(self, raise_exception=True, detailed=False):
        """Check there are no Rooms with windows and otherwise composed of AirBoundaries.

        This is a requirement for energy simulation since EnergyPlus will throw
        an error if it encounters a Room composed entirely of AirBoundaries except
        for one Face with a window.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if a Room composed entirely of AirBoundaries is found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        detailed = False if raise_exception else detailed
        msgs = []
        for room in self.host._rooms:
            non_ab = [f for f in room._faces if not isinstance(f.type, AirBoundary)]
            if all(len(f.apertures) > 0 for f in non_ab):
                if len(non_ab) != 0:
                    st_msg = 'is almost entirely composed of AirBoundary Faces with ' \
                        'the other {} Faces having Apertures'.format(len(non_ab))
                    msg = 'Room "{}" {}.\nIt should be merged with adjacent ' \
                        'rooms.'.format(room.full_id, st_msg)
                    msg = self.host._validation_message_child(
                        msg, room, detailed, '000207',
                        error_type='Room Composed Entirely of AirBoundaries')
                    msgs.append(msg)
        if detailed:
            return msgs
        full_msg = '\n'.join(msgs)
        if raise_exception and len(msgs) != 0:
            raise ValueError(full_msg)
        return full_msg

    def check_detailed_hvac_rooms(self, raise_exception=True, detailed=False):
        """Check that any rooms referenced within a DetailedHVAC exist in the model.

        This method will also check to make sure that two detailed HVACs do not
        reference the same room and that all rooms referencing a detailed HVAC
        have setpoints.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised if
                DetailedHVAC reference Rooms that are not in the Model. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        detailed = False if raise_exception else detailed
        all_err = []

        # get all of the HVACs and check Rooms for setpoints in the process
        hvacs = []
        for room in self.host.rooms:
            hvac = room.properties.energy._hvac
            if hvac is not None and isinstance(hvac, DetailedHVAC):
                if not self._instance_in_array(hvac, hvacs):
                    hvacs.append(hvac)
                if room.properties.energy.setpoint is None:
                    msg = 'Detailed HVAC "{}" is assigned to Room {}, which lacks a ' \
                        'thermostat setpoint specification.\nThis makes the model ' \
                        'un-simulate-able in EnergyPlus/OpenStudio.'.format(
                            hvac.display_name, room.full_id)
                    if detailed:
                        error_dict = {
                            'type': 'ValidationError',
                            'code': '020011',
                            'error_type': 'Room With HVAC Lacks Setpoint',
                            'extension_type': 'Energy',
                            'element_type': 'Room',
                            'element_id': [room.identifier],
                            'element_name': [room.display_name],
                            'message': msg
                        }
                        all_err.append(error_dict)
                    else:
                        all_err.append(msg)

        # gather a list of all the rooms and evaluate it against the HVACs
        room_ids = set(room.identifier for room in self.host.rooms)
        rooms_with_hvac = set()
        problem_hvacs, problem_rooms = [], []
        for hvac in hvacs:
            missing_rooms = []
            for zone in hvac.thermal_zones:
                if zone not in room_ids:
                    missing_rooms.append(zone)
                if zone in rooms_with_hvac:
                    problem_rooms.append(zone)
                rooms_with_hvac.add(zone)
            if len(missing_rooms) != 0:
                problem_hvacs.append((hvac, missing_rooms))

        # if missing room references were found, report them
        if len(problem_hvacs) != 0:
            for bad_hvac, missing_rooms in problem_hvacs:
                msg = 'DetailedHVAC "{}" is referencing the following Rooms that ' \
                    'are not in the Model:\n{}'.format(
                        bad_hvac.display_name, '\n'.join(missing_rooms))
                if detailed:
                    error_dict = {
                        'type': 'ValidationError',
                        'code': '020012',
                        'error_type': 'DetailedHVAC Rooms Not In Model',
                        'extension_type': 'Energy',
                        'element_type': 'HVAC',
                        'element_id': [bad_hvac.identifier],
                        'element_name': [bad_hvac.display_name],
                        'message': msg
                    }
                    all_err.append(error_dict)
                else:
                    all_err.append(msg)

        # if rooms were found with multiple HVAC references, report them
        if len(problem_rooms) != 0:
            room_objs = [room for room in self.host.rooms
                         if room.identifier in problem_rooms]
            for mult_hvac_room in room_objs:
                msg = 'Room {} is referenced by more than one detailed HVAC.'.format(
                        mult_hvac_room.full_id)
                if detailed:
                    error_dict = {
                        'type': 'ValidationError',
                        'code': '020013',
                        'error_type': 'Room Referenced by Multiple Detailed HVAC',
                        'extension_type': 'Energy',
                        'element_type': 'Room',
                        'element_id': [mult_hvac_room.identifier],
                        'element_name': [mult_hvac_room.display_name],
                        'message': msg
                    }
                    all_err.append(error_dict)
                else:
                    all_err.append(msg)

        # return any of the errors that were discovered
        if len(all_err) != 0:
            if raise_exception:
                raise ValueError('\n'.join(all_err))
            return all_err if detailed else '\n'.join(all_err)
        return [] if detailed else ''

    def check_interior_constructions_reversed(
            self, raise_exception=True, detailed=False):
        """Check that all interior constructions are in reversed order for paired faces.

        Note that, if there are missing adjacencies in the model, the message from
        this method will simply note this fact without reporting on mis-matched layers.

        Args:
            raise_exception: Boolean to note whether a ValueError should be raised
                if mis-matched interior construction layers are found. (Default: True).
            detailed: Boolean for whether the returned object is a detailed list of
                dicts with error info or a string with a message. (Default: False).

        Returns:
            A string with the message or a list with a dictionary if detailed is True.
        """
        detailed = False if raise_exception else detailed
        # first gather all interior faces in the model and their adjacent object
        adj_constr, base_objs, adj_ids = [], [], []
        for face in self.host.faces:
            if isinstance(face.boundary_condition, Surface):
                const = face.properties.energy.construction
                if not isinstance(const, AirBoundaryConstruction):
                    adj_constr.append(face.properties.energy.construction)
                    base_objs.append(face)
                    adj_ids.append(face.boundary_condition.boundary_condition_object)
        # next, get the adjacent objects
        try:
            adj_faces = self.host.faces_by_identifier(adj_ids)
        except ValueError as e:  # the model has missing adjacencies
            if detailed:  # the user will get a more detailed error in honeybee-core
                return []
            else:
                msg = 'Matching adjacent constructions could not be verified because ' \
                    'of missing adjacencies in the model.  \n{}'.format(e)
                if raise_exception:
                    raise ValueError(msg)
                return msg
        # loop through the adjacent face pairs and report if materials are not matched
        full_msgs, reported_items = [], set()
        for adj_c, base_f, adj_f in zip(adj_constr, base_objs, adj_faces):
            if (base_f.identifier, adj_f.identifier) in reported_items:
                continue
            try:
                rev_mat = tuple(reversed(adj_f.properties.energy.construction.materials))
            except AttributeError:
                rev_mat = None
            if not adj_c.materials == rev_mat:
                f_msg = 'Face "{}" with construction "{}" does not have material ' \
                    'layers matching in reversed order with its adjacent pair "{}" '\
                    'with construction "{}".'.format(
                            base_f.full_id,
                            base_f.properties.energy.construction.identifier,
                            adj_f.full_id,
                            adj_f.properties.energy.construction.identifier
                        )
                f_msg = self.host._validation_message_child(
                    f_msg, base_f, detailed, '020201', 'Energy',
                    error_type='Mismatched Adjacent Constructions')
                if detailed:
                    f_msg['element_id'].append(adj_f.identifier)
                    f_msg['element_name'].append(adj_f.display_name)
                    parents = []
                    rel_obj = adj_f
                    while getattr(rel_obj, '_parent', None) is not None:
                        rel_obj = getattr(rel_obj, '_parent')
                        par_dict = {
                            'parent_type': rel_obj.__class__.__name__,
                            'id': rel_obj.identifier,
                            'name': rel_obj.display_name
                        }
                        parents.append(par_dict)
                    f_msg['parents'].append(parents)
                full_msgs.append(f_msg)
                reported_items.add((adj_f.identifier, base_f.identifier))
        full_msg = full_msgs if detailed else '\n'.join(full_msgs)
        if raise_exception and len(full_msgs) != 0:
            raise ValueError(full_msg)
        return full_msg

    def reset_resource_ids(
            self, reset_materials=True, reset_constructions=True,
            reset_construction_sets=True, reset_schedules=True, reset_programs=True):
        """Reset the identifiers of energy resource objects in this Model.

        Note that this method may have unintended consequences if the resources
        assigned to this Model instance are also being used by another Model
        instance that exists in the current Python session. In this case,
        running this method will result in the resource identifiers of the
        other Model also being reset.

        This method is useful when human-readable names are needed when the model
        is exported to other formats like IDF and OSM. Cases of duplicate IDs
        resulting from non-unique names will be resolved by adding integers
        to the ends of the new IDs that are derived from the name.

        Args:
            reset_materials: Boolean to note whether the IDs of all materials in
                the model should be reset or kept. (Default: True).
            reset_constructions: Boolean to note whether the IDs of all constructions
                in the model should be reset or kept. (Default: True).
            reset_construction_sets: Boolean to note whether the IDs of all construction
                sets in the model should be reset or kept. (Default: True).
            reset_schedules: Boolean to note whether the IDs of all schedules
                in the model should be reset or kept. (Default: True).
            reset_programs: Boolean to note whether the IDs of all program
                types in the model should be reset or kept. (Default: True).

        Returns:
            A dictionary with the original identifiers of resources as keys and the
            edited resource objects as values. This can be used to set the identifiers
            of the objects back to the original value after this method has been
            run and any other routines have been performed. This will help prevent
            unintended consequences of changing the resource identifiers in the
            global resource library or in other Models that may be using the same
            resource object instances.
        """
        # set up the dictionaries used to check for uniqueness
        res_func = clean_and_number_ep_string
        mat_dict, con_dict, con_set_dict = {}, {}, {}
        sch_dict, sch_day_dict, prog_dict = {}, {}, {}
        resource_map = {}

        # change the identifiers of the materials
        if reset_materials:
            for mat in self.materials:
                mat.unlock()
                resource_map[mat.identifier] = mat
                mat.identifier = res_func(mat.display_name, mat_dict)
                mat.lock()

        # change the identifiers of the constructions
        if reset_constructions:
            for con in self.constructions:
                con.unlock()
                resource_map[con.identifier] = con
                con.identifier = res_func(con.display_name, con_dict)
                con.lock()

        # change the identifiers of the construction_sets
        if reset_construction_sets:
            for cs in self.construction_sets:
                cs.unlock()
                resource_map[cs.identifier] = cs
                cs.identifier = res_func(cs.display_name, con_set_dict)
                cs.lock()

        # change the identifiers of the schedules
        if reset_schedules:
            sch_skip = ('Seated Adult Activity', 'HumidNoLimit', 'DeHumidNoLimit')
            for sch in self.schedules:
                if sch.identifier in sch_skip:
                    continue
                sch.unlock()
                sch.identifier = res_func(sch.display_name, sch_dict)
                resource_map[sch.identifier] = sch
                if isinstance(sch, ScheduleRuleset):
                    for day_sch in sch.day_schedules:
                        day_sch.unlock()
                        resource_map[day_sch.identifier] = day_sch
                        day_sch.identifier = res_func(day_sch.display_name, sch_day_dict)
                        day_sch.lock()
                sch.lock()

        # change the identifiers of the program
        if reset_programs:
            for prg in self.program_types:
                prg.unlock()
                resource_map[prg.identifier] = prg
                prg.identifier = res_func(prg.display_name, prog_dict)
                prg.lock()

        return resource_map

    @staticmethod
    def restore_resource_ids(resource_map):
        """Restore the identifiers of resource objects after resetting them.

        This can be used to set the identifiers of the objects back to the original
        value after the reset_resource_ids() method was called. This will help prevent
        unintended consequences of changing the resource identifiers in the
        global resource library or in other Models that may be using the same
        resource object instances.

        Args:
            resource_map: A dictionary with the original identifiers of resources
                as keys and the edited resource objects as values. This type of
                dictionary is output from the reset_resource_ids method.
        """
        for orignal_id, res_obj in resource_map.items():
            res_obj.unlock()
            res_obj.identifier = orignal_id
            res_obj.lock()

    def apply_properties_from_dict(self, data):
        """Apply the energy properties of a dictionary to the host Model of this object.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
                Note that this dictionary must have ModelEnergyProperties in order
                for this method to successfully apply the energy properties.
        """
        assert 'energy' in data['properties'], \
            'Dictionary possesses no ModelEnergyProperties.'
        _, constructions, construction_sets, _, schedules, program_types, hvacs, shws = \
            self.load_properties_from_dict(data)

        # collect lists of energy property dictionaries
        room_e_dicts, face_e_dicts, shd_e_dicts, ap_e_dicts, dr_e_dicts = \
            model_extension_dicts(data, 'energy', [], [], [], [], [])

        # apply energy properties to objects using the energy property dictionaries
        for room, r_dict in zip(self.host.rooms, room_e_dicts):
            if r_dict is not None:
                room.properties.energy.apply_properties_from_dict(
                    r_dict, construction_sets, program_types, hvacs, shws,
                    schedules, constructions)
        for face, f_dict in zip(self.host.faces, face_e_dicts):
            if f_dict is not None:
                face.properties.energy.apply_properties_from_dict(f_dict, constructions)
        for aperture, a_dict in zip(self.host.apertures, ap_e_dicts):
            if a_dict is not None:
                aperture.properties.energy.apply_properties_from_dict(
                    a_dict, constructions)
        for door, d_dict in zip(self.host.doors, dr_e_dicts):
            if d_dict is not None:
                door.properties.energy.apply_properties_from_dict(
                    d_dict, constructions)
        all_shades = self.host.shades + self.host._shade_meshes
        for shade, s_dict in zip(all_shades, shd_e_dicts):
            if s_dict is not None:
                shade.properties.energy.apply_properties_from_dict(
                    s_dict, constructions, schedules)

        energy_prop = data['properties']['energy']
        # re-serialize the ventilation_simulation_control
        if 'ventilation_simulation_control' in energy_prop and \
                energy_prop['ventilation_simulation_control'] is not None:
            self.ventilation_simulation_control = \
                VentilationSimulationControl.from_dict(
                    energy_prop['ventilation_simulation_control'])
        # re-serialize the electric_load_center
        if 'electric_load_center' in energy_prop and \
                energy_prop['electric_load_center'] is not None:
            self.electric_load_center = \
                ElectricLoadCenter.from_dict(energy_prop['electric_load_center'])

    def to_dict(self):
        """Return Model energy properties as a dictionary."""
        base = {'energy': {'type': 'ModelEnergyProperties'}}

        # add all materials, constructions and construction sets to the dictionary
        schs = self._add_constr_type_objs_to_dict(base)

        # add all schedule type limits, schedules, program types, hvacs, shws to the dict
        self._add_sched_type_objs_to_dict(base, schs)

        # add ventilation_simulation_control
        base['energy']['ventilation_simulation_control'] = \
            self.ventilation_simulation_control.to_dict()
        # add electric_load_center
        base['energy']['electric_load_center'] = self.electric_load_center.to_dict()

        return base

    def add_autocal_properties_to_dict(self, data):
        """Add auto-calculated energy properties to a Model dictionary.

        This includes Room volumes, ceiling heights, and (in the case of Faces
        and Shades with holes) vertices. These properties are used
        in translation from Honeybee to OpenStudio to ensure that the properties
        in Honeybee are aligned with those in OSM, IDF, and gbXML.

        Note that the host model must be in Meters in order for the
        added properties to be in the correct units system.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
        """
        # check that the host model is in meters and add geometry properties
        assert self.host.units == 'Meters', 'Host model units must be Meters to use ' \
            'add_autocal_properties_to_dict. Not {}.'.format(self.host.units)
        # process rooms to add volume, ceiling height, and faces with holes
        if len(self.host.rooms) != 0:
            for room, room_dict in zip(self.host.rooms, data['rooms']):
                room_dict['ceiling_height'] = room.geometry.max.z - room.geometry.min.z
                room_dict['volume'] = room.volume
                self._add_shade_vertices(room, room_dict)
                for face, face_dict in zip(room._faces, room_dict['faces']):
                    self._add_shade_vertices(face, face_dict)
                    if face.geometry.has_holes:
                        ul_verts = face.upper_left_vertices
                        if isinstance(face.boundary_condition, Surface):
                            # check if the first vertex is the upper-left vertex
                            pt1, found_i = ul_verts[0], False
                            for pt in ul_verts[1:]:
                                if pt == pt1:
                                    found_i = True
                                    break
                            if found_i:  # reorder the vertices to have boundary first
                                ul_verts = reversed(ul_verts)
                        face_dict['geometry']['vertices'] = \
                            [[round(v, 3) for v in pt] for pt in ul_verts]
                    if len(face._apertures) != 0:
                        for ap, ap_dict in zip(face._apertures, face_dict['apertures']):
                            self._add_shade_vertices(ap, ap_dict)
                            if ap.properties.energy.construction.has_frame:
                                ap_dict['properties']['energy']['frame'] = \
                                    ap.properties.energy.construction.frame.identifier
                    if len(face._doors) != 0:
                        for dr, dr_dict in zip(face._doors, face_dict['doors']):
                            self._add_shade_vertices(dr, dr_dict)
                            if dr.properties.energy.construction.has_frame:
                                dr_dict['properties']['energy']['frame'] = \
                                    dr.properties.energy.construction.frame.identifier
        # process orphaned shades to add geometries with holes
        if len(self.host._orphaned_shades) != 0:
            for shd, shd_d in zip(self.host._orphaned_shades, data['orphaned_shades']):
                if shd.geometry.has_holes:
                    shd_d['geometry']['vertices'] = \
                        [pt.to_array() for pt in shd.upper_left_vertices]
        # process orphaned faces for punched geometry and aperture transmittance
        trans_orphaned = False
        if len(self.host._orphaned_faces) != 0:
            for shd, shd_d in zip(self.host._orphaned_faces, data['orphaned_faces']):
                shd_d['geometry']['vertices'] = \
                    [pt.to_array() for pt in shd.punched_vertices]
                if 'apertures' in shd_d:
                    for ap, ap_d in zip(shd._apertures, shd_d['apertures']):
                        ap_con = ap.properties.energy.construction
                        ap_d['transmit'] = str(round(ap_con.solar_transmittance, 3))
                        trans_orphaned = True
                if 'doors' in shd_d:
                    for dr, dr_d in zip(shd._doors, shd_d['doors']):
                        if dr.is_glass:
                            dr_con = dr.properties.energy.construction
                            dr_d['transmit'] = str(round(dr_con.solar_transmittance, 3))
                            trans_orphaned = True
        # add auto-generated transmittance schedules for transparent orphaned objects
        if len(self.host._orphaned_apertures) != 0:
            trans_orphaned = True
            ap_iter = zip(self.host._orphaned_apertures, data['orphaned_apertures'])
            for ap, ap_d in ap_iter:
                ap_con = ap.properties.energy.construction
                ap_d['transmit'] = str(round(ap_con.solar_transmittance, 3))
        if len(self.host._orphaned_doors) != 0:
            for dr, dr_d in zip(self.host._orphaned_doors, data['orphaned_doors']):
                if dr.is_glass:
                    dr_con = dr.properties.energy.construction
                    dr_d['transmit'] = str(round(dr_con.solar_transmittance, 3))
                    trans_orphaned = True
        # add transmittance schedules to the model if needed
        if trans_orphaned:
            for sched in self.orphaned_trans_schedules:
                data['properties']['energy']['schedules'].append(
                    sched.to_dict(abridged=True))
        # if there are any detailed HVACs, add the path to the ironbug installation
        # this is the only reliable way to pass the path to the honeybee-openstudio gem
        if folders.ironbug_exe is not None:
            for hvac_dict in data['properties']['energy']['hvacs']:
                if hvac_dict['type'] == 'DetailedHVAC':
                    hvac_dict['ironbug_exe'] = folders.ironbug_exe
        # CWM: there is a very weird bug in OpenStudio
        # program types cannot have the same name as the model (Building) in OpenStudio
        model_id = data['identifier']
        for prog in data['properties']['energy']['program_types']:
            if prog['identifier'] == model_id:
                data['identifier'] = '{}1'.format(data['identifier'])
                if 'display_name' in data and data['display_name'] is not None:
                    data['display_name'] = '{}1'.format(data['display_name'])
                break

    @staticmethod
    def _add_shade_vertices(obj, obj_dict):
        if len(obj._outdoor_shades) != 0:
            for shd, shd_dict in zip(obj._outdoor_shades, obj_dict['outdoor_shades']):
                if shd.geometry.has_holes:
                    shd_dict['geometry']['vertices'] = \
                        [pt.to_array() for pt in shd.upper_left_vertices]

    def simplify_window_constructions_in_dict(self, data):
        """Convert all window constructions in a model dictionary to SimpleGlazSys.

        This is useful when translating to gbXML and other formats that do not
        support layered window constructions.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
        """
        # add the window construction u-factors
        mat_dicts = data['properties']['energy']['materials']
        con_dicts = data['properties']['energy']['constructions']
        w_cons = (WindowConstruction, WindowConstructionShade, WindowConstructionDynamic)
        for i, con in enumerate(self.constructions):
            if isinstance(con, WindowConstruction):
                new_con = con.to_simple_construction()
            elif isinstance(con, WindowConstructionShade):
                new_con = con.window_construction.to_simple_construction()
            elif isinstance(con, WindowConstructionDynamic):
                new_con = con.window_construction.to_simple_construction()
            if isinstance(con, w_cons):
                con_dicts[i] = new_con.to_dict(abridged=True)
                mat_dicts.append(new_con.materials[0].to_dict())

    def duplicate(self, new_host=None):
        """Get a copy of this object.

        Args:
            new_host: A new Model object that hosts these properties.
                If None, the properties will be duplicated with the same host.
        """
        _host = new_host or self._host
        return ModelEnergyProperties(
            _host, self._ventilation_simulation_control.duplicate(),
            self.electric_load_center.duplicate())

    @staticmethod
    def load_properties_from_dict(data, skip_invalid=False):
        """Load model energy properties of a dictionary to Python objects.

        Loaded objects include Materials, Constructions, ConstructionSets,
        ScheduleTypeLimits, Schedules, and ProgramTypes.

        The function is called when re-serializing a Model object from a dictionary
        to load honeybee_energy objects into their Python object form before
        applying them to the Model geometry.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
                Note that this dictionary must have ModelEnergyProperties in order
                for this method to successfully load the energy properties.
            skip_invalid: A boolean to note whether objects that cannot be loaded
                should be ignored (True) or whether an exception should be raised
                about the invalid object (False). (Default: False).

        Returns:
            A tuple with eight elements

            -   materials -- A dictionary with identifiers of materials as keys
                and Python material objects as values.

            -   constructions -- A dictionary with identifiers of constructions
                as keys and Python construction objects as values.

            -   construction_sets -- A dictionary with identifiers of construction
                sets as keys and Python construction set objects as values.

            -   schedule_type_limits -- A dictionary with identifiers of schedule
                type limits as keys and Python schedule type limit objects as values.

            -   schedules -- A dictionary with identifiers of schedules as keys
                and Python schedule objects as values.

            -   program_types -- A dictionary with identifiers of program types
                as keys and Python program type objects as values.

            -   hvacs -- A dictionary with identifiers of HVAC systems as keys
                and Python HVACSystem objects as values.

            -   shws -- A dictionary with identifiers of SHW systems as keys
                and Python SHWSystem objects as values.
        """
        assert 'energy' in data['properties'], \
            'Dictionary possesses no ModelEnergyProperties.'

        # process all schedule type limits in the ModelEnergyProperties dictionary
        schedule_type_limits = {}
        if 'schedule_type_limits' in data['properties']['energy'] and \
                data['properties']['energy']['schedule_type_limits'] is not None:
            for t_lim in data['properties']['energy']['schedule_type_limits']:
                try:
                    schedule_type_limits[t_lim['identifier']] = \
                        ScheduleTypeLimit.from_dict(t_lim)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(t_lim, e)

        # process all schedules in the ModelEnergyProperties dictionary
        schedules = {}
        if 'schedules' in data['properties']['energy'] and \
                data['properties']['energy']['schedules'] is not None:
            for sched in data['properties']['energy']['schedules']:
                try:
                    if sched['type'] in SCHEDULE_TYPES:
                        schedules[sched['identifier']] = dict_to_schedule(sched)
                    else:
                        schedules[sched['identifier']] = dict_abridged_to_schedule(
                            sched, schedule_type_limits)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(sched, e)

        # process all materials in the ModelEnergyProperties dictionary
        materials = {}
        if 'materials' in data['properties']['energy'] and \
                data['properties']['energy']['materials'] is not None:
            for mat in data['properties']['energy']['materials']:
                try:
                    materials[mat['identifier']] = dict_to_material(mat)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(mat, e)

        # process all constructions in the ModelEnergyProperties dictionary
        constructions = {}
        if 'constructions' in data['properties']['energy'] and \
                data['properties']['energy']['constructions'] is not None:
            for cnstr in data['properties']['energy']['constructions']:
                try:
                    if cnstr['type'] in CONSTRUCTION_TYPES:
                        constructions[cnstr['identifier']] = dict_to_construction(cnstr)
                    else:
                        constructions[cnstr['identifier']] = \
                            dict_abridged_to_construction(cnstr, materials, schedules)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(cnstr, e)

        # process all construction sets in the ModelEnergyProperties dictionary
        construction_sets = {}
        if 'construction_sets' in data['properties']['energy'] and \
                data['properties']['energy']['construction_sets'] is not None:
            for c_set in data['properties']['energy']['construction_sets']:
                try:
                    if c_set['type'] == 'ConstructionSet':
                        construction_sets[c_set['identifier']] = \
                            ConstructionSet.from_dict(c_set)
                    else:
                        construction_sets[c_set['identifier']] = \
                            ConstructionSet.from_dict_abridged(c_set, constructions)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(c_set, e)

        # process all ProgramType in the ModelEnergyProperties dictionary
        program_types = {}
        if 'program_types' in data['properties']['energy'] and \
                data['properties']['energy']['program_types'] is not None:
            for p_typ in data['properties']['energy']['program_types']:
                try:
                    if p_typ['type'] == 'ProgramType':
                        program_types[p_typ['identifier']] = ProgramType.from_dict(p_typ)
                    else:
                        program_types[p_typ['identifier']] = \
                            ProgramType.from_dict_abridged(p_typ, schedules)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(p_typ, e)

        # process all HVAC systems in the ModelEnergyProperties dictionary
        hvacs = {}
        if 'hvacs' in data['properties']['energy'] and \
                data['properties']['energy']['hvacs'] is not None:
            for hvac in data['properties']['energy']['hvacs']:
                hvac_class = HVAC_TYPES_DICT[hvac['type'].replace('Abridged', '')]
                try:
                    hvacs[hvac['identifier']] = \
                        hvac_class.from_dict_abridged(hvac, schedules)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(hvac, e)

        # process all SHW systems in the ModelEnergyProperties dictionary
        shws = {}
        if 'shws' in data['properties']['energy'] and \
                data['properties']['energy']['shws'] is not None:
            for shw in data['properties']['energy']['shws']:
                try:
                    shws[shw['identifier']] = SHWSystem.from_dict(shw)
                except Exception as e:
                    if not skip_invalid:
                        invalid_dict_error(shw, e)

        return materials, constructions, construction_sets, schedule_type_limits, \
            schedules, program_types, hvacs, shws

    @staticmethod
    def dump_properties_to_dict(
            materials=None, constructions=None, construction_sets=None,
            schedule_type_limits=None, schedules=None, program_types=None,
            hvacs=None, shws=None):
        """Get a ModelEnergyProperties dictionary from arrays of Python objects.

        Args:
            materials: A list or tuple of energy material objects.
            constructions:  A list or tuple of construction objects.
            construction_sets:  A list or tuple of construction set objects.
            schedule_type_limits:  A list or tuple of schedule type limit objects.
            schedules:  A list or tuple of schedule objects.
            program_types:  A list or tuple of program type objects.
            hvacs: A list or tuple of HVACSystem objects.
            shws:  A list or tuple of SHWSystem objects.

        Returns:
            data: A dictionary representation of ModelEnergyProperties. Note that
                all objects in this dictionary will follow the abridged schema.
        """
        # process the input schedules and type limits
        type_lim = [] if schedule_type_limits is None else list(schedule_type_limits)
        scheds = [] if schedules is None else list(schedules)

        # process the program types
        all_progs, misc_p_scheds = [], []
        if program_types is not None:
            for program in program_types:
                all_progs.append(program)
                misc_p_scheds.extend(program.schedules)

        # process the materials, constructions, and construction sets
        all_m = [] if materials is None else list(materials)
        all_c = [] if constructions is None else list(constructions)
        all_con_sets = [] if construction_sets is None else list(construction_sets)
        for con_set in all_con_sets:
            all_c.extend(con_set.modified_constructions)

        # get schedules assigned in constructions
        misc_c_scheds = []
        for constr in all_c:
            if isinstance(constr, (WindowConstructionShade, WindowConstructionDynamic)):
                misc_c_scheds.append(constr.schedule)
            elif isinstance(constr, AirBoundaryConstruction):
                misc_c_scheds.append(constr.air_mixing_schedule)

        # process the HVAC and SHW systems
        all_hvac = [] if hvacs is None else list(hvacs)
        all_shw = [] if shws is None else list(shws)
        misc_hvac_scheds = []
        for hvac_obj in all_hvac:
            misc_hvac_scheds.extend(hvac_obj.schedules)

        # get sets of unique objects
        all_scheds = set(scheds + misc_p_scheds + misc_c_scheds + misc_hvac_scheds)
        sched_tl = [sch.schedule_type_limit for sch in all_scheds
                    if sch.schedule_type_limit is not None]
        all_typ_lim = set(type_lim + sched_tl)
        all_cons = set(all_c)
        misc_c_mats = []
        for constr in all_cons:
            try:
                misc_c_mats.extend(constr.materials)
                if constr.has_frame:
                    misc_c_mats.append(constr.frame)
                if constr.has_shade:
                    if constr.is_switchable_glazing:
                        misc_c_mats.append(constr.switched_glass_material)
                    if constr.shade_location == 'Between':
                        materials.append(constr.window_construction.materials[-2])
            except AttributeError:  # not a construction with materials
                pass
        all_mats = set(all_m + misc_c_mats)

        # add all object dictionaries into one object
        data = {'type': 'ModelEnergyProperties'}
        data['schedule_type_limits'] = [tl.to_dict() for tl in all_typ_lim]
        data['schedules'] = [sch.to_dict(abridged=True) for sch in all_scheds]
        data['program_types'] = [pro.to_dict(abridged=True) for pro in all_progs]
        data['materials'] = [m.to_dict() for m in all_mats]
        data['constructions'] = []
        for con in all_cons:
            try:
                data['constructions'].append(con.to_dict(abridged=True))
            except TypeError:  # no abridged option
                data['constructions'].append(con.to_dict())
        data['construction_sets'] = [cs.to_dict(abridged=True) for cs in all_con_sets]
        data['hvacs'] = [hv.to_dict(abridged=True) for hv in all_hvac]
        data['shws'] = [sw.to_dict(abridged=True) for sw in all_shw]
        return data

    @staticmethod
    def reset_resource_ids_in_dict(
            data, add_uuid=False, reset_materials=True, reset_constructions=True,
            reset_construction_sets=True, reset_schedules=True, reset_programs=True):
        """Reset the identifiers of energy resource objects in a Model dictionary.

        This is useful when human-readable names are needed when the model is
        exported to other formats like IDF and OSM and the uniqueness of the
        identifiers is less of a concern.

        Args:
            data: A dictionary representation of an entire honeybee-core Model.
                Note that this dictionary must have ModelEnergyProperties in order
                for this method to successfully edit the energy properties.
            add_uuid: Boolean to note whether newly-generated resource object IDs
                should be derived only from a cleaned display_name (False) or
                whether this new ID should also have a unique set of 8 characters
                appended to it to guarantee uniqueness. (Default: False).
            reset_materials: Boolean to note whether the IDs of all materials in
                the model should be reset or kept. (Default: True).
            reset_constructions: Boolean to note whether the IDs of all constructions
                in the model should be reset or kept. (Default: True).
            reset_construction_sets: Boolean to note whether the IDs of all construction
                sets in the model should be reset or kept. (Default: True).
            reset_schedules: Boolean to note whether the IDs of all schedules
                in the model should be reset or kept. (Default: True).
            reset_programs: Boolean to note whether the IDs of all program
                types in the model should be reset or kept. (Default: True).

        Returns:
            A new Model dictionary with the resource identifiers reset. All references
            to the reset resources will be correct and valid in the resulting dictionary,
            assuming that the input is valid.
        """
        model = Model.from_dict(data)
        materials, constructions, construction_sets, schedule_type_limits, \
            schedules, program_types, _, _ = \
            model.properties.energy.load_properties_from_dict(data)
        res_func = clean_and_id_ep_string if add_uuid else clean_ep_string

        # change the identifiers of the materials
        if reset_materials:
            model_mats = set()
            for mat in model.properties.energy.materials:
                mat.unlock()
                old_id, new_id = mat.identifier, res_func(mat.display_name)
                mat.identifier = new_id
                materials[old_id].unlock()
                materials[old_id].identifier = new_id
                model_mats.add(old_id)
            for old_id, mat in materials.items():
                if old_id not in model_mats:
                    mat.unlock()
                    mat.identifier = res_func(mat.display_name)

        # change the identifiers of the constructions
        if reset_constructions:
            model_cons = set()
            for con in model.properties.energy.constructions:
                con.unlock()
                old_id, new_id = con.identifier, res_func(con.display_name)
                con.identifier = new_id
                constructions[old_id].unlock()
                constructions[old_id].identifier = new_id
                model_cons.add(old_id)
            for old_id, con in constructions.items():
                if old_id not in model_cons:
                    con.unlock()
                    con.identifier = res_func(con.display_name)

        # change the identifiers of the construction_sets
        if reset_construction_sets:
            model_cs = set()
            for cs in model.properties.energy.construction_sets:
                cs.unlock()
                old_id, new_id = cs.identifier, res_func(cs.display_name)
                cs.identifier = new_id
                construction_sets[old_id].unlock()
                construction_sets[old_id].identifier = new_id
                model_cs.add(old_id)
            for old_id, cs in construction_sets.items():
                if old_id not in model_cs:
                    cs.unlock()
                    cs.identifier = res_func(cs.display_name)

        # change the identifiers of the schedules
        if reset_schedules:
            sch_skip = ('Seated Adult Activity', 'HumidNoLimit', 'DeHumidNoLimit')
            model_sch = set()
            for sch in model.properties.energy.schedules:
                if sch.identifier in sch_skip:
                    schedules[sch.identifier] = sch
                    model_sch.add(sch.identifier)
                    continue
                sch.unlock()
                old_id, new_id = sch.identifier, res_func(sch.display_name)
                sch.identifier = new_id
                schedules[old_id].unlock()
                schedules[old_id].identifier = new_id
                model_sch.add(old_id)
                if isinstance(sch, ScheduleRuleset):
                    for day_sch in sch.day_schedules:
                        day_sch.identifier = res_func(day_sch.display_name)
                    for day_sch in schedules[old_id].day_schedules:
                        day_sch.identifier = res_func(day_sch.display_name)
            for old_id, sch in schedules.items():
                if old_id not in model_sch:
                    sch.unlock()
                    sch.identifier = res_func(sch.display_name)
                    if isinstance(sch, ScheduleRuleset):
                        for day_sch in schedules[old_id].day_schedules:
                            day_sch.identifier = res_func(day_sch.display_name)

        # change the identifiers of the program
        if reset_programs:
            model_prg = set()
            for prg in model.properties.energy.program_types:
                prg.unlock()
                old_id, new_id = prg.identifier, res_func(prg.display_name)
                prg.identifier = new_id
                program_types[old_id].unlock()
                program_types[old_id].identifier = new_id
                model_prg.add(old_id)
            for old_id, prg in program_types.items():
                if old_id not in model_prg:
                    prg.unlock()
                    prg.identifier = res_func(prg.display_name)

        # create the model dictionary and update any unreferenced resources
        model_dict = model.to_dict()
        me_props = model_dict['properties']['energy']
        me_props['materials'] = [mat.to_dict() for mat in materials.values()]
        me_props['constructions'] = []
        for cnst in constructions.values():
            try:
                me_props['constructions'].append(cnst.to_dict(abridged=True))
            except TypeError:  # ShadeConstruction
                me_props['constructions'].append(cnst.to_dict())
        me_props['construction_sets'] = \
            [cs.to_dict(abridged=True) for cs in construction_sets.values()]
        me_props['schedule_type_limits'] = \
            [stl.to_dict() for stl in schedule_type_limits.values()]
        me_props['schedules'] = [sc.to_dict(abridged=True) for sc in schedules.values()]
        me_props['program_types'] = \
            [p.to_dict(abridged=True) for p in program_types.values()]
        return model_dict

    def _add_constr_type_objs_to_dict(self, base):
        """Add materials, constructions and construction sets to a base dictionary.

        Args:
            base: A base dictionary for a Honeybee Model.

        Returns:
            A list of of schedules that are assigned to the constructions.
        """
        # add the global construction set to the dictionary
        gs = self.global_construction_set.to_dict(abridged=True, none_for_defaults=False)
        gs['type'] = 'GlobalConstructionSet'
        del gs['identifier']
        g_constr = self.global_construction_set.constructions_unique
        g_materials = []
        for constr in g_constr:
            try:
                g_materials.extend(constr.materials)
            except AttributeError:
                pass  # ShadeConstruction or AirBoundaryConstruction
        gs['context_construction'] = generic_context.identifier
        gs['constructions'] = [generic_context.to_dict()]
        for cnst in g_constr:
            try:
                gs['constructions'].append(cnst.to_dict(abridged=True))
            except TypeError:  # ShadeConstruction
                gs['constructions'].append(cnst.to_dict())
        gs['materials'] = [mat.to_dict() for mat in set(g_materials)]
        base['energy']['global_construction_set'] = gs

        # add all ConstructionSets to the dictionary
        base['energy']['construction_sets'] = []
        construction_sets = self.construction_sets
        for cnstr_set in construction_sets:
            base['energy']['construction_sets'].append(cnstr_set.to_dict(abridged=True))

        # add all unique Constructions to the dictionary
        room_constrs = []
        for cnstr_set in construction_sets:
            room_constrs.extend(cnstr_set.modified_constructions_unique)
        mass_constrs = []
        for room in self.host.rooms:
            for int_mass in room.properties.energy._internal_masses:
                constr = int_mass.construction
                if not self._instance_in_array(constr, mass_constrs):
                    mass_constrs.append(constr)
        all_constrs = room_constrs + mass_constrs + \
            self.face_constructions + self.shade_constructions
        constructions = list(set(all_constrs))
        base['energy']['constructions'] = []
        for cnst in constructions:
            try:
                base['energy']['constructions'].append(cnst.to_dict(abridged=True))
            except TypeError:  # ShadeConstruction
                base['energy']['constructions'].append(cnst.to_dict())

        # add all unique Materials to the dictionary
        materials = []
        for cnstr in constructions:
            try:
                materials.extend(cnstr.materials)
                if cnstr.has_frame:
                    materials.append(cnstr.frame)
                if isinstance(cnstr, WindowConstructionShade):
                    if cnstr.is_switchable_glazing:
                        materials.append(cnstr.switched_glass_material)
                    if cnstr.shade_location == 'Between':
                        materials.append(cnstr.window_construction.materials[-2])
            except AttributeError:
                pass  # ShadeConstruction
        base['energy']['materials'] = [mat.to_dict() for mat in set(materials)]

        # extract all of the schedules from the constructions
        schedules = []
        for constr in constructions:
            if isinstance(constr, AirBoundaryConstruction):
                self._check_and_add_schedule(constr.air_mixing_schedule, schedules)
            elif isinstance(constr, WindowConstructionShade):
                if constr.schedule is not None:
                    self._check_and_add_schedule(constr.schedule, schedules)
            elif isinstance(constr, WindowConstructionDynamic):
                self._check_and_add_schedule(constr.schedule, schedules)
        return schedules

    def _add_sched_type_objs_to_dict(self, base, schs):
        """Add type limits, schedules, program types, hvacs, shws to a base dictionary.

        Args:
            base: A base dictionary for a Honeybee Model.
            schs: A list of additional schedules to be serialized to the
                base dictionary.
        """
        # add all unique hvacs to the dictionary
        hvacs = self.hvacs
        base['energy']['hvacs'] = []
        for hvac in hvacs:
            base['energy']['hvacs'].append(hvac.to_dict(abridged=True))

        # add all unique shws to the dictionary
        base['energy']['shws'] = [shw.to_dict() for shw in self.shws]

        # add all unique program types to the dictionary
        program_types = self.program_types
        base['energy']['program_types'] = []
        for p_type in program_types:
            base['energy']['program_types'].append(p_type.to_dict(abridged=True))

        # add all unique Schedules to the dictionary
        p_type_scheds = []
        for p_type in program_types:
            for sched in p_type.schedules:
                self._check_and_add_schedule(sched, p_type_scheds)
        hvac_scheds = []
        for hvac in hvacs:
            for sched in hvac.schedules:
                self._check_and_add_schedule(sched, hvac_scheds)
        all_scheds = hvac_scheds + p_type_scheds + self.room_schedules + \
            self.shade_schedules + schs
        schedules = list(set(all_scheds))
        base['energy']['schedules'] = []
        for sched in schedules:
            base['energy']['schedules'].append(sched.to_dict(abridged=True))

        # add all unique ScheduleTypeLimits to the dictionary
        type_limits = []
        for sched in schedules:
            t_lim = sched.schedule_type_limit
            if t_lim is not None and not self._instance_in_array(t_lim, type_limits):
                type_limits.append(t_lim)
        base['energy']['schedule_type_limits'] = \
            [s_typ.to_dict() for s_typ in set(type_limits)]

    def _check_and_add_obj_construction(self, obj, constructions):
        """Check if a construction is assigned to an object and add it to a list."""
        constr = obj.properties.energy._construction
        if constr is not None:
            if not self._instance_in_array(constr, constructions):
                constructions.append(constr)

    def _check_and_add_obj_construction_inc_parent(self, obj, constructions):
        """Check if a construction is assigned to an object and add it to a list."""
        constr = obj.properties.energy.construction
        if not self._instance_in_array(constr, constructions):
            constructions.append(constr)

    def _check_and_add_shade_schedule(self, obj, schedules):
        """Check if a schedule is assigned to a shade and add it to a list."""
        sched = obj.properties.energy._transmittance_schedule
        if sched is not None:
            if not self._instance_in_array(sched, schedules):
                schedules.append(sched)

    def _check_and_add_schedule(self, sched, schedules):
        """Check if a schedule is in a list and add it if not."""
        if not self._instance_in_array(sched, schedules):
            schedules.append(sched)

    def _check_and_add_obj_transmit(self, hb_obj, transmittances):
        """Check and add the transmittance of a honeybee object to a set."""
        constr = hb_obj.properties.energy.construction
        transmittances.add(round(constr.solar_transmittance, 3))

    def _assign_room_modifier_sets(self, unique_mod_sets):
        """Assign modifier sets to rooms using a dictionary of unique modifier sets."""
        for room in self._host.rooms:
            room.properties.radiance.modifier_set = \
                unique_mod_sets[room.properties.energy.construction_set.identifier]

    def _assign_face_modifiers(self, unique_mods):
        """Assign modifiers to faces, apertures, doors and shades using a dictionary."""
        for room in self._host.rooms:
            for face in room.faces:  # check Face constructions
                self._assign_obj_modifier_shade(face, unique_mods)
                for ap in face.apertures:  # check  Aperture constructions
                    self._assign_obj_modifier_shade(ap, unique_mods)
                for dr in face.doors:  # check  Door constructions
                    self._assign_obj_modifier_shade(dr, unique_mods)
            for shade in room.shades:
                self._assign_obj_modifier(shade, unique_mods)
        for face in self.host.orphaned_faces:  # check orphaned Face constructions
            self._assign_obj_modifier_shade(face, unique_mods)
            for ap in face.apertures:  # check Aperture constructions
                self._assign_obj_modifier_shade(ap, unique_mods)
            for dr in face.doors:  # check Door constructions
                self._assign_obj_modifier_shade(dr, unique_mods)
        for ap in self.host.orphaned_apertures:  # check orphaned Aperture constructions
            self._assign_obj_modifier_shade(ap, unique_mods)
        for dr in self.host.orphaned_doors:  # check orphaned Door constructions
            self._assign_obj_modifier_shade(dr, unique_mods)
        for shade in self.host.orphaned_shades:
            self._assign_obj_modifier(shade, unique_mods)
        for sm in self.host.shade_meshes:
            self._assign_obj_modifier(sm, unique_mods)

    def _assign_obj_modifier_shade(self, obj, unique_mods):
        """Check if an object or child shades have a unique constr and assign a modifier.
        """
        self._assign_obj_modifier(obj, unique_mods)
        for shade in obj.shades:
            self._assign_obj_modifier(shade, unique_mods)

    @staticmethod
    def _always_on_schedule():
        """Get the Always On schedule."""
        return always_on

    @staticmethod
    def _assign_obj_modifier(obj, unique_mods):
        """Check if an object has a unique construction and assign a modifier."""
        if obj.properties.energy._construction is not None:
            obj.properties.radiance.modifier = \
                unique_mods[obj.properties.energy._construction.identifier]

    @staticmethod
    def _instance_in_array(object_instance, object_array):
        """Check if a specific object instance is already in an array.

        This can be much faster than  `if object_instance in object_array`
        when you expect to be testing a lot of the same instance of an object for
        inclusion in an array since the builtin method uses an == operator to
        test inclusion.
        """
        for val in object_array:
            if val is object_instance:
                return True
        return False

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Model Energy Properties: [host: {}]'.format(self.host.display_name)
