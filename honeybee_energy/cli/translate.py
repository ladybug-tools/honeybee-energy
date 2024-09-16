"""honeybee energy translation commands."""
import click
import sys
import os
import logging
import json
import shutil
import re

from ladybug.futil import preparedir
from ladybug.analysisperiod import AnalysisPeriod
from ladybug.epw import EPW
from honeybee.model import Model
from honeybee.typing import clean_rad_string
from honeybee.config import folders as hb_folders

from honeybee_energy.simulation.parameter import SimulationParameter
from honeybee_energy.construction.dictutil import dict_to_construction
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.schedule.dictutil import dict_to_schedule
from honeybee_energy.schedule.ruleset import ScheduleRuleset
from honeybee_energy.properties.model import ModelEnergyProperties
from honeybee_energy.run import measure_compatible_model_json, to_openstudio_osw, \
    to_gbxml_osw, to_sdd_osw, run_osw, from_gbxml_osw, from_osm_osw, from_idf_osw, \
    add_gbxml_space_boundaries, set_gbxml_floor_types, trace_compatible_model_json, \
    _parse_os_cli_failure
from honeybee_energy.writer import energyplus_idf_version
from honeybee_energy.config import folders

_logger = logging.getLogger(__name__)


@click.group(help='Commands for translating Honeybee Models files.')
def translate():
    pass


@translate.command('model-to-osm')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for '
              'the simulation. If None default parameters will be generated.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--epw-file', '-epw', help='Full path to an EPW file to be associated '
              'with the exported OSM. This is typically not necessary but may be '
              'used when a sim-par-json is specified that requests a HVAC sizing '
              'calculation to be run as part of the translation process but no design '
              'days are inside this simulation parameter.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--folder', '-f', help='Folder on this computer, into which the '
              'working files, OSM and IDF files will be written. If None, the '
              'files will be output in the same location as the model_file.',
              default=None, show_default=True,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--osm-file', '-osm', help='Optional path where the OSM will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--idf-file', '-idf', help='Optional path where the IDF will be copied '
              'after it is translated in the folder. If None, the file will not '
              'be copied.', type=str, default=None, show_default=True)
@click.option('--geometry-ids/--geometry-names', ' /-gn', help='Flag to note whether a '
              'cleaned version of all geometry display names should be used instead '
              'of identifiers when translating the Model to OSM and IDF. '
              'Using this flag will affect all Rooms, Faces, Apertures, '
              'Doors, and Shades. It will generally result in more read-able names '
              'in the OSM and IDF but this means that it will not be easy to map '
              'the EnergyPlus results back to the original Honeybee Model. Cases '
              'of duplicate IDs resulting from non-unique names will be resolved '
              'by adding integers to the ends of the new IDs that are derived from '
              'the name.', default=True, show_default=True)
@click.option('--resource-ids/--resource-names', ' /-rn', help='Flag to note whether a '
              'cleaned version of all resource display names should be used instead '
              'of identifiers when translating the Model to OSM and IDF. '
              'Using this flag will affect all Materials, Constructions, '
              'ConstructionSets, Schedules, Loads, and ProgramTypes. It will generally '
              'result in more read-able names for the resources in the OSM and IDF. '
              'Cases of duplicate IDs resulting from non-unique names will be resolved '
              'by adding integers to the ends of the new IDs that are derived from '
              'the name.', default=True, show_default=True)
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'exported directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--log-file', '-log', help='Optional log file to output the paths to the '
              'generated OSM and IDF files if they were successfully created. '
              'By default this will be printed out to stdout.',
              type=click.File('w'), default='-', show_default=True)
def model_to_osm_cli(
        model_file, sim_par_json, epw_file, folder, osm_file, idf_file,
        geometry_ids, resource_ids, check_model, log_file):
    """Translate a Honeybee Model file into an OpenStudio Model and corresponding IDF.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        geo_names = not geometry_ids
        res_names = not resource_ids
        bypass_check = not check_model
        model_to_osm(
            model_file, sim_par_json, epw_file, folder, osm_file, idf_file,
            geo_names, res_names, bypass_check, log_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_osm(
    model_file, sim_par_json=None, epw_file=None, folder=None,
    osm_file=None, idf_file=None, geometry_names=False, resource_names=False,
    bypass_check=False, log_file=None,
    geometry_ids=True, resource_ids=True, check_model=True
):
    """Translate a Honeybee Model file into an OpenStudio Model and corresponding IDF.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        sim_par_json: Full path to a honeybee energy SimulationParameter JSON that
            describes all of the settings for the simulation. If None, default
            parameters will be generated.
        epw_file: Full path to an EPW file to be associated with the exported OSM.
            This is typically not necessary but may be used when a sim-par-json is
            specified that requests a HVAC sizing calculation to be run as part
            of the translation process but no design days are inside this
            simulation parameter.
        folder: Folder on this computer, into which the working files, OSM and IDF
            files will be written. If None, the files will be output in the
            same location as the model_file.
        osm_file: Optional path where the OSM will be copied after it is translated
            in the folder. If None, the file will not be copied.
        idf_file: Optional path where the IDF will be copied after it is translated
            in the folder. If None, the file will not be copied.
        geometry_names: Boolean to note whether a cleaned version of all geometry
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Rooms, Faces,
            Apertures, Doors, and Shades. It will generally result in more read-able
            names in the OSM and IDF but this means that it will not be easy to map
            the EnergyPlus results back to the original Honeybee Model. Cases
            of duplicate IDs resulting from non-unique names will be resolved
            by adding integers to the ends of the new IDs that are derived from
            the name. (Default: False).
        resource_names: Boolean to note whether a cleaned version of all resource
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Materials,
            Constructions, ConstructionSets, Schedules, Loads, and ProgramTypes.
            It will generally result in more read-able names for the resources
            in the OSM and IDF. Cases of duplicate IDs resulting from non-unique
            names will be resolved by adding integers to the ends of the new IDs
            that are derived from the name. (Default: False).
        bypass_check: Boolean to note whether the Model should be re-serialized
            to Python and checked before it is translated to .osm. The check is
            not needed if the model-json was exported directly from the
            honeybee-energy Python library. (Default: False).
        log_file: Optional log file to output the paths to the generated OSM and]
            IDF files if they were successfully created. By default this string
            will be returned from this method.
    """
    # set the default folder if it's not specified
    if folder is None:
        folder = os.path.dirname(os.path.abspath(model_file))
    preparedir(folder, remove_content=False)

    # generate default simulation parameters
    if sim_par_json is None:
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        sim_par.output.add_hvac_energy_use()
        sim_par.output.add_electricity_generation()
        sim_par.output.reporting_frequency = 'Monthly'

    else:
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        sim_par = SimulationParameter.from_dict(data)

    # perform a check to be sure the EPW file is specified for sizing runs
    def ddy_from_epw(epw_file, sim_par):
        """Produce a DDY from an EPW file."""
        epw_obj = EPW(epw_file)
        des_days = [epw_obj.approximate_design_day('WinterDesignDay'),
                    epw_obj.approximate_design_day('SummerDesignDay')]
        sim_par.sizing_parameter.design_days = des_days

    def write_sim_par(sim_par):
        """Write simulation parameter object to a JSON."""
        sim_par_dict = sim_par.to_dict()
        sp_json = os.path.abspath(os.path.join(folder, 'simulation_parameter.json'))
        with open(sp_json, 'w') as fp:
            json.dump(sim_par_dict, fp)
        return sp_json

    if sim_par.sizing_parameter.efficiency_standard is not None:
        assert epw_file is not None, 'An epw_file must be specified for ' \
            'translation to OSM whenever a Simulation Parameter ' \
            'efficiency_standard is specified.\nNo EPW was specified yet the ' \
            'Simulation Parameter efficiency_standard is "{}".'.format(
                sim_par.sizing_parameter.efficiency_standard
            )
        epw_folder, epw_file_name = os.path.split(epw_file)
        ddy_file = os.path.join(epw_folder, epw_file_name.replace('.epw', '.ddy'))
        if len(sim_par.sizing_parameter.design_days) == 0 and \
                os.path.isfile(ddy_file):
            try:
                sim_par.sizing_parameter.add_from_ddy_996_004(ddy_file)
            except AssertionError:  # no design days within the DDY file
                ddy_from_epw(epw_file, sim_par)
        elif len(sim_par.sizing_parameter.design_days) == 0:
            ddy_from_epw(epw_file, sim_par)
        sim_par_json = write_sim_par(sim_par)
    elif sim_par_json is None:
        sim_par_json = write_sim_par(sim_par)

    # run the Model re-serialization and check if specified
    if not bypass_check:  # use display names if requested
        model_file = measure_compatible_model_json(
            model_file, folder, use_geometry_names=geometry_names,
            use_resource_names=resource_names)

    # Write the osw file to translate the model to osm
    osw = to_openstudio_osw(folder, model_file, sim_par_json, epw_file=epw_file)

    # run the measure to translate the model JSON to an openstudio measure
    osm, idf = run_osw(osw)
    # run the resulting idf through EnergyPlus
    if idf is not None and os.path.isfile(idf):
        if osm_file is not None:
            if not osm_file.lower().endswith('.osm'):
                osm_file = osm_file + '.osm'
            shutil.copyfile(osm, osm_file)
        if idf_file is not None:
            if not idf_file.lower().endswith('.idf'):
                idf_file = idf_file + '.idf'
            shutil.copyfile(idf, idf_file)
        if log_file is None:
            return json.dumps([osm, idf], indent=4)
        else:
            log_file.write(json.dumps([osm, idf], indent=4))
    else:
        _parse_os_cli_failure(folder)


@translate.command('model-to-idf')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--sim-par-json', '-sp', help='Full path to a honeybee energy '
              'SimulationParameter JSON that describes all of the settings for the '
              'simulation. If None default parameters will be generated.',
              default=None, show_default=True,
              type=click.Path(exists=True, file_okay=True, dir_okay=False,
                              resolve_path=True))
@click.option('--additional-str', '-a', help='Text string for additional lines that '
              'should be added to the IDF.', type=str, default='', show_default=True)
@click.option('--compact-schedules/--csv-schedules', ' /-c', help='Flag to note '
              'whether any ScheduleFixedIntervals in the model should be included '
              'in the IDF string as a Schedule:Compact or they should be written as '
              'CSV Schedule:File and placed in a directory next to the output-file.',
              default=True, show_default=True)
@click.option('--hvac-to-ideal-air/--hvac-check', ' /-h', help='Flag to note '
              'whether any detailed HVAC system templates should be converted to '
              'an equivalent IdealAirSystem upon export. If hvac-check is used'
              'and the Model contains detailed systems, a ValueError will '
              'be raised.', default=True, show_default=True)
@click.option('--geometry-ids/--geometry-names', ' /-gn', help='Flag to note whether a '
              'cleaned version of all geometry display names should be used instead '
              'of identifiers when translating the Model to IDF. Using this flag will '
              'affect all Rooms, Faces, Apertures, Doors, and Shades. It will '
              'generally result in more read-able names in the IDF but this means that '
              'it will not be easy to map the EnergyPlus results back to the original '
              'Honeybee Model. Cases of duplicate IDs resulting from non-unique names '
              'will be resolved by adding integers to the ends of the new IDs that are '
              'derived from the name.', default=True, show_default=True)
@click.option('--resource-ids/--resource-names', ' /-rn', help='Flag to note whether a '
              'cleaned version of all resource display names should be used instead '
              'of identifiers when translating the Model to IDF. Using this flag will '
              'affect all Materials, Constructions, ConstructionSets, Schedules, '
              'Loads, and ProgramTypes. It will generally result in more read-able '
              'names for the resources in the IDF. Cases of duplicate IDs resulting '
              'from non-unique names will be resolved by adding integers to the ends '
              'of the new IDs that are derived from the name.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_to_idf_cli(model_file, sim_par_json, additional_str, compact_schedules,
                     hvac_to_ideal_air, geometry_ids, resource_ids, output_file):
    """Translate a Model (HBJSON) file to a simplified IDF using direct-to-idf methods.

    The direct-to-idf methods are faster than those that translate the model
    to OSM but certain features like detailed HVAC systems and the Airflow Network
    are not supported.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        csv_schedules = not compact_schedules
        hvac_check = not hvac_to_ideal_air
        geo_names = not geometry_ids
        res_names = not resource_ids
        model_to_idf(
            model_file, sim_par_json, additional_str, csv_schedules,
            hvac_check, geo_names, res_names, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_idf(
    model_file, sim_par_json=None, additional_str='', csv_schedules=False,
    hvac_check=False, geometry_names=False, resource_names=False, output_file=None,
    compact_schedules=True, hvac_to_ideal_air=True, geometry_ids=True, resource_ids=True
):
    """Translate a Honeybee Model file to a simplified IDF using direct-to-idf methods.

    The direct-to-idf methods are faster than those that translate the model
    to OSM but certain features like detailed HVAC systems and the Airflow Network
    are not supported.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        sim_par_json: Full path to a honeybee energy SimulationParameter JSON that
            describes all of the settings for the simulation. If None, default
            parameters will be generated.
        additional_str: Text string for additional lines that should be added
            to the IDF.
        csv_schedules: Boolean to note whether any ScheduleFixedIntervals in the
            model should be included in the IDF string as a Schedule:Compact or
            they should be written as CSV Schedule:File and placed in a directory
            next to the output_file. (Default: False).
        hvac_check: Boolean to note whether any detailed HVAC system templates
            should be converted to an equivalent IdealAirSystem upon export.
            If hvac-check is used and the Model contains detailed systems, a
            ValueError will be raised. (Default: False).
        geometry_names: Boolean to note whether a cleaned version of all geometry
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Rooms, Faces,
            Apertures, Doors, and Shades. It will generally result in more read-able
            names in the OSM and IDF but this means that it will not be easy to map
            the EnergyPlus results back to the original Honeybee Model. Cases
            of duplicate IDs resulting from non-unique names will be resolved
            by adding integers to the ends of the new IDs that are derived from
            the name. (Default: False).
        resource_names: Boolean to note whether a cleaned version of all resource
            display names should be used instead of identifiers when translating
            the Model to OSM and IDF. Using this flag will affect all Materials,
            Constructions, ConstructionSets, Schedules, Loads, and ProgramTypes.
            It will generally result in more read-able names for the resources
            in the OSM and IDF. Cases of duplicate IDs resulting from non-unique
            names will be resolved by adding integers to the ends of the new IDs
            that are derived from the name. (Default: False).
        output_file: Optional IDF file to output the IDF string of the translation.
            By default this string will be returned from this method.
    """
    # load simulation parameters or generate default ones
    if sim_par_json is not None:
        with open(sim_par_json) as json_file:
            data = json.load(json_file)
        sim_par = SimulationParameter.from_dict(data)
    else:
        sim_par = SimulationParameter()
        sim_par.output.add_zone_energy_use()
        sim_par.output.add_hvac_energy_use()
        sim_par.output.add_electricity_generation()
        sim_par.output.reporting_frequency = 'Monthly'

    # re-serialize the Model to Python
    model = Model.from_file(model_file)

    # reset the IDs to be derived from the display_names if requested
    if geometry_names:
        model.reset_ids()
    if resource_names:
        model.properties.energy.reset_resource_ids()

    # set the schedule directory in case it is needed
    sch_directory = None
    if csv_schedules:
        sch_path = os.path.abspath(model_file) \
            if output_file is not None and 'stdout' in str(output_file) \
            else os.path.abspath(str(output_file))
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

    # create the strings for simulation parameters and model
    ver_str = energyplus_idf_version() if folders.energyplus_version \
        is not None else ''
    sim_par_str = sim_par.to_idf()
    hvac_to_ideal = not hvac_check
    model_str = model.to.idf(
        model, schedule_directory=sch_directory,
        use_ideal_air_equivalent=hvac_to_ideal)
    idf_str = '\n\n'.join([ver_str, sim_par_str, model_str, additional_str])

    # write out the IDF file
    if output_file is None:
        return idf_str
    else:
        output_file.write(idf_str)


@translate.command('model-to-gbxml')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--default-subfaces/--triangulate-subfaces', ' /-t',
              help='Flag to note whether sub-faces (including Apertures and Doors) '
              'should be triangulated if they have more than 4 sides (True) or whether '
              'they should be left as they are (False). This triangulation is '
              'necessary when exporting directly to EnergyPlus since it cannot accept '
              'sub-faces with more than 4 vertices.', default=True, show_default=True)
@click.option('--triangulate-non-planar/--permit-non-planar', ' /-np',
              help='Flag to note whether any non-planar orphaned geometry in the '
              'model should be triangulated upon export. This can be helpful because '
              'OpenStudio simply raises an error when it encounters non-planar '
              'geometry, which would hinder the ability to save gbXML files that are '
              'to be corrected in other software.', default=True, show_default=True)
@click.option('--minimal/--full-geometry', ' /-fg', help='Flag to note whether space '
              'boundaries and shell geometry should be included in the exported '
              'gbXML vs. just the minimal required non-manifold geometry.',
              default=True, show_default=True)
@click.option('--interior-face-type', '-ift', help='Text string for the type to be '
              'used for all interior floor faces. If unspecified, the interior types '
              'will be left as they are. Choose from: InteriorFloor, Ceiling.',
              type=str, default='', show_default=True)
@click.option('--ground-face-type', '-gft', help='Text string for the type to be '
              'used for all ground-contact floor faces. If unspecified, the ground '
              'types will be left as they are. Choose from: UndergroundSlab, '
              'SlabOnGrade, RaisedFloor.', type=str, default='', show_default=True)
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'exported directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional gbXML file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_to_gbxml_cli(
        model_file, osw_folder, default_subfaces, triangulate_non_planar, minimal,
        interior_face_type, ground_face_type, check_model, output_file):
    """Translate a Honeybee Model (HBJSON) to a gbXML file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        triangulate_subfaces = not default_subfaces
        permit_non_planar = not triangulate_non_planar
        full_geometry = not minimal
        bypass_check = not check_model
        model_to_gbxml(
            model_file, osw_folder, triangulate_subfaces, permit_non_planar,
            full_geometry, interior_face_type, ground_face_type, bypass_check,
            output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_gbxml(
    model_file, osw_folder=None, triangulate_subfaces=False,
    permit_non_planar=False, full_geometry=False,
    interior_face_type='', ground_face_type='', bypass_check=False, output_file=None,
    default_subfaces=True, triangulate_non_planar=True, minimal=True, check_model=True
):
    """Translate a Honeybee Model file to a gbXML file.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        osw_folder: Folder on this computer, into which the working files will
            be written. If None, it will be written into a temp folder in the
            default simulation folder.
        triangulate_subfaces: Boolean to note whether sub-faces (including
            Apertures and Doors) should be triangulated if they have more
            than 4 sides (True) or whether they should be left as they are (False).
            This triangulation is necessary when exporting directly to EnergyPlus
            since it cannot accept sub-faces with more than 4 vertices. (Default: False).
        permit_non_planar: Boolean to note whether any non-planar orphaned geometry
            in the model should be triangulated upon export. This can be helpful
            because OpenStudio simply raises an error when it encounters non-planar
            geometry, which would hinder the ability to save gbXML files that are
            to be corrected in other software. (Default: False).
        full_geometry: Boolean to note whether space boundaries and shell geometry
            should be included in the exported gbXML vs. just the minimal required
            non-manifold geometry. (Default: False).
        interior_face_type: Text string for the type to be used for all interior
            floor faces. If unspecified, the interior types will be left as they are.
            Choose from: InteriorFloor, Ceiling.
        ground_face_type: Text string for the type to be used for all ground-contact
            floor faces. If unspecified, the ground types will be left as they are.
            Choose from: UndergroundSlab, SlabOnGrade, RaisedFloor.
        bypass_check: Boolean to note whether the Model should be re-serialized
            to Python and checked before it is translated to .osm. The check is
            not needed if the model-json was exported directly from the
            honeybee-energy Python library. (Default: False).
        output_file: Optional gbXML file to output the string of the translation.
            By default it will be returned from this method.
    """
    # set the default folder if it's not specified
    out_path = None
    out_directory = os.path.join(
        hb_folders.default_simulation_folder, 'temp_translate')
    if output_file is None or output_file.endswith('-'):
        f_name = os.path.basename(model_file).lower()
        f_name = f_name.replace('.hbjson', '.xml').replace('.json', '.xml')
        out_path = os.path.join(out_directory, f_name)

    # run the Model re-serialization and check if specified
    if not bypass_check:
        tri_non_planar = not permit_non_planar
        model_file = measure_compatible_model_json(
            model_file, out_directory, simplify_window_cons=True,
            triangulate_sub_faces=triangulate_subfaces,
            triangulate_non_planar_orphaned=tri_non_planar)

    # Write the osw file and translate the model to gbXML
    file_contents = None
    out_f = out_path if output_file is None or output_file.endswith('-') else output_file
    osw = to_gbxml_osw(model_file, out_f, osw_folder)
    if not full_geometry and not (interior_face_type or ground_face_type):
        file_contents = _run_translation_osw(osw, out_path)
    else:
        _, idf = run_osw(osw, silent=True)
        if idf is not None and os.path.isfile(idf):
            if interior_face_type or ground_face_type:
                int_ft = interior_face_type if interior_face_type != '' else None
                gnd_ft = ground_face_type if ground_face_type != '' else None
                set_gbxml_floor_types(out_f, int_ft, gnd_ft)
            if full_geometry:
                hb_model = Model.from_hbjson(model_file)
                add_gbxml_space_boundaries(out_f, hb_model)
            if out_path is not None:  # load the JSON string to stdout
                with open(out_path) as json_file:
                    file_contents = json_file.read()
        else:
            _parse_os_cli_failure(osw_folder)

    # return the file contents if requested
    if file_contents is not None:
        if output_file is None:
            return file_contents
        else:
            print(file_contents)


@translate.command('model-to-trace-gbxml')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--single-window/--detailed-windows', ' /-fg', help='Flag to note '
              'whether all windows within walls should be converted to a single '
              'window with an area that matches the original geometry.',
              default=True, show_default=True)
@click.option('--rect-sub-distance', '-r', help='A number for the resolution at which '
              'non-rectangular Apertures will be subdivided into smaller rectangular '
              'units. This is required as TRACE 3D plus cannot model non-rectangular '
              'geometries. This can include the units of the distance (eg. 0.5ft) or, '
              'if no units are provided, the value will be interpreted in the '
              'honeybee model units.',
              type=str, default='0.15m', show_default=True)
@click.option('--frame-merge-distance', '-m', help='A number for the maximum distance '
              'between non-rectangular Apertures at which point the Apertures will be '
              'merged into a single rectangular geometry. This is often helpful when '
              'there are several triangular Apertures that together make a rectangle '
              'when they are merged across their frames. This can include the units '
              'of the distance (eg. 0.5ft) or, if no units are provided, the value '
              'will be interpreted in the honeybee model units',
              type=str, default='0.2m', show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional gbXML file to output the string '
              'of the translation. By default it printed out to stdout.', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_to_trace_gbxml_cli(
        model_file, single_window, rect_sub_distance, frame_merge_distance,
        osw_folder, output_file):
    """Translate a Honeybee Model (HBJSON) to a gbXML file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        detailed_windows = not single_window
        model_to_trace_gbxml(model_file, detailed_windows, rect_sub_distance,
                             frame_merge_distance, osw_folder, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_trace_gbxml(
    model_file, detailed_windows=False, rect_sub_distance='0.15m',
    frame_merge_distance='0.2m', osw_folder=None, output_file=None,
    single_window=True
):
    """Translate a Honeybee Model to a gbXML file that is compatible with TRACE 3D Plus.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        detailed_windows: A boolean for whether all windows within walls should be
            left as they are (True) or converted to a single window with an area
            that matches the original geometry (False). (Default: False).
        rect_sub_distance: A number for the resolution at which non-rectangular
            Apertures will be subdivided into smaller rectangular units. This is
            required as TRACE 3D plus cannot model non-rectangular geometries.
            This can include the units of the distance (eg. 0.5ft) or, if no units
            are provided, the value will be interpreted in the honeybee model
            units. (Default: 0.15m).
        frame_merge_distance: A number for the maximum distance between non-rectangular
            Apertures at which point the Apertures will be merged into a single
            rectangular geometry. This is often helpful when there are several
            triangular Apertures that together make a rectangle when they are
            merged across their frames. This can include the units of the
            distance (eg. 0.5ft) or, if no units are provided, the value will
            be interpreted in the honeybee model units. (Default: 0.2m).
        osw_folder: Folder on this computer, into which the working files will
            be written. If None, it will be written into a temp folder in the
            default simulation folder.
        output_file: Optional gbXML file to output the string of the translation.
            By default it will be returned from this method.
    """
    # set the default folder if it's not specified
    out_path = None
    out_directory = os.path.join(
        hb_folders.default_simulation_folder, 'temp_translate')
    if output_file is None or output_file.endswith('-'):
        f_name = os.path.basename(model_file).lower()
        f_name = f_name.replace('.hbjson', '.xml').replace('.json', '.xml')
        out_path = os.path.join(out_directory, f_name)

    # run the Model re-serialization and check if specified
    single_window = not detailed_windows
    model_file = trace_compatible_model_json(
        model_file, out_directory, single_window,
        rect_sub_distance, frame_merge_distance)

    # Write the osw file and translate the model to gbXML
    out_f = out_path if output_file is None or output_file.endswith('-') else output_file
    osw = to_gbxml_osw(model_file, out_f, osw_folder)
    file_contents = _run_translation_osw(osw, out_path)

    # return the file contents if requested
    if file_contents is not None:
        if output_file is None:
            return file_contents
        else:
            print(file_contents)


@translate.command('model-to-sdd')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--check-model/--bypass-check', ' /-bc', help='Flag to note whether the '
              'Model should be re-serialized to Python and checked before it is '
              'translated to .osm. The check is not needed if the model-json was '
              'exported directly from the honeybee-energy Python library.',
              default=True, show_default=True)
@click.option('--output-file', '-f', help='Optional SDD file to output the string '
              'of the translation. By default it printed out to stdout.', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_to_sdd_cli(model_file, osw_folder, check_model, output_file):
    """Translate a Honeybee Model file to a SDD file.

    \b
    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
    """
    try:
        bypass_check = not check_model
        model_to_sdd(model_file, osw_folder, bypass_check, output_file)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def model_to_sdd(model_file, osw_folder=None, bypass_check=False, output_file=None):
    """Translate a Honeybee Model file to a SDD file.

    Args:
        model_file: Full path to a Honeybee Model file (HBJSON or HBpkl).
        osw_folder: Folder on this computer, into which the working files will
            be written. If None, it will be written into a temp folder in the
            default simulation folder.
        bypass_check: Boolean to note whether the Model should be re-serialized
            to Python and checked before it is translated to .osm. The check is
            not needed if the model-json was exported directly from the
            honeybee-energy Python library. (Default: False).
        output_file: Optional SDD file to output the string of the translation.
            By default it will be returned from this method.
    """
    # set the default folder if it's not specified
    out_path = None
    out_directory = os.path.join(
        hb_folders.default_simulation_folder, 'temp_translate')
    if output_file is None or output_file.endswith('-'):
        f_name = os.path.basename(model_file).lower()
        f_name = f_name.replace('.hbjson', '.xml').replace('.json', '.xml')
        out_path = os.path.join(out_directory, f_name)

    # run the Model re-serialization and check if specified
    if not bypass_check:
        model_file = measure_compatible_model_json(
            model_file, out_directory, simplify_window_cons=True,
            triangulate_sub_faces=True)

    # Write the osw file and translate the model to SDD
    out_f = out_path if output_file is None or output_file.endswith('-') \
        else output_file
    osw = to_sdd_osw(model_file, out_f, osw_folder)
    file_contents = _run_translation_osw(osw, out_path)

    # return the file contents if requested
    if file_contents is not None:
        if output_file is None:
            return file_contents
        else:
            print(file_contents)


@translate.command('model-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_osm(osm_file, osw_folder, output_file):
    """Translate a OpenStudio Model (OSM) to a Honeybee Model (HBJSON).

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(osm_file).lower().replace('.osm', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_osm_osw(osm_file, out_f, osw_folder)
        file_contents = _run_translation_osw(osw, out_path)

        # return the file contents if requested
        if file_contents is not None:
            if output_file is None:
                return file_contents
            else:
                print(file_contents)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-from-idf')
@click.argument('idf-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_idf(idf_file, osw_folder, output_file):
    """Translate an EnergyPlus Model (IDF) to a Honeybee Model (HBJSON).

    \b
    Args:
        idf_file: Path to an EnergyPlus Model (IDF) file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(idf_file).lower().replace('.idf', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_idf_osw(idf_file, out_f, osw_folder)
        # run the measure to translate the model JSON to an openstudio measure
        _, idf = run_osw(osw, silent=True)
        if idf is not None and os.path.isfile(idf):
            if out_path is not None:  # load the JSON string to stdout
                with open(out_path) as json_file:
                    print(json_file.read())
        else:
            # check the version of the IDF; most of the time, this is the issue
            ver_regex = r'[V|v][E|e][R|r][S|s][I|i][O|o][N|n],\s*(\d*\.\d*)[;|.]'
            ver_pattern = re.compile(ver_regex)
            with open(idf_file, 'r') as mf:
                ver_val = re.search(ver_pattern, mf.read())
            if ver_val is not None:
                ver_tup = tuple(int(v) for v in ver_val.groups()[0].split('.'))
                if folders.energyplus_version[:2] != ver_tup:
                    msg = 'The IDF is from EnergyPlus version {}.\nThis must be ' \
                        'changed to {} with the IDFVersionUpdater\nin order to import ' \
                        'it with this Ladybug Tools installation.'.format(
                            '.'.join((str(v) for v in ver_tup)),
                            '.'.join((str(v) for v in folders.energyplus_version[:2]))
                        )
                    raise ValueError(msg)
            _parse_os_cli_failure(os.path.dirname(osw))
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-from-gbxml')
@click.argument('gbxml-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional HBJSON file to output the string '
              'of the translation. By default it printed out to stdout', default='-',
              type=click.Path(file_okay=True, dir_okay=False, resolve_path=True))
def model_from_gbxml(gbxml_file, osw_folder, output_file):
    """Translate a gbXML to a Honeybee Model (HBJSON).

    \b
    Args:
        gbxml_file: Path to a gbXML file.
    """
    try:
        # set the default folder if it's not specified
        out_path = None
        if output_file.endswith('-'):
            out_directory = os.path.join(
                hb_folders.default_simulation_folder, 'temp_translate')
            f_name = os.path.basename(gbxml_file).lower()
            f_name = f_name.replace('.gbxml', '.hbjson').replace('.xml', '.hbjson')
            out_path = os.path.join(out_directory, f_name)

        # Write the osw file and translate the model to HBJSON
        out_f = out_path if output_file.endswith('-') else output_file
        osw = from_gbxml_osw(gbxml_file, out_f, osw_folder)
        file_contents = _run_translation_osw(osw, out_path)

        # return the file contents if requested
        if file_contents is not None:
            if output_file is None:
                return file_contents
            else:
                print(file_contents)
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('constructions-to-idf')
@click.argument('construction-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF string '
              'of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_to_idf(construction_json, output_file):
    """Translate a Construction JSON file to an IDF using direct-to-idf translators.

    \b
    Args:
        construction_json: Full path to a Construction JSON file. This file should
            either be an array of non-abridged Constructions or a dictionary where
            the values are non-abridged Constructions.
    """
    try:
        # re-serialize the Constructions to Python
        with open(construction_json) as json_file:
            data = json.load(json_file)
        constr_list = data.values() if isinstance(data, dict) else data
        constr_objs = [dict_to_construction(constr) for constr in constr_list]
        mat_objs = set()
        for constr in constr_objs:
            try:
                for mat in constr.materials:
                    mat_objs.add(mat)
                if constr.has_frame:
                    mat_objs.add(constr.frame)
                if constr.has_shade:
                    if constr.is_switchable_glazing:
                        mat_objs.add(constr.switched_glass_material)
            except AttributeError:  # not a construction with materials
                pass

        # create the IDF strings
        idf_str_list = []
        idf_str_list.append('!-   ============== MATERIALS ==============\n')
        idf_str_list.extend([mat.to_idf() for mat in mat_objs])
        idf_str_list.append('!-   ============ CONSTRUCTIONS ============\n')
        idf_str_list.extend([constr.to_idf() for constr in constr_objs])
        idf_str = '\n\n'.join(idf_str_list)

        # write out the IDF file
        output_file.write(idf_str)
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('constructions-from-idf')
@click.argument('construction-idf', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_from_idf(construction_idf, indent, output_file):
    """Translate a Construction IDF file to a honeybee JSON as an array of constructions.

    \b
    Args:
        construction_idf: Full path to a Construction IDF file. Only the constructions
            and materials in this file will be extracted.
    """
    try:
        # re-serialize the Constructions to Python
        opaque_constrs = OpaqueConstruction.extract_all_from_idf_file(construction_idf)
        win_constrs = WindowConstruction.extract_all_from_idf_file(construction_idf)

        # create the honeybee dictionaries
        hb_obj_list = []
        for constr in opaque_constrs[0]:
            hb_obj_list.append(constr.to_dict())
        for constr in win_constrs[0]:
            hb_obj_list.append(constr.to_dict())

        # write out the JSON file
        output_file.write(json.dumps(hb_obj_list, indent=indent))
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('materials-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def materials_from_osm(osm_file, indent, osw_folder, output_file):
    """Translate all Materials in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    materials to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the material dictionaries from the model dictionary
        out_dict = {}
        for mat in model_dict['properties']['energy']['materials']:
            out_dict[mat['identifier']] = mat
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Material translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('constructions-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the materials-from-osm command will be used to separately '
              'translate all of the materials from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def constructions_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all Constructions in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    constructions to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the construction dictionaries from the model dictionary
        out_dict = {}
        if not full:  # objects are already abridged and good to go
            for con in model_dict['properties']['energy']['constructions']:
                out_dict[con['identifier']] = con
            output_file.write(json.dumps(out_dict, indent=indent))
        else:  # rebuild the full objects to write them as full
            _, constructions, _, _, _, _, _, _ = \
                ModelEnergyProperties.load_properties_from_dict(
                    model_dict, skip_invalid=True)
            for con in constructions.values():
                out_dict[con.identifier] = con.to_dict()
        # write the resulting JSON
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Construction translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('construction-sets-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the constructions-from-osm command will be used to separately '
              'translate all of the constructions from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def construction_sets_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all ConstructionSets in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    constructions to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the construction set dictionaries from the model dictionary
        out_dict = {}
        if not full:  # objects are already abridged and good to go
            for c_set in model_dict['properties']['energy']['construction_sets']:
                out_dict[c_set['identifier']] = c_set
            output_file.write(json.dumps(out_dict, indent=indent))
        else:  # rebuild the full objects to write them as full
            _, _, construction_sets, _, _, _, _, _ = \
                ModelEnergyProperties.load_properties_from_dict(
                    model_dict, skip_invalid=True)
            for c_set in construction_sets.values():
                out_dict[c_set.identifier] = c_set.to_dict()
        # write the resulting JSON
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('ConstructionSet translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-to-idf')
@click.argument('schedule-json', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--output-file', '-f', help='Optional IDF file to output the IDF '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_to_idf(schedule_json, output_file):
    """Translate a Schedule JSON file to an IDF using direct-to-idf translators.

    \b
    Args:
        schedule_json: Full path to a Schedule JSON file. This file should
            either be an array of non-abridged Schedules or a dictionary where
            the values are non-abridged Schedules.
    """
    try:
        # re-serialize the Schedule to Python
        with open(schedule_json) as json_file:
            data = json.load(json_file)
        sch_list = data.values() if isinstance(data, dict) else data
        sch_objs = [dict_to_schedule(sch) for sch in sch_list]
        type_objs = set()
        for sch in sch_objs:
            type_objs.add(sch.schedule_type_limit)

        # set the schedule directory in case it is needed
        sch_path = os.path.abspath(schedule_json) if 'stdout' in str(output_file) \
            else os.path.abspath(str(output_file))
        sch_directory = os.path.join(os.path.split(sch_path)[0], 'schedules')

        # create the IDF strings
        sched_strs = []
        used_day_sched_ids = []
        for sched in sch_objs:
            try:  # ScheduleRuleset
                year_schedule, week_schedules = sched.to_idf()
                if week_schedules is None:  # ScheduleConstant
                    sched_strs.append(year_schedule)
                else:  # ScheduleYear
                    # check that day schedules aren't referenced by other schedules
                    day_scheds = []
                    for day in sched.day_schedules:
                        if day.identifier not in used_day_sched_ids:
                            day_scheds.append(day.to_idf(sched.schedule_type_limit))
                            used_day_sched_ids.append(day.identifier)
                    sched_strs.extend([year_schedule] + week_schedules + day_scheds)
            except AttributeError:  # ScheduleFixedInterval
                sched_strs.append(sched.to_idf(sch_directory))
        idf_str_list = []
        idf_str_list.append('!-   ========= SCHEDULE TYPE LIMITS =========\n')
        idf_str_list.extend([type_limit.to_idf() for type_limit in type_objs])
        idf_str_list.append('!-   ============== SCHEDULES ==============\n')
        idf_str_list.extend(sched_strs)
        idf_str = '\n\n'.join(idf_str_list)

        # write out the IDF file
        output_file.write(idf_str)
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-from-idf')
@click.argument('schedule-idf', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--output-file', '-f', help='Optional JSON file to output the JSON '
              'string of the translation. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_from_idf(schedule_idf, indent, output_file):
    """Translate a schedule IDF file to a honeybee JSON as an array of schedules.

    \b
    Args:
        schedule_idf: Full path to a Schedule IDF file. Only the schedules
            and schedule type limits in this file will be extracted.
    """
    try:
        # re-serialize the schedules to Python
        schedules = ScheduleRuleset.extract_all_from_idf_file(schedule_idf)
        # create the honeybee dictionaries
        hb_obj_list = [sch.to_dict() for sch in schedules]
        # write out the JSON file
        output_file.write(json.dumps(hb_obj_list, indent=indent))
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedule-type-limits-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedule_type_limits_from_osm(osm_file, indent, osw_folder, output_file):
    """Translate all ScheduleTypeLimits in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    type limits to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the material dictionaries from the model dictionary
        out_dict = {}
        for stl in model_dict['properties']['energy']['schedule_type_limits']:
            out_dict[stl['identifier']] = stl
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('ScheduleTypeLimit translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('schedules-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the schedule-type-limits-from-osm command will be used to '
              'separately translate all of the type limits from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def schedules_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all Schedules in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    schedules to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the construction dictionaries from the model dictionary
        out_dict = {}
        if not full:  # objects are already abridged and good to go
            for sch in model_dict['properties']['energy']['schedules']:
                out_dict[sch['identifier']] = sch
            output_file.write(json.dumps(out_dict, indent=indent))
        else:  # rebuild the full objects to write them as full
            _, _, _, _, schedules, _, _, _ = \
                ModelEnergyProperties.load_properties_from_dict(
                    model_dict, skip_invalid=True)
            for sch in schedules.values():
                out_dict[sch.identifier] = sch.to_dict()
        # write the resulting JSON
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Schedule translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('programs-from-osm')
@click.argument('osm-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--full/--abridged', ' /-a', help='Flag to note whether the objects '
              'should be translated as an abridged specification instead of a '
              'specification that fully describes the object. This option should be '
              'used when the schedules-from-osm command will be used to separately '
              'translate all of the schedules from the OSM.',
              default=True, show_default=True)
@click.option('--indent', '-i', help='Optional integer to specify the indentation in '
              'the output JSON file. Specifying an value here can produce more read-able'
              ' JSONs.', type=int, default=None, show_default=True)
@click.option('--osw-folder', '-osw', help='Folder on this computer, into which the '
              'working files will be written. If None, it will be written into the a '
              'temp folder in the default simulation folder.', default=None,
              type=click.Path(file_okay=False, dir_okay=True, resolve_path=True))
@click.option('--output-file', '-f', help='Optional JSON file to output the string '
              'of the translation. By default it printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def programs_from_osm(osm_file, full, indent, osw_folder, output_file):
    """Translate all ProgramTypes in an OpenStudio Model (OSM) to a Honeybee JSON.

    The resulting JSON can be written into a user standards folder to add the
    programs to a users standards library.

    \b
    Args:
        osm_file: Path to a OpenStudio Model (OSM) file.
    """
    try:
        # translate the OSM to a HBJSON
        model_dict = _translate_osm_to_hbjson(osm_file, osw_folder)
        # extract the construction dictionaries from the model dictionary
        out_dict = {}
        if not full:  # objects are already abridged and good to go
            for prog in model_dict['properties']['energy']['program_types']:
                out_dict[prog['identifier']] = prog
            output_file.write(json.dumps(out_dict, indent=indent))
        else:  # rebuild the full objects to write them as full
            _, _, _, _, _, program_types, _, _ = \
                ModelEnergyProperties.load_properties_from_dict(
                    model_dict, skip_invalid=True)
            for prog in program_types.values():
                out_dict[prog.identifier] = prog.to_dict()
        # write the resulting JSON
        output_file.write(json.dumps(out_dict, indent=indent))
    except Exception as e:
        _logger.exception('Program translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-occ-schedules')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--threshold', '-t', help='A number between 0 and 1 for the threshold '
              'at and above which a schedule value is considered occupied.',
              type=float, default=0.1, show_default=True)
@click.option('--period', '-p', help='An AnalysisPeriod string to dictate '
              'the start and end of the exported occupancy values '
              '(eg. "6/21 to 9/21 between 0 and 23 @1"). Note that the timestep '
              'of the period will determine the timestep of output values. If '
              'unspecified, the values will be annual.', default=None, type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON of '
              'occupancy values. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_occ_schedules(model_file, threshold, period, output_file):
    """Translate a Model's occupancy schedules into a JSON of 0/1 values.

    \b
    Args:
        model_file: Full path to a Model JSON or Pkl file.
    """
    try:
        # re-serialize the Model
        model = Model.from_file(model_file)

        # loop through the rooms and collect all unique occupancy schedules
        scheds, room_occupancy = [], {}
        for room in model.rooms:
            people = room.properties.energy.people
            if people is not None:
                model.properties.energy._check_and_add_schedule(
                    people.occupancy_schedule, scheds)
                room_occupancy[room.identifier] = people.occupancy_schedule.identifier
            else:
                room_occupancy[room.identifier] = None

        # process the run period if it is supplied
        if period is not None and period != '' and period != 'None':
            a_per = AnalysisPeriod.from_string(period)
        else:
            a_per = AnalysisPeriod()

        # convert occupancy schedules to lists of 0/1 values
        schedules = {}
        for sch in scheds:
            sch_data = sch.data_collection() if isinstance(sch, ScheduleRuleset) \
                else sch.data_collection
            if not a_per.is_annual:
                sch_data = sch_data.filter_by_analysis_period(a_per)
            values = []
            for val in sch_data.values:
                is_occ = 0 if val <= threshold else 1
                values.append(is_occ)
            schedules[sch.identifier] = values

        # write out the JSON file
        occ_dict = {'schedules': schedules, 'room_occupancy': room_occupancy}
        output_file.write(json.dumps(occ_dict))
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


@translate.command('model-transmittance-schedules')
@click.argument('model-file', type=click.Path(
    exists=True, file_okay=True, dir_okay=False, resolve_path=True))
@click.option('--period', '-p', help='An AnalysisPeriod string to dictate '
              'the start and end of the exported occupancy values '
              '(eg. "6/21 to 9/21 between 0 and 23 @1"). Note that the timestep '
              'of the period will determine the timestep of output values. If '
              'unspecified, the values will be annual.', default=None, type=str)
@click.option('--output-file', '-f', help='Optional file to output the JSON of '
              'occupancy values. By default this will be printed out to stdout',
              type=click.File('w'), default='-', show_default=True)
def model_trans_schedules(model_file, period, output_file):
    """Translate a Model's shade transmittance schedules into a JSON of fractional vals.

    \b
    Args:
        model_file: Full path to a Model JSON or Pkl file.
    """
    try:
        # re-serialize the Model
        model = Model.from_file(model_file)

        # loop through the rooms and collect all unique occupancy schedules
        scheds = []
        for shade in model.shades:
            t_sch = shade.properties.energy.transmittance_schedule
            if t_sch is not None:
                model.properties.energy._check_and_add_schedule(t_sch, scheds)

        # process the run period if it is supplied
        if period is not None and period != '' and period != 'None':
            a_per = AnalysisPeriod.from_string(period)
        else:
            a_per = AnalysisPeriod()

        # convert occupancy schedules to lists of 0/1 values
        schedules = {}
        for sch in scheds:
            sch_data = sch.data_collection() if isinstance(sch, ScheduleRuleset) \
                else sch.data_collection
            if not a_per.is_annual:
                sch_data = sch_data.filter_by_analysis_period(a_per)
            schedules[clean_rad_string(sch.identifier)] = sch_data.values

        # write out the JSON file
        output_file.write(json.dumps(schedules))
    except Exception as e:
        _logger.exception('Model translation failed.\n{}'.format(e))
        sys.exit(1)
    else:
        sys.exit(0)


def _run_translation_osw(osw, out_path):
    """Generic function used by all import methods that run OpenStudio CLI."""
    # run the measure to translate the model JSON to an openstudio measure
    _, idf = run_osw(osw, silent=True)
    if idf is not None and os.path.isfile(idf):
        if out_path is not None:  # load the JSON string to stdout
            with open(out_path) as json_file:
                return json_file.read()
    else:
        _parse_os_cli_failure(os.path.dirname(osw))


def _translate_osm_to_hbjson(osm_file, osw_folder):
    """Translate an OSM to a HBJSON for use in resource extraction commands."""
    # come up with a temporary path to write the HBJSON
    out_directory = os.path.join(
        hb_folders.default_simulation_folder, 'temp_translate')
    f_name = os.path.basename(osm_file).lower().replace('.osm', '.hbjson')
    out_path = os.path.join(out_directory, f_name)
    # run the OSW to translate the OSM to HBJSON
    osw = from_osm_osw(osm_file, out_path, osw_folder)
    # load the resulting HBJSON to a dictionary and return it
    _, idf = run_osw(osw, silent=True)
    if idf is not None and os.path.isfile(idf):
        with open(out_path) as json_file:
            return json.load(json_file)
    else:
        _parse_os_cli_failure(os.path.dirname(osw))
