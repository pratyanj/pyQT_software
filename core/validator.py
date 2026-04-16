"""
Validation logic for WindowModel parameters.

Returns a list of human-readable error strings.
An empty list means the model is valid.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from core.enums import ProductKind, WindowType
from core.profile_library import get_profile

if TYPE_CHECKING:
    from core.models import WindowModel


class Validator:
    """Validates a WindowModel before rendering/export."""

    @staticmethod
    def validate(model: "WindowModel") -> list[str]:
        errors: list[str] = []

        if model.width <= 0:
            errors.append("Width must be positive")
        if model.height <= 0:
            errors.append("Height must be positive")
        if model.frame_width <= 0:
            errors.append("Frame width must be positive")
        if model.frame_depth <= 0:
            errors.append("Frame depth must be positive")
        if model.glass_thickness <= 0:
            errors.append("Glass thickness must be positive")
        if model.threshold_height < 0:
            errors.append("Threshold height cannot be negative")

        if model.frame_width * 2 >= min(model.width, model.height):
            errors.append("Frame width too large for product dimensions")

        if model.glass_thickness >= model.frame_depth:
            errors.append("Glass thickness must be less than frame depth")

        if model.num_panels < 1:
            errors.append("Must have at least 1 panel")

        if model.num_panels > 1 and model.mullion_width <= 0:
            errors.append("Mullion width must be positive for multi-panel design")

        available_width = model.width - 2 * model.frame_width
        if model.num_panels > 1:
            available_width -= (model.num_panels - 1) * model.mullion_width
        if available_width <= 0:
            errors.append("Not enough space for panels with current dimensions")

        if model.product_kind == ProductKind.WINDOW:
            if model.window_type in (
                WindowType.SINGLE_SWING_DOOR,
                WindowType.DOUBLE_SWING_DOOR,
            ):
                errors.append("Door opening type cannot be used for windows")
            if model.height < 300:
                errors.append("Window height must be at least 300 mm")
        else:
            if model.window_type == WindowType.FIXED:
                errors.append("Doors cannot use fixed opening type")
            if model.window_type == WindowType.CASEMENT:
                errors.append("Use swing door type for hinged doors")
            if model.height < 1700:
                errors.append("Door height should be at least 1700 mm")
            if model.window_type == WindowType.SINGLE_SWING_DOOR and model.num_panels != 1:
                errors.append("Single swing door must have exactly 1 panel")
            if model.window_type == WindowType.DOUBLE_SWING_DOOR and model.num_panels != 2:
                errors.append("Double swing door must have exactly 2 panels")
            if model.window_type == WindowType.SLIDING and model.num_panels < 2:
                errors.append("Sliding door must have at least 2 panels")

        profile = get_profile(model.profile_key)
        if profile is not None:
            if model.glass_thickness < profile.min_glass_thickness:
                errors.append(
                    f"Glass thickness too low for selected profile ({profile.min_glass_thickness:.0f} mm min)"
                )
            if model.glass_thickness > profile.max_glass_thickness:
                errors.append(
                    f"Glass thickness too high for selected profile ({profile.max_glass_thickness:.0f} mm max)"
                )

        return errors
