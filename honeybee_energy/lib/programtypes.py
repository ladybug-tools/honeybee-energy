"""Collection of program types."""
from honeybee_energy.programtype import ProgramType
from honeybee_energy.load.people import People
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.load.infiltration import Infiltration
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.load.setpoint import Setpoint

from ._loadprogramtypes import _program_types, _program_types_standards_dict, \
    _program_types_standards_registry
import honeybee_energy.lib.schedules as _s


# establish variables for the default schedules used across the library
# and auto-generate schedules if they were not loaded from default.idf
try:
    plenum_program = _program_types['Plenum']
except KeyError:
    plenum_program = ProgramType('Plenum')
    plenum_program.lock()
    _program_types['Plenum'] = plenum_program

try:
    office_program = _program_types['Generic Office Program']
except KeyError:
    if _s.generic_office_occupancy is not None:
        people = People('Generic Office People', 0.0565,
                        _s.generic_office_occupancy, _s.generic_office_activity)
        lighting = Lighting('Generic Office Lighting', 10.55,
                            _s.generic_office_lighting, 0.0, 0.7, 0.2)
        equipment = ElectricEquipment('Generic Office Equipment', 10.33,
                                      _s.generic_office_equipment, 0.5)
        infiltration = Infiltration('Generic Office Infiltration', 0.0002266,
                                    _s.generic_office_infiltration)
        ventilation = Ventilation('Generic Office Ventilation', 0.00236, 0.000305)
        setpoint = Setpoint('Generic Office Setpoints', _s.generic_office_heating,
                            _s.generic_office_cooling)
        office_program = ProgramType(
            'Generic Office Program', people, lighting, equipment, None, infiltration,
            ventilation, setpoint)
        office_program.lock()
    else:
        office_program = None
    _program_types['Generic Office Program'] = office_program


# make lists of program types to look up items in the library
PROGRAM_TYPES = tuple(_program_types.keys()) + \
    tuple(_program_types_standards_dict.keys())
STANDARDS_REGISTRY = _program_types_standards_registry


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
    add_schedule(scheds, p_type_dict, 'infiltration', 'schedule')
    add_schedule(scheds, p_type_dict, 'ventilation', 'schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'heating_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'cooling_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'humidifying_schedule')
    add_schedule(scheds, p_type_dict, 'setpoint', 'dehumidifying_schedule')
    return scheds
