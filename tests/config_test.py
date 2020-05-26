# coding=utf-8
from honeybee_energy.config import folders
from honeybee_energy.writer import energyplus_idf_version

import pytest


def test_config_init():
    """Test the initialization of the config module and basic properties."""
    assert hasattr(folders, 'energyplus_path')
    assert folders.energyplus_path is None or isinstance(folders.energyplus_path, str)
    assert hasattr(folders, 'energyplus_exe')
    assert folders.energyplus_exe is None or isinstance(folders.energyplus_exe, str)
    assert hasattr(folders, 'energyplus_version')
    assert folders.energyplus_version is None or isinstance(folders.energyplus_version, tuple)

    assert hasattr(folders, 'openstudio_path')
    assert folders.openstudio_path is None or isinstance(folders.openstudio_path, str)
    assert hasattr(folders, 'openstudio_exe')
    assert folders.openstudio_exe is None or isinstance(folders.openstudio_exe, str)
    assert hasattr(folders, 'openstudio_version')
    assert folders.openstudio_version is None or isinstance(folders.openstudio_version, tuple)

    assert hasattr(folders, 'honeybee_openstudio_gem_path')
    assert folders.honeybee_openstudio_gem_path is None or \
        isinstance(folders.honeybee_openstudio_gem_path, str)

    assert hasattr(folders, 'standards_data_folder')
    assert isinstance(folders.standards_data_folder, str)
    assert isinstance(folders.construction_lib, str)
    assert isinstance(folders.constructionset_lib, str)
    assert isinstance(folders.schedule_lib, str)
    assert isinstance(folders.programtype_lib, str)

    assert isinstance(folders.config_file, str)


def test_writer_version_idf():
    """Test the energyplus_idf_version method."""
    assert energyplus_idf_version() is None or \
        isinstance(energyplus_idf_version(), str)
    assert isinstance(energyplus_idf_version((9, 2, 0)), str)
