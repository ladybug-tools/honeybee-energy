# coding=utf-8
"""Module for running IDF files through EnergyPlus."""
from __future__ import division

import os
import json
import subprocess

from .config import folders

from honeybee.model import Model
from honeybee.config import folders as hb_folders

from ladybug.futil import write_to_file, preparedir


def from_gbxml_osw(gbxml_path, model_path=None, osw_directory=None):
    """Create a .osw to translate gbXML to a HBJSON file.

    Args:
        gbxml_path: File path to the gbXML to be translated to HBJSON.
        model_path: File path to where the Model HBJSON will be written. If None, it
            will be output right next to the input file and given the same name.
        osw_directory: The directory into which the .osw should be written. If None,
            it will be written into the a temp folder in the default simulation folder.
    """
    return _import_model_osw(gbxml_path, 'gbxml', model_path, osw_directory)


def from_osm_osw(osm_path, model_path=None, osw_directory=None):
    """Create a .osw to translate OSM to a HBJSON file.

    Args:
        osm_path: File path to the OSM to be translated to HBJSON.
        model_path: File path to where the Model HBJSON will be written. If None, it
            will be output right next to the input file and given the same name.
        osw_directory: The directory into which the .osw should be written. If None,
            it will be written into the a temp folder in the default simulation folder.
    """
    return _import_model_osw(osm_path, 'openstudio', model_path, osw_directory)


def from_idf_osw(idf_path, model_path=None, osw_directory=None):
    """Create a .osw to translate IDF to a HBJSON file.

    Args:
        osm_path: File path to the IDF to be translated to HBJSON.
        model_path: File path to where the Model HBJSON will be written. If None, it
            will be output right next to the input file and given the same name.
        osw_directory: The directory into which the .osw should be written. If None,
            it will be written into the a temp folder in the default simulation folder.
    """
    return _import_model_osw(idf_path, 'idf', model_path, osw_directory)


def measure_compatible_model_json(model_json_path, destination_directory=None):
    """Convert a Model JSON to one that is compatible with the honeybee_openstudio_gem.

    This includes the re-serialization of the Model to Python, which will
    automatically ensure that all Apertures and Doors point in the same direction
    as their parent Face. If the Model tolerance is non-zero and Rooms are closed
    solids, this will also ensure that all Room Faces point outwards from their
    parent's volume. If the Model units are not Meters, the model will be scaled
    to be in Meters. Lastly, apertures and doors with more than 4 vertices will
    be triangulated to ensure EnergyPlus accepts them.

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
    directory, _ = os.path.split(model_json_path)
    dest_dir = directory if destination_directory is None else destination_directory
    dest_file_path = os.path.join(dest_dir, 'in.hbjson')

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


def to_gbxml_osw(model_path, output_path=None, osw_directory=None):
    """Create a .osw to translate HBJSON to a gbXML file.

    Args:
        model_path: File path to Honeybee Model (HBJSON).
        output_path: File path to where the gbXML will be written. If None, it
            will be output right next to the input file and given the same name.
        osw_directory: The directory into which the .osw should be written. If None,
            it will be written into the a temp folder in the default simulation folder.
    """
    # create the dictionary with the OSW steps
    osw_dict = {'steps': []}
    model_measure_dict = {
        'arguments': {
            'model_json': model_path
        },
        'measure_dir_name': 'from_honeybee_model_to_gbxml'
    }
    if output_path is not None:
        model_measure_dict['arguments']['output_file_path'] = output_path
    osw_dict['steps'].append(model_measure_dict)

    # add measure paths
    osw_dict['measure_paths'] = []
    if folders.honeybee_openstudio_gem_path:  # include honeybee-openstudio measure path
        measure_dir = os.path.join(folders.honeybee_openstudio_gem_path, 'measures')
        osw_dict['measure_paths'].append(measure_dir)

    # write the dictionary to a workflow.osw
    if osw_directory is None:
        osw_directory = os.path.join(
            hb_folders.default_simulation_folder, 'temp_translate')
        if not os.path.isdir(osw_directory):
            os.mkdir(osw_directory)
    osw_json = os.path.join(osw_directory, 'translate_honeybee.osw')
    with open(osw_json, 'w') as fp:
        json.dump(osw_dict, fp, indent=4)

    return os.path.abspath(osw_json)


def to_openstudio_osw(osw_directory, model_json_path, sim_par_json_path=None,
                      additional_measures=None, base_osw=None, epw_file=None,
                      schedule_directory=None):
    """Create a .osw to translate honeybee JSONs to an .osm file.

    Args:
        osw_directory: The directory into which the .osw should be written and the
            .osm will eventually be written into.
        model_json_path: File path to the Model JSON.
        sim_par_json_path: Optional file path to the SimulationParameter JSON.
            If None, the resulting OSM will not have everything it needs to be
            simulate-able in EnergyPlus. (Default: None).
        additional_measures: An optional array of honeybee-energy Measure objects
            to be included in the output osw. These Measure objects must have
            values for all required input arguments or an exception will be
            raised while running this function. (Default: None).
        base_osw: Optional file path to an existing OSW JSON be used as the base
            for the output .osw. This is another way that outside measures
            can be incorporated into the workflow. (Default: None).
        epw_file: Optional file path to an EPW that should be associated with the
            output energy model. If None, no EPW file will be written into the
            OSW. (Default: None).
        schedule_directory: An optional file directory to which all file-based
            schedules should be written to. If None, all ScheduleFixedIntervals
            will be translated to Schedule:Compact and written fully into the
            IDF string instead of to Schedule:File. (Default: None).

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
    if schedule_directory is not None:
        model_measure_dict['arguments']['schedule_csv_dir'] = schedule_directory
    osw_dict['steps'].insert(0, model_measure_dict)

    # assign the measure_paths to the osw_dict
    if 'measure_paths' not in osw_dict:
        osw_dict['measure_paths'] = []
    if folders.honeybee_openstudio_gem_path:  # include honeybee-openstudio measure path
        measure_dir = os.path.join(folders.honeybee_openstudio_gem_path, 'measures')
        osw_dict['measure_paths'].append(measure_dir)

    # assign the schedule_directory to the file_paths if it is specified
    if schedule_directory is not None:
        if 'file_paths' not in osw_dict:
            osw_dict['file_paths'] = [schedule_directory]
        else:
            osw_dict['file_paths'].append(schedule_directory)

    # add any additional measures to the osw_dict
    if additional_measures:
        measure_paths = set()  # set of all unique measure paths
        # ensure measures are correctly ordered
        m_dict = {'ModelMeasure': [], 'EnergyPlusMeasure': [], 'ReportingMeasure': []}
        for measure in additional_measures:
            m_dict[measure.type].append(measure)
        sorted_measures = m_dict['ModelMeasure'] + m_dict['EnergyPlusMeasure'] + \
            m_dict['ReportingMeasure']
        # add the measures and the measure paths to the OSW
        for measure in sorted_measures:
            measure.validate()  # ensure that all required arguments have values
            measure_paths.add(os.path.dirname(measure.folder))
            osw_dict['steps'].append(measure.to_osw_dict())  # add measure to workflow
        for m_path in measure_paths:
            osw_dict['measure_paths'].append(m_path)
        # if there were reporting measures, add the ladybug adapter to get sim progress
        adapter = folders.honeybee_adapter_path
        if len(m_dict['ReportingMeasure']) != 0 and adapter is not None:
            if 'run_options' not in osw_dict:
                osw_dict['run_options'] = {}
            osw_dict['run_options']['output_adapter'] = {
                'custom_file_name': adapter,
                'class_name': 'HoneybeeAdapter',
                'options': {}
            }

    # assign the epw_file to the osw if it is input
    if epw_file is not None:
        osw_dict['weather_file'] = epw_file

    # write the dictionary to a workflow.osw
    osw_json = os.path.join(osw_directory, 'workflow.osw')
    with open(osw_json, 'w') as fp:
        json.dump(osw_dict, fp, indent=4)

    return os.path.abspath(osw_json)


def run_osw(osw_json, measures_only=True, silent=False):
    """Run a .osw file using the OpenStudio CLI on any operating system.

    Args:
        osw_json: File path to a OSW file to be run using OpenStudio CLI.
        measures_only: Boolean to note whether only the measures should be
            applied in the running of the OSW (True) or the resulting model
            should be run through EnergyPlus after the measures are applied
            to it (False). (Default: True).
        silent: Boolean to note whether the OSW should be run silently.
            This only has an effect on Windows simulations since Unix-based
            simulations always use shell and are always silent (Default: False).

    Returns:
        The following files output from the CLI run

        -   osm -- Path to a .osm file representing the output model.
            Will be None if no file exists.

        -   idf -- Path to a .idf file representing the model.
            Will be None if no file exists.
    """
    # run the simulation
    if os.name == 'nt':  # we are on Windows
        directory = _run_osw_windows(osw_json, measures_only, silent)
    else:  # we are on Mac, Linux, or some other unix-based system
        directory = _run_osw_unix(osw_json, measures_only)

    # output the simulation files
    return _output_openstudio_files(directory)


def prepare_idf_for_simulation(idf_file_path, epw_file_path=None):
    """Prepare an IDF file to be run through EnergyPlus.

    This includes checking that the EPW file and IDF file exist and renaming the
    IDF to in.idf (if it is not already named so). A check is also performed to
    be sure that a valid EnergyPlus installation was found.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file. Note that inputting None here
            is only appropriate when the simulation is just for design days and has
            no weather file run period. (Default: None).

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
    if epw_file_path is not None:
        assert os.path.isfile(epw_file_path), \
            'No EPW file found at {}.'.format(epw_file_path)

    # rename the idf file to in.idf if it isn't named that already
    directory = os.path.split(idf_file_path)[0]
    idf_file_name = os.path.split(idf_file_path)[-1]
    if idf_file_name != 'in.idf':
        old_file_name = os.path.join(directory, idf_file_name)
        new_file_name = os.path.join(directory, 'in.idf')
        # ensure that there isn't an in.idf file there already
        if os.path.isfile(new_file_name):
            os.remove(new_file_name)
        os.rename(old_file_name, new_file_name)

    return directory


def run_idf(idf_file_path, epw_file_path=None, expand_objects=True, silent=False):
    """Run an IDF file through energyplus on any operating system.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file. Note that inputting None here
            is only appropriate when the simulation is just for design days and has
            no weather file run period. (Default: None).
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objects in
            the IDF but it is unnecessary extra time when they are not
            present. (Default: True).
        silent: Boolean to note whether the simulation should be run silently.
            This only has an effect on Windows simulations since Unix-based
            simulations always use shell and are always silent (Default: False).

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
        directory = _run_idf_windows(
            idf_file_path, epw_file_path, expand_objects, silent)
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


def _import_model_osw(model_path, extension, output_path=None, osw_directory=None):
    """Base function used for OSW transating from various formats to HBJSON.

    Args:
        model_path: File path to the file to be translated to HBJSON.
        extension: Name of the file type to be translated (eg. gbxml).
        output_path: File path to where the Model HBJSON will be written.
        osw_directory: The directory into which the .osw should be written.
    """
    # create the dictionary with the OSW steps
    osw_dict = {'steps': []}
    model_measure_dict = {
        'arguments': {
            '{}_model'.format(extension): model_path
        },
        'measure_dir_name': 'from_{}_model'.format(extension)
    }
    if output_path is not None:
        model_measure_dict['arguments']['output_file_path'] = output_path
    osw_dict['steps'].append(model_measure_dict)

    # add measure paths
    osw_dict['measure_paths'] = []
    if folders.honeybee_openstudio_gem_path:  # include honeybee-openstudio measure path
        measure_dir = os.path.join(folders.honeybee_openstudio_gem_path, 'measures')
        osw_dict['measure_paths'].append(measure_dir)

    # write the dictionary to a workflow.osw
    if osw_directory is None:
        osw_directory = os.path.join(
            hb_folders.default_simulation_folder, 'temp_translate')
        if not os.path.isdir(osw_directory):
            os.mkdir(osw_directory)
    osw_json = os.path.join(osw_directory, 'translate_{}.osw'.format(extension))
    with open(osw_json, 'w') as fp:
        json.dump(osw_dict, fp, indent=4)

    return os.path.abspath(osw_json)


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


def _run_osw_windows(osw_json, measures_only=True, silent=False):
    """Run a .osw file using the OpenStudio CLI on a Windows-based operating system.

    A batch file will be used to run the simulation.

    Args:
        osw_json: File path to a OSW file to be run using OpenStudio CLI.
        measures_only: Boolean to note whether only the measures should be applied
            in the running of the OSW (True) or the resulting model should be run
            through EnergyPlus after the measures are applied to it (False).
            Default: True.
        silent: Boolean to note whether the OSW should be run silently (without
            the batch window). If so, the simulation will be run using subprocess
            with shell set to True. (Default: False).

    Returns:
        Path to the folder out of which the OSW was run.
    """
    # check the input file
    directory = _check_osw(osw_json)

    if not silent:  # write the batch file to call OpenStudio CLI
        working_drive = directory[:2]
        measure_str = '-m ' if measures_only else ''
        batch = '{}\n"{}" -I "{}" run {}-w "{}"'.format(
            working_drive, folders.openstudio_exe, folders.honeybee_openstudio_gem_path,
            measure_str, osw_json)
        batch_file = os.path.join(directory, 'run_workflow.bat')
        write_to_file(batch_file, batch, True)
        os.system('"{}"'.format(batch_file))  # run the batch file
    else:  # run it all using subprocess
        cmds = [folders.openstudio_exe, '-I', folders.honeybee_openstudio_gem_path,
                'run', '-w', osw_json]
        if measures_only:
            cmds.append('-m')
        process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=True)
        process.communicate()  # prevents the script from running before command is done

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
    shell = '#!/usr/bin/env bash\n"{}" -I "{}" run {}-w "{}"'.format(
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


def _run_idf_windows(idf_file_path, epw_file_path=None, expand_objects=True,
                     silent=False):
    """Run an IDF file through energyplus on a Windows-based operating system.

    A batch file will be used to run the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file. Note that inputting None here
            is only appropriate when the simulation is just for design days and has
            no weather file run period. (Default: None).
        expand_objects: If True, the IDF run will include the expansion of any
            HVAC Template objects in the file before beginning the simulation.
            This is a necessary step whenever there are HVAC Template objects in
            the IDF but it is unnecessary extra time when they are not
            present. (Default: True).
        silent: Boolean to note whether the simulation should be run silently
            (without the batch window). If so, the simulation will be run using
            subprocess with shell set to True. (Default: False).

    Returns:
        Path to the folder out of which the simulation was run.
    """
    # check and prepare the input files
    directory = prepare_idf_for_simulation(idf_file_path, epw_file_path)

    if not silent:  # run the simulations using a batch file
        # generate various arguments to pass to the energyplus command
        epw_str = '-w "{}"'.format(os.path.abspath(epw_file_path)) \
            if epw_file_path is not None else ''
        idd_str = '-i "{}"'.format(folders.energyplus_idd_path)
        expand_str = ' -x' if expand_objects else ''
        working_drive = directory[:2]
        # write the batch file
        batch = '{}\ncd "{}"\n"{}" {} {}{}'.format(
            working_drive, directory, folders.energyplus_exe, epw_str,
            idd_str, expand_str)
        batch_file = os.path.join(directory, 'in.bat')
        write_to_file(batch_file, batch, True)
        os.system('"{}"'.format(batch_file))  # run the batch file
    else:  # run the simulation using subprocess
        cmds = [folders.energyplus_exe, '-i', folders.energyplus_idd_path]
        if epw_file_path is not None:
            cmds.append('-w')
            cmds.append(os.path.abspath(epw_file_path))
        if expand_objects:
            cmds.append('-x')
        process = subprocess.Popen(
            cmds, cwd=directory, stdout=subprocess.PIPE, shell=True)
        process.communicate()  # prevents the script from running before command is done

    return directory


def _run_idf_unix(idf_file_path, epw_file_path=None, expand_objects=True):
    """Run an IDF file through energyplus on a Unix-based operating system.

    This includes both Mac OS and Linux since a shell will be used to run
    the simulation.

    Args:
        idf_file_path: The full path to an IDF file.
        epw_file_path: The full path to an EPW file. Note that inputting None here
            is only appropriate when the simulation is just for design days and has
            no weather file run period. (Default: None).
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

    # generate various arguments to pass to the energyplus command
    epw_str = '-w "{}"'.format(os.path.abspath(epw_file_path))\
        if epw_file_path is not None else ''
    idd_str = '-i "{}"'.format(folders.energyplus_idd_path)
    expand_str = ' -x' if expand_objects else ''

    # write a shell file
    shell = '#!/usr/bin/env bash\n\ncd "{}"\n"{}" {} {}{}'.format(
        directory, folders.energyplus_exe, epw_str, idd_str, expand_str)
    shell_file = os.path.join(directory, 'in.sh')
    write_to_file(shell_file, shell, True)

    # make the shell script executable using subprocess.check_call
    # this is more reliable than native Python chmod on Mac
    subprocess.check_call(['chmod', 'u+x', shell_file])

    # run the shell script
    subprocess.call(shell_file)

    return directory
