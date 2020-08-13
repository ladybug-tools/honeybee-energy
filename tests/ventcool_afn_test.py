# coding=utf-8

from honeybee.model import Model
from honeybee.room import Room
from honeybee.door import Door
from honeybee.boundarycondition import Surface, Outdoors

import honeybee_energy.lib.programtypes as prog_type_lib
from honeybee_energy.ventcool import afn
from honeybee_energy.ventcool.crack import AFNCrack
from honeybee_energy.ventcool.opening import VentilationOpening
from honeybee_energy.ventcool.control import VentilationControl
from honeybee_energy.ventcool.crack_data import crack_data_dict

from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug_geometry.geometry3d.polyface import Polyface3D

import pytest
from pprint import pprint as pp


def test_density_from_pressure():
    """Test derivation of dry air density."""

    chk_d = afn.air_density_from_pressure(101325, 20.0)
    assert chk_d == pytest.approx(1.2041, abs=1e-4)

    chk_d = afn.air_density_from_pressure(100000, 0)
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
    window_vent_controls = [None]

    # generate afn, w/ average leakage
    afn.generate(model.rooms, window_vent_controls, leakage_type='Average',
                 use_room_infiltration=True)
    faces = model.faces

    # check ventcontrol
    assert room.properties.energy.window_vent_control is None

    # check ext wall
    crack = faces[1].properties.energy.vent_crack
    chk_cof = crack_data_dict['external_average_cracks']['wall_flow_cof']
    chk_exp = crack_data_dict['external_average_cracks']['wall_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[1].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # check roof
    crack = faces[5].properties.energy.vent_crack
    chk_cof = crack_data_dict['external_average_cracks']['roof_flow_cof']
    chk_exp = crack_data_dict['external_average_cracks']['roof_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[5].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # generate afn, w/ tight leakage
    afn.generate(model.rooms, window_vent_controls, leakage_type='Tight',
                 use_room_infiltration=False)
    faces = model.faces

    # check ventcontrol
    assert room.properties.energy.window_vent_control is None

    # check ext wall
    crack = faces[1].properties.energy.vent_crack
    chk_cof = crack_data_dict['external_tight_cracks']['wall_flow_cof']
    chk_exp = crack_data_dict['external_tight_cracks']['wall_flow_exp']
    assert crack.flow_coefficient == pytest.approx(chk_cof * faces[1].area, abs=1e-10)
    assert crack.flow_exponent == pytest.approx(chk_exp, abs=1e-10)

    # check roof
    crack = faces[5].properties.energy.vent_crack
    chk_cof = crack_data_dict['external_tight_cracks']['roof_flow_cof']
    chk_exp = crack_data_dict['external_tight_cracks']['roof_flow_exp']
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
    window_vent_controls = [VentilationControl()]
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
    n = 0.65
    dP = 4
    d = afn.air_density_from_pressure()

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

    # get cracks
    int_cracks = crack_data_dict['internal_average_cracks']

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
    window_vent_controls = [VentilationControl().duplicate() for _ in rooms]
    afn.generate(model.rooms, window_vent_controls)

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
    d = afn.air_density_from_pressure()
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
