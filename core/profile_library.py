"""
Aluminium profile library.

Supports:
1) Built-in profile presets.
2) Custom profiles loaded from `config/custom_profiles.json`.
"""

from __future__ import annotations

from dataclasses import dataclass
import json
from pathlib import Path

from config.settings import CUSTOM_PROFILE_FILE
from core.enums import ProductKind, WindowType


@dataclass(frozen=True)
class SectionFeature:
    """A rectangular detail element in a profile cross-section.

    All values are normalized (0..1) relative to the profile body.
    """

    layer: str
    x: float
    y: float
    width: float
    height: float


@dataclass(frozen=True)
class AluminiumProfilePreset:
    """Profile metadata and optional section-detail templates."""

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
    horizontal_features: tuple[SectionFeature, ...] = ()
    vertical_features: tuple[SectionFeature, ...] = ()


BUILTIN_PRESETS: tuple[AluminiumProfilePreset, ...] = (
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
        horizontal_features=(
            SectionFeature("cavity", 0.10, 0.18, 0.30, 0.28),
            SectionFeature("cavity", 0.10, 0.56, 0.30, 0.26),
            SectionFeature("reinforcement", 0.48, 0.34, 0.14, 0.32),
        ),
        vertical_features=(
            SectionFeature("cavity", 0.16, 0.12, 0.26, 0.34),
            SectionFeature("cavity", 0.58, 0.12, 0.26, 0.34),
        ),
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
        horizontal_features=(
            SectionFeature("cavity", 0.08, 0.10, 0.22, 0.24),
            SectionFeature("cavity", 0.08, 0.42, 0.22, 0.24),
            SectionFeature("cavity", 0.08, 0.72, 0.22, 0.18),
            SectionFeature("thermal_break", 0.34, 0.34, 0.14, 0.32),
            SectionFeature("reinforcement", 0.54, 0.20, 0.18, 0.60),
        ),
        vertical_features=(
            SectionFeature("cavity", 0.12, 0.10, 0.24, 0.22),
            SectionFeature("cavity", 0.40, 0.10, 0.20, 0.22),
            SectionFeature("thermal_break", 0.64, 0.08, 0.10, 0.30),
        ),
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
        horizontal_features=(
            SectionFeature("cavity", 0.10, 0.12, 0.22, 0.22),
            SectionFeature("cavity", 0.10, 0.42, 0.22, 0.22),
            SectionFeature("reinforcement", 0.44, 0.14, 0.18, 0.52),
        ),
        vertical_features=(
            SectionFeature("cavity", 0.12, 0.12, 0.24, 0.24),
            SectionFeature("reinforcement", 0.52, 0.12, 0.18, 0.28),
        ),
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
        horizontal_features=(
            SectionFeature("cavity", 0.08, 0.10, 0.20, 0.18),
            SectionFeature("cavity", 0.08, 0.34, 0.20, 0.18),
            SectionFeature("cavity", 0.08, 0.58, 0.20, 0.18),
            SectionFeature("reinforcement", 0.42, 0.18, 0.16, 0.56),
        ),
        vertical_features=(
            SectionFeature("cavity", 0.10, 0.10, 0.22, 0.24),
            SectionFeature("cavity", 0.42, 0.10, 0.22, 0.24),
        ),
    ),
)


_CUSTOM_PROFILE_PATH = Path(__file__).resolve().parents[1] / CUSTOM_PROFILE_FILE


def _to_features(raw_features: object) -> tuple[SectionFeature, ...]:
    if not isinstance(raw_features, list):
        return ()
    out: list[SectionFeature] = []
    for item in raw_features:
        if not isinstance(item, dict):
            continue
        try:
            feature = SectionFeature(
                layer=str(item["layer"]),
                x=float(item["x"]),
                y=float(item["y"]),
                width=float(item["width"]),
                height=float(item["height"]),
            )
        except (KeyError, TypeError, ValueError):
            continue
        if feature.width <= 0 or feature.height <= 0:
            continue
        out.append(feature)
    return tuple(out)


def _parse_custom_profile(item: dict) -> AluminiumProfilePreset | None:
    try:
        return AluminiumProfilePreset(
            key=str(item["key"]),
            name=str(item["name"]),
            product_kind=ProductKind(str(item["product_kind"])),
            supported_types=tuple(WindowType(str(v)) for v in item["supported_types"]),
            frame_width=float(item["frame_width"]),
            frame_depth=float(item["frame_depth"]),
            mullion_width=float(item["mullion_width"]),
            default_glass_thickness=float(item["default_glass_thickness"]),
            min_glass_thickness=float(item["min_glass_thickness"]),
            max_glass_thickness=float(item["max_glass_thickness"]),
            default_panels=int(item["default_panels"]),
            threshold_height=float(item.get("threshold_height", 25.0)),
            horizontal_features=_to_features(item.get("horizontal_features", [])),
            vertical_features=_to_features(item.get("vertical_features", [])),
        )
    except (KeyError, TypeError, ValueError):
        return None


def _load_custom_presets() -> tuple[AluminiumProfilePreset, ...]:
    if not _CUSTOM_PROFILE_PATH.exists():
        return ()
    try:
        payload = json.loads(_CUSTOM_PROFILE_PATH.read_text(encoding="utf-8"))
    except (OSError, json.JSONDecodeError):
        return ()

    if not isinstance(payload, list):
        return ()

    custom: list[AluminiumProfilePreset] = []
    for item in payload:
        if not isinstance(item, dict):
            continue
        profile = _parse_custom_profile(item)
        if profile is None:
            continue
        custom.append(profile)
    return tuple(custom)


def _all_presets() -> tuple[AluminiumProfilePreset, ...]:
    return BUILTIN_PRESETS + _load_custom_presets()


def get_profile(profile_key: str) -> AluminiumProfilePreset | None:
    """Return a profile preset by key."""

    for preset in _all_presets():
        if preset.key == profile_key:
            return preset
    return None


def list_profiles(
    product_kind: ProductKind,
    window_type: WindowType | None = None,
) -> list[AluminiumProfilePreset]:
    """Return matching presets for a product and optional opening type."""

    out: list[AluminiumProfilePreset] = []
    for preset in _all_presets():
        if preset.product_kind != product_kind:
            continue
        if window_type is not None and window_type not in preset.supported_types:
            continue
        out.append(preset)
    return out


def default_profile_key(product_kind: ProductKind) -> str:
    """Get first preset key for a product kind."""

    for preset in _all_presets():
        if preset.product_kind == product_kind:
            return preset.key
    return BUILTIN_PRESETS[0].key
