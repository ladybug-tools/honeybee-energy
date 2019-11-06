# coding=utf-8
"""Module for running IDF files through EnergyPlus.

NOTE: This module is only temporary and will eventually be replaced with
the use of queenbee and workerbee.
"""
from __future__ import division

import os

from ladybug.futil import write_to_file_by_name, copy_files_to_folder


def run_idf(idf_file_path, epw_file_path, energyplus_directory):
    """Run an IDF file through energyplus.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
        energyplus_directory: The directory in which EnergyPlus is installed on
            the machine. Specifically, this should be the folder containing
            energyplus.exe as well as the other supporting files.
            (eg. 'C:/openstudio-2.8.0/EnergyPlus/')

    Returns:
        sql -- Path to a .sqlite file containing all simulation results.
            Will be None if no file exists.
        eio -- Path to a .eio file containing properties of the model, including
            the size of HVAC objects. Will be None if no file exists.
        rdd -- Path to a .rdd file containing all possible outputs that can be
            requested from the simulation. Will be None if no file exists.
        html -- Path to a .html file containing all summary reports.
            Will be None if no file exists.
    """
    # check the input files
    assert os.path.isfile(idf_file_path), \
        'No IDF file found at {}.'.format(idf_file_path)
    assert os.path.isfile(epw_file_path), \
        'No EPW file found at {}.'.format(epw_file_path)
    assert os.path.isdir(energyplus_directory), \
        'No EnergyPlus installation was found at {}.'.format(energyplus_directory)

    # copy all files needed for simulation to the folder
    directory, idf_file_name = os.path.split(idf_file_path)
    idd_path = os.path.join(energyplus_directory, 'Energy+.idd')
    copy_files_to_folder([idd_path, epw_file_path], directory, True)

    # rename the weather file to in.epw
    folder, epw_file_name = os.path.split(epw_file_path)
    old_file_name = os.path.join(directory, epw_file_name)
    new_file_name = os.path.join(directory, 'in.epw')
    try:
        os.remove(new_file_name)
    except Exception:
        pass  # file does not yet exist
    os.rename(old_file_name, new_file_name)

    # write a batch file
    expand_path = os.path.join(energyplus_directory, 'ExpandObjects')
    run_path = os.path.join(energyplus_directory, 'EnergyPlus')
    working_drive = directory[:2]
    batch = '{}\ncd {}\n{}\nif exist expanded.idf MOVE expanded.idf in.idf\n{}'.format(
        working_drive, directory, expand_path, run_path)
    write_to_file_by_name(directory, 'in.bat', batch, True)

    # run the batch file
    os.system(os.path.join(directory, 'in.bat'))

    # output the simulation files
    sql_file = os.path.join(directory, 'eplusout.sql')
    eio_file = os.path.join(directory, 'eplusout.eio')
    rdd_file = os.path.join(directory, 'eplusout.rdd')
    html_file = os.path.join(directory, 'eplustbl.htm')

    sql = sql_file if os.path.isfile(sql_file) else None
    eio = eio_file if os.path.isfile(eio_file) else None
    rdd = rdd_file if os.path.isfile(rdd_file) else None
    html = sql_file if os.path.isfile(html_file) else None

    return sql, eio, rdd, html
