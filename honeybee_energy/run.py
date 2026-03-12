# coding=utf-8
"""Module for running IDF files through EnergyPlus."""
from __future__ import division

import os
import sys
import json
import shutil
import subprocess

if (sys.version_info < (3, 0)):
    readmode = 'rb'
    writemode = 'wb'
else:
    readmode = 'r'
    writemode = 'w'

from ladybug.futil import write_to_file
from ladybug.epw import EPW
from ladybug.stat import STAT

from .config import folders
from .measure import Measure
from .result.osw import OSW
from .simulation.parameter import SimulationParameter

HB_OS_MSG = 'Honeybee-openstudio is not installed. Translation to OpenStudio cannot ' \
    'be performed.\nRun pip install honeybee-energy[openstudio] to get all ' \
    'dependencies needed for OpenStudio translation.'


def to_openstudio_sim_folder(
        model, directory, epw_file=None, sim_par=None, schedule_directory=None,
        enforce_rooms=False, use_geometry_names=False, use_resource_names=False,
        additional_measures=None, base_osw=None, strings_to_inject=None,
        report_units=None, viz_variables=None, print_progress=False):
    """Create a .osw to translate honeybee JSONs to an .osm file.

    Args:
        model: The Honeybee Model to be converted into an OpenStudio Model. This
            can also be the path to an .osm file that is already written into
            the directory, in which case the process of translating the model
            will be skipped and this function will only evaluate whether an OSW
            is needed to run the simulation or a directly-translated IDF is suitable.
        directory: The directory into which the output files will be written to.
        epw_file: Optional file path to an EPW that should be associated with the
            output energy model. If None, no EPW file will be assigned to the
            resulting OpenStudio Model and the OSM will not have everything it
            needs to be simulate-able in EnergyPlus. (Default: None).
        sim_par: Optional SimulationParameter object that describes all of the
            settings for the simulation. If None, the resulting OSM will not have
            everything it needs to be simulate-able in EnergyPlus. (Default: None).
        schedule_directory: An optional file directory to which all file-based
            schedules should be written to. If None, all ScheduleFixedIntervals
            will be translated to Schedule:Compact and written fully into the
            IDF string instead of to Schedule:File. (Default: None).
        enforce_rooms: Boolean to note whether this method should enforce the
            presence of Rooms in the Model, which is as necessary prerequisite
            for simulation in EnergyPlus. (Default: False).
        use_geometry_names: Boolean to note whether a cleaned version of all
            geometry display names should be used instead of identifiers when
            translating the Model to OSM and IDF. Using this flag will affect
            all Rooms, Faces, Apertures, Doors, and Shades. It will generally
            result in more read-able names in the OSM and IDF but this means
            that it will not be easy to map the EnergyPlus results back to the
            input Honeybee Model. Cases of duplicate IDs resulting from
            non-unique names will be resolved by adding integers to the ends
            of the new IDs that are derived from the name. (Default: False).
        use_resource_names: Boolean to note whether a cleaned version of all
            resource display names should be used instead of identifiers when
            translating the Model to OSM and IDF. Using this flag will affect
            all Materials, Constructions, ConstructionSets, Schedules, Loads,
            and ProgramTypes. It will generally result in more read-able names
            for the resources in the OSM and IDF. Cases of duplicate IDs
            resulting from non-unique names will be resolved by adding integers
            to the ends of the new IDs that are derived from the name. (Default: False).
        additional_measures: An optional array of honeybee-energy Measure objects
            to be included in the output osw. These Measure objects must have
            values for all required input arguments or an exception will be
            raised while running this function. (Default: None).
        base_osw: Optional file path to an existing OSW JSON be used as the base
            for the output .osw. This is another way that outside measures
            can be incorporated into the workflow. (Default: None).
        strings_to_inject: An additional text string to get appended to the IDF
            before simulation. The input should include complete EnergyPlus objects
            as a single string following the IDF format.
        report_units: A text value to set the units of the OpenStudio Results report
            that can optionally be included in the OSW. If set to None, no report
            will be produced. (Default: None). Choose from the following.

            * si - all units will be in SI
            * ip - all units will be in IP

        viz_variables: An optional list of EnergyPlus output variable names to
            be visualized on the geometry in an output view_data HTML report.
            If None or an empty list, no view_data report is produced. See below
            for an example.
        print_progress: Set to True to have the progress of the translation
            printed as it is completed.

    .. code-block:: python

        viz_variables = [
            "Zone Air System Sensible Heating Rate",
            "Zone Air System Sensible Cooling Rate"
        ]

    Returns:
        A series of file paths to the simulation input files.

        -   osm -- Path to an OpenStudio Model (.osm) file containing the direct
            translation of the Honeybee Model to OpenStudio. None of the
            additional_measures will be applied to this OSM if they are specified
            and any efficiency standards in the simulation parameters won't be
            applied until the OSW is run.

        -   osw -- Path to an OpenStudio Workflow (.osw) JSON file that can be run
            with the OpenStudio CLI. Will be None if the OpenStudio CLI is not
            needed for simulation. This can happen if there is no base_osw,
            no additional_measures, no report_units or viz_variables, and no
            efficiency standard specified in the simulation parameters (which
            requires openstudio-standards).

        -   idf -- Path to an EnergyPlus Input Data File (.idf) that is ready to
            be simulated in EnergyPlus. Will be None if there is an OSW that must
            be run to create the IDF for simulation.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.openstudio import openstudio, OSModel, os_path
        from honeybee_openstudio.simulation import simulation_parameter_to_openstudio, \
            assign_epw_to_model
        from honeybee_openstudio.writer import model_to_openstudio
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))

    # write the OpenStudio model into the directory
    if not os.path.isdir(directory):
        os.makedirs(directory)
    osm = os.path.abspath(os.path.join(directory, 'in.osm'))
    if isinstance(model, str):
        assert os.path.isfile(model), \
            'No file path for an OSM was found at "{}"'.format(model)
        model = os.path.abspath(model)
        if os.path.normcase(model) == os.path.normcase(osm):
            shutil.copy(model, osm)
        osm, os_model = model, None
    else:  # translate the Honeybee SimPar and Model to OpenStudio
        os_model = OSModel()
        set_cz = True
        if sim_par is not None and sim_par.sizing_parameter.climate_zone is not None:
            set_cz = False
        if epw_file is not None:
            assign_epw_to_model(epw_file, os_model, set_cz)
        if sim_par is not None:
            simulation_parameter_to_openstudio(sim_par, os_model)
        os_model = model_to_openstudio(
            model, os_model, schedule_directory=schedule_directory,
            use_geometry_names=use_geometry_names, use_resource_names=use_resource_names,
            enforce_rooms=enforce_rooms, print_progress=print_progress)
        os_model.save(os_path(osm), overwrite=True)

    # load the OpenStudio Efficiency Standards measure if one is specified
    if sim_par is not None and sim_par.sizing_parameter.efficiency_standard is not None:
        assert folders.efficiency_standard_measure_path is not None, \
            'Efficiency standard was specified in the simulation parameters ' \
            'but the efficiency_standard measure is not installed.'
        eff_measure = Measure(folders.efficiency_standard_measure_path)
        units_arg = eff_measure.arguments[0]
        units_arg.value = sim_par.sizing_parameter.efficiency_standard
        if additional_measures is None:
            additional_measures = [eff_measure]
        else:
            additional_measures = list(additional_measures)
            additional_measures.append(eff_measure)

    # load the OpenStudio Results measure if report_units have bee specified
    if report_units is not None and report_units.lower() != 'none':
        assert folders.openstudio_results_measure_path is not None, 'OpenStudio report' \
            ' requested but the openstudio_results measure is not installed.'
        report_measure = Measure(folders.openstudio_results_measure_path)
        units_arg = report_measure.arguments[0]
        units_arg.value = report_units.upper()
        if additional_measures is None:
            additional_measures = [report_measure]
        else:
            additional_measures = list(additional_measures)
            additional_measures.append(report_measure)

    # load the OpenStudio view_data measure if outputs have been requested
    if viz_variables is not None and len(viz_variables) != 0:
        assert folders.view_data_measure_path is not None, 'A visualization variable' \
            'has been requested but the view_data measure is not installed.'
        viz_measure = Measure(folders.view_data_measure_path)
        if len(viz_variables) > 3:
            viz_variables = viz_variables[:3]
        for i, var in enumerate(viz_variables):
            var_arg = viz_measure.arguments[i + 2]
            var_arg.value = var
        if additional_measures is None:
            additional_measures = [viz_measure]
        else:
            additional_measures = list(additional_measures)
            additional_measures.append(viz_measure)

    osw, idf = None, None
    if additional_measures or base_osw:  # prepare an OSW with all of the measures to run
        # load the inject IDF measure if strings_to_inject have bee specified
        if strings_to_inject is not None and strings_to_inject != '':
            assert folders.inject_idf_measure_path is not None, \
                'Additional IDF strings input but the inject_idf measure is not installed.'
            idf_measure = Measure(folders.inject_idf_measure_path)
            inject_idf = os.path.join(directory, 'inject.idf')
            with open(inject_idf, "w") as idf_file:
                idf_file.write(strings_to_inject)
            units_arg = idf_measure.arguments[0]
            units_arg.value = inject_idf
            if additional_measures is None:
                additional_measures = [idf_measure]
            else:
                additional_measures = list(additional_measures)
                additional_measures.append(idf_measure)
        # create a dictionary representation of the .osw
        if base_osw is None:
            osw_dict = {'steps': []}
        else:
            assert os.path.isfile(base_osw), \
                'No base OSW file found at {}.'.format(base_osw)
            with open(base_osw, readmode) as base_file:
                osw_dict = json.load(base_file)
        osw_dict['seed_file'] = osm
        if schedule_directory is not None:
            if 'file_paths' not in osw_dict:
                osw_dict['file_paths'] = [schedule_directory]
            else:
                osw_dict['file_paths'].append(schedule_directory)
        if epw_file is not None:
            osw_dict['weather_file'] = epw_file
        if additional_measures is not None:
            if 'measure_paths' not in osw_dict:
                osw_dict['measure_paths'] = []
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
            if adapter is not None:
                if 'run_options' not in osw_dict:
                    osw_dict['run_options'] = {}
                osw_dict['run_options']['output_adapter'] = {
                    'custom_file_name': adapter,
                    'class_name': 'HoneybeeAdapter',
                    'options': {}
                }
        # write the dictionary to a workflow.osw
        osw = os.path.abspath(os.path.join(directory, 'workflow.osw'))
        if (sys.version_info < (3, 0)):  # we need to manually encode it as UTF-8
            with open(osw, writemode) as fp:
                workflow_str = json.dumps(osw_dict, indent=4, ensure_ascii=False)
                fp.write(workflow_str.encode('utf-8'))
        else:
            with open(osw, writemode, encoding='utf-8') as fp:
                workflow_str = json.dump(osw_dict, fp, indent=4, ensure_ascii=False)
    else:  # the OSM is ready for simulation; translate it to IDF
        run_directory = os.path.join(directory, 'run')
        if not os.path.isdir(run_directory):
            os.mkdir(run_directory)
        idf = os.path.abspath(os.path.join(run_directory, 'in.idf'))
        if not os.path.isfile(idf):
            if os_model is None:  # load the model from the file
                exist_os_model = OSModel.load(os_path(osm))
                if exist_os_model.is_initialized():
                    os_model = exist_os_model.get()
            if (sys.version_info < (3, 0)):
                idf_translator = openstudio.EnergyPlusForwardTranslator()
            else:
                idf_translator = openstudio.energyplus.ForwardTranslator()
            workspace = idf_translator.translateModel(os_model)
            workspace.save(os_path(idf), overwrite=True)
            if strings_to_inject is not None and strings_to_inject != '':
                if (sys.version_info < (3, 0)):  # we need to manually encode it as ASCII
                    with open(idf, 'a') as idf_file:
                        idf_file.write(strings_to_inject.encode('ascii'))
                else:
                    with open(idf, 'a', encoding='ascii') as idf_file:
                        idf_file.write(strings_to_inject)

    return osm, osw, idf


def empty_osm(sim_par=None, epw_file=None, osm_file=None, idf_file=None):
    """Create an empty OSM or IDF file with no building geometry.

    This is useful as a starting point for OSMs to which detailed Ironbug systems
    will be added. Such models with only Ironbug HVAC components can simulate
    in EnergyPlus if they use the LoadProfile:Plant object to represent the
    building loads.

    Args:
        sim_par: A SimulationParameter object that describes all of the settings
            for the simulation. If None, default parameters will be generated.
        epw_file: Full path to an EPW file to be associated with the exported OSM.
            This is typically not necessary but may be used when a sim-par-json is
            specified that requests a HVAC sizing calculation to be run as part
            of the translation process but no design days are inside this
            simulation parameter.
        osm_file: Optional path where the OSM will be output.
        idf_file: Optional path where the IDF will be output.

    Returns:
        A tuple of two file paths.

        -   osm -- Path to an OpenStudio Model (.osm) file containing the simulation
            parameters and references to the EPW file. Will be None if no osm_file
            was input.

        -   idf -- Path to an EnergyPlus Input Data File (.idf) containing the
            simulation parameters. Will be None if no idf_file was input.
    """
    # check that honeybee-openstudio is installed
    try:
        from honeybee_openstudio.openstudio import openstudio, os_path, OSModel
        from honeybee_openstudio.simulation import simulation_parameter_to_openstudio, \
            assign_epw_to_model
    except ImportError as e:  # honeybee-openstudio is not installed
        raise ImportError('{}\n{}'.format(HB_OS_MSG, e))

    # initialize the OpenStudio model that will hold everything
    os_model = OSModel()
    # generate default simulation parameters
    if sim_par is None:
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        sim_par.output.add_hvac_energy_use()
        sim_par.output.add_electricity_generation()
    else:
        sim_par = sim_par.duplicate()  # ensure input is not edited

    # use any specified EPW files to assign design days and the climate zone
    def ddy_from_epw(epw_file, sim_par):
        """Produce a DDY from an EPW file."""
        epw_obj = EPW(epw_file)
        des_days = [epw_obj.approximate_design_day('WinterDesignDay'),
                    epw_obj.approximate_design_day('SummerDesignDay')]
        sim_par.sizing_parameter.design_days = des_days

    if epw_file is not None:
        epw_folder, epw_file_name = os.path.split(epw_file)
        ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))
        stat_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.stat'))
        if len(sim_par.sizing_parameter.design_days) == 0 and \
                os.path.isfile(ddy_file):
            try:
                sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)
            except AssertionError:  # no design days within the DDY file
                ddy_from_epw(epw_file, sim_par)
        elif len(sim_par.sizing_parameter.design_days) == 0:
            ddy_from_epw(epw_file, sim_par)
        if sim_par.sizing_parameter.climate_zone is None and os.path.isfile(stat_file):
            stat_obj = STAT(stat_file)
            sim_par.sizing_parameter.climate_zone = stat_obj.ashrae_climate_zone
        set_cz = True if sim_par.sizing_parameter.climate_zone is None else False
        assign_epw_to_model(epw_file, os_model, set_cz)

    # translate the simulation parameter
    simulation_parameter_to_openstudio(sim_par, os_model)
    gen_files, osm, idf = [], None, None

    # write the OpenStudio Model if specified
    if osm_file is not None:
        osm = os.path.abspath(osm_file)
        os_model.save(os_path(osm), overwrite=True)
        gen_files.append(osm)
    # write the IDF if specified
    if idf_file is not None:
        idf = os.path.abspath(idf_file)
        if (sys.version_info < (3, 0)):
            idf_translator = openstudio.EnergyPlusForwardTranslator()
        else:
            idf_translator = openstudio.energyplus.ForwardTranslator()
        workspace = idf_translator.translateModel(os_model)
        workspace.save(os_path(idf), overwrite=True)
        gen_files.append(idf)
    return osm, idf


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
    # rename the stat file to ensure EnergyPlus does not find it and error
    stat_file, renamed_stat = None, None
    if epw_file_path is not None:
        epw_folder = os.path.dirname(epw_file_path)
        for wf in os.listdir(epw_folder):
            if wf.endswith('.stat'):
                stat_file = os.path.join(epw_folder, wf)
                renamed_stat = os.path.join(epw_folder, wf.replace('.stat', '.hide'))
                try:
                    os.rename(stat_file, renamed_stat)
                except Exception:  # STAT file in restricted location (Program Files)
                    stat_file = None  # hope that it is not a OneBuilding EPW
                break

    # run the simulation
    if os.name == 'nt':  # we are on Windows
        directory = _run_idf_windows(
            idf_file_path, epw_file_path, expand_objects, silent)
    else:  # we are on Mac, Linux, or some other unix-based system
        directory = _run_idf_unix(idf_file_path, epw_file_path, expand_objects)

    # put back the .stat file
    if stat_file is not None:
        os.rename(renamed_stat, stat_file)

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

    if not silent:
        # write a batch file to call OpenStudio CLI; useful for re-running the sim
        working_drive = directory[:2]
        measure_str = '-m ' if measures_only else ''
        batch = '{}\n"{}" run --show-stdout {}-w "{}"'.format(
            working_drive, folders.openstudio_exe, measure_str, osw_json)
        if all(ord(c) < 128 for c in batch):  # just run the batch file as it is
            batch_file = os.path.join(directory, 'run_workflow.bat')
            write_to_file(batch_file, batch, True)
            os.system('"{}"'.format(batch_file))  # run the batch file
            return directory
    # given .bat file restrictions with non-ASCII characters, run the sim with subprocess
    cmds = [folders.openstudio_exe, 'run', '--show-stdout', '-w', osw_json]
    if measures_only:
        cmds.append('-m')
    process = subprocess.Popen(cmds, shell=silent)
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
    shell = '#!/usr/bin/env bash\n"{}" run --show-stdout {}-w "{}"'.format(
        folders.openstudio_exe, measure_str, osw_json)
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

    if not silent:  # write a batch file; useful for re-running the sim
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
        if all(ord(c) < 128 for c in batch):  # just run the batch file as it is
            batch_file = os.path.join(directory, 'in.bat')
            write_to_file(batch_file, batch, True)
            os.system('"{}"'.format(batch_file))  # run the batch file
            return directory
    # given .bat file restrictions with non-ASCII characters, run the sim with subprocess
    cmds = [folders.energyplus_exe, '-i', folders.energyplus_idd_path]
    if epw_file_path is not None:
        cmds.append('-w')
        cmds.append(os.path.abspath(epw_file_path))
    if expand_objects:
        cmds.append('-x')
    process = subprocess.Popen(cmds, cwd=directory, shell=silent)
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


def _parse_os_cli_failure(directory):
    """Parse the failure log of OpenStudio CLI.

    Args:
        directory: Path to the directory out of which the simulation is run.
    """
    log_osw = OSW(os.path.join(directory, 'out.osw'))
    raise Exception(
        'Failed to run OpenStudio CLI:\n{}'.format('\n'.join(log_osw.errors)))


"""Deprecated methods that depend on the old honeybee-openstudio Ruby gem."""


def from_gbxml_osw(gbxml_path, model_path=None, osw_directory=None):
    """Deprecated function that is no longer used."""
    return _raise_deprecation('from_gbxml_osw')


def from_osm_osw(osm_path, model_path=None, osw_directory=None):
    """Deprecated function that is no longer used."""
    return _raise_deprecation('from_osm_osw')


def from_idf_osw(idf_path, model_path=None, osw_directory=None):
    """Deprecated function that is no longer used."""
    _raise_deprecation('from_idf_osw')


def measure_compatible_model_json(
        model_file_path, destination_directory=None, simplify_window_cons=False,
        triangulate_sub_faces=True, triangulate_non_planar_orphaned=False,
        enforce_rooms=False, use_geometry_names=False, use_resource_names=False):
    """Deprecated function that is no longer used."""
    _raise_deprecation('measure_compatible_model_json')


def trace_compatible_model_json(
        model_file_path, destination_directory=None, single_window=True,
        rect_sub_distance='0.15m', frame_merge_distance='0.2m'):
    """Deprecated function that is no longer used."""
    _raise_deprecation('trace_compatible_model_json')


def to_openstudio_osw(osw_directory, model_path, sim_par_json_path=None,
                      additional_measures=None, base_osw=None, epw_file=None,
                      schedule_directory=None, strings_to_inject=None,
                      report_units=None, viz_variables=None):
    """Deprecated function that is no longer used."""
    _raise_deprecation('to_openstudio_osw')


def to_gbxml_osw(model_path, output_path=None, osw_directory=None):
    """Deprecated function that is no longer used."""
    _raise_deprecation('to_gbxml_osw')


def to_sdd_osw(model_path, output_path=None, osw_directory=None):
    """Deprecated function that is no longer used."""
    _raise_deprecation('to_sdd_osw')


def to_empty_osm_osw(osw_directory, sim_par_json_path, epw_file=None):
    """Deprecated function that is no longer used."""
    _raise_deprecation('to_empty_osm_osw')


def _raise_deprecation(func_name):
    msg = 'The function "{}" has been deprecated.\nIf you are receiving this message, ' \
        'it is likely because you are using an old Grasshopper component while ' \
        'having newer core Python libraries installed.\nTo avoid this error, use ' \
        'the updated Grasshopper component from your toolbar.'.format(func_name)
    raise NotImplementedError(msg)
