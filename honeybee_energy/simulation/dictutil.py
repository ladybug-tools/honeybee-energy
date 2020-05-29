# coding=utf-8
"""Utilities to convert simulation dictionaries to Python objects."""
from honeybee_energy.simulation.control import SimulationControl
from honeybee_energy.simulation.runperiod import RunPeriod
from honeybee_energy.simulation.daylightsaving import DaylightSavingTime
from honeybee_energy.simulation.shadowcalculation import ShadowCalculation
from honeybee_energy.simulation.sizing import SizingParameter
from honeybee_energy.simulation.output import SimulationOutput
from honeybee_energy.simulation.parameter import SimulationParameter


SIMULATION_TYPES = ('SimulationControl', 'RunPeriod', 'DaylightSavingTime',
                    'ShadowCalculation', 'SizingParameter', 'SimulationOutput',
                    'SimulationParameter')


def dict_to_simulation(sim_dict, raise_exception=True):
    """Get a Python object of any Simulation object from a dictionary.

    Args:
        sim_dict: A dictionary of any Honeybee energy simulation object. Note
            that this should be a non-abridged dictionary to be valid.
        raise_exception: Boolean to note whether an excpetion should be raised
            if the object is not identified as a simulation object. Default: True.

    Returns:
        A Python object derived from the input sim_dict.
    """
    try:  # get the type key from the dictionary
        sim_type = sim_dict['type']
    except KeyError:
        raise ValueError('Simulation dictionary lacks required "type" key.')

    if sim_type == 'SimulationControl':
        return SimulationControl.from_dict(sim_dict)
    elif sim_type == 'RunPeriod':
        return RunPeriod.from_dict(sim_dict)
    elif sim_type == 'DaylightSavingTime':
        return DaylightSavingTime.from_dict(sim_dict)
    elif sim_type == 'ShadowCalculation':
        return ShadowCalculation.from_dict(sim_dict)
    elif sim_type == 'SizingParameter':
        return SizingParameter.from_dict(sim_dict)
    elif sim_type == 'SimulationOutput':
        return SimulationOutput.from_dict(sim_dict)
    elif sim_type == 'SimulationParameter':
        return SimulationParameter.from_dict(sim_dict)
    elif raise_exception:
        raise ValueError('{} is not a recognized energy Simulation type'.format(sim_type))
