# coding=utf-8
"""Module for running IDF files through EnergyPlus.

NOTE: This module is only temporary and will eventually be replaced with
the use of queenbee and workerbee.
"""
from __future__ import division

import os
import json
import subprocess

from .config import folders

from honeybee.model import Model

from ladybug.futil import write_to_file, copy_files_to_folder, copy_file_tree, preparedir


def measure_compatible_model_json(model_json_path, destination_directory=None):
    """Convert a Model JSON to a version that's compatible with the energy_model_measure.

    This includes the re-serialization of the Model to Python, which will
    automatically ensure that all Apertures and Doors point in the same direction
    as their parent Face. If the Model tolerance is non-zero and Rooms are closed
    solids, this will also ensure that all Room Faces point outwards from their
    parent's volume. Lastly, if the Model units are not Meters, the model will
    be scaled to be in Meters.

    Args:
        model_json_path: File path to the Model JSON.
        destination_directory: The directory into which the Model JSON that's
            compatible with the energy_model_measure should be written. If None,
            this will be the same location as the input model_json_path. Default: None.

    Returns:
        The full file path to the new Model JSON written out by this method.
    """
    # check that the file is thre
    assert os.path.isfile(model_json_path), \
        'No JSON file found at {}.'.format(model_json_path)

    # get the directory and the file path for the new Model JSON
    directory, init_file_name = os.path.split(model_json_path)
    dest_dir = directory if destination_directory is None else destination_directory
    base_file_name = init_file_name.replace('.json', '')
    file_name = '{}_osm.json'.format(base_file_name)
    dest_file_path = os.path.join(dest_dir, file_name)

    # serialze the Model to Python
    with open(model_json_path) as json_file:
        data = json.load(json_file)
    parsed_model = Model.from_dict(data)

    # convert the Model to Meters and get the dictionary
    parsed_model.convert_to_units('Meters')
    model_dict = parsed_model.to_dict(triangulate_sub_faces=True)

    # write the dictionary into a file
    preparedir(dest_dir, remove_content=False)  # create the directory if it's not there
    with open(dest_file_path, 'w') as fp:
        json.dump(model_dict, fp)
    
    return os.path.abspath(dest_file_path)


def to_openstudio_osw(osw_directory, model_json_path, sim_par_json_path=None,
                      epw_file=None):
    """Create a .osw to translate honeybee JSONs to an .osm file.
    
    Args:
        osw_directory: The directory into which the .osw should be written and the
            .osm will eventually be written into.
        model_json_path: File path to the Model JSON.
        sim_par_json_path: Optional file path to the SimulationParameter JSON.
            If None, the resulting OSM will not have everything it needs to be
            simulate-able.
        epw_file: Optional file path to an EPW that should be associated with the
            output energy model.
    
    Returns:
        The file path to the .osw written out by this method.
    """
    # check the energy_model_measure_path
    if not folders.energy_model_measure_path:
        raise OSError('The energy_model_measure that translates honeybee models'
                      ' to OpenStudio was not found on this machine.')

    # create a dictionary representation of the .osw with steps to run
    # the model measure and the simulation parameter measure
    model_measure_dict = {
        'arguments' : {
            'model_json' : model_json_path
            },
         'measure_dir_name': 'from_honeybee_model'
        }
    osw_dict = {'steps': [model_measure_dict]}
    
    # add a simulation parameter step if it is specified
    if sim_par_json_path is not None:
        sim_par_dict = {
            'arguments' : {
                'simulation_parameter_json' : sim_par_json_path
                },
            'measure_dir_name': 'from_honeybee_simulation_parameter'
            }
        osw_dict['steps'].append(sim_par_dict)
        

    # assign the measure_paths to the osw_dict
    measure_directory = os.path.join(folders.energy_model_measure_path, 'measures')
    osw_dict['measure_paths'] = [measure_directory]

    # assign the epw_file to the osw if it is input
    if epw_file is not None:
        osw_dict['weather_file'] = epw_file

    # write the dictionary to a workflow.json
    osw_json = os.path.join(osw_directory, 'workflow.osw')
    with open(osw_json, 'w') as fp:
        json.dump(osw_dict, fp, indent=4)

    return os.path.abspath(osw_json)


def run_osw(osw_json, measures_only=True):
    """Run a .osw file using the OpenStudio CLI on any operating system.
    
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
    # run the simulation
    if os.name == 'nt':  # we are on Windows
        directory = _run_osw_windows(osw_json, measures_only)
    else:  # we are on Mac, Linux, or some other unix-based system
        directory = _run_osw_unix(osw_json, measures_only)

    # output the simulation files
    return _output_openstudio_files(directory)


def prepare_idf_for_simulation(idf_file_path, epw_file_path):
    """Prepare an IDF file to be run through EnergyPlus.

    This includes copying the Energy+.idd to the directory of the IDF, copying the EPW
    file to the directory, renaming the EPW to in.epw and renaming the IDF to in.idf
    (if it is not already names so).

    A check is also performed to be sure that a valid EnergyPlus installation
    was found.

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


def run_idf(idf_file_path, epw_file_path, expand_objects=True):
    """Run an IDF file through energyplus on any operating system.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objets in
            the IDF but it is unnecessary extra time when they are not present.
            Default: True.

    Returns:
        A series of file paths to the simulation output files.
        sql -- Path to a .sqlite file containing all simulation results.
            Will be None if no file exists.
        eio -- Path to a .eio file containing properties of the model, including
            the size of HVAC objects. Will be None if no file exists.
        rdd -- Path to a .rdd file containing all possible outputs that can be
            requested from the simulation. Will be None if no file exists.
        html -- Path to a .html file containing all summary reports.
            Will be None if no file exists.
        err -- Path to a .err file containing all errors and warnings from the
            simulation. Will be None if no file exists.
    """
    # run the simulation
    if os.name == 'nt':  # we are on Windows
        directory = _run_idf_windows(idf_file_path, epw_file_path, expand_objects)
    else:  # we are on Mac, Linux, or some other unix-based system
        directory = _run_idf_unix(idf_file_path, epw_file_path, expand_objects)

    # output the simulation files
    return _output_energyplus_files(directory)


def _check_osw(osw_json):
    """Prepare an OSW file to be run through OpenStudio CLI.

    This includes checking for a valid OpenStudio installation and ensuring the
    OSW file exists.

    Args:
        osw_json: The full path to an OSW file.
        epw_file_path: The full path to an EPW file.
    
    Returns:
        The folder in which the OSW exists and out of which the OpenStudio CLI
        will operate.
    """
    # check the openstudio directory
    if not folders.openstudio_path:
        raise OSError('No OpenStudio installation was found on this machine.\n'
                      'Install OpenStudio to run energy simulations.')

    # check the input files
    assert os.path.isfile(osw_json), 'No OSW file found at {}.'.format(osw_json)
    return os.path.split(osw_json)[0]


def _run_osw_windows(osw_json, measures_only=True):
    """Run a .osw file using the OpenStudio CLI on a Windows-based operating system.

    A batch file will be used to run the simulation.
    
    Args:
        osw_json: File path to a OSW file to be run using OpenStudio CLI.
        measures_only: Boolean to note whether only the measures should be applied
            in the runnning of the OSW (True) or the resulting model shoudl be run
            through EnergyPlus after the measures are aplied to it (False).
            Default: True.
    
    Returns:
        Path to the folder out of which the OSW was run.
    """
    # check the input file
    directory = _check_osw(osw_json)

    # Write the batch file to call OpenStudio CLI
    working_drive = directory[:2]
    measure_str = '-m ' if measures_only else ''
    batch = '{}\ncd {}\n"openstudio.exe" -I {} run {}-w {}'.format(
        working_drive, folders.openstudio_path, folders.energy_model_measure_path,
        measure_str, osw_json)
    batch_file = os.path.join(directory, 'run_workflow.bat')
    write_to_file(batch_file, batch, True)
    
    # run the batch file
    os.system(batch_file)

    return directory


def _run_osw_unix(osw_json, measures_only=True):
    """Run a .osw file using the OpenStudio CLI on a Unix-based operating system.

    This includes both Mac OS and Linux since a shell will be used to run
    the simulation.
    
    Args:
        osw_json: File path to a OSW file to be run using OpenStudio CLI.
        measures_only: Boolean to note whether only the measures should be applied
            in the runnning of the OSW (True) or the resulting model shoudl be run
            through EnergyPlus after the measures are aplied to it (False).
            Default: True.
    
    Returns:
        Path to the folder out of which the OSW was run.
    """
    # check the input file
    directory = _check_osw(osw_json)

    # Write the shell script to call OpenStudio CLI
    measure_str = '-m ' if measures_only else ''
    shell = '#!/usr/bin/env bash\n\ncd {}\n"openstudio" -I {} run {}-w {}'.format(
        folders.openstudio_path, folders.energy_model_measure_path,
        measure_str, osw_json)
    shell_file = os.path.join(directory, 'run_workflow.sh')
    write_to_file(shell_file, shell, True)

    # make the shell script executable using subprocess.check_call
    # this is more reliable than native Python chmod on Mac
    subprocess.check_call(['chmod','u+x', shell_file])

    # run the shell script
    subprocess.call(shell_file)

    return directory


def _output_openstudio_files(directory):
    """Get the paths to the OpenStudio simulation output files given the osw directory.

    Args:
        directory: The path to where the OSW was run.
    
    Returns:
        osm -- Path to a .osm file containing all simulation results.
            Will be None if no file exists.
        idf -- Path to a .idf file containing properties of the model, including
            the size of HVAC objects. Will be None if no file exists.
    """
    # generate paths to the OSM and IDF files
    osm_file = os.path.join(directory, 'run', 'in.osm')
    idf_file = os.path.join(directory, 'run', 'in.idf')

    # check that the OSM and IDF files exist
    osm = osm_file if os.path.isfile(osm_file) else None
    idf = idf_file if os.path.isfile(idf_file) else None

    return osm, idf


def _run_idf_windows(idf_file_path, epw_file_path, expand_objects=True):
    """Run an IDF file through energyplus on a Windows-based operating system.

    A batch file will be used to run the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objets in
            the IDF but it is unnecessary extra time when they are not present.
            Default: True.

    Returns:
        Path to the folder out of which the simulation was run.
    """
    # check and prepare the input files
    directory = prepare_idf_for_simulation(idf_file_path, epw_file_path)

    # generate the object expansion string if requested
    if expand_objects:
        exp_path = os.path.join(folders.energyplus_path, 'ExpandObjects')
        exp_str = '{}\nif exist expanded.idf MOVE expanded.idf in.idf\n'.format(exp_path)
    else:
        exp_str = ''

    # write a batch file
    run_path = os.path.join(folders.energyplus_path, 'EnergyPlus')
    working_drive = directory[:2]
    batch = '{}\ncd {}\n{}{}'.format(working_drive, directory, exp_str, run_path)
    batch_file = os.path.join(directory, 'in.bat')
    write_to_file(batch_file, batch, True)

    # run the batch file
    os.system(batch_file)

    return directory


def _run_idf_unix(idf_file_path, epw_file_path, expand_objects=True):
    """Run an IDF file through energyplus on a Unix-based operating system.

    This includes both Mac OS and Linux since a shell will be used to run
    the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objets in
            the IDF but it is unnecessary extra time when they are not present.
            Default: True.

    Returns:
        Path to the folder out of which the simulation was run.
    """
    # check and prepare the input files
    directory = prepare_idf_for_simulation(idf_file_path, epw_file_path)

    # generate the object expansion string if requested
    if expand_objects:
        exp_path = os.path.join(folders.energyplus_path, 'ExpandObjects')
        exp_str = '{}\ntest -f expanded.idf && mv expanded.idf in.idf\n'.format(exp_path)
    else:
        exp_str = ''

    # write a shell file
    run_path = os.path.join(folders.energyplus_path, 'EnergyPlus')
    shell = '#!/usr/bin/env bash\n\ncd {}\n{}{}'.format(directory, exp_str, run_path)
    shell_file = os.path.join(directory, 'in.sh')
    write_to_file(shell_file, shell, True)

    # make the shell script executable using subprocess.check_call
    # this is more reliable than native Python chmod on Mac
    subprocess.check_call(['chmod','u+x', shell_file])

    # run the shell script
    subprocess.call(shell_file)

    return directory


def _output_energyplus_files(directory):
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
        err -- Path to a .err file containing all errors and warnings from the
            simulation. Will be None if no file exists.
    """
    # generate paths to the simulation files
    sql_file = os.path.join(directory, 'eplusout.sql')
    eio_file = os.path.join(directory, 'eplusout.eio')
    rdd_file = os.path.join(directory, 'eplusout.rdd')
    html_file = os.path.join(directory, 'eplusout.html')
    err_file = os.path.join(directory, 'eplusout.err')

    # check that the simulation files exist
    sql = sql_file if os.path.isfile(sql_file) else None
    eio = eio_file if os.path.isfile(eio_file) else None
    rdd = rdd_file if os.path.isfile(rdd_file) else None
    html = html_file if os.path.isfile(html_file) else None
    err = err_file if os.path.isfile(err_file) else None

    return sql, eio, rdd, html, err
