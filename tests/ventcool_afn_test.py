# coding=utf-8

from honeybee.model import Model
from honeybee.room import Room
from honeybee.door import Door
from honeybee.boundarycondition import Surface, Outdoors
from honeybee.facetype import face_types

import honeybee_energy.lib.programtypes as prog_type_lib
from honeybee_energy.ventcool import afn
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool._crack_data import CRACK_TEMPLATE_DATA

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D
from ladybug_geometry.bounding import bounding_box_extents

import pytest
import math


def test_density_from_pressure():
    """Test derivation of dry air density."""

    chk_d = afn._air_density_from_pressure(101325, 20.0)
    assert chk_d == pytest.approx(1.2041, abs=1e-4)

    chk_d = afn._air_density_from_pressure(100000, 0)
    assert chk_d == pytest.approx(1.2754, abs=1e-4)


def test_afn_plenum_zone():
    """Test case where no infiltration load exists."""
    zone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    room = Room.from_polyface3d(
        'PlenumRoom', Polyface3D.from_offset_face(zone_pts, 1))
    room.properties.energy.program_type = prog_type_lib.plenum_program

    # Make model
    model = Model('PlenumSimple', [room])

    # generate afn, w/ average leakage
    afn.generate(model.rooms, leakage_type='Medium', use_room_infiltration=True)
    faces = model.faces

    # check ext wall
    crack = faces[1].properties.energy.vent_crack
    chk_cof = CRACK_TEMPLATE_DATA['external_medium_cracks']['wall_flow_cof']
    chk_exp = CRACK_TEMPLATE_DATA['external_medium_cracks']['wall_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[1].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # check roof
    crack = faces[5].properties.energy.vent_crack
    chk_cof = CRACK_TEMPLATE_DATA['external_medium_cracks']['roof_flow_cof']
    chk_exp = CRACK_TEMPLATE_DATA['external_medium_cracks']['roof_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[5].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # generate afn, w/ tight leakage
    afn.generate(model.rooms, leakage_type='Excellent', use_room_infiltration=False)
    faces = model.faces

    # check ext wall
    crack = faces[1].properties.energy.vent_crack
    chk_cof = CRACK_TEMPLATE_DATA['external_excellent_cracks']['wall_flow_cof']
    chk_exp = CRACK_TEMPLATE_DATA['external_excellent_cracks']['wall_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[1].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # check roof
    crack = faces[5].properties.energy.vent_crack
    chk_cof = CRACK_TEMPLATE_DATA['external_excellent_cracks']['roof_flow_cof']
    chk_exp = CRACK_TEMPLATE_DATA['external_excellent_cracks']['roof_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[5].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)


def test_afn_single_zone():
    """Test adding afn to single zone with window and door."""
    zone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    room = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(zone_pts, 3))

    # Add door and window
    door_pts = [Point3D(2, 10, 0.01), Point3D(4, 10, 0.01),
                Point3D(4, 10, 2.50), Point3D(2, 10, 2.50)]
    door = Door('FrontDoor', Face3D(door_pts))
    room[3].add_door(door)  # Door to north face
    room[1].apertures_by_ratio(0.3)  # Window on south face
    room.properties.energy.program_type = prog_type_lib.office_program

    # Make model
    model = Model('Single_Zone_Simple', [room])
    afn.generate(model.rooms)

    # Check that walls have AFNCrack in face
    room = model.rooms[0]
    faces = room.faces

    # Test that no cracks to roofs/floors were added
    assert faces[0].properties.energy.vent_crack is None

    # Test that we have cracks in walls
    assert isinstance(faces[1].properties.energy.vent_crack, AFNCrack)
    assert isinstance(faces[2].properties.energy.vent_crack, AFNCrack)
    assert isinstance(faces[3].properties.energy.vent_crack, AFNCrack)
    assert isinstance(faces[4].properties.energy.vent_crack, AFNCrack)
    assert isinstance(faces[5].properties.energy.vent_crack, AFNCrack)

    # Test that we have ventilation openings
    assert isinstance(
        faces[1].apertures[0].properties.energy.vent_opening, VentilationOpening)
    assert isinstance(
        faces[3].doors[0].properties.energy.vent_opening, VentilationOpening)

    # Calculate parameters for checks
    qv = room.properties.energy.infiltration.flow_per_exterior_area
    n = 0.65
    dP = 4
    d = afn._air_density_from_pressure()

    # Test flow coefficients and exponents
    for i in range(1, 6):

        opening_area = 0
        # check openings
        if i == 1 or i == 3:
            if i == 1:
                opening_area = faces[i].apertures[0].area
                vface = faces[i].apertures[0]
            elif i == 3:
                opening_area = faces[i].doors[0].area
                vface = faces[i].doors[0]
            v = vface.properties.energy.vent_opening
            chk_cq = qv * d / (dP ** n) * vface.area / vface.perimeter
            cq = v.flow_coefficient_closed
            n = v.flow_exponent_closed
            assert chk_cq == pytest.approx(cq, abs=1e-10)
            assert 0.65 == pytest.approx(n, abs=1e-10)

        # check opaque areas
        chk_cq = qv * d / (dP ** n) * (faces[i].area - opening_area)
        cq = faces[i].properties.energy.vent_crack.flow_coefficient
        n = faces[i].properties.energy.vent_crack.flow_exponent
        assert chk_cq == pytest.approx(cq, abs=1e-10)
        assert 0.65 == pytest.approx(n, abs=1e-10)

    # confirm that auto-calculated flow coefficients produce room.infiltration rate
    total_room_flow = 0
    for i in range(1, 6):
        if i == 1 or i == 3:
            if i == 1:
                vface = faces[i].apertures[0]
            elif i == 3:
                vface = faces[i].doors[0]
            v = vface.properties.energy.vent_opening
            cq = v.flow_coefficient_closed * vface.perimeter
            total_room_flow += cq * (dP ** v.flow_exponent_closed) / d

        crack = faces[i].properties.energy.vent_crack
        cq = crack.flow_coefficient
        total_room_flow += cq * (dP ** crack.flow_exponent) / d

    chk_infil = total_room_flow / room.exposed_area  # m3/s/m2
    assert qv == pytest.approx(chk_infil, abs=1e-10)


def test_afn_multizone():
    """Test adding afn to multiple zones with windows."""
    # South Room
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 3))

    # North Room
    nzone_pts = Face3D(
        [Point3D(0, 10), Point3D(20, 10), Point3D(20, 20), Point3D(0, 20)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 3))

    # Add adjacent interior windows
    sroom[3].apertures_by_ratio(0.3)  # Window on south face
    nroom[1].apertures_by_ratio(0.3)  # Window on north face

    # rooms
    rooms = [sroom, nroom]
    for room in rooms:
        # Add program and hvac
        room.properties.energy.program_type = prog_type_lib.office_program

    # Make model
    model = Model('Two_Zone_Simple', rooms)

    # Make interior faces
    adj_info = Room.solve_adjacency(rooms, 0.01)

    inter_sface3 = adj_info['adjacent_faces'][0][0]
    inter_nface1 = adj_info['adjacent_faces'][0][1]
    inter_saper3 = adj_info['adjacent_apertures'][0][0]
    inter_naper1 = adj_info['adjacent_apertures'][0][1]

    # confirm face adjacencies
    assert len(adj_info['adjacent_faces']) == 1
    assert isinstance(inter_sface3.boundary_condition, Surface)
    assert isinstance(inter_nface1.boundary_condition, Surface)

    # confirm aper adjacencies
    assert len(adj_info['adjacent_apertures']) == 1
    assert isinstance(inter_saper3.boundary_condition, Surface)
    assert isinstance(inter_naper1.boundary_condition, Surface)

    # Make afn
    afn.generate(model.rooms)

    # get cracks
    int_cracks = CRACK_TEMPLATE_DATA['internal_medium_cracks']

    # Check internal cracks in adjacent faces
    int_crack = sroom[3].properties.energy.vent_crack
    ref_area = sroom[3].area - sroom[3].apertures[0].area
    assert int_crack.flow_coefficient == pytest.approx(
        int_cracks['wall_flow_cof'] * ref_area, abs=1e-10)
    assert int_crack.flow_exponent == pytest.approx(
        int_cracks['wall_flow_exp'], abs=1e-10)

    int_crack = nroom[1].properties.energy.vent_crack
    assert int_crack.flow_coefficient == pytest.approx(
        int_cracks['wall_flow_cof'] * ref_area, abs=1e-10)
    assert int_crack.flow_exponent == pytest.approx(
        int_cracks['wall_flow_exp'], abs=1e-10)

    # Check that there is only one vent opening for interior walls
    assert isinstance(
        sroom[3].apertures[0].properties.energy.vent_opening, VentilationOpening)
    assert isinstance(
        nroom[1].apertures[0].properties.energy.vent_opening, VentilationOpening)

    # confirm that auto-calculated flow coefficients produce room.infiltration rate
    d = afn._air_density_from_pressure()
    dP = 4

    for room in model.rooms:

        total_room_flow = 0
        faces = room.faces
        qv = room.properties.energy.infiltration.flow_per_exterior_area

        for face in faces:
            if isinstance(face.boundary_condition, Outdoors):
                crack = face.properties.energy.vent_crack
                cq = crack.flow_coefficient
                total_room_flow += cq * (dP ** crack.flow_exponent) / d

        chk_infil = total_room_flow / room.exposed_area  # m3/s/m2
        assert qv == pytest.approx(chk_infil, abs=1e-10)


def test_afn_multizone_air_boundary():
    """Test adding afn to multiple zones with an AirBoundary between them."""
    # South Room
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 3))

    # North Room
    nzone_pts = Face3D(
        [Point3D(0, 10), Point3D(20, 10), Point3D(20, 20), Point3D(0, 20)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 3))

    # Make interior faces
    rooms = [sroom, nroom]
    adj_info = Room.solve_adjacency(rooms, 0.01)
    inter_sface3 = adj_info['adjacent_faces'][0][0]
    inter_nface1 = adj_info['adjacent_faces'][0][1]
    inter_sface3.type = face_types.air_boundary
    inter_nface1.type = face_types.air_boundary

    # Make afn
    afn.generate(rooms)

    sface3_crack = inter_sface3.properties.energy.vent_crack
    nface1_crack = inter_nface1.properties.energy.vent_crack
    assert sface3_crack is not None
    assert nface1_crack is not None
    assert sface3_crack.flow_coefficient > 50  # ensure it's nice and large
    assert nface1_crack.flow_coefficient > 50  # ensure it's nice and large
    assert sface3_crack.flow_exponent == 0.5
    assert nface1_crack.flow_exponent == 0.5


def test_compute_bounding_box_extents_simple():
    """Test the bounding box extents calculation of ladybug_geometry."""
    # South Room 1: 20 x 6 x 3
    szone1 = Face3D(
        [Point3D(-10, -3), Point3D(10, -3), Point3D(10, 3), Point3D(-10, 3)])
    sroom1 = Room.from_polyface3d('SouthRoom1', Polyface3D.from_offset_face(szone1, 3))
    theta = 90.0
    sroom1.rotate_xy(theta, Point3D(0, 0, 0))
    xx, yy, zz = bounding_box_extents([sroom1.geometry], math.radians(theta))

    assert xx == pytest.approx(20, abs=1e-10)
    assert yy == pytest.approx(6, abs=1e-10)
    assert zz == pytest.approx(3, abs=1e-10)


def test_compute_bounding_box_extents_complex():
    """Test the bounding box extents of ladybug_geometry."""
    # South Room 1: 21 x 10.5 x 3
    szone1 = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10.5), Point3D(0, 10.5)])
    sroom1 = Room.from_polyface3d('SouthRoom1', Polyface3D.from_offset_face(szone1, 3))

    # North Room 1: 21 x 10.5 x 3
    nzone1 = Face3D(
        [Point3D(0, 10.5), Point3D(21, 10.5), Point3D(21, 21), Point3D(0, 21)])
    nroom1 = Room.from_polyface3d('NorthRoom1', Polyface3D.from_offset_face(nzone1, 3))

    # South Room 2: 21 x 10.5 x 3
    szone2 = Face3D(
        [Point3D(0, 0, 3), Point3D(21, 0, 3), Point3D(21, 10.5, 3), Point3D(0, 10.5, 3)])
    sroom2 = Room.from_polyface3d('SouthRoom2', Polyface3D.from_offset_face(szone2, 3))

    # North Room 2: 21 x 10.5 x 3
    nzone2 = Face3D(
        [Point3D(0, 10.5, 3), Point3D(21, 10.5, 3), Point3D(21, 21, 3), Point3D(0, 21, 3)])
    nroom2 = Room.from_polyface3d('NorthRoom2', Polyface3D.from_offset_face(nzone2, 3))

    rooms = [sroom1, nroom1, sroom2, nroom2]
    model = Model('Four_Zone_Simple', rooms)

    # Rotate the buildings
    theta = 30.0
    model.rotate_xy(theta, rooms[0].geometry.vertices[-1])
    geoms = [room.geometry for room in model.rooms]
    xx, yy, zz = bounding_box_extents(geoms, math.radians(theta))

    assert xx == pytest.approx(21, abs=1e-10)
    assert yy == pytest.approx(21, abs=1e-10)
    assert zz == pytest.approx(6, abs=1e-10)


def test_compute_building_type():
    """Test calculation of building type."""
    # Test lowrise: 21 x 21 x 3

    # South Room: 21 x 10.5
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10.5), Point3D(0, 5)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 3))

    # North Room: 21 x 10.5
    nzone_pts = Face3D(
        [Point3D(0, 10.5), Point3D(21, 10.5), Point3D(21, 21), Point3D(0, 21)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 3))

    # Add detail and create the model
    sroom[3].apertures_by_ratio(0.3)  # Window on south face
    nroom[1].apertures_by_ratio(0.3)  # Window on north face
    rooms = [sroom, nroom]
    model = Model('Test_Zone', rooms)

    # autocalculate the building type
    model.properties.energy.autocalculate_ventilation_simulation_control()
    btype = model.properties.energy.ventilation_simulation_control.building_type
    assert btype == 'LowRise'

    # Test highrise 21 x 21 x 63

    # South Room: 21 x 10.5
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10.5), Point3D(0, 10.5)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 63))

    # North Room: 21 x 10.5
    nzone_pts = Face3D(
        [Point3D(0, 10.5), Point3D(21, 10.5), Point3D(21, 21), Point3D(0, 21)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 63))

    # Add detail and create the model
    rooms = [sroom, nroom]
    model = Model('Test_Zone', rooms)
    model.rotate_xy(3, rooms[0].geometry.vertices[0])

    # autocalculate the building type
    model.properties.energy.autocalculate_ventilation_simulation_control()
    btype = model.properties.energy.ventilation_simulation_control.building_type
    assert btype == 'LowRise'

    # Test highrise 21 x 21 x 63.1

    # South Room: 21 x 10.5
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10.5), Point3D(0, 10.5)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 63.1))

    # North Room: 21 x 10.5
    nzone_pts = Face3D(
        [Point3D(0, 10.5), Point3D(21, 10.5), Point3D(21, 21), Point3D(0, 21)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 63.1))

    # Add detail and create the model
    rooms = [sroom, nroom]
    model = Model('Test_Zone', rooms)

    # autocalculate the building type
    model.properties.energy.autocalculate_ventilation_simulation_control()
    btype = model.properties.energy.ventilation_simulation_control.building_type
    assert btype == 'HighRise'


def test_compute_aspect_ratio():
    """Test calculation of aspect ratio."""
    # South Room: 21 x 21 x 3
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 21), Point3D(0, 10)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 3))

    # add detail and create the Model
    rooms = [sroom]
    model = Model('Test_Zone', rooms)

    # autocalculate the aspect ratio
    model.properties.energy.autocalculate_ventilation_simulation_control()
    ar = model.properties.energy.ventilation_simulation_control.aspect_ratio
    assert ar == pytest.approx(1.0, abs=1e-10)
    axis = model.properties.energy.ventilation_simulation_control.long_axis_angle
    assert axis == 0

    # Test lowrise 15 x 21 x 3
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10), Point3D(0, 10)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 3))

    # North Room: 21 x 15 x 3
    nzone_pts = Face3D(
        [Point3D(0, 10), Point3D(21, 10), Point3D(21, 15), Point3D(0, 15)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 3))

    # add detail and create the model
    rooms = [sroom, nroom]
    model = Model('Test_Zone', rooms)

    # autocalculate the aspect ratio
    model.properties.energy.autocalculate_ventilation_simulation_control()
    ar = model.properties.energy.ventilation_simulation_control.aspect_ratio
    assert ar == pytest.approx(15.0 / 21.0, abs=1e-10)
    axis = model.properties.energy.ventilation_simulation_control.long_axis_angle
    assert axis == 90

    # Test 21 x 22 x 3
    szone_pts = Face3D(
        [Point3D(0, 0), Point3D(21, 0), Point3D(21, 10.5), Point3D(0, 10.5)])
    sroom = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(szone_pts, 63.1))

    nzone_pts = Face3D(
        [Point3D(0, 10.5), Point3D(21, 10.5), Point3D(21, 22), Point3D(0, 22)])
    nroom = Room.from_polyface3d(
        'NorthRoom', Polyface3D.from_offset_face(nzone_pts, 3))

    # add detail and create the model
    rooms = [sroom, nroom]
    model = Model('Test_Zone', rooms)

    # autocalculate the aspect ratio
    model.properties.energy.autocalculate_ventilation_simulation_control()
    ar = model.properties.energy.ventilation_simulation_control.aspect_ratio
    assert ar == pytest.approx(21.0 / 22.0, abs=1e-10)
    axis = model.properties.energy.ventilation_simulation_control.long_axis_angle
    assert axis == 0
