# coding=utf-8
from honeybee_energy.simulation.runperiod import RunPeriod
from honeybee_energy.simulation.daylightsaving import DaylightSavingTime

from ladybug.dt import Date

import pytest


def test_daylight_saving_time_init():
    """Test the initialization of DaylightSavingTime and basic properties."""
    daylight_save = DaylightSavingTime()
    str(daylight_save)  # test the string representation

    assert daylight_save.start_date == Date(3, 12)
    assert daylight_save.end_date == Date(11, 5)


def test_daylight_saving_time_setability():
    """Test the setting of properties of DaylightSavingTime."""
    daylight_save = DaylightSavingTime()

    daylight_save.start_date = Date(3, 10)
    assert daylight_save.start_date == Date(3, 10)
    daylight_save.end_date = Date(11, 3)
    assert daylight_save.end_date == Date(11, 3)

    with pytest.raises(AssertionError):
        daylight_save.start_date = Date(11, 10)
    with pytest.raises(AssertionError):
        daylight_save.start_date = Date(3, 10, True)


def test_daylight_saving_time_equality():
    """Test the equality of DaylightSavingTime objects."""
    daylight_save = DaylightSavingTime()
    daylight_save_dup = daylight_save.duplicate()
    daylight_save_alt = DaylightSavingTime(Date(3, 10), Date(11, 3))

    assert daylight_save is daylight_save
    assert daylight_save is not daylight_save_dup
    assert daylight_save == daylight_save_dup
    daylight_save_dup.start_date = Date(3, 10)
    assert daylight_save != daylight_save_dup
    assert daylight_save != daylight_save_alt


def test_simulation_control_init_from_idf():
    """Test the initialization of SimulationControl from_idf."""
    daylight_save = DaylightSavingTime(Date(3, 10), Date(11, 3))

    idf_str = daylight_save.to_idf()
    rebuilt_daylight_save = DaylightSavingTime.from_idf(idf_str)
    assert daylight_save == rebuilt_daylight_save
    assert rebuilt_daylight_save.to_idf() == idf_str


def test_simulation_control_dict_methods():
    """Test the to/from dict methods."""
    daylight_save = DaylightSavingTime(Date(3, 10), Date(11, 3))

    ds_dict = daylight_save.to_dict()
    new_daylight_save = DaylightSavingTime.from_dict(ds_dict)
    assert new_daylight_save == daylight_save
    assert ds_dict == new_daylight_save.to_dict()


def test_run_period_init():
    """Test the initialization of RunPeriod and basic properties."""
    run_period = RunPeriod()
    str(run_period)  # test the string representation

    assert run_period.start_date == Date(1, 1)
    assert run_period.end_date == Date(12, 31)
    assert run_period.start_day_of_week == 'Sunday'
    assert run_period.holidays is None
    assert run_period.daylight_saving_time is None
    assert run_period.is_leap_year is False


def test_run_period_setability():
    """Test the setting of properties of RunPeriod."""
    run_period = RunPeriod()

    run_period.start_date = Date(1, 1)
    assert run_period.start_date == Date(1, 1)
    run_period.end_date = Date(6, 21)
    assert run_period.end_date == Date(6, 21)
    run_period.start_day_of_week = 'Monday'
    assert run_period.start_day_of_week == 'Monday'
    run_period.holidays = (Date(1, 1), Date(3, 17))
    assert run_period.holidays == (Date(1, 1), Date(3, 17))
    run_period.daylight_saving_time = DaylightSavingTime()
    assert run_period.daylight_saving_time == DaylightSavingTime()
    with pytest.raises(AssertionError):
        run_period.start_date = Date(11, 10)
    with pytest.raises(AssertionError):
        run_period.start_date = Date(3, 10, True)
    run_period.is_leap_year = True
    assert run_period.is_leap_year


def test_run_period_equality():
    """Test the equality of RunPeriod objects."""
    run_period = RunPeriod()
    run_period_dup = run_period.duplicate()
    run_period_alt = RunPeriod(end_date=Date(6, 21))

    assert run_period is run_period
    assert run_period is not run_period_dup
    assert run_period == run_period_dup
    run_period_dup.start_day_of_week = 'Monday'
    assert run_period != run_period_dup
    assert run_period != run_period_alt


def test_run_period_init_from_idf():
    """Test the initialization of RunPeriod from_idf."""
    run_period = RunPeriod()
    run_period.start_date = Date(1, 1)
    run_period.end_date = Date(6, 21)
    run_period.start_day_of_week = 'Monday'
    run_period.holidays = (Date(1, 1), Date(3, 17))
    run_period.daylight_saving_time = DaylightSavingTime()

    rp_str, holidays, dst = run_period.to_idf()
    rebuilt_run_period = RunPeriod.from_idf(rp_str, holidays, dst)
    assert run_period == rebuilt_run_period
    assert rebuilt_run_period.to_idf() == (rp_str, holidays, dst)


def test_run_period_dict_methods():
    """Test the to/from dict methods."""
    run_period = RunPeriod()
    run_period.start_date = Date(1, 1)
    run_period.end_date = Date(6, 21)
    run_period.start_day_of_week = 'Monday'
    run_period.holidays = (Date(1, 1), Date(3, 17))
    run_period.daylight_saving_time = DaylightSavingTime()

    rp_dict = run_period.to_dict()
    new_run_period = RunPeriod.from_dict(rp_dict)
    assert new_run_period == run_period
    assert rp_dict == new_run_period.to_dict()
