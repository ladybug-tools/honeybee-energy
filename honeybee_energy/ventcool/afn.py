# coding=utf-8
"""Functions to generate an Airflow Network for a list of rooms."""
from __future__ import division

import math

from .crack import AFNCrack
from .opening import VentilationOpening
from ._crack_data import CRACK_TEMPLATE_DATA


def _air_density_from_pressure(atmospheric_pressure=101325, air_temperature=20.0):
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


def _interior_afn(interior_face_groups, int_cracks, air_density=1.2041):
    """Mutate interior faces and subfaces to model airflow through cracks and openings.

    This function creates an AFNCrack object with an air mass flow coefficient that
    reflects the leakage characteristics of faces with different areas and types.
    This requires multiplying the area-normalized air mass flow coefficients from the
    reference crack data in int_cracks, by the wall area. This function assumes adjacent
    faces share the same type and area properties so that the computed leakage parameters
    are equivalent for each face.

    Args:
        interior_face_groups: A tuple with four groups of interior faces types

            - int_walls: List of interior Wall type Face objects.

            - int_floorceilings: List of interior RoofCeiling and Floor type Face
                objects.

            - int_apertures: List of interior Aperture Face objects.

            - int_doors: List of interior Door Face objects.

            - int_air: List of interior Faces with AirBoundary face type.

        int_cracks: A dictionary of air mass flow coefficient and exponent data
            corresponding to the face types in the interior_face_groups. Face
            data flow coefficients should be normalized by surface area, and closed
            opening flow coefficients should be normalized by edge lengths, for example:

        .. code-block:: python

            {
            "wall_flow_cof": 0.003, # wall flow coefficient
            "wall_flow_exp": 0.75, # wall flow exponent
            "floorceiling_flow_cof": 0.0009, # floorceiling flow coefficient
            "floorceiling_flow_exp": 0.7, # floorceiling flow exponent
            "window_flow_cof": 0.0014, # window flow coefficient
            "window_flow_exp": 0.65, # window flow exponent
            "door_flow_cof": 0.02, # door flow coefficient
            "door_flow_exp": 0.6 # door flow exponent
            }

        air_density: Air density in kg/m3. (Default: 1.2041 represents
            air density at a temperature of 20 C and 101325 Pa).
    """

    # simplify parameters
    int_walls, int_floorceilings, int_apertures, int_doors, int_air = interior_face_groups

    # add interior crack leakage components for opaque building Faces
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

    # add interior crack leakage for air boundary Faces
    for int_ab in int_air:
        # derive (large) flow coefficient from the orifice equation with 0.65 discharge
        flow_cof = 0.65 * int_ab.area * math.sqrt(air_density * 2)
        flow_exp = 0.5  # always use 0.5 exponent for a large hole-shaped opening
        int_ab.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    # add interior opening leakage components
    for int_aperture in int_apertures:
        if int_aperture.properties.energy.vent_opening is None:
            int_aperture.is_operable = True
            int_aperture.properties.energy.vent_opening = \
                VentilationOpening(fraction_area_operable=0)
        vent_opening = int_aperture.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = int_cracks['window_flow_cof']
        vent_opening.flow_exponent_closed = int_cracks['window_flow_exp']

    for int_door in int_doors:
        if int_door.properties.energy.vent_opening is None:
            int_door.properties.energy.vent_opening = \
                VentilationOpening(fraction_area_operable=0)
        vent_opening = int_door.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = int_cracks['door_flow_cof']
        vent_opening.flow_exponent_closed = int_cracks['door_flow_exp']


def _exterior_afn(exterior_face_groups, ext_cracks):
    """Mutate exterior faces and subfaces to model airflow through cracks and openings.

    This function creates an AFNCrack object with an air mass flow coefficient that
    reflects the leakage characteristics of faces with different areas and types.
    This requires multiplying the area-normalized air mass flow coefficients from the
    reference crack data in ext_cracks, by the wall area.

    Args:
        exterior_face_groups: A tuple with five groups of exterior envelope types

            -   ext_walls - A list of exterior Wall type Face objects.

            -   ext_roofs - A list of exterior RoofCeiling type Face objects.

            -   ext_floors - A list of exterior Floor type Face objects, like you
                would find in a cantilevered Room.

            -   ext_apertures - A list of exterior Aperture Face objects.

            -   ext_doors - A list of exterior Door Face objects.

        ext_cracks: A dictionary of air mass flow coefficient and exponent data
            corresponding to the face types in the exterior_face_groups. Face
            data flow coefficients should be normalized by surface area, and closed
            opening flow coefficients should be normalized by edge lengths, for example:

        .. code-block:: python

            {
            "wall_flow_cof": 0.003, # wall flow coefficient
            "wall_flow_exp": 0.75, # wall flow exponent
            "roof_flow_cof": 0.0009, # roof flow coefficient
            "roof_flow_exp": 0.7, # roof flow exponent
            "floor_flow_cof": 0.0009, # floor flow coefficient
            "floor_flow_exp": 0.7, # floor flow exponent
            "window_flow_cof": 0.0014, # window flow coefficient
            "window_flow_exp": 0.65, # window flow exponent
            "door_flow_cof": 0.02, # door flow coefficient
            "door_flow_exp": 0.6 # door flow exponent
            }
    """

    # simplify parameters
    ext_walls, ext_roofs, ext_floors, ext_apertures, ext_doors = exterior_face_groups

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

    for ext_floor in ext_floors:
        face_area = ext_floor.area
        flow_cof = ext_cracks['floor_flow_cof'] * face_area
        flow_exp = ext_cracks['floor_flow_exp']
        ext_floor.properties.energy.vent_crack = AFNCrack(flow_cof, flow_exp)

    # add exterior opening leakage components
    for ext_aperture in ext_apertures:
        if ext_aperture.properties.energy.vent_opening is None:
            ext_aperture.is_operable = True
            ext_aperture.properties.energy.vent_opening = \
                VentilationOpening(fraction_area_operable=0)
        vent_opening = ext_aperture.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = ext_cracks['window_flow_cof']
        vent_opening.flow_exponent_closed = ext_cracks['window_flow_exp']

    for ext_door in ext_doors:
        if ext_door.properties.energy.vent_opening is None:
            ext_door.properties.energy.vent_opening = \
                VentilationOpening(fraction_area_operable=0)
        vent_opening = ext_door.properties.energy.vent_opening
        vent_opening.flow_coefficient_closed = ext_cracks['door_flow_cof']
        vent_opening.flow_exponent_closed = ext_cracks['door_flow_exp']


def generate(rooms, leakage_type='Medium', use_room_infiltration=True,
             atmospheric_pressure=101325):
    """
    Mutate a list of Honeybee Room objects to represent an EnergyPlus AirflowNetwork.

    This function will compute leakage component parameters for the ventilation
    cooling energy properties of Honeybee Room and Face objects to simulate an
    EnergyPlus AirflowNetwork. The leakage flow coefficient and exponent values are
    referenced from the DesignBuilder Cracks Template[1], which provides typical air
    changes rates for different envelope tightness classifications for a range of
    building types. Specifically this function references leakage values for an
    'Excellent', 'Medium', and 'VeryPoor' classification of envelope tightness.

    VentilationOpening objects will be added to Aperture and Door objects if not already
    defined, with the fraction_area_operable set to 0. If already defined, only the
    parameters defining leakage when the openings are closed will be overwritten.
    AFNCrack objects will be added to all external and internal Face objects, and any
    existing AFNCrack objects will be overwritten.

    Note:
        [1] DesignBuilder (6.1.6.008). DesignBuilder Software Ltd, 2000-2020.

    Args:
        rooms: List of Honeybee Room objects that make up the Airflow Network. The
            adjacencies of these rooms must be solved.
        leakage_type: Text identifying the leakiness of the internal walls. This
            will be used to determine the air mass flow rate parameters for cracks in
            internal floors, ceilings and walls. (Default: ''Medium'').
            Choose from the following:

            * Excellent
            * Medium
            * VeryPoor

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
        atmospheric_pressure: Optional number to define the atmospheric pressure
            measurement in Pascals used to calculate dry air density. (Default: 101325).
    """
    # simplify parameters
    if leakage_type == 'Excellent':
        int_cracks = CRACK_TEMPLATE_DATA['internal_excellent_cracks']
        ext_cracks = CRACK_TEMPLATE_DATA['external_excellent_cracks']
    elif leakage_type == 'Medium':
        int_cracks = CRACK_TEMPLATE_DATA['internal_medium_cracks']
        ext_cracks = CRACK_TEMPLATE_DATA['external_medium_cracks']
    elif leakage_type == 'VeryPoor':
        int_cracks = CRACK_TEMPLATE_DATA['internal_verypoor_cracks']
        ext_cracks = CRACK_TEMPLATE_DATA['external_verypoor_cracks']
    else:
        raise AssertionError('leakage_type must be "Excellent", "Medium", '
                             'or "VeryPoor". Got: {}.'.format(leakage_type))

    # generate the airflow newtwork
    for room in rooms:
        # get grouped faces by type that experience air flow leakage
        ext_faces, int_faces = room.properties.energy.envelope_components_by_type()

        # mutate surfaces with AFN flow parameters
        rho = _air_density_from_pressure(atmospheric_pressure)
        if use_room_infiltration and room.properties.energy.infiltration is not None:
            room.properties.energy.exterior_afn_from_infiltration_load(ext_faces, rho)
        else:
            _exterior_afn(ext_faces, ext_cracks)
        _interior_afn(int_faces, int_cracks, rho)
