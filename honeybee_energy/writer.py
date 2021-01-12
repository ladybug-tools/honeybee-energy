# coding=utf-8
"""Methods to write to idf."""
from .config import folders

from honeybee.room import Room
from honeybee.face import Face
from honeybee.boundarycondition import Outdoors, Surface, Ground
from honeybee.facetype import RoofCeiling, AirBoundary

import os
try:
    from itertools import izip as zip  # python 2
except ImportError:
    xrange = range  # python 3


def generate_idf_string(object_type, values, comments=None):
    """Get an IDF string representation of an EnergyPlus object.

    Args:
        object_type: Text representing the expected start of the IDF object.
            (ie. WindowMaterial:Glazing).
        values: A list of values associated with the EnergyPlus object in the
            order that they are supposed to be written to IDF format.
        comments: A list of text comments with the same length as the values.
            If None, no comments will be written into the object.

    Returns:
        ep_str -- Am EnergyPlus IDF string representing a single object.
    """
    if comments is not None:
        space_count = tuple((25 - len(str(n))) for n in values)
        spaces = tuple(s_c * ' ' if s_c > 0 else ' ' for s_c in space_count)
        body_str = '\n '.join('{},{}!- {}'.format(val, spc, com) for val, spc, com in
                              zip(values[:-1], spaces[:-1], comments[:-1]))
        ep_str = '{},\n {}'.format(object_type, body_str)
        if len(values) == 1:  # ensure we don't have an extra line break
            ep_str = ''.join(
                (ep_str, '{};{}!- {}'.format(values[-1], spaces[-1], comments[-1])))
        else:  # include an extra line break
            end_str = '\n {};{}!- {}'.format(values[-1], spaces[-1], comments[-1]) \
                if comments[-1] != '' else '\n {};'.format(values[-1])
            ep_str = ''.join((ep_str, end_str))
    else:
        body_str = '\n '.join('{},'.format(val) for val in values[:-1])
        ep_str = '{},\n {}'.format(object_type, body_str)
        if len(values) == 1:  # ensure we don't have an extra line break
            ep_str = ''.join((ep_str, '{};'.format(values[-1])))
        else:  # include an extra line break
            ep_str = ''.join((ep_str, '\n {};'.format(values[-1])))
    return ep_str


def shade_to_idf(shade):
    """Generate an IDF string representation of a Shade.

    Note that the resulting string will possess both the Shading object
    as well as a ShadingProperty:Reflectance if the Shade's construction
    is not in line with the EnergyPlus default of 0.2 reflectance.

    Args:
        shade: A honeybee Shade for which an IDF representation will be returned.
    """
    # create the Shading:Detailed IDF string
    trans_sched = shade.properties.energy.transmittance_schedule.identifier if \
        shade.properties.energy.transmittance_schedule is not None else ''
    if shade.has_parent and not isinstance(shade.parent, Room):
        if isinstance(shade.parent, Face):
            base_srf = shade.parent.identifier
        else:  # Aperture or Door for parent
            try:
                base_srf = shade.parent.parent.identifier
            except AttributeError:
                base_srf = 'unknown'  # aperture without a parent (not simulate-able)
        values = (shade.identifier,
                  base_srf,
                  trans_sched,
                  len(shade.vertices),
                  ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z)
                              for v in shade.upper_left_vertices))
        comments = ('name',
                    'base surface',
                    'transmittance schedule',
                    'number of vertices',
                    '')
        shade_str = generate_idf_string('Shading:Zone:Detailed', values, comments)
    else:
        values = (shade.identifier,
                  trans_sched,
                  len(shade.vertices),
                  ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z)
                              for v in shade.upper_left_vertices))
        comments = ('name',
                    'transmittance schedule',
                    'number of vertices',
                    '')
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)

    # create the ShadingProperty:Reflectance IDF string if construction is not default
    construction = shade.properties.energy.construction
    if construction.is_default:
        return shade_str
    else:
        values = (shade.identifier,
                  construction.solar_reflectance,
                  construction.visible_reflectance)
        comments = ('shading surface name',
                    'diffuse solar reflectance',
                    'diffuse visible reflectance')
        if construction.is_specular:
            values = values + (1, construction.identifier)
            comments = comments + ('glazed fraction of surface', 'glazing construction')
        constr_str = generate_idf_string('ShadingProperty:Reflectance', values, comments)
    return '\n\n'.join((shade_str, constr_str))


def door_to_idf(door):
    """Generate an IDF string representation of a Door.

    Note that the resulting string does not include full construction definitions
    but it will include a WindowShadingControl definition if a WindowConstructionShade
    is assigned to the door. It will also include a ventilation object if the door
    has a VentilationOpening object assigned to it.

    Also note that shades assigned to the Door are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Door.shades, and call the to.idf method on each one.

    Args:
        door: A honeybee Door for which an IDF representation will be returned.
    """
    # set defaults for missing fields
    door_bc_obj = door.boundary_condition.boundary_condition_object if \
        isinstance(door.boundary_condition, Surface) else ''
    construction = door.properties.energy.construction
    constr_name = construction.identifier if not construction.has_shade \
        else construction.window_construction.identifier
    if door.has_parent:
        parent_face = door.parent.identifier
        parent_room = door.parent.parent.identifier if door.parent.has_parent \
            else 'unknown'
    else:
        parent_room = parent_face = 'unknown'

    # create the fenestration surface string
    values = (door.identifier,
              'Door' if not door.is_glass else 'GlassDoor',
              constr_name,
              parent_face,
              door_bc_obj,
              door.boundary_condition.view_factor,
              '',  # TODO: Implement Frame and Divider objects on WindowConstructions
              '1',
              len(door.vertices),
              ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z)
                          for v in door.upper_left_vertices))
    comments = ('name',
                'surface type',
                'construction name',
                'building surface name',
                'boundary condition object',
                'view factor to ground',
                'frame and divider name',
                'multiplier',
                'number of vertices',
                '')
    fen_str = generate_idf_string('FenestrationSurface:Detailed', values, comments)

    # create the WindowShadingControl object if it is needed
    if construction.has_shade:
        shd_prop_str = construction.to_shading_control_idf(door.identifier, parent_room)
        fen_str = '\n\n'.join((fen_str, shd_prop_str))

    # create the VentilationOpening object if it is needed
    if door.properties.energy.vent_opening is not None:
        try:
            vent_str = door.properties.energy.vent_opening.to_idf()
            fen_str = '\n\n'.join((fen_str, vent_str))
        except AssertionError:  # door does not have a parent room
            pass
    return fen_str


def aperture_to_idf(aperture):
    """Generate an IDF string representation of an Aperture.

    Note that the resulting string does not include full construction definitions
    but it will include a WindowShadingControl definition if a WindowConstructionShade
    is assigned to the aperture. It will also include a ventilation object if the
    aperture has a VentilationOpening object assigned to it.

    Also note that shades assigned to the Aperture are not included in the resulting
    string. To write these objects into a final string, you must loop through the
    Aperture.shades, and call the to.idf method on each one.

    Args:
        aperture: A honeybee Aperture for which an IDF representation will be returned.
    """
    # set defaults for missing fields
    ap_bc_obj = aperture.boundary_condition.boundary_condition_object if \
        isinstance(aperture.boundary_condition, Surface) else ''
    construction = aperture.properties.energy.construction
    constr_name = construction.identifier if not construction.has_shade \
        else construction.window_construction.identifier
    if aperture.has_parent:
        parent_face = aperture.parent.identifier
        parent_room = aperture.parent.parent.identifier if aperture.parent.has_parent \
            else 'unknown'
    else:
        parent_room = parent_face = 'unknown'

    # create the fenestration surface string
    values = (aperture.identifier,
              'Window',
              constr_name,
              parent_face,
              ap_bc_obj,
              aperture.boundary_condition.view_factor,
              '',  # TODO: Implement Frame and Divider objects on WindowConstructions
              '1',
              len(aperture.vertices),
              ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z)
                          for v in aperture.upper_left_vertices))
    comments = ('name',
                'surface type',
                'construction name',
                'building surface name',
                'boundary condition object',
                'view factor to ground',
                'frame and divider name',
                'multiplier',
                'number of vertices',
                '')
    fen_str = generate_idf_string('FenestrationSurface:Detailed', values, comments)

    # create the WindowShadingControl object if it is needed
    if construction.has_shade:
        shd_prop_str = construction.to_shading_control_idf(
            aperture.identifier, parent_room)
        fen_str = '\n\n'.join((fen_str, shd_prop_str))

    # create the VentilationOpening object if it is needed
    if aperture.properties.energy.vent_opening is not None:
        try:
            vent_str = aperture.properties.energy.vent_opening.to_idf()
            fen_str = '\n\n'.join((fen_str, vent_str))
        except AssertionError:  # aperture does not have a parent room
            pass
    return fen_str


def face_to_idf(face):
    """Generate an IDF string representation of a Face.

    Note that the resulting string does not include full construction definitions.

    Also note that this does not include any of the shades assigned to the Face
    in the resulting string. Nor does it include the strings for the
    apertures or doors. To write these objects into a final string, you must
    loop through the Face.shades, Face.apertures, and Face.doors and call the
    to.idf method on each one.

    Args:
        face: A honeybee Face for which an IDF representation will be returned.
    """
    if isinstance(face.type, RoofCeiling):
        face_type = 'Roof' if isinstance(face.boundary_condition, (Outdoors, Ground)) \
            else 'Ceiling'  # EnergyPlus distinguishes between Roof and Ceiling
    elif isinstance(face.type, AirBoundary):
        face_type = 'Wall'  # air boundaries are not a Surface type in EnergyPlus
    else:
        face_type = face.type.name
    face_bc_obj = face.boundary_condition.boundary_condition_object if \
        isinstance(face.boundary_condition, Surface) else ''
    values = (face.identifier,
              face_type,
              face.properties.energy.construction.identifier,
              face.parent.identifier if face.has_parent else 'unknown',
              face.boundary_condition.name,
              face_bc_obj,
              face.boundary_condition.sun_exposure_idf,
              face.boundary_condition.wind_exposure_idf,
              face.boundary_condition.view_factor,
              len(face.vertices),
              ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z)
                          for v in face.upper_left_vertices))
    comments = ('name',
                'surface type',
                'construction name',
                'zone name',
                'boundary condition',
                'boundary condition object',
                'sun exposure',
                'wind exposure',
                'view factor to ground',
                'number of vertices',
                '')
    return generate_idf_string('BuildingSurface:Detailed', values, comments)


def room_to_idf(room):
    """Generate an IDF string representation of a Room.

    The resulting string will include all internal gain defintiions for the Room
    (people, lights, equipment), infiltration definitions, ventilation requirements,
    and thermostat objects. However, complete schedule defintions assigned to
    these objects are excluded and the Room's hvac is also excluded.

    Also note that this method does not write any of the geometry of the Room
    into the resulting string. To represent the Room geometry, you must loop
    through the Room.shades and Room.faces and call the to.idf method on
    each one. Note that you will likely also need to call to.idf on the
    apertures, doors and shades of each face as well as the shades on each
    aperture.

    Args:
        room: A honeybee Room for which an IDF representation will be returned.
    """
    # list of zone strings that will eventually be joined
    zone_str = ['!-   ________ZONE:{}________\n'.format(room.display_name)]

    # write the zone defintiion
    zone_values = (room.identifier,)
    zone_comments = ('name',)
    if room.multiplier != 1:
        zone_values = zone_values + ('', '', '', '', '', room.multiplier)
        zone_comments = zone_comments + ('north', 'x', 'y', 'z', 'type', 'multiplier')
    zone_str.append(generate_idf_string('Zone', zone_values, zone_comments))

    # write the load definitions
    people = room.properties.energy.people
    lighting = room.properties.energy.lighting
    electric_equipment = room.properties.energy.electric_equipment
    gas_equipment = room.properties.energy.gas_equipment
    shw = room.properties.energy.service_hot_water
    infiltration = room.properties.energy.infiltration
    ventilation = room.properties.energy.ventilation

    if people is not None:
        zone_str.append(people.to_idf(room.identifier))
    if lighting is not None:
        zone_str.append(lighting.to_idf(room.identifier))
    if electric_equipment is not None:
        zone_str.append(electric_equipment.to_idf(room.identifier))
    if gas_equipment is not None:
        zone_str.append(gas_equipment.to_idf(room.identifier))
    if shw is not None:
        shw_str, shw_sch = shw.to_idf(room)
        zone_str.append(shw_str)
        zone_str.extend(shw_sch)
    if infiltration is not None:
        zone_str.append(infiltration.to_idf(room.identifier))

    # write the ventilation and thermostat
    if ventilation is not None:
        zone_str.append(ventilation.to_idf(room.identifier))
    if room.properties.energy.is_conditioned:
        zone_str.append(room.properties.energy.setpoint.to_idf(room.identifier))

    return '\n\n'.join(zone_str)


def model_to_idf(model, schedule_directory=None):
    r"""Generate an IDF string representation of a Model.

    The resulting string will include all geometry (Rooms, Faces, Shades, Apertures,
    Doors), all fully-detailed constructions + materials, all fully-detailed
    schedules, and the room properties (loads, thermostats with setpoints, and HVAC).

    Essentially, the string includes everything needed to simulate the model
    except the simulation parameters. So joining this string with the output of
    SimulationParameter.to_idf() should create a simulate-able IDF.

    Args:
        model: A honeybee Model for which an IDF representation will be returned.
        schedule_directory: An optional file directory to which all file-based
            schedules should be written to. If None, all ScheduleFixedIntervals
            will be translated to Schedule:Compact and written fully into the
            IDF string instead of to Schedule:File. (Default: None).

    Usage:

    .. code-block:: python

        import os
        from ladybug.futil import write_to_file
        from honeybee.model import Model
        from honeybee.room import Room
        from honeybee.config import folders
        from honeybee_energy.lib.programtypes import office_program
        from honeybee_energy.hvac.idealair import IdealAirSystem
        from honeybee_energy.simulation.parameter import SimulationParameter

        # Get input Model
        room = Room.from_box('Tiny House Zone', 5, 10, 3)
        room.properties.energy.program_type = office_program
        room.properties.energy.add_default_ideal_air()
        model = Model('Tiny House', [room])

        # Get the input SimulationParameter
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        ddy_file = 'C:/EnergyPlusV9-0-1/WeatherData/USA_CO_Golden-NREL.724666_TMY3.ddy'
        sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)

        # create the IDF string for simulation paramters and model
        idf_str = '\n\n'.join((sim_par.to_idf(), model.to.idf(model)))

        # write the final string into an IDF
        idf = os.path.join(folders.default_simulation_folder, 'test_file', 'in.idf')
        write_to_file(idf, idf_str, True)
    """
    # duplicate model to avoid mutating it as we edit it for energy simulation
    model = model.duplicate()
    # remove colinear vertices using the Model tolerance to avoid E+ tolerance issues
    if model.tolerance != 0:
        for room in model.rooms:
            room.remove_colinear_vertices_envelope(model.tolerance)
    # scale the model if the units are not meters
    if model.units != 'Meters':
        model.convert_to_units('Meters')
    # check to be sure that the Airflow Network is not being used
    assert model.properties.energy.ventilation_simulation_control.vent_control_type == \
        'SingleZone', 'The Honeybee Airflow Network does not support direct ' \
        'translation to IDF.\nUse the export to OpenStudio workflow instead.'

    # write the building object into the string
    model_str = ['!-   =======================================\n'
                 '!-   ================ MODEL ================\n'
                 '!-   =======================================\n']

    # write all of the schedules and type limits
    sched_strs = []
    type_limits = []
    used_day_sched_ids = []
    sched_dir = None
    for sched in model.properties.energy.schedules:
        try:  # ScheduleRuleset
            year_schedule, week_schedules = sched.to_idf()
            if week_schedules is None:  # ScheduleConstant
                sched_strs.append(year_schedule)
            else:  # ScheduleYear
                # check that day schedules aren't referenced by other model schedules
                day_scheds = []
                for day in sched.day_schedules:
                    if day.identifier not in used_day_sched_ids:
                        day_scheds.append(day.to_idf(sched.schedule_type_limit))
                        used_day_sched_ids.append(day.identifier)
                sched_strs.extend([year_schedule] + week_schedules + day_scheds)
        except TypeError:  # ScheduleFixedInterval
            if sched_dir is None:
                if schedule_directory is None:
                    sched_strs.append(sched.to_idf_compact())
                else:
                    sched_strs.append(sched.to_idf(schedule_directory))
        t_lim = sched.schedule_type_limit
        if t_lim is not None and not _instance_in_array(t_lim, type_limits):
            type_limits.append(t_lim)
    model_str.append('!-   ========= SCHEDULE TYPE LIMITS =========\n')
    model_str.extend([type_limit.to_idf() for type_limit in set(type_limits)])
    model_str.append('!-   ============== SCHEDULES ==============\n')
    model_str.extend(sched_strs)

    # get the default generic construction set
    # must be imported here to avoid circular imports
    from .lib.constructionsets import generic_construction_set

    # write all of the materials and constructions
    materials = []
    construction_strs = []
    all_constrs = model.properties.energy.constructions + \
        generic_construction_set.constructions_unique
    for constr in set(all_constrs):
        try:
            materials.extend(constr.materials)
            construction_strs.append(constr.to_idf())
            if constr.has_shade:
                construction_strs.append(constr.to_shaded_idf())
        except AttributeError:
            try:  # AirBoundaryConstruction or ShadeConstruction
                construction_strs.append(constr.to_idf())  # AirBoundaryConstruction
            except TypeError:
                pass  # ShadeConstruction; no need to write it
    model_str.append('!-   ============== MATERIALS ==============\n')
    model_str.extend([mat.to_idf() for mat in set(materials)])
    model_str.append('!-   ============ CONSTRUCTIONS ============\n')
    model_str.extend(construction_strs)

    # write all of the HVAC systems
    model_str.append('!-   ============ HVAC SYSTEMS ============\n')
    for room in model.rooms:
        if room.properties.energy.hvac is not None:
            try:
                model_str.append(room.properties.energy.hvac.to_idf(room))
            except AttributeError:
                raise TypeError(
                    'HVAC system type "{}" does not support direct translation to IDF.\n'
                    'Use the export to OpenStudio workflow instead.'.format(
                        room.properties.energy.hvac.__class__.__name__))

    # write all of the zone geometry
    model_str.append('!-   ============ ZONE GEOMETRY ============\n')
    for room in model.rooms:
        model_str.append(room.to.idf(room))
        for face in room.faces:
            model_str.append(face.to.idf(face))
            if isinstance(face.type, AirBoundary):  # write the air mixing objects
                air_constr = face.properties.energy.construction
                adj_room = face.boundary_condition.boundary_condition_objects[-1]
                model_str.append(air_constr.to_air_mixing_idf(face, adj_room))
            for ap in face.apertures:
                if len(ap.geometry) <= 4:  # ignore apertures to be triangulated
                    model_str.append(ap.to.idf(ap))
                for shade in ap.outdoor_shades:
                    model_str.append(shade.to.idf(shade))
            for dr in face.doors:
                if len(dr.geometry) <= 4:  # ignore doors to be triangulated
                    model_str.append(dr.to.idf(dr))
                for shade in dr.outdoor_shades:
                    model_str.append(shade.to.idf(shade))
            for shade in face.outdoor_shades:
                model_str.append(shade.to.idf(shade))
        for shade in room.outdoor_shades:
            model_str.append(shade.to.idf(shade))

    # triangulate any apertures or doors with more than 4 vertices
    tri_apertures, parents_to_edit = model.triangulated_apertures()
    for tri_aps in tri_apertures:
        for ap in tri_aps:
            model_str.append(ap.to.idf(ap))
    tri_doors, parents_to_edit = model.triangulated_doors()
    for tri_drs in tri_doors:
        for dr in tri_drs:
            model_str.append(dr.to.idf(dr))

    # write all context shade geometry
    model_str.append('!-   ========== CONTEXT GEOMETRY ==========\n')
    for shade in model.orphaned_shades:
        model_str.append(shade.to.idf(shade))

    return '\n\n'.join(model_str)


def energyplus_idf_version(version_array=None):
    """Get IDF text for the version of EnergyPlus.

    This will match the version of EnergyPlus found in the config if it it exists.
    It will be None otherwise.

    Args:
        version_array: An array of up to 3 integers for the version of EnergyPlus
            for which an IDF string should be generated. If None, the energyplus_version
            from the config will be used if it exists.
    """
    if version_array:
        ver_str = '.'.join((str(d) for d in version_array))
        return generate_idf_string('Version', [ver_str], ['version identifier'])
    elif folders.energyplus_version:
        ver_str = '.'.join((str(d) for d in folders.energyplus_version))
        return generate_idf_string('Version', [ver_str], ['version identifier'])
    return None


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
