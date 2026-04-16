"""
Data models for fenestration products.

WindowModel remains the primary parametric model for compatibility with
existing save files and application code.
"""

from __future__ import annotations

from dataclasses import dataclass, asdict

from core.enums import ProductKind, WindowType
from core.profile_library import default_profile_key


@dataclass
class WindowModel:
    """Parametric model for a window or door product."""

    product_kind: ProductKind = ProductKind.WINDOW
    window_type: WindowType = WindowType.FIXED
    profile_key: str = default_profile_key(ProductKind.WINDOW)

    width: float = 1200.0
    height: float = 1000.0
    frame_width: float = 50.0
    frame_depth: float = 70.0
    glass_thickness: float = 6.0
    num_panels: int = 1
    mullion_width: float = 50.0
    threshold_height: float = 25.0

    def to_dict(self) -> dict:
        """Serialize model to a JSON-safe dictionary."""

        data = asdict(self)
        data["product_kind"] = self.product_kind.value
        data["window_type"] = self.window_type.value
        return data

    @classmethod
    def from_dict(cls, data: dict) -> "WindowModel":
        """Deserialize a dictionary into WindowModel.

        Supports legacy files that only contain `window_type` and have no
        `product_kind` / `profile_key`.
        """

        data = data.copy()
        product_kind_raw = data.get("product_kind", ProductKind.WINDOW.value)
        data["product_kind"] = ProductKind(product_kind_raw)

        window_type_raw = data.get("window_type", WindowType.FIXED.value)
        data["window_type"] = WindowType(window_type_raw)

        if "profile_key" not in data:
            data["profile_key"] = default_profile_key(data["product_kind"])

        if "threshold_height" not in data:
            data["threshold_height"] = 25.0

        return cls(**data)

    @property
    def inner_width(self) -> float:
        """Usable opening width (minus frame on each side)."""

        return self.width - 2 * self.frame_width

    @property
    def inner_height(self) -> float:
        """Usable opening height (minus frame top/bottom)."""

        return self.height - 2 * self.frame_width

    @property
    def panel_width(self) -> float:
        """Width of a single panel within the opening."""

        total_mullion = (self.num_panels - 1) * self.mullion_width
        return (self.inner_width - total_mullion) / self.num_panels
