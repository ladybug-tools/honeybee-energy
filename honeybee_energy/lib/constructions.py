"""Load all of the constructions and materials from the IDF libraries."""
from honeybee_energy.construction import OpaqueConstruction, \
    WindowConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas
import os


# empty dictionaries to hold idf-loaded materials and constructions
idf_opaque_materials = {}
idf_window_materials = {}
idf_opaque_constructions = {}
idf_window_constructions = {}


# load everythng from the default library
default_lib = './idf/constructions/default.idf'
if os.path.isfile(default_lib):
    constructions, materials = OpaqueConstruction.extract_all_from_idf_file(default_lib)
    for mat in materials:
        mat.lock()
        idf_opaque_materials[mat.name] = mat
    for cnstr in constructions:
        cnstr.lock()
        idf_opaque_constructions[cnstr.name] = cnstr
    constructions, materials = WindowConstruction.extract_all_from_idf_file(default_lib)
    for mat in materials:
        mat.lock()
        idf_window_materials[mat.name] = mat
    for cnstr in constructions:
        cnstr.lock()
        idf_window_constructions[cnstr.name] = cnstr


# auto-generate materials and constructions if they were not loaded
# generic opaque materials
if 'Generic Brick' not in idf_opaque_materials:
    idf_opaque_materials['Generic Brick'] = EnergyMaterial(
        'Generic Brick', 0.1, 0.9, 1920, 790, 'MediumRough', 0.9, 0.7, 0.7)
    idf_opaque_materials['Generic Brick'].lock()
if 'Generic LW Concrete' not in idf_opaque_materials:
    idf_opaque_materials['Generic LW Concrete'] = EnergyMaterial(
        'Generic LW Concrete', 0.1, 0.53, 1280, 840, 'MediumRough', 0.9, 0.8, 0.8)
    idf_opaque_materials['Generic LW Concrete'].lock()
if 'Generic HW Concrete' not in idf_opaque_materials:
    idf_opaque_materials['Generic HW Concrete'] = EnergyMaterial(
        'Generic HW Concrete', 0.2, 1.95, 2240, 900, 'MediumRough', 0.9, 0.8, 0.8)
    idf_opaque_materials['Generic HW Concrete'].lock()
if 'Generic 50mm Insulation' not in idf_opaque_materials:
    idf_opaque_materials['Generic 50mm Insulation'] = EnergyMaterial(
        'Generic 50mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
    idf_opaque_materials['Generic 50mm Insulation'].lock()
if 'Generic 25mm Insulation' not in idf_opaque_materials:
    idf_opaque_materials['Generic 25mm Insulation'] = EnergyMaterial(
        'Generic 25mm Insulation', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
    idf_opaque_materials['Generic 25mm Insulation'].lock()
if 'Generic Gypsum Board' not in idf_opaque_materials:
    idf_opaque_materials['Generic Gypsum Board'] = EnergyMaterial(
        'Generic Gypsum Board', 0.0127, 0.16, 800, 1090, 'MediumSmooth', 0.9, 0.5, 0.5)
    idf_opaque_materials['Generic Gypsum Board'].lock()
if 'Generic Acoustic Tile' not in idf_opaque_materials:
    idf_opaque_materials['Generic Acoustic Tile'] = EnergyMaterial(
        'Generic Acoustic Tile', 0.02, 0.06, 368, 590, 'MediumSmooth', 0.9, 0.3, 0.3)
    idf_opaque_materials['Generic Acoustic Tile'].lock()
if 'Generic Metal Surface' not in idf_opaque_materials:
    idf_opaque_materials['Generic Metal Surface'] = EnergyMaterial(
        'Generic Metal Surface', 0.0015, 45, 7690, 410, 'Smooth', 0.9, 0.5, 0.5)
    idf_opaque_materials['Generic Metal Surface'].lock()
if 'Generic Roof Membrane' not in idf_opaque_materials:
    idf_opaque_materials['Generic Roof Membrane'] = EnergyMaterial(
        'Generic Roof Membrane', 0.01, 0.16, 1120, 1460, 'MediumRough', 0.9, 0.7, 0.7)
    idf_opaque_materials['Generic Roof Membrane'].lock()
if 'Generic 25mm Wood' not in idf_opaque_materials:
    idf_opaque_materials['Generic 25mm Wood'] = EnergyMaterial(
        'Generic 25mm Wood', 0.0254, 0.15, 608, 1630, 'MediumSmooth', 0.9, 0.5, 0.5)
    idf_opaque_materials['Generic 25mm Wood'].lock()

# generic opqaue air gap materials
if 'Generic Wall Air Gap' not in idf_opaque_materials:
    idf_opaque_materials['Generic Wall Air Gap'] = EnergyMaterial(
        'Generic Wall Air Gap', 0.1, 0.667, 1.28, 1000, 'Smooth')
    idf_opaque_materials['Generic Wall Air Gap'].lock()
if 'Generic Ceiling Air Gap' not in idf_opaque_materials:
    idf_opaque_materials['Generic Ceiling Air Gap'] = EnergyMaterial(
        'Generic Ceiling Air Gap', 0.1, 0.556, 1.28, 1000, 'Smooth')
    idf_opaque_materials['Generic Ceiling Air Gap'].lock()
if 'Air Wall Material' not in idf_opaque_materials:
    idf_opaque_materials['Air Wall Material'] = EnergyMaterial(
        'Air Wall Material', 0.01, 0.6, 1.28, 1004, 'Smooth', 0.95, 0.95, 0.95)
    idf_opaque_materials['Air Wall Material'].lock()

# generic glazing materials
if 'Generic Clear Glass' not in idf_window_materials:
    idf_window_materials['Generic Clear Glass'] = EnergyWindowMaterialGlazing(
        'Generic Clear Glass', 0.006, 0.771, 0.07, 0.884, 0.0804, 0, 0.84, 0.84, 1.0)
    idf_window_materials['Generic Clear Glass'].lock()
if 'Generic Low-e Glass' not in idf_window_materials:
    idf_window_materials['Generic Low-e Glass'] = EnergyWindowMaterialGlazing(
        'Generic Low-e Glass', 0.006, 0.452, 0.359, 0.714, 0.207, 0, 0.84, 0.046578, 1.0)
    idf_window_materials['Generic Low-e Glass'].lock()

# generic window air gap materials
if 'Generic Window Air Gap' not in idf_window_materials:
    idf_window_materials['Generic Window Air Gap'] = EnergyWindowMaterialGas(
        'Generic Window Air Gap', 0.0127, 'Air')
    idf_window_materials['Generic Window Air Gap'].lock()
if 'Generic Window Argon Gap' not in idf_window_materials:
    idf_window_materials['Generic Window Argon Gap'] = EnergyWindowMaterialGas(
        'Generic Window Argon Gap', 0.0127, 'Argon')
    idf_window_materials['Generic Window Argon Gap'].lock()

# establish the default materials used across the library
brick = idf_opaque_materials['Generic Brick']
concrete_lw = idf_opaque_materials['Generic LW Concrete']
concrete_hw = idf_opaque_materials['Generic HW Concrete']
insulation = idf_opaque_materials['Generic 50mm Insulation']
insulation_thin = idf_opaque_materials['Generic 25mm Insulation']
gypsum = idf_opaque_materials['Generic Gypsum Board']
acoustic_tile = idf_opaque_materials['Generic Acoustic Tile']
metal_surface = idf_opaque_materials['Generic Metal Surface']
roof_membrane = idf_opaque_materials['Generic Roof Membrane']
wood = idf_opaque_materials['Generic 25mm Wood']
wall_gap = idf_opaque_materials['Generic Wall Air Gap']
ceiling_gap = idf_opaque_materials['Generic Ceiling Air Gap']
air = idf_opaque_materials['Air Wall Material']
clear_glass = idf_window_materials['Generic Clear Glass']
lowe_glass = idf_window_materials['Generic Low-e Glass']
air_gap = idf_window_materials['Generic Window Air Gap']
argon_gap = idf_window_materials['Generic Window Argon Gap']

# generic wall constructions
if 'Generic Exterior Wall' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Exterior Wall'] = OpaqueConstruction(
        'Generic Exterior Wall', [brick, concrete_lw, insulation, wall_gap, gypsum])
    idf_opaque_constructions['Generic Exterior Wall'] .lock()
if 'Generic Interior Wall' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Interior Wall'] = OpaqueConstruction(
        'Generic Interior Wall', [gypsum, wall_gap, gypsum])
    idf_opaque_constructions['Generic Interior Wall'].lock()
if 'Generic Underground Wall' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Underground Wall'] = OpaqueConstruction(
        'Generic Underground Wall', [insulation, concrete_hw])
    idf_opaque_constructions['Generic Underground Wall'].lock()

# generic floor constructions
if 'Generic Exposed Floor' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Exposed Floor'] = OpaqueConstruction(
        'Generic Exposed Floor', [metal_surface, ceiling_gap, insulation, concrete_lw])
    idf_opaque_constructions['Generic Exposed Floor'].lock()
if 'Generic Interior Floor' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Interior Floor'] = OpaqueConstruction(
        'Generic Interior Floor', [acoustic_tile, ceiling_gap, concrete_lw])
    idf_opaque_constructions['Generic Interior Floor'].lock()
if 'Generic Ground Slab' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Ground Slab'] = OpaqueConstruction(
        'Generic Ground Slab', [insulation, concrete_hw])
    idf_opaque_constructions['Generic Ground Slab'].lock()

# generic roof/ceiling constructions
if 'Generic Roof' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Roof'] = OpaqueConstruction(
        'Generic Roof', [roof_membrane, insulation, concrete_lw,
                         ceiling_gap, acoustic_tile])
    idf_opaque_constructions['Generic Roof'].lock()
if 'Generic Interior Ceiling' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Interior Ceiling'] = OpaqueConstruction(
        'Generic Interior Ceiling', [concrete_lw, ceiling_gap, acoustic_tile])
    idf_opaque_constructions['Generic Interior Ceiling'].lock()
if 'Generic Underground Roof' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Underground Roof'] = OpaqueConstruction(
        'Generic Underground Roof', [insulation, concrete_hw,
                                     ceiling_gap, acoustic_tile])
    idf_opaque_constructions['Generic Underground Roof'].lock()

# generic window constructions
if 'Generic Double Pane' not in idf_window_constructions:
    idf_window_constructions['Generic Double Pane'] = WindowConstruction(
        'Generic Double Pane', [clear_glass, air_gap, clear_glass])
    idf_window_constructions['Generic Double Pane'].lock()
if 'Generic Single Pane' not in idf_window_constructions:
    idf_window_constructions['Generic Single Pane'] = WindowConstruction(
        'Generic Single Pane', [clear_glass])
    idf_window_constructions['Generic Single Pane'].lock()

# generic door constructions
if 'Generic Exterior Door' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Exterior Door'] = OpaqueConstruction(
        'Generic Exterior Door', [metal_surface, insulation_thin, metal_surface])
    idf_opaque_constructions['Generic Exterior Door'].lock()
if 'Generic Interior Door' not in idf_opaque_constructions:
    idf_opaque_constructions['Generic Interior Door'] = OpaqueConstruction(
        'Generic Interior Door', [wood])
    idf_opaque_constructions['Generic Interior Door'].lock()

# air wall construction
if 'Air Wall' not in idf_opaque_constructions:
    idf_opaque_constructions['Air Wall'] = OpaqueConstruction(
        'Air Wall', [air])
    idf_opaque_constructions['Air Wall'].lock()

# establish the default constructions used across the library
generic_exterior_wall = idf_opaque_constructions['Generic Exterior Wall']
generic_interior_wall = idf_opaque_constructions['Generic Interior Wall']
generic_underground_wall = idf_opaque_constructions['Generic Underground Wall']
generic_exposed_floor = idf_opaque_constructions['Generic Exposed Floor']
generic_interior_floor = idf_opaque_constructions['Generic Interior Floor']
generic_ground_slab = idf_opaque_constructions['Generic Ground Slab']
generic_roof = idf_opaque_constructions['Generic Roof']
generic_interior_ceiling = idf_opaque_constructions['Generic Interior Ceiling']
generic_underground_roof = idf_opaque_constructions['Generic Underground Roof']
generic_double_pane = idf_window_constructions['Generic Double Pane']
generic_single_pane = idf_window_constructions['Generic Single Pane']
generic_exterior_door = idf_opaque_constructions['Generic Exterior Door']
generic_interior_door = idf_opaque_constructions['Generic Interior Door']
air_wall = idf_opaque_constructions['Air Wall']

# load other materials and constructions from user-supplied files
construction_lib = os.path.abspath('./honeybee_energy/lib/idf/constructions/')
for f in os.listdir(construction_lib):
    if f.endswith('.idf') and f != 'default.idf' and os.path.isfile(f):
        constructions, materials = OpaqueConstruction.extract_all_from_idf_file(f)
        for mat in materials:
            mat.lock()
            idf_opaque_materials[mat.name] = mat
        for cnstr in constructions:
            cnstr.lock()
            idf_opaque_constructions[cnstr.name] = cnstr
        constructions, materials = WindowConstruction.extract_all_from_idf_file(f)
        for mat in materials:
            mat.lock()
            idf_window_materials[mat.name] = mat
        for cnstr in constructions:
            cnstr.lock()
            idf_window_constructions[cnstr.name] = cnstr

# make lists of construction and material names to look up items in the library
OPAQUE_MATERIALS = tuple(idf_opaque_materials.keys())
WINDOW_MATERIALS = tuple(idf_window_materials.keys())
OPAQUE_CONSTRUCTIONS = tuple(idf_opaque_constructions.keys())
WINDOW_CONSTRUCTIONS = tuple(idf_window_constructions.keys())


# methods to look up materials + constructions from the library


def opaque_material_by_name(material_name):
    """Get an opaque material from the library given the material name.

    Args:
        material_name: A text string for the name of the material.
    """
    try:
        return idf_opaque_materials[material_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the opaque energy material library.'.format(
                    material_name))


def window_material_by_name(material_name):
    """Get an window material from the library given the material name.

    Args:
        material_name: A text string for the name of the material.
    """
    try:
        return idf_window_materials[material_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the window energy material library.'.format(
                    material_name))


def opaque_construction_by_name(construction_name):
    """Get an opaque construction from the library given the construction name.

    Args:
        construction_name: A text string for the name of the construction.
    """
    try:
        return idf_opaque_constructions[construction_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the opaque energy construction library.'.format(
                    construction_name))


def window_construction_by_name(construction_name):
    """Get an window construction from the library given the construction name.

    Args:
        construction_name: A text string for the name of the construction.
    """
    try:
        return idf_window_constructions[construction_name]
    except KeyError:
        raise ValueError(
            '"{}" was not found in the window energy construction library.'.format(
                    construction_name))
