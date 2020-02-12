# coding=utf-8
from honeybee_energy.config import folders

import pytest


def test_config_init():
    """Test the initialization of the config module and basic properties."""
    assert hasattr(folders, 'energyplus_path')
    assert folders.energyplus_path is None or isinstance(folders.energyplus_path, str)

    assert hasattr(folders, 'openstudio_path')
    assert folders.openstudio_path is None or isinstance(folders.openstudio_path, str)

    assert hasattr(folders, 'energy_model_measure_path')
    assert folders.energy_model_measure_path is None or \
        isinstance(folders.energy_model_measure_path, str)

    assert hasattr(folders, 'standards_data_folder')
    assert isinstance(folders.standards_data_folder, str)
    assert isinstance(folders.construction_lib, str)
    assert isinstance(folders.constructionset_lib, str)
    assert isinstance(folders.schedule_lib, str)
    assert isinstance(folders.programtype_lib, str)

    assert isinstance(folders.config_file, str)
