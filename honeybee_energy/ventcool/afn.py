# coding=utf-8
"""Functions to generate an Airflow Network for a list of rooms."""
from __future__ import division
import math

from .crack import AFNCrack
from .opening import VentilationOpening
from ._crack_data import CRACK_TEMPLATE_DATA


# TODO: Move to ladybug_geometry
def _compute_bounding_box_x(geometries):
    """Calculate minimum and maximum x coordinates of multiple geometries.

    Note this function returns the coordinate extents relative to the standard
    basis. If extents relative to a rotated bounding box is required, the geometries
    need to be rotated to the standard basis before running this function.
    """

    geoms = geometries
    min_x, max_x = geoms[0].min.x, geoms[0].max.x

    for geom in geoms[1:]:
        if geom.min.x < min_x:
            min_x = geom.min.x
        if geom.max.x > max_x:
            max_x = geom.max.x

    return min_x, max_x


# TODO: Move to ladybug_geometry
def _compute_bounding_box_y(geometries):
    """Calculate minimum and maximum y coordinates of multiple geometries.

    Note this function returns the coordinate extents relative to the standard
    basis. If extents relative to a rotated bounding box is required, the geometries
    need to be rotated to the standard basis before running this function.
    """

    geoms = geometries
    min_y, max_y = geoms[0].min.y, geoms[0].max.y

    for geom in geoms[1:]:
        if geom.min.y < min_y:
            min_y = geom.min.y
        if geom.max.y > max_y:
            max_y = geom.max.y

    return min_y, max_y


# TODO: Move to ladybug_geometry
def _compute_bounding_box_z(geometries):
    """Calculate minimum and maximum z coordinates of multiple geometries.

    Note this function returns the coordinate extents relative to the standard
    basis. If extents relative to a rotated bounding box is required, the geometries
    need to be rotated to the standard basis before running this function.
    """

    geoms = geometries
    min_z, max_z = geoms[0].min.z, geoms[0].max.z

    for geom in geometries:
        if geom.max.z > max_z:
            max_z = geom.max.z
        if geom.min.z < min_z:
            min_z = geom.min.z

    return min_z, max_z


# TODO: Move to ladybug_geometry
def _compute_bounding_box_extents(geometries, axis_angle=0):
    """Calculate the extents of an oriented bounding box from an array of 3D geometry objects.

    Args:
        geometries: An array of 3D geometry objects.
        axis_angle: The counter-clockwise rotation angle in radians in the xy plane
            to represent the orientation of the bounding box extents. (Default: 0).
    Returns:
        The distances associated with the width, length and height of the bounding box.
    """

    geoms = geometries
    theta = -axis_angle / 180.0 * math.pi
    cpt = geoms[0].vertices[0]

    if abs(axis_angle) > 1e-10:
        geoms = [geom.rotate_xy(theta, cpt) for geom in geoms]

    xx = _compute_bounding_box_x(geoms)
    yy = _compute_bounding_box_y(geoms)
    zz = _compute_bounding_box_z(geoms)

    return xx[1] - xx[0], yy[1] - yy[0], zz[1] - zz[0]


def _compute_building_type(bounding_box_extents):
    """Compute the relationship between building footprint and height for AirflowNetwork.

    Args:
        bounding_box_extents: A tuple with three numbers representing the distance of
            the bounding box width, length, and height.
        rooms: List of Honeybee Room objects.
    Returns:
        Either a 'LowRise' text string if the bounding box height is less then three
        times the width and length of the footprint, or a 'HighRise' text string
        if the bounding box height is more than three times the width and length of
        the footprint.
    """

    xx, yy, zz = bounding_box_extents

    hdist = 3 * max(xx, yy)
    zdist = zz

    return 'LowRise' if zdist <= hdist else 'HighRise'


def _compute_aspect_ratio(bounding_box_extents):
    """Compute the AirflowNetwork aspect ratio of a building.

    Args:
        bounding_box_extents: A tuple with three numbers representing the distance of
            the bounding box width, length, and height.
    Returns:
        A number representing the ratio of length of the short axis divided by the
        length of the long axis.
    """

    xx, yy, _ = bounding_box_extents

    if xx < yy:
        return xx / yy
    else:
        return yy / xx


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


def _interior_afn(interior_face_groups, int_cracks):
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
    air_density = _air_density_from_pressure(atmospheric_pressure)

    # generate
    for room in rooms:

        # get grouped faces by type that experience air flow leakage
        ext_faces, int_faces = room.properties.energy.envelope_components_by_type()

        has_room_infiltration = room.properties.energy.infiltration is not None

        # mutate surfaces with AFN flow parameters
        if use_room_infiltration and has_room_infiltration:
            room.properties.energy.exterior_afn_from_infiltration_load(
                ext_faces, air_density)
        else:
            _exterior_afn(ext_faces, ext_cracks)

        _interior_afn(int_faces, int_cracks)
