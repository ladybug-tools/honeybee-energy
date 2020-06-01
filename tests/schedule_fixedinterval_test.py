# coding=utf-8
from __future__ import division

from honeybee_energy.schedule.fixedinterval import ScheduleFixedInterval
from honeybee_energy.schedule.typelimit import ScheduleTypeLimit
from honeybee_energy.schedule.ruleset import ScheduleRuleset
import honeybee_energy.lib.scheduletypelimits as schedule_types

from ladybug.dt import Date, DateTime
from ladybug.datatype import fraction
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.futil import csv_to_matrix

import random
import os
import pytest


def test_schedule_fixedinterval_init():
    """Test the ScheduleFixedInterval initialization and basic properties."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)
    str(trans_sched)  # test the string representation

    assert trans_sched.identifier == 'Custom Transmittance'
    assert len(trans_sched.values) == 8760
    assert trans_sched[0] == 0
    assert trans_sched[1] == 1 / 8760
    assert isinstance(trans_sched.schedule_type_limit, ScheduleTypeLimit)
    assert trans_sched.schedule_type_limit == schedule_types.fractional
    assert trans_sched.timestep == 1
    assert not trans_sched.interpolate
    assert trans_sched.start_date == Date(1, 1)
    assert trans_sched.end_date_time == DateTime(12, 31, 23)
    assert not trans_sched.is_leap_year
    assert trans_sched.placeholder_value == 0

    sch_data = trans_sched.data_collection
    assert len(sch_data) == 8760
    assert isinstance(sch_data.header.data_type, fraction.Fraction)
    assert sch_data.header.unit == 'fraction'
    assert sch_data.header.analysis_period == AnalysisPeriod()


def test_schedule_fixedinterval_single_day():
    """Test the ScheduleFixedInterval initialization for a single day."""
    increase_sched = ScheduleFixedInterval(
        'Solstice Increasing', [round(x / 23, 4) for x in range(24)],
        schedule_types.fractional, start_date=Date(6, 21))

    assert increase_sched.identifier == 'Solstice Increasing'
    assert len(increase_sched.values) == 24
    assert increase_sched[0] == 0
    assert increase_sched[-1] == 1
    assert isinstance(increase_sched.schedule_type_limit, ScheduleTypeLimit)
    assert increase_sched.schedule_type_limit == schedule_types.fractional
    assert increase_sched.timestep == 1
    assert not increase_sched.interpolate
    assert increase_sched.start_date == Date(6, 21)


def test_schedule_fixedinterval_single_day_fine_timestep():
    """Test the ScheduleFixedInterval initialization for a single day at a fine timestep."""
    increase_sched = ScheduleFixedInterval(
        'Solstice Increasing', [round(x / 143, 4) for x in range(144)],
        schedule_types.fractional, start_date=Date(6, 21), timestep=6,)

    assert increase_sched.identifier == 'Solstice Increasing'
    assert len(increase_sched.values) == 144
    assert increase_sched[0] == 0
    assert increase_sched[-1] == 1
    assert isinstance(increase_sched.schedule_type_limit, ScheduleTypeLimit)
    assert increase_sched.schedule_type_limit == schedule_types.fractional
    assert increase_sched.timestep == 6
    assert not increase_sched.interpolate
    assert increase_sched.start_date == Date(6, 21)


def test_schedule_fixedinterval_equality():
    """Test the ScheduleFixedInterval to/from dict methods."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)
    trans_sched_dup = trans_sched.duplicate()
    occ_sched = ScheduleFixedInterval(
        'Random Occupancy', [round(random.random(), 4) for i in range(8760)],
        schedule_types.fractional)

    assert trans_sched is trans_sched
    assert trans_sched is not trans_sched_dup
    assert trans_sched == trans_sched_dup
    trans_sched_dup.identifier = 'Transmittance'
    assert trans_sched != trans_sched_dup
    assert trans_sched != occ_sched


def test_schedule_fixedinterval_lockability():
    """Test the lockability of ScheduleFixedInterval objects."""
    schedule = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)

    schedule.interpolate = True
    schedule.lock()
    with pytest.raises(AttributeError):
        schedule.interpolate = False
    with pytest.raises(AttributeError):
        schedule.values = [1] * 8760
    schedule.unlock()
    schedule.interpolate = False
    schedule.values = [1] * 8760


def test_schedule_fixedinterval_values_at_timestep():
    """Test the ScheduleFixedInterval values_at_timestep method."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)
    values = trans_sched.values_at_timestep()
    assert len(values) == 8760
    assert values == list(trans_sched.values)

    trans_sched_2 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 24 for x in range(24)],
        schedule_types.fractional)
    values = trans_sched_2.values_at_timestep()
    assert len(values) == 8760
    assert values[:24] == [x / 24 for x in range(24)]
    assert values[24] == 0

    trans_sched_3 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 24 for x in range(24)],
        schedule_types.fractional, start_date=Date(1, 2))
    values = trans_sched_3.values_at_timestep()
    assert len(values) == 8760
    assert values[24:48] == [x / 24 for x in range(24)]
    assert values[0] == 0
    assert values[48] == 0

    trans_sched_4 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 168 for x in range(168)],
        schedule_types.fractional)
    values = trans_sched_4.values_at_timestep(end_date=Date(1, 2))
    assert len(values) == 48
    assert values[0] == 0
    assert values[47] == 47 / 168

    values = trans_sched_4.values_at_timestep(start_date=Date(1, 2), end_date=Date(1, 3))
    assert len(values) == 48
    assert values[0] == 24 / 168
    assert values[47] == 71 / 168


def test_schedule_fixedinterval_values_at_finer_timestep():
    """Test the ScheduleFixedInterval values_at_timestep method with a finer step."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)
    values = trans_sched.values_at_timestep(timestep=2)
    assert len(values) == 8760 * 2
    assert values[0] == values[1] == trans_sched.values[0]

    trans_sched_2 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 24 for x in range(24)],
        schedule_types.fractional, interpolate=True)
    values = trans_sched_2.values_at_timestep(timestep=4, end_date=Date(1, 1))
    assert len(values) == 24 * 4
    assert values[0] == trans_sched.values[0]
    assert values[0] != values[1]


def test_schedule_fixedinterval_values_at_coarser_timestep():
    """Test the ScheduleFixedInterval values_at_timestep method with a coarser step."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 17520 for x in range(17520)],
        schedule_types.fractional, timestep=2)
    values = trans_sched.values_at_timestep(timestep=1)
    assert len(values) == 8760
    assert values[0] == trans_sched.values[0]

    trans_sched_2 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 96 for x in range(96)],
        schedule_types.fractional, interpolate=True)
    values = trans_sched_2.values_at_timestep(timestep=1, end_date=Date(1, 1))
    assert len(values) == 24
    assert values[0] == trans_sched.values[0]


def test_schedule_fixedinterval_values_at_timestep_reversed():
    """Test the ScheduleFixedInterval values_at_timestep method with a reversed list."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional, start_date=Date(1, 2))
    values = trans_sched.values_at_timestep()
    assert len(values) == 8760
    assert values[24] == 0
    assert values[0] == trans_sched.values[-24]

    trans_sched_4 = ScheduleFixedInterval(
        'Custom Transmittance', [x / 168 for x in range(168)],
        schedule_types.fractional, start_date=Date(12, 31))
    values = trans_sched_4.values_at_timestep(end_date=Date(1, 2))
    assert len(values) == 48
    assert values[0] == 24 / 168
    assert values[23] == 47 / 168


def test_schedule_fixedinterval_data_collection():
    """Test the ScheduleFixedInterval data_collection_at_timestep method."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)

    sch_data = trans_sched.data_collection_at_timestep()
    assert len(sch_data) == 8760
    assert sch_data.values == trans_sched.values
    assert isinstance(sch_data.header.data_type, fraction.Fraction)
    assert sch_data.header.unit == 'fraction'
    assert sch_data.header.analysis_period == AnalysisPeriod()

    sch_data = trans_sched.data_collection_at_timestep(timestep=2)
    assert len(sch_data) == 8760 * 2


def test_schedule_fixedinterval_dict_methods():
    """Test the ScheduleFixedInterval to/from dict methods."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)

    sch_dict = trans_sched.to_dict()
    new_schedule = ScheduleFixedInterval.from_dict(sch_dict)
    assert new_schedule == trans_sched
    assert sch_dict == new_schedule.to_dict()


def test_schedule_fixedinterval_from_idf():
    """Test the ScheduleFixedInterval from_idf method."""
    idf_str = \
        """Schedule:File,
            Electrochromic Control,   !- schedule name
            On-Off,                   !- schedule type limits
            ./tests/csv/Electrochromic_Control.csv, !- file name
            1,                        !- column number
            0,                        !- rows to skip
            8760,                     !- number of hours of data
            Comma,                    !- column separator
            No,                       !- interpolate to timestep
            60;                       !- minutes per item
        """
    ec_schedule = ScheduleFixedInterval.from_idf(idf_str)

    assert ec_schedule.identifier == 'Electrochromic Control'
    assert len(ec_schedule.values) == 8760
    assert ec_schedule[0] == 0
    assert ec_schedule.schedule_type_limit is None
    assert ec_schedule.timestep == 1
    assert not ec_schedule.interpolate
    assert ec_schedule.start_date == Date(1, 1)
    assert ec_schedule.end_date_time == DateTime(12, 31, 23)
    assert not ec_schedule.is_leap_year
    assert ec_schedule.placeholder_value == 0


def test_schedule_fixedinterval_from_idf_file():
    """Test the initialization of ScheduleFixedInterval from file."""
    ec_sched_idf = './tests/idf/ElectrochromicControlSchedules.idf'
    ec_scheds = ScheduleFixedInterval.extract_all_from_idf_file(ec_sched_idf)

    assert len(ec_scheds) == 4

    assert ec_scheds[0].identifier == 'Electrochromic Control 0'
    assert ec_scheds[1].identifier == 'Electrochromic Control 90'
    assert ec_scheds[2].identifier == 'Electrochromic Control 180'
    assert ec_scheds[3].identifier == 'Electrochromic Control 270'
    assert len(ec_scheds[0].values) == 8760
    assert len(ec_scheds[1].values) == 8760
    assert len(ec_scheds[2].values) == 8760
    assert len(ec_scheds[3].values) == 8760

    assert ec_scheds[0].schedule_type_limit is ec_scheds[1].schedule_type_limit == \
        schedule_types.on_off


def test_schedule_fixedinterval_to_idf():
    """Test the methods that go to and from an IDF."""
    random_occ = [0.5] * 8760
    occ_sched = ScheduleFixedInterval('Random Occupancy', random_occ,
                                      schedule_types.fractional)

    schedule_file = occ_sched.to_idf('./tests/csv/', include_datetimes=False)
    sch_type = schedule_types.fractional.to_idf()

    rebuilt_schedule = ScheduleFixedInterval.from_idf(schedule_file, sch_type)
    assert rebuilt_schedule == occ_sched
    assert rebuilt_schedule.to_idf('./tests/csv/') == schedule_file

    schedule_file = occ_sched.to_idf('./tests/csv/', include_datetimes=True)
    rebuilt_schedule = ScheduleFixedInterval.from_idf(schedule_file, sch_type)
    assert rebuilt_schedule == occ_sched

    os.remove('./tests/csv/Random_Occupancy.csv')


def test_schedule_fixedinterval_to_idf_compact():
    """Test the ScheduleFixedInterval to_idf_compact method."""
    trans_sched = ScheduleFixedInterval(
        'Custom Transmittance', [x / 8760 for x in range(8760)],
        schedule_types.fractional)

    compact_idf = trans_sched.to_idf_compact()
    assert len(compact_idf.split(',')) > 8760 * 2


def test_shcedule_fixedinterval_to_idf_collective_csv():
    """Test the to_idf_collective_csv method."""
    ec_sched_idf = './tests/idf/ElectrochromicControlSchedules.idf'
    ec_scheds = ScheduleFixedInterval.extract_all_from_idf_file(ec_sched_idf)

    collective_string = ScheduleFixedInterval.to_idf_collective_csv(
        ec_scheds, './tests/csv/', 'All Electrochromic')

    assert len(collective_string) == 4
    assert os.path.isfile('./tests/csv/All_Electrochromic.csv')
    all_data = csv_to_matrix('./tests/csv/All_Electrochromic.csv')
    assert len(all_data) == 8761
    assert len(all_data[0]) >= 4

    os.remove('./tests/csv/All_Electrochromic.csv')


def test_schedule_fixedinterval_average_schedules():
    """Test the average_schedules method."""
    trans_sched_1 = ScheduleFixedInterval('Transmittance 1', [1 for i in range(8760)],
                                          schedule_types.fractional)
    trans_sched_2 = ScheduleFixedInterval('Transmittance 2', [0 for i in range(8760)],
                                          schedule_types.fractional)

    avg_trans = ScheduleFixedInterval.average_schedules(
        'Transmittance Avg', [trans_sched_1, trans_sched_2])
    assert avg_trans.identifier == 'Transmittance Avg'
    assert avg_trans.schedule_type_limit == schedule_types.fractional
    assert len(avg_trans.values) == 8760
    assert list(avg_trans.values) == [0.5] * 8760

    avg_trans = ScheduleFixedInterval.average_schedules(
        'Transmittance Avg', [trans_sched_1, trans_sched_2], [0.75, 0.25])
    assert len(avg_trans.values) == 8760
    assert list(avg_trans.values) == [0.75] * 8760

    with pytest.raises(AssertionError):
        avg_trans = ScheduleFixedInterval.average_schedules(
            'Transmittance Avg', [trans_sched_1, trans_sched_2], [0.5, 0.25])


def test_schedule_fixedinterval_average_schedules_ruleset():
    """Test the average_schedules method with a ScheduleRuleset."""
    trans_sched_1 = ScheduleFixedInterval('Transmittance 1', [1 for i in range(8760)],
                                          schedule_types.fractional)
    trans_sched_2 = ScheduleRuleset.from_constant_value('Transmittance 2', 0)

    avg_trans = ScheduleFixedInterval.average_schedules(
        'Transmittance Avg', [trans_sched_1, trans_sched_2])
    assert avg_trans.identifier == 'Transmittance Avg'
    assert avg_trans.schedule_type_limit == schedule_types.fractional
    assert len(avg_trans.values) == 8760
    assert list(avg_trans.values) == [0.5] * 8760

    avg_trans = ScheduleFixedInterval.average_schedules(
        'Transmittance Avg', [trans_sched_1, trans_sched_2], [0.75, 0.25])
    assert len(avg_trans.values) == 8760
    assert list(avg_trans.values) == [0.75] * 8760
