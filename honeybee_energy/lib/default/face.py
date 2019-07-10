"""A collection of default energy constructions.

Note that these constructions are not in accordance with any particular building
code or climate zone. They are just meant to represent "Typical" constructions
that are plausible for a building constructed in the last few decades. While they
provide a decent starting point, it is recommended that at least the outdoor
constructions be changed to suit a given project's building code and climate.
"""
from honeybee_energy.construction import OpaqueConstruction, \
    WindowConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas


# generic opaque materials
brick = EnergyMaterial(
    'Generic Brick', 0.1, 0.9, 1920, 790, 'MediumRough', 0.9, 0.7, 0.7)
brick.lock()
concrete_lw = EnergyMaterial(
    'Generic Lightweight Concrete', 0.1, 0.53, 1280, 840, 'MediumRough', 0.9, 0.8, 0.8)
concrete_lw.lock()
concrete_hw = EnergyMaterial(
    'Generic Heavyweight Concrete', 0.2, 1.95, 2240, 900, 'MediumRough', 0.9, 0.8, 0.8)
concrete_hw.lock()
insulation = EnergyMaterial(
    'Generic 50mm Insulation Board', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
insulation.lock()
insulation_thin = EnergyMaterial(
    'Generic 25mm Insulation Board', 0.05, 0.03, 43, 1210, 'MediumRough', 0.9, 0.7, 0.7)
insulation_thin.lock()
gypsum = EnergyMaterial(
    'Generic Gypsum Board', 0.0127, 0.16, 800, 1090, 'MediumSmooth', 0.9, 0.5, 0.5)
gypsum.lock()
acoustic_tile = EnergyMaterial(
    'Generic Acoustic Tile', 0.02, 0.06, 368, 590, 'MediumSmooth', 0.9, 0.3, 0.3)
acoustic_tile.lock()
metal_surface = EnergyMaterial(
    'Generic Metal Surface', 0.0015, 45, 7690, 410, 'Smooth', 0.9, 0.5, 0.5)
metal_surface.lock()
roof_membrane = EnergyMaterial(
    'Generic Roof Membrane', 0.01, 0.16, 1120, 1460, 'MediumRough', 0.9, 0.7, 0.7)
roof_membrane.lock()
wood = EnergyMaterial(
    'Generic 25mm Wood', 0.0254, 0.15, 608, 1630, 'MediumSmooth', 0.9, 0.5, 0.5)
wood.lock()

# generic opqaue air gap materials
wall_gap = EnergyMaterial(
    'Generic Wall Air Gap', 0.1, 0.667, 1.28, 1000, 'Smooth')
wall_gap.lock()
ceiling_gap = EnergyMaterial(
    'Generic Ceiling Air Gap', 0.1, 0.556, 1.28, 1000, 'Smooth')
ceiling_gap.lock()
air = EnergyMaterial(
    'Air Wall Material', 0.01, 0.6, 1.28, 1004, 'Smooth', 0.95, 0.95, 0.95)
air.lock()

# generic glazing materials
clear_glass = EnergyWindowMaterialGlazing(
    'Generic Clear Glass', 0.006, 0.771, 0.07, 0.884, 0.0804, 0, 0.84, 0.84, 1.0)
clear_glass.lock()
lowe_glass = EnergyWindowMaterialGlazing(
    'Generic Low-e Glass', 0.006, 0.452, 0.359, 0.714, 0.207, 0, 0.84, 0.046578, 1.0)
lowe_glass.lock()

# generic window air gap materials
gap = EnergyWindowMaterialGas('Generic Window Air Gap', thickness=0.0127)
gap.lock()

# generic wall constructions
generic_exterior_wall = OpaqueConstruction(
    'Generic Exterior Brick Wall', [brick, concrete_lw, insulation, wall_gap, gypsum])
generic_exterior_wall.lock()
generic_interior_wall = OpaqueConstruction(
    'Generic Interior Wall', [gypsum, wall_gap, gypsum])
generic_interior_wall.lock()
generic_underground_wall = OpaqueConstruction(
    'Generic Underground Wall', [insulation, concrete_hw])
generic_underground_wall.lock()

# generic floor constructions
generic_exposed_floor = OpaqueConstruction(
    'Generic Exposed Floor Slab', [metal_surface, ceiling_gap, insulation, concrete_lw])
generic_exposed_floor.lock()
generic_interior_floor = OpaqueConstruction(
    'Generic Interior Floor', [acoustic_tile, ceiling_gap, concrete_lw])
generic_interior_floor.lock()
generic_ground_slab = OpaqueConstruction(
    'Generic Ground Slab', [insulation, concrete_hw])
generic_ground_slab.lock()

# generic roof/ceiling constructions
generic_roof = OpaqueConstruction(
    'Generic Roof', [roof_membrane, insulation, concrete_lw, ceiling_gap, acoustic_tile])
generic_roof.lock()
generic_interior_ceiling = OpaqueConstruction(
    'Generic Interior Ceiling', [concrete_lw, ceiling_gap, acoustic_tile])
generic_interior_ceiling.lock()
generic_underground_roof = OpaqueConstruction(
    'Generic Underground Roof', [insulation, concrete_hw, ceiling_gap, acoustic_tile])
generic_underground_roof.lock()

# generic window constructions
generic_double_pane = WindowConstruction(
    'Generic Double Pane Window', [clear_glass, gap, clear_glass])
generic_double_pane.lock()
generic_single_pane = WindowConstruction(
    'Generic Single Pane Window', [clear_glass])
generic_single_pane.lock()

# generic door constructions
generic_exterior_door = OpaqueConstruction(
    'Generic Exterior Door', [metal_surface, insulation_thin, metal_surface])
generic_exterior_door.lock()
generic_interior_door = OpaqueConstruction(
    'Generic Interior Door', [wood])
generic_interior_door.lock()

# air wall construction
air_wall = OpaqueConstruction(
    'Air Wall', [air])
air_wall.lock()
