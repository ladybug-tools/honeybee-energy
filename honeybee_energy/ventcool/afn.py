# coding=utf-8
"""Functions to generate airflownetwork for a list of rooms."""
from __future__ import division

from .crack import AFNCrack
from .opening import VentilationOpening
from .crack_data import crack_data_dict


def air_density_from_pressure(atmospheric_pressure=101325, air_temperature=20.0):
    """Calculate density of dry air using the ideal gas law from temperature and pressure.

    Args:
        atmospheric_pressure: Atmospheric pressure in Pascals. (Default: 101325).
        air_temperature: Air temperature in Celsius. (Default: 20.0).
    Returns:
        Air density at the given atmospheric pressure in kg/m3.
    """
    r_specific = 287.058  # specific gas constant for dry air in J/kg/K
    air_temperature += 273.15  # absolute temperature
    return atmospheric_pressure / (r_specific * air_temperature)


def interior_afn(interior_face_groups, int_cracks):
    """Mutate interior faces and subfaces to model airflow through cracks and openings.

    This function creates an AFNCrack object with an air mass flow coefficient that
    reflects the leakage characteristics of faces with different areas and types.
    This requires multiplying the area-normalized air mass flow coefficients from the
    reference crack data in int_cracks, by the wall area.

    This function does not check adjacency information when computing leakage parameters
    for adjacent faces or subfaces. It assumes adjacent faces share the same type and
    area properties so that the computed leakage parameters are equivalent. Note that
    EnergyPlus only requires one of the adjacent interzone surfaces to be
    assigned a leakage component. If both adjacent surfaces have a leakage component,
    the air flow through the surface will be counted twice.

    Args:
        interior_face_groups: A tuple with four groups of interior faces types:

            * int_walls: List of interior Wall type Face objects.
            * int_floorceilings: List of interior RoofCeiling and Floor type Face
                objects.
            * int_apertures: List of interior Aperture subface Face objects.
            * int_doors: List of interior Door subface Face objects.

        int_cracks: A dictionary of air mass flow coefficient and exponent data
            corresponding to the face types in the interior_face_groups. Face
            data flow coefficients should be normalized by surface area, and closed
            opening flow coefficients should be normalized by edge lengths, for example:

            {
                # kg/s/m2 @ 1 Pa
                'wall_flow_cof': 0.003,
                'wall_flow_exp': 0.75,
                'floorceiling_flow_cof': 0.0009,
                'floorceiling_flow_exp': 0.7,
                # kg/s/m @ 1 Pa
                'window_flow_cof': 0.0014,
                'window_flow_exp': 0.65,
                'door_flow_cof': 0.02,
                'door_flow_exp': 0.6
            }
    """

    # simplify parameters
    int_walls, int_floorceilings, int_apertures, int_doors = interior_face_groups

    # add interior crack leakage components
    for int_wall in int_walls:
        opening_area = sum([aper.area for aper in int_wall.apertures])
        opening_area += sum([door.area for door in int_wall.doors])
        face_area = int_wall.area - opening_area
        flow_cof = int_cracks['wall_flow_cof'] * face_area
        flow_exp = int_cracks['wall_flow_exp']
        int_wall.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    for int_floorceiling in int_floorceilings:
        opening_area = sum([aper.area for aper in int_floorceiling.apertures])
        face_area = int_floorceiling.area - opening_area
        flow_cof = int_cracks['floorceiling_flow_cof'] * face_area
        flow_exp = int_cracks['floorceiling_flow_exp']
        int_floorceiling.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    # add interior opening leakage components
    for int_aperture in int_apertures:
        if int_aperture.properties.energy.vent_opening is None:
            int_aperture.is_operable = True
            int_aperture.properties.energy.vent_opening = VentilationOpening()
        vent_opening = int_aperture.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = int_cracks['window_flow_cof']
        vent_opening.flow_exponent_closed = int_cracks['window_flow_exp']

    for int_door in int_doors:
        if int_door.properties.energy.vent_opening is None:
            int_door.properties.energy.vent_opening = VentilationOpening()
        vent_opening = int_door.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = int_cracks['door_flow_cof']
        vent_opening.flow_exponent_closed = int_cracks['door_flow_exp']


def exterior_afn(exterior_face_groups, ext_cracks):
    """Mutate exterior faces and subfaces to model airflow through cracks and openings.

    This function creates an AFNCrack object with an air mass flow coefficient that
    reflects the leakage characteristics of faces with different areas and types.
    This requires multiplying the area-normalized air mass flow coefficients from the
    reference crack data in ext_cracks, by the wall area.

    Args:
        exterior_face_groups: A tuple with four groups of exterior faces types:

            * ext_walls: List of exterior Wall type Face objects.
            * ext_roofs: List of exterior RoofCeiling type Face objects.
            * ext_apertures: List of exterior Aperture subface Face objects.
            * ext_doors: List of exterior Door subface Face objects.

        ext_cracks: A dictionary of air mass flow coefficient and exponent data
            corresponding to the face types in the exterior_face_groups. Face
            data flow coefficients should be normalized by surface area, and closed
            opening flow coefficients should be normalized by edge lengths, for example:

            {
                # kg/s/m2 @ 1 Pa
                'wall_flow_cof': 0.00001,
                'wall_flow_exp': 0.7,
                'roof_flow_cof': 0.00001,
                'roof_flow_exp': 0.70,
                # kg/s/m @ 1 Pa
                'window_flow_cof': 0.00001,
                'window_flow_exp': 0.7,
                'door_flow_cof': 0.0002,
                'door_flow_exp': 0.7
            }
    """

    # simplify parameters
    ext_walls, ext_roofs, ext_apertures, ext_doors = exterior_face_groups

    # add exterior crack leakage components
    for ext_wall in ext_walls:
        opening_area = sum([aper.area for aper in ext_wall.apertures])
        opening_area += sum([door.area for door in ext_wall.doors])
        face_area = ext_wall.area - opening_area
        flow_cof = ext_cracks['wall_flow_cof'] * face_area
        flow_exp = ext_cracks['wall_flow_exp']
        ext_wall.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    for ext_roof in ext_roofs:
        opening_area = sum([aper.area for aper in ext_roof.apertures])
        face_area = ext_roof.area - opening_area
        flow_cof = ext_cracks['roof_flow_cof'] * face_area
        flow_exp = ext_cracks['roof_flow_exp']
        ext_roof.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    # add exterior opening leakage components
    for ext_aperture in ext_apertures:
        if ext_aperture.properties.energy.vent_opening is None:
            ext_aperture.is_operable = True
            ext_aperture.properties.energy.vent_opening = VentilationOpening()
        vent_opening = ext_aperture.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = ext_cracks['window_flow_cof']
        vent_opening.flow_exponent_closed = ext_cracks['window_flow_exp']

    for ext_door in ext_doors:
        if ext_door.properties.energy.vent_opening is None:
            ext_door.properties.energy.vent_opening = VentilationOpening()
        vent_opening = ext_door.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = ext_cracks['door_flow_cof']
        vent_opening.flow_exponent_closed = ext_cracks['door_flow_exp']


def generate(rooms, window_vent_controls, leakage_type='Average',
             use_room_infiltration=True, atmospheric_pressure=101325):
    """
    Mutate a list of Honeybee Room objects to represent an EnergyPlus AirflowNetwork.

    This function will compute leakage component parameters for the ventilation
    cooling energy properties of Honeybee Room and Face objects to simulate an
    EnergyPlus AirflowNetwork.

    VentilationOpening objects will be added to Aperture and Door objects if not already
    defined. If already defined, only the parameters defining leakage when the openings
    are closed will be overwritten. AFNCrack objects will be added to all external and
    internal Face objects, and any existing AFNCrack objects will be overwritten.

    Args:
        rooms: List of Honeybee Room objects that make up the Airflow Network. The
            adjacencies of these rooms must be solved.
        window_vent_controls: List or tuple of VentilationControl objects or None,
            corresponding to the list of rooms.
        leakage_type: Text identifying the leakiness of the internal walls. This
            will be used to determine the air mass flow rate parameters for cracks in
            internal floors, ceilings and walls. (Default: 'Average').
            Choose from the following:

            * Tight
            * Average
            * Leaky

        use_room_infiltration: Boolean value to specify how exterior leakage parameters
            are computed. If True the exterior airflow leakage parameters will be derived
            from the room infiltration rate specified in RoomEnergyProperties. This will
            compute air leakage parameters for exterior cracks and opening edges that
            produce a total air flow rate equivalent to the room infiltration rate, at
            an envelope pressure difference of 4 Pa. However, the individual flow air
            leakage parameters are not meant to be representative of real values, since
            the infiltration flow rate is an average of the actual, variable surface
            flow dynamics. If False, the airflow leakage parameters are selected from a
            crack data template, corresponding to the provided leakage_type. Since these
            leakage parameters reflect empirically obtained values for different surface
            types, they will result in a more realistic simulation of air flow through
            orifices and cracks. In both cases, interzone airflow leakage parameters are
            referenced from the crack data template, corresponding to the provided
            leakage_type.

        atmospheric_pressure: Atmospheric pressure measurement in Pascals used to
            calculate dry air density. (Default: 101325).
    """

    assert isinstance(window_vent_controls, (tuple, list)) and \
        len(window_vent_controls) == len(rooms), 'The window_vent_control parameter ' \
        'must be a list or tuple of VentilationControl objects equal to the list of ' \
        'rooms. Got a {} with length {}.'.format(
            type(window_vent_controls), len(window_vent_controls))

    # simplify parameters
    if leakage_type == 'Tight':
        int_cracks = crack_data_dict['internal_tight_cracks']
        ext_cracks = crack_data_dict['external_tight_cracks']
    elif leakage_type == 'Average':
        int_cracks = crack_data_dict['internal_average_cracks']
        ext_cracks = crack_data_dict['external_average_cracks']
    elif leakage_type == 'Leaky':
        int_cracks = crack_data_dict['internal_leaky_cracks']
        ext_cracks = crack_data_dict['external_leaky_cracks']
    else:
        raise AssertionError('leakage_type must be "Tight", "Average", '
                             'or "Leaky". Got: {}.'.format(leakage_type))
    air_density = air_density_from_pressure(atmospheric_pressure)

    # generate
    for room, window_vent_control in zip(rooms, window_vent_controls):

        # assign ventilation control to room
        room.properties.energy.window_vent_control = window_vent_control

        # get grouped faces by type that experience air flow leakage
        ext_faces, int_faces = room.properties.energy.afn_face_groups()

        has_room_infiltration = room.properties.energy.infiltration is not None

        # mutate surfaces with AFN flow parameters
        if use_room_infiltration and has_room_infiltration:
            room.properties.energy.exterior_afn_from_infiltration_load(
                ext_faces, air_density)
        else:
            exterior_afn(ext_faces, ext_cracks)

        interior_afn(int_faces, int_cracks)

