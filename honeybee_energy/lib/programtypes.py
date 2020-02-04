"""Collection of program types."""
from honeybee_energy.programtype import ProgramType
from honeybee_energy.load.people import People
from honeybee_energy.load.lighting import Lighting
from honeybee_energy.load.equipment import ElectricEquipment
from honeybee_energy.load.infiltration import Infiltration
from honeybee_energy.load.ventilation import Ventilation
from honeybee_energy.load.setpoint import Setpoint

from ._loadprogramtypes import _json_program_types
import honeybee_energy.lib.schedules as _s


# establish variables for the default schedules used across the library
# and auto-generate schedules if they were not loaded from default.idf
try:
    plenum_program = _json_program_types['Plenum']
except KeyError:
    plenum_program = ProgramType('Plenum')
    plenum_program.lock()
    _json_program_types['Plenum'] = plenum_program

try:
    office_program = _json_program_types['Generic Office Program']
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
    _json_program_types['Generic Office Program'] = office_program


# make lists of program types to look up items in the library
PROGRAM_TYPES = tuple(_json_program_types.keys())


def program_type_by_name(program_type_name):
    """Get a program_type from the library given its name.

    Args:
        program_type_name: A text string for the name of the ProgramType.
    """
    try:
        return _json_program_types[program_type_name]
    except KeyError:
        raise ValueError('"{}" was not found in the program type library.'.format(
            program_type_name))
