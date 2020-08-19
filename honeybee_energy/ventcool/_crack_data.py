# coding':utf-8
"""Crack data dictionary.

The flow coefficient and exponent data is referenced here from the DesignBuilder Cracks
Template, which derives these values to empirically provide typical air changes rates
for the respective air tightness classifications for a range of building types[1].

Note that this crack data is normalized by area and perimeter for face cracks and subface
edges, respectively. As such, the units for the wall, and roof flow coefficients are
kg/s/m2 at 1 Pa, and the units for the window, and door coefficients are kg/s/m at 1 Pa.
In EnergyPlus the face cracks are not normalized by area, but subface edges are
normalized by perimeter.

Note:
    [1] DesignBuilder (6.1.6.008). DesignBuilder Software Ltd, 2000-2020.
"""

CRACK_TEMPLATE_DATA = {

    'external_excellent_cracks': {
        'wall_flow_cof': 0.00001,
        'wall_flow_exp': 0.7,
        'roof_flow_cof': 0.00001,
        'roof_flow_exp': 0.7,
        'floor_flow_cof': 0.0001,
        'floor_flow_exp': 0.7,
        'window_flow_cof': 0.00001,
        'window_flow_exp': 0.7,
        'door_flow_cof': 0.0002,
        'door_flow_exp': 0.7
    },

    'external_medium_cracks': {
        'wall_flow_cof': 0.0001,
        'wall_flow_exp': 0.7,
        'roof_flow_cof': 0.0001,
        'roof_flow_exp': 0.7,
        'floor_flow_cof': 0.0007,
        'floor_flow_exp': 1,
        'window_flow_cof': 0.00014,
        'window_flow_exp': 0.65,
        'door_flow_cof': 0.0014,
        'door_flow_exp': 0.65
    },

    'external_verypoor_cracks': {
        'wall_flow_cof': 0.0004,
        'wall_flow_exp': 0.7,
        'roof_flow_cof': 0.0002,
        'roof_flow_exp': 0.7,
        'floor_flow_cof': 0.002,
        'floor_flow_exp': 1,
        'window_flow_cof': 0.003,
        'window_flow_exp': 0.6,
        'door_flow_cof': 0.003,
        'door_flow_exp': 0.66
    },

    'internal_excellent_cracks': {
        'wall_flow_cof': 0.001,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.00001,
        'floorceiling_flow_exp': 0.7,
        'window_flow_cof': 0.0002,
        'window_flow_exp': 0.7,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.7
    },

    'internal_medium_cracks': {
        'wall_flow_cof': 0.003,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.0009,
        'floorceiling_flow_exp': 0.7,
        'window_flow_cof': 0.0014,
        'window_flow_exp': 0.65,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    },

    'internal_verypoor_cracks': {
        'wall_flow_cof': 0.019,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.003,
        'floorceiling_flow_exp': 0.7,
        'window_flow_cof': 0.003,
        'window_flow_exp': 0.6,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    }
}
