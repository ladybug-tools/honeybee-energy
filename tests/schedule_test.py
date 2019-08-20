# coding=utf-8
from honeybee_energy.schedule import ScheduleDay

from ladybug.dt import Time

import pytest


def test_schedule_day_init():
    """Test the initialization of ScheduleDay and basic properties."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(9, 0), Time(17, 0), Time(23, 59)])
    str(simple_office)  # test the string representation

    assert simple_office.name == 'Simple Office Occupancy'
    assert len(simple_office.values) == 3
    assert len(simple_office.times) == 3
    for t in simple_office.times:
        assert isinstance(t, Time)
    assert not simple_office.interpolate


def test_schedule_day_init_from_values():
    """Test the initialization of ScheduleDay from_values_at_timestep."""
    test_vals = [0.5, 0.5, 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1, 1, 1,
                 0.5, 0.5, 0.5, 0.5, 1, 1, 1, 1, 0.5, 0.5, 0.5, 0.5]
    test_sched = ScheduleDay.from_values_at_timestep('Test Schedule', test_vals)

    assert test_sched.values == (0.5, 1.0, 0.5, 1.0, 0.5)
    assert test_sched.times == (Time(6, 0), Time(12, 0), Time(16, 0),
                                Time(20, 0), Time(23, 59))

    test_sched_2 = ScheduleDay.from_values_at_timestep('Test Schedule', test_vals,
                                                       remove_repeated=False)
    assert test_sched_2.values == tuple(test_vals)
    assert test_sched_2.values_at_timestep() == test_vals
    assert len(test_sched_2.times) == 24


def test_schedule_day_init_from_values_at_timestep():
    """Test the initialization of ScheduleDay from_values_at_timestep."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(9, 0), Time(17, 0), Time(23, 59)])
    half_hour_vals = simple_office.values_at_timestep(2)
    test_sched = ScheduleDay.from_values_at_timestep('Simple Office Occupancy',
                                                     half_hour_vals, 2)

    assert test_sched == simple_office


def test_schedule_day_init_from_idf():
    """Test the initialization of ScheduleDay from_idf."""
    sched_str = """Schedule:Day:Interval,\n
                Medium Office Bldg Occ Default Schedule, !- Name\n
                Schedule Type Limits 1,                 !- Schedule Type Limits Name\n
                No,                                     !- Interpolate to Timestep\n
                06:00,                                  !- Time 1 {hh:mm}\n
                0,                                      !- Value Until Time 1\n
                07:00,                                  !- Time 2 {hh:mm}\n
                0.1,                                    !- Value Until Time 2\n
                08:00,                                  !- Time 3 {hh:mm}\n
                0.2,                                    !- Value Until Time 3\n
                12:00,                                  !- Time 4 {hh:mm}\n
                0.95,                                   !- Value Until Time 4\n
                13:00,                                  !- Time 5 {hh:mm}\n
                0.5,                                    !- Value Until Time 5\n
                17:00,                                  !- Time 6 {hh:mm}\n
                0.95,                                   !- Value Until Time 6\n
                18:00,                                  !- Time 7 {hh:mm}\n
                0.7,                                    !- Value Until Time 7\n
                20:00,                                  !- Time 8 {hh:mm}\n
                0.4,                                    !- Value Until Time 8\n
                22:00,                                  !- Time 9 {hh:mm}\n
                0.1,                                    !- Value Until Time 9\n
                24:00,                                  !- Time 10 {hh:mm}\n
                0.05;                                   !- Value Until Time 10
                """
    test_sched = ScheduleDay.from_idf(sched_str)
    rebuilt_sched = ScheduleDay.from_idf(test_sched.to_idf())
    assert test_sched == rebuilt_sched


def test_schedule_day_values_at_timestep():
    """Test the ScheduleDay values_at_timestep methods without interpolation."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(9, 0), Time(17, 0), Time(23, 59)])
    hourly_vals = simple_office.values_at_timestep()
    half_hour_vals = simple_office.values_at_timestep(2)
    ep_hourly_vals = simple_office.values_at_ep_timestep()
    ep_half_hour_vals = simple_office.values_at_ep_timestep(2)

    assert len(hourly_vals) == 24
    assert hourly_vals[8] == 0
    assert hourly_vals[9] == 1
    assert hourly_vals[16] == 1
    assert hourly_vals[17] == 0

    assert len(half_hour_vals) == 48
    assert half_hour_vals[18] == 0
    assert half_hour_vals[19] == 1
    assert half_hour_vals[34] == 1
    assert half_hour_vals[35] == 0

    assert len(ep_hourly_vals) == 24
    assert ep_hourly_vals[8] == 0
    assert ep_hourly_vals[9] == 1
    assert ep_hourly_vals[16] == 1
    assert ep_hourly_vals[17] == 0

    assert len(half_hour_vals) == 48
    assert ep_half_hour_vals[17] == 0
    assert ep_half_hour_vals[18] == 1
    assert ep_half_hour_vals[33] == 1
    assert ep_half_hour_vals[34] == 0


def test_schedule_day_values_at_timestep_ep_result():
    """Test the ScheduleDay values_at_timestep methods against EP output."""
    simple_office = ScheduleDay(
        'Simple Office Occupancy', [1, 2, 1, 2, 1],
        [Time(6, 0), Time(12, 0), Time(16, 0), Time(20, 0), Time(23, 59)])
    hourly_vals = simple_office.values_at_timestep()
    half_hour_vals = simple_office.values_at_timestep(2)
    ep_hourly_vals = simple_office.values_at_ep_timestep()
    ep_half_hour_vals = simple_office.values_at_ep_timestep(2)

    hour_vals_from_ep = [1, 1, 1, 1, 1, 1, 2, 2, 2, 2, 2, 2,
                         1, 1, 1, 1, 2, 2, 2, 2, 1, 1, 1, 1]
    vals_from_ep = [1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1, 1,
                    2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2, 2,
                    1, 1, 1, 1, 1, 1, 1, 1,
                    2, 2, 2, 2, 2, 2, 2, 2,
                    1, 1, 1, 1, 1, 1, 1, 1]

    assert ep_hourly_vals == hour_vals_from_ep
    assert ep_half_hour_vals == vals_from_ep

    assert hourly_vals == hour_vals_from_ep
    vals_from_ep.insert(0, vals_from_ep.pop(-1))
    assert half_hour_vals == vals_from_ep


def test_schedule_day_values_at_timestep_interpolate():
    """Test the ScheduleDay values_at_timestep method."""
    simple_office = ScheduleDay(
        'Simple Office Occupancy', [1, 2, 1, 2, 1],
        [Time(6, 0), Time(12, 0), Time(16, 0), Time(20, 0), Time(23, 59)])
    simple_office.interpolate = True
    hourly_vals = simple_office.values_at_timestep()
    half_hour_vals = simple_office.values_at_timestep(2)
    ep_hourly_vals = simple_office.values_at_ep_timestep()
    ep_half_hour_vals = simple_office.values_at_ep_timestep(2)

    hourly_vals_from_ep = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.166667, 1.333333, 1.5,
                           1.666667, 1.833333, 2.0, 1.75, 1.5, 1.25, 1.0, 1.25, 1.5,
                           1.75, 2.0, 1.75, 1.5, 1.25, 1.0]
    vals_from_ep = [1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0, 1.0,
                    1.083333, 1.166667, 1.25, 1.333333, 1.416667, 1.5,
                    1.583333, 1.666667, 1.75, 1.833333, 1.916667, 2.0,
                    1.875, 1.75, 1.625, 1.5, 1.375, 1.25, 1.125, 1.0, 1.125, 1.25,
                    1.375, 1.5, 1.625, 1.75, 1.875, 2.0, 1.875, 1.75, 1.625, 1.5,
                    1.375, 1.25, 1.125, 1.0]

    for hb_val, ep_val in zip(ep_hourly_vals, hourly_vals_from_ep):
        assert hb_val == pytest.approx(ep_val, rel=1e-3)
    for hb_val, ep_val in zip(ep_half_hour_vals, vals_from_ep):
        assert hb_val == pytest.approx(ep_val, rel=1e-3)

    for hb_val, ep_val in zip(hourly_vals, hourly_vals_from_ep):
        assert hb_val == pytest.approx(ep_val, rel=1e-3)
    vals_from_ep.insert(0, vals_from_ep.pop(-1))
    for hb_val, ep_val in zip(half_hour_vals, vals_from_ep):
        assert hb_val == pytest.approx(ep_val, rel=1e-3)


def test_schedule_day_dict_methods():
    """Test the to/from dict methods."""
    simple_office = ScheduleDay('Simple Office Occupancy', [0, 1, 0],
                                [Time(9, 0), Time(17, 0), Time(23, 59)])
    sch_dict = simple_office.to_dict()
    new_simple_office = ScheduleDay.from_dict(sch_dict)
    assert new_simple_office == simple_office
    assert sch_dict == new_simple_office.to_dict()
