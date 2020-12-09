# coding=utf-8
from honeybee_energy.result.colorobj import ColorRoom, ColorFace
from honeybee_energy.result.loadbalance import LoadBalance

from honeybee.model import Model
from honeybee.room import Room
from ladybug_geometry.geometry3d.pointvector import Point3D
from ladybug_geometry.geometry3d.face import Face3D
from ladybug.sql import SQLiteResult
from ladybug.legend import LegendParameters
from ladybug.graphic import GraphicContainer
from ladybug.datacollection import HourlyContinuousCollection
from ladybug.datatype.energyintensity import EnergyIntensity
from ladybug.datatype.energy import Energy
from ladybug.datatype.temperature import Temperature
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.header import Header

import json
import pytest


def test_colorrooms_init():
    """Test the initialization of ColorRoom and basic properties."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)
    lighting_data = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    rooms = []
    for i in range(7):
        rooms.append(Room.from_box(
            'Residence_{}'.format(i + 1), 3, 6, 3.2, origin=Point3D(3 * i, 0, 0)))
    color_obj = ColorRoom(lighting_data, rooms)

    str(color_obj)
    assert len(color_obj.data_collections) == 7
    for coll in color_obj.data_collections:
        assert isinstance(coll, HourlyContinuousCollection)
        assert coll.header.unit == 'kWh'
    assert isinstance(color_obj.legend_parameters, LegendParameters)
    assert color_obj.simulation_step is None
    assert color_obj.normalize_by_floor
    assert color_obj.geo_unit == 'm'
    assert len(color_obj.matched_rooms) == 7
    assert len(color_obj.matched_values) == 7
    for val in color_obj.matched_values:
        assert isinstance(val, (float, int))
    assert len(color_obj.matched_floor_faces) == 7
    for face_array in color_obj.matched_floor_faces:
        assert len(face_array) == 1
        assert isinstance(face_array[0], Face3D)
    assert len(color_obj.matched_floor_areas) == 7
    for val in color_obj.matched_floor_areas:
        assert isinstance(val, (float, int))
    assert isinstance(color_obj.graphic_container, GraphicContainer)
    assert len(color_obj.graphic_container.value_colors) == 7
    assert color_obj.unit == 'kWh/m2'
    assert isinstance(color_obj.data_type, EnergyIntensity)
    assert color_obj.data_type_text == 'Zone Lights Electric Energy'
    assert color_obj.time_interval_text(0) == '06 Jan 00:00'
    assert color_obj.title_text == 'Total Zone Lights Electric Energy Intensity ' \
        '(kWh/m2)\n1/6 to 1/12 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Zone Lights Electric Energy Intensity ' \
        '(kWh/m2)\n06 Jan 00:00'

    with pytest.raises(AssertionError):
        color_obj.simulation_step = 8760


def test_colorrooms_not_normalized():
    """Test the initialization of ColorRoom without normalizing data by floor area."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)
    lighting_data = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    rooms = []
    for i in range(7):
        rooms.append(Room.from_box(
            'Residence_{}'.format(i + 1), 3, 6, 3.2, origin=Point3D(3 * i, 0, 0)))
    color_obj = ColorRoom(lighting_data, rooms, normalize_by_floor=False)

    assert len(color_obj.graphic_container.value_colors) == 7
    assert color_obj.unit == 'kWh'
    assert isinstance(color_obj.data_type, Energy)
    assert color_obj.data_type_text == 'Zone Lights Electric Energy'
    assert color_obj.time_interval_text(0) == '06 Jan 00:00'
    assert color_obj.title_text == 'Total Zone Lights Electric Energy ' \
        '(kWh)\n1/6 to 1/12 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Zone Lights Electric Energy (kWh)\n06 Jan 00:00'


def test_colorrooms_temperature():
    """Test the initialization of ColorRoom with temperature data."""
    sql_path = './tests/result/eplusout_hourly.sql'
    sql_obj = SQLiteResult(sql_path)
    lighting_data = sql_obj.data_collections_by_output_name(
        'Zone Mean Radiant Temperature')
    rooms = []
    for i in range(7):
        rooms.append(Room.from_box(
            'Residence_{}'.format(i + 1), 3, 6, 3.2, origin=Point3D(3 * i, 0, 0)))
    color_obj = ColorRoom(lighting_data, rooms)

    assert len(color_obj.graphic_container.value_colors) == 7
    assert color_obj.unit == 'C'
    assert isinstance(color_obj.data_type, Temperature)
    assert color_obj.data_type_text == 'Zone Mean Radiant Temperature'
    assert color_obj.time_interval_text(0) == '06 Jan 00:00'
    assert color_obj.title_text == 'Average Zone Mean Radiant Temperature ' \
        '(C)\n1/6 to 1/12 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Zone Mean Radiant Temperature (C)\n06 Jan 00:00'


def test_colorrooms_daily():
    """Test the initialization of ColorRoom with daily data."""
    sql_path = './tests/result/eplusout_daily.sql'
    sql_obj = SQLiteResult(sql_path)
    lighting_data = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    rooms = []
    for i in range(7):
        rooms.append(Room.from_box(
            'Residence_{}'.format(i + 1), 3, 6, 3.2, origin=Point3D(3 * i, 0, 0)))
    color_obj = ColorRoom(lighting_data, rooms)

    assert len(color_obj.graphic_container.value_colors) == 7
    assert color_obj.unit == 'kWh/m2'
    assert isinstance(color_obj.data_type, EnergyIntensity)
    assert color_obj.data_type_text == 'Zone Lights Electric Energy'
    assert color_obj.time_interval_text(0) == '01 Jan'
    assert color_obj.title_text == 'Total Zone Lights Electric Energy Intensity ' \
        '(kWh/m2)\n1/1 to 12/31 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Zone Lights Electric Energy Intensity (kWh/m2)\n01 Jan'


def test_colorrooms_monthly():
    """Test the initialization of ColorRoom with monthly data."""
    sql_path = './tests/result/eplusout_monthly.sql'
    sql_obj = SQLiteResult(sql_path)
    lighting_data = sql_obj.data_collections_by_output_name(
        'Zone Lights Electric Energy')
    rooms = []
    for i in range(7):
        rooms.append(Room.from_box(
            'Residence_{}'.format(i + 1), 3, 6, 3.2, origin=Point3D(3 * i, 0, 0)))
    color_obj = ColorRoom(lighting_data, rooms)

    assert len(color_obj.graphic_container.value_colors) == 7
    assert color_obj.unit == 'kWh/m2'
    assert isinstance(color_obj.data_type, EnergyIntensity)
    assert color_obj.data_type_text == 'Zone Lights Electric Energy'
    assert color_obj.time_interval_text(0) == 'Jan'
    assert color_obj.title_text == 'Total Zone Lights Electric Energy Intensity ' \
        '(kWh/m2)\n1/1 to 12/31 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Zone Lights Electric Energy Intensity (kWh/m2)\nJan'


def test_colorfaces_init():
    """Test the initialization of ColorFace and basic properties."""
    data = []
    identifiers = ['Bottom', 'Front', 'Right', 'Back', 'Left', 'Top']
    for identifier in identifiers:
        metadata = {'type': 'Surface Inside Face Temperature',
                    'Surface': 'RESIDENCE_{}'.format(identifier.upper())}
        head = Header(Temperature(), 'C', AnalysisPeriod(1, 1, 0, 1, 1, 23), metadata)
        data.append(HourlyContinuousCollection(head, [22] * 24))

    room = Room.from_box('Residence', 3, 6, 3.2)
    color_obj = ColorFace(data, room.faces)

    str(color_obj)
    assert len(color_obj.data_collections) == 6
    for coll in color_obj.data_collections:
        assert isinstance(coll, HourlyContinuousCollection)
        assert coll.header.unit == 'C'
    assert isinstance(color_obj.legend_parameters, LegendParameters)
    assert color_obj.simulation_step is None
    assert color_obj.normalize
    assert color_obj.geo_unit == 'm'
    assert len(color_obj.matched_flat_faces) == 6
    assert len(color_obj.matched_values) == 6
    for val in color_obj.matched_values:
        assert isinstance(val, (float, int))
    assert len(color_obj.matched_flat_geometry) == 6
    for face3d in color_obj.matched_flat_geometry:
        assert isinstance(face3d, Face3D)
    assert len(color_obj.matched_flat_areas) == 6
    for val in color_obj.matched_flat_areas:
        assert isinstance(val, (float, int))
    assert isinstance(color_obj.graphic_container, GraphicContainer)
    assert len(color_obj.graphic_container.value_colors) == 6
    assert color_obj.unit == 'C'
    assert isinstance(color_obj.data_type, Temperature)
    assert color_obj.data_type_text == 'Surface Inside Face Temperature'
    assert color_obj.title_text == 'Average Surface Inside Face Temperature ' \
        '(C)\n1/1 to 1/1 between 0 and 23 '

    color_obj.simulation_step = 0
    assert color_obj.title_text == 'Surface Inside Face Temperature ' \
        '(C)\n01 Jan 00:00'

    with pytest.raises(AssertionError):
        color_obj.simulation_step = 8760


def test_colorfaces_triangulated():
    """Test the initialization of ColorFace with a triangulated aperture."""
    model_json = './tests/result/triangulated/TriangleModel.json'
    with open(model_json, 'r') as fp:
        model_data = json.load(fp)
    model = Model.from_dict(model_data)

    sql_path = './tests/result/triangulated/eplusout.sql'
    sql_obj = SQLiteResult(sql_path)

    data_colls = sql_obj.data_collections_by_output_name(
        'Surface Inside Face Temperature')
    color_obj = ColorFace(data_colls, model.rooms[0].faces)
    assert len(color_obj.matched_values) == 8

    data_colls = sql_obj.data_collections_by_output_name(
        'Surface Window Heat Loss Energy')
    color_obj = ColorFace(data_colls, model.rooms[0].faces)
    assert len(color_obj.matched_values) == 1

    data_colls = sql_obj.data_collections_by_output_name(
        'Surface Average Face Conduction Heat Transfer Energy')
    color_obj = ColorFace(data_colls, model.rooms[0].faces)
    assert len(color_obj.matched_values) == 7


def test_load_balance():
    """Test the initialization of LoadBalance from an sql file."""
    model_json = './tests/result/triangulated/TriangleModel.json'
    with open(model_json, 'r') as fp:
        model_data = json.load(fp)
    model = Model.from_dict(model_data)
    sql_path = './tests/result/triangulated/eplusout.sql'

    load_bal_obj = LoadBalance.from_sql_file(model, sql_path)

    load_colls = load_bal_obj.load_balance_terms()
    load_colls_storage = load_bal_obj.load_balance_terms(include_storage=True)
    assert len(load_colls) >= 8
    assert len(load_colls_storage) == len(load_colls) + 1

    load_colls_norm_storage = load_bal_obj.load_balance_terms(True, True)
    assert len(load_colls_norm_storage) == len(load_colls) + 1
