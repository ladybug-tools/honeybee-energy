# coding':utf-8
"""Crack data dictionary.

This data is obtained from the DesignBuilder Crack Template. Note that this
crack data is normalized by area and perimeter for face cracks and subface edges,
respectively. In EP face cracks are not normalized by area, but subface edges
are normalized by perimeter.
"""

crack_data_dict = {
    # TODO: Fix the external crack data
    'external_tight_crack': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.001,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.00001,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.0002,
        'window_flow_exp': 0.7,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.7
    },
    # TODO: Fix the external crack data
    'external_average_crack': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.003,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.0009,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.0014,
        'window_flow_exp': 0.65,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    },
    # TODO: Fix the external crack data
    'external_leaky_cracks': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.019,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.003,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.003,
        'window_flow_exp': 0.6,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    },

    'internal_tight_crack': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.001,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.00001,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.0002,
        'window_flow_exp': 0.7,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.7
    },

    'internal_average_crack': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.003,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.0009,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.0014,
        'window_flow_exp': 0.65,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    },

    'internal_leaky_cracks': {
        # kg/s/m2 @ 1 Pa
        'wall_flow_cof': 0.019,
        'wall_flow_exp': 0.75,
        'floorceiling_flow_cof': 0.003,
        'floorceiling_flow_exp': 0.7,
        # kg/s/m @ 1 Pa
        'window_flow_cof': 0.003,
        'window_flow_exp': 0.6,
        'door_flow_cof': 0.02,
        'door_flow_exp': 0.6
    }
}
