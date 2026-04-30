"""Utility functions for converting energy attributes to common units."""
from __future__ import division
import os
import io
import json

units_path = os.path.join(os.path.dirname(__file__), 'units.json')
with io.open(units_path, encoding='utf-8') as uf:
    UNITS = json.load(uf)
SAFE = {'__builtins__': {}}


def convert_people_per_area(value, units='si'):
    group, atr = 'people', 'people_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_people_activity_max_sensible(value, units='si'):
    group, atr = 'people', 'activity_max_sensible'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_people_activity_max_latent(value, units='si'):
    group, atr = 'people', 'activity_max_latent'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_lighting_watts_per_area(value, units='si'):
    group, atr = 'lighting', 'watts_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_electric_equipment_watts_per_area(value, units='si'):
    group, atr = 'electric_equipment', 'watts_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_gas_equipment_watts_per_area(value, units='si'):
    group, atr = 'gas_equipment', 'watts_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_service_hot_water_flow_per_area(value, units='si'):
    group, atr = 'service_hot_water', 'flow_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_service_hot_water_target_temperature(value, units='si'):
    group, atr = 'service_hot_water', 'target_temperature'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_infiltration_flow_per_exterior_area(value, units='si'):
    group, atr = 'infiltration', 'flow_per_exterior_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_ventilation_flow_per_person(value, units='si'):
    group, atr = 'ventilation', 'flow_per_person'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_ventilation_flow_per_area(value, units='si'):
    group, atr = 'ventilation', 'flow_per_area'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_ventilation_flow_per_zone(value, units='si'):
    group, atr = 'ventilation', 'flow_per_zone'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_ventilation_air_changes_per_hour(value, units='si'):
    group, atr = 'ventilation', 'air_changes_per_hour'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_setpoint(value, units='si'):
    group, atr = 'setpoint', 'heating_setpoint'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)


def convert_setpoint_cutout_difference(value, units='si'):
    group, atr = 'setpoint', 'setpoint_cutout_difference'
    return eval(UNITS[group][atr]['convert_to_{}'.format(units)].format(x=value), SAFE)
