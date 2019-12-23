# coding=utf-8
"""Module for running IDF files through EnergyPlus.

NOTE: This module is only temporary and will eventually be replaced with
the use of queenbee and workerbee.
"""
from __future__ import division

import os
import json

from .config import folders

from ladybug.futil import write_to_file_by_name, copy_files_to_folder, copy_file_tree


def run_idf_windows(idf_file_path, epw_file_path):
    """Run an IDF file through energyplus on a Windows-based operating system.

    A batch file will be used to run the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.

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
    # check and prepare the input files
    directory = prepare_idf_for_simulation(idf_file_path, epw_file_path)

    # write a batch file
    expand_path = os.path.join(folders.energyplus_path, 'ExpandObjects')
    run_path = os.path.join(folders.energyplus_path, 'EnergyPlus')
    working_drive = directory[:2]
    batch = '{}\ncd {}\n{}\nif exist expanded.idf MOVE expanded.idf in.idf\n{}'.format(
        working_drive, directory, expand_path, run_path)
    write_to_file_by_name(directory, 'in.bat', batch, True)

    # run the batch file
    os.system(os.path.join(directory, 'in.bat'))

    # output the simulation files
    return _output_files_from_directory(directory)



def run_osw_windows(osw_json, measures_only=True):
    """Run a .osw file using the OpenStudio CLI.
    
    Args:
        osw_json: File path to a OSW file to be run using OpenStudio CLI.
        measures_only: Boolean to note whether only the measures should be applied
            in the runnning of the OSW (True) or the resulting model shoudl be run
            through EnergyPlus after the measures are aplied to it (False).
            Default: True.
    
    Returns:
        The following files output from the CLI run.
        osm -- Path to a .osm file containing all simulation results.
            Will be None if no file exists.
        idf -- Path to a .idf file containing properties of the model, including
            the size of HVAC objects. Will be None if no file exists.
    """
    # check the openstudio directory
    if not folders.openstudio_path:
        raise OSError('No OpenStudio installation was found on this machine.\n'
                      'Install OpenStudio to run energy simulations.')

    # check the input files
    assert os.path.isfile(osw_json), 'No OSW file found at {}.'.format(osw_json)
    directory = os.path.split(osw_json)[0]

    # Write the batch file to apply the measures.
    working_drive = directory[:2]
    measure_str = '-m ' if measures_only else ''
    batch = '{}\ncd {}\n"openstudio.exe" run {}-w {}'.format(
        working_drive, folders.openstudio_path, measure_str, osw_json)
    write_to_file_by_name(directory, 'run_workflow.bat', batch, True)
    
    # run the batch file
    os.system(os.path.join(directory, 'run_workflow.bat'))
    
    # return the paths to the OSM and IDF
    osm_file = os.path.join(directory, 'run', 'in.osm')
    idf_file = os.path.join(directory, 'run', 'in.idf')

    # check that the OSM and IDF files exist
    osm = osm_file if os.path.isfile(osm_file) else None
    idf = idf_file if os.path.isfile(idf_file) else None

    return osm, idf


def to_openstudio_osw(osw_directory, model_json_path, sim_par_json_path, epw_file=None):
    """Create a .osw to translate honeybee JSONs to an .osm file.
    
    Args:
        osw_directory: The directory into which the .osw should be written and the
            .osm will eventually be written into.
        model_json_path: File path to the Model JSON.
        sim_par_json_path: File path to the SimulationParameter JSON.
        epw_file: Optional file path to an EPW that should be associated with the
            output energy model.
    
    Returns:
        The file path to the .osw written out by this method.
    """
    # check the energy_model_measure_path
    if not folders.energy_model_measure_path:
        raise OSError('The energy_model_measure that translates honeybee models'
                      ' to OpenStudio was not found.')

    # copy the measures into the directory
    measure_directory = os.path.join(folders.energy_model_measure_path, 'measures')
    sim_measures_dir = os.path.join(osw_directory, 'measures')
    copy_file_tree(measure_directory, sim_measures_dir)

    # copy the ladybug ruby library to the directory
    ladybug_ruby_directory = os.path.join(folders.energy_model_measure_path, 'ladybug')
    sim_ladybug_ruby = os.path.join(osw_directory, 'ladybug')
    copy_file_tree(ladybug_ruby_directory, sim_ladybug_ruby)

    # copy the files to the directory
    files_directory = os.path.join(folders.energy_model_measure_path, 'files')
    sim_files = os.path.join(osw_directory, 'files')
    copy_file_tree(files_directory, sim_files)

    # create a dictionary representation of the .osw
    model_measure_dict = {
        'arguments' : {
            'ladybug_json' : model_json_path
            },
         'measure_dir_name': 'ladybug_energy_model_measure'
         }

    sim_par_dict = {
        'arguments' : {
            'simulation_parameter_json' : sim_par_json_path
            },
         'measure_dir_name': 'ladybug_simulation_parameter_measure'
         }

    osw_dict = {'steps': [model_measure_dict, sim_par_dict]}

    # assign the epw_file to the osw if it is input
    if epw_file is not None:
        osw_dict['weather_file'] = epw_file

    # write the dictionary to a workflow.json
    osw_json = os.path.join(osw_directory, 'workflow.osw')
    with open(osw_json, 'w') as fp:
        json.dump(osw_dict, fp, indent=4)

    return osw_json


def prepare_idf_for_simulation(idf_file_path, epw_file_path):
    """Prepare an IDF file to be run through EnergyPlus.

    This includes copying the Energy+.idd to the directory of the IDF, copying the EPW
    file to the directory, renaming the EPW to in.epw and renaming the IDF to in.idf.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
    
    Returns:
        directory: The folder in which the IDF exists and out of which the EnergyPlus
            simulation will be run.
    """
    # check the energyplus directory
    if not folders.energyplus_path:
        raise OSError('No EnergyPlus installation was found on this machine.\n'
                        'Install EnergyPlus to run energy simulations.')

    # check the input files
    assert os.path.isfile(idf_file_path), \
        'No IDF file found at {}.'.format(idf_file_path)
    assert os.path.isfile(epw_file_path), \
        'No EPW file found at {}.'.format(epw_file_path)

    # copy all files needed for simulation to the folder
    directory = os.path.split(idf_file_path)[0]
    idd_path = os.path.join(folders.energyplus_path, 'Energy+.idd')
    copy_files_to_folder([idd_path, epw_file_path], directory, True)

    # rename the weather file to in.epw (what energyplus is expecting)
    epw_file_name = os.path.split(epw_file_path)[-1]
    if epw_file_name != 'in.epw':
        old_file_name = os.path.join(directory, epw_file_name)
        new_file_name = os.path.join(directory, 'in.epw')
        # ensure that there isn't an in.epw file there already
        if os.path.isfile(new_file_name):
            os.remove(new_file_name)
        os.rename(old_file_name, new_file_name)

    # rename the idf file to in.idf if it isn't named that already
    idf_file_name = os.path.split(idf_file_path)[-1]
    if idf_file_name != 'in.idf':
        old_file_name = os.path.join(directory, epw_file_name)
        new_file_name = os.path.join(directory, 'in.idf')
        # ensure that there isn't an in.idf file there already
        if os.path.isfile(new_file_name):
            os.remove(new_file_name)
        os.rename(old_file_name, new_file_name)
    
    return directory


def _output_files_from_directory(directory):
    """Get the paths to the EnergyPlus simulation output files given the idf directory.

    Args:
        directory: The path to where the IDF was run.
    
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
