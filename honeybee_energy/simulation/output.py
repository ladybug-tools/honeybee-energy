# coding=utf-8
"""Object to hold EnergyPlus simulation outputs."""
from __future__ import division

from honeybee.typing import float_in_range

from ..reader import parse_idf_string
from ..writer import generate_idf_string


class SimulationOutput(object):
    """Object to hold EnergyPlus simulation outputs.

    Args:
        outputs: A list of EnergyPlus output names as strings, which are requested
            from the simulation. If None, no outputs will be requested.
            Note that this object does not check whether the outputs exist
            within the EnergyPlus IDD or are request-able from a given Model.
            (eg. ['Zone Ideal Loads Supply Air Total Cooling Energy']).
            Default: None.
        reporting_frequency: Text for the frequency at which the outputs
            are reported. Default: 'Hourly'.
            Choose from the following:

            * Annual
            * Monthly
            * Daily
            * Hourly
            * Timestep

        include_sqlite: Boolean to note whether a SQLite report should be
            generated from the simulation, which contains all of the outputs and
            summary_reports. Default: True.
        include_html: Boolean to note whether an HTML report should be generated
            from the simulation, which contains all of the summary_reports.
            Default: True.
        summary_reports: An array of EnergyPlus summary report names as strings.
            An empty list or None will result in no summary reports.
            Default: ('AllSummary',). See the Input Output Reference SummaryReports
            section for a full list of all reports that can be requested.
            (https://bigladdersoftware.com/epx/docs/9-1/input-output-reference/\
output-table-summaryreports.html#outputtablesummaryreports).
        unmet_setpoint_tolerance: A number in degrees Celsius for the difference that
            the zone conditions must be from the thermostat setpoint in order
            for the setpoint to be considered unmet. This will affect how unmet
            hours are reported in the output. ASHRAE 90.1 uses a tolerance of
            1.11C, which is equivalent to 1.8F. (Default: 1.11C).

    Properties:
        * outputs
        * reporting_frequency
        * include_sqlite
        * include_html
        * summary_reports
        * unmet_setpoint_tolerance
    """
    __slots__ = ('_outputs', '_reporting_frequency', '_include_sqlite',
                 '_include_html', '_summary_reports', '_unmet_setpoint_tolerance')
    REPORTING_FREQUENCIES = ('Annual', 'Monthly', 'Daily', 'Hourly', 'Timestep')

    def __init__(self, outputs=None, reporting_frequency='Hourly', include_sqlite=True,
                 include_html=True, summary_reports=('AllSummary',),
                 unmet_setpoint_tolerance=1.11):
        """Initialize SimulationOutput."""
        self.outputs = outputs
        self.reporting_frequency = reporting_frequency
        self.include_sqlite = include_sqlite
        self.include_html = include_html
        self.summary_reports = summary_reports
        self.unmet_setpoint_tolerance = unmet_setpoint_tolerance

    @property
    def outputs(self):
        """Get or set a tuple of EnergyPlus output names as strings.

        These outputs will be requested from the simulation and, if None,
        no outputs will be requested.
        """
        return tuple(sorted(self._outputs))

    @outputs.setter
    def outputs(self, value):
        if value is not None:
            assert not isinstance(value, (str, bytes)), 'Expected list or tuple for ' \
                'SimulationOutput outputs. Got {}.'.format(type(value))
            vals = []
            for output in value:
                vals.append(str(output))
            value = set(vals)
        else:
            value = set()
        self._outputs = value

    @property
    def reporting_frequency(self):
        """Get or set text for the frequency at which the outputs are reported.

        Choose from the following:

        * Annual
        * Monthly
        * Daily
        * Hourly
        * Timestep
        """
        return self._reporting_frequency

    @reporting_frequency.setter
    def reporting_frequency(self, value):
        value = value.title()
        assert value in self.REPORTING_FREQUENCIES, 'reporting_frequency {} ' \
            'is not recognized.\nChoose from the following:\n{}'.format(
                value, self.REPORTING_FREQUENCIES)
        self._reporting_frequency = value

    @property
    def include_sqlite(self):
        """Get or set a boolean for whether a SQLite report should be generated."""
        return self._include_sqlite

    @include_sqlite.setter
    def include_sqlite(self, value):
        self._include_sqlite = bool(value)

    @property
    def include_html(self):
        """Get or set a boolean for whether an HTML report should be generated."""
        return self._include_html

    @include_html.setter
    def include_html(self, value):
        self._include_html = bool(value)

    @property
    def summary_reports(self):
        """Get or set a tuple of EnergyPlus summary report names as strings.

        These reports will be requested from the simulation and, if None,
        no summary reports will be written.
        """
        return tuple(sorted(self._summary_reports))

    @summary_reports.setter
    def summary_reports(self, value):
        if value is not None:
            assert not isinstance(value, (str, bytes)), 'Expected list, tuple, or ' \
                'set for SimulationOutput summary_reports. Got {}.'.format(type(value))
            vals = []
            for output in value:
                vals.append(str(output))
            value = set(vals)
        else:
            value = set(('AllSummary',))
        self._summary_reports = value

    @property
    def unmet_setpoint_tolerance(self):
        """Get or set a number in Celsius for the tolerance of unmet conditions."""
        return self._unmet_setpoint_tolerance
    
    @unmet_setpoint_tolerance.setter
    def unmet_setpoint_tolerance(self, value):
        self._unmet_setpoint_tolerance = \
            float_in_range(value, 0, 10, 'unmet setpoint tolerance')

    def add_summary_report(self, report_name):
        """Add another summary report to the list of requested reports.

        See the Input Output Reference SummaryReports
        section for a full list of all reports that can be requested.
        (https://bigladdersoftware.com/epx/docs/9-1/input-output-reference/\
output-table-summaryreports.html#outputtablesummaryreports)

        Args:
            report_name: The name of an EnergyPlus simulation report to be requested
                from the model. Note that this method does not check whether the
                output exists within the EnergyPlus IDD.
                (eg. 'AnnualBuildingUtilityPerformanceSummary').
        """
        assert isinstance(report_name, str), \
            'SummaryReport {} is not valid'.format(report_name)
        self._summary_reports.add(report_name)

    def add_output(self, output_name):
        """Add another output to the list of requested outputs.

        Args:
            output_name: The name of an EnergyPlus output that is requested
                from the simulation. Note that this method does not check whether
                the output exists within the EnergyPlus IDD or are request-able
                from a given Model.
                (eg. 'Zone Ideal Loads Supply Air Total Cooling Energy').
        """
        self._outputs.add(str(output_name))

    def add_zone_energy_use(self, load_type='All'):
        """Add outputs for zone energy use when ideal air loads are assigned.

        This includes, ideal air heating + cooling, lighting, electric + gas
        equipment, and fan electric energy.

        Args:
            load_type: A text value to set the type of load outputs requested.
                Default: 'All'. Choose from the following:

                * All - all energy use including heat lost from the zone
                * Total - total load added/removed from the zone (sensible + latent)
                * Sensible - sensible load added/removed to the zone
                * Latent - latent load added/removed to the zone
        """
        load_type = load_type.title()
        if load_type == 'All':
            outputs = ['Zone Ideal Loads Supply Air Total Cooling Energy',
                       'Zone Ideal Loads Supply Air Total Heating Energy',
                       'Zone Lights Electricity Energy',
                       'Zone Electric Equipment Electricity Energy',
                       'Zone Gas Equipment NaturalGas Energy',
                       'Zone Ventilation Fan Electricity Energy',
                       'Water Use Equipment Heating Energy',
                       'Zone Other Equipment Total Heating Energy',
                       'Zone Other Equipment Lost Heat Energy']
        elif load_type == 'Total':
            outputs = ['Zone Ideal Loads Supply Air Total Cooling Energy',
                       'Zone Ideal Loads Supply Air Total Heating Energy',
                       'Zone Lights Total Heating Energy',
                       'Zone Electric Equipment Total Heating Energy',
                       'Zone Gas Equipment Total Heating Energy',
                       'Water Use Equipment Zone Sensible Heat Gain Energy',
                       'Water Use Equipment Zone Latent Gain Energy',
                       'Zone Other Equipment Total Heating Energy']
        elif load_type == 'Sensible':
            outputs = ['Zone Ideal Loads Supply Air Sensible Cooling Energy',
                       'Zone Ideal Loads Supply Air Sensible Heating Energy',
                       'Zone Lights Total Heating Energy',
                       'Zone Electric Equipment Radiant Heating Energy',
                       'Zone Electric Equipment Convective Heating Energy',
                       'Zone Gas Equipment Radiant Heating Energy',
                       'Zone Gas Equipment Convective Heating Energy',
                       'Water Use Equipment Zone Sensible Heat Gain Energy',
                       'Zone Other Equipment Convective Heating Energy',
                       'Zone Other Equipment Radiant Heating Energy']
        elif load_type == 'Latent':
            outputs = ['Zone Ideal Loads Supply Air Latent Cooling Energy',
                       'Zone Ideal Loads Supply Air Latent Heating Energy',
                       'Zone Electric Equipment Latent Gain Energy',
                       'Zone Gas Equipment Latent Gain Energy',
                       'Water Use Equipment Zone Latent Gain Energy',
                       'Zone Other Equipment Latent Heating Energy']
        else:
            raise ValueError('load_type {} is not valid'.format(load_type))
        for outp in outputs:
            self._outputs.add(outp)

    def add_hvac_energy_use(self):
        """Add outputs for HVAC energy use when detailed systems are assigned.

        This includes a range of outputs for different pieces of equipment,
        which is meant to catch all energy-consuming parts of a system.
        (eg. chillers, boilers, coils, humidifiers, fans, pumps).
        """
        outputs = ['Cooling Coil Electricity Energy',
                   'Chiller Electricity Energy',
                   'Boiler NaturalGas Energy',
                   'Heating Coil Total Heating Energy',
                   'Heating Coil NaturalGas Energy',
                   'Heating Coil Electricity Energy',
                   'Humidifier Electricity Energy',
                   'Fan Electricity Energy',
                   'Cooling Tower Fan Electricity Energy',
                   'Pump Electricity Energy',
                   'Zone VRF Air Terminal Cooling Electricity Energy',
                   'Zone VRF Air Terminal Heating Electricity Energy',
                   'VRF Heat Pump Cooling Electricity Energy',
                   'VRF Heat Pump Heating Electricity Energy',
                   'VRF Heat Pump Defrost Electricity Energy',
                   'VRF Heat Pump Crankcase Heater Electricity Energy',
                   'Chiller Heater System Cooling Electricity Energy',
                   'Chiller Heater System Heating Electricity Energy',
                   'District Cooling Water Energy',
                   'District Heating Water Energy',
                   'Baseboard Electricity Energy',
                   'Evaporative Cooler Electricity Energy',
                   'Hot_Water_Loop_Central_Air_Source_Heat_Pump Electricity Consumption',
                   'Boiler Electricity Energy',
                   'Water Heater NaturalGas Energy',
                   'Water Heater Electricity Energy',
                   'Cooling Coil Water Heating Electricity Energy']
        for outp in outputs:
            self._outputs.add(outp)

    def add_gains_and_losses(self, load_type='Total'):
        """Add outputs for zone gains and losses.

        This includes such as people gains, solar gains, infiltration losses/gains,
        and ventilation losses/gains.

        Args:
            load_type: A text value to set the type of load outputs requested.
                Default: 'Total'. Choose from the following:

                * Total - the total load added to the zone (both sensible and latent)
                * Sensible - the sensible load added to the zone
                * Latent - the latent load added to the zone
        """
        load_type = load_type.title()
        always_sensible = ['Zone Windows Total Transmitted Solar Radiation Energy',
                           'AFN Zone Infiltration Sensible Heat Gain Energy',
                           'AFN Zone Infiltration Sensible Heat Loss Energy',
                           'AFN Zone Ventilation Sensible Heat Gain Energy',
                           'AFN Zone Ventilation Sensible Heat Loss Energy']
        if load_type == 'Total':
            outputs = ['Zone People Total Heating Energy',
                       'Zone Ideal Loads Zone Total Heating Energy',
                       'Zone Ideal Loads Zone Total Cooling Energy',
                       'Zone Infiltration Total Heat Loss Energy',
                       'Zone Infiltration Total Heat Gain Energy',
                       'Zone Ventilation Sensible Heat Gain Energy',
                       'Zone Ventilation Latent Heat Gain Energy',
                       'Zone Ventilation Sensible Heat Loss Energy',
                       'Zone Ventilation Latent Heat Loss Energy'] + always_sensible
        elif load_type == 'Sensible':
            outputs = ['Zone People Sensible Heating Energy',
                       'Zone Ventilation Sensible Heat Loss Energy',
                       'Zone Ventilation Sensible Heat Gain Energy',
                       'Zone Ideal Loads Zone Sensible Heating Energy',
                       'Zone Ideal Loads Zone Sensible Cooling Energy',
                       'Zone Infiltration Sensible Heat Loss Energy',
                       'Zone Infiltration Sensible Heat Gain Energy'] + always_sensible
        elif load_type == 'Latent':
            outputs = ['Zone People Latent Gain Energy',
                       'Zone Ventilation Latent Heat Loss Energy',
                       'Zone Ventilation Latent Heat Gain Energy',
                       'Zone Ideal Loads Zone Latent Heating Energy',
                       'Zone Ideal Loads Zone Latent Cooling Energy',
                       'Zone Infiltration Latent Heat Loss Energy',
                       'Zone Infiltration Latent Heat Gain Energy',
                       'AFN Zone Infiltration Latent Heat Loss Energy',
                       'AFN Zone Infiltration Latent Heat Gain Energy',
                       'AFN Zone Ventilation Latent Heat Gain Energy',
                       'AFN Zone Ventilation Latent Heat Loss Energy']
        else:
            raise ValueError('load_type {} is not valid'.format(load_type))
        for outp in outputs:
            self._outputs.add(outp)

    def add_electricity_generation(self):
        """Add outputs related to on-site electricity generation."""
        outputs = ['Facility Total Produced Electricity Energy',
                   'Facility Net Purchased Electricity Energy',
                   'Generator Produced DC Electricity Energy']
        for outp in outputs:
            self._outputs.add(outp)

    def add_comfort_metrics(self):
        """Add outputs for zone thermal comfort analysis.

        This includes air temperature, mean radiant temperature, relative
        humidity.
        """
        outputs = ['Zone Operative Temperature',
                   'Zone Mean Air Temperature',
                   'Zone Mean Radiant Temperature',
                   'Zone Air Relative Humidity']
        for outp in outputs:
            self._outputs.add(outp)

    def add_unmet_hours(self):
        """Add outputs for time that the heating/cooling setpoints are not met."""
        outputs = ['Zone Heating Setpoint Not Met Time',
                   'Zone Cooling Setpoint Not Met Time']
        for outp in outputs:
            self._outputs.add(outp)

    def add_surface_temperature(self):
        """Add outputs for indoor and outdoor surface temperature."""
        outputs = ['Surface Outside Face Temperature',
                   'Surface Inside Face Temperature']
        for outp in outputs:
            self._outputs.add(outp)

    def add_surface_energy_flow(self):
        """Add outputs for energy flow across all surfaces."""
        outputs = ['Surface Inside Face Conduction Heat Transfer Energy',
                   'Surface Window Heat Loss Energy',
                   'Surface Window Heat Gain Energy']
        for outp in outputs:
            self._outputs.add(outp)

    def add_glazing_solar(self):
        """Add outputs for the transmitted solar gain through individual window surfaces.

        This includes transmitted beam, diffuse, and total solar gain.
        """
        outputs = ['Surface Window Transmitted Beam Solar Radiation Energy',
                   'Surface Window Transmitted Diffuse Solar Radiation Energy',
                   'Surface Window Transmitted Solar Radiation Energy']
        for outp in outputs:
            self._outputs.add(outp)

    def add_stratification_variables(self):
        """Add outputs for estimating stratification across a zone.

        This includes all air flow into the zone as well as all heat gain
        to the air.
        """
        outputs = ['Zone Ventilation Standard Density Volume Flow Rate',
                   'Zone Infiltration Standard Density Volume Flow Rate',
                   'Zone Mechanical Ventilation Standard Density Volume Flow Rate',
                   'Zone Air Heat Balance Internal Convective Heat Gain Rate',
                   'Zone Air Heat Balance Surface Convection Rate',
                   'Zone Air Heat Balance System Air Transfer Rate']
        for outp in outputs:
            self._outputs.add(outp)

    def add_energy_balance_variables(self, load_type='Total'):
        """Add all outputs needed to generate complete energy balance graphics.

        This includes zone energy use, zone gains and losses, and surface energy flow.

        Args:
            load_type: A text value to set the type of load outputs requested.
                Default: 'Total'. Choose from the following:

                * Total - the total load added to the zone (both sensible and latent)
                * Sensible - the sensible load added to the zone
                * Latent - the latent load added to the zone
        """
        self.add_zone_energy_use(load_type)
        self.add_gains_and_losses(load_type)
        self.add_surface_energy_flow()

    def add_comfort_map_variables(self, include_stratification=True):
        """Add all outputs needed to generate detailed thermal comfort maps.

        This includes zone air temperatures, surface temperatures, and
        stratification variables.

        Args:
            include_stratification: Boolean to note whether stratification variables
                should be included.
        """
        outputs = ['Zone Mean Air Temperature', 'Zone Air Relative Humidity']
        for outp in outputs:
            self._outputs.add(outp)
        self.add_surface_temperature()
        if include_stratification:
            self.add_stratification_variables()

    @classmethod
    def from_idf(cls, table_style=None, output_variables=None, summary_reports=None,
                 reporting_tolerance=None, include_sqlite=True):
        """Create a RunPeriod object from an EnergyPlus IDF text string.

        Args:
            table_style: An IDF OutputControl:Table:Style string.
            output_variables: A list of IDF Output:Variable strings for the requested
                outputs. If None, no outputs will be been requested.
            summary_reports: An IDF Output:Table:SummaryReports string listing
                the summary reports that are requested. If None, no summary
                reports will be requested.
            reporting_tolerance: An IDF OutputControl:ReportingTolerances string.
            include_sqlite: Boolean to note whether a SQLite report should be
                generated from the simulation, which contains all of the outputs and
                summary_reports. Default: True.
        """
        # extract the table_style
        include_html = True
        if table_style is not None:
            style_strs = parse_idf_string(table_style, 'OutputControl:Table:Style,')
            try:
                include_html = True if 'HTML' in style_strs[0].upper() else False
            except IndexError:
                pass  # shorter Table:Style without separator

        # extract the unmet hours reporting tolerance
        unmet_tol = 1.11
        if reporting_tolerance is not None:
            tol_str = parse_idf_string(
                reporting_tolerance, 'OutputControl:ReportingTolerances,')
            try:
                unmet_tol = float(tol_str[0])
            except (IndexError, ValueError, TypeError):
                unmet_tol = 0.2  # shorter ReportingTolerances with default value

        # extract the output_variables
        outputs = None
        frequency = 'Hourly'
        if output_variables is not None:
            outputs = []
            for out_str in output_variables:
                ep_out_str = parse_idf_string(out_str, 'Output:Variable,')
                outputs.append(ep_out_str[1])
                try:
                    frequency = ep_out_str[2] if ep_out_str[2] != '' else 'Hourly'
                except IndexError:
                    pass  # shorter output variable with default hourly frequency

        # extract the summary_reports
        reports = None
        if summary_reports is not None:
            reports = parse_idf_string(summary_reports, 'Output:Table:SummaryReports,')

        return cls(outputs, frequency, include_sqlite, include_html, reports, unmet_tol)

    @classmethod
    def from_dict(cls, data):
        """Create a SimulationOutput object from a dictionary.

        Args:
            data: A SimulationOutput dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SimulationOutput",
            "outputs": ['Zone Ideal Loads Supply Air Total Cooling Energy'],
            "reporting_frequency": 'Annual',
            "include_sqlite": True,
            "include_html": True,
            "summary_reports": ['AllSummary', 'AnnualBuildingUtilityPerformanceSummary'],
            "unmet_setpoint_tolerance": 0.2
            }
        """
        assert data['type'] == 'SimulationOutput', \
            'Expected SimulationOutput dictionary. Got {}.'.format(data['type'])
        outputs = data['outputs'] if 'outputs' in data else None
        frequency = data['reporting_frequency'] if \
            'reporting_frequency' in data else 'Hourly'
        sqlite = data['include_sqlite'] if 'include_sqlite' in data and \
            data['include_sqlite'] is not None else True
        html = data['include_html'] if 'include_html' in data and \
            data['include_html'] is not None else True
        reports = data['summary_reports'] if 'summary_reports' in data else None
        unmet_tol = data['unmet_setpoint_tolerance'] \
            if 'unmet_setpoint_tolerance' in data else 1.11
        return cls(outputs, frequency, sqlite, html, reports, unmet_tol)

    def to_idf(self):
        """Get EnergyPlus string representations of the SimulationOutput.

        Returns:
            A tuple with six elements

            -   table_style: An IDF OutputControl:Table:Style string for the simulation.

            -   output_variables: A list of IDF Output:Variable strings for the requested
                outputs. Will be None if no outputs have been requested.

            -   summary_reports: An IDF Output:Table:SummaryReports string
                listing the summary reports that are requested. Will be None
                if no summary reports have not been requested.

            -   sqlite: An IDF Output:SQLite string to request the SQLite file from
                the simulation. Will be None if include_sqlite is False.

            -   variable_dictionary: An IDF Output:VariableDictionary string, which
                will ensure that a .rdd file is generated from the simulation.

            -   unmet_tolerance: An IDF OutputControl:ReportingTolerances string to
                pass the unmet setpoint tolerance to the IDF file.
        """
        style = 'CommaAndHTML' if self.include_html else 'Comma'
        table_style = generate_idf_string(
            'OutputControl:Table:Style',
            (style, 'None'), ('column separator', 'unit conversion'))
        output_variables = [self._output_to_idf(out_p) for out_p in self.outputs] if \
            len(self._outputs) != 0 else None
        r_comments = ['report {}'.format(i) for i in range(len(self._summary_reports))]
        summary_reports = generate_idf_string(
            'Output:Table:SummaryReports', self.summary_reports, r_comments) if \
            len(self._summary_reports) != 0 else None
        sqlite = generate_idf_string(
            'Output:SQLite', ('SimpleAndTabular',), ('option type',)) if \
            self.include_sqlite else None
        variable_dictionary = generate_idf_string(
            'Output:VariableDictionary', ('IDF', 'Unsorted'),
            ('key field', 'sort option'))
        unmet_tolerance = generate_idf_string(
            'OutputControl:ReportingTolerances',
            (self.unmet_setpoint_tolerance, self.unmet_setpoint_tolerance),
            ('heating unmet setpoint tolerance', 'cooling unmet setpoint tolerance'))
        return table_style, output_variables, summary_reports, sqlite, \
            variable_dictionary, unmet_tolerance

    def to_dict(self):
        """DaylightSavingTime dictionary representation."""
        base = {'type': 'SimulationOutput',
                'reporting_frequency': self.reporting_frequency}
        if not self.include_sqlite:
            base['include_sqlite'] = False
        if not self.include_html:
            base['include_html'] = False
        if len(self._outputs) != 0:
            base['outputs'] = self.outputs
        if len(self._summary_reports) != 0:
            base['summary_reports'] = self.summary_reports
        if self.unmet_setpoint_tolerance != 1.11:
            base['unmet_setpoint_tolerance'] = self.unmet_setpoint_tolerance
        return base

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def _output_to_idf(self, output_name):
        """Convert an output name to an IDF Output:Variable string."""
        values = ('*', output_name, self.reporting_frequency)
        comments = ('key value', 'name', 'frequency')
        return generate_idf_string('Output:Variable', values, comments)

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SimulationOutput(
            self._outputs, self.reporting_frequency, self.include_sqlite,
            self.include_html, self._summary_reports, self.unmet_setpoint_tolerance)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return self.outputs + self.summary_reports + \
            (self.reporting_frequency, self.include_sqlite, self.include_html,
             self.unmet_setpoint_tolerance)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SimulationOutput) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'SimulationOutput:\n {}'.format('\n '.join(self.outputs))
