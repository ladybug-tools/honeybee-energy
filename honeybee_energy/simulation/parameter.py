# coding=utf-8
"""Complete set of EnergyPlus Simulation Settings."""
from __future__ import division

from .output import SimulationOutput
from .runperiod import RunPeriod
from .control import SimulationControl
from .shadowcalculation import ShadowCalculation
from .sizing import SizingParameter
from ..reader import parse_idf_string
from ..writer import generate_idf_string

from honeybee.typing import int_positive

import re


class SimulationParameter(object):
    """Complete set of EnergyPlus Simulation Settings.

    Args:
        output: A SimulationOutput that lists the desired outputs from the
            simulation and the format in which to report them. If None, no
            outputs will be requested. Default: None.
        run_period: A RunPeriod object to describe the time period over which to
            run the simulation. Default: Run for the whole year starting on Sunday.
        timestep: An integer for the number of timesteps per hour at which the
            calculation will be run. Default: 6.
        simulation_control: A SimulationControl object that describes which types
            of calculations to run. Default: perform a sizing calculation but only
            run the simulation for the RunPeriod.
        shadow_calculation: A ShadowCalculation object describing settings for
            the EnergyPlus Shadow Calculation. Default: Average over 30 days with
            FullInteriorAndExteriorWithReflections.
        sizing_parameter: A SizingParameter object with criteria for sizing the
            heating and cooling system.

    Properties:
        * output
        * run_period
        * timestep
        * simulation_control
        * shadow_calculation
        * sizing_parameter
        * global_geometry_rules
    """
    __slots__ = ('_output', '_run_period', '_timestep', '_simulation_control',
                 '_shadow_calculation', '_sizing_parameter')
    VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)

    def __init__(self, output=None, run_period=None, timestep=6, simulation_control=None,
                 shadow_calculation=None, sizing_parameter=None):
        """Initialize SimulationParameter."""
        self.output = output
        self.run_period = run_period
        self.timestep = timestep
        self.simulation_control = simulation_control
        self.shadow_calculation = shadow_calculation
        self.sizing_parameter = sizing_parameter

    @property
    def output(self):
        """Get or set a SimulationOutput object for the outputs from the simulation."""
        return self._output

    @output.setter
    def output(self, value):
        if value is not None:
            assert isinstance(value, SimulationOutput), 'Expected SimulationOutput for ' \
                'SimulationParameter output. Got {}.'.format(type(value))
            self._output = value
        else:
            self._output = SimulationOutput()

    @property
    def run_period(self):
        """Get or set a RunPeriod object for the time period to run the simulation."""
        return self._run_period

    @run_period.setter
    def run_period(self, value):
        if value is not None:
            assert isinstance(value, RunPeriod), 'Expected RunPeriod for ' \
                'SimulationParameter run_period. Got {}.'.format(type(value))
            self._run_period = value
        else:
            self._run_period = RunPeriod()

    @property
    def timestep(self):
        """Get or set a integer for the number of days with unique shadow calculations.
        """
        return self._timestep

    @timestep.setter
    def timestep(self, value):
        value = int_positive(value, 'simulation parameter timestep')
        assert value in self.VALIDTIMESTEPS, 'SimulationParameter timestep "{}" is ' \
            'invalid. Must be one of the following:{}'.format(value, self.VALIDTIMESTEPS)
        self._timestep = value

    @property
    def simulation_control(self):
        """Get or set a SimulationControl object for which types of calculations to run.
        """
        return self._simulation_control

    @simulation_control.setter
    def simulation_control(self, value):
        if value is not None:
            assert isinstance(value, SimulationControl), 'Expected SimulationControl ' \
                'for SimulationParameter run_period. Got {}.'.format(type(value))
            self._simulation_control = value
        else:
            self._simulation_control = SimulationControl()

    @property
    def shadow_calculation(self):
        """Get or set a ShadowCalculation object with settings for the shadow calculation.
        """
        return self._shadow_calculation

    @shadow_calculation.setter
    def shadow_calculation(self, value):
        if value is not None:
            assert isinstance(value, ShadowCalculation), 'Expected ShadowCalculation ' \
                'for SimulationParameter shadow_calculation. Got {}.'.format(type(value))
            self._shadow_calculation = value
        else:
            self._shadow_calculation = ShadowCalculation()

    @property
    def sizing_parameter(self):
        """Get or set a SizingParameter object with factors for the peak loads."""
        return self._sizing_parameter

    @sizing_parameter.setter
    def sizing_parameter(self, value):
        if value is not None:
            assert isinstance(value, SizingParameter), 'Expected SizingParameter ' \
                'for SimulationParameter sizing_parameter. Got {}.'.format(type(value))
            self._sizing_parameter = value
        else:
            self._sizing_parameter = SizingParameter()

    @property
    def global_geometry_rules(self):
        """Get an IDF string for the official honeybee global geometry rules.

        Specifically, these are counter-clockwise vertices starting from the
        upper left corner of the surface. The output string is the following:

        .. code-block:: python

            GlobalGeometryRules,
             UpperLeftCorner,          !- starting vertex position
             Counterclockwise,         !- vertex entry direction
             Relative;                 !- coordinate system
        """
        values = ('UpperLeftCorner', 'Counterclockwise', 'Relative')
        comments = ('starting vertex position', 'vertex entry direction',
                    'coordinate system')
        return generate_idf_string('GlobalGeometryRules', values, comments)

    @classmethod
    def from_idf(cls, idf_string):
        """Create a SimulationParameter object from an EnergyPlus IDF text string.

        Args:
            idf_string: A text string with all IDF objects that should be included
                in the resulting SimulationParameter object. Note that, unlike other
                from_idf methods throughout honeybee_energy, this method can have
                multiple IDF objects within the idf_string. Any object in the idf_string
                that is not relevant to SimulationParameter will be ignored by this
                method. So the input idf_string can simply be the entire file contents
                of an IDF.
        """
        # Regex patterns for the varios objects comprising the SimulationParameter
        out_style_pattern = re.compile(r"(?i)(OutputControl:Table:Style,[\s\S]*?;)")
        out_var_pattern = re.compile(r"(?i)(Output:Variable,[\s\S]*?;)")
        out_report_pattern = re.compile(r"(?i)(Output:Table:SummaryReports,[\s\S]*?;)")
        sqlite_pattern = re.compile(r"(?i)(Output:SQLite,[\s\S]*?;)")
        runper_pattern = re.compile(r"(?i)(RunPeriod,[\s\S]*?;)")
        holiday_pattern = re.compile(r"(?i)(RunPeriodControl:SpecialDays,[\s\S]*?;)")
        dls_pattern = re.compile(r"(?i)(RunPeriodControl:DaylightSavingTime,[\s\S]*?;)")
        timestep_pattern = re.compile(r"(?i)(Timestep,[\s\S]*?;)")
        sh_calc_pattern = re.compile(r"(?i)(ShadowCalculation,[\s\S]*?;)")
        bldg_pattern = re.compile(r"(?i)(Building,[\s\S]*?;)")
        control_pattern = re.compile(r"(?i)(SimulationControl,[\s\S]*?;)")
        sizing_pattern = re.compile(r"(?i)(Sizing:Parameters,[\s\S]*?;)")
        ddy_p = re.compile(r"(SizingPeriod:DesignDay,(.|\n)*?((;\s*!)|(;\s*\n)|(;\n)))")
        loc_pattern = re.compile(r"(?i)(Site:Location,[\s\S]*?;)")

        # process the outputs within the idf_string
        try:
            out_style_str = out_style_pattern.findall(idf_string)[0]
        except IndexError:  # No Table:Style in the file.
            out_style_str = None
        try:
            out_report_str = out_report_pattern.findall(idf_string)[0]
        except IndexError:  # No SummaryReports in the file. Default to None.
            out_report_str = None
        sqlite = True if len(sqlite_pattern.findall(idf_string)) != 0 else False
        output = SimulationOutput.from_idf(
            out_style_str, out_var_pattern.findall(idf_string), out_report_str, sqlite)

        # process the RunPeriod within the idf_string
        try:
            run_period_str = runper_pattern.findall(idf_string)[0]
        except IndexError:  # No RunPeriod in the file. Default to the whole year.
            run_period_str = None
            run_period = None
        if run_period_str is not None:
            holidays_str = holiday_pattern.findall(idf_string)
            if len(holidays_str) == 0:
                holidays_str = None
            try:
                dls_str = dls_pattern.findall(idf_string)[0]
            except IndexError:  # No DalyightSavingTime in the file.
                dls_str = None
            run_period = RunPeriod.from_idf(run_period_str, holidays_str, dls_str)

        # process the Timestep within the idf_string
        try:
            timestep_str = timestep_pattern.findall(idf_string)[0]
            timestep = int(parse_idf_string(timestep_str)[0])
        except IndexError:  # No Timestep in the file. Default to 6.
            timestep = 6

        # process the SimulationControl within the idf_string
        try:
            sim_control_str = control_pattern.findall(idf_string)[0]
            sim_control = SimulationControl.from_idf(sim_control_str)
        except IndexError:  # No SimulationControl in the file.
            sim_control = None

        # process the ShadowCalculation within the idf_string
        try:
            sh_calc_str = sh_calc_pattern.findall(idf_string)[0]
        except IndexError:  # No ShadowCalculation in the file.
            sh_calc_str = None
            shadow_calc = None
        if sh_calc_str is not None:
            try:
                bldg_str = bldg_pattern.findall(idf_string)[0]
                solar_dist = bldg_str[5] if bldg_str[5] != '' else 'FullExterior'
            except IndexError:  # No Building in the file. Use honeybee default.
                solar_dist = 'FullInteriorAndExteriorWithReflections'
            shadow_calc = ShadowCalculation.from_idf(sh_calc_str, solar_dist)

        # process the SizingParameter within the idf_string
        try:
            sizing_str = sizing_pattern.findall(idf_string)[0]
        except IndexError:  # No Sizing:Parameters in the file.
            sizing_str = None
        try:
            location = loc_pattern.findall(idf_string)[0]
        except IndexError:  # No Site:Location in the file.
            location = None
        sizing_par = SizingParameter.from_idf([dy[0] for dy in ddy_p.findall(idf_string)],
                                              sizing_str, location)

        return cls(output, run_period, timestep, sim_control, shadow_calc, sizing_par)

    @classmethod
    def from_dict(cls, data):
        """Create a SimulationParameter object from a dictionary.

        Args:
            data: A SimulationParameter dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SimulationParameter",
            "output": {}, # Honeybee SimulationOutput disctionary
            "run_period": {}, # Honeybee RunPeriod disctionary
            "timestep": 6, # Integer for the simulation timestep
            "simulation_control": {}, # Honeybee SimulationControl dictionary
            "shadow_calculation": {}, # Honeybee ShadowCalculation dictionary
            "sizing_parameter": {} # Honeybee SizingParameter dictionary
            }
        """
        assert data['type'] == 'SimulationParameter', \
            'Expected SimulationParameter dictionary. Got {}.'.format(data['type'])

        timestep = data['timestep'] if 'timestep' in data else 6
        output = None
        if 'output' in data and data['output'] is not None:
            output = SimulationOutput.from_dict(data['output'])
        run_period = None
        if 'run_period' in data and data['run_period'] is not None:
            run_period = RunPeriod.from_dict(data['run_period'])
        simulation_control = None
        if 'simulation_control' in data and data['simulation_control'] is not None:
            simulation_control = SimulationControl.from_dict(data['simulation_control'])
        shadow_calculation = None
        if 'shadow_calculation' in data and data['shadow_calculation'] is not None:
            shadow_calculation = ShadowCalculation.from_dict(data['shadow_calculation'])
        sizing_parameter = None
        if 'sizing_parameter' in data and data['sizing_parameter'] is not None:
            sizing_parameter = SizingParameter.from_dict(data['sizing_parameter'])

        return cls(output, run_period, timestep, simulation_control,
                   shadow_calculation, sizing_parameter)

    def to_idf(self):
        """Get an EnergyPlus string representation of the SimulationParameter.

        Note that this string is a concatenation of the IDF strings for all of the
        objects that make up the SimulationParameter (ie. RunPeriod, SimulationControl,
        etc.),
        """
        sim_param_str = ['!-   ==========================================\n'
                         '!-   =========  SIMULATION PARAMETERS =========\n'
                         '!-   ==========================================\n']

        # add the outputs requested
        table_style, output_vars, reports, sqlite, rdd, surfaces = self.output.to_idf()
        sim_param_str.append(table_style)
        if output_vars is not None:
            sim_param_str.append('\n\n'.join(output_vars))
        if reports is not None:
            sim_param_str.append(reports)
        if sqlite is not None:
            sim_param_str.append(sqlite)
        sim_param_str.append(rdd)
        sim_param_str.append(surfaces)

        # add simulation settings
        sim_param_str.append(self.simulation_control.to_idf())
        sim_param_str.append(self.shadow_calculation.to_idf())
        sim_param_str.append(generate_idf_string(
            'Timestep', [self.timestep], ['timesteps per hour']))

        # add the run period
        run_period_str, holidays, daylight_saving = self.run_period.to_idf()
        sim_param_str.append(run_period_str)
        if holidays is not None:
            sim_param_str.append('\n\n'.join(holidays))
        if daylight_saving is not None:
            sim_param_str.append(daylight_saving)

        # write the sizing parameters
        design_days, siz_par = self.sizing_parameter.to_idf()
        if len(design_days) != 0:
            sim_param_str.append('\n\n'.join(design_days))
        sim_param_str.append(siz_par)

        # write the global geometry rules
        sim_param_str.append(self.global_geometry_rules)

        return '\n\n'.join(sim_param_str)

    def to_dict(self):
        """SimulationParameter dictionary representation."""
        return {
            'type': 'SimulationParameter',
            'output': self.output.to_dict(),
            'run_period': self.run_period.to_dict(),
            'timestep': self.timestep,
            'simulation_control': self.simulation_control.to_dict(),
            'shadow_calculation': self.shadow_calculation.to_dict(),
            'sizing_parameter': self.sizing_parameter.to_dict()
        }

    def duplicate(self):
        """Get a copy of this object."""
        return self.__copy__()

    def ToString(self):
        """Overwrite .NET ToString."""
        return self.__repr__()

    def __copy__(self):
        return SimulationParameter(
            self.output.duplicate(), self.run_period.duplicate(), self.timestep,
            self.simulation_control.duplicate(), self.shadow_calculation.duplicate(),
            self.sizing_parameter.duplicate())

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self.output), hash(self.run_period), self.timestep,
                hash(self.simulation_control),
                hash(self.shadow_calculation), hash(self.sizing_parameter))

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SimulationParameter) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Energy SimulationParameter:'
