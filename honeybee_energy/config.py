"""Honeybee_energy configurations.

Import this into every module where access configurations are needed.

Usage:

.. code-block:: python

    from honeybee_energy.config import folders
    print(folders.energyplus_path)
    print(folders.openstudio_path)
    folders.energyplus_path = "C:/EnergyPlusV9-0-1"
"""
import honeybee.config as hb_config

import os
import platform
import json


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
        * energyplus_path
        * energyplus_exe
        * energy_model_measure_path
        * standards_data_folder
        * construction_lib
        * constructionset_lib
        * schedule_lib
        * programtype_lib
        * config_file
        * mute
    """

    def __init__(self, config_file=None, mute=True):
        # set the mute value
        self.mute = bool(mute)

        # load paths from the config JSON file 
        self.config_file  = config_file

    @property
    def openstudio_path(self):
        """Get or set the path to OpenStudio installation folder.
        
        This is the "bin" directory for OpenStudio installation (the one that
        contains the openstudio executable file).
        """
        return self._openstudio_path

    @openstudio_path.setter
    def openstudio_path(self, path):
        exe_name = 'openstudio.exe' if os.name == 'nt' else 'openstudio'
        if not path:  # check the PATH and then the default installation location
            path, os_exe_file = self._which(exe_name)
            if path is None:  # search within the default installation location
                path, os_exe_file = self._find_openstudio_folder()
        else:
            os_exe_file = os.path.join(path, exe_name)

        if path:  # check that the OpenStudio executable exists in the path
            assert os.path.isfile(os_exe_file), \
                '{} is not a valid path to an openstudio installation.'.format(path)

        #set the openstudio_path
        self._openstudio_path = path
        self._openstudio_exe = os_exe_file
        if path and not self.mute:
            print("Path to OpenStudio is set to: %s" % path)
    
    @property
    def openstudio_exe(self):
        """Get the path to the executable openstudio file."""
        return self._openstudio_exe

    @property
    def energyplus_path(self):
        """Get or set the path to EnergyPlus installation folder."""
        return self._energyplus_path
    
    @energyplus_path.setter
    def energyplus_path(self, path):
        exe_name = 'energyplus.exe' if os.name == 'nt' else 'energyplus'
        if not path:  # check the PATH and then the default installation location
            path, ep_exe_file = self._which(exe_name)
            if path is None:  # search within the default installation location
                path, ep_exe_file = self._find_energyplus_folder()
        else:
            ep_exe_file = os.path.join(path, exe_name)
        
        if path:  # check that the Energyplus executable exists in the installation
            assert os.path.isfile(ep_exe_file), \
                '{} is not a valid path to an energyplus installation.'.format(path)

        # set the energyplus_path
        self._energyplus_path = path
        self._energyplus_exe = ep_exe_file
        if path and not self.mute:
            print("Path to EnergyPlus is set to: %s" % self._energyplus_path)

    @property
    def energyplus_exe(self):
        """Get the path to the executable energyplus file."""
        return self._energyplus_exe
    
    @property
    def energy_model_measure_path(self):
        """Get or set the path to the energy_model_measure translating to OpenStudio.
        
        This folder must have the following sub-folders in order to be valid:
            * ladybug - ruby library with modules for model translation to OpenStudio.
            * measures - folder with the actual measures that run the translation.
            * files - folder containing the openapi schemas
        """
        return self._energy_model_measure_path
    
    @energy_model_measure_path.setter
    def energy_model_measure_path(self, path):
        if not path:  # check the default locations of the energy_model_measure
            path = self._find_energy_model_measure_path()

        # check that the library's sub-folders exist
        if path:
            assert os.path.isdir(os.path.join(path, 'from_honeybee')), '{} lacks a ' \
                '"from_honeybee" folder for the translation ruby library.'.format(path)
            assert os.path.isdir(os.path.join(path, 'measures')), \
                '{} lacks a "measures" folder.'.format(path)

        # set the energy_model_measure_path
        self._energy_model_measure_path = path
        if path and not self.mute:
            print('Path to the energy_model_measure is set to: '
                    '{}'.format(self._energy_model_measure_path))
    
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
        self._construction_lib = os.path.join(path, 'constructions') if path else None
        self._constructionset_lib = os.path.join(path, 'constructionsets') if path else None
        self._schedule_lib = os.path.join(path, 'schedules') if path else None
        self._programtype_lib = os.path.join(path, 'programtypes') if path else None

        # check that the library's sub-folders exist
        if path:
            assert os.path.isdir(self._construction_lib), \
                '{} lacks a "constructions" folder.'.format(path)
            assert os.path.isdir(self._constructionset_lib), \
                '{} lacks a "constructionsets" folder.'.format(path)
            assert os.path.isdir(self._schedule_lib), \
                '{} lacks a "schedules" folder.'.format(path)
            assert os.path.isdir(self._programtype_lib), \
                '{} lacks a "programtypes" folder.'.format(path)

        # set the standards_data_folder
        self._standards_data_folder = path
        if path and not self.mute:
            print('Path to the standards_data_folder is set to: '
                    '{}'.format(self._standards_data_folder))
    
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
            "energy_model_measure_path": r'',
            "standards_data_folder": r''
        }

        with open(file_path, 'r') as cfg:
            try:
                paths = json.load(cfg)
            except Exception as e:
                print('Failed to load paths from {}.\n{}'.format(file_path, e))
            else:
                for key, p in paths.items():
                    if not key.startswith('__') and p.strip():
                        default_path[key] = p.strip()

        # set paths for energyplus and openstudio installations
        self.openstudio_path = default_path["openstudio_path"]
        self.energyplus_path = default_path["energyplus_path"]

        # set the paths for the energy_model_measure
        self.energy_model_measure_path = default_path["energy_model_measure_path"]

        # set path for the standards_data_folder
        self.standards_data_folder = default_path["standards_data_folder"]

    def _find_energyplus_folder(self):
        """Find the most recent EnergyPlus installation in its default location.
        
        This method will first attempt to return the path of the EnergyPlus that
        installs with OpenStudio and, if none are found, it will search for a
        standalone installation of EnergyPlus.

        Returns:
            File directory and full path to executable in case of success.
            None, None in case of failure.
        """
        def getversion(energyplus_path):
            """Get digits for the version of EnergyPlus."""
            ver = ''.join(s for s in energyplus_path if (s.isdigit() or s == '-'))
            return sum(int(d) * (10 ** i) for i, d in enumerate(reversed(ver.split('-'))))

        # first check for the EnergyPlus that comes with OpenStudio
        ep_path = None
        if self.openstudio_path is not None and os.path.isdir(os.path.join(
                os.path.split(self.openstudio_path)[0], 'EnergyPlus')):
            ep_path = os.path.join(os.path.split(self.openstudio_path)[0], 'EnergyPlus')
        # then check the default location where standalone EnergyPlus is installed
        elif os.name == 'nt':  # search the C:/ drive on Windows
            ep_folders = ['C:\\{}'.format(f) for f in os.listdir('C:\\')
                          if (f.lower().startswith('energyplus') and
                              os.path.isdir('C:\\{}'.format(f)))]
        elif platform.system() == 'Darwin':  # search the Applications folder on Mac
            ep_folders = ['/Applications/{}'.format(f) for f in os.listdir('/Applications/')
                          if (f.lower().startswith('energyplus') and
                              os.path.isdir('/Applications/{}'.format(f)))]
        elif platform.system() == 'Linux':  # search the usr/local folder
            ep_folders = ['/usr/local/{}'.format(f) for f in os.listdir('/usr/local/')
                          if (f.lower().startswith('energyplus') and
                              os.path.isdir('/usr/local/{}'.format(f)))]
        else:  # unknown operating system
            ep_folders = None
        
        if not ep_path and not ep_folders:  # No EnergyPlus installations were found
            return None, None
        elif not ep_path:
            # get the most recent version of energyplus that was found
            ep_path = sorted(ep_folders, key=getversion, reverse=True)[0]
        
        # return the path to the executable
        exec_file = os.path.join(ep_path, 'energyplus.exe') if os.name == 'nt' \
            else os.path.join(ep_path, 'energyplus')
        return ep_path, exec_file

    @staticmethod
    def _find_openstudio_folder():
        """Find the most recent OpenStudio installation in its default location.

        Returns:
            File directory and full path to executable in case of success.
            None, None in case of failure.
        """
        def getversion(openstudio_path):
            """Get digits for the version of OpenStudio."""
            ver = ''.join(s for s in openstudio_path if (s.isdigit() or s == '.'))
            return sum(int(d) * (10 ** i) for i, d in enumerate(reversed(ver.split('.'))))

        if os.name == 'nt':  # search the C:/ drive on Windows
            os_folders = ['C:\\{}'.format(f) for f in os.listdir('C:\\')
                          if (f.lower().startswith('openstudio') and
                              os.path.isdir('C:\\{}'.format(f)))]
        elif platform.system() == 'Darwin':  # search the Applications folder on Mac
            os_folders = ['/Applications/{}'.format(f) for f in os.listdir('/Applications/')
                          if (f.lower().startswith('openstudio') and
                              os.path.isdir('/Applications/{}'.format(f)))]
        elif platform.system() == 'Linux':  # search the usr/local folder
            os_folders = ['/usr/local/{}'.format(f) for f in os.listdir('/usr/local/')
                          if (f.lower().startswith('openstudio') and
                              os.path.isdir('/usr/local/{}'.format(f)))]
        else:  # unknown operating system
            os_folders = None
        
        if not os_folders:  # No Openstudio installations were found
            return None, None
        
        # get the most recent version of OpenStudio that was found
        os_path = sorted(os_folders, key=getversion, reverse=True)[0]
        
        # return the path to the executable
        exec_file = os.path.join(os_path, 'bin', 'openstudio.exe') if os.name == 'nt' \
            else os.path.join(os_path, 'bin', 'openstudio')
        return os.path.join(os_path, 'bin'), exec_file

    @staticmethod
    def _find_energy_model_measure_path():
        """Find the energy_model_measure_path in its default location.

        This is usually the OpenStudio BCL Measures path .
        """
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        bcl_folder = os.path.join(home_folder, 'OpenStudio', 'Measures')
        measure_path = os.path.join(bcl_folder, 'energy_model_measure', 'lib')
        if not os.path.isdir(measure_path):
            if not os.path.isdir(measure_path):
                measure_path = os.path.join(bcl_folder, 'energy-model-measure', 'lib')
                if not os.path.isdir(measure_path):
                    return  # No energy model measure is installed
        return measure_path
    
    @staticmethod
    def _find_standards_data_folder():
        """Find the the user template library in its default location.
        
        The HOME/honeybee/honeybee_standards/data folder will be checked first,
        which can conatain libraries that are not overwritten with the update of the
        honeybee_energy package. If no such folder is found, this method defaults to
        the lib/library/ folder within this package.
        """
        # first check the default sim folder folder, where permanent libraries live
        home_folder = os.getenv('HOME') or os.path.expanduser('~')
        lib_folder = os.path.join(home_folder, 'honeybee', 'honeybee_standards', 'data')
        if os.path.isdir(lib_folder):
            return lib_folder
        else:  # default to the library folder that installs with this Python package
            return os.path.join(os.path.dirname(__file__), 'lib', 'data')
    
    @staticmethod
    def _which(program):
        """Find an executable program in the PATH by name.

        Args:
            program: Full file name for the program (e.g. energyplus.exe)

        Returns:
            File directory and full path to program in case of success.
            None, None in case of failure.
        """
        def is_exe(fpath):
            # Return true if the file exists and is executable
            return os.path.isfile(fpath) and os.access(fpath, os.X_OK)

        # check for the file in all path in environment
        for path in os.environ["PATH"].split(os.pathsep):
            exe_file = os.path.join(path.strip('"'), program)  # strip "" in Windows
            if is_exe(exe_file):
                return path, exe_file

        # couldn't find it in the PATH! return None :|
        return None, None


"""Object possesing all key folders within the configuration."""
folders = Folders(mute=True)
