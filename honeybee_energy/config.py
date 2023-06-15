"""Honeybee_energy configurations.

Import this into every module where access configurations are needed.

Usage:

.. code-block:: python

    from honeybee_energy.config import folders
    print(folders.energyplus_path)
    print(folders.openstudio_path)
    folders.energyplus_path = "C:/EnergyPlusV9-0-1"
"""
import ladybug.config as lb_config
import honeybee_standards

import os
import platform
import subprocess
import json
import pkgutil


class Folders(object):
    """Honeybee_energy folders.

    Args:
        config_file: The path to the config.json file from which folders are loaded.
            If None, the config.json module included in this package will be used.
            Default: None.
        mute: If False, the paths to the various folders will be printed as they
            are found. If True, no printing will occur upon initialization of this
            class. Default: True.

    Properties:
        * openstudio_path
        * openstudio_exe
        * openstudio_version
        * openstudio_version_str
        * openstudio_csharp_path
        * openstudio_lib_path
        * energyplus_path
        * energyplus_exe
        * energyplus_version
        * energyplus_version_str
        * energyplus_idd_path
        * lbt_measures_path
        * openstudio_results_measure_path
        * view_data_measure_path
        * inject_idf_measure_path
        * honeybee_openstudio_gem_path
        * honeybee_adapter_path
        * ironbug_path
        * ironbug_exe
        * ironbug_version
        * ironbug_version_str
        * standards_data_folder
        * construction_lib
        * constructionset_lib
        * schedule_lib
        * programtype_lib
        * defaults_file
        * standards_extension_folders
        * config_file
        * mute
    """

    def __init__(self, config_file=None, mute=True):
        self.mute = bool(mute)  # set the mute value
        self.config_file = config_file  # load paths from the config JSON file

    @property
    def openstudio_path(self):
        """Get or set the path to OpenStudio installation folder.

        This is the "bin" directory for OpenStudio installation (the one that
        contains the openstudio executable file).
        """
        return self._openstudio_path

    @openstudio_path.setter
    def openstudio_path(self, path):
        if not path:  # check the default installation location
            path = self._find_openstudio_folder()
        exe_name = 'openstudio.exe' if os.name == 'nt' else 'openstudio'
        os_exe_file = os.path.join(path, exe_name) if path is not None else None

        if path:  # check that the OpenStudio executable exists in the path
            assert os.path.isfile(os_exe_file), \
                '{} is not a valid path to an openstudio installation.'.format(path)
            # see if the CSharp folder is installed
            csharp_path = os.path.join(os.path.dirname(path), 'CSharp', 'openstudio')
            self._openstudio_csharp_path = csharp_path \
                if os.path.isdir(csharp_path) else None
            # see if the lib path is installed
            lib_path = os.path.join(os.path.dirname(path), 'lib')
            self._openstudio_lib_path = lib_path \
                if os.path.isdir(lib_path) else None
        else:
            self._openstudio_csharp_path = None
            self._openstudio_lib_path = None

        # set the openstudio_path
        self._openstudio_path = path
        self._openstudio_exe = os_exe_file
        self._openstudio_version = None
        self._openstudio_version_str = None
        if path and not self.mute:
            print("Path to OpenStudio is set to: %s" % path)

    @property
    def openstudio_exe(self):
        """Get the path to the executable openstudio file."""
        return self._openstudio_exe

    @property
    def openstudio_version(self):
        """Get a tuple for the version of openstudio (eg. (3, 0, 1)).

        This will be None if the version could not be sensed or if no OpenStudio
        installation was found.
        """
        if self._openstudio_exe and self._openstudio_version_str is None:
            self._openstudio_version_from_cli()
        return self._openstudio_version

    @property
    def openstudio_version_str(self):
        """Get text for the full version of openstudio (eg. "3.0.1+09b7c8a554").

        This will be None if the version could not be sensed or if no OpenStudio
        installation was found.
        """
        if self._openstudio_exe and self._openstudio_version_str is None:
            self._openstudio_version_from_cli()
        return self._openstudio_version_str

    @property
    def openstudio_csharp_path(self):
        """Get the path to the OpenStudio CSharp folder if it exists."""
        if self._openstudio_csharp_path is None and self._ironbug_path is not None:
            os_dll = os.path.join(self._ironbug_path, 'OpenStudio.dll')
            if os.path.isfile(os_dll):
                return self._ironbug_path
        return self._openstudio_csharp_path

    @property
    def openstudio_lib_path(self):
        """Get the path to the OpenStudio lib folder if it exists."""
        return self._openstudio_lib_path

    @property
    def energyplus_path(self):
        """Get or set the path to EnergyPlus installation folder."""
        return self._energyplus_path

    @energyplus_path.setter
    def energyplus_path(self, path):
        if not path:  # check the default installation location
            path = self._find_energyplus_folder()
        exe_name = 'energyplus.exe' if os.name == 'nt' else 'energyplus'
        ep_exe_file = os.path.join(path, exe_name) if path is not None else None

        if path:  # check that the Energyplus executable exists in the installation
            assert os.path.isfile(ep_exe_file), \
                '{} is not a valid path to an energyplus installation.'.format(path)

        # set the energyplus_path
        self._energyplus_path = path
        self._energyplus_exe = ep_exe_file
        self._energyplus_version = None
        self._energyplus_version_str = None
        self._energyplus_idd_path = None
        if path and not self.mute:
            print("Path to EnergyPlus is set to: %s" % self._energyplus_path)

    @property
    def energyplus_exe(self):
        """Get the path to the executable energyplus file."""
        return self._energyplus_exe

    @property
    def energyplus_version(self):
        """Get a tuple for the version of energyplus (eg. (9, 3, 0)).

        This will be None if the version could not be sensed or if no EnergyPlus
        installation was found.
        """
        if self._energyplus_exe and self._energyplus_version_str is None:
            self._energyplus_version_from_cli()
        return self._energyplus_version

    @property
    def energyplus_version_str(self):
        """Get text for the full version of energyplus (eg. "9.3.0-baff08990c").

        This will be None if the version could not be sensed or if no EnergyPlus
        installation was found.
        """
        if self._energyplus_exe and self._energyplus_version_str is None:
            self._energyplus_version_from_cli()
        return self._energyplus_version_str

    @property
    def energyplus_idd_path(self):
        if self._energyplus_exe and self._energyplus_idd_path is None:
            idd_path = os.path.join(self.energyplus_path, 'Energy+.idd')
            if os.path.isfile(idd_path):
                self._energyplus_idd_path = idd_path
        return self._energyplus_idd_path

    @property
    def lbt_measures_path(self):
        """Get or set the path to the the measures that ship with with Ladybug Tools.

        This folder must have the following sub-folders in order to be valid:

        * openstudio_results - Measure to display a clean energy use HTML report.
        * view_data - Measure to color geometry with simulation results.
        """
        return self._lbt_measures_path

    @lbt_measures_path.setter
    def lbt_measures_path(self, path):
        if not path:  # check the default locations of the lbt_measures
            path = self._find_lbt_measures_path()

        # check that the library's sub-folders exist
        self._openstudio_results_measure_path = None
        self._view_data_measure_path = None
        self._inject_idf_measure_path = None
        if path:
            result_mea = os.path.join(path, 'openstudio_results')
            view_mea = os.path.join(path, 'view_data')
            idf_mea = os.path.join(path, 'inject_idf')
            if os.path.isdir(result_mea):
                self._openstudio_results_measure_path = result_mea
            if os.path.isdir(view_mea):
                self._view_data_measure_path = view_mea
            if os.path.isdir(idf_mea):
                self._inject_idf_measure_path = idf_mea

        # set the lbt_measures_path
        self._lbt_measures_path = path
        if path and not self.mute:
            print('Path to the lbt_measures is set to: '
                  '{}'.format(self._lbt_measures_path))

    @property
    def openstudio_results_measure_path(self):
        """Get the path to the measure that displays a clean energy use HTML report."""
        return self._openstudio_results_measure_path

    @property
    def view_data_measure_path(self):
        """Get the path to the measure that colors geometry with simulation results."""
        return self._view_data_measure_path

    @property
    def inject_idf_measure_path(self):
        """Get the path to the measure that injects IDF text."""
        return self._inject_idf_measure_path

    @property
    def honeybee_openstudio_gem_path(self):
        """Get or set the path to the honeybee_openstudio_gem.

        This gem contains libraries and measures for translating between Honeybee
        JSON schema and OpenStudio Model schema (OSM).
        This folder must have the following sub-folders in order to be valid:

        * honeybee - Ruby library with modules for model translation to OpenStudio.
        * measures - folder with the actual measures that run the translation.
        * files - folder containing the adapter and other supporting files.
        """
        return self._honeybee_openstudio_gem_path

    @honeybee_openstudio_gem_path.setter
    def honeybee_openstudio_gem_path(self, path):
        if not path:  # check the default locations of the honeybee_openstudio_gem
            path = self._find_honeybee_openstudio_gem_path()

        # check that the library's sub-folders exist
        self._honeybee_adapter_path = None
        if path:
            assert os.path.isdir(os.path.join(path, 'measures')), \
                '{} lacks a "measures" folder.'.format(path)
            assert os.path.isdir(os.path.join(path, 'files')), \
                '{} lacks a "files" folder.'.format(path)
            adapter = os.path.join(path, 'files', 'honeybee_adapter.rb')
            self._honeybee_adapter_path = adapter if os.path.isfile(adapter) else None

        # set the honeybee_openstudio_gem_path
        self._honeybee_openstudio_gem_path = path
        if path and not self.mute:
            print('Path to the honeybee_openstudio_gem is set to: '
                  '{}'.format(self._honeybee_openstudio_gem_path))

    @property
    def honeybee_adapter_path(self):
        """Get the path to the honeybee adapter.

        This adapter file is used to report the EnergyPlus simulation progress
        when running simulations using the OpenStudio CLI.
        """
        return self._honeybee_adapter_path

    @property
    def ironbug_path(self):
        """Get or set the path to an Ironbug installation folder."""
        return self._ironbug_path

    @ironbug_path.setter
    def ironbug_path(self, path):
        if not path:  # check the default installation location
            path = self._find_ironbug_path_folder()
        exe_name = 'Ironbug.Console.exe' if os.name == 'nt' else 'Ironbug.Console'
        ib_exe_file = os.path.join(path, exe_name) if path is not None else None

        if path:  # check that the Ironbug executable exists in the installation
            assert os.path.isfile(ib_exe_file), \
                '{} is not a valid path to an Ironbug installation.'.format(path)

        # set the ironbug_path
        self._ironbug_path = path
        self._ironbug_exe = ib_exe_file
        self._ironbug_version = None
        self._ironbug_version_str = None
        if path and not self.mute:
            print("Path to IronBug is set to: %s" % self._ironbug_path)

    @property
    def ironbug_exe(self):
        """Get the path to the executable Ironbug console file."""
        return self._ironbug_exe

    @property
    def ironbug_version(self):
        """Get a tuple for the version of Ironbug (eg. (1, 4, 3, 0)).

        This will be None if the version could not be sensed or if no Ironbug
        installation was found.
        """
        if self._ironbug_exe and self._ironbug_version_str is None:
            self._ironbug_version_from_cli()
        return self._ironbug_version

    @property
    def ironbug_version_str(self):
        """Get text for the full version of Ironbug (eg. "v1.4.3.0 (Jan 17, 2023)").

        This will be None if the version could not be sensed or if no Ironbug
        installation was found.
        """
        if self._ironbug_exe and self._ironbug_version_str is None:
            self._ironbug_version_from_cli()
        return self._ironbug_version_str

    @property
    def standards_data_folder(self):
        """Get or set the path to the library of standards loaded to honeybee_energy.lib.

        This folder must have the following sub-folders in order to be valid:

        * constructions - folder with IDF files for materials + constructions.
        * constructionsets - folder with JSON files of abridged ConstructionSets.
        * schedules - folder with IDF files for schedules.
        * programtypes - folder with JSON files of abridged ProgramTypes.
        """
        return self._standards_data_folder

    @standards_data_folder.setter
    def standards_data_folder(self, path):
        if not path:  # check the default locations of the template library
            path = self._find_standards_data_folder()

        # gather all of the sub folders underneath the master folder
        self._construction_lib, self._constructionset_lib, self._schedule_lib, \
            self._programtype_lib = self._check_standards_folder(path)

        # set the standards_data_folder
        self._standards_data_folder = path
        if path and not self.mute:
            print('Path to the standards_data_folder is set to: '
                  '{}'.format(self._standards_data_folder))

    @property
    def standards_extension_folders(self):
        """Get or set an array of paths to standards extensions loaded to the lib.

        Each extension folder folder must have the following sub-folders:

        * constructions - folder with honeybee JSON files for materials + constructions.
            It should have the following 4 JSON files:
            opaque_material, opaque_construction, window_material, window_construction.
        * constructionsets - folder with honeybee JSON files of ConstructionSets.
        * schedules - folder with honeybee JSON files for schedules.
        * programtypes - folder with honeybee JSON files of ProgramTypes.
        """
        return tuple(self._standards_extension_folders)

    @standards_extension_folders.setter
    def standards_extension_folders(self, folders):
        if not folders:  # check the default locations
            folders = self._find_standards_extension_folders()

        # check that any extensions have the proper sub-folders
        for path in folders:
            self._check_standards_folder(path)
            if not self.mute:
                print('Standards extension folder found: {}'.format(path))

        # set the standards_data_folder
        self._standards_extension_folders = folders

    @property
    def construction_lib(self):
        """Get the path to the construction library in the standards_data_folder."""
        return self._construction_lib

    @property
    def constructionset_lib(self):
        """Get the path to the constructionset library in the standards_data_folder."""
        return self._constructionset_lib

    @property
    def schedule_lib(self):
        """Get the path to the schedule library in the standards_data_folder."""
        return self._schedule_lib

    @property
    def programtype_lib(self):
        """Get the path to the programtype library in the standards_data_folder."""
        return self._programtype_lib

    @property
    def defaults_file(self):
        """Get the path to the JSON file where honeybee's defaults are loaded from."""
        return self._defaults_file

    @defaults_file.setter
    def defaults_file(self, path):
        if not path:  # check the default location
            path = self._find_defaults_file()
        assert os.path.isfile(path), \
            '{} is not a valid path to an defaults JSON file.'.format(path)
        self._defaults_file = path
        if not self.mute:
            print("Path to defaults file is set to: %s" % self._defaults_file)

    @property
    def config_file(self):
        """Get or set the path to the config.json file from which folders are loaded.

        Setting this to None will result in using the config.json module included
        in this package.
        """
        return self._config_file

    @config_file.setter
    def config_file(self, cfg):
        if cfg is None:
            cfg = os.path.join(os.path.dirname(__file__), 'config.json')
        self._load_from_file(cfg)
        self._config_file = cfg

    def _load_from_file(self, file_path):
        """Set all of the the properties of this object from a config JSON file.

        Args:
            file_path: Path to a JSON file containing the file paths. A sample of this
                JSON is the config.json file within this package.
        """
        # check the default file path
        assert os.path.isfile(str(file_path)), \
            ValueError('No file found at {}'.format(file_path))

        # set the default paths to be all blank
        default_path = {
            "energyplus_path": r'',
            "openstudio_path": r'',
            "lbt_measures_path": r'',
            "honeybee_openstudio_gem_path": r'',
            "ironbug_path": r'',
            "standards_data_folder": r'',
            "standards_extension_folders": [],
            "defaults_file": r''
        }

        with open(file_path, 'r') as cfg:
            try:
                paths = json.load(cfg)
            except Exception as e:
                print('Failed to load paths from {}.\n{}'.format(file_path, e))
            else:
                for key, p in paths.items():
                    if isinstance(key, list) or not key.startswith('__'):
                        try:
                            default_path[key] = p.strip()
                        except AttributeError:
                            default_path[key] = p

        # set paths for energyplus and openstudio installations
        self.openstudio_path = default_path["openstudio_path"]
        self.energyplus_path = default_path["energyplus_path"]

        # set the paths for lbt_measures and the honeybee_openstudio_gem
        self.lbt_measures_path = default_path["lbt_measures_path"]
        self.honeybee_openstudio_gem_path = default_path["honeybee_openstudio_gem_path"]

        # set the paths for ironbug
        self.ironbug_path = default_path["ironbug_path"]

        # set path for the standards_data_folder and defaults_file
        self.standards_data_folder = default_path["standards_data_folder"]
        self.defaults_file = default_path["defaults_file"]

        # set path for the standards_extension_folders
        self.standards_extension_folders = default_path["standards_extension_folders"]

    def _find_lbt_measures_path(self):
        """Find the lbt_measures_path in its default location.

        The ladybug_tools/resources/measures folder will be checked for the
        expected directories of measures.
        """
        # first, check the resources/measures folder in the ladybug_tools folder
        lb_install = lb_config.folders.ladybug_tools_folder
        if os.path.isdir(lb_install):
            measure_path = os.path.join(lb_install, 'resources', 'measures')
            if os.path.isdir(os.path.join(measure_path, 'openstudio_results')):
                return measure_path
        return None  # No lbt_measures is installed

    def _find_honeybee_openstudio_gem_path(self):
        """Find the honeybee_openstudio_gem_path in its default location.

        First, the ladybug_tools/resources/measures folder will be checked for a
        honeybee_openstudio_gem directory.

        If nothing is found there, the OpenStudio installation will be checked
        to see if there is a compatible version of the measure installed that
        is specific for that version of OpenStudio.
        """
        # first, check the resources/measures folder in the ladybug_tools folder
        lb_install = lb_config.folders.ladybug_tools_folder
        if os.path.isdir(lb_install):
            measure_path = os.path.join(
                lb_install, 'resources', 'measures', 'honeybee_openstudio_gem', 'lib')
            if os.path.isdir(measure_path):
                return measure_path

        # then check if there's a version installed in the OpenStudio folder
        if self.openstudio_path:
            os_root = os.path.split(self.openstudio_path)[0]
            measure_path = os.path.join(os_root, 'honeybee_openstudio_gem', 'lib')
            if os.path.isdir(measure_path):
                return measure_path

        return None  # No energy model measure is installed

    def _find_ironbug_path_folder(self):
        """Find the ironbug_path in its default location.

        The ladybug_tools/grasshopper/ironbug folder will be checked for the
        expected directories.
        """
        # first, check the grasshopper/ironbug folder in the ladybug_tools folder
        lb_install = lb_config.folders.ladybug_tools_folder
        if os.path.isdir(lb_install):
            ib_path = os.path.join(lb_install, 'grasshopper', 'ironbug')
            if os.path.isdir(ib_path):
                return ib_path
        return None  # No ironbug is installed

    def _find_energyplus_folder(self):
        """Find the most recent EnergyPlus installation in its default location.

        This method will first attempt to return the path of the EnergyPlus that
        installs with OpenStudio and, if none are found, it will search for a
        standalone installation of EnergyPlus.

        Returns:
            File directory and full path to executable in case of success.
            None in case of failure.
        """
        def getversion(energyplus_path):
            """Get digits for the version of EnergyPlus."""
            try:
                ver = ''.join(s for s in energyplus_path if (s.isdigit() or s == '-'))
                return sum(int(d) * (10 ** i)
                           for i, d in enumerate(reversed(ver.split('-'))))
            except ValueError:  # folder starting with 'EnergyPlus' and no version
                return 0

        # first check for the EnergyPlus that comes with OpenStudio
        ep_path, ep_folders = None, []
        if self.openstudio_path is not None and os.path.isdir(os.path.join(
                os.path.split(self.openstudio_path)[0], 'EnergyPlus')):
            ep_path = os.path.join(os.path.split(self.openstudio_path)[0], 'EnergyPlus')

        # then check the default location where standalone EnergyPlus is installed
        elif os.name == 'nt':  # search the C:/ drive on Windows
            for f in os.listdir('C:\\'):
                f_path = 'C:\\{}'.format(f)
                if f.lower().startswith('energyplus') and os.path.isdir(f_path):
                    ep_folders.append(f_path)
        elif platform.system() == 'Darwin':  # search the Applications folder on Mac
            for f in os.listdir('/Applications/'):
                f_path = '/Applications/{}'.format(f)
                if f.lower().startswith('energyplus') and os.path.isdir(f_path):
                    ep_folders.append(f_path)
        elif platform.system() == 'Linux':  # search the usr/local folder
            for f in os.listdir('/usr/local/'):
                f_path = '/usr/local/{}'.format(f)
                if f.lower().startswith('energyplus') and os.path.isdir(f_path):
                    ep_folders.append(f_path)

        if not ep_path and not ep_folders:  # No EnergyPlus installations were found
            return None
        elif not ep_path:  # get the most recent version of energyplus that was found
            ep_path = sorted(ep_folders, key=getversion, reverse=True)[0]
        return ep_path

    def _openstudio_version_from_cli(self):
        """Set this object's OpenStudio version by making a call to OpenStudio CLI."""
        cmds = [self.openstudio_exe, 'openstudio_version']
        use_shell = True if os.name == 'nt' else False
        process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=use_shell)
        stdout = process.communicate()
        try:
            base_str = str(stdout[0]).replace("b'", '').replace(r"\r\n'", '')
            self._openstudio_version_str = base_str
            ver_nums = self._openstudio_version_str.split('+')[0].split('.')
            ver_nums[-1] = ver_nums[-1].split('-')[0] \
                if '-' in ver_nums[-1] else ver_nums[-1]
            self._openstudio_version = tuple(int(i) for i in ver_nums)
        except Exception:
            pass  # failed to parse the version into integers

    def _energyplus_version_from_cli(self):
        """Set this object's EnergyPlus version by making a call to EnergyPlus CLI."""
        cmds = [self.energyplus_exe, '--version']
        use_shell = True if os.name == 'nt' else False
        process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=use_shell)
        stdout = process.communicate()
        try:
            base_str = str(stdout[0]).replace("b'", '').replace(r"\r\n'", '')
            self._energyplus_version_str = base_str.split(',')[1].split(' ')[-1]
            ver_nums = self._energyplus_version_str.split('-')[0].split('.')
            self._energyplus_version = tuple(int(i) for i in ver_nums)
        except Exception:
            pass  # failed to parse the version into integers

    def _ironbug_version_from_cli(self):
        """Set this object's Ironbug version by making a call to Ironbug CLI."""
        cmds = [self.ironbug_exe, '--version']
        use_shell = True if os.name == 'nt' else False
        process = subprocess.Popen(cmds, stdout=subprocess.PIPE, shell=use_shell)
        stdout = process.communicate()
        base_str = str(stdout[0]).replace("b'", '')
        base_str = base_str.replace("\r\n", '__').replace(r"\r\n", '__') \
            if os.name == 'nt' else base_str.replace("\n", '__').replace(r"\n", '__')
        try:
            base_str = base_str.split('__')[-2]
            self._ironbug_version_str = base_str
            ver_nums = base_str.split(' ')[0].replace('v', '').split('.')
            self._ironbug_version = tuple(int(i) for i in ver_nums)
        except Exception:
            pass  # failed to parse the version into integers

    @staticmethod
    def _find_openstudio_folder():
        """Find the most recent OpenStudio installation in its default location.

        Returns:
            File directory and full path to executable in case of success.
            None in case of failure.
        """
        def getversion(openstudio_path):
            """Get digits for the version of OpenStudio."""
            try:
                ver = ''.join(s for s in openstudio_path if (s.isdigit() or s == '.'))
                return sum(int(d) * (10 ** i)
                           for i, d in enumerate(reversed(ver.split('.'))))
            except ValueError:  # folder starting with 'openstudio' and no version
                return 0

        # first check if there's a version installed in the ladybug_tools folder
        lb_install = lb_config.folders.ladybug_tools_folder
        os_folders = []
        if os.path.isdir(lb_install):
            for f in os.listdir(lb_install):
                f_path = os.path.join(lb_install, f)
                if f.lower().startswith('openstudio') and os.path.isdir(f_path):
                    os_folders.append(f_path)

        # then check the default installation folders
        if len(os_folders) != 0 and os.path.isdir(os.path.join(os_folders[0], 'bin')):
            pass  # we found a version of openstudio in the ladybug_tools folder
        elif os.name == 'nt':  # search the C:/ drive on Windows
            for f in os.listdir('C:\\'):
                f_path = 'C:\\{}'.format(f)
                if f.lower().startswith('openstudio') and os.path.isdir(f_path):
                    os_folders.append(f_path)
        elif platform.system() == 'Darwin':  # search the Applications folder on Mac
            for f in os.listdir('/Applications/'):
                f_path = '/Applications/{}'.format(f)
                if f.lower().startswith('openstudio') and os.path.isdir(f_path):
                    os_folders.append(f_path)
        elif platform.system() == 'Linux':  # search the usr/local folder
            for f in os.listdir('/usr/local/'):
                f_path = '/usr/local/{}'.format(f)
                if f.lower().startswith('openstudio') and os.path.isdir(f_path):
                    os_folders.append(f_path)
        else:  # unknown operating system
            os_folders = None

        if not os_folders:  # No Openstudio installations were found
            return None

        # get the most recent version of OpenStudio that was found
        os_path = sorted(os_folders, key=getversion, reverse=True)[0]

        return os.path.join(os_path, 'bin')

    @staticmethod
    def _find_standards_data_folder():
        """Find the user template library in its default location.

        The %AppData%/ladybug_tools/standards folder will be checked first, which
        can contain libraries that are not overwritten with the update of the
        honeybee_energy package. If this is not found, the ladybug_tools/resources/
        standards/honeybee_standards folder will be checked next,  If no such folder
        is found, this method defaults to the lib/library/ folder within this package.
        """
        # first check if there's a user-defined folder in AppData
        app_folder = os.getenv('APPDATA')
        if app_folder is not None:
            lib_folder = os.path.join(app_folder, 'ladybug_tools', 'standards')
            if os.path.isdir(lib_folder):
                return lib_folder

        # then check the ladybug_tools installation folder were permanent lib is
        lb_install = lb_config.folders.ladybug_tools_folder
        if os.path.isdir(lb_install):
            lib_folder = os.path.join(
                lb_install, 'resources', 'standards', 'honeybee_standards')
            if os.path.isdir(lib_folder):
                try:
                    Folders._check_standards_folder(lib_folder)
                    return lib_folder
                except AssertionError:  # the folder is not valid
                    pass

        # default to the library folder that installs with this Python package
        return os.path.join(os.path.dirname(honeybee_standards.__file__))

    @staticmethod
    def _find_standards_extension_folders():
        """Find the standards extension folders in their default locations.

        Extension folders are expected to start with the words "honeybee_energy"
        and end with the words "standards" (eg. honeybee_energy_cibse_standards).

        The ladybug_tools/resources/standards folder will be checked first, which
        can contain libraries that are not overwritten with the update of the
        honeybee_energy package.
        If no folders are found, this method will look for any Python packages
        sitting next to honeybee_energy that follow the naming criteria above.
        """
        standards_extensions = []
        # first check the ladybug_tools installation folder were permanent lib is
        lb_install = lb_config.folders.ladybug_tools_folder
        std_folder = os.path.join(lb_install, 'resources', 'standards')
        if os.path.isdir(std_folder):
            for folder in os.listdir(std_folder):
                if folder.endswith('standards') and folder.startswith('honeybee_energy'):
                    lib_folder = os.path.join(std_folder, folder)
                    if os.path.isdir(lib_folder):
                        standards_extensions.append(lib_folder)
        # then check next to the Python library
        if len(standards_extensions) == 0:
            for finder, name, ispkg in pkgutil.iter_modules():
                if name.endswith('standards') and name.startswith('honeybee_energy'):
                    lib_folder = os.path.join(finder.path, name)
                    if os.path.isdir(lib_folder):
                        standards_extensions.append(lib_folder)
        return standards_extensions

    @staticmethod
    def _check_standards_folder(path):
        """Check that a standards data sub-folders exist."""
        if not path:  # first check that a path exists
            return [None] * 4

        # gather all of the sub folders underneath the master folder
        _construction_lib = os.path.join(path, 'constructions')
        _constructionset_lib = os.path.join(path, 'constructionsets')
        _schedule_lib = os.path.join(path, 'schedules')
        _programtype_lib = os.path.join(path, 'programtypes')

        assert os.path.isdir(_construction_lib), \
            '{} lacks a "constructions" folder.'.format(path)
        assert os.path.isdir(_constructionset_lib), \
            '{} lacks a "constructionsets" folder.'.format(path)
        assert os.path.isdir(_schedule_lib), \
            '{} lacks a "schedules" folder.'.format(path)
        assert os.path.isdir(_programtype_lib), \
            '{} lacks a "programtypes" folder.'.format(path)

        return _construction_lib, _constructionset_lib, _schedule_lib, _programtype_lib

    @staticmethod
    def _find_defaults_file():
        """Find the energy default JSON in its default locations."""
        # first check the ladybug_tools installation folder were permanent lib is
        lb_install = lb_config.folders.ladybug_tools_folder
        if os.path.isdir(lb_install):
            def_file = os.path.join(
                lb_install, 'resources', 'standards', 'honeybee_standards',
                'energy_default.json')
            if os.path.isfile(def_file):
                return def_file

        # default to the library folder that installs with this Python package
        return os.path.join(
            os.path.dirname(honeybee_standards.__file__), 'energy_default.json')


"""Object possesing all key folders within the configuration."""
folders = Folders(mute=True)
