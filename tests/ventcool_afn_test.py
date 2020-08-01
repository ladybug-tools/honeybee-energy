# coding=utf-8

from honeybee.model import Model
from honeybee.room import Room
from honeybee.door import Door
from honeybee.boundarycondition import Surface

import honeybee_energy.lib.programtypes as prog_type_lib

from honeybee_energy.ventcool import afn
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool.control import VentilationControl

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

import pytest
from pprint import pprint as pp


def test_group_faces_by_type():

    zone_pts = Face3D(
        [Point3D(0, 0, 0), Point3D(20, 0, 0), Point3D(20, 10, 0), Point3D(0, 10, 0)])
    room = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(zone_pts, 3))

    door_pts = [Point3D(2, 10, 0.01), Point3D(4, 10, 0.01),
                Point3D(4, 10, 2.50), Point3D(2, 10, 2.50)]
    door = Door('FrontDoor', Face3D(door_pts))
    room[3].add_door(door)  # Door to north face
    room[1].apertures_by_ratio(0.3)  # Window on south face

    walls, roofceilings, apertures, doors = afn._group_faces_by_type(room.faces)

    assert len(walls) == 4
    assert len(roofceilings) == 1
    assert len(apertures) == 1
    assert len(doors) == 1


def test_solve_area_leakage_mass_flow_coefficient():
    """Test calculation of leakage parameters from infiltration load."""

    zone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    room = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(zone_pts, 3))
    room.properties.energy.program_type = prog_type_lib.office_program
    wall_area = 180  # m2
    refn = 0.65

    # Test leaky envelope
    Cq = afn.solve_area_leakage_mass_flow_coefficient(0.0006, wall_area, refn)
    assert Cq == pytest.approx(0.000293386 * wall_area, abs=1e-7)

    # Test average envelope
    Cq = afn.solve_area_leakage_mass_flow_coefficient(0.0003, 180, refn)
    assert Cq == pytest.approx(0.000146693 * wall_area, abs=1e-7)

    # Test tight envelope
    Cq = afn.solve_area_leakage_mass_flow_coefficient(0.0001, 180, refn)
    assert Cq == pytest.approx(4.88976e-5 * wall_area, abs=1e-7)


def test_afn_single_zone():
    """Test adding afn to single zone with window and door."""
    zone_pts = Face3D(
        [Point3D(0, 0), Point3D(20, 0), Point3D(20, 10), Point3D(0, 10)])
    room = Room.from_polyface3d(
        'SouthRoom', Polyface3D.from_offset_face(zone_pts, 3))

    # Add program
    room.properties.energy.program_type = prog_type_lib.office_program

    # Add door and window
    door_pts = [Point3D(2, 10, 0.01), Point3D(4, 10, 0.01),
                Point3D(4, 10, 2.50), Point3D(2, 10, 2.50)]
    door = Door('FrontDoor', Face3D(door_pts))
    room[3].add_door(door)  # Door to north face
    room[1].apertures_by_ratio(0.3)  # Window on south face

    # Make model
    model = Model('Single_Zone_Simple', [room])
    window_vent_controls = [VentilationControl().duplicate()]
    afn.generate(model.rooms, window_vent_controls)

    # Check that walls have AFNCrack in face
    room = model.rooms[0]
    faces = room.faces

    # Test ventcontrol
    assert isinstance(room.properties.energy.window_vent_control, VentilationControl)

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
    exposed_area = (20 * 3 * 2) + (10 * 3 * 2) + (10 * 20)
    opening_area = (2 * 2.49) + (0.3 * 20 * 3)

    # Test surface crack Cq
    area = exposed_area - opening_area
    n = afn.DEFAULT_EXTERIOR_CRACK_N
    chk_cq = qv * area * afn.AIR_DENSITY / (afn.DELTA_PRESSURE ** n)

    assert room.exposed_area == pytest.approx(exposed_area, abs=1e-10)
    assert room.exterior_aperture_area == pytest.approx(0.3 * 20 * 3, abs=1e-10)

    for i in range(1, 6):
        cq = faces[i].properties.energy.vent_crack.air_mass_flow_coefficient_reference
        n = faces[i].properties.energy.vent_crack.air_mass_flow_exponent
        assert chk_cq == pytest.approx(cq, abs=1e-10)
        assert 0.65 == pytest.approx(n, abs=1e-10)

    # test opening cracks Cq
    perimeter = faces[3].doors[0].perimeter + faces[1].apertures[0].perimeter
    chk_cq = qv * opening_area / perimeter * afn.AIR_DENSITY / (afn.DELTA_PRESSURE ** n)

    # window
    v = faces[1].apertures[0].properties.energy.vent_opening
    cq = v.air_mass_flow_coefficient_closed
    n = v.air_mass_flow_exponent_closed
    assert chk_cq == pytest.approx(cq, abs=1e-10)
    assert 0.65 == pytest.approx(n, abs=1 - 10)

    # door
    v = faces[3].doors[0].properties.energy.vent_opening
    cq = v.air_mass_flow_coefficient_closed
    n = v.air_mass_flow_exponent_closed
    assert chk_cq == pytest.approx(cq, abs=1e-10)
    assert 0.65 == pytest.approx(n, abs=1-10)


def test_afn_multi_zone_opening():
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
    model = Model('Two_Zone_Simple', rooms)
    window_vent_controls = [VentilationControl().duplicate() for _ in rooms]
    afn.generate(model.rooms, window_vent_controls, adj_info)

    # Check that there is only one crack in adjacent faces
    assert isinstance(inter_sface3.properties.energy.vent_crack, AFNCrack)
    assert inter_nface1.properties.energy.vent_crack is None

    # Check that there is only one vent opening for interior walls
    assert isinstance(inter_saper3.properties.energy.vent_opening, VentilationOpening)
    assert inter_naper1.properties.energy.vent_opening is None
