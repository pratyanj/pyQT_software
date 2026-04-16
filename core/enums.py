"""
Enumerations used across the Fenestration Designer application.
"""

from enum import Enum


class ProductKind(Enum):
    """Top-level product family."""

    WINDOW = "window"
    DOOR = "door"


class WindowType(Enum):
    """Opening types used by windows and doors."""

    FIXED = "fixed"
    SLIDING = "sliding"
    CASEMENT = "casement"
    SINGLE_SWING_DOOR = "single_swing_door"
    DOUBLE_SWING_DOOR = "double_swing_door"


class ViewMode(Enum):
    """Available drawing view modes."""
    FRONT = "front"
    HORIZONTAL_SECTION = "horizontal_section"
    VERTICAL_SECTION = "vertical_section"
    VIEW_3D = "view_3d"
