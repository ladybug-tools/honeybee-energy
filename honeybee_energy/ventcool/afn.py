# coding=utf-8
"""Functions to generate airflownetwork from list of rooms."""
from __future__ import division

from honeybee.boundarycondition import Outdoors, Ground
from honeybee.facetype import Wall, Floor, AirBoundary

from .crack import AFNCrack
from .opening import VentilationOpening

import collections

# physical constants
AIR_DENSITY = 1.204  # [kg/m3] at temp of 20, and 1 atm
DELTA_PRESSURE = 4  # [Pa] pressure drop across envelope at infiltration measurement
DEFAULT_EXTERIOR_CRACK_N = 0.65  # mass flow exponent for wall leakage


InternalCracks = collections.namedtuple(
    'InternalCracks', 'wall_cq wall_n floorceiling_cq floorceiling_n window_cq ' +
    'window_n door_cq door_n')


internal_tight_cracks = InternalCracks(
    # kg/s/m2 @ 1 Pa
    wall_cq=0.001,
    wall_n=0.75,
    floorceiling_cq=0.00001,
    floorceiling_n=0.7,
    # kg/s/m @ 1 Pa
    window_cq=0.0002,
    window_n=0.7,
    door_cq=0.02,
    door_n=0.7
)


internal_average_cracks  = InternalCracks(
    # kg/s/m2 @ 1 Pa
    wall_cq=0.003,
    wall_n=0.75,
    floorceiling_cq=0.0009,
    floorceiling_n=0.7,
    # kg/s/m @ 1 Pa
    window_cq=0.0014,
    window_n=0.65,
    door_cq=0.02,
    door_n=0.6
)


internal_leaky_cracks  = InternalCracks(
    # kg/s/m2 @ 1 Pa
    wall_cq=0.019,
    wall_n=0.75,
    floorceiling_cq=0.003,
    floorceiling_n=0.7,
    # kg/s/m @ 1 Pa
    window_cq=0.003,
    window_n=0.6,
    door_cq=0.02,
    door_n=0.6
)


def _group_faces_by_boundary_condition(faces):
    """Group faces by boundary condition.

    Args:
        faces: List of Face3D objects.

    Returns:
        Two lists:
            * ext_faces: Face3D objects with Outdoor boundary conditions
            * int_faces: Face3D objects with Surface boundary conditions.
            * grd_faces: Face3D objects with Ground boundary conditions.
    """

    ext_faces, int_faces, grd_faces = [], [], []
    for face in faces:
        if isinstance(face.boundary_condition, Outdoors):
            ext_faces.append(face)
        elif isinstance(face.boundary_condition, Ground):
            grd_faces.append(face)
        else:  # Surface BC
            int_faces.append(face)
    return ext_faces, int_faces, grd_faces


def _group_faces_by_type(faces):
    """Group faces and subfaces by type.

    Args:
        faces: List of Face3D objects.

    Return:
        A tuple with six items:
            * walls: List of Wall type Face3D objects.
            * roofceilings: List of RoofCeiling type Face3D objects.
            * floors: List of Floor type Face3D objects.
            * airboundaries: List of AirBoundary type of Face3D objects.
            * apertures: List of Aperture sub-face Face3D objects.
            * doors: List of Door sub-face Face3D objects.
    """

    walls, roofceilings, floors, airboundaries, apertures, doors = [], [], [], [], [], []

    for face in faces:
        if isinstance(face.type, Wall):
            walls.append(face)
            apertures.extend(face.apertures)
            doors.extend(face.doors)
        elif isinstance(face.type, AirBoundary):
            airboundaries.append(face)
        elif isinstance(face.type, Floor):
            floors.append(face)
        else:
            roofceilings.append(face)
            apertures.extend(face.apertures)  # Add any potential skylights

    return walls, roofceilings, floors, airboundaries, apertures, doors


def solve_area_leakage_mass_flow_coefficient(flow_per_exterior_area, face_area,
                                             mass_flow_exponent, air_density=AIR_DENSITY,
                                             delta_pressure=DELTA_PRESSURE):
    """Calculate leakage parameters for exposed surface area from zone infiltration rate.

    The air mass flow coefficient in kg/s/P^n for a room's exposed surface areas is
    derived from its infiltration flow rate per unit area using the following formula:

        Cq = (Qv * d * A) / dP^n

        where:
            Cq: Air mass flow coefficient at 1 Pa [kg/s/P^n]
            Qv: Volumetric air flow rate per area [m3/s/m2]
            d: Air density [kg/m3]
            A: Surface area [m2]
            dP: Change in pressure across building envelope [Pa]
            n: Air mass flow exponent [-]

    Args:
        flow_per_exterior_area: A numerical value for the intensity of infiltration
            in m3/s per square meter of exterior surface area.
        face_area: A numerical value for the total exterior area in m2.
        mass_flow_exponent: A numerical value for the air mass flow exponent.
        air_density: Reference air density in kg/m3. Default: 1.204 represents
            air density at a temperature of 20 C, and 101325 Pa.
        delta_pressure: Reference building air pressure in Pascals. Default: 4
            represents typical building pressures.

    Returns:
        Air mass flow coefficient in kg/s/P^n at 1 Pa
    """
    qv = flow_per_exterior_area
    a = face_area
    n = mass_flow_exponent
    d = air_density
    dp = delta_pressure

    return qv * a * d / (dp ** n)


def solve_perimeter_leakage_mass_flow_coefficient(flow_per_exterior_perimeter,
                                                  mass_flow_exponent,
                                                  air_density=AIR_DENSITY,
                                                  delta_pressure=DELTA_PRESSURE):
    """Calculate leakage parameters for exposed opening edges from zone infiltration rate.

    The air mass flow coefficient in kg/s/m/P^n for a room's exposed opening perimeter.
    Specifically, this is parameter is used to derive air flow for the four cracks
    around the perimeter of a closed window or door: one along the bottom, one along the
    top, and one on each side. Note that the units for this air mass flow coefficient is
    different from equivalent surface area cracks.

    The air mass flow coefficient is derived from its infiltration flow rate per unit
    length using the following formula:

        Cq = (Qv * d * L) / dP^n

        where:
            Cq: Air mass flow coefficient at 1 Pa [kg/s/m/P^n]
            Qv: Volumetric air flow rate per length [m3/s/m]
            d: Air density [kg/m3]
            dP: Change in pressure across building envelope [Pa]
            n: Air mass flow exponent [-]

    Args:
        flow_per_exterior_perimeter: A numerical value for the intensity of infiltration
            in m3/s per meter of exterior surface perimeter.
        mass_flow_exponent: A numerical value for the air mass flow exponent.
        air_density: Reference air density in kg/m3. Default: 1.204 represents
            air density at a temperature of 20 C, and 101325 Pa.
        delta_pressure: Reference building air pressure in Pascals. Default: 4
            represents typical building pressures.

    Returns:
        Air mass flow coefficient in kg/s/m/P^n at 1 Pa
    """
    qv = flow_per_exterior_perimeter
    n = mass_flow_exponent
    d = air_density
    dp = delta_pressure

    return qv * d / (dp ** n)


def generate(rooms, window_vent_controls, internal_leakage_type='Average'):
    """
    Auto-generate airflow networks given an array of honeybee Rooms and other properties.

    Args:
        rooms: List of Honeybee Room objects that make up the Airflow Network. The
            adjacencies of these rooms must be solved.
        window_vent_controls: List or tuple of VentilationControl objects corresponding
            to the list of rooms, or a single VentilationControl.
        internal_leakage_type: Text identifying the leakiness of the internal walls. This
            will be used to determine the air mass flow rate parameters for cracks in
            internal floors, ceilings and walls. (Default: 'Average').
            Choose from the following:

            * Tight
            * Average
            * Leaky

    Returns:
        rooms: List of Honeybee Room objects with Airflow Network properties set.
    """

    assert isinstance(window_vent_controls, (tuple, list)) and \
        len(window_vent_controls) == len(rooms), 'The window_vent_control parameter ' \
        'must be a list or tuple of VentilationControl objects equal to the list of ' \
        'rooms. Got a {} with length {}.'.format(
            type(window_vent_controls), len(window_vent_controls))

    # define reference cracks
    if internal_leakage_type == 'Tight':
        int_cracks = internal_tight_cracks
    elif internal_leakage_type == 'Average':
        int_cracks = internal_average_cracks
    elif internal_leakage_type == 'Leaky':
        int_cracks = internal_leaky_cracks
    else:
        raise AssertionError('internal_leakage_type must be "Tight", "Average", '
                             'or "Leaky". Got: {}.'.format(internal_leakage_type))

    # loop through all rooms get wall data
    for i, room in enumerate(rooms):

        # assign ventilation control to room
        room.properties.energy.window_vent_control = window_vent_controls[i]

        # group face data, omitting the ground face data
        walls, roofceilings, floors, _, apertures, doors = \
            _group_faces_by_type(room.faces)
        ext_walls, int_walls, _ = _group_faces_by_boundary_condition(walls)
        ext_roofceilings, int_roofceilings, _ = \
            _group_faces_by_boundary_condition(roofceilings)
        _, int_floors, _ = _group_faces_by_boundary_condition(floors)
        int_floorceilings = int_floors + int_roofceilings

        # get reference air flow data for area leakage
        infil_per_area = room.properties.energy.infiltration.flow_per_exterior_area
        opening_area = room.exterior_aperture_area + sum([door.area for door in doors])

        # solve for leakage parameters of all exposed areas minus apertures/doors
        ext_cq_area = solve_area_leakage_mass_flow_coefficient(
            infil_per_area, room.exposed_area - opening_area, DEFAULT_EXTERIOR_CRACK_N)
        ext_area_crack = AFNCrack(ext_cq_area, DEFAULT_EXTERIOR_CRACK_N, 1)

        # get reference air flow data for perimeter leakage
        if len(doors) > 0 and len(apertures) > 0:
            opening_perimeter = sum([aperture.perimeter for aperture in apertures])
            opening_perimeter += sum([door.perimeter for door in doors])
            infil_per_perimeter = infil_per_area * opening_area / opening_perimeter

            # solve for leakage parameters of all exposed apertures/doors
            ext_cq_perimeter = solve_perimeter_leakage_mass_flow_coefficient(
                infil_per_perimeter, DEFAULT_EXTERIOR_CRACK_N)

        # Add crack leakage components
        for ext_wall in ext_walls:
            ext_wall.properties.energy.vent_crack = ext_area_crack.duplicate()

        for ext_roofceiling in ext_roofceilings:
            ext_roofceiling.properties.energy.vent_crack = ext_area_crack.duplicate()

        for int_wall in int_walls:
            int_wall_crack = AFNCrack(int_cracks.wall_cq, int_cracks.wall_n, 1)
            int_wall.properties.energy.vent_crack = int_wall_crack

        for int_floorceiling in int_floorceilings:
            int_floorceiling_crack = \
                AFNCrack(int_cracks.floorceiling_cq, int_cracks.floorceiling_n)
            int_floorceiling.properties.energy.vent_crack = int_floorceiling_crack

        # Add opening leakage components
        for aperture in apertures:
            if aperture.properties.energy.vent_opening is None:
                aperture.is_operable = True
                aperture.properties.energy.vent_opening = VentilationOpening()
            vent_opening = aperture.properties.energy.vent_opening
            vent_opening.air_mass_flow_coefficient_closed = ext_cq_perimeter
            vent_opening.air_mass_flow_exponent_closed = DEFAULT_EXTERIOR_CRACK_N

        for door in doors:
            if door.properties.energy.vent_opening is None:
                door.properties.energy.vent_opening = VentilationOpening()
            vent_opening = door.properties.energy.vent_opening
            vent_opening.air_mass_flow_coefficient_closed = ext_cq_perimeter
            vent_opening.air_mass_flow_exponent_closed = DEFAULT_EXTERIOR_CRACK_N

    return rooms
