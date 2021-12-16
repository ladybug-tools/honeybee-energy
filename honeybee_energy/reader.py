"""Methods to read from idf."""
import re
import os


def clean_idf_file_contents(idf_file):
    """Get the contents of an IDF file without any commented lines.

    These comment lines might interfere with regex parsing if they are present.

    Args:
        idf_file: A path to an IDF file containing objects to be parsed.

    Returns:
        A single string for the clean IDF file contents.
    """
    assert os.path.isfile(idf_file), 'Cannot find an idf file at {}'.format(idf_file)
    file_lines = []
    with open(idf_file, 'r') as ep_file:
        for line in ep_file:
            if not line.startswith('!'):
                file_lines.append(line)
    return ''.join(file_lines)


def parse_idf_string(idf_string, expected_type=None):
    """Parse an EnergyPlus string of a single object into a list of values.

    Args:
        idf_string: An IDF string for a single EnergyPlus object.
        expected_type: Text representing the expected start of the IDF object.
            (ie. WindowMaterial:Glazing). If None, no type check will be performed.

    Returns:
        ep_fields -- A list of strings with each item in the list as a separate field.
        Note that this list does NOT include the string for the start of the IDF
        object. (ie. WindowMaterial:Glazing)
    """
    idf_string = idf_string.strip()
    if expected_type is not None:
        assert idf_string.startswith(expected_type), 'Expected EnergyPlus {} ' \
            'but received a different object: {}'.format(expected_type, idf_string)
    idf_strings = idf_string.split(';')
    assert len(idf_strings) == 2, 'Received more than one object in idf_string.'
    idf_string = re.sub(r'!.*\n', '', idf_strings[0])
    ep_fields = [e_str.strip() for e_str in idf_string.split(',')]
    ep_fields.pop(0)  # remove the EnergyPlus object name
    return ep_fields
