from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.windowshade import WindowConstructionShade
from honeybee_energy.properties.extension import WindowConstructionShadeProperties
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas
from honeybee_energy.material.shade import EnergyWindowMaterialShade

def test_energy_properties():
    # -- Build the Window Construction
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    construction_window = WindowConstruction(
        'Triple Pane', [clear_glass, gap, clear_glass, gap, clear_glass])
    
    # -- Build the Shade Construction
    material_shade = EnergyWindowMaterialShade("test_shade_material")
    construction_shade = WindowConstructionShade(
        "test_construction_shade", construction_window, material_shade)
    
    # --
    assert hasattr(construction_shade, "properties")
    assert isinstance(
        construction_shade.properties, WindowConstructionShadeProperties)
    assert construction_shade.identifier == "test_construction_shade"
    assert construction_shade.window_construction == construction_window

def test_shade_construction_dict_round_trip():
    # -- Build the Window Construction
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    construction_window = WindowConstruction(
        'Triple Pane', [clear_glass, gap, clear_glass, gap, clear_glass])
    
    # -- Build the Shade Construction
    material_shade = EnergyWindowMaterialShade("test_shade_material")
    c1 = WindowConstructionShade(
        "test_c1", construction_window, material_shade)
    
    d1 = c1.to_dict()
    c2 = WindowConstructionShade.from_dict(d1)
    assert c2.to_dict() == d1

def test_duplicate_shade_construction():
    # -- Build the Window Construction
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    construction_window = WindowConstruction(
        'Triple Pane', [clear_glass, gap, clear_glass, gap, clear_glass])
    
    # -- Build the Shade Construction
    material_shade = EnergyWindowMaterialShade("test_shade_material")
    c1 = WindowConstructionShade(
        "test_c1", construction_window, material_shade)

    c2 = c1.duplicate()
    assert c2.to_dict() == c1.to_dict()
