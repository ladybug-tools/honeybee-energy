# coding=utf-8
"""Module for parsing OpenStudio measures and setting measure arguments."""
from __future__ import division

import os
import xml.etree.ElementTree as ElementTree


class Measure(object):
    """Object to hold all properties of an OpenStudio measure, including arguments.

    Args:
        folder: Path to the folder in which the measure exists. This folder
            must contain a measure.rb and a measure.xml file. Other files are
            optional.

    Properties:
        * folder
        * metadata_file
        * program_file
        * resources_folder
        * identifier
        * display_name
        * description
        * type
        * arguments
    """
    __slots__ = ('_folder', '_metadata_file', '_program_file', '_resources_folder',
                 '_identifier', '_display_name', '_description', '_type', '_arguments')

    def __init__(self, folder):
        """Initialize Measure."""
        # check to be sure that the required files are all there
        assert os.path.isdir(folder), \
            'No directory was found at {}'.format(folder)
        self._folder = os.path.abspath(folder)
        self._metadata_file = os.path.join(self._folder, 'measure.xml')
        assert os.path.isfile(self._metadata_file), \
            'No Measure XML file was found at {}'.format(self._metadata_file)
        self._program_file = os.path.join(self._folder, 'measure.rb')
        assert os.path.isfile(self._program_file), \
            'No Measure Ruby file was found at {}'.format(self._program_file)
        resources_folder = os.path.join(self._folder, 'resources')
        self._resources_folder = None
        if os.path.isdir(resources_folder):
            self._resources_folder = resources_folder

        # parse the XML file to extract the measure properties and arguments
        self._parse_metadata_file()

    @property
    def folder(self):
        """Get the path to the folder in which the measure exists."""
        return self._folder

    @property
    def metadata_file(self):
        """Get the path to the measure.xml file within the measure folder.

        This file contains metadata about the measure and this is where many of
        the properties on this object originate from.
        """
        return self._metadata_file

    @property
    def program_file(self):
        """Get the path to the measure.rb file within the measure folder.

        This file contains the Ruby code that is executed whenever the measure
        is run by the OpenStudio CLI.
        """
        return self._program_file

    @property
    def resources_folder(self):
        """Get the path to the folder for resource Ruby file if it exists.

        This folder contains Ruby file dependencies that are used in the program_file.
        """
        return self._resources_folder

    @property
    def identifier(self):
        """Get text for the identifier of the measure.

        This is also called the "name" in the measure.xml file.
        """
        return self._identifier

    @property
    def display_name(self):
        """Get text for the human-readable display name of the measure.

        This is called the "display_name" in the measure.xml file.
        """
        return self._display_name

    @property
    def description(self):
        """Get text for describing what the measure does."""
        return self._description

    @property
    def type(self):
        """Get text for the type of measure this is. This is always one of 3 values.

            * ModelMeasure - for measures that operate on the .osm model.
            * EnergyPlusMeasure - for measures that operate on the .idf file.
            * ReportingMeasure - for measures that run after the simulation is finished.
        """
        return self._type

    @property
    def arguments(self):
        """Get a tuple of MeasureArgument objects for the measure input arguments.

        The value property of these objects can be set in order to specify input
        arguments for the measure.
        """
        return tuple(self._arguments)

    @classmethod
    def from_dict(cls, data, folder='.'):
        """Initialize a Measure from a dictionary.

        Args:
            data: A dictionary in the format below.
            folder: Path to a destination folder to save the measure files. (Default '.')

        .. code-block:: python

            {
            "type": "Measure",
            "identifier": string,  # Measure identifier
            "xml_data": string,  # XML file data as string
            "rb_data": string,  # Ruby file data as string
            "resource_data": {},  # Dictionary of strings for any resource ruby files
            "argument_values": [],  # List of values for each of the measure arguments
            }
        """
        assert data['type'] == 'Measure', \
            'Expected Measure dictionary. Got {}.'.format(data['type'])
        fp = os.path.join(folder, data['identifier'])
        if not os.path.isdir(fp):
            os.makedirs(fp)

        # write out the contents of the measure
        xml_fp = os.path.join(fp, 'measure.xml')
        cls._decompress_to_file(data['xml_data'], xml_fp)
        rb_fp = os.path.join(fp, 'measure.rb')
        cls._decompress_to_file(data['rb_data'], rb_fp)
        if 'resource_data' in data and data['resource_data'] is not None:
            resource_path = os.path.join(fp, 'resources')
            os.makedirs(resource_path)
            for f_name, res in data['resource_data'].items():
                res_fp = os.path.join(resource_path, f_name)
                cls._decompress_to_file(res, res_fp)

        # create the measure object and assign the arguments
        new_measure = cls(fp)
        for arg, val in zip(new_measure.arguments, data['argument_values']):
            if val is not None:
                arg.value = val
        return new_measure

    def to_dict(self):
        """Convert Measure to a dictionary."""
        # create a base dictionary with the XML and Ruby file data, and the arguments
        base = {
            'type': 'Measure',
            'identifier': self.identifier,
            'xml_data': self._compress_file(self.metadata_file),
            'rb_data': self._compress_file(self.program_file),
            'argument_values': [arg._value for arg in self._arguments]
        }

        # add any resource files to the dictionary if they exist
        if self.resources_folder:
            base['resource_data'] = {}
            for rb_file in os.listdir(self.resources_folder):
                path = os.path.join(self.folder, rb_file)
                base['resource_data'][rb_file] = self._compress_file(path)

        return base

    def to_osw_dict(self, full_path=False):
        """Get a Python dictionary that can be written to an OSW JSON.

        Specifically, this dictionary can be appended to the "steps" key of the
        OpenStudio Workflow (.osw) JSON dictionary in order to include the measure
        in the workflow.

        Note that this method does not perform any checks to validate that the
        Measure has all required values and only arguments with values will be
        included in the dictionary. Validation should be done separately with
        the validate method.

        Args:
            full_path: Boolean to note whether the full path to the measure should
                be written under the 'measure_dir_name' key or just the measure
                base name. (Default: False)
        """
        meas_dir = self.folder if full_path else os.path.basename(self.folder)
        base = {'measure_dir_name': meas_dir, 'arguments': {}}
        for arg in self._arguments:
            if arg.value is not None:
                base['arguments'][arg.identifier] = arg.value
        return base

    def validate(self, raise_exception=True):
        """Check if all required arguments have values needed for simulation.

        Args:
            raise_exception: If True, an exception will be raised if there's a
                required argument and there is no value. Otherwise, False will
                be returned for this case and True will be returned if all
                is correct.
        """
        for arg in self._arguments:
            if not arg.validate(raise_exception):
                return False
        return True

    @staticmethod
    def sort_measures(measures):
        """Sort measures according to the order they will be executed by OpenStudio CLI.

        ModelMeasures will be first, followed by EnergyPlusMeasures, followed by
        ReportingMeasures.
        """
        m_dict = {'ModelMeasure': [], 'EnergyPlusMeasure': [], 'ReportingMeasure': []}
        for measure in measures:
            m_dict[measure.type].append(measure)
        return m_dict['ModelMeasure'] + m_dict['EnergyPlusMeasure'] + \
            m_dict['ReportingMeasure']

    def _parse_metadata_file(self):
        """Parse measure properties from the measure.xml file."""
        # create an element tree object
        tree = ElementTree.parse(self._metadata_file)
        root = tree.getroot()

        # parse the measure properties from the element tree
        self._identifier = root.find('name').text
        self._display_name = root.find('display_name').text
        self._description = root.find('description').text
        self._type = None
        for atr in root.find('attributes'):
            if atr.find('name').text == 'Measure Type':
                self._type = atr.find('value').text

        # parse the measure arguments
        self._arguments = []
        arg_info = root.find('arguments')
        if arg_info is not None:
            for arg in arg_info:
                arg_obj = MeasureArgument(arg)
                if arg_obj.model_dependent:
                    # TODO: Figure out how to implement model-dependent arguments
                    raise NotImplementedError(
                        'Model dependent arguments are not yet supported and measure '
                        'argument is "{}" model dependent.'.format(arg_obj.identifier))
                self._arguments.append(arg_obj)

    @staticmethod
    def _compress_file(filepath):
        """Compress file contents to a string."""
        # TODO: Research better ways to compress the file
        with open(filepath, 'r') as input_file:
            content = input_file.read()
        return content

    @staticmethod
    def _decompress_to_file(value, filepath):
        """Write file contents to a file."""
        with open(filepath, 'w') as output_file:
            output_file.write(value)

    def __len__(self):
        return len(self._arguments)

    def __getitem__(self, key):
        return self._arguments[key]

    def __iter__(self):
        return iter(self._arguments)

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return 'Measure: {}'.format(self.display_name)


class MeasureArgument(object):
    """Object representing a single measure argument.

    Args:
        xml_element: A Python XML Element object taken from the <arguments> section
            of the measure.xml file.

    Properties:
        * identifier
        * display_name
        * value
        * default_value
        * type
        * type_text
        * required
        * description
        * model_dependent
        * valid_choices
    """
    PYTHON_TYPES = {
        'Double': float,
        'Integer': int,
        'Boolean': bool,
        'String': str,
        'Choice': str
    }

    __slots__ = ('_identifier', '_display_name', '_value', '_default_value',
                 '_type', '_type_text', '_required', '_description',
                 '_model_dependent', '_valid_choices')

    def __init__(self, xml_element):
        """Initialize MeasureArgument."""
        # parse the required properties of the argument
        self._identifier = xml_element.find('name').text
        self._type_text = xml_element.find('type').text
        self._type = self.PYTHON_TYPES[self._type_text]
        required = xml_element.find('required').text
        self._required = True if required == 'true' else False

        # set up the argument value and default value
        self._value = None  # will be set by user
        self._default_value = None  # will be overridden if it is present
        if xml_element.find('default_value') is not None and \
                xml_element.find('default_value').text is not None:
            d_val = xml_element.find('default_value').text
            if self._type_text == 'Boolean':
                self._default_value = True if d_val.lower() == 'true' else False
            else:  # just use the type to cast the text
                self._default_value = self._type(d_val)

        # parse the optional properties of the argument
        self._display_name = xml_element.find('display_name').text \
            if xml_element.find('display_name') is not None else None
        self._description = xml_element.find('description').text \
            if xml_element.find('description') is not None else None
        model_dependent = xml_element.find('model_dependent').text
        self._model_dependent = True if model_dependent == 'true' else False

        # parse any choice arguments if they exist
        self._valid_choices = None
        if self._type_text == 'Choice':
            try:
                self._valid_choices = tuple(choice.find('value').text
                                            for choice in xml_element.find('choices'))
            except TypeError as e:
                raise ValueError(
                    'The measure is invalid. Choice argument was found without any '
                    'available choices.\n{}'.format(e))

    @property
    def identifier(self):
        """Get text for the identifier of the argument.

        This is also called the "name" in the measure.xml file.
        """
        return self._identifier

    @property
    def display_name(self):
        """Get text for the human-readable display name of the argument.

        This is called the "display_name" in the measure.xml file.
        """
        return self._display_name

    @property
    def value(self):
        """Get or set the value for the argument.

        If not set, this will be equal to the default_value and, if no default
        value is included for this argument, it will be None.
        """
        if self._value is not None:
            return self._value
        return self._default_value

    @value.setter
    def value(self, val):
        if val is not None:
            try:
                val = self._type(val)
            except Exception:
                raise TypeError('Value for measure argument "{}" must be a {}. '
                                'Got {}'.format(self.identifier, self._type, type(val)))
            if self._valid_choices:
                assert val in self._valid_choices, 'Choice measure argument "{}" ' \
                    'must be one of the following:\n{}\nGot {}'.format(
                        self.identifier, self._valid_choices, val)
        self._value = val

    @property
    def default_value(self):
        """Get the default value for the argument.

        This may be None if no default value has been included.
        """
        return self._default_value

    @property
    def type(self):
        """Get the Python type of argument this is (eg. float, str, int)."""
        return self._type

    @property
    def type_text(self):
        """Get a text string for the argument type as it appears in the measure.xml.

        (eg. 'Double', 'String', 'Boolean').
        """
        return self._type_text

    @property
    def required(self):
        """Get a boolean for whether this argument is required to run the measure."""
        return self._required

    @property
    def description(self):
        """Get text for describing what the measure does if it exists."""
        return self._description

    @property
    def model_dependent(self):
        """Get a boolean for whether this argument is dependent on the model."""
        return self._model_dependent

    @property
    def valid_choices(self):
        """Get a list of text for valid inputs for choice arguments.

        This will be None if the argument type is not Choice.
        """
        return self._valid_choices

    def validate(self, raise_exception=True):
        """If this argument is required, check that it has a value.

        If this argument is not required, this method will always return True.

        Args:
            raise_exception: If True, an exception will be raised if this argument
                is required and there is no value. Otherwise, False will be returned
                for this case and True will be returned if all is correct.
        """
        if self.required and self.value is None:
            if self._valid_choices != (None,):
                if raise_exception:
                    raise ValueError('Measure argument "{}" is required and missing '
                                     'a value'.format(self.identifier))
                return False
        return True

    def ToString(self):
        return self.__repr__()

    def __repr__(self):
        return '{} <{}> value: {}'.format(self.display_name, self.type_text, self.value)
