# coding=utf-8
"""Functions to generate airflownetwork from list of rooms."""
from __future__ import division

from honeybee.boundarycondition import Outdoors
from honeybee.facetype import Wall, RoofCeiling

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


internal_average_cracks = InternalCracks(
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


internal_leaky_cracks = InternalCracks(
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


def _group_faces_by_type(faces):
    """Group faces and subfaces by types that experience exterior air flow leakage.

    Args:
        faces: List of Face objects.

    Return:
        A tuple with four items:
            * walls: List of exterior Wall type Face objects.
            * roofceilings: List of exterior RoofCeiling type Face objects.
            * apertures: List of exterior Aperture sub-face Face objects.
            * doors: List of exterior Door sub-face Face objects.
    """

    walls, roofceilings, apertures, doors = [], [], [], []

    for face in faces:
        if isinstance(face.boundary_condition, Outdoors):
            if isinstance(face.type, Wall):
                walls.append(face)
                apertures.extend(face.apertures)
                doors.extend(face.doors)
            elif isinstance(face.type, RoofCeiling):
                roofceilings.append(face)
                apertures.extend(face.apertures)  # Add any potential skylights

    return walls, roofceilings, apertures, doors


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


def generate(rooms, window_vent_controls, rooms_adjacency_info=None,
             internal_leakage_type='Average'):
    """
    Generate an AirflowNetwork from a list of Honeybee Room objects and associated data.

    This function will derive the leakage component parameters for the ventilation
    cooling energy properties of Honeybee Room and Face objects to simulate an
    EnergyPlus AirflowNetwork. The exterior airflow leakage parameters will be
    calculated to be consistent with the specified Room infiltration rate, while
    interzone airflow leakage parameters are referenced from the DesignBuilder Cracks
    template, based on the 'internal_leakage_type' parameter.

    VentilationOpening objects will be added to Aperture and Door objects if not already
    defined. If already defined, only the parameters defining leakage when the openings
    are closed will be overwritten. AFNCrack objects will be added to all external and
    internal Face objects.

    Args:
        rooms: List of Honeybee Room objects that make up the Airflow Network. The
            adjacencies of these rooms must be solved.
        window_vent_controls: List or tuple of VentilationControl objects corresponding
            to the list of rooms, or a single VentilationControl.
        rooms_adjacency_info: Either a dictionary of adjacency information returned from
            the Room.solve_adjacency method, or None. If None the air flow through
            interzone faces and sub-faces will not be modeled.
        internal_leakage_type: Text identifying the leakiness of the internal walls. This
            will be used to determine the air mass flow rate parameters for cracks in
            internal floors, ceilings and walls. (Default: 'Average').
            Choose from the following:

            * Tight
            * Average
            * Leaky
    """

    assert isinstance(window_vent_controls, (tuple, list)) and \
        len(window_vent_controls) == len(rooms), 'The window_vent_control parameter ' \
        'must be a list or tuple of VentilationControl objects equal to the list of ' \
        'rooms. Got a {} with length {}.'.format(
            type(window_vent_controls), len(window_vent_controls))

    # simplify reference cracks
    if internal_leakage_type == 'Tight':
        int_cracks = internal_tight_cracks
    elif internal_leakage_type == 'Average':
        int_cracks = internal_average_cracks
    elif internal_leakage_type == 'Leaky':
        int_cracks = internal_leaky_cracks
    else:
        raise AssertionError('internal_leakage_type must be "Tight", "Average", '
                             'or "Leaky". Got: {}.'.format(internal_leakage_type))

    # make reference AFNCracks
    int_wall_crack = AFNCrack(int_cracks.wall_cq, int_cracks.wall_n, 1)
    int_floorceiling_crack = \
        AFNCrack(int_cracks.floorceiling_cq, int_cracks.floorceiling_n)
    int_wall_crack.lock()
    int_floorceiling_crack.lock()

    # loop through all rooms get wall data
    for i, room in enumerate(rooms):

        # assign ventilation control to room
        room.properties.energy.window_vent_control = window_vent_controls[i]

        # get exterior faces by type that experience air flow leakage
        ext_walls, ext_roofceilings, ext_apertures, ext_doors = \
            _group_faces_by_type(room.faces)

        if len(ext_walls) > 0 or len(ext_roofceilings) > 0:
            # get reference air flow data for area leakage
            infil_per_area = room.properties.energy.infiltration.flow_per_exterior_area
            opening_area = sum([ext_aperture.area for ext_aperture in ext_apertures])
            opening_area += sum([ext_door.area for ext_door in ext_doors])

            # solve for leakage parameters of all exposed areas minus apertures/doors
            ext_cq_area = solve_area_leakage_mass_flow_coefficient(
                infil_per_area, room.exposed_area - opening_area,
                DEFAULT_EXTERIOR_CRACK_N)

            # make single AFNCrack for all exterior surfaces
            ext_area_crack = AFNCrack(ext_cq_area, DEFAULT_EXTERIOR_CRACK_N, 1)
            ext_area_crack.lock()

            # add exterior crack leakage components
            for ext_wall in ext_walls:
                ext_wall.properties.energy.vent_crack = ext_area_crack

            for ext_roofceiling in ext_roofceilings:
                ext_roofceiling.properties.energy.vent_crack = ext_area_crack

        # get reference air flow data for perimeter leakage
        if len(ext_doors) > 0 or len(ext_apertures) > 0:
            opening_perimeter = sum([aperture.perimeter for aperture in ext_apertures])
            opening_perimeter += sum([door.perimeter for door in ext_doors])
            infil_per_perimeter = infil_per_area * opening_area / opening_perimeter

            # solve for leakage parameters of all exposed apertures/doors
            ext_cq_perimeter = solve_perimeter_leakage_mass_flow_coefficient(
                infil_per_perimeter, DEFAULT_EXTERIOR_CRACK_N)

            # add exterior opening leakage components
            for ext_aperture in ext_apertures:
                if ext_aperture.properties.energy.vent_opening is None:
                    ext_aperture.is_operable = True
                    ext_aperture.properties.energy.vent_opening = VentilationOpening()
                vent_opening = ext_aperture.properties.energy.vent_opening
                vent_opening.flow_coefficient_closed = ext_cq_perimeter
                vent_opening.flow_exponent_closed = DEFAULT_EXTERIOR_CRACK_N

            for ext_door in ext_doors:
                if ext_door.properties.energy.vent_opening is None:
                    ext_door.properties.energy.vent_opening = VentilationOpening()
                vent_opening = ext_door.properties.energy.vent_opening
                vent_opening.flow_coefficient_closed = ext_cq_perimeter
                vent_opening.flow_exponent_closed = DEFAULT_EXTERIOR_CRACK_N


    # simplify adjacency data
    if rooms_adjacency_info:
        adj_faces = rooms_adjacency_info['adjacent_faces']
        adj_apertures = rooms_adjacency_info['adjacent_apertures']
        adj_doors = rooms_adjacency_info['adjacent_doors']

    if rooms_adjacency_info:
        # Note that only one of the adjacent interzone surfaces need to be assigned
        # a leakage component. If both adjacent surfaces have a leakage component,
        # the air flow through the surface will be counted twice.

        # add interior crack leakage components
        for adj_face1, adj_face2 in adj_faces:
            if isinstance(adj_face1.type, Wall):
                adj_face1.properties.energy.vent_crack = int_wall_crack
            else:  # floor or ceiling
                adj_face1.properties.energy.vent_crack = int_floorceiling_crack
            adj_face2.properties.energy.vent_crack = None

        # add interior opening leakage components
        for adj_aperture1, adj_aperture2 in adj_apertures:
            if adj_aperture1.properties.energy.vent_opening is None:
                adj_aperture1.is_operable = True
                adj_aperture1.properties.energy.vent_opening = VentilationOpening()
            vent_opening = adj_aperture1.properties.energy.vent_opening
            vent_opening.flow_coefficient_closed = int_cracks.window_cq
            vent_opening.flow_exponent_closed = int_cracks.window_n

        for adj_door1, adj_door2 in adj_doors:
            if adj_door1.properties.energy.vent_opening is None:
                adj_door1.properties.energy.vent_opening = VentilationOpening()
            vent_opening = adj_door1.properties.energy.vent_opening
            vent_opening.flow_coefficient_closed = int_cracks.door_cq
            vent_opening.flow_exponent_closed = int_cracks.door_n

