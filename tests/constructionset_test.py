from honeybee_energy.constructionset import ConstructionSet, WallConstructionSet, FloorConstructionSet, \
    RoofCeilingConstructionSet, ApertureConstructionSet, DoorConstructionSet
from honeybee_energy.construction.opaque import OpaqueConstruction
from honeybee_energy.construction.window import WindowConstruction
from honeybee_energy.construction.shade import ShadeConstruction
from honeybee_energy.material.opaque import EnergyMaterial
from honeybee_energy.material.glazing import EnergyWindowMaterialGlazing
from honeybee_energy.material.gas import EnergyWindowMaterialGas

import pytest


def test_constructionset_init():
    """Test the initialization of ConstructionSet and basic properties."""
    default_set = ConstructionSet('Default Set')
    str(default_set)  # test the string representation of the construction

    assert default_set.identifier == 'Default Set'
    assert len(default_set.constructions) == 20
    assert len(default_set.constructions_unique) == 15
    assert len(default_set.materials_unique) == 15
    assert len(default_set.modified_constructions_unique) == 0
    assert len(default_set.modified_materials_unique) == 0

    assert isinstance(default_set.wall_set, WallConstructionSet)
    assert isinstance(default_set.floor_set, FloorConstructionSet)
    assert isinstance(default_set.roof_ceiling_set, RoofCeilingConstructionSet)
    assert isinstance(default_set.aperture_set, ApertureConstructionSet)
    assert isinstance(default_set.door_set, DoorConstructionSet)
    assert isinstance(default_set.shade_construction, ShadeConstruction)


def test_constructionset_defaults():
    """Test the ConstructionSet defaults."""
    default_set = ConstructionSet('Default Set')

    assert len(default_set.wall_set) == 3
    assert len(default_set.floor_set) == 3
    assert len(default_set.roof_ceiling_set) == 3
    assert len(default_set.aperture_set) == 4
    assert len(default_set.door_set) == 5

    for constr in default_set.wall_set:
        assert isinstance(constr, OpaqueConstruction)
    for constr in default_set.floor_set:
        assert isinstance(constr, OpaqueConstruction)
    for constr in default_set.roof_ceiling_set:
        assert isinstance(constr, OpaqueConstruction)
    for constr in default_set.aperture_set:
        assert isinstance(constr, WindowConstruction)

    assert isinstance(default_set.wall_set.exterior_construction, OpaqueConstruction)
    assert isinstance(default_set.wall_set.interior_construction, OpaqueConstruction)
    assert isinstance(default_set.wall_set.ground_construction, OpaqueConstruction)
    assert isinstance(default_set.floor_set.exterior_construction, OpaqueConstruction)
    assert isinstance(default_set.floor_set.interior_construction, OpaqueConstruction)
    assert isinstance(default_set.floor_set.ground_construction, OpaqueConstruction)
    assert isinstance(default_set.roof_ceiling_set.exterior_construction, OpaqueConstruction)
    assert isinstance(default_set.roof_ceiling_set.interior_construction, OpaqueConstruction)
    assert isinstance(default_set.roof_ceiling_set.ground_construction, OpaqueConstruction)
    assert isinstance(default_set.aperture_set.window_construction, WindowConstruction)
    assert isinstance(default_set.aperture_set.interior_construction, WindowConstruction)
    assert isinstance(default_set.aperture_set.skylight_construction, WindowConstruction)
    assert isinstance(default_set.aperture_set.operable_construction, WindowConstruction)
    assert isinstance(default_set.door_set.exterior_construction, OpaqueConstruction)
    assert isinstance(default_set.door_set.interior_construction, OpaqueConstruction)
    assert isinstance(default_set.door_set.exterior_glass_construction, WindowConstruction)
    assert isinstance(default_set.door_set.interior_glass_construction, WindowConstruction)
    assert isinstance(default_set.door_set.overhead_construction, OpaqueConstruction)


def test_setting_construction():
    """Test the setting of constructions on the ConstructionSet."""
    default_set = ConstructionSet('Thermal Mass Construction Set')
    concrete20 = EnergyMaterial('20cm Concrete', 0.2, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    concrete10 = EnergyMaterial('10cm Concrete', 0.1, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    stone_door = EnergyMaterial('Stone Door', 0.05, 2.31, 2322, 832,
                                'MediumRough', 0.95, 0.75, 0.8)
    thick_constr = OpaqueConstruction(
        'Thick Concrete Construction', [concrete20])
    thin_constr = OpaqueConstruction(
        'Thin Concrete Construction', [concrete10])
    door_constr = OpaqueConstruction(
        'Stone Door', [stone_door])
    light_shelf = ShadeConstruction('Light Shelf', 0.5, 0.5, True)

    default_set.wall_set.exterior_construction = thick_constr
    assert default_set.wall_set.exterior_construction == thick_constr
    assert len(default_set.modified_constructions_unique) == 1
    assert len(default_set.modified_materials_unique) == 1

    assert isinstance(default_set.wall_set.exterior_construction[0], EnergyMaterial)
    with pytest.raises(AttributeError):
        default_set.wall_set.exterior_construction[0].thickness = 0.15

    default_set.wall_set.interior_construction = thin_constr
    assert default_set.wall_set.interior_construction == thin_constr
    default_set.wall_set.ground_construction = thick_constr
    assert default_set.wall_set.ground_construction == thick_constr
    default_set.floor_set.exterior_construction = thick_constr
    assert default_set.floor_set.exterior_construction == thick_constr
    default_set.floor_set.interior_construction = thin_constr
    assert default_set.floor_set.interior_construction == thin_constr
    default_set.floor_set.ground_construction = thick_constr
    assert default_set.floor_set.ground_construction == thick_constr
    default_set.roof_ceiling_set.exterior_construction = thick_constr
    assert default_set.roof_ceiling_set.exterior_construction == thick_constr
    default_set.roof_ceiling_set.interior_construction = thin_constr
    assert default_set.roof_ceiling_set.interior_construction == thin_constr
    default_set.roof_ceiling_set.ground_construction = thick_constr
    assert default_set.roof_ceiling_set.ground_construction == thick_constr
    default_set.door_set.exterior_construction = door_constr
    assert default_set.door_set.exterior_construction == door_constr
    default_set.door_set.interior_construction = door_constr
    assert default_set.door_set.interior_construction == door_constr
    default_set.door_set.overhead_construction = door_constr
    assert default_set.door_set.overhead_construction == door_constr
    default_set.shade_construction = light_shelf
    assert default_set.shade_construction == light_shelf

    assert len(default_set.modified_constructions_unique) == 4
    assert len(default_set.modified_materials_unique) == 3


def test_setting_window_construction():
    """Test the setting of aperture and glass door constructions on ConstructionSet."""
    default_set = ConstructionSet('Tinted Window Set')
    tinted_glass = EnergyWindowMaterialGlazing(
        'Tinted Glass', 0.006, 0.35, 0.03, 0.884, 0.0804, 0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('Window Air Gap', thickness=0.0127)
    double_tint = WindowConstruction(
        'Double Tinted Window', [tinted_glass, gap, tinted_glass])
    single_tint = WindowConstruction(
        'Single Tinted Window', [tinted_glass])

    default_set.aperture_set.window_construction = double_tint
    assert default_set.aperture_set.window_construction == double_tint
    assert len(default_set.modified_constructions_unique) == 1
    assert len(default_set.modified_materials_unique) == 2

    assert isinstance(default_set.aperture_set.window_construction[0],
                      EnergyWindowMaterialGlazing)
    with pytest.raises(AttributeError):
        default_set.aperture_set.window_construction[0].thickness = 0.003

    default_set.aperture_set.interior_construction = single_tint
    assert default_set.aperture_set.interior_construction == single_tint
    default_set.aperture_set.skylight_construction = double_tint
    assert default_set.aperture_set.skylight_construction == double_tint
    default_set.aperture_set.operable_construction = double_tint
    assert default_set.aperture_set.operable_construction == double_tint

    default_set.door_set.exterior_glass_construction = double_tint
    assert default_set.door_set.exterior_glass_construction == double_tint
    default_set.door_set.interior_glass_construction = single_tint
    assert default_set.door_set.interior_glass_construction == single_tint

    assert len(default_set.modified_constructions_unique) == 2
    assert len(default_set.modified_materials_unique) == 2


def test_constructionset_equality():
    """Test the equality of ConstructionSets to one another."""
    default_set = ConstructionSet('Default Set')
    concrete = EnergyMaterial('Concrete', 0.15, 2.31, 2322, 832, 'MediumRough',
                              0.95, 0.75, 0.8)
    wall_constr = OpaqueConstruction(
        'Concrete Construction', [concrete])
    default_set.wall_set.exterior_construction = wall_constr
    new_default_set = default_set.duplicate()

    cnstr_set_list = [default_set, default_set, new_default_set]
    assert cnstr_set_list[0] is cnstr_set_list[1]
    assert cnstr_set_list[0] is not cnstr_set_list[2]
    assert cnstr_set_list[0] == cnstr_set_list[2]

    new_default_set.identifier = 'ASHRAE 90.1 Construction Set'
    assert cnstr_set_list[0] != cnstr_set_list[2]


def test_constructionset_to_dict_full():
    """Test the to_dict method writing out all constructions."""
    default_set = ConstructionSet('Default Set')

    constr_dict = default_set.to_dict(none_for_defaults=False)

    assert constr_dict['wall_set']['exterior_construction'] is not None
    assert constr_dict['wall_set']['interior_construction'] is not None
    assert constr_dict['wall_set']['ground_construction'] is not None
    assert constr_dict['floor_set']['exterior_construction'] is not None
    assert constr_dict['floor_set']['interior_construction'] is not None
    assert constr_dict['floor_set']['ground_construction'] is not None
    assert constr_dict['roof_ceiling_set']['exterior_construction'] is not None
    assert constr_dict['roof_ceiling_set']['interior_construction'] is not None
    assert constr_dict['roof_ceiling_set']['ground_construction'] is not None
    assert constr_dict['aperture_set']['window_construction'] is not None
    assert constr_dict['aperture_set']['interior_construction'] is not None
    assert constr_dict['aperture_set']['skylight_construction'] is not None
    assert constr_dict['aperture_set']['operable_construction'] is not None
    assert constr_dict['door_set']['exterior_construction'] is not None
    assert constr_dict['door_set']['interior_construction'] is not None
    assert constr_dict['door_set']['exterior_glass_construction'] is not None
    assert constr_dict['door_set']['interior_glass_construction'] is not None
    assert constr_dict['door_set']['overhead_construction'] is not None
    assert constr_dict['shade_construction'] is not None


def test_constructionset_dict_methods():
    """Test the to/from dict methods."""
    insulated_set = ConstructionSet('Insulated Set')
    clear_glass = EnergyWindowMaterialGlazing(
        'Clear Glass', 0.005715, 0.770675, 0.07, 0.8836, 0.0804,
        0, 0.84, 0.84, 1.0)
    gap = EnergyWindowMaterialGas('air gap', thickness=0.0127)
    triple_clear = WindowConstruction(
        'Triple Clear Window', [clear_glass, gap, clear_glass, gap, clear_glass])

    insulated_set.aperture_set.window_construction = triple_clear
    constr_dict = insulated_set.to_dict()

    assert constr_dict['wall_set']['exterior_construction'] is None
    assert constr_dict['wall_set']['interior_construction'] is None
    assert constr_dict['wall_set']['ground_construction'] is None
    assert constr_dict['floor_set']['exterior_construction'] is None
    assert constr_dict['floor_set']['interior_construction'] is None
    assert constr_dict['floor_set']['ground_construction'] is None
    assert constr_dict['roof_ceiling_set']['exterior_construction'] is None
    assert constr_dict['roof_ceiling_set']['interior_construction'] is None
    assert constr_dict['roof_ceiling_set']['ground_construction'] is None
    assert constr_dict['aperture_set']['window_construction'] is not None
    assert constr_dict['aperture_set']['interior_construction'] is None
    assert constr_dict['aperture_set']['skylight_construction'] is None
    assert constr_dict['aperture_set']['operable_construction'] is None
    assert constr_dict['door_set']['exterior_construction'] is None
    assert constr_dict['door_set']['interior_construction'] is None
    assert constr_dict['door_set']['exterior_glass_construction'] is None
    assert constr_dict['door_set']['interior_glass_construction'] is None
    assert constr_dict['door_set']['overhead_construction'] is None
    assert constr_dict['shade_construction'] is None

    new_constr = ConstructionSet.from_dict(constr_dict)
    assert constr_dict == new_constr.to_dict()
