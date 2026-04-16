"""
3-D geometry generator for fenestration products.

Converts a WindowModel into a list of box primitives that
the OpenGL viewport can render.

Each shape dict:
    type      : 'box'
    position  : (cx, cy, cz)  – centre of the box
    size      : (w,  h,  d)   – full width / height / depth
    layer     : 'frame' | 'glass' | 'mullion'
"""

from __future__ import annotations

from core.models import WindowModel
from core.enums import WindowType


class Generator3D:
    """Produces 3-D box primitives from a WindowModel."""

    def generate(self, model: WindowModel) -> list[dict]:
        shapes: list[dict] = []

        W  = model.width
        H  = model.height
        FW = model.frame_width
        FD = model.frame_depth
        GT = model.glass_thickness
        IW = model.inner_width
        IH = model.inner_height
        PW = model.panel_width
        MW = model.mullion_width

        # ── Outer frame (4 beams) ───────────────────────────────────

        # Left jamb
        shapes.append(self._box(-W/2 + FW/2, 0, 0, FW, H, FD, "frame"))

        # Right jamb
        shapes.append(self._box(W/2 - FW/2, 0, 0, FW, H, FD, "frame"))

        # Head (top rail) – spans between jambs
        shapes.append(self._box(0, H/2 - FW/2, 0, IW, FW, FD, "frame"))

        # Sill (bottom rail)
        shapes.append(self._box(0, -H/2 + FW/2, 0, IW, FW, FD, "frame"))

        # ── Glass panels ───────────────────────────────────────────

        for i in range(model.num_panels):
            px = -IW/2 + i * (PW + MW) + PW / 2

            # Sliding: offset alternating panels on Z-axis (tracks)
            if model.window_type == WindowType.SLIDING:
                z_off = FD * 0.15 * (1 if i % 2 == 0 else -1)
            else:
                z_off = 0.0

            shapes.append(self._box(px, 0, z_off, PW, IH, GT, "glass"))

            # Mullion between panels
            if i < model.num_panels - 1:
                mx = -IW/2 + (i + 1) * (PW + MW) - MW / 2
                shapes.append(self._box(mx, 0, 0, MW, IH, FD, "mullion"))

        return shapes

    # ── helper ──────────────────────────────────────────────────────

    @staticmethod
    def _box(x, y, z, w, h, d, layer):
        return dict(
            type="box",
            position=(x, y, z),
            size=(w, h, d),
            layer=layer,
        )
