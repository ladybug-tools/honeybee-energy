# coding=utf-8
"""Module for parsing OpenStudio Workflow (OSW) files."""
from __future__ import division

import os
import json


class OSW(object):
    """Object for parsing OpenStudio Workflow (OSW) files.

    Args:
        file_path: Full path to an OSW file.

    Properties:
        * file_path
        * file_dict
        * stdout
        * warnings
        * errors
        * error_tracebacks
    """

    def __init__(self, file_path):
        """Initialize OSW"""
        assert os.path.isfile(file_path), 'No file was found at {}'.format(file_path)
        assert file_path.endswith('.osw'), \
            '{} is not an OSW file ending in .osw.'.format(file_path)
        self._file_path = file_path
        self._load_contents()
        self._parse_contents()

    @property
    def file_path(self):
        """Get the path to the .osw file."""
        return self._file_path

    @property
    def file_dict(self):
        """Get a dictionary of all contents in the file."""
        return self._file_dict

    @property
    def stdout(self):
        """Get a list of strings for all of the stdout of each step of the .osw file."""
        return self._stdout

    @property
    def warnings(self):
        """Get a list of strings for all of the warnings found in the .osw file."""
        return self._warnings

    @property
    def errors(self):
        """Get a list of strings for all of the fatal errors found in the .osw file."""
        return self._errors

    @property
    def error_tracebacks(self):
        """Get a list of strings for the tracebacks found in the .osw file."""
        return self._error_tracebacks

    def _load_contents(self):
        """Parse all of the contents of a file path."""
        with open(self._file_path) as json_file:
            self._file_dict = json.load(json_file)

    def _parse_contents(self):
        """Sort the contents of the error file into warnings and errors."""
        self._stdout = []
        self._warnings = []
        self._errors = []
        self._error_tracebacks = []
        try:
            for step in self.file_dict['steps']:
                result = step['result']
                self._stdout.append(result['stdout'])
                self._warnings.extend(result['step_warnings'])
                for error in result['step_errors']:
                    self._error_tracebacks.append(error)
                    self._errors.append(error.split('\n')[0])
        except KeyError:  # no results yet
            pass

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __repr__(self):
        return 'OSW: {}'.format(self.file_path)
