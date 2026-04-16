"""
Aluminium profile presets for windows and doors.

These presets represent common cross-section families and provide
recommended default dimensions for the parametric model.
"""

from __future__ import annotations

from dataclasses import dataclass

from core.enums import ProductKind, WindowType


@dataclass(frozen=True)
class AluminiumProfilePreset:
    """Preset profile metadata."""

    key: str
    name: str
    product_kind: ProductKind
    supported_types: tuple[WindowType, ...]
    frame_width: float
    frame_depth: float
    mullion_width: float
    default_glass_thickness: float
    min_glass_thickness: float
    max_glass_thickness: float
    default_panels: int
    threshold_height: float = 25.0


PROFILE_PRESETS: tuple[AluminiumProfilePreset, ...] = (
    AluminiumProfilePreset(
        key="win_basic_50",
        name="Window 50 Series (Economic)",
        product_kind=ProductKind.WINDOW,
        supported_types=(WindowType.FIXED, WindowType.SLIDING, WindowType.CASEMENT),
        frame_width=50.0,
        frame_depth=70.0,
        mullion_width=45.0,
        default_glass_thickness=6.0,
        min_glass_thickness=5.0,
        max_glass_thickness=12.0,
        default_panels=2,
    ),
    AluminiumProfilePreset(
        key="win_thermal_65",
        name="Window 65 Thermal Break",
        product_kind=ProductKind.WINDOW,
        supported_types=(WindowType.FIXED, WindowType.SLIDING, WindowType.CASEMENT),
        frame_width=60.0,
        frame_depth=110.0,
        mullion_width=52.0,
        default_glass_thickness=20.0,
        min_glass_thickness=18.0,
        max_glass_thickness=30.0,
        default_panels=2,
    ),
    AluminiumProfilePreset(
        key="door_swing_75",
        name="Door 75 Swing Series",
        product_kind=ProductKind.DOOR,
        supported_types=(WindowType.SINGLE_SWING_DOOR, WindowType.DOUBLE_SWING_DOOR),
        frame_width=75.0,
        frame_depth=100.0,
        mullion_width=70.0,
        default_glass_thickness=24.0,
        min_glass_thickness=20.0,
        max_glass_thickness=32.0,
        default_panels=1,
        threshold_height=30.0,
    ),
    AluminiumProfilePreset(
        key="door_slide_90",
        name="Door 90 Sliding Series",
        product_kind=ProductKind.DOOR,
        supported_types=(WindowType.SLIDING,),
        frame_width=80.0,
        frame_depth=130.0,
        mullion_width=65.0,
        default_glass_thickness=22.0,
        min_glass_thickness=18.0,
        max_glass_thickness=30.0,
        default_panels=2,
        threshold_height=35.0,
    ),
)


def get_profile(profile_key: str) -> AluminiumProfilePreset | None:
    """Return a profile preset by key."""

    for preset in PROFILE_PRESETS:
        if preset.key == profile_key:
            return preset
    return None


def list_profiles(
    product_kind: ProductKind,
    window_type: WindowType | None = None,
) -> list[AluminiumProfilePreset]:
    """Return matching presets for a product and optional opening type."""

    out: list[AluminiumProfilePreset] = []
    for preset in PROFILE_PRESETS:
        if preset.product_kind != product_kind:
            continue
        if window_type is not None and window_type not in preset.supported_types:
            continue
        out.append(preset)
    return out


def default_profile_key(product_kind: ProductKind) -> str:
    """Get first preset key for a product kind."""

    for preset in PROFILE_PRESETS:
        if preset.product_kind == product_kind:
            return preset.key
    return PROFILE_PRESETS[0].key
