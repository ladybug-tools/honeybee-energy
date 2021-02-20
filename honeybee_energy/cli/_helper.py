"""A collection of helper functions used throughout the CLI.

Most functions assist with the serialization of objects to/from JSON.
"""
import json

from ladybug.analysisperiod import AnalysisPeriod
from honeybee_energy.simulation.runperiod import RunPeriod


def _load_run_period_json(run_period_json):
    """Load a RunPeriod from a JSON file with a run period or analysis period.
    
    Args:
        run_period_json: A JSON file of a RunPeriod or AnalysisPeriod to be loaded.
    """
    if run_period_json is not None and run_period_json != 'None':
        with open(run_period_json) as json_file:
            data = json.load(json_file)
        if data['type'] == 'AnalysisPeriod':
            return RunPeriod.from_analysis_period(AnalysisPeriod.from_dict(data))
        elif data['type'] == 'RunPeriod':
            return RunPeriod.from_dict(data)
