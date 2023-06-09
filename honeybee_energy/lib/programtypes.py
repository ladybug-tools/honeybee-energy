"""Collection of program types."""
from honeybee_energy.programtype import ProgramType

from ._loadprogramtypes import _program_types, _program_types_standards_dict, \
    _program_types_standards_registry, _building_programs_dict
import honeybee_energy.lib.schedules as _s


# establish variables for the default schedules used across the library
plenum_program = _program_types['Plenum']
office_program = _program_types['Generic Office Program']


# make lists of program types to look up items in the library
PROGRAM_TYPES = tuple(_program_types.keys()) + \
    tuple(_program_types_standards_dict.keys())
STANDARDS_REGISTRY = _program_types_standards_registry
BUILDING_TYPES = tuple(_building_programs_dict.keys())


def program_type_by_identifier(program_type_identifier):
    """Get a program_type from the library given its identifier.

    Args:
        program_type_identifier: A text string for the identifier of the ProgramType.
    """
    try:
        return _program_types[program_type_identifier]
    except KeyError:
        try:  # search the extension data
            p_type_dict = _program_types_standards_dict[program_type_identifier]
            scheds = _scheds_from_ptype_dict(p_type_dict)
            return ProgramType.from_dict_abridged(p_type_dict, scheds)
        except KeyError:  # construction is nowhere to be found; raise an error
            raise ValueError('"{}" was not found in the program type library.'.format(
                program_type_identifier))


def building_program_type_by_identifier(building_type):
    """Get a program_type representing the program mix of a building_type.

    Args:
        building_type: A text string for the type of building. This must appear
            under the BUILDING_TYPES constant of this module.
    """
    program_id = '{} Building'.format(building_type)
    try:
        return _program_types[program_id]
    except KeyError:
        try:  # search the extension data
            bld_mix_dict = _building_programs_dict[building_type]
            progs, ratios = [], []
            for key, val in bld_mix_dict.items():
                progs.append(program_type_by_identifier(key))
                ratios.append(val)
            bld_program = ProgramType.average(program_id, progs, ratios)
            bld_program.lock()
            _program_types[program_id] = bld_program  # cache the object for next time
            return bld_program
        except KeyError:  # construction is nowhere to be found; raise an error
            raise ValueError(
                '"{}" was not found in the building types.\nChoose from:\n{}'.format(
                    building_type, '\n'.join(BUILDING_TYPES)))


def _scheds_from_ptype_dict(p_type_dict):
    """Get a dictionary of schedules used in a ProgramTypeAbridged dictionary."""
    def add_schedule(scheds, p_type_dict, load_id, sch_id):
        try:
            sch_id = p_type_dict[load_id][sch_id]
            scheds[sch_id] = _s.schedule_by_identifier(sch_id)
        except KeyError:
            pass  # key is not included

    scheds = {}
    add_schedule(scheds, p_type_dict, 'people', 'occupancy_schedule')
    add_schedule(scheds, p_type_dict, 'people', 'activity_schedule')
    add_schedule(scheds, p_type_dict, 'lighting', 'schedule')
    add_schedule(scheds, p_type_dict, 'electric_equipment', 'schedule')
    add_schedule(scheds, p_type_dict, 'gas_equipment', 'schedule')
    add_schedule(scheds, p_type_dict, 'service_hot_water', 'schedule')
    add_schedule(scheds, p_type_dict, 'infiltration', 'schedule')
    add_schedule(scheds, p_type_dict, 'ventilation', 'schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'heating_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'cooling_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'humidifying_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'dehumidifying_schedule')
    return scheds


def lib_dict_abridged_to_program_type(program_dict, schedules):
    """Get a Python object of a ProgramType from an abridged dictionary.

    When the sub-objects needed to create the program type are not available
    in the resources provided, the current standards library will be searched.

    Args:
        program_dict: An abridged dictionary of a Honeybee ProgramType.
        schedules: Dictionary of all schedule objects that might be used in the
            construction set with the schedule identifiers as the keys.

    Returns:
        A Python object derived from the input program_dict.
    """
    def add_schedule(scheds, p_type_dict, load_id, sch_id):
        try:
            sch_id = p_type_dict[load_id][sch_id]
            if sch_id not in scheds:
                scheds[sch_id] = _s.schedule_by_identifier(sch_id)
        except KeyError:
            pass  # key is not included

    add_schedule(schedules, program_dict, 'people', 'occupancy_schedule')
    add_schedule(schedules, program_dict, 'people', 'activity_schedule')
    add_schedule(schedules, program_dict, 'lighting', 'schedule')
    add_schedule(schedules, program_dict, 'electric_equipment', 'schedule')
    add_schedule(schedules, program_dict, 'gas_equipment', 'schedule')
    add_schedule(schedules, program_dict, 'service_hot_water', 'schedule')
    add_schedule(schedules, program_dict, 'infiltration', 'schedule')
    add_schedule(schedules, program_dict, 'ventilation', 'schedule')
    add_schedule(schedules, program_dict, 'setpoint', 'heating_schedule')
    add_schedule(schedules, program_dict, 'setpoint', 'cooling_schedule')
    add_schedule(schedules, program_dict, 'setpoint', 'humidifying_schedule')
    add_schedule(schedules, program_dict, 'setpoint', 'dehumidifying_schedule')
    return ProgramType.from_dict_abridged(program_dict, schedules)
