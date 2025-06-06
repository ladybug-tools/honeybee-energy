# coding=utf-8
"""Methods to write to idf."""
from .config import folders

from ladybug_geometry.geometry3d import Face3D
from honeybee.room import Room
from honeybee.face import Face
from honeybee.boundarycondition import Outdoors, Surface, Ground, boundary_conditions
from honeybee.facetype import Wall, Floor, RoofCeiling, AirBoundary
from honeybee.units import parse_distance_string, conversion_factor_to_meters

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


def shade_mesh_to_idf(shade_mesh):
    """Generate an IDF string representation of a ShadeMesh.

    Note that the resulting string will possess both the Shading object
    as well as a ShadingProperty:Reflectance if the Shade's construction
    is not in line with the EnergyPlus default of 0.2 reflectance.

    Args:
        shade_mesh: A honeybee ShadeMesh for which an IDF representation
            will be returned.
    """
    trans_sched = shade_mesh.properties.energy.transmittance_schedule.identifier if \
        shade_mesh.properties.energy.transmittance_schedule is not None else ''
    all_shd_str = []
    for i, shade in enumerate(shade_mesh.geometry.face_vertices):
        # process the geometry to get upper-left vertices
        shade_face = Face3D(shade)
        ul_verts = shade_face.upper_left_counter_clockwise_vertices

        # create the Shading:Detailed IDF string
        values = (
            '{}_{}'.format(shade_mesh.identifier, i),
            trans_sched,
            len(ul_verts),
            ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
        )
        comments = (
            'name',
            'transmittance schedule',
            'number of vertices',
            ''
        )
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)
        all_shd_str.append(shade_str)

        # create the ShadingProperty:Reflectance if construction is not default
        construction = shade_mesh.properties.energy.construction
        if not construction.is_default:
            values = (
                shade_mesh.identifier,
                construction.solar_reflectance,
                construction.visible_reflectance
            )
            comments = (
                'shading surface name',
                'diffuse solar reflectance',
                'diffuse visible reflectance'
            )
            if construction.is_specular:
                values = values + (1, construction.identifier)
                comments = comments + ('glazed fraction', 'glazing construction')
            constr_str = generate_idf_string(
                'ShadingProperty:Reflectance', values, comments)
            all_shd_str.append(constr_str)

    return '\n\n'.join(all_shd_str)


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
    ul_verts = shade.upper_left_vertices
    if shade.has_parent and not isinstance(shade.parent, Room):
        if isinstance(shade.parent, Face):
            base_srf = shade.parent.identifier
        else:  # aperture or door for parent
            try:
                base_srf = shade.parent.parent.identifier
            except AttributeError:
                base_srf = 'unknown'  # aperture without a parent (not simulate-able)
        values = (
            shade.identifier,
            base_srf,
            trans_sched,
            len(shade.vertices),
            ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
        )
        comments = (
            'name',
            'base surface',
            'transmittance schedule',
            'number of vertices',
            ''
        )
        shade_str = generate_idf_string('Shading:Zone:Detailed', values, comments)
    else:  # orphaned shade
        values = (
            shade.identifier,
            trans_sched,
            len(shade.vertices),
            ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
        )
        comments = (
            'name',
            'transmittance schedule',
            'number of vertices',
            ''
        )
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)

    # create the ShadingProperty:Reflectance IDF string if construction is not default
    construction = shade.properties.energy.construction
    if construction.is_default:
        return shade_str
    else:
        values = (
            shade.identifier,
            construction.solar_reflectance,
            construction.visible_reflectance
        )
        comments = (
            'shading surface name',
            'diffuse solar reflectance',
            'diffuse visible reflectance'
        )
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

    If the input door is orphaned, the resulting string will possess both the
    Shading object as well as a ShadingProperty:Reflectance that aligns with the
    Doors's exterior construction properties. However, a transmittance schedule
    that matches the transmittance of the window construction will only be
    referenced and not included in the resulting string. All transmittance schedules
    follow the format of 'Constant %.3f Transmittance'.

    Args:
        door: A honeybee Door for which an IDF representation will be returned.
    """
    # IF ORPHANED: write the door as a shade
    if not door.has_parent:
        # create the Shading:Detailed IDF string
        cns = door.properties.energy.construction
        trans_sch = 'Constant %.3f Transmittance' % cns.solar_transmittance \
            if door.is_glass else ''
        verts = door.upper_left_vertices
        verts_str = ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in verts)
        values = (door.identifier, trans_sch, len(verts), verts_str)
        comments = ('name', 'transmittance schedule', 'number of vertices', '')
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)

        # create the ShadingProperty:Reflectance
        comments = (
            'shade surface name', 'diffuse solar reflectance', 'diffuse visible reflectance')
        if door.is_glass:
            values = (door.identifier, 0.2, 0.2, 1, cns.identifier)
            comments = comments + ('glazed fraction of surface', 'glazing construction')
        else:
            values = (door.identifier, cns.outside_solar_reflectance,
                      cns.outside_visible_reflectance)
        constr_str = generate_idf_string('ShadingProperty:Reflectance', values, comments)
        return '\n\n'.join((shade_str, constr_str))

    # IF CHILD: write the door as a fenestration surface
    # set defaults for missing fields
    door_bc_obj = door.boundary_condition.boundary_condition_object if \
        isinstance(door.boundary_condition, Surface) else ''
    construction = door.properties.energy.construction
    frame_name = construction.frame.identifier if construction.has_frame else ''
    if construction.has_shade:
        constr_name = construction.window_construction.identifier
    elif construction.is_dynamic:
        constr_name = '{}State0'.format(construction.constructions[0].identifier)
    else:
        constr_name = construction.identifier
    if door.has_parent:
        parent_face = door.parent.identifier
        parent_room = door.parent.parent.identifier if door.parent.has_parent \
            else 'unknown'
    else:
        parent_room = parent_face = 'unknown'

    # create the fenestration surface string
    ul_verts = door.upper_left_vertices
    values = (
        door.identifier,
        'Door' if not door.is_glass else 'GlassDoor',
        constr_name,
        parent_face,
        door_bc_obj,
        door.boundary_condition.view_factor,
        frame_name,
        '1',
        len(door.vertices),
        ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
    )
    comments = (
        'name',
        'surface type',
        'construction name',
        'building surface name',
        'boundary condition object',
        'view factor to ground',
        'frame and divider name',
        'multiplier',
        'number of vertices',
        ''
    )
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

    If the input aperture is orphaned, the resulting string will possess both the
    Shading object as well as a ShadingProperty:Reflectance that aligns with the
    Aperture's exterior construction properties. However, a transmittance schedule
    that matches the transmittance of the window construction will only be
    referenced and not included in the resulting string. All transmittance schedules
    follow the format of 'Constant %.3f Transmittance'.

    Args:
        aperture: A honeybee Aperture for which an IDF representation will be returned.
    """
    # IF ORPHANED: write the aperture as a shade
    if not aperture.has_parent:
        # create the Shading:Detailed IDF string
        cns = aperture.properties.energy.construction
        trans_sch = 'Constant %.3f Transmittance' % cns.solar_transmittance
        verts = aperture.upper_left_vertices
        verts_str = ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in verts)
        values = (aperture.identifier, trans_sch, len(verts), verts_str)
        comments = ('name', 'transmittance schedule', 'number of vertices', '')
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)

        # create the ShadingProperty:Reflectance
        values = (aperture.identifier, 0.2, 0.2, 1, cns.identifier)
        comments = (
            'shade surface name', 'diffuse solar reflectance', 'diffuse visible reflectance',
            'glazed fraction of surface', 'glazing construction'
        )
        constr_str = generate_idf_string('ShadingProperty:Reflectance', values, comments)
        return '\n\n'.join((shade_str, constr_str))

    # IF CHILD: write the aperture as a fenestration surface
    # set defaults for missing fields
    ap_bc_obj = aperture.boundary_condition.boundary_condition_object if \
        isinstance(aperture.boundary_condition, Surface) else ''
    construction = aperture.properties.energy.construction
    frame_name = construction.frame.identifier if construction.has_frame else ''
    if construction.has_shade:
        constr_name = construction.window_construction.identifier
    elif construction.is_dynamic:
        constr_name = '{}State0'.format(construction.constructions[0].identifier)
    else:
        constr_name = construction.identifier
    if aperture.has_parent:
        parent_face = aperture.parent.identifier
        parent_room = aperture.parent.parent.identifier if aperture.parent.has_parent \
            else 'unknown'
    else:
        parent_room = parent_face = 'unknown'

    # create the fenestration surface string
    ul_verts = aperture.upper_left_vertices
    values = (
        aperture.identifier,
        'Window',
        constr_name,
        parent_face,
        ap_bc_obj,
        aperture.boundary_condition.view_factor,
        frame_name,
        '1',
        len(aperture.vertices),
        ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
    )
    comments = (
        'name',
        'surface type',
        'construction name',
        'building surface name',
        'boundary condition object',
        'view factor to ground',
        'frame and divider name',
        'multiplier',
        'number of vertices',
        ''
    )
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

    If the input face is orphaned, the resulting string will possess both the
    Shading object as well as a ShadingProperty:Reflectance that aligns with
    the Face's exterior construction properties. Furthermore, any child
    apertures of doors in the face will also be included as shading geometries.

    Args:
        face: A honeybee Face for which an IDF representation will be returned.
    """
    # IF ORPHANED: write the face as a shade
    if not face.has_parent:
        # create the Shading:Detailed IDF string
        verts = face.punched_geometry.upper_left_counter_clockwise_vertices
        verts_str = ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in verts)
        values = (face.identifier, '', len(verts), verts_str)
        comments = ('name', 'transmittance schedule', 'number of vertices', '')
        shade_str = generate_idf_string('Shading:Building:Detailed', values, comments)

        # create the ShadingProperty:Reflectance IDF string
        cns = face.properties.energy.construction
        values = (
            face.identifier, cns.outside_solar_reflectance, cns.outside_visible_reflectance)
        comments = (
            'shade surface name', 'diffuse solar reflectance', 'diffuse visible reflectance')
        constr_str = generate_idf_string('ShadingProperty:Reflectance', values, comments)

        # translate any child apertures or doors
        face_str = [shade_str, constr_str]
        for ap in face.apertures:
            ap._parent = None  # remove parent to translate as orphaned
            face_str.append(aperture_to_idf(ap))
            ap._parent = face  # put back the parent
        for dr in face.doors:
            dr._parent = None  # remove parent to translate as orphaned
            face_str.append(door_to_idf(dr))
            dr._parent = face  # put back the parent
        return '\n\n'.join(face_str)

    # IF CHILD: write the aperture as a fenestration surface
    # select the correct face type
    if isinstance(face.type, AirBoundary):
        face_type = 'Wall'  # air boundaries are not a Surface type in EnergyPlus
    elif isinstance(face.type, RoofCeiling):
        if face.altitude < 0:
            face_type = 'Wall'  # ensure E+ does not try to flip the Face
        elif isinstance(face.boundary_condition, (Outdoors, Ground)):
            face_type = 'Roof'  # E+ distinguishes between Roof and Ceiling
        else:
            face_type = 'Ceiling'
    elif isinstance(face.type, Floor) and face.altitude > 0:
        face_type = 'Wall'  # ensure E+ does not try to flip the Face
    else:
        face_type = face.type.name
    # select the correct boundary condition
    bc_name, append_txt = face.boundary_condition.name, None
    if isinstance(face.boundary_condition, Surface):
        face_bc_obj = face.boundary_condition.boundary_condition_object
    elif face.boundary_condition.name == 'OtherSideTemperature':
        face_bc_obj = '{}_OtherTemp'.format(face.identifier)
        append_txt = face.boundary_condition.to_idf(face_bc_obj)
        bc_name = 'OtherSideCoefficients'
    else:
        face_bc_obj = ''
    # process the geometry correctly if it has holes
    ul_verts = face.upper_left_vertices
    if face.geometry.has_holes and isinstance(face.boundary_condition, Surface):
        # check if the first vertex is the upper-left vertex
        pt1, found_i = ul_verts[0], False
        for pt in ul_verts[1:]:
            if pt == pt1:
                found_i = True
                break
        if found_i:  # reorder the vertices to have boundary first
            ul_verts = reversed(ul_verts)
    # assemble the values and the comments
    if face.has_parent:
        if face.parent.identifier == face.parent.zone:
            zone_name, space_name = face.parent.zone, ''
        else:
            zone_name, space_name = face.parent.zone, face.parent.identifier
    else:
        zone_name, space_name = 'unknown', ''
    values = (
        face.identifier,
        face_type,
        face.properties.energy.construction.identifier,
        zone_name,
        space_name,
        bc_name,
        face_bc_obj,
        face.boundary_condition.sun_exposure_idf,
        face.boundary_condition.wind_exposure_idf,
        face.boundary_condition.view_factor,
        len(face.vertices),
        ',\n '.join('%.3f, %.3f, %.3f' % (v.x, v.y, v.z) for v in ul_verts)
    )
    comments = (
        'name',
        'surface type',
        'construction name',
        'zone name',
        'space name',
        'boundary condition',
        'boundary condition object',
        'sun exposure',
        'wind exposure',
        'view factor to ground',
        'number of vertices',
        ''
    )
    face_idf = generate_idf_string('BuildingSurface:Detailed', values, comments)
    return face_idf if not append_txt else face_idf + append_txt


def room_to_idf(room):
    """Generate an IDF string representation of a Room.

    The resulting string will include all internal gain definitions for the Room
    (people, lights, equipment, process) and the infiltration definition. It will
    also include internal masses, ventilation fans, and daylight controls. However,
    complete schedule definitions assigned to these load objects are excluded.

    If the room's zone name is the same as the room identifier, the resulting IDF
    string will be for an EnergyPlus Zone and it will include ventilation
    requirements and thermostat objects. Otherwise, the IDF string will be for
    a Space with ventilation and thermostats excluded (with the assumption
    that these objects are to be written separately with the parent Zone).

    The Room's HVAC is always excluded in the string returned from this method
    regardless of whether the room represents an entire zone or an individual
    space within a larger zone.

    Also note that this method does not write any of the geometry of the Room
    into the resulting string. To represent the Room geometry, you must loop
    through the Room.shades and Room.faces and call the to.idf method on
    each one. Note that you will likely also need to call to.idf on the
    apertures, doors and shades of each face as well as the shades on each
    aperture.

    Args:
        room: A honeybee Room for which an IDF representation will be returned.
    """
    # clean the room name so that it can be written into a comment
    clean_name = room.display_name.replace('\n', '')

    if room.identifier == room.zone:  # write the zone definition
        is_zone = True
        room_str = ['!-   ________ZONE:{}________\n'.format(clean_name)]
        ceil_height = room.geometry.max.z - room.geometry.min.z
        include_floor = 'No' if room.exclude_floor_area else 'Yes'
        zone_values = (room.identifier, '', '', '', '', '', room.multiplier,
                       ceil_height, room.volume, room.floor_area, '', '', include_floor)
        zone_comments = ('name', 'north', 'x', 'y', 'z', 'type', 'multiplier',
                         'ceiling height', 'volume', 'floor area', 'inside convection',
                         'outside convection', 'include floor area')
        room_str.append(generate_idf_string('Zone', zone_values, zone_comments))
    else:  # write the space definition
        is_zone = False
        room_str = ['!-   ________SPACE:{}________\n'.format(clean_name)]
        ceil_height = room.geometry.max.z - room.geometry.min.z
        space_values = (room.identifier, room.zone,
                        ceil_height, room.volume, room.floor_area)
        space_comments = ('name', 'zone name', 'ceiling height', 'volume', 'floor area')
        room_str.append(generate_idf_string('Space', space_values, space_comments))

    # write the load definitions
    people = room.properties.energy.people
    lighting = room.properties.energy.lighting
    electric_equipment = room.properties.energy.electric_equipment
    gas_equipment = room.properties.energy.gas_equipment
    shw = room.properties.energy.service_hot_water
    infiltration = room.properties.energy.infiltration
    ventilation = room.properties.energy.ventilation

    if people is not None:
        room_str.append(people.to_idf(room.identifier))
    if lighting is not None:
        room_str.append(lighting.to_idf(room.identifier))
    if electric_equipment is not None:
        room_str.append(electric_equipment.to_idf(room.identifier))
    if gas_equipment is not None:
        room_str.append(gas_equipment.to_idf(room.identifier))
    if shw is not None:
        shw_str, shw_sch = shw.to_idf(room)
        room_str.append(shw_str)
        room_str.extend(shw_sch)
    if infiltration is not None:
        room_str.append(infiltration.to_idf(room.identifier))

    # write the ventilation and thermostat
    if is_zone:
        if ventilation is not None:
            room_str.append(ventilation.to_idf(room.identifier))
        if room.properties.energy.is_conditioned and \
                room.properties.energy.setpoint is not None:
            room_str.append(room.properties.energy.setpoint.to_idf(room.identifier))

    # write any ventilation fan definitions
    for fan in room.properties.energy._fans:
        room_str.append(fan.to_idf(room.identifier))

    # write the daylighting control
    if room.properties.energy.daylighting_control is not None:
        room_str.extend(room.properties.energy.daylighting_control.to_idf())

    # write any process load definitions
    for p_load in room.properties.energy._process_loads:
        room_str.append(p_load.to_idf(room.identifier))

    # write any internal mass definitions
    for int_mass in room.properties.energy._internal_masses:
        room_str.append(int_mass.to_idf(room.identifier, is_zone))

    return '\n\n'.join(room_str)


def model_to_idf(
    model, schedule_directory=None, use_ideal_air_equivalent=True,
    patch_missing_adjacencies=False
):
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
        use_ideal_air_equivalent: Boolean to note whether any detailed HVAC system
            templates should be converted to an equivalent IdealAirSystem upon export.
            If False and the Model contains detailed systems, a ValueError will
            be raised since this method does not support the translation of
            detailed systems. (Default:True).
        patch_missing_adjacencies: Boolean to note whether any missing adjacencies
            in the model should be replaced with Adiabatic boundary conditions.
            This is useful when the input model is only a portion of a much
            larger model. (Default: False).

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

        # create the IDF string for simulation parameters and model
        idf_str = '\n\n'.join((sim_par.to_idf(), model.to.idf(model)))

        # write the final string into an IDF
        idf = os.path.join(folders.default_simulation_folder, 'test_file', 'in.idf')
        write_to_file(idf, idf_str, True)
    """
    # duplicate model to avoid mutating it as we edit it for energy simulation
    original_model = model
    model = model.duplicate()
    # scale the model if the units are not meters
    if model.units != 'Meters':
        model.convert_to_units('Meters')
    # remove degenerate geometry within native E+ tolerance of 0.01 meters
    try:
        model.remove_degenerate_geometry(0.01)
    except ValueError:
        error = 'Failed to remove degenerate Rooms.\nYour Model units system is: {}. ' \
            'Is this correct?'.format(original_model.units)
        raise ValueError(error)

    # convert model to simple ventilation and Ideal Air Systems
    model.properties.energy.ventilation_simulation_control.vent_control_type = \
        'SingleZone'
    if use_ideal_air_equivalent:
        for room in model.rooms:
            room.properties.energy.assign_ideal_air_equivalent()

    # patch missing adjacencies
    if patch_missing_adjacencies:
        model.properties.energy.missing_adjacencies_to_adiabatic()

    # resolve the properties across zones
    single_zones, zone_dict = model.properties.energy.resolve_zones()

    # write the building object into the string
    model_str = ['!-   =======================================\n'
                 '!-   ================ MODEL ================\n'
                 '!-   =======================================\n']

    # write all of the schedules and type limits
    sched_strs = []
    type_limits = []
    used_day_sched_ids, used_day_count = {}, 1
    always_on_included = False
    all_scheds = model.properties.energy.schedules + \
        model.properties.energy.orphaned_trans_schedules
    for sched in all_scheds:
        if sched.identifier == 'Always On':
            always_on_included = True
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
                        used_day_sched_ids[day.identifier] = day
                    elif day != used_day_sched_ids[day.identifier]:
                        new_day = day.duplicate()
                        new_day.identifier = 'Schedule Day {}'.format(used_day_count)
                        day_scheds.append(new_day.to_idf(sched.schedule_type_limit))
                        for i, week_sch in enumerate(week_schedules):
                            week_schedules[i] = \
                                week_sch.replace(day.identifier, new_day.identifier)
                        used_day_count += 1
                sched_strs.extend([year_schedule] + week_schedules + day_scheds)
        except TypeError:  # ScheduleFixedInterval
            if schedule_directory is None:
                sched_strs.append(sched.to_idf_compact())
            else:
                sched_strs.append(sched.to_idf(schedule_directory))
        t_lim = sched.schedule_type_limit
        if t_lim is not None and not _instance_in_array(t_lim, type_limits):
            type_limits.append(t_lim)
    if not always_on_included:
        always_schedule, _ = model.properties.energy._always_on_schedule().to_idf()
        sched_strs.append(always_schedule)
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
    dynamic_cons = []
    all_constrs = model.properties.energy.constructions + \
        generic_construction_set.constructions_unique
    for constr in set(all_constrs):
        try:
            materials.extend(constr.materials)
            construction_strs.append(constr.to_idf())
            if constr.has_frame:
                materials.append(constr.frame)
            if constr.has_shade:
                if constr.window_construction in all_constrs:
                    construction_strs.pop(-1)  # avoid duplicate specification
                if constr.is_switchable_glazing:
                    materials.append(constr.switched_glass_material)
                construction_strs.append(constr.to_shaded_idf())
            elif constr.is_dynamic:
                dynamic_cons.append(constr)
        except AttributeError:
            try:  # AirBoundaryConstruction or ShadeConstruction
                construction_strs.append(constr.to_idf())  # AirBoundaryConstruction
            except TypeError:
                pass  # ShadeConstruction; no need to write it
    model_str.append('!-   ============== MATERIALS ==============\n')
    model_str.extend([mat.to_idf() for mat in set(materials)])
    model_str.append('!-   ============ CONSTRUCTIONS ============\n')
    model_str.extend(construction_strs)

    # write all of the HVAC systems for zones
    model_str.append('!-   ============ HVAC SYSTEMS ============\n')
    for zone_id, zone_data in zone_dict.items():
        rooms, z_prop, set_pt, vent = zone_data
        mult, ceil_hgt, vol, flr_area, inc_flr = z_prop
        model_str.append('!-   ________ZONE:{}________\n'.format(zone_id))
        zone_values = (zone_id, '', '', '', '', '', mult,
                       ceil_hgt, vol, flr_area, '', '', inc_flr)
        zone_comments = ('name', 'north', 'x', 'y', 'z', 'type', 'multiplier',
                         'ceiling height', 'volume', 'floor area', 'inside convection',
                         'outside convection', 'include floor area')
        model_str.append(generate_idf_string('Zone', zone_values, zone_comments))
        if vent is not None:
            model_str.append(vent.to_idf(zone_id))
        hvacs = [r.properties.energy.hvac for r in rooms
                 if r.properties.energy.hvac is not None]
        if set_pt is not None and len(hvacs) != 0:
            model_str.append(set_pt.to_idf(zone_id))
            try:
                model_str.append(hvacs[0].to_idf_zone(zone_id, set_pt, vent))
            except AttributeError:
                raise TypeError(
                    'HVAC system type "{}" does not support direct translation to IDF.\n'
                    'Use the export to OpenStudio workflow instead.'.format(
                        room.properties.energy.hvac.__class__.__name__))
    # write all of the HVAC systems for individual rooms not using zones
    for room in single_zones:
        if room.properties.energy.hvac is not None \
                and room.properties.energy.setpoint is not None:
            try:
                model_str.append(room.properties.energy.hvac.to_idf(room))
            except AttributeError:
                raise TypeError(
                    'HVAC system type "{}" does not support direct translation to IDF.\n'
                    'Use the export to OpenStudio workflow instead.'.format(
                        room.properties.energy.hvac.__class__.__name__))

    # get the default air boundary construction
    # must be imported here to avoid circular imports
    from .lib.constructions import air_boundary

    # write all of the room geometry
    model_str.append('!-   ============ ROOM GEOMETRY ============\n')
    sf_objs = []
    found_ab = []
    for room in model.rooms:
        model_str.append(room.to.idf(room))
        for face in room.faces:
            model_str.append(face.to.idf(face))
            if isinstance(face.type, AirBoundary):  # write the air mixing objects
                air_constr = face.properties.energy.construction
                try:
                    if face.identifier not in found_ab:
                        adj_face = face.boundary_condition.boundary_condition_object
                        adj_room = face.boundary_condition.boundary_condition_objects[-1]
                        try:
                            model_str.append(
                                air_constr.to_cross_mixing_idf(face, adj_room))
                        except AttributeError:  # opaque construction for air boundary
                            model_str.append(
                                air_boundary.to_cross_mixing_idf(face, adj_room))
                        found_ab.append(adj_face)
                except AttributeError as e:
                    raise ValueError(
                        'Face "{}" is an Air Boundary but lacks a Surface boundary '
                        'condition.\n{}'.format(face.full_id, e))
            for ap in face.apertures:
                if len(ap.geometry) <= 4:  # ignore apertures to be triangulated
                    model_str.append(ap.to.idf(ap))
                    sf_objs.append(ap)
                for shade in ap.outdoor_shades:
                    model_str.append(shade.to.idf(shade))
            for dr in face.doors:
                if len(dr.geometry) <= 4:  # ignore doors to be triangulated
                    model_str.append(dr.to.idf(dr))
                    sf_objs.append(dr)
                for shade in dr.outdoor_shades:
                    model_str.append(shade.to.idf(shade))
            for shade in face.outdoor_shades:
                model_str.append(shade.to.idf(shade))
        for shade in room.outdoor_shades:
            model_str.append(shade.to.idf(shade))

    # triangulate any apertures or doors with more than 4 vertices
    tri_apertures, _ = model.triangulated_apertures()
    for tri_aps in tri_apertures:
        for i, ap in enumerate(tri_aps):
            if i != 0:
                ap.properties.energy.vent_opening = None
            model_str.append(ap.to.idf(ap))
            sf_objs.append(ap)
    tri_doors, _ = model.triangulated_doors()
    for tri_drs in tri_doors:
        for i, dr in enumerate(tri_drs):
            if i != 0:
                dr.properties.energy.vent_opening = None
            model_str.append(dr.to.idf(dr))
            sf_objs.append(dr)

    # write all context shade geometry
    model_str.append('!-   ========== CONTEXT GEOMETRY ==========\n')
    pv_objects = []
    for shade in model.orphaned_shades:
        model_str.append(shade.to.idf(shade))
        if shade.properties.energy.pv_properties is not None:
            pv_objects.append(shade)
    for shade_mesh in model.shade_meshes:
        model_str.append(shade_mesh.to.idf(shade_mesh))
    for face in model.orphaned_faces:
        model_str.append(face_to_idf(face))
    for ap in model.orphaned_apertures:
        model_str.append(aperture_to_idf(ap))
    for dr in model.orphaned_doors:
        model_str.append(door_to_idf(dr))

    # write any EMS programs for dynamic constructions
    if len(dynamic_cons) != 0:
        model_str.append('!-   ========== EMS PROGRAMS ==========\n')
        dyn_dict = {}
        for sf in sf_objs:
            con = sf.properties.energy.construction
            try:
                dyn_dict[con.identifier].append(sf.identifier)
            except KeyError:
                dyn_dict[con.identifier] = [sf.identifier]
        for con in dynamic_cons:
            model_str.append(con.to_program_idf(dyn_dict[con.identifier]))
        model_str.append(dynamic_cons[0].idf_program_manager(dynamic_cons))

    # write any generator objects that were discovered in the model
    if len(pv_objects) != 0:
        model_str.append('!-   ========== PHOTOVOLTAIC GENERATORS ==========\n')
        for shade in pv_objects:
            model_str.append(shade.properties.energy.pv_properties.to_idf(shade))
        model_str.extend(model.properties.energy.electric_load_center.to_idf(pv_objects))

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


def _preprocess_model_for_trace(
        model, single_window=True, rect_sub_distance='0.15m',
        frame_merge_distance='0.2m'):
    """Pre-process a Honeybee Model to be written to TRANE TRACE as a gbXML.

    Args:
        model: A Honeybee Model to be converted to a TRACE-compatible gbXML.
        single_window: A boolean for whether all windows within walls should be
            converted to a single window with an area that matches the original
            geometry. (Default: True).
        rect_sub_distance: Text string of a number for the resolution at which
            non-rectangular Apertures will be subdivided into smaller rectangular
            units. This is required as TRACE 3D plus cannot model non-rectangular
            geometries. This can include the units of the distance (eg. 0.5ft) or,
            if no units are provided, the value will be interpreted in the
            honeybee model units. (Default: 0.15m).
        frame_merge_distance: Text string of a number for the maximum distance
            between non-rectangular Apertures at which point the Apertures will
            be merged into a single rectangular geometry. This is often helpful
            when there are several triangular Apertures that together make a
            rectangle when they are merged across their frames. This can include
            the units of the distance (eg. 0.5ft) or, if no units are provided,
            the value will be interpreted in the honeybee model units. (Default: 0.2m).

    Returns:
        The input Model modified such that it can import to TRACE as a gbXML
        without issues.
    """
    # make sure there are rooms and remove all shades and orphaned objects
    assert len(model.rooms) != 0, \
        'Model contains no Rooms and therefore cannot be simulated in TRACE.'
    model.remove_all_shades()
    model.remove_faces()
    model.remove_apertures()
    model.remove_doors()

    # remove degenerate geometry within native E+ tolerance of 0.01 meters
    original_units = model.units
    model.convert_to_units('Meters')
    try:
        model.remove_degenerate_geometry(0.01)
    except ValueError:
        error = 'Failed to remove degenerate Rooms.\nYour Model units system is: {}. ' \
            'Is this correct?'.format(original_units)
        raise ValueError(error)
    rect_sub_distance = parse_distance_string(rect_sub_distance, original_units)
    frame_merge_distance = parse_distance_string(frame_merge_distance, original_units)
    if original_units != 'Meters':
        c_factor = conversion_factor_to_meters(original_units)
        rect_sub_distance = rect_sub_distance * c_factor
        frame_merge_distance = frame_merge_distance * c_factor

    # remove all interior windows in the model
    for room in model.rooms:
        for face in room.faces:
            if isinstance(face.boundary_condition, Surface):
                face.remove_sub_faces()

    # convert all rooms to extrusions and patch the resulting missing adjacencies
    model.rooms_to_extrusions()
    model.properties.energy.missing_adjacencies_to_adiabatic()

    # convert windows in walls to a single geometry
    if single_window:
        for room in model.rooms:
            for face in room.faces:
                if isinstance(face.type, Wall) and face.has_sub_faces:
                    face.boundary_condition = boundary_conditions.outdoors
                    face.apertures_by_ratio(face.aperture_ratio, 0.01, rect_split=False)

    # convert all of the Aperture geometries to rectangles so they can be translated
    model.rectangularize_apertures(
        subdivision_distance=rect_sub_distance, max_separation=frame_merge_distance,
        merge_all=True, resolve_adjacency=False
    )

    # if there are still multiple windows in a given Face, ensure they do not touch
    for room in model.rooms:
        for face in room.faces:
            if len(face.apertures) > 1:
                face.offset_aperture_edges(-0.01, 0.01)

    # re-solve adjacency given that all of the previous operations have messed with it
    model.solve_adjacency(merge_coplanar=True, intersect=True, overwrite=True)

    # reset all display_names so that they are unique (derived from reset identifiers)
    model.reset_ids()  # sets the identifiers based on the display_name
    for room in model.rooms:
        room.display_name = None
        for face in room.faces:
            face.display_name = None
            for ap in face.apertures:
                ap.display_name = None
            for dr in face.apertures:
                dr.display_name = None
        if room.story is not None and room.story.startswith('-'):
            room.story = 'neg{}'.format(room.story[1:])

    # remove the HVAC from any Rooms lacking setpoints
    rem_msgs = model.properties.energy.remove_hvac_from_no_setpoints()
    if len(rem_msgs) != 0:
        print('\n'.join(rem_msgs))

    return model
