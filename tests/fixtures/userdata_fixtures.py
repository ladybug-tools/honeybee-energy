import pytest


@pytest.fixture
def userdatadict():
    """A fixture to test the various data types that are supported within user_data."""
    return {
        'str_key': 'str_val',
        'float_key': 0.01,
        't_key': True,
        'f_key': False,
        'list_key': [1, 0.1, 'test', True, False]
    }
