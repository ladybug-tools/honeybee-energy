"""Collection of construction sets."""
import honeybee_energy.lib.construction as const_lib


def generic(type, boundary_condition):
    _construction_set = {
        'Wall': {
            'Outdoors': const_lib.generic_wall,
            # 'Ground': '',
            # 'Surface': ''
        }
    }
    try:
        return _construction_set[type.name][boundary_condition.name]
    except KeyError:
        raise ValueError(
            'Failed to find preset construction for %s %s' % (
                boundary_condition, type)
        )
    except AttributeError as e:
        print(e)
        raise TypeError('Invalid type or boundary condition')
