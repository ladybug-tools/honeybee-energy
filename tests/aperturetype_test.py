"""test Face class."""
from honeybee.aperturetype import Window, OperableWindow, GlassDoor, aperture_types

import pytest


def test_window():
    """Test the initialization of the Wall aperture type."""
    window_type_1 = Window()
    window_type_2 = aperture_types.window

    str(window_type_1)  # test the string representation
    assert window_type_1 == window_type_2
    assert window_type_1 != aperture_types.glass_door


def test_roof_ceiling():
    """Test the initialization of the OperableWindow aperture type."""
    operable_window_type_1 = OperableWindow()
    operable_window_type_2 = aperture_types.operable_window()

    str(operable_window_type_1)  # test the string representation
    assert operable_window_type_1 == operable_window_type_2
    assert operable_window_type_1 != aperture_types.glass_door


def test_floor():
    """Test the initialization of the Floor face type."""
    glass_door_type_1 = GlassDoor()
    glass_door_type_2 = aperture_types.glass_door

    str(glass_door_type_1)  # test the string representation
    assert glass_door_type_1 == glass_door_type_2
    assert glass_door_type_1 != aperture_types.operable_window
