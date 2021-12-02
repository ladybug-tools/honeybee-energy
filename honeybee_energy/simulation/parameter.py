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

from honeybee.typing import int_positive, float_in_range
from ladybug_geometry.geometry2d.pointvector import Vector2D

import re
import math


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
        north_angle: North angle in degrees. A number between -360 and 360 for the
            counterclockwise difference between the North and the positive Y-axis in
            degrees. 90 is West and 270 is East (Default: 0).
        terrain_type: Text for the terrain type in which the model sits.
            Choose from: 'Ocean', 'Country', 'Suburbs', 'Urban', 'City'.(Default: 'City')

    Properties:
        * output
        * run_period
        * timestep
        * simulation_control
        * shadow_calculation
        * sizing_parameter
        * global_geometry_rules
        * north_angle
        * north_vector
        * terrain_type
    """
    __slots__ = ('_output', '_run_period', '_timestep', '_simulation_control',
                 '_shadow_calculation', '_sizing_parameter', '_north_angle',
                 '_north_vector', '_terrain_type')
    VALIDTIMESTEPS = (1, 2, 3, 4, 5, 6, 10, 12, 15, 20, 30, 60)
    TERRAIN_TYPES = ('Ocean', 'Country', 'Suburbs', 'Urban', 'City')

    def __init__(self, output=None, run_period=None, timestep=6,
                 simulation_control=None, shadow_calculation=None, sizing_parameter=None,
                 north_angle=0, terrain_type='City'):
        """Initialize SimulationParameter."""
        self.output = output
        self.run_period = run_period
        self.timestep = timestep
        self.simulation_control = simulation_control
        self.shadow_calculation = shadow_calculation
        self.sizing_parameter = sizing_parameter
        self.north_angle = north_angle
        self.terrain_type = terrain_type

    @property
    def output(self):
        """Get or set a SimulationOutput object for the outputs from the simulation."""
        return self._output

    @output.setter
    def output(self, value):
        if value is not None:
            assert isinstance(value, SimulationOutput), 'Expected SimulationOutput ' \
                'for SimulationParameter output. Got {}.'.format(type(value))
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
        """Get or set a integer for the number of simulation timesteps per hour."""
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

    @property
    def north_angle(self):
        """Get or set a number between -360 and 360 for the north direction in degrees.

        This is the counterclockwise difference between the North and the positive
        Y-axis. 90 is West and 270 is East (Default: 0). Note that this is different
        than the convention used in EnergyPlus, which uses clockwise difference
        instead of counterclockwise difference.
        """
        return self._north_angle

    @north_angle.setter
    def north_angle(self, value):
        self._north_angle = float_in_range(value, -360.0, 360.0, 'north angle')
        self._north_vector = Vector2D(0, 1).rotate(math.radians(self._north_angle))

    @property
    def north_vector(self):
        """Get or set a ladybug_geometry Vector2D for the north direction."""
        return self._north_vector

    @north_vector.setter
    def north_vector(self, value):
        assert isinstance(value, Vector2D), \
            'Expected Vector2D for north_vector. Got {}.'.format(type(value))
        self._north_vector = value
        self._north_angle = \
            math.degrees(self._north_vector.angle_clockwise(Vector2D(0, 1)))

    @property
    def terrain_type(self):
        """Get or set a text string for the terrain in which the model sits.

        This is used to determine the wind profile over the height of the
        building. Default is 'City'. Choose from the following options:

        * Ocean
        * Country
        * Suburbs
        * Urban
        * City
        """
        return self._terrain_type

    @terrain_type.setter
    def terrain_type(self, value):
        if value is not None:
            assert value in self.TERRAIN_TYPES, 'Input terrain_type "{}" is ' \
                'not valid. Choose from the following options:\n{}'.format(
                    value, self.TERRAIN_TYPES)
            self._terrain_type = value
        else:
            self._terrain_type = 'City'

    def building_idf(self, identifier='Building'):
        """Get an IDF string for an IDF Building object.

        Args:
            identifier: Text string for to be used as a unique identifier for the
                building object.
        """
        values = (identifier, self.north_angle, self.terrain_type, '', '',
                  self.shadow_calculation.solar_distribution)
        comments = ('name',
                    'clockwise north axis',
                    'terrain',
                    'loads convergence tolerance',
                    'temperature convergence tolerance',
                    'solar distribution')
        return generate_idf_string('Building', values, comments)

    def water_mains_idf(self):
        """Get an IDF string for the water mains object."""
        #TODO: Remove generation of mains temps from des days if bug is fixed in E+ 9.7
        if len(self.sizing_parameter.design_days) > 0:
            db_temps = [dday.dry_bulb_condition.dry_bulb_max
                        for dday in self.sizing_parameter.design_days]
            avg_temp = (max(db_temps) + min(db_temps)) / 2
            return generate_idf_string(
                'Site:WaterMainsTemperature', ('Correlation', '', str(avg_temp), '4'),
                ('calculation method', 'schedule', 'average temp', 'delta temp'))
        else:
            return generate_idf_string(
                'Site:WaterMainsTemperature', ('CorrelationFromWeatherFile',),
                ('calculation method',))

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
        # Regex patterns for the various objects comprising the SimulationParameter
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
            except IndexError:  # No DaylightSavingTime in the file.
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

        # process the Building within the idf_string
        try:
            bldg_str = bldg_pattern.findall(idf_string)[0]
            bldg_prop = parse_idf_string(bldg_str)
            north_angle = float(bldg_prop[1]) if bldg_prop[1] != '' else 0
            terrain = bldg_prop[2].title() if bldg_prop[2] != '' else 'Suburbs'
            solar_dist = bldg_prop[5] if bldg_prop[5] != '' else 'FullExterior'
        except IndexError:  # No Building in the file. Use honeybee default.
            north_angle = 0
            terrain = 'City'
            solar_dist = 'FullExteriorWithReflections'

        # process the ShadowCalculation within the idf_string
        try:
            sh_calc_str = sh_calc_pattern.findall(idf_string)[0]
        except IndexError:  # No ShadowCalculation in the file.
            sh_calc_str = None
            shadow_calc = None
        if sh_calc_str is not None:
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
        sizing_par = SizingParameter.from_idf(
            [dy[0] for dy in ddy_p.findall(idf_string)], sizing_str, location)

        return cls(output, run_period, timestep, sim_control, shadow_calc,
                   sizing_par, north_angle, terrain)

    @classmethod
    def from_dict(cls, data):
        """Create a SimulationParameter object from a dictionary.

        Args:
            data: A SimulationParameter dictionary in following the format below.

        .. code-block:: python

            {
            "type": "SimulationParameter",
            "output": {}, # Honeybee SimulationOutput dictionary
            "run_period": {}, # Honeybee RunPeriod dictionary
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
        north_angle = 0
        if 'north_angle' in data and data['north_angle'] is not None:
            north_angle = data['north_angle']
        terrain_type = 'City'
        if 'terrain_type' in data and data['terrain_type'] is not None:
            terrain_type = data['terrain_type']

        return cls(output, run_period, timestep, simulation_control,
                   shadow_calculation, sizing_parameter, north_angle, terrain_type)

    def to_idf(self, identifier='Building'):
        """Get an EnergyPlus string representation of the SimulationParameter.

        Note that this string is a concatenation of the IDF strings that make up
        the SimulationParameter (ie. RunPeriod, SimulationControl, etc.).

        Args:
            identifier: Text string for to be used as a unique identifier for the
                IDF Building object.
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

        # write the Building and water mains object
        sim_param_str.append(self.building_idf(identifier))
        sim_param_str.append(self.water_mains_idf())

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
            'sizing_parameter': self.sizing_parameter.to_dict(),
            'north_angle': self.north_angle,
            'terrain_type': self.terrain_type
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
            self.sizing_parameter.duplicate(), self.north_angle, self.terrain_type)

    def __key(self):
        """A tuple based on the object properties, useful for hashing."""
        return (hash(self.output), hash(self.run_period), self.timestep,
                hash(self.simulation_control),
                hash(self.shadow_calculation), hash(self.sizing_parameter),
                self.north_angle, self.terrain_type)

    def __hash__(self):
        return hash(self.__key())

    def __eq__(self, other):
        return isinstance(other, SimulationParameter) and self.__key() == other.__key()

    def __ne__(self, other):
        return not self.__eq__(other)

    def __repr__(self):
        return 'Energy SimulationParameter:'
