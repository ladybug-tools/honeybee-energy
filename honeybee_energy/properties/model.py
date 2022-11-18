# coding=utf-8
"""Model Energy Properties."""
try:
    from itertools import izip as zip  # python 2
except ImportError:
    pass   # python 3

from ladybug_geometry.geometry2d.pointvector import Vector2D
from honeybee.boundarycondition import Outdoors, Surface, boundary_conditions
from honeybee.facetype import AirBoundary, face_types
from honeybee.extensionutil import model_extension_dicts
from honeybee.checkdup import check_duplicate_identifiers
from honeybee.typing import invalid_dict_error
from honeybee.face import Face

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
from ..hvac import HVAC_TYPES_DICT
from ..shw import SHWSystem
from ..ventcool.simulation import VentilationSimulationControl

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
    """

    def __init__(self, host, ventilation_simulation_control=None):
        """Initialize Model energy properties."""
        self._host = host
        self.ventilation_simulation_control = ventilation_simulation_control

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
                if isinstance(constr, WindowConstructionShade) \
                        and constr.is_switchable_glazing:
                    materials.append(constr.switched_glass_material)
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
        """Set the construction of exterior Apertures in Walls facing a given orientation.

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
        # loop thorugh the faces and create new offset exterior ones
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
        # perform checks for key honeybee model schema rules
        msgs.append(self.check_duplicate_material_identifiers(False, detailed))
        msgs.append(self.check_duplicate_construction_identifiers(False, detailed))
        msgs.append(self.check_duplicate_construction_set_identifiers(False, detailed))
        msgs.append(
            self.check_duplicate_schedule_type_limit_identifiers(False, detailed))
        msgs.append(self.check_duplicate_schedule_identifiers(False, detailed))
        msgs.append(self.check_duplicate_program_type_identifiers(False, detailed))
        msgs.append(self.check_duplicate_hvac_identifiers(False, detailed))
        msgs.append(self.check_duplicate_shw_identifiers(False, detailed))
        msgs.append(self.check_shw_rooms_in_model(False, detailed))
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
            self.materials, raise_exception, 'Energy Material',
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
                        'element_type': 'SHWSystem',
                        'element_id': shw_sys.identifier,
                        'element_name': shw_sys.display_name,
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
                        'element_type': 'Energy Material',
                        'element_id': v_mat.identifier,
                        'element_name': v_mat.display_name,
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
        adj_constr, adj_ids = [], []
        for face in self.host.faces:
            if isinstance(face.boundary_condition, Surface):
                const = face.properties.energy.construction
                if not isinstance(const, AirBoundaryConstruction):
                    adj_constr.append(face.properties.energy.construction)
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
        full_msgs = []
        for adj_c, adj_f in zip(adj_constr, adj_faces):
            try:
                rev_mat = tuple(reversed(adj_f.properties.energy.construction.materials))
            except AttributeError:
                rev_mat = None
            if not adj_c.materials == rev_mat:
                f_msg = 'Face "{}" with construction "{}" does not have material ' \
                    'layers matching in reversed order with its adjacent pair.'.format(
                        adj_f.full_id, adj_f.properties.energy.construction.identifier)
                f_msg = self.host._validation_message_child(
                    f_msg, adj_f, detailed, '020201', 'Energy',
                    error_type='Mismatched Adjacent Constructions')
                full_msgs.append(f_msg)
        full_msg = full_msgs if detailed else '\n'.join(full_msgs)
        if raise_exception and len(full_msgs) != 0:
            raise ValueError(full_msg)
        return full_msg

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
        for shade, s_dict in zip(self.host.shades, shd_e_dicts):
            if s_dict is not None:
                shade.properties.energy.apply_properties_from_dict(
                    s_dict, constructions, schedules)
        for aperture, a_dict in zip(self.host.apertures, ap_e_dicts):
            if a_dict is not None:
                aperture.properties.energy.apply_properties_from_dict(
                    a_dict, constructions)
        for door, d_dict in zip(self.host.doors, dr_e_dicts):
            if d_dict is not None:
                door.properties.energy.apply_properties_from_dict(
                    d_dict, constructions)

        # re-serialize the ventilation_simulation_control
        energy_prop = data['properties']['energy']
        if 'ventilation_simulation_control' in energy_prop and \
                energy_prop['ventilation_simulation_control'] is not None:
            self.ventilation_simulation_control = \
                VentilationSimulationControl.from_dict(
                    energy_prop['ventilation_simulation_control'])

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
            _host, self._ventilation_simulation_control.duplicate())

    @staticmethod
    def load_properties_from_dict(data):
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
                    invalid_dict_error(sched, e)

        # process all materials in the ModelEnergyProperties dictionary
        materials = {}
        if 'materials' in data['properties']['energy'] and \
                data['properties']['energy']['materials'] is not None:
            for mat in data['properties']['energy']['materials']:
                try:
                    materials[mat['identifier']] = dict_to_material(mat)
                except Exception as e:
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
                    invalid_dict_error(hvac, e)

        # process all SHW systems in the ModelEnergyProperties dictionary
        shws = {}
        if 'shws' in data['properties']['energy'] and \
                data['properties']['energy']['shws'] is not None:
            for shw in data['properties']['energy']['shws']:
                try:
                    shws[shw['identifier']] = SHWSystem.from_dict(shw)
                except Exception as e:
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
                if isinstance(cnstr, WindowConstructionShade) \
                        and cnstr.is_switchable_glazing:
                    materials.append(cnstr.switched_glass_material)
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
