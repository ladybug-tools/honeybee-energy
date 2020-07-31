# coding=utf-8

from honeybee.model import Model
from honeybee.room import Room
from honeybee.door import Door
from honeybee.facetype import face_types, Floor, RoofCeiling
from honeybee.boundarycondition import boundary_conditions

import honeybee_energy.lib.programtypes as prog_type_lib

from honeybee_energy.ventcool import afn
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.load.infiltration import Infiltration

from ladybug_geometry.geometry3d.pointvector import Point3D, Vector3D
from ladybug_geometry.geometry3d.plane import Plane
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

import pytest
from pprint import pprint as pp


def test_group_faces_by_boundary_condition():
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

    rooms = [sroom, nroom]
    Room.solve_adjacency(rooms, 0.01)

    extf, intf, grdf = afn._group_faces_by_boundary_condition(rooms[0].faces)

    assert len(extf) == 4
    assert len(intf) == 1
    assert len(grdf) == 1

    assert 'SouthRoom..Face1' in [f.identifier for f in extf]
    assert 'SouthRoom..Face3' in [f.identifier for f in intf]


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

    walls, roofceilings, floors, airboundaries, apertures, doors = \
        afn._group_faces_by_type(room.faces)
    floorceilings = roofceilings + floors

    assert len(walls) == 4
    assert len(floorceilings) == 2
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


def test_afn_single_window():
    """Test adding afn to single zone with windows."""
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
    rooms = afn.generate(model.rooms, window_vent_controls)

    # Check that walls have AFNCrack in face
    room = rooms[0]
    faces = room.faces
    #pp(faces)
    #pp([face.type for face in faces])

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

    # TODO test AFN crack parameters
    # TODO test window openings


def test_afn_simple_multi():
    """Test adding afn to multiple zones no windows."""
    # TODO: finish test.
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

    # TODO add windows and door btwn window
    rooms = [sroom, nroom]
    for room in rooms:
        # Add program and hvac
        room.properties.energy.program_type = prog_type_lib.office_program

    adj_info = Room.solve_adjacency(rooms, 0.01)

    # sface = adj_info['adjacent_faces'][0][0]
    # nface = adj_info['adjacent_faces'][0][1]
    # print(sface.type, sface.boundary_condition)
    # print(nface.type, nface.boundary_condition)

    model = Model('Two_Zone_Simple', rooms)

    window_vent_controls = [VentilationControl().duplicate() for _ in rooms]
    rooms = afn.generate(model.rooms, window_vent_controls)

    sroom, nroom = rooms