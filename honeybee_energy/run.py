# coding=utf-8
"""Module for running IDF files through EnergyPlus."""
from __future__ import division

import os
import json
import subprocess

from .config import folders

from honeybee.model import Model

from ladybug.futil import write_to_file, copy_files_to_folder, preparedir


def measure_compatible_model_json(model_json_path, destination_directory=None):
    """Convert a Model JSON to one that is compatible with the honeybee_openstudio_gem.

    This includes the re-serialization of the Model to Python, which will
    automatically ensure that all Apertures and Doors point in the same direction
    as their parent Face. If the Model tolerance is non-zero and Rooms are closed
    solids, this will also ensure that all Room Faces point outwards from their
    parent's volume. Lastly, if the Model units are not Meters, the model will
    be scaled to be in Meters.

    Args:
        model_json_path: File path to the Model JSON.
        destination_directory: The directory into which the Model JSON that is
            compatible with the honeybee_openstudio_gem should be written. If None,
            this will be the same location as the input model_json_path. Default: None.

    Returns:
        The full file path to the new Model JSON written out by this method.
    """
    # check that the file is there
    assert os.path.isfile(model_json_path), \
        'No JSON file found at {}.'.format(model_json_path)

    # get the directory and the file path for the new Model JSON
    directory, init_file_name = os.path.split(model_json_path)
    dest_dir = directory if destination_directory is None else destination_directory
    base_file_name = init_file_name.replace('.json', '')
    file_name = '{}_osm.json'.format(base_file_name)
    dest_file_path = os.path.join(dest_dir, file_name)

    # serialize the Model to Python
    with open(model_json_path) as json_file:
        data = json.load(json_file)
    parsed_model = Model.from_dict(data)

    # remove colinear vertices to avoid E+ tolerance issues and convert Model to Meters
    if parsed_model.tolerance != 0:
        for room in parsed_model.rooms:
            room.remove_colinear_vertices_envelope(parsed_model.tolerance)
    parsed_model.convert_to_units('Meters')

    # get the dictionary representation of the Model
    model_dict = parsed_model.to_dict(triangulate_sub_faces=True)

    # write the dictionary into a file
    preparedir(dest_dir, remove_content=False)  # create the directory if it's not there
    with open(dest_file_path, 'w') as fp:
        json.dump(model_dict, fp)

    return os.path.abspath(dest_file_path)


def to_openstudio_osw(osw_directory, model_json_path, sim_par_json_path=None,
                      additional_measures=None, base_osw=None, epw_file=None):
    """Create a .osw to translate honeybee JSONs to an .osm file.

    Args:
        osw_directory: The directory into which the .osw should be written and the
            .osm will eventually be written into.
        model_json_path: File path to the Model JSON.
        sim_par_json_path: Optional file path to the SimulationParameter JSON.
            If None, the resulting OSM will not have everything it needs to be
            simulate-able.
        additional_measures: An optional array of honeybee-energy Measure objects
            to be included in the output osw. These Measure objects must have
            values for all required input arguments or an exception will be
            raised while running this function.
        base_osw: Optional file path to an existing OSW JSON be used as the base
            for the output .osw. This is another way that outside measures
            can be incorporated into the workflow.
        epw_file: Optional file path to an EPW that should be associated with the
            output energy model.

    Returns:
        The file path to the .osw written out by this method.
    """
    # create a dictionary representation of the .osw with steps to run
    # the model measure and the simulation parameter measure
    if base_osw is None:
        osw_dict = {'steps': []}
    else:
        assert os.path.isfile(base_osw), 'No base OSW file found at {}.'.format(base_osw)
        with open(base_osw, 'r') as base_file:
            osw_dict = json.load(base_file)

    # add a simulation parameter step if it is specified
    if sim_par_json_path is not None:
        sim_par_dict = {
            'arguments': {
                'simulation_parameter_json': sim_par_json_path
            },
            'measure_dir_name': 'from_honeybee_simulation_parameter'
        }
        osw_dict['steps'].insert(0, sim_par_dict)

    # addd the model json serialization into the steps
    model_measure_dict = {
        'arguments': {
            'model_json': model_json_path
        },
        'measure_dir_name': 'from_honeybee_model'
    }
    osw_dict['steps'].insert(0, model_measure_dict)

    # assign the measure_paths to the osw_dict
    if 'measure_paths' not in osw_dict:
        osw_dict['measure_paths'] = []
    if folders.honeybee_openstudio_gem_path:  # include honeybee-openstudio measure path
        measure_dir = os.path.join(folders.honeybee_openstudio_gem_path, 'measures')
        osw_dict['measure_paths'].append(measure_dir)

    # add any additional measures to the osw_dict
    if additional_measures:
        measure_paths = set()  # set of all unique measure paths
        # ensure measures are correctly ordered
        m_dict = {'ModelMeasure': [], 'EnergyPlusMeasure': [], 'ReportingMeasure': []}
        for measure in additional_measures:
            m_dict[measure.type].append(measure)
        sorted_measures = m_dict['ModelMeasure'] + m_dict['EnergyPlusMeasure'] + \
            m_dict['ReportingMeasure']
        for measure in sorted_measures:
            measure.validate()  # ensure that all required arguments have values
            measure_paths.add(os.path.dirname(measure.folder))
            osw_dict['steps'].append(measure.to_osw_dict())  # add measure to workflow
        for m_path in measure_paths:
            osw_dict['measure_paths'].append(m_path)

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
            in the running of the OSW (True) or the resulting model should be run
            through EnergyPlus after the measures are applied to it (False).
            Default: True.

    Returns:
        The following files output from the CLI run

        -   osm -- Path to a .osm file representing the output model.
            Will be None if no file exists.

        -   idf -- Path to a .idf file representing the model.
            Will be None if no file exists.
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
        directory -- The folder in which the IDF exists and out of which the EnergyPlus
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
            This is a necessary step whenever there are HVAC Template objects in
            the IDF but it is unnecessary extra time when they are not present.
            Default: True.

    Returns:
        A series of file paths to the simulation output files

        -   sql -- Path to a .sqlite file containing all simulation results.
            Will be None if no file exists.

        -   zsz -- Path to a .csv file containing detailed zone load information
            recorded over the course of the design days. Will be None if no
            file exists.

        -   rdd -- Path to a .rdd file containing all possible outputs that can be
            requested from the simulation. Will be None if no file exists.

        -   html -- Path to a .html file containing all summary reports.
            Will be None if no file exists.

        -   err -- Path to a .err file containing all errors and warnings from the
            simulation. Will be None if no file exists.
    """
    # run the simulation
    if os.name == 'nt':  # we are on Windows
        directory = _run_idf_windows(idf_file_path, epw_file_path, expand_objects)
    else:  # we are on Mac, Linux, or some other unix-based system
        directory = _run_idf_unix(idf_file_path, epw_file_path, expand_objects)

    # output the simulation files
    return output_energyplus_files(directory)


def output_energyplus_files(directory):
    """Get the paths to the EnergyPlus simulation output files given the idf directory.

    Args:
        directory: The path to where the IDF was run.

    Returns:
        A tuple with four elements

        -   sql -- Path to a .sqlite file containing all simulation results.
            Will be None if no file exists.

        -   zsz -- Path to a .csv file containing detailed zone load information
            recorded over the course of the design days. Will be None if no
            file exists.

        -   rdd -- Path to a .rdd file containing all possible outputs that can be
            requested from the simulation. Will be None if no file exists.

        -   html -- Path to a .html file containing all summary reports.
            Will be None if no file exists.

        -   err -- Path to a .err file containing all errors and warnings from the
            simulation. Will be None if no file exists.
    """
    # generate paths to the simulation files
    sql_file = os.path.join(directory, 'eplusout.sql')
    zsz_file = os.path.join(directory, 'epluszsz.csv')
    rdd_file = os.path.join(directory, 'eplusout.rdd')
    html_file = os.path.join(directory, 'eplustbl.htm')
    err_file = os.path.join(directory, 'eplusout.err')

    # check that the simulation files exist
    sql = sql_file if os.path.isfile(sql_file) else None
    zsz = zsz_file if os.path.isfile(zsz_file) else None
    rdd = rdd_file if os.path.isfile(rdd_file) else None
    html = html_file if os.path.isfile(html_file) else None
    err = err_file if os.path.isfile(err_file) else None

    return sql, zsz, rdd, html, err


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
            in the running of the OSW (True) or the resulting model should be run
            through EnergyPlus after the measures are applied to it (False).
            Default: True.

    Returns:
        Path to the folder out of which the OSW was run.
    """
    # check the input file
    directory = _check_osw(osw_json)

    # Write the batch file to call OpenStudio CLI
    working_drive = directory[:2]
    measure_str = '-m ' if measures_only else ''
    batch = '{}\n"{}" -I {} run {}-w {}'.format(
        working_drive, folders.openstudio_exe, folders.honeybee_openstudio_gem_path,
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
            in the running of the OSW (True) or the resulting model should be run
            through EnergyPlus after the measures are applied to it (False).
            Default: True.

    Returns:
        Path to the folder out of which the OSW was run.
    """
    # check the input file
    directory = _check_osw(osw_json)

    # Write the shell script to call OpenStudio CLI
    measure_str = '-m ' if measures_only else ''
    shell = '#!/usr/bin/env bash\n"{}" -I {} run {}-w {}'.format(
        folders.openstudio_exe, folders.honeybee_openstudio_gem_path,
        measure_str, osw_json)
    shell_file = os.path.join(directory, 'run_workflow.sh')
    write_to_file(shell_file, shell, True)

    # make the shell script executable using subprocess.check_call
    # this is more reliable than native Python chmod on Mac
    subprocess.check_call(['chmod', 'u+x', shell_file])

    # run the shell script
    subprocess.call(shell_file)

    return directory


def _output_openstudio_files(directory):
    """Get the paths to the OpenStudio simulation output files given the osw directory.

    Args:
        directory: The path to where the OSW was run.

    Returns:

        -   osm -- Path to a .osm file containing all simulation results.
            Will be None if no file exists.

        -   idf -- Path to a .idf file containing properties of the model, including
            the size of HVAC objects. Will be None if no file exists.
    """
    # generate and check paths to the OSM and IDF files
    osm_file = os.path.join(directory, 'run', 'in.osm')
    osm = osm_file if os.path.isfile(osm_file) else None

    # check the pre-process idf and replace the other in.idf with it
    idf_file_right = os.path.join(directory, 'run', 'pre-preprocess.idf')
    idf_file_wrong = os.path.join(directory, 'run', 'in.idf')
    if os.path.isfile(idf_file_right) and os.path.isfile(idf_file_wrong):
        os.remove(idf_file_wrong)
        os.rename(idf_file_right, idf_file_wrong)
        idf = idf_file_wrong
    else:
        idf = None

    return osm, idf


def _run_idf_windows(idf_file_path, epw_file_path, expand_objects=True):
    """Run an IDF file through energyplus on a Windows-based operating system.

    A batch file will be used to run the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file.
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objects in
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
            This is a necessary step whenever there are HVAC Template objects in
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
    run_path = os.path.join(folders.energyplus_path, 'energyplus')
    shell = '#!/usr/bin/env bash\n\ncd {}\n{}{}'.format(directory, exp_str, run_path)
    shell_file = os.path.join(directory, 'in.sh')
    write_to_file(shell_file, shell, True)

    # make the shell script executable using subprocess.check_call
    # this is more reliable than native Python chmod on Mac
    subprocess.check_call(['chmod', 'u+x', shell_file])

    # run the shell script
    subprocess.call(shell_file)

    return directory
